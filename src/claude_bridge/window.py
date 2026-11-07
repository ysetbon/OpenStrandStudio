"""The main window: the toolbar, the round buttons beside the canvas and the
buttons under the layer panel, run with the window's own code on the tab
showing. Where a button asks first (Delete All) or opens a file dialog (Save,
Image), the question is answered with Claude's request and the button's own
code runs on, as when the person answers.

window_view ops (the view only, the design does not change; in every mode):
  zoom       value "in" / "out" (the zoom buttons, steps clicks), "reset" (100 %), "fit"
             (the whole design, or the layers given), or a percent 10..500
  center     the target button: the design, or the layers given, in the middle of the view
  grid       value true/false: the Grid button
  names      value true/false: Draw Names
  tabs       value true/false: the Tabs button (the tab edge shown)
  layer_tab  value "strands" / "masks": the switch under the layer panel
  mode       value view/select/attach/move/rotate: the toolbar's mode buttons
  select     layer: a click on its layer button
  deselect   Deselect All (in lock mode too, where that button clears the locks instead)
window ops (change the tab; saved in the undo history as the buttons save them):
  undo, redo      steps (1 by default)
  points          value true/false: the Points button (control points shown)
  shadow          value true/false: the Shadow button
  new_strand      start [x, y], end [x, y] in canvas px: New Strand, drawn from start to end
  delete          layers [names]: Delete Strand / Delete Mask on each (n_1 takes its whole set)
  delete_all      value "strands" / "masks": Delete All on that tab, answered Yes
  new_level       New Level
  lock            value true with layers [the layers locked] (lock mode on), or false (off)
  reset_history   the home button: the undo history keeps only the tab as it is now
window_file ops (write a file of the tab showing):
  save            path (.json; the tab's own file by default), overwrite: the Save button
  save_image      path (.png), overwrite: the Image button (the view as it shows, at 4x)
"""
import os

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from .base import Action, BridgeError, patched

VIEW_OPS = ('zoom', 'center', 'grid', 'names', 'tabs', 'layer_tab', 'mode', 'select', 'deselect')
EDIT_OPS = ('undo', 'redo', 'points', 'shadow', 'new_strand', 'delete', 'delete_all', 'new_level', 'lock',
            'reset_history')
FILE_OPS = ('save', 'save_image')
MODES = ('view', 'select', 'attach', 'move', 'rotate')
DEFERRED = {'new_strand'}  # the app saves their undo step a moment later
MARGIN = 60  # px kept around what a fit shows, as the app's own fit leaves it
MASK_EDIT = 'Edit Mask is on in the tab: ask the person to leave it (Esc) first'


def answer_yes(box):
    """QMessageBox.exec_ answered Yes: the box's Yes button clicked, the box never shown."""
    for button in box.buttons():
        if box.buttonRole(button) == QMessageBox.YesRole:
            button.click()
            break
    return 0


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def point(value):
    return isinstance(value, (list, tuple)) and len(value) == 2 and all(number(v) for v in value)


class WindowActions:
    ACTIONS = {
        'window_view': Action(run='window_view', check='check_window_view'),
        'window': Action(run='window_edit', change=True, tab=True, edits=True, check='check_window_edit',
                         card='window_card'),
        'window_file': Action(run='window_file', change=True, tab=True, check='check_window_file',
                              card='window_card'),
    }

    # ---------------------------------------------------------- lookups
    @property
    def undo_manager(self):
        manager = getattr(self.canvas, 'undo_redo_manager', None)
        if manager is None:
            raise BridgeError('this window has no undo history')
        return manager

    def index_of(self, name):
        return self.canvas.strands.index(self.layer(name))

    def view_state(self):
        """What the person sees: zoom, toggles, mode, selection, locks."""
        canvas, panel = self.canvas, self.layer_panel
        selected = getattr(canvas, 'selected_strand', None)
        edge = getattr(self.window, 'tab_edge', None)
        locked = sorted(getattr(panel, 'locked_layers', ()) or ())
        return {
            'zoom': round(canvas.zoom_factor * 100),
            'grid': bool(getattr(canvas, 'show_grid', False)),
            'names': bool(getattr(canvas, 'should_draw_names', False)),
            'points': bool(getattr(canvas, 'show_control_points', False)),
            'shadow': bool(getattr(canvas, 'shadow_enabled', False)),
            'tabs': bool(edge is not None and edge.isVisible()),
            'layer_tab': getattr(panel, 'layer_tab', 'strands'),
            'mode': getattr(self.window, 'current_mode', None),
            'selected': getattr(selected, 'layer_name', None),
            'lock_mode': bool(getattr(panel, 'lock_mode', False)),
            'locked': [canvas.strands[i].layer_name for i in locked if i < len(canvas.strands)],
        }

    def layers_box(self, names):
        """The box around layers, as the target button measures strands (ends and handles)."""
        xs, ys = [], []
        for name in names:
            layer = self.layer(name)
            if hasattr(layer, 'get_mask_path'):
                rect = layer.get_mask_path().boundingRect()
                xs += [rect.left(), rect.right()]
                ys += [rect.top(), rect.bottom()]
                continue
            for p in (layer.start, layer.end, getattr(layer, 'control_point1', None),
                      getattr(layer, 'control_point2', None)):
                if p is not None:
                    xs.append(p.x())
                    ys.append(p.y())
        if not xs:
            raise BridgeError('those layers have no points to show')
        return min(xs), min(ys), max(xs), max(ys)

    def center_on(self, box):
        """The box in the middle of the view: the target button's own formula."""
        canvas = self.canvas
        x0, y0, x1, y1 = box
        canvas.pan_offset_x = (canvas.width() / 2 - (x0 + x1) / 2) * canvas.zoom_factor
        canvas.pan_offset_y = (canvas.height() / 2 - (y0 + y1) / 2) * canvas.zoom_factor
        canvas.update_canvas_bounds()

    def check_panel_free(self):
        """The person is not in the middle of something these buttons would break."""
        if getattr(self.canvas, 'mask_edit_mode', False) or getattr(self.layer_panel, 'mask_editing', False):
            raise BridgeError(MASK_EDIT)
        if getattr(self.layer_panel, 'masked_mode', False):
            raise BridgeError('the person is making a mask (Ctrl held): try again after')

    # ------------------------------------------------------------ cards
    def window_card(self, args, session):
        op = args.get('op')
        names = ', '.join(map(str, args.get('layers') or []))
        steps = args.get('steps') or 1
        what = {
            'undo': f'undo {steps} step{"s" if steps != 1 else ""}',
            'redo': f'redo {steps} step{"s" if steps != 1 else ""}',
            'points': f'{"show" if args.get("value") else "hide"} the control points',
            'shadow': f'turn shadows {"on" if args.get("value") else "off"}',
            'new_strand': f'draw a new strand from {tuple(args.get("start") or ())} to {tuple(args.get("end") or ())}',
            'delete': f'delete {names}',
            'delete_all': f'delete all {args.get("value")}',
            'new_level': 'add a new level',
            'lock': (f'turn lock mode on and lock {names or "no layers"}' if args.get('value')
                     else 'leave lock mode'),
            'reset_history': 'clear the undo history, keeping only the tab as it is now',
            'save': f'save the tab to {self.save_path(args, session)}',
            'save_image': f'save the view as an image to {self.image_path(args)}',
        }.get(op, str(op))
        return 'window', self.tabs.title_for(session), what

    # ----------------------------------------------------------- checks
    def check_window_view(self, args, session):
        op = args.get('op')
        if op not in VIEW_OPS:
            raise BridgeError(f'op is one of {", ".join(VIEW_OPS)}')
        if args.get('tab_id'):
            self.require_showing(self.session(args['tab_id']))
        if op not in ('zoom', 'center'):
            self.check_panel_free()
        value = args.get('value')
        if op == 'zoom':
            if not (value in ('in', 'out', 'reset', 'fit') or number(value)):
                raise BridgeError('zoom: value "in", "out", "reset", "fit" or a percent (10..500)')
            if number(value) and not 10 <= value <= 500:
                raise BridgeError('zoom: a percent from 10 to 500')
            steps = args.get('steps', 1)
            if not (isinstance(steps, int) and not isinstance(steps, bool) and 1 <= steps <= 30):
                raise BridgeError('zoom: steps, a whole number from 1 to 30')
        if op in ('zoom', 'center'):
            for name in args.get('layers') or []:
                self.layer(name)
        if op in ('grid', 'names', 'tabs') and not isinstance(value, bool):
            raise BridgeError(f'{op}: value true or false')
        if op == 'layer_tab' and value not in ('strands', 'masks'):
            raise BridgeError('layer_tab: value "strands" or "masks"')
        if op == 'mode' and value not in MODES:
            raise BridgeError(f'mode: value one of {", ".join(MODES)}')
        if op == 'select':
            self.layer(args.get('layer'))

    def check_window_edit(self, args, session):
        op = args.get('op')
        if op not in EDIT_OPS:
            raise BridgeError(f'op is one of {", ".join(EDIT_OPS)}')
        self.check_panel_free()
        canvas, panel, value = self.canvas, self.layer_panel, args.get('value')
        if op in ('undo', 'redo'):
            manager, steps = self.undo_manager, args.get('steps', 1)
            if not (isinstance(steps, int) and not isinstance(steps, bool) and steps >= 1):
                raise BridgeError(f'{op}: steps, a whole number from 1')
            if op == 'undo' and manager.current_step <= 0:
                raise BridgeError('nothing to undo: the tab is at the start of its history')
            if op == 'redo' and manager.current_step >= manager.max_step:
                raise BridgeError('nothing to redo: the tab is at the newest step of its history')
        if op in ('points', 'shadow', 'lock') and not isinstance(value, bool):
            raise BridgeError(f'{op}: value true or false')
        if op == 'new_strand':
            for key in ('start', 'end'):
                if not point(args.get(key)):
                    raise BridgeError(f'new_strand: {key} [x, y] in canvas px')
            if list(args['start']) == list(args['end']):
                raise BridgeError('new_strand: start and end are the same point')
        if op == 'delete':
            names = args.get('layers')
            if not (isinstance(names, list) and names):
                raise BridgeError('delete: layers, e.g. ["1_3"]')
            if getattr(panel, 'multi_select_mode', False):
                raise BridgeError('multi-select is on in the layer panel (Delete Strand would delete the layers the '
                                  'person picked there): ask them to leave it first')
            for name in names:
                layer, index = self.layer(name), self.index_of(name)
                if panel.lock_mode and index in panel.locked_layers:
                    raise BridgeError(f'{name} is locked: unlock it first (op lock)')
                if not hasattr(layer, 'get_mask_path') and not panel.is_strand_deletable(layer):
                    raise BridgeError(f'{name} cannot be deleted: strands are attached at both its ends (the app '
                                      'deletes a strand with a free end, or one joined by Close the Knot)')
        if op == 'delete_all':
            if value not in ('strands', 'masks'):
                raise BridgeError('delete_all: value "strands" (every layer) or "masks"')
            if value == 'masks' and not any(hasattr(s, 'get_mask_path') for s in canvas.strands):
                raise BridgeError('there are no masks in this tab')
            if value == 'strands' and not canvas.strands:
                raise BridgeError('the tab is empty')
        if op == 'lock' and value:
            names = args.get('layers', [])
            if not isinstance(names, list):
                raise BridgeError('lock: layers, the layers locked, e.g. ["1_1", "2_1"] ([] for none)')
            for name in names:
                self.layer(name)

    def save_path(self, args, session):
        path = args.get('path') or getattr(session, 'file_path', None) or ''
        return os.path.normpath(str(path)) if path else ''

    @staticmethod
    def image_path(args):
        path = str(args.get('path') or '')
        if path and not path.lower().endswith('.png'):
            path += '.png'  # as the Image button adds it
        return os.path.normpath(path) if path else ''

    def check_window_file(self, args, session):
        op = args.get('op')
        if op not in FILE_OPS:
            raise BridgeError(f'op is one of {", ".join(FILE_OPS)}')
        self.require_showing(session)
        path = self.save_path(args, session) if op == 'save' else self.image_path(args)
        if not path:
            raise BridgeError(f'{op}: path, a full path' + (' ending in .json (the tab has no file of its own yet)'
                                                            if op == 'save' else ' ending in .png'))
        if op == 'save' and not path.lower().endswith('.json'):
            raise BridgeError('save: a path ending in .json')
        if not os.path.isabs(path):
            raise BridgeError(f'{op}: a full path (with its folder), not {path}')
        folder = os.path.dirname(path)
        if not os.path.isdir(folder):
            raise BridgeError(f'there is no folder {folder}')
        own = (op == 'save' and getattr(session, 'file_path', None)
               and os.path.normcase(os.path.abspath(session.file_path)) == os.path.normcase(path))
        if os.path.exists(path) and not own and not args.get('overwrite'):
            raise BridgeError(f'{path} exists: give overwrite true to replace it, or another name')

    # -------------------------------------------------------------- run
    def window_view(self, args, session):
        op = args['op']
        note = getattr(self, f'view_{op}')(args)
        self.canvas.update()
        return {'op': op, 'note': note or 'nothing to change: already so', 'view': self.view_state()}

    def window_edit(self, args, session):
        op = args['op']
        manager = self.undo_manager
        before = manager.current_step
        note = getattr(self, f'edit_{op}')(args)
        if note and op in DEFERRED:
            self.settle(before)
        self.canvas.update()
        result = {'tab_id': session.id, 'op': op, 'note': note or 'nothing to change: already so',
                  'view': self.view_state(), 'step': manager.current_step, 'steps': manager.max_step}
        if note and op not in ('undo', 'redo', 'reset_history') and manager.current_step == before:
            # Some saves come from wrappers the app installs once it has started: until
            # then, and where the button saves nothing, save the step here.
            self.save_undo(f'window.{op}', [str(n) for n in args.get('layers') or []])
            result['step'], result['steps'] = manager.current_step, manager.max_step
            if manager.current_step == before:
                result['undo'] = 'the app keeps no undo step for this (as when the person clicks it)'
        return result

    def window_file(self, args, session):
        op = args['op']
        path = self.save_path(args, session) if op == 'save' else self.image_path(args)
        when = os.path.getmtime(path) if os.path.exists(path) else None
        answer = staticmethod(lambda *a, **k: (path, 'JSON Files (*.json)' if op == 'save' else 'PNG Files (*.png)'))
        with patched(QFileDialog, 'getSaveFileName', answer):
            if op == 'save':
                written = self.window.save_project()
            else:
                self.window.save_canvas_as_image()
                written = os.path.exists(path) and os.path.getmtime(path) != when
        if not written:
            raise BridgeError(f'the app could not write {path}')
        if op == 'save':
            note = f'saved the tab to {path} (the tab is that file now, saved)'
        else:
            image = QImage(path)
            note = f'saved the view as {path} ({image.width()} x {image.height()} px)'
        return {'tab_id': session.id, 'op': op, 'path': path, 'note': note}

    # view
    def view_zoom(self, args):
        canvas, value = self.canvas, args['value']
        before = canvas.zoom_factor
        if value in ('in', 'out'):
            for _ in range(int(args.get('steps') or 1)):
                (canvas.zoom_in if value == 'in' else canvas.zoom_out)()
        elif value == 'reset':
            canvas.reset_zoom()
        elif value == 'fit':
            if args.get('layers'):
                x0, y0, x1, y1 = box = self.layers_box(args['layers'])
                fit = min((canvas.width() - MARGIN) / max(x1 - x0, 1.0), (canvas.height() - MARGIN) / max(y1 - y0, 1.0))
                canvas.zoom_factor = max(canvas.min_zoom, min(canvas.max_zoom, fit))
                self.center_on(box)
            else:
                self.window.fit_design_in_view()  # zooms out until it all shows (never in), then centers
        else:
            # A percent, about the middle of the view: what is there stays there
            factor = max(canvas.min_zoom, min(canvas.max_zoom, value / 100.0))
            scale = factor / canvas.zoom_factor
            canvas.pan_offset_x *= scale
            canvas.pan_offset_y *= scale
            canvas.zoom_factor = factor
            canvas.update_canvas_bounds()
        now = round(canvas.zoom_factor * 100)
        if value in ('in', 'out') and canvas.zoom_factor == before:
            return f'the zoom stays at {now} %: the limit'
        return f'zoom {now} %' + (', centered' if value == 'fit' else '')

    def view_center(self, args):
        if args.get('layers'):
            self.center_on(self.layers_box(args['layers']))
            return f"{', '.join(args['layers'])} in the middle of the view"
        if not self.canvas.strands:
            return None
        self.layer_panel.center_all_strands()
        return 'the design in the middle of the view'

    def view_grid(self, args):
        if bool(self.canvas.show_grid) == args['value']:
            return None
        self.window.toggle_grid_button.click()
        if bool(self.canvas.show_grid) != args['value']:
            raise BridgeError('the Grid button cannot be used now')
        return f"grid {'shown' if args['value'] else 'hidden'}"

    def view_names(self, args):
        panel = self.layer_panel
        if bool(panel.should_draw_names) == args['value']:
            return None
        panel.request_draw_names()
        return f"layer names {'drawn on' if args['value'] else 'off'} the canvas"

    def view_tabs(self, args):
        edge = getattr(self.window, 'tab_edge', None)
        if edge is None:
            raise BridgeError('this window has no tab edge')
        if edge.isVisible() == args['value']:
            return None
        self.window.toggle_tabs_edge()
        return f"tab edge {'shown' if args['value'] else 'hidden'}"

    def view_layer_tab(self, args):
        panel = self.layer_panel
        if panel.layer_tab == args['value']:
            return None
        (panel.strands_tab_button if args['value'] == 'strands' else panel.masks_tab_button).click()
        return f"the layer panel shows the {args['value']}"

    def view_mode(self, args):
        getattr(self.window, f"set_{args['value']}_mode")()
        return f"{args['value']} mode"

    def view_select(self, args):
        layer = self.layer(args['layer'])
        self.layer_panel.select_layer(self.canvas.strands.index(layer))
        return f'selected {layer.layer_name}'

    def view_deselect(self, args):
        panel = self.layer_panel
        if panel.lock_mode:
            with patched(panel, 'lock_mode', False):  # the button's Deselect All, not Clear All Locks
                panel.deselect_all()
        else:
            panel.deselect_all()
        return 'nothing selected'

    # edits
    def edit_undo(self, args):
        return self.step_through(args, back=True)

    def edit_redo(self, args):
        return self.step_through(args, back=False)

    def step_through(self, args, back):
        manager = self.undo_manager
        start = manager.current_step
        for _ in range(int(args.get('steps') or 1)):
            if manager.current_step <= 0 if back else manager.current_step >= manager.max_step:
                break
            here = manager.current_step
            manager.undo() if back else manager.redo()
            if manager.current_step == here:
                break
        return (f"{'undo' if back else 'redo'}: from step {start} to step {manager.current_step} "
                f'of {manager.max_step}')

    def edit_points(self, args):
        if bool(self.canvas.show_control_points) == args['value']:
            return None
        self.window.toggle_control_points_button.setChecked(args['value'])
        self.window.on_toggle_control_points_button_clicked(args['value'])  # what the click runs
        return f"control points {'shown' if args['value'] else 'hidden'}"

    def edit_shadow(self, args):
        if bool(self.canvas.shadow_enabled) == args['value']:
            return None
        self.canvas.toggle_shadow()
        self.window.toggle_shadow_button.setChecked(bool(self.canvas.shadow_enabled))
        return f"shadows {'on' if args['value'] else 'off'}"

    def edit_new_strand(self, args):
        canvas, panel = self.canvas, self.layer_panel
        panel.request_new_strand()  # New Strand: a free set number, drawing on
        canvas.new_strand_start_point = QPointF(*map(float, args['start']))
        canvas.new_strand_end_point = QPointF(*map(float, args['end']))
        canvas.finalize_new_strand()  # what releasing the mouse does (then attach mode)
        name = f'{panel.current_set}_1'
        strand = next((s for s in canvas.strands if s.layer_name == name), None)
        if strand is None:
            raise BridgeError('the new strand could not be made')
        return (f'drew {name} from ({strand.start.x():g}, {strand.start.y():g}) '
                f'to ({strand.end.x():g}, {strand.end.y():g})')

    def edit_delete(self, args):
        canvas, panel = self.canvas, self.layer_panel
        before = [s.layer_name for s in canvas.strands]
        for name in args['layers']:
            layer = next((s for s in canvas.strands if s.layer_name == str(name)), None)
            if layer is None:
                continue  # it went with its set
            panel.select_layer(canvas.strands.index(layer), emit_signal=False)
            panel.request_delete_strand()
        left = {s.layer_name for s in canvas.strands}
        gone = [n for n in before if n not in left]
        if not gone:
            raise BridgeError('nothing was deleted')
        return f"deleted {', '.join(gone)}"

    def edit_delete_all(self, args):
        canvas, panel = self.canvas, self.layer_panel
        if args['value'] == 'masks':
            count = sum(1 for s in canvas.strands if hasattr(s, 'get_mask_path'))
            with patched(panel, '_ask_yes_no', lambda title, text: True):
                panel.request_delete_all_masks()
            return f'deleted all {count} masks'
        count = len(canvas.strands)
        with patched(QMessageBox, 'exec_', answer_yes):
            panel.request_delete_all()
        if canvas.strands:
            raise BridgeError('the layers could not be deleted')
        return f'deleted all {count} layers (groups are kept, as the button keeps them)'

    def edit_new_level(self, args):
        self.layer_panel.request_new_level()
        return f'added level {self.canvas.level_count}: the strands made or attached next go on it'

    def edit_lock(self, args):
        panel = self.layer_panel
        if not args['value']:
            if not panel.lock_mode:
                return None
            panel.lock_layers_button.click()
            return 'left lock mode (the app keeps the locks for the next time it is on)'
        want = {self.index_of(n) for n in args.get('layers') or []}
        if panel.lock_mode and set(panel.locked_layers) == want:
            return None
        if not panel.lock_mode:
            panel.lock_layers_button.click()
            if not panel.lock_mode:
                raise BridgeError('the Lock Layers button cannot be used now')
        for index in sorted(set(panel.locked_layers) ^ want):
            panel.toggle_layer_lock(index)
        locked = [self.canvas.strands[i].layer_name for i in sorted(panel.locked_layers)]
        return f"lock mode on; locked: {', '.join(locked) or 'none'}"

    def edit_reset_history(self, args):
        manager = self.undo_manager
        self.layer_panel.reset_to_current_state()
        return f'the undo history now starts at the tab as it is (step {manager.current_step})'
