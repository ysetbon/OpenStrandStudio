"""Changes to an existing project."""
from . import colors, project


def recolor(data, by_set):
    """Give each set in by_set ({set number: color}) that color, masks included.

    Returns the number of strands changed. Raises ValueError for a set the
    project does not have.
    """
    present = {project.set_of(s) for s in data['strands'] if s['type'] != 'MaskedStrand'}
    missing = sorted(set(by_set) - present)
    if missing:
        raise ValueError(f"the project has no set {', '.join(map(str, missing))} "
                         f"(sets: {', '.join(map(str, sorted(present)))})")
    rgba = {n: colors.rgba(c) for n, c in by_set.items()}
    changed = 0
    for s in data['strands']:
        n = project.set_of(s)
        if n in rgba:
            s['color'] = dict(rgba[n])
            changed += 1
    table = data.setdefault('strand_colors', {})
    for n, color in rgba.items():
        table[str(n)] = dict(color)
    return changed
