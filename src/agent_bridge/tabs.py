"""Tabs: list them, read one as it is now or at any step of its undo history,
open a design in a new tab, rename, switch, close. Every tab has a version (a
fingerprint of its strands and groups) that changes whenever the person
edits, undoes or redoes.

Closing is the one thing here that can lose the person's work, so it is
hedged on this side, whatever the agent was told or understood:
- one tab per request, named by its id AND its title as list_tabs gives them
  now: a guessed, remembered or off-by-one id closes nothing;
- a tab with unsaved changes stays open unless the request says to discard
  them and names the tab's version: when the person changed the tab since the
  agent looked, it stays open;
- the app's own "Unsaved changes" dialog is never shown for the agent (it
  would wait for a click nobody knows to make): the checks above stand in;
- the closed tab is kept, whole (design, undo history, file, unsaved state),
  on a card in the conversation with Reopen: a wrong close is one click to
  put right."""
import hashlib
import json
import os

from .base import Action, BridgeError, patched

MAX_TITLE = 60


class TabActions:
    ACTIONS = {
        'list_tabs': Action(run='list_tabs_action'),
        'read_tab': Action(run='read_tab_action', tab=True),
        'read_tab_step': Action(run='read_tab_step_action', tab=True),
        'open_in_new_tab': Action(run='open_tab_action', change=True, check='check_open', ask='open_tab_card'),
        'rename_tab': Action(run='rename_tab_action', change=True, tab=True, check='check_rename',
                             card='rename_card'),
        'switch_tab': Action(run='switch_tab_action', change=True, tab=True, card='switch_card'),
        'close_tab': Action(run='close_tab_action', change=True, tab=True, check='check_close', card='close_card'),
    }

    # ---------------------------------------------------------- actions
    def list_tabs_action(self, args, session):
        return {'tabs': self.list_tabs()}

    def read_tab_action(self, args, session):
        return self.read_tab(session.id)

    def read_tab_step_action(self, args, session):
        return self.read_tab_step(session.id, args.get('step'))

    def check_open(self, args, session):
        self.design_path(args.get('path'))
        self.title(args.get('title'))

    def open_tab_card(self, args, session):
        """Ask mode: the design waits as a card the person opens."""
        path, title = self.design_path(args.get('path')), self.title(args.get('title'))
        self.panel.add_design_card(path, title)
        return {'opened': False, 'title': title, 'note': f'"{title}" waits as a card the person opens'}

    def open_tab_action(self, args, session):
        return self.open_in_new_tab(self.design_path(args.get('path')), self.title(args.get('title')))

    def check_rename(self, args, session):
        self.title(args.get('title'))

    def rename_card(self, args, session):
        return ('rename_tab', self.tabs.title_for(session), self.title(args.get('title')))

    def rename_tab_action(self, args, session):
        title = self.title(args.get('title'))
        self.set_title(session, title)
        return {'tab_id': session.id, 'title': title, 'note': f'renamed to "{title}"'}

    def switch_card(self, args, session):
        return ('switch_tab', self.tabs.title_for(session), '')

    def switch_tab_action(self, args, session):
        if not self.tabs.switch_to_tab(session.id):
            raise BridgeError('the app could not switch tabs')
        return {'tab_id': session.id, 'title': self.tabs.title_for(session), 'note': 'switched'}

    # ------------------------------------------------------------ closing
    def check_close(self, args, session):
        """Refuses a close that is not surely the tab meant, or that would lose work unasked."""
        title = self.tabs.title_for(session)
        same = lambda text: ' '.join(str(text or '').split()).casefold()
        if same(args.get('title')) != same(title):
            raise BridgeError(f'tab {session.id} is titled "{title}", not "{args.get("title") or ""}": nothing was '
                              'closed. Call list_tabs and give the id and the title of the tab the person asked '
                              'to close, both as listed')
        if not session.dirty:
            return
        if args.get('discard_unsaved') is not True:
            raise BridgeError(f'"{title}" has unsaved changes, so it stays open: closing it would lose them. Tell '
                              'the person it is unsaved. Close it only if they said, in this request, to close it '
                              'without saving or to discard its changes: then pass discard_unsaved: true with its '
                              'version from list_tabs. To save it first: switch_tab to it, then app_window save')
        expected = args.get('version')
        if not expected:
            raise BridgeError(f'"{title}" has unsaved changes: to close it without saving, also give its version '
                              'from list_tabs, so it is closed only as you saw it')
        if str(expected) != self.version(session):
            raise BridgeError(f'"{title}" changed since you listed it (the person is working in it): it stays '
                              'open. Tell the person, rather than closing work they just did')

    def close_card(self, args, session):
        """Ask mode's Allow / Deny card, which says when the tab has unsaved changes."""
        return ('close_tab_unsaved' if session.dirty else 'close_tab', self.tabs.title_for(session), '')

    def close_tab_action(self, args, session):
        """Close the tab with the app's own code, after check_close, keeping it on a Reopen card."""
        tm = self.tabs
        title, unsaved, index = tm.title_for(session), bool(session.dirty), tm.tabs.index(session)
        if session.id == tm.active_tab_id and not tm.capture_active_session():
            # What is on the canvas is this tab: without a copy of it, Reopen would have nothing.
            raise BridgeError(f'"{title}" could not be kept for reopening, so it was not closed')
        # check_close has decided about unsaved changes: the app's own dialog must not open,
        # it would wait for a click while the agent waits for this answer.
        with patched(self.canvas, 'skip_close_tab_warning', True):
            tm.close_tab(session.id)
        if tm.find(session.id) is not None:
            raise BridgeError(f'the app did not close "{title}"')
        self.panel.add_closed_tab_card(session, index, title, unsaved)
        note = f'closed "{title}"' + (' without saving it' if unsaved else '')
        return {'tab_id': session.id, 'title': title, 'closed': True, 'unsaved': unsaved,
                'note': note + '; the person can reopen it from the card in the conversation'}

    def reopen_tab(self, session, index):
        """A tab the agent closed, back as it was: its design, undo history, file and unsaved
        state, at its old place, showing. For the Reopen link on its card."""
        tm = self.tabs
        if tm.find(session.id) is not None:
            return False
        if not tm._capture_or_warn():  # the tab showing now is kept first, as for any switch
            return False
        unsaved = session.dirty
        tm.tabs.insert(max(0, min(index, len(tm.tabs))), session)
        tm.active_tab_id = session.id
        tm.restore_session(session.id)
        session.dirty = unsaved
        tm.changed.emit()
        return True

    def list_tabs(self):
        tm = self.tabs
        out = []
        for session in tm.tabs:
            active = session.id == tm.active_tab_id
            if active:
                strands = len(getattr(self.window.canvas, 'strands', []))
            else:
                strands = len((session.project_state or {}).get('strands', []))
            history = self.history(session)
            out.append({'id': session.id, 'title': tm.title_for(session), 'active': active,
                        'strands': strands, 'unsaved': bool(session.dirty),
                        'version': self.version(session),
                        'undo_steps': history['max_step'], 'at_step': history['current_step']})
        return out

    # ------------------------------------------------- versions, history
    def tab_data(self, session):
        """The tab's design now: the live canvas for the tab showing, else its kept state."""
        if session.id == self.tabs.active_tab_id:
            return self.window.agent_canvas_snapshot()
        return session.project_state

    @staticmethod
    def fingerprint(data):
        """A short fingerprint of a design's strands and groups (not of what is selected)."""
        body = json.dumps({'strands': (data or {}).get('strands') or [], 'groups': (data or {}).get('groups') or {}},
                          sort_keys=True, default=str)
        return hashlib.sha1(body.encode('utf-8')).hexdigest()[:12]

    def version(self, session):
        return self.fingerprint(self.tab_data(session))

    def check_fresh(self, args, session):
        """An edit worked out on the tab as the agent read it: refused if the tab changed since."""
        expected = args.get('version')
        if expected and expected != self.version(session):
            raise BridgeError(f'"{self.tabs.title_for(session)}" changed since you read it (the person edited it, '
                              'or undid or redid a step): read_tab it again before editing')

    def history(self, session):
        """The tab's undo history: {current_step, max_step, steps: [{step, what, current}]}."""
        if session.id == self.tabs.active_tab_id:
            manager = getattr(self.window.canvas, 'undo_redo_manager', None)
            if manager is None or not hasattr(manager, 'get_history_entries'):
                return {'current_step': 0, 'max_step': 0, 'steps': []}
            steps = [{'step': e['step'], 'what': e.get('description') or '', 'current': e['is_current']}
                     for e in manager.get_history_entries()]
            return {'current_step': manager.current_step, 'max_step': manager.max_step, 'steps': steps}
        payload = session.history_payload or {}
        current = payload.get('current_step', 0)
        steps = []
        for state in payload.get('states') or []:
            data = state.get('data') or {}
            meta = data.get('undo_metadata') or {}  # undo_redo_metadata.METADATA_KEY
            steps.append({'step': state.get('step'), 'what': self.describe_meta(meta),
                          'current': state.get('step') == current})
        return {'current_step': current, 'max_step': payload.get('max_step', len(steps)), 'steps': steps}

    @staticmethod
    def describe_meta(meta):
        try:
            from undo_redo_metadata import describe
            return describe(meta) if meta else ''
        except Exception:
            return ''

    def step_data(self, session, step):
        """The design as it was at one step of the tab's undo history."""
        if session.id == self.tabs.active_tab_id:
            manager = getattr(self.window.canvas, 'undo_redo_manager', None)
            if manager is None:
                raise BridgeError('this tab keeps no undo history')
            if not 1 <= step <= manager.max_step:
                raise BridgeError(f'the tab has undo steps 1 to {manager.max_step}')
            path = manager._get_state_filename(step)
            if not os.path.isfile(path):
                raise BridgeError(f'undo step {step} is no longer kept')
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        for state in (session.history_payload or {}).get('states') or []:
            if state.get('step') == step:
                return state.get('data')
        raise BridgeError(f'"{self.tabs.title_for(session)}" keeps no undo step {step}')

    def read_tab_step(self, tab_id, step):
        """One past (or undone) step of a tab, as a design file the agent reads. The tab is unchanged."""
        session = self.session(tab_id)
        try:
            step = int(step)
        except (TypeError, ValueError):
            raise BridgeError('step is a number from the tab\'s history (read_tab lists them)') from None
        data = self.step_data(session, step)
        if not data or not data.get('strands'):
            raise BridgeError(f'undo step {step} has no design in it')
        path = os.path.join(self.run_folder(), f'tab_{session.id}_step_{step}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        history = self.history(session)
        what = next((s['what'] for s in history['steps'] if s['step'] == step), '')
        return {'file': path, 'title': self.tabs.title_for(session), 'step': step, 'what': what,
                'current_step': history['current_step'], 'max_step': history['max_step']}

    def read_tab(self, tab_id):
        tm = self.tabs
        session = self.session(tab_id)
        if session.id == tm.active_tab_id:
            data = self.window.agent_canvas_snapshot()
        else:
            data = session.project_state
        if not data or not data.get('strands'):
            raise BridgeError(f'tab "{tm.title_for(session)}" has no design in it')
        if 'project_settings' not in data:
            # The curve settings the tab is drawn with, so the agent's copy has
            # the same paths (as a saved project file carries them).
            from project_settings import capture_project_settings
            data = dict(data, project_settings=capture_project_settings(self.window.canvas))
        path = os.path.join(self.run_folder(), f'tab_{session.id}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return {'file': path, 'title': tm.title_for(session), 'version': self.fingerprint(data),
                'history': self.history(session)}

    def open_in_new_tab(self, path, title):
        """The same way as the agent's finished designs: a new tab, then Load's own loader."""
        tm = self.tabs
        if not self.window.open_agent_design(path):
            raise BridgeError('the design could not be opened in a new tab')
        session = tm.get_active()
        self.set_title(session, title)
        return {'opened': True, 'tab_id': session.id, 'title': title}

    def set_title(self, session, title):
        session.title = title
        session.untitled_index = None  # a custom title: no longer "Untitled N"
        self.tabs.changed.emit()

    def run_folder(self):
        folder = self.panel.out_dir
        if not folder or not os.path.isdir(folder):
            raise BridgeError('there is no agent request running')
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
