"""What the main window's buttons do in the person's app: the toolbar, the round
buttons beside the canvas and the buttons under the layer panel, done with the
window's own code (src/agent_bridge/window.py). After a change the tab is read
back, so the agent's copy is the tab again."""
from .. import project
from ..errors import ToolError
from .strands import require_read
from .tabs import read_into_workspace

VIEW_OPS = ('zoom', 'center', 'grid', 'names', 'tabs', 'layer_tab', 'mode', 'select', 'deselect')
EDIT_OPS = ('undo', 'redo', 'points', 'shadow', 'new_strand', 'delete', 'delete_all', 'new_level', 'lock',
            'reset_history')
FILE_OPS = ('save', 'save_image')
OPS = VIEW_OPS + EDIT_OPS + FILE_OPS
KEYS = ('value', 'steps', 'layers', 'layer', 'start', 'end', 'path', 'overwrite')

TOOLS = [
    {
        'name': 'app_window',
        'description': (
            "Use the buttons of the person's main window, with the app's own code, on the tab showing: the "
            'toolbar, the round buttons beside the canvas and the buttons under the layer panel.\n'
            'View ops change only what the person sees (no undo step, no need to read the tab):\n'
            '- zoom: value "in" / "out" (the zoom buttons; steps: how many clicks), "reset" (100 %), "fit" (the '
            'whole design, or layers [names] up close), or a percent 10..500.\n'
            '- center: the design, or layers [names], in the middle of the view.\n'
            '- grid, names (Draw Names: layer names on the canvas), tabs (the tab edge): value true/false.\n'
            '- layer_tab: value "strands" or "masks" (the layer panel\'s switch). mode: value view / select / '
            'attach / move / rotate (the toolbar\'s modes).\n'
            '- select: layer (as a click on its layer button). deselect: nothing selected.\n'
            'Edit ops change the tab: read_tab it first (tab_id); in ask mode the person allows it first; each is '
            'saved in the undo history as the button saves it:\n'
            '- undo / redo: steps (1 by default).\n'
            '- points (control points shown) / shadow (shadows drawn): value true/false.\n'
            '- new_strand: start [x, y], end [x, y] in canvas px: a new set (n_1), as New Strand drawn by hand.\n'
            '- delete: layers [names] (Delete Strand / Delete Mask: n_1 takes its whole set; the app deletes a '
            'strand only with a free end). delete_all: value "strands" (every layer) or "masks".\n'
            '- new_level: New Level (the strands made or attached next go on it).\n'
            '- lock: value true with layers [the layers locked] (lock mode on: locked layers cannot be selected '
            'or moved), or value false (lock mode off).\n'
            '- reset_history: the undo history keeps only the tab as it is now. The person loses their undo '
            'steps: only when they ask for it.\n'
            'File ops write a file of the tab showing:\n'
            '- save: path, a full path ending in .json (the tab\'s own file if it has one); the tab saved with its '
            'history, as the Save button does. overwrite true to replace another file.\n'
            '- save_image: path, a full .png path: the view as it shows (zoom it first), at 4x, as the Image '
            'button. overwrite true to replace a file.'),
        'input_schema': {'type': 'object', 'properties': {
            'op': {'type': 'string', 'enum': list(OPS)},
            'tab_id': {'type': 'string', 'description': 'from list_tabs (the tab showing); edit and file ops need it'},
            'value': {'description': 'what the op takes (see above)'},
            'steps': {'type': 'integer'},
            'layers': {'type': 'array', 'items': {'type': 'string'}},
            'layer': {'type': 'string'},
            'start': {'type': 'array', 'items': {'type': 'number'}},
            'end': {'type': 'array', 'items': {'type': 'number'}},
            'path': {'type': 'string'},
            'overwrite': {'type': 'boolean'},
        }, 'required': ['op']},
    },
]
LOOK_ONLY = set()

INSTRUCTIONS = """- The main window's buttons (zoom, center, grid, layer names, modes, select,
  undo and redo, control points, shadows, new strand, delete, levels, locks,
  save, image) go through app_window: use them on the person's app rather than
  telling them the clicks. To show the person a part of the design, zoom "fit"
  on those layers instead of describing where it is.
"""


def view_text(view):
    """The view as a line: zoom, toggles, mode, selection, locks."""
    if not view:
        return ''
    on = lambda key: 'on' if view.get(key) else 'off'  # noqa: E731
    bits = [f"zoom {view.get('zoom')} %", f"grid {on('grid')}", f"names {on('names')}", f"points {on('points')}",
            f"shadow {on('shadow')}", f"{view.get('mode')} mode", f"layer panel: {view.get('layer_tab')}",
            f"selected {view.get('selected') or 'nothing'}"]
    if view.get('lock_mode'):
        bits.append(f"lock mode on (locked: {', '.join(view.get('locked') or []) or 'none'})")
    return ', '.join(bits)


def app_window(agent, args):
    op = str(args.get('op', ''))
    if op not in OPS:
        raise ToolError(f'op is one of {", ".join(OPS)}')
    call = {'op': op}
    call.update({k: args[k] for k in KEYS if k in args})
    tab = str(args.get('tab_id') or '')
    if op in VIEW_OPS:
        if tab:
            call['tab_id'] = tab
        result = agent.app.call('window_view', call)
        note = result.get('note', op)
        return f'App · {note[:70]}', f"{note}.\nThe view now: {view_text(result.get('view'))}."
    if not tab:
        raise ToolError(f'{op}: tab_id, the tab showing (list_tabs)')
    call['tab_id'] = tab
    if op in FILE_OPS:
        result = agent.app.call('window_file', call)
        if 'path' not in result:  # ask mode: the person decides; nothing written yet
            return f'{op} · waiting for the person', result.get('note') or 'shown to the person'
        return f"App · {result.get('note', op)[:70]}", result.get('note', 'done')
    require_read(agent, tab)
    call['version'] = agent.workspace.tab_version
    result = agent.app.call('window', call)
    if 'version' not in result:  # ask mode: the person decides; nothing changed yet
        return f'{op} · waiting for the person', result.get('note') or 'shown to the person'
    fresh, data = read_into_workspace(agent, tab)
    lines = [f"{result.get('note', 'done')} in the tab."]
    if result.get('undo'):
        lines.append(f"Note: {result['undo']}.")
    lines.append(f"Undo history: at step {result.get('step')} of {result.get('steps')}.")
    lines.append(f"The view now: {view_text(result.get('view'))}.")
    lines.append(f"The tab is the current design again (version {fresh.get('version')}): {project.summary(data)}")
    return f"App · {result.get('note', op)[:70]}", '\n'.join(lines)


HANDLERS = {'app_window': app_window}
