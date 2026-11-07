"""Load a project with the app's own loader and report what is wrong with it."""
from types import SimpleNamespace

from .generators import application


def problems(data):
    """A list of problems, empty when the app loads the project cleanly."""
    application()
    from generate_creative_samples import CURVE_SETTINGS
    from save_load_manager import load_strands_from_data
    from attached_strand import AttachedStrand
    from masked_strand import MaskedStrand
    canvas = SimpleNamespace(default_shadow_color=None, shadow_enabled=False, _suppress_repaint=True,
                             update=lambda: None, selected_strand=None, **CURVE_SETTINGS)
    try:
        loaded, groups, *_ = load_strands_from_data(data, canvas)
    except Exception as e:
        return [f'the app cannot load it: {type(e).__name__}: {e}']
    found = []
    loaded_ok = [s for s in loaded if s]
    if len(loaded_ok) != len(data['strands']):
        found.append(f"{len(data['strands'])} strands in the file, but {len(loaded_ok)} loaded")
    names = [s.layer_name for s in loaded_ok]
    twice = sorted({n for n in names if names.count(n) > 1})
    if twice:
        found.append(f"layer names used more than once: {', '.join(twice)}")
    for s in loaded_ok:
        if isinstance(s, AttachedStrand):
            anchor = s.parent.start if s.attachment_side == 0 else s.parent.end
            if abs(s.start.x() - anchor.x()) > .01 or abs(s.start.y() - anchor.y()) > .01:
                found.append(f'{s.layer_name} does not start where it attaches to {s.parent.layer_name}')
            if s not in s.parent.attached_strands:
                found.append(f'{s.layer_name} is not listed on its parent {s.parent.layer_name}')
        if isinstance(s, MaskedStrand) and s.get_mask_path().isEmpty():
            found.append(f'mask {s.layer_name} covers nothing: its two strands do not cross')
    lookup = set(names)
    for name, group in groups.items():
        missing = [n for n in list(group.get('strands', [])) + list(group.get('main_strands', []))
                   if isinstance(n, str) and n not in lookup]
        if missing:
            found.append(f'group "{name}" names strands that do not exist: {", ".join(missing)}')
    return found
