"""The bridge between Claude and the running OpenStrand Studio.

Claude's agent runs in its own process (python -m openstrand agent --app) and
cannot reach the app's windows. When it calls one of its app tools it writes
a request line on stdout; the Claude panel hands it to AppBridge.handle here,
on the app's main thread, and writes the answer back to the agent's stdin
(see openstrand/app_tools.py for the other end).

Only the actions in ACTIONS exist, each a few lines over the app's own code:
the real TabManager, the same loader as Load, the canvas snapshot. What runs
follows the panel's mode:

- plan: Claude may look (list_tabs, read_tab, read_tab_step), nothing changes;
- ask: a design waits as a card the person opens; a rename, a switch, a
  mask or strand edit waits for the person's Allow or Deny in the conversation;
- auto: it happens.

Every tab has a version: a fingerprint of its strands and groups. read_tab
gives it, and an edit names the version it was worked out on; when the
person has changed the tab since, the edit is refused and Claude reads the
tab again, so it never edits a picture of the tab that is out of date.
"""
import hashlib
import json
import os

LOOK = {'list_tabs', 'read_tab', 'read_tab_step'}
CHANGE = {'open_in_new_tab', 'rename_tab', 'switch_tab', 'edit_mask', 'edit_strand'}
POINTS = ('start', 'end', 'control_point1', 'control_point2', 'control_point_center')
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
            if name in ('rename_tab', 'switch_tab', 'edit_mask', 'edit_strand'):
                session = self.session(args.get('tab_id'))
                if name in ('edit_mask', 'edit_strand'):
                    self.check_fresh(args, session)
                if name == 'edit_mask':
                    self.check_mask_edit(args, session)
                if name == 'edit_strand':
                    self.check_strand_edit(args, session)
                if mode == 'ask':
                    self.pending[call_id] = call
                    self.panel.add_confirm_card(call_id, self.describe(call, session))
                    return None
                return self.ok(call_id, self.do(call))
            if name == 'list_tabs':
                return self.ok(call_id, {'tabs': self.list_tabs()})
            if name == 'read_tab_step':
                return self.ok(call_id, self.read_tab_step(args.get('tab_id'), args.get('step')))
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
            history = self.history(session)
            out.append({'id': session.id, 'title': tm.title_for(session), 'active': active,
                        'strands': strands, 'unsaved': bool(session.dirty),
                        'version': self.version(session),
                        'undo_steps': history['max_step'], 'at_step': history['current_step']})
        return out

    # ----------------------------------------------------- versions, history
    def tab_data(self, session):
        """The tab's design now: the live canvas for the tab showing, else its kept state."""
        if session.id == self.tabs.active_tab_id:
            return self.window.claude_canvas_snapshot()
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
        """An edit worked out on the tab as Claude read it: refused if the tab changed since."""
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
        """One past (or undone) step of a tab, as a design file Claude reads. The tab is unchanged."""
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
        return {'file': path, 'title': tm.title_for(session), 'version': self.fingerprint(data),
                'history': self.history(session)}

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
        if name in ('edit_mask', 'edit_strand'):
            self.check_fresh(args, session)  # again: the person may have edited it while deciding
            if name == 'edit_mask':
                self.check_mask_edit(args, session)
                result = self.edit_mask(args, session)
            else:
                self.check_strand_edit(args, session)
                result = self.edit_strand(args, session)
            return dict(result, version=self.version(session))
        if name == 'rename_tab':
            title = self.title(args.get('title'))
            self.set_title(session, title)
            return {'tab_id': session.id, 'title': title, 'note': f'renamed to "{title}"'}
        if not self.tabs.switch_to_tab(session.id):
            raise BridgeError('the app could not switch tabs')
        return {'tab_id': session.id, 'title': self.tabs.title_for(session), 'note': 'switched'}

    # ------------------------------------------------------------- strands
    def check_strand_edit(self, args, session):
        """A strand edit moves points of one strand of the tab showing."""
        if session.id != self.tabs.active_tab_id:
            raise BridgeError(f'"{self.tabs.title_for(session)}" is not the tab showing: switch_tab to it first')
        strand = self.strand(args.get('strand'))
        points = args.get('points')
        if not isinstance(points, dict) or not points:
            raise BridgeError(f'points: which points to move and where, e.g. {{"control_point1": [x, y]}}; '
                              f'points are {", ".join(POINTS)}')
        for key, value in points.items():
            if key not in POINTS:
                raise BridgeError(f'{key} is not a point of a strand: {", ".join(POINTS)}')
            if not (isinstance(value, (list, tuple)) and len(value) == 2
                    and all(isinstance(v, (int, float)) for v in value)):
                raise BridgeError(f'{key}: give [x, y]')
        canvas = self.window.canvas
        if 'control_point_center' in points and not getattr(canvas, 'enable_third_control_point', False):
            raise BridgeError('the third control point is off in Settings: move control_point1 and control_point2')
        # Move mode's own rules for what a drag may move.
        move = canvas.move_mode
        if getattr(move, 'is_moving', False):
            raise BridgeError('the person is dragging a strand right now: try again once they let go')
        if getattr(canvas, 'mask_edit_mode', False):
            raise BridgeError('Edit Mask is on in the tab: ask the person to leave it first')
        if getattr(strand, 'is_hidden', False):
            raise BridgeError(f'{strand.layer_name} is hidden in the layer panel: it must be shown first')
        index = canvas.strands.index(strand)
        for key in points:
            side = {'start': 0, 'end': 1}.get(key, 'control_point1')  # every handle follows the control points' rule
            if not move.can_move_side(strand, side, index):
                raise BridgeError(f'{strand.layer_name}: its {key} cannot move: the strand, or a strand sharing '
                                  'that point, is locked in the layer panel (lock mode)')

    def edit_strand(self, args, session):
        """Move points of one strand with Move mode's own code, as a drag does:
        strands attached at a moved end follow, erase boxes follow their
        crossing. One undo step."""
        from PyQt5.QtCore import QPointF
        canvas = self.window.canvas
        strand = self.strand(args.get('strand'))
        move = canvas.move_mode
        # A move deselects the strand it moves: the person's selection, to put back after.
        selection = (canvas.selected_strand, canvas.selected_attached_strand,
                     [(s, s.is_selected) for s in canvas.strands])
        sides = {'start': 0, 'end': 1}
        # Ends first, then the handles, so a handle lands where it is asked even if an end moved.
        order = sorted(args['points'], key=lambda k: 0 if k in sides else 1)
        try:
            for key in order:
                x, y = args['points'][key]
                if key == 'control_point_center':
                    strand.control_point_center_locked = True
                if key == 'control_point2' and hasattr(strand, 'control_point2_shown'):
                    strand.control_point2_shown = True
                side = sides.get(key, key)
                move.affected_strand, move.moving_side = strand, side
                # As a drag starts (start_movement): which strands meet at the moved point,
                # from connections taken from the strands as they are now.
                manager = getattr(canvas, 'layer_state_manager', None)
                if manager is not None:
                    manager.save_current_state()
                move.build_connection_cache()
                moving = move.gather_moving_strands(strand, side) if side in (0, 1) else [strand]
                canvas.truly_moving_strands = moving
                move._box_anchors = move._capture_box_anchors([strand] + list(moving))
                move.update_strand_position(QPointF(float(x), float(y)))
                for masked in move._box_anchors or {}:
                    masked.calculate_center_point()
        finally:
            # Ended as a mouse release ends a drag: the app's own reset clears what the move
            # left on the canvas (the moving strands, drawing caches, the connection cache),
            # then the selection comes back as it was before.
            move.reset_movement_state()
            for one, was in selection[2]:
                one.is_selected = was
            canvas.selected_strand, canvas.selected_attached_strand = selection[0], selection[1]
        canvas.update()
        manager = getattr(canvas, 'undo_redo_manager', None)
        if manager is not None:
            manager._last_save_time = 0
            manager.save_state(action='strand.claude_move', source='claude', targets=[strand.layer_name])
        p = lambda q: [round(q.x(), 1), round(q.y(), 1)]
        now = {k: p(getattr(strand, k)) for k in POINTS if getattr(strand, k, None) is not None}
        return {'tab_id': session.id, 'strand': strand.layer_name, 'now': now,
                'note': f'moved {", ".join(order)} of {strand.layer_name}'}

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
        if call['name'] == 'edit_strand':
            args = call.get('args') or {}
            return ('edit_strand', tm.title_for(session),
                    f"{args.get('strand')}: {', '.join((args.get('points') or {}).keys())}")
        if call['name'] == 'rename_tab':
            return ('rename_tab', tm.title_for(session), self.title((call.get('args') or {}).get('title')))
        return ('switch_tab', tm.title_for(session), '')
