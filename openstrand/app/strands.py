"""A strand's shape in the person's tab: move its ends and handles (the app's
Move mode code, as a drag), then read the tab back."""
from .. import identify
from ..errors import ToolError
from .tabs import read_into_workspace

TOOLS = [
    {
        'name': 'edit_strand_in_tab',
        'description': ("Move points of one strand in the person's tab, in place, with the app's Move mode code "
                        '(as a drag): strands attached at a moved end follow, erase boxes follow their crossing; one '
                        'undo step; in ask mode the person allows it first. The tab must be the one showing and '
                        'read with read_tab since its last change (otherwise it is refused: read it again). points: '
                        'any of start, end, control_point1, control_point2, control_point_center (the third control '
                        'point, when on in Settings), each [x, y] in canvas coordinates as read_tab gives them. '
                        'Answers with the strand\'s points now and the knot the tab shows, and your copy becomes '
                        'the edited tab. To make a strand symmetrical, mirror its points about the axis you want.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'strand': {'type': 'string', 'description': 'the strand name, e.g. "1_6"'},
            'points': {'type': 'object', 'description': 'e.g. {"control_point1": [612, 380], "end": [700, 402]}'},
        }, 'required': ['tab_id', 'strand', 'points']},
    },
]
LOOK_ONLY = set()

INSTRUCTIONS = """- To change a strand's shape in the person's tab (make it symmetrical, move an
  end or a handle), edit_strand_in_tab with the points worked out from read_tab;
  then render and check the knot it reports is still the right one.
"""


def require_read(agent, tab):
    ws = agent.workspace
    if ws.data is None or ws.tab != tab:
        raise ToolError('read_tab this tab first (and change nothing else before editing it)')


def edit_strand_in_tab(agent, args):
    """Move points of a strand in the tab, then read the tab back: the copy is the tab again."""
    tab = str(args.get('tab_id', ''))
    require_read(agent, tab)
    points = args.get('points')
    if not isinstance(points, dict) or not points:
        raise ToolError('points: e.g. {"control_point1": [x, y]}')
    result = agent.app.call('edit_strand', {'tab_id': tab, 'strand': str(args.get('strand', '')),
                                            'points': points, 'version': agent.workspace.tab_version})
    if not result.get('now'):  # ask mode: the person decides; nothing changed yet
        return f"{args.get('strand')} · waiting for the person", result.get('note') or 'shown to the person'
    fresh, data = read_into_workspace(agent, tab)
    now = ', '.join(f'{k} {v}' for k, v in result['now'].items())
    return (f"In the tab · {result.get('note', 'moved')}",
            f"{result.get('note', 'moved')} in the tab (one undo step there). {result.get('strand')} now: {now}.\n"
            f"Knot: {identify.summary(data)}\nThe tab is the current design again (version "
            f"{fresh.get('version')}): render it and look.")


HANDLERS = {'edit_strand_in_tab': edit_strand_in_tab}
