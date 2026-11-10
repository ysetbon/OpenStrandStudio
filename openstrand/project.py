"""Read, write and describe OpenStrand Studio project files."""
import json
from pathlib import Path

HISTORY_TYPE = 'OpenStrandStudioHistory'


def read(path):
    """The project in a file, as the plain dict the app saves (strands, groups, ...).

    A history file (one with undo states) gives its current state.
    """
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError(f'{path}: no such file') from None
    except json.JSONDecodeError as e:
        raise ValueError(f'{path}: not valid JSON ({e.msg}, line {e.lineno})') from None
    if isinstance(data, dict) and data.get('type') == HISTORY_TYPE:
        states = data.get('states') or []
        if not states:
            raise ValueError(f'{path}: the history file holds no states')
        current = data.get('current_step')
        data = next((s for s in states if s.get('step') == current), states[-1])['data']
    if not isinstance(data, dict) or not isinstance(data.get('strands'), list):
        raise ValueError(f'{path}: not an OpenStrand Studio project (it has no strands)')
    return data


def write(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    return path


def hex_color(color):
    return '#{:02x}{:02x}{:02x}'.format(color['r'], color['g'], color['b'])


def set_of(strand):
    """The set a strand belongs to; a mask belongs to the set of the strand on top."""
    if strand['type'] == 'MaskedStrand':
        return int(str(strand['layer_name']).split('_')[0])
    return int(strand['set_number'])


def describe(data):
    """Counts, colors and size of a project: what is needed to check a result."""
    sets, masks, xs, ys, spans = {}, 0, [], [], {}
    for s in data['strands']:
        if s['type'] == 'MaskedStrand':
            masks += 1
            continue
        n = set_of(s)
        entry = sets.setdefault(n, {'strands': 0, 'colors': [], 'runs': ''})
        entry['strands'] += 1
        color = hex_color(s['color'])
        if color not in entry['colors']:
            entry['colors'].append(color)
        span = spans.setdefault(n, [[], []])
        for p in [s['start'], s['end']] + [c for c in s.get('control_points') or [] if c]:
            xs.append(p['x'])
            ys.append(p['y'])
            span[0].append(p['x'])
            span[1].append(p['y'])
    # Which way each set runs, so a stitch's vertical and horizontal ribbons
    # can be told apart (a ring or knot runs neither way).
    for n, (sx, sy) in spans.items():
        w, h = max(sx) - min(sx), max(sy) - min(sy)
        sets[n]['runs'] = 'vertical' if h > 1.5 * w else 'horizontal' if w > 1.5 * h else ''
    return {
        'strands': sum(e['strands'] for e in sets.values()),
        'masks': masks,
        'sets': dict(sorted(sets.items())),
        'groups': sorted(data.get('groups') or {}),
        'size': [round(max(xs) - min(xs)), round(max(ys) - min(ys))] if xs else [0, 0],
    }


def summary(data):
    """One line: '1 set · 15 strands · 7 masks'."""
    info = describe(data)
    sets = len(info['sets'])
    return (f"{sets} set{'s' if sets != 1 else ''} · {info['strands']} strands · "
            f"{info['masks']} mask{'s' if info['masks'] != 1 else ''}")


def detail(data):
    """Every strand and mask, one line each, with exact coordinates: what the agent
    needs to reason about a design's geometry (and to move points in a tab)."""
    from .steps import mask_parts
    pt = lambda p: f"[{p['x']:.1f}, {p['y']:.1f}]" if isinstance(p, dict) and 'x' in p else '-'
    names = [s['layer_name'] for s in data['strands'] if s.get('type') != 'MaskedStrand']
    lines = []
    for s in data['strands']:
        if s.get('type') == 'MaskedStrand':
            parts = mask_parts(s['layer_name'], names)
            over = f'{parts[0]} over {parts[1]}' if len(parts) == 2 else '?'
            boxes = len(s.get('deletion_rectangles') or [])
            flags = [w for k, w in (('is_hidden', 'hidden'), ('shadow_only', 'shadow only'),
                                    ('hide_shadow', 'casts no shadow')) if s.get(k)]
            lines.append(f"mask {s['layer_name']}: {over}"
                         + (f", {boxes} erase box{'es' if boxes != 1 else ''}" if boxes else '')
                         + (f" | {', '.join(flags)}" if flags else ''))
            continue
        cps = s.get('control_points') or []
        line = (f"strand {s['layer_name']}: start {pt(s.get('start'))}, end {pt(s.get('end'))}, "
                f"control_point1 {pt(cps[0] if len(cps) > 0 else None)}, "
                f"control_point2 {pt(cps[1] if len(cps) > 1 else None)}")
        if s.get('control_point_center_locked') and s.get('control_point_center'):
            line += f", control_point_center {pt(s['control_point_center'])}"
        line += f", width {s.get('width')}"
        if s.get('attached_to'):
            line += f", attached to {s['attached_to']} at its {'start' if s.get('attachment_side') == 0 else 'end'}"
        lines.append(line + looks(s))
    for name, group in sorted((data.get('groups') or {}).items()):
        members = group.get('layers') or group.get('strands') or []
        sets = sorted({str(m).split('_')[0] for m in (group.get('main_strands') or members)}, key=lambda n: (len(n), n))
        lines.append(f"group {name}: sets {', '.join(sets) or '-'}"
                     + (f" ({len(members)} layers: {', '.join(map(str, members))})" if members else ''))
    for caster, rows in sorted((data.get('shadow_overrides') or {}).items()):
        for receiver, row in sorted((rows or {}).items()):
            bits = [f"{'visible' if row.get('visibility', True) else 'hidden'}"]
            if row.get('allow_full_shadow'):
                bits.append('full shadow')
            if row.get('subtracted_layers'):
                bits.append('minus ' + ', '.join(row['subtracted_layers']))
            lines.append(f"shadow of {caster} on {receiver}: {', '.join(bits)}")
    return '\n'.join(lines)


def looks(s):
    """How a strand is drawn, where it differs from a plain strand: ' | ...' (empty when plain).
    What edit_layers_in_tab changes, so the agent knows what is on before it changes it."""
    color = lambda c: ('#%02x%02x%02x' % (c['r'], c['g'], c['b']) + ('' if c.get('a', 255) == 255 else '%02x' % c['a'])
                       if isinstance(c, dict) and 'r' in c else '-')
    out = [f"color {color(s.get('color'))}", f"stroke {color(s.get('stroke_color'))} {s.get('stroke_width')}"]
    for key, word in (('is_hidden', 'hidden'), ('shadow_only', 'shadow only'), ('hide_shadow', 'casts no shadow'),
                      ('full_arrow_visible', 'full arrow'), ('elliptical_end_caps', 'elliptical ends')):
        if s.get(key):
            out.append(word)
    circles = s.get('has_circles') or [False, False]
    for index, side in enumerate(('start', 'end')):
        ends = []
        if index < len(circles) and circles[index]:
            ends.append('circle')
        if s.get(f'{side}_arrow_visible'):
            ends.append('arrow')
        if s.get(f'{side}_extension_visible'):
            ends.append('dash')
        if s.get(f'{side}_line_visible') is False:
            ends.append('no line')
        style = (s.get('end_styles') or [None, None])[index] if len(s.get('end_styles') or []) > index else None
        if style:
            ends.append(f"style {style.get('shape', 'straight')}")
        if (s.get('closed_connections') or [False, False])[index]:
            ends.append('closes the knot')
        if ends:
            out.append(f"{side}: {' '.join(ends)}")
    edge = s.get('start_circle_stroke_color')
    if isinstance(edge, dict) and s.get('type') != 'MaskedStrand':
        out.append('start edge folded' if edge.get('a', 255) else 'start edge unfolded')
    return ' | ' + ', '.join(out)
