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
- ask: a design waits as a card the person opens; a rename, a switch or a
  mask edit waits for the person's Allow or Deny in the conversation;
- auto: it happens.
"""
import json
import os

LOOK = {'list_tabs', 'read_tab'}
CHANGE = {'open_in_new_tab', 'rename_tab', 'switch_tab', 'edit_mask'}
MASK_OPS = ('erase', 'reset', 'swap', 'delete', 'create')
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
            if name in ('rename_tab', 'switch_tab', 'edit_mask'):
                session = self.session(args.get('tab_id'))
                if name == 'edit_mask':
                    self.check_mask_edit(args, session)
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
        if 'project_settings' not in data:
            # The curve settings the tab is drawn with, so Claude's copy has
            # the same paths (as a saved project file carries them).
            from project_settings import capture_project_settings
            data = dict(data, project_settings=capture_project_settings(self.window.canvas))
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
        if name == 'edit_mask':
            self.check_mask_edit(args, session)
            return self.edit_mask(args, session)
        if name == 'rename_tab':
            title = self.title(args.get('title'))
            self.set_title(session, title)
            return {'tab_id': session.id, 'title': title, 'note': f'renamed to "{title}"'}
        if not self.tabs.switch_to_tab(session.id):
            raise BridgeError('the app could not switch tabs')
        return {'tab_id': session.id, 'title': self.tabs.title_for(session), 'note': 'switched'}

    # --------------------------------------------------------------- masks
    def check_mask_edit(self, args, session):
        """A mask edit names its op and layers; it works on the tab showing."""
        if session.id != self.tabs.active_tab_id:
            raise BridgeError(f'"{self.tabs.title_for(session)}" is not the tab showing: switch_tab to it first')
        op = args.get('op')
        if op not in MASK_OPS:
            raise BridgeError(f'op is one of {", ".join(MASK_OPS)}')
        if op == 'create':
            first, second = self.strand(args.get('first')), self.strand(args.get('second'))
            for s in self.window.canvas.strands:
                parts = (getattr(s, 'first_selected_strand', None), getattr(s, 'second_selected_strand', None))
                if hasattr(s, 'get_mask_path') and set(parts) == {first, second}:
                    raise BridgeError(f'{first.layer_name} and {second.layer_name} already have mask '
                                      f'{s.layer_name}: swap it or delete it first')
        else:
            self.mask(args.get('mask'))
        boxes = args.get('boxes')
        if op == 'erase' and (not isinstance(boxes, list) or not boxes):
            raise BridgeError('erase needs boxes')
        if boxes is not None and not isinstance(boxes, list):
            raise BridgeError('boxes is a list of erase boxes')
        if boxes:
            for box in boxes:
                try:
                    ok = all(len(box[k]) == 2 and all(isinstance(v, (int, float)) for v in box[k])
                             for k in ('top_left', 'top_right', 'bottom_left', 'bottom_right'))
                except (TypeError, KeyError):
                    ok = False
                if not ok:
                    raise BridgeError('an erase box gives its four corners: top_left, top_right, '
                                      'bottom_right, bottom_left')

    def strand(self, name):
        for s in self.window.canvas.strands:
            if s.layer_name == str(name or '') and not hasattr(s, 'get_mask_path'):
                return s
        raise BridgeError(f'there is no strand {name} in this tab')

    def mask(self, name):
        for s in self.window.canvas.strands:
            if s.layer_name == str(name or '') and hasattr(s, 'get_mask_path'):
                return s
        raise BridgeError(f'there is no mask {name} in this tab')

    def edit_mask(self, args, session):
        """The edit, with the canvas's own mask code, as one undo step."""
        canvas = self.window.canvas
        op, name = args['op'], args.get('mask')
        editing = getattr(canvas, 'editing_masked_strand', None)
        if getattr(canvas, 'mask_edit_mode', False) and editing is not None and editing.layer_name in (
                name, f"{args.get('first')}_{args.get('second')}"):
            canvas.exit_mask_edit_mode()  # the person was editing this mask: leave Edit Mask first
        if op == 'reset':
            mask = self.mask(name)
            canvas.reset_mask(canvas.strands.index(mask))  # Reset Mask, saved for undo by the canvas
            return {'tab_id': session.id, 'note': f'reset mask {name}'}
        if op == 'erase':
            mask = self.mask(name)
            for box in args['boxes']:
                mask.deletion_rectangles.append({k: (float(box[k][0]), float(box[k][1]))
                                                 for k in ('top_left', 'top_right', 'bottom_left', 'bottom_right')})
            mask.set_custom_mask(mask.get_mask_path())
            note = f"erased mask {name} with {len(args['boxes'])} box{'es' if len(args['boxes']) != 1 else ''}"
        elif op == 'delete':
            if not canvas.delete_masked_layer(self.mask(name)):
                raise BridgeError(f'mask {name} could not be deleted')
            note = f'deleted mask {name}'
        else:
            if op == 'swap':
                mask = self.mask(name)
                first, second = mask.second_selected_strand, mask.first_selected_strand
                if not canvas.delete_masked_layer(mask):
                    raise BridgeError(f'mask {name} could not be deleted')
            else:
                first, second = self.strand(args.get('first')), self.strand(args.get('second'))
            canvas.create_masked_layer(first, second)
            made = f'{first.layer_name}_{second.layer_name}'
            mask = next((s for s in canvas.strands if s.layer_name == made and hasattr(s, 'get_mask_path')), None)
            if mask is None:
                raise BridgeError(f'{first.layer_name} and {second.layer_name} do not cross: no mask made')
            note = f'{"swapped" if op == "swap" else "made"} mask {made}: {first.layer_name} on top'
            boxes = args.get('boxes') or []
            if boxes:  # trimmed where it would paint the wrong way, as Claude's copy is
                for box in boxes:
                    mask.deletion_rectangles.append({k: (float(box[k][0]), float(box[k][1]))
                                                     for k in ('top_left', 'top_right', 'bottom_left', 'bottom_right')})
                mask.set_custom_mask(mask.get_mask_path())
                note += f", erased with {len(boxes)} box{'es' if len(boxes) != 1 else ''} where it would paint the wrong way"
        canvas.update()
        manager = getattr(canvas, 'undo_redo_manager', None)
        if manager is not None:
            manager._last_save_time = 0
            manager.save_state(action=f'mask.claude_{op}', source='claude', targets=[name or args.get('first')])
        return {'tab_id': session.id, 'note': note}

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
        if call['name'] == 'edit_mask':
            args = call.get('args') or {}
            what = {'erase': f"erase part of mask {args.get('mask')}", 'reset': f"reset mask {args.get('mask')}",
                    'swap': f"swap mask {args.get('mask')}", 'delete': f"delete mask {args.get('mask')}",
                    'create': f"mask {args.get('first')} over {args.get('second')}"}[args['op']]
            return ('edit_mask', tm.title_for(session), what)
        if call['name'] == 'rename_tab':
            return ('rename_tab', tm.title_for(session), self.title((call.get('args') or {}).get('title')))
        return ('switch_tab', tm.title_for(session), '')
