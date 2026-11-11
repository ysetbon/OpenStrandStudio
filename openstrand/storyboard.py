"""Steps drawn one by one: a tutorial whose pictures differ from step to step.

steps.py shows one finished design drawn bit by bit, which suits a mat or a
weave. Most how-to pictures are not that: in a crochet stitch, a slip knot on
a hook or a knot shown stage by stage, the cord has moved between one picture
and the next, a loop was pulled through, a hook went in, and an arrow shows
the move to make. Here every step is its own drawing (draw.build), given
together in one design:

    {"steps": [
        {"title": "Fold the yarn into a loop",
         "cords": [{"label": "Yarn", "points": [...], "heights": [...]}]},
        {"title": "Put the hook through the loop",
         "keep": ["Yarn"],
         "cords": [{"tool": "hook", "from": [820, 180], "to": [520, 430], "height": 10}],
         "arrows": [{"points": [[540, 470], [620, 520], [700, 470]]}]}]}

A step says only what is new in it: "keep" names the cords (by label) that
stay exactly as in the step before, "cords" are the ones drawn anew or moved
(a label used in the step before replaces that cord), "arrows" belong to the
step alone. replace() changes single steps of a sequence already sent, so a
picture that came out wrong is fixed without sending the others again.

    from openstrand import storyboard
    for step in storyboard.build(spec):
        step['title'], step['data'], step['report']
"""
import copy
import math

from .draw import DrawError, tool_of

MAX_STEPS = 12


class StepsError(DrawError):
    """Steps that cannot be drawn; the message names the step and what to change."""


def _label(cord, index, what):
    """The cord's label: its own, else the default name its tool or its place gives it
    ("Hook", "Cord 2"). Labels are how a step names the cords of the step before."""
    if not isinstance(cord, dict):
        raise StepsError(f'{what}: cord {index + 1} must be an object')
    tool = tool_of(cord, f'{what}, cord {index + 1}')
    return str(cord.get('label') or (tool.capitalize() if tool else f'Cord {index + 1}')).strip()[:40]


def resolve(steps):
    """Every step with all its cords: [{'title', 'cords', 'arrows', 'weave'}].
    A kept cord is the step before's, as it was; a cord with a label of the
    step before takes that cord's place; new labels come after."""
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise StepsError(f'"steps" must list 1 to {MAX_STEPS} steps')
    out, before = [], {}
    for n, step in enumerate(steps, start=1):
        what = f'step {n}'
        if not isinstance(step, dict):
            raise StepsError(f'{what} must be an object with "title" and "cords"')
        title = str(step.get('title') or f'Step {n}').strip()[:60]
        keep = step.get('keep')
        if keep is True or (isinstance(keep, str) and keep.strip().lower() == 'all'):
            keep = list(before)
        elif keep in (None, False):
            keep = []
        elif isinstance(keep, str):
            keep = [keep]
        if not isinstance(keep, list) or not all(isinstance(k, str) for k in keep):
            raise StepsError(f'{what}: "keep" lists the labels of cords that stay as in the step before, or is "all"')
        keep = [k.strip()[:40] for k in keep]
        missing = [k for k in keep if k not in before]
        if missing:
            there = ', '.join(f'"{k}"' for k in before) or 'no cords (it is the first step)'
            raise StepsError(f'{what} keeps {", ".join(repr(k) for k in missing)}, but the step before has '
                             f'{there}: "keep" names cords of the step before by their label')
        cords = step.get('cords') or []
        if not isinstance(cords, list):
            raise StepsError(f'{what}: "cords" must be a list of cords')
        drawn = {}
        for k, cord in enumerate(cords):
            label = _label(cord, k, what)
            if label in keep and not str(cord.get('label') or '').strip():
                # Its name is only the default one ("Cord 1", "Hook"): it cannot mean the kept cord.
                raise StepsError(f'{what}: cord {k + 1} has no label, and its default name "{label}" is a cord '
                                 'this step keeps. Give it a label of its own to add it, or give it the label '
                                 f'"{label}" and leave that out of "keep" to redraw that cord')
            if label in drawn:
                raise StepsError(f'{what} has two cords labelled "{label}": give each cord its own label')
            drawn[label] = dict(copy.deepcopy(cord), label=label)
        order = [label for label in before if label in keep or label in drawn]
        order += [label for label in drawn if label not in before]
        now = {label: drawn.get(label) or before[label] for label in order}
        if not now:
            raise StepsError(f'{what} has no cords: give "cords", or "keep" cords of the step before')
        arrows = step.get('arrows') or []
        out.append({'title': title, 'cords': [copy.deepcopy(c) for c in now.values()],
                    'arrows': copy.deepcopy(arrows), 'weave': step.get('weave')})
        before = now
    return out


def replace(steps, changes):
    """The steps with some of them changed: each change is a step with
    "step": its number. The number after the last adds a step."""
    if not steps:
        raise StepsError('there are no steps to change yet: send the whole sequence in "steps" first')
    if isinstance(changes, dict):
        changes = [changes]
    if not isinstance(changes, list) or not changes:
        raise StepsError('"replace" lists the changed steps, each with "step": its number')
    out = [copy.deepcopy(s) for s in steps]
    for change in changes:
        number = change.get('step') if isinstance(change, dict) else None
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= len(out) + 1:
            raise StepsError(f'each replaced step needs "step": a number from 1 to {len(out) + 1} '
                             f'({len(out) + 1} adds a step after the last)')
        step = {k: copy.deepcopy(v) for k, v in change.items() if k != 'step'}
        if number == len(out) + 1:
            out.append(step)
        else:
            out[number - 1] = step
    if len(out) > MAX_STEPS:
        raise StepsError(f'at most {MAX_STEPS} steps')
    return out


def build(spec, progress=None):
    """Draw every step: [{'title', 'data', 'report'}], in order. spec is
    {"steps": [...]} with an optional "weave" for all of them."""
    from . import draw
    if not isinstance(spec, dict):
        raise StepsError('the design must be an object with a "steps" list')
    steps = resolve(spec.get('steps'))
    made = []
    for n, step in enumerate(steps, start=1):
        def shown(fraction=None, stage=None, frame=None, n=n, **_):
            """draw.build's progress, shown as this step of the whole call: its cords, its number."""
            progress((n - 1) / len(steps), 'draw_step', frame, step=n, steps=len(steps))
        if progress is not None:
            shown()
        design = {'name': step['title'], 'cords': step['cords'], 'arrows': step['arrows']}
        if step['weave'] or spec.get('weave'):
            design['weave'] = step['weave'] or spec.get('weave')
        try:
            data, report = draw.build(design, mask_check=False, progress=shown if progress is not None else None)
        except DrawError as e:
            raise StepsError(f'step {n} ("{step["title"]}"): {e}') from None
        data, found = _masks(data)
        made.append({'title': step['title'], 'data': data, 'report': report + '\n' + found,
                     'labels': [c['label'] for c in step['cords']]})
    if progress is not None:
        progress(1.0, 'draw_step', step=len(steps), steps=len(steps))
    return made


def _masks(data):
    """The step with its masks checked and what is safe fixed (a hook
    through a loop and a loop pulled through another sit close together, as
    in a tight knot): (data, what was fixed and what is left, as lines)."""
    from . import masks
    try:
        fixed_data, fixed, left = masks.repair(data, create_masks=True)
    except masks.MaskError as e:
        return data, f'masks: {e}'
    lines = [f'masks fixed: {text}' for text in fixed] + [f"masks left: {p['text']}" for p in left]
    return (fixed_data if fixed else data), '\n'.join(lines) or 'masks: no problems'


def summary(made):
    """What was drawn, step by step, for a person or the agent."""
    lines = []
    for n, step in enumerate(made, start=1):
        lines.append(f'step {n} "{step["title"]}" ({", ".join(step["labels"])}):')
        lines += ['  ' + line for line in step['report'].splitlines() if not line.startswith('built in')]
    return '\n'.join(lines)


# ------------------------------------------------------------ contact sheet
def columns_for(count):
    """How many pictures in a row: up to three side by side, then a grid."""
    return count if count <= 3 else 2 if count == 4 else 3 if count <= 9 else 4


def sheet(pictures, titles, path, cell=(430, 320), header=34):
    """One picture of all the steps, numbered and titled, in reading order:
    what the agent looks at to check a whole tutorial at once. pictures are
    image files, one per step. Returns path."""
    from PyQt5.QtCore import QRect, Qt
    from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPen
    count = len(pictures)
    columns = columns_for(count)
    rows = math.ceil(count / columns)
    width, height = cell
    image = QImage(columns * width, rows * (height + header), QImage.Format_RGB32)
    image.fill(QColor('#ffffff'))
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        font = QFont()
        font.setPixelSize(17)
        font.setBold(True)
        painter.setFont(font)
        for k, (picture, title) in enumerate(zip(pictures, titles)):
            x, y = (k % columns) * width, (k // columns) * (height + header)
            painter.fillRect(QRect(x, y, width, header), QColor('#263446'))
            painter.setPen(QColor('#ffffff'))
            text = painter.fontMetrics().elidedText(f'{k + 1} · {title}', Qt.ElideRight, width - 20)
            painter.drawText(QRect(x + 10, y, width - 20, header), Qt.AlignVCenter | Qt.AlignLeft, text)
            shot = QImage(str(picture))
            if not shot.isNull():
                shot = shot.scaled(width - 16, height - 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                painter.drawImage(x + (width - shot.width()) // 2, y + header + (height - shot.height()) // 2, shot)
            painter.setPen(QPen(QColor('#c9ced6'), 1))
            painter.drawRect(QRect(x, y, width - 1, height + header - 1))
    finally:
        painter.end()
    if not image.save(str(path)):
        raise OSError(f'cannot write {path}')
    return path
