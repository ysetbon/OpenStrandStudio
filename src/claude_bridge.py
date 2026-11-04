"""The bridge between Claude and the running OpenStrand Studio.

Claude's agent runs in its own process (python -m openstrand agent --app) and
cannot reach the app's windows. When it calls one of its app tools it writes
a request line on stdout; the Claude panel hands it to AppBridge.handle here,
on the app's main thread, and writes the answer back to the agent's stdin
(see openstrand/app_tools.py for the other end).

Only the actions in ACTIONS exist, each a few lines over the app's own code:
the real TabManager, the same loader as Load, the canvas snapshot. What runs
follows the panel's mode:

- plan: Claude may look (list_tabs, read_tab), nothing changes;
- ask: a design waits as a card the person opens; a rename or a switch waits
  for the person's Allow or Deny in the conversation;
- auto: it happens.
"""
import json
import os

LOOK = {'list_tabs', 'read_tab'}
CHANGE = {'open_in_new_tab', 'rename_tab', 'switch_tab'}
ACTIONS = LOOK | CHANGE
MAX_TITLE = 60


class BridgeError(Exception):
    pass


class AppBridge:
    def __init__(self, window, panel):
        self.window = window
        self.panel = panel
        self.pending = {}  # call id -> the call, waiting for the person's Allow or Deny

    # -------------------------------------------------------------- calls
    def handle(self, call):
        """Answer one request: a reply dict, or None when the person decides later."""
        call_id, name, args = call.get('id'), call.get('name'), call.get('args') or {}
        try:
            if name not in ACTIONS:
                raise BridgeError(f'the app has no action {name}')
            mode = self.panel.run_mode
            if name in CHANGE and mode == 'plan':
                raise BridgeError('plan mode is on: Claude may look at tabs but not change them')
            if name == 'open_in_new_tab':
                path, title = self.design_path(args.get('path')), self.title(args.get('title'))
                if mode == 'ask':
                    self.panel.add_design_card(path, title)
                    return self.ok(call_id, {'opened': False, 'title': title,
                                             'note': f'"{title}" waits as a card the person opens'})
                return self.ok(call_id, self.open_in_new_tab(path, title))
            if name in ('rename_tab', 'switch_tab'):
                session = self.session(args.get('tab_id'))
                if mode == 'ask':
                    self.pending[call_id] = call
                    self.panel.add_confirm_card(call_id, self.describe(call, session))
                    return None
                return self.ok(call_id, self.do(call))
            if name == 'list_tabs':
                return self.ok(call_id, {'tabs': self.list_tabs()})
            return self.ok(call_id, self.read_tab(args.get('tab_id')))
        except BridgeError as e:
            return self.fail(call_id, str(e))
        except Exception as e:  # the app's own code failed: tell Claude, keep the app running
            return self.fail(call_id, f'{type(e).__name__}: {e}')

    def decide(self, call_id, allowed):
        """The person's Allow or Deny for a waiting change: the reply to send."""
        call = self.pending.pop(call_id, None)
        if call is None:
            return None
        if not allowed:
            return self.fail(call_id, 'the person declined this change')
        try:
            return self.ok(call_id, self.do(call))
        except BridgeError as e:
            return self.fail(call_id, str(e))
        except Exception as e:
            return self.fail(call_id, f'{type(e).__name__}: {e}')

    def forget(self):
        """The agent has stopped: nothing is waiting any more."""
        self.pending.clear()

    @staticmethod
    def ok(call_id, result):
        return {'id': call_id, 'ok': True, 'result': result}

    @staticmethod
    def fail(call_id, error):
        return {'id': call_id, 'ok': False, 'error': error}

    # ------------------------------------------------------------ actions
    @property
    def tabs(self):
        manager = getattr(self.window, 'tab_manager', None)
        if manager is None:
            raise BridgeError('this window has no tabs')
        return manager

    def list_tabs(self):
        tm = self.tabs
        out = []
        for session in tm.tabs:
            active = session.id == tm.active_tab_id
            if active:
                strands = len(getattr(self.window.canvas, 'strands', []))
            else:
                strands = len((session.project_state or {}).get('strands', []))
            out.append({'id': session.id, 'title': tm.title_for(session), 'active': active,
                        'strands': strands, 'unsaved': bool(session.dirty)})
        return out

    def read_tab(self, tab_id):
        tm = self.tabs
        session = self.session(tab_id)
        if session.id == tm.active_tab_id:
            data = self.window.claude_canvas_snapshot()
        else:
            data = session.project_state
        if not data or not data.get('strands'):
            raise BridgeError(f'tab "{tm.title_for(session)}" has no design in it')
        path = os.path.join(self.run_folder(), f'tab_{session.id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return {'file': path, 'title': tm.title_for(session)}

    def open_in_new_tab(self, path, title):
        """The same way as Claude's finished designs: a new tab, then Load's own loader."""
        tm = self.tabs
        if not self.window.open_claude_design(path):
            raise BridgeError('the design could not be opened in a new tab')
        session = tm.get_active()
        self.set_title(session, title)
        return {'opened': True, 'tab_id': session.id, 'title': title}

    def do(self, call):
        name, args = call['name'], call.get('args') or {}
        session = self.session(args.get('tab_id'))
        if name == 'rename_tab':
            title = self.title(args.get('title'))
            self.set_title(session, title)
            return {'tab_id': session.id, 'title': title, 'note': f'renamed to "{title}"'}
        if not self.tabs.switch_to_tab(session.id):
            raise BridgeError('the app could not switch tabs')
        return {'tab_id': session.id, 'title': self.tabs.title_for(session), 'note': 'switched'}

    # ------------------------------------------------------------- checks
    def session(self, tab_id):
        session = self.tabs.find(str(tab_id or ''))
        if session is None:
            raise BridgeError(f'no tab {tab_id}: list_tabs gives the ids')
        return session

    def set_title(self, session, title):
        session.title = title
        session.untitled_index = None  # a custom title: no longer "Untitled N"
        self.tabs.changed.emit()

    def run_folder(self):
        folder = self.panel.out_dir
        if not folder or not os.path.isdir(folder):
            raise BridgeError('there is no Claude request running')
        return folder

    def design_path(self, path):
        """A design file this request made: nothing outside its own folder opens."""
        folder = os.path.realpath(self.run_folder())
        real = os.path.realpath(str(path or ''))
        if os.path.commonpath([folder, real]) != folder or not real.endswith('.json') or not os.path.isfile(real):
            raise BridgeError('only designs made in this request can open')
        return real

    @staticmethod
    def title(text):
        text = ' '.join(str(text or '').split())[:MAX_TITLE]
        if not text:
            raise BridgeError('a tab needs a title')
        return text

    def describe(self, call, session):
        tm = self.tabs
        if call['name'] == 'rename_tab':
            return ('rename_tab', tm.title_for(session), self.title((call.get('args') or {}).get('title')))
        return ('switch_tab', tm.title_for(session), '')
