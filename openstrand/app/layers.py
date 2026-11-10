"""What the layer panel's right-click menu does, on layers of the person's tab:
done in the app with the menu's own code (src/agent_bridge/layers.py), then
the tab is read back so the agent's copy is the tab again."""
import re

from .. import colors, identify
from ..errors import ToolError
from .strands import require_read
from .tabs import read_into_workspace

OPS = ('visible', 'shadow_only', 'hide_shadow', 'shadow', 'color', 'stroke_color', 'width', 'line', 'arrow',
       'dash', 'circle', 'full_arrow', 'arrow_style', 'arrow_sizes', 'start_edge', 'closing_side', 'end_style',
       'close_knot', 'paste_from')

TOOLS = [
    {
        'name': 'edit_layers_in_tab',
        'description': (
            "Do what the layer panel's right-click menu does, on layers of the person's tab, with the app's own "
            'code (each change one undo step, as the menu makes it; in ask mode the person allows it first). The '
            'tab must be the one showing and read with read_tab since its last change. read_tab lists each '
            "strand's looks (color, stroke, circles, arrows, dashes, lines, end styles, start edge, shadows). "
            'ops, with what each takes:\n'
            '- visible / shadow_only / hide_shadow: value true/false (also masks). hide_shadow true: the layer '
            'casts no shadow.\n'
            '- shadow (Edit Shadows): value {"receiver": a layer below, "visible": bool, "full_shadow": bool '
            '(layers between do not block it), "subtract": [layer names cut out of the shadow]}.\n'
            '- color / stroke_color: value a color name or "#rrggbb" ("#rrggbbaa" with alpha); scope "set" (every '
            'layer of the set, default) or "layer" (this layer only).\n'
            '- width: value {"width": px of the color, "stroke_width": px of the stroke each side, '
            '"elliptical_ends": bool (scope "layer")}; scope "set" or "layer".\n'
            '- line / arrow / dash / circle: side "start" or "end", value true/false (a circle only where a strand '
            'is attached at that end; an attached strand has no start line).\n'
            '- full_arrow: value true/false; arrow_style (full arrow on): value {"color": color or null (the '
            'stroke\'s), "transparency": 0-100, "texture": none/stripes/dots/crosshatch, "shaft": '
            'solid/tiles/stripes/dots, "head": bool, "casts_shadow": bool}.\n'
            '- arrow_sizes (every arrow in the app): value any of head_length, head_width, head_stroke_width, '
            'gap_length, line_length, line_width.\n'
            '- start_edge: value "fold" (Fold Over Start Edge: the start circle drawn over the edge) or "unfold".\n'
            '- closing_side (a strand that closes the knot): value "transparent" or "default".\n'
            '- end_style (Stylize End Side, a free end only): side, value {"shape": straight/angled/rounded/'
            'pointed/notched/concave, "tilt": -60..60 degrees, "depth": 0..1, "offset": px (+ extends, - trims), '
            '"line_width": px or null, "line_color": color or null, "show_line": bool, "both_ends": bool}.\n'
            '- close_knot: the strand\'s one free end joins the nearest free end of its set.\n'
            '- paste_from (Copy/Paste Strand Data): value {"source": a strand, "properties": any of start_point, '
            'end_point, control_points, width, strand_color, stroke_color, "anchor": "start" or "end"}.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'layers': {'type': 'array', 'items': {'type': 'string'},
                       'description': 'layer names, e.g. ["1_1"]; for scope "set", one layer of each set is enough'},
            'op': {'type': 'string', 'enum': list(OPS)},
            'value': {'description': 'what the op takes (see above)'},
            'side': {'type': 'string', 'enum': ['start', 'end']},
            'scope': {'type': 'string', 'enum': ['set', 'layer']},
        }, 'required': ['tab_id', 'layers', 'op']},
    },
]
LOOK_ONLY = set()

INSTRUCTIONS = """- To change how layers of the person's tab look (colors, widths, circles, arrows,
  dashes, side lines, end styles, folding the start edge, shadows, hiding), use
  edit_layers_in_tab on the tab itself: it is what the layer panel's right-click
  menu does. Do not recolor a copy and open a new tab when they asked about
  their tab.
"""


def color_value(value):
    """A color name or hex for the app: '#rrggbb', or '#rrggbbaa' with alpha."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if re.fullmatch(r'#?[0-9a-f]{8}', text):
        return '#' + text.lstrip('#')
    try:
        return colors.parse(text)
    except ValueError as e:
        raise ToolError(str(e)) from None


def app_value(op, value):
    """The agent's value with its colors made exact for the app."""
    if op in ('color', 'stroke_color'):
        return color_value(value)
    if op == 'arrow_style' and isinstance(value, dict) and value.get('color') is not None:
        return dict(value, color=color_value(value['color']))
    if op == 'end_style' and isinstance(value, dict) and value.get('line_color') is not None:
        return dict(value, line_color=color_value(value['line_color']))
    return value


def edit_layers_in_tab(agent, args):
    tab, op = str(args.get('tab_id', '')), str(args.get('op', ''))
    require_read(agent, tab)
    if op not in OPS:
        raise ToolError(f'op is one of {", ".join(OPS)}')
    call = {'tab_id': tab, 'layers': [str(n) for n in args.get('layers') or []], 'op': op,
            'version': agent.workspace.tab_version}
    for key in ('side', 'scope'):
        if args.get(key) is not None:
            call[key] = args[key]
    if 'value' in args:
        call['value'] = app_value(op, args['value'])
    result = agent.app.call('edit_layers', call)
    if 'version' not in result:  # ask mode: the person decides; nothing changed yet
        return f'{op} · waiting for the person', result.get('note') or 'shown to the person'
    fresh, data = read_into_workspace(agent, tab)
    lines = [f"{result.get('note', 'done')} in the tab."]
    if result.get('undo'):
        lines.append(f"Note: {result['undo']}.")
    if op == 'close_knot':
        lines.append(f'Knot: {identify.summary(data)}')
    lines.append(f"The tab is the current design again (version {fresh.get('version')}).")
    return f"Layers · {result.get('note', op)[:70]}", '\n'.join(lines)


HANDLERS = {'edit_layers_in_tab': edit_layers_in_tab}
