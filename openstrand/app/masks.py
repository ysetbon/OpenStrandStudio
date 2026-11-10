"""Masks in the person's tab: the edit is worked out on the agent's copy (the
openstrand mask tools), checked, then done in the tab by the canvas's own
mask code, as one undo step."""
from ..errors import ToolError
from .strands import require_read

TOOLS = [
    {
        'name': 'edit_mask_in_tab',
        'description': ("Change one mask in the person's tab, in place, with the app's own code (one undo step; "
                        'in ask mode the person allows it first). The tab must be the one showing and read with '
                        'read_tab first. Same ops and arguments as edit_mask (erase with at, covers, around or '
                        'box; reset; swap; delete; create): the edit is worked out on your copy, checked, then '
                        'done in the tab, and your copy becomes the edited design.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'op': {'type': 'string', 'enum': ['erase', 'reset', 'swap', 'delete', 'create']},
            'mask': {'type': 'string'}, 'covers': {'type': 'string'},
            'at': {'type': 'array', 'items': {'type': 'number'}},
            'around': {'type': 'array', 'items': {'type': 'number'}}, 'box': {'type': 'array'},
            'first': {'type': 'string'}, 'second': {'type': 'string'},
        }, 'required': ['tab_id', 'op']},
    },
]
LOOK_ONLY = set()

INSTRUCTIONS = """- After tie_knot, call check_masks, fix each problem with edit_mask (preview
  first when unsure), then render and look before opening the steps.
- When the person points at a mask in their tab (a strand cut off, the wrong
  strand on top at a crossing): read_tab it, check_masks, then either
  edit_mask and open_in_new_tab the fixed design (their tab stays as it is),
  or, when they want their own tab fixed, edit_mask_in_tab (switch_tab to it
  first; it is one undo step). Use the names and coordinates check_masks
  gives, never guessed ones.
"""

CORNERS = ('top_left', 'top_right', 'bottom_left', 'bottom_right')


def edit_mask_in_tab(agent, args):
    """Work the edit out on the copy read from the tab, then have the app do it there."""
    ws = agent.workspace
    tab = str(args.get('tab_id', ''))
    require_read(agent, tab)
    before = ws.data
    with agent.quiet():
        summary, text = ws.edit_mask(dict(args, preview=True), store=False)
    after = ws.last_edit
    call = {'tab_id': tab, 'op': args.get('op'), 'mask': args.get('mask'),
            'first': args.get('first'), 'second': args.get('second')}
    if args.get('op') == 'erase':
        call['boxes'] = new_boxes(before, after, str(args.get('mask')))
        if not call['boxes']:
            raise ToolError('the erase added no box')
    elif args.get('op') in ('create', 'swap'):
        # The new mask is trimmed on the agent's copy: the same boxes go to the tab.
        made = (f"{args.get('first')}_{args.get('second')}" if args.get('op') == 'create'
                else swapped(before, str(args.get('mask'))))
        call['boxes'] = new_boxes(before, after, made)
    call['version'] = ws.tab_version
    result = agent.app.call('edit_mask', call)
    ws.store(after, tab=tab, tab_version=result.get('version'))
    note = result.get('note') or 'done'
    return (f'In the tab · {note}',
            f"{note} in the tab (one undo step there).\n" + text.replace('Preview, not kept: ', '', 1))


HANDLERS = {'edit_mask_in_tab': edit_mask_in_tab}


def swapped(data, name):
    """The name a mask has once swapped: its two strands the other way round."""
    from ..steps import mask_parts
    names = [s['layer_name'] for s in data['strands'] if s.get('type') != 'MaskedStrand']
    parts = mask_parts(name, names)
    return f'{parts[1]}_{parts[0]}' if len(parts) == 2 else name


def new_boxes(before, after, name):
    """The erase boxes a mask has in after and not in before."""
    def boxes(data):
        for s in data['strands']:
            if s.get('type') == 'MaskedStrand' and s.get('layer_name') == name:
                return [{k: [float(v) for v in r[k]] for k in CORNERS}
                        for r in s.get('deletion_rectangles') or [] if 'top_left' in r]
        return []
    old = boxes(before)
    return [b for b in boxes(after) if b not in old]
