"""Duplicate Group keeps levels on every sample in tests/levels/duplicate_samples.

samples.json lists the samples (built by make_samples.py in that folder):
the box on one, two or four levels, raised masks, a mask between two levels,
a mask whose partner set is outside the group, no levels, empty levels,
hidden layers, a selected level block, a copy of a copy, a single strand,
and the designs shipped in src/samples with their sets spread over levels.

Each case loads one sample in the real MainWindow (offscreen), duplicates the
groups it names through GroupPanel.duplicate_group, and checks every copy
against the layer it copies. The pairs come from copy_strand_properties,
which duplicate_group calls once for every copied layer.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import (apply_project_state, keep_masks_on_top, mask_base_level,
                               mask_own_level, serialize_project_state, serialize_strand,
                               set_mask_level, strand_level)

APP = QApplication.instance() or QApplication([])
SAMPLES_DIR = Path(__file__).resolve().parent / "levels" / "duplicate_samples"
SAMPLES = json.loads((SAMPLES_DIR / "samples.json").read_text(encoding="utf-8"))
# Big enough for every sample to be drawn whole. Set before the window is
# shown: the level rows follow later resizes of the layer list.
WINDOW_SIZE = (2800, 2000)
# Saved values a copy does not share with its original: its names and
# level (checked on their own), and values worked out again from the
# geometry (an attached strand's angle and length; a mask's ends, centre
# and width come from its two strands).
NOT_COPIED = {"index", "layer_name", "set_number", "attached_to", "level", "angle", "length"}
NOT_COPIED_MASK = NOT_COPIED | {"start", "end", "control_point_center", "width"}


def same_picture(a, b, noise=8, stray=12):
    """Whether two renders match, allowing anti-aliasing noise: a channel
    may differ by up to *noise* (a line shifted by a hundredth of a pixel),
    and up to *stray* pixels by more (the tip of a hair-thin wedge where two
    outlines meet). A layer drawn differently changes hundreds of pixels."""
    if a.size() != b.size():
        return False
    if a == b:
        return True
    a = a.convertToFormat(a.Format_ARGB32)
    b = b.convertToFormat(b.Format_ARGB32)
    pa = a.constBits(); pa.setsize(a.sizeInBytes())
    pb = b.constBits(); pb.setsize(b.sizeInBytes())
    pa, pb = bytes(pa), bytes(pb)
    off = sum(1 for i in range(0, len(pa), 4)
              if max(abs(pa[i + c] - pb[i + c]) for c in range(4)) > noise)
    return off <= stray


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


class Run:
    """One sample, loaded and duplicated."""

    def __init__(self, sample):
        self.sample = sample
        self.win = MainWindow()
        canvas = self.win.canvas
        apply_project_state(canvas, json.loads((SAMPLES_DIR / sample["file"]).read_text(encoding="utf-8")))
        canvas.selected_strand = None
        self.win.layer_panel.refresh()
        self.win.resize(*WINDOW_SIZE)
        self.win.show()
        pump(150)
        self.top = canvas.level_count
        if any("Level 1" in step for step in sample["steps"]):
            self.win.layer_panel.set_level_scope(1)
            assert self.win.layer_panel.level_scope() == 1
        self.originals = list(canvas.strands)
        self.levels_before = self.levels()
        self.pairs = []  # (original, copy, the original's level when it was copied)
        panel = canvas.group_layer_manager.group_panel
        copy_props = panel.copy_strand_properties

        def recording(original, new_strand):
            self.pairs.append((original, new_strand, strand_level(original, self.top)))
            return copy_props(original, new_strand)

        panel.copy_strand_properties = recording
        for group in sample["duplicate"]:
            assert group in panel.groups, f"{group} not in {list(panel.groups)}"
            with contextlib.redirect_stdout(io.StringIO()):  # duplicate_group logs every layer
                panel.duplicate_group(group)
            pump(100)
        panel.copy_strand_properties = copy_props
        # Duplicating selects the last copy; compare pictures with nothing selected
        canvas.selected_strand = None
        for strand in canvas.strands:
            strand.is_selected = False
        canvas.update()
        pump(50)

    def level(self, strand):
        return strand_level(strand, self.win.canvas.level_count)

    def levels(self):
        return {s.layer_name: self.level(s) for s in self.win.canvas.strands}

    def render(self, layers):
        """The canvas with only *layers* drawn (their own hidden flags kept).
        A hidden strand still draws its full arrow, so the others' arrows
        are switched off too."""
        strands = self.win.canvas.strands
        kept = {id(s): (s.is_hidden, getattr(s, 'full_arrow_visible', False)) for s in strands}
        wanted = {id(s) for s in layers}
        for s in strands:
            if id(s) not in wanted:
                s.is_hidden = True
                if not isinstance(s, MaskedStrand):
                    s.full_arrow_visible = False
        self.win.canvas.update()
        pump(50)
        image = self.win.canvas.grab().toImage()
        for s in strands:
            s.is_hidden = kept[id(s)][0]
            if not isinstance(s, MaskedStrand):
                s.full_arrow_visible = kept[id(s)][1]
        return image

    def drawn_box(self, image):
        """Where *image* differs from the empty canvas: (left, top, right, bottom)."""
        empty = self.render([])
        xs, ys = [], []
        for y in range(0, image.height(), 2):
            for x in range(0, image.width(), 2):
                if image.pixel(x, y) != empty.pixel(x, y):
                    xs.append(x)
                    ys.append(y)
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None

    def fit(self, layers):
        """Centre the design and zoom out until all of *layers* is drawn
        inside the canvas; return whether it fits."""
        canvas = self.win.canvas
        canvas.center_all_strands()
        for _ in range(25):
            picture = self.render(layers)
            box = self.drawn_box(picture)
            if box is None or (box[0] > 2 and box[1] > 2 and box[2] < picture.width() - 3
                               and box[3] < picture.height() - 3):
                return True
            canvas.zoom_out()
            canvas.center_all_strands()
        return False

    def close(self):
        self.win._confirm_close_with_dirty_tabs = lambda *a, **k: True
        self.win.close()
        self.win.deleteLater()
        pump(20)


@pytest.fixture(scope="module", params=SAMPLES, ids=[s["file"][:-5] for s in SAMPLES])
def run(request):
    r = Run(request.param)
    yield r
    r.close()


def test_every_layer_of_the_group_is_copied(run):
    assert run.pairs, "nothing was duplicated"
    copies = [c for _, c, _ in run.pairs]
    assert all(c is not None for c in copies)
    assert all(c in run.win.canvas.strands for c in copies)
    names = [c.layer_name for c in copies]
    assert len(names) == len(set(names))


def test_each_copy_is_on_the_level_of_the_layer_it_copies(run):
    wrong = {c.layer_name: (o.layer_name, want, run.level(c))
             for o, c, want in run.pairs if run.level(c) != want}
    assert not wrong, "copy: (original, its level, copy's level) " + repr(wrong)


def test_copied_masks_keep_a_raised_level_and_nothing_else(run):
    for original, copy, _ in run.pairs:
        if isinstance(original, MaskedStrand):
            own = mask_own_level(original)
            assert mask_own_level(copy) == own, copy.layer_name


def test_copied_masks_sit_on_their_strands_level_or_higher(run):
    for _, copy, _ in run.pairs:
        if isinstance(copy, MaskedStrand):
            assert run.level(copy) >= mask_base_level(copy, run.win.canvas.level_count)


def test_the_originals_stay_where_they_were(run):
    after = run.levels()
    assert {n: after[n] for n in run.levels_before} == run.levels_before


def test_duplicating_adds_and_removes_no_level(run):
    assert run.win.canvas.level_count == run.top


def test_the_stack_is_in_level_order(run):
    strands = run.win.canvas.strands
    ordered, _ = keep_masks_on_top(strands, (), run.win.canvas.level_count)
    assert [s.layer_name for s in ordered] == [s.layer_name for s in strands]


def test_copies_keep_hidden_and_shadow_only(run):
    for original, copy, _ in run.pairs:
        assert copy.is_hidden == original.is_hidden, copy.layer_name
        assert getattr(copy, 'shadow_only', False) == getattr(original, 'shadow_only', False), copy.layer_name


def test_the_copy_is_drawn_like_the_original(run):
    """Copies sit where their originals are: drawn alone, they must give the
    same picture as the originals drawn alone."""
    originals = [o for o, _, _ in run.pairs]
    copies = [c for _, c, _ in run.pairs]
    if run.sample.get("known_issue"):
        pytest.xfail(run.sample["known_issue"])
    assert run.fit(originals + copies), "the design does not fit on the canvas"
    assert same_picture(run.render(originals), run.render(copies))


def test_each_copy_saves_like_its_original(run):
    """Everything the file keeps about a layer (colours, widths, end caps,
    arrows, curves, circles, closed ends, erased boxes...) is copied, apart
    from its names and the values worked out again from the geometry. An
    attached copy is attached to the copy of its original's parent."""
    canvas = run.win.canvas
    copy_of = {id(o): c for o, c, _ in run.pairs}
    for original, copy, _ in run.pairs:
        a = serialize_strand(original, canvas)
        b = serialize_strand(copy, canvas)
        skip = NOT_COPIED_MASK if isinstance(original, MaskedStrand) else NOT_COPIED
        differ = {k: (a.get(k), b.get(k)) for k in set(a) | set(b)
                  if k not in skip and json.dumps(a.get(k), sort_keys=True, default=str)
                  != json.dumps(b.get(k), sort_keys=True, default=str)}
        assert not differ, f"{original.layer_name} -> {copy.layer_name}: {differ}"
        if "attached_to" in a:
            parent = copy_of.get(id(original.parent))
            assert parent is not None and b.get("attached_to") == parent.layer_name, copy.layer_name


def test_saving_and_reopening_keeps_every_level(run):
    canvas = run.win.canvas
    state = serialize_project_state(canvas.strands, run.win.group_layer_manager.get_group_data(), canvas)
    if canvas.level_count == 0:
        assert "level_count" not in state
        assert all("level" not in s for s in state["strands"])
    reopened = MainWindow()
    try:
        apply_project_state(reopened.canvas, json.loads(json.dumps(state)))
        top = reopened.canvas.level_count
        assert top == canvas.level_count
        assert {s.layer_name: strand_level(s, top) for s in reopened.canvas.strands} == run.levels()
    finally:
        reopened._confirm_close_with_dirty_tabs = lambda *a, **k: True
        reopened.close()
        reopened.deleteLater()


def test_copied_masks_move_between_their_floor_and_the_top_level(run):
    """What the user tried: move a copied mask down. It goes as low as its
    strands and as high as the top level. (Runs last: it moves masks.)"""
    top = run.win.canvas.level_count
    for _, copy, _ in run.pairs:
        if not isinstance(copy, MaskedStrand):
            continue
        floor = mask_base_level(copy, top)
        set_mask_level(copy, top, top)
        assert run.level(copy) == top
        set_mask_level(copy, 0, top)
        assert run.level(copy) == floor
