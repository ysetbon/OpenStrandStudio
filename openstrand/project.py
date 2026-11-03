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
