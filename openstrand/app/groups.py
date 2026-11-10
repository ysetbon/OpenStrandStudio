"""What the group panel does, on groups of the person's tab: done in the app with
the panel's own code (src/agent_bridge/groups.py), then the tab is read back."""
from .. import identify
from ..errors import ToolError
from .strands import require_read
from .tabs import read_into_workspace

EDIT_OPS = ('create', 'rename', 'delete', 'move', 'snap', 'rotate', 'angles', 'shadow', 'mask_grid', 'duplicate')

TOOLS = [
    {
        'name': 'edit_groups_in_tab',
        'description': (
            "Do what the group panel does, on the person's tab, with the app's own code (one undo step each; in "
            'ask mode the person allows it first). The tab must be the one showing and read with read_tab since '
            'its last change; read_tab lists the groups and their sets. A group holds whole sets (a set: one '
            'cord, n_1 and the strands attached to it). ops:\n'
            '- create: group (a name), sets ["1", "3"] (sets that share a mask come along, as in the app); '
            'replace true to replace a group of that name.\n'
            '- rename: group, new_name. delete: group (its strands stay). duplicate: group (the copy sits on the '
            'original with new set numbers: move it after).\n'
            '- move: group, dx and dy in canvas px, or grid_steps [x, y]; snap true snaps the strand ends to the '
            'grid after. snap: snap the strand ends to the grid.\n'
            '- rotate: group, angle in degrees (positive turns clockwise on screen) about the group\'s middle.\n'
            '- angles: group, angles {layer: degrees} for strands attached with one end free (their length '
            'stays; 0 points right, 90 down).\n'
            '- shadow: group, receivers [layer names] or "below" (every layer under each of its strands), with '
            'visible true/false, full_shadow true/false (layers between do not block), subtract [layer names].\n'
            '- mask_grid: group, pairs [[first, second], ...] (first on top) of its strands that cross. The app '
            'then removes the group (it removes a group whenever a mask touches its sets): create it again '
            'after if it should stay.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'op': {'type': 'string', 'enum': list(EDIT_OPS)},
            'group': {'type': 'string'},
            'sets': {'type': 'array', 'items': {'type': 'string'}},
            'replace': {'type': 'boolean'},
            'new_name': {'type': 'string'},
            'dx': {'type': 'number'}, 'dy': {'type': 'number'},
            'grid_steps': {'type': 'array', 'items': {'type': 'number'}},
            'snap': {'type': 'boolean'},
            'angle': {'type': 'number'},
            'angles': {'type': 'object'},
            'receivers': {'description': '[layer names] or "below"'},
            'visible': {'type': 'boolean'}, 'full_shadow': {'type': 'boolean'},
            'subtract': {'type': 'array', 'items': {'type': 'string'}},
            'pairs': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'string'}}},
        }, 'required': ['tab_id', 'op', 'group']},
    },
    {
        'name': 'show_group',
        'description': ("Show the person something in the group panel, changing nothing in the design: op "
                        '"focus" scrolls to a group and flashes it; op "panel" with collapsed true/false folds or '
                        'opens the group column.'),
        'input_schema': {'type': 'object', 'properties': {
            'op': {'type': 'string', 'enum': ['focus', 'panel']},
            'group': {'type': 'string'}, 'collapsed': {'type': 'boolean'},
        }, 'required': ['op']},
    },
]
LOOK_ONLY = set()

INSTRUCTIONS = """- Groups (the group panel: create, rename, delete, move, rotate, strand angles,
  shadows, mask grid, duplicate) go through edit_groups_in_tab. A group has no
  color or visibility of its own: change its strands with edit_layers_in_tab.
"""

KEYS = ('sets', 'replace', 'new_name', 'dx', 'dy', 'grid_steps', 'snap', 'angle', 'angles', 'receivers', 'visible',
        'full_shadow', 'subtract', 'pairs')


def edit_groups_in_tab(agent, args):
    tab, op = str(args.get('tab_id', '')), str(args.get('op', ''))
    require_read(agent, tab)
    if op not in EDIT_OPS:
        raise ToolError(f'op is one of {", ".join(EDIT_OPS)}')
    call = {'tab_id': tab, 'op': op, 'group': str(args.get('group') or ''), 'version': agent.workspace.tab_version}
    call.update({k: args[k] for k in KEYS if k in args})
    result = agent.app.call('edit_groups', call)
    if 'version' not in result:  # ask mode: the person decides; nothing changed yet
        return f'{op} · waiting for the person', result.get('note') or 'shown to the person'
    fresh, data = read_into_workspace(agent, tab)
    lines = [f"{result.get('note', 'done')} in the tab. Groups now: {', '.join(result.get('groups') or []) or 'none'}."]
    if op in ('move', 'rotate', 'angles', 'mask_grid'):
        lines.append(f'Knot: {identify.summary(data)}')
    lines.append(f"The tab is the current design again (version {fresh.get('version')}): render it and look.")
    return f"Groups · {result.get('note', op)[:70]}", '\n'.join(lines)


def show_group(agent, args):
    call = {'op': str(args.get('op', ''))}
    for key in ('group', 'collapsed'):
        if key in args:
            call[key] = args[key]
    result = agent.app.call('group_view', call)
    return f"Group panel · {result.get('note', call['op'])}", result.get('note') or 'done'


HANDLERS = {'edit_groups_in_tab': edit_groups_in_tab, 'show_group': show_group}
