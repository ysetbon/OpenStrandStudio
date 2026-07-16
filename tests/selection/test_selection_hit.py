"""Regression tests for exact-geometry strand selection (select mode).

Run from anywhere:
    python tests\\selection\\test_selection_hit.py

Covers the three hit-testing fixes:
  #1  an attached strand's start no longer claims clicks through an invisible
      120x120 square - only its real rendered geometry counts
  #2  the strand body hit area matches the drawn thickness
      (width + 2*stroke_width), so clicks on the visible stroke edge land on
      the top strand instead of falling through to the layer below
  #3  a masked strand is clickable on its whole rendered footprint, including
      the stroke edge (get_mask_path_stroke united with get_mask_path)
Plus: topmost-first z-order, hidden strands skipped, and hit areas following
per-strand width/stroke changes.
"""

import os
import sys

# This test lives in tests/selection/ ; the source modules are in <repo>/src.
_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor, QPainterPath

from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
from select_mode import SelectMode
from mask_mode import MaskMode
from selection_utils import selection_outline_path

# --------------------------------------------------------------------------- io
_PASS = 0
_FAIL = 0


def check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("[PASS] %s" % name)
    else:
        _FAIL += 1
        print("[FAIL] %s  ::  %s" % (name, detail))


# ---------------------------------------------------------------- test helpers
class DummyCanvas:
    """Minimal canvas stand-in for SelectMode hit-testing."""

    def __init__(self):
        self.strands = []
        self.show_hover_highlights = True

    def update(self):
        pass

    def setCursor(self, *_args):
        pass


def make_strand(start, end, set_number, layer_name, width=46, stroke_width=4):
    s = Strand(
        QPointF(*start), QPointF(*end), width,
        color=QColor(200, 170, 230, 255),
        stroke_color=QColor(0, 0, 0, 255),
        stroke_width=stroke_width,
        set_number=set_number, layer_name=layer_name,
    )
    s.update_control_points_from_geometry()
    s.update_shape()
    s.update_side_line()
    return s


def make_loaded_straight_strand(start, end, set_number, layer_name,
                                parent=None, attachment_side=1,
                                has_circles=None):
    """Recreate the straight-line geometry stored in the reported JSON.

    Its saved control points both coincide with the start. This is visually a
    straight strand, but it takes a different path-building branch than the
    simple horizontal/vertical fixtures above.
    """
    if parent is None:
        strand = Strand(
            QPointF(*start), QPointF(*end), 46,
            color=QColor(200, 170, 230, 255),
            stroke_color=QColor(0, 0, 0, 255),
            stroke_width=4, set_number=set_number, layer_name=layer_name,
        )
    else:
        strand = AttachedStrand(parent, QPointF(*end), attachment_side)
        strand.start = QPointF(*start)
        strand.end = QPointF(*end)
        strand.width = 46
        strand.stroke_width = 4
        strand.set_number = set_number
        strand.layer_name = layer_name
        parent.attached_strands.append(strand)

    strand.has_circles = list(has_circles or (False, False))
    strand.control_point1 = QPointF(*start)
    strand.control_point2 = QPointF(*start)
    strand.update_control_points(reset_control_points=False)
    strand.update_shape()
    strand.update_side_line()
    return strand


def make_mask_bug_fixture():
    """Minimal in-repo fixture matching masknotworkingexample.json."""
    s11 = make_loaded_straight_strand(
        (1316, 224), (1512, 420), 1, "1_1", has_circles=(False, True))
    s12 = make_loaded_straight_strand(
        (1512, 420), (1092, 560), 1, "1_2", parent=s11,
        has_circles=(True, True))
    s21 = make_loaded_straight_strand(
        (1260, 700), (1344, 476), 2, "2_1", has_circles=(False, True))
    s22 = make_loaded_straight_strand(
        (1344, 476), (896, 280), 2, "2_2", parent=s21,
        has_circles=(True, False))
    s13 = make_loaded_straight_strand(
        (1092, 560), (1120, 196), 1, "1_3", parent=s12,
        has_circles=(True, True))
    s14 = make_loaded_straight_strand(
        (1120, 196), (1512, 532), 1, "1_4", parent=s13,
        has_circles=(True, False))
    return [s11, s12, s21, s22, s13, s14]


def hits(strands, point):
    """Topmost-first (strand, type) list at point via SelectMode."""
    canvas = DummyCanvas()
    canvas.strands = list(strands)
    mode = SelectMode(canvas)
    return mode.find_strands_at_point(QPointF(*point))


def top_hit(strands, point):
    result = hits(strands, point)
    return result[0][0] if result else None


def names(result):
    return [s.layer_name for s, _t in result]


# ------------------------------------------------------------------- case #2:
# body hit area == drawn thickness (width + 2*stroke), any width/stroke
def test_body_matches_rendered_thickness():
    # width 46, stroke 4 -> visible half-thickness 27
    a = make_strand((0, 0), (400, 0), 1, "1_1")

    check("edge inside rendered stroke is a hit (y=26, half=27)",
          top_hit([a], (200, 26)) is a,
          "click on visible stroke edge missed the strand")
    check("just outside rendered stroke is a miss (y=29)",
          top_hit([a], (200, 29)) is None,
          "hit area is larger than the rendered strand")

    # narrow strand + wide stroke: width 10, stroke 10 -> half = 15
    b = make_strand((0, 100), (400, 100), 1, "1_2", width=10, stroke_width=10)
    check("narrow strand with wide stroke: y offset 14 is a hit",
          top_hit([b], (200, 114)) is b,
          "stroke width not included in hit area")
    check("narrow strand with wide stroke: y offset 17 is a miss",
          top_hit([b], (200, 117)) is None,
          "hit area wider than rendered")

    # width changed at runtime (width dialog): hit area must follow
    a.width = 100  # half = (100 + 8) / 2 = 54
    check("after width change, new edge is a hit (y=53)",
          top_hit([a], (200, 53)) is a,
          "hit area did not follow width change")
    a.width = 46


def test_top_strand_stroke_edge_wins_over_lower_body():
    # a (bottom) covers y in [-27, 27]; b (top) at y=48 covers [21, 75].
    a = make_strand((0, 0), (400, 0), 1, "1_1")
    b = make_strand((0, 48), (400, 48), 2, "2_1")

    # (200, 22): visually b's stroke edge drawn over a's body.
    # Old code: b missed (26 > 23) and the click fell through to a.
    check("click on top strand's stroke edge selects the top strand",
          top_hit([a, b], (200, 22)) is b,
          "click fell through to the strand below")
    check("both strands reported, topmost first",
          names(hits([a, b], (200, 22))) == ["2_1", "1_1"],
          "z-order wrong: %s" % names(hits([a, b], (200, 22))))
    # A point only on the bottom strand still selects it
    check("point only on bottom strand selects it",
          top_hit([a, b], (200, -20)) is a,
          "bottom strand not selectable")


def test_angled_touching_decorations_do_not_destroy_body_hits():
    """Regression for masknotworkingexample.json's angled side-lines."""
    strands = make_mask_bug_fixture()
    by_name = {strand.layer_name: strand for strand in strands}

    for layer_name, point in (
            ("1_1", (1414, 322)),
            ("2_1", (1302, 588)),
            ("1_4", (1316, 364))):
        strand = by_name[layer_name]
        check("angled %s body midpoint is selectable" % layer_name,
              top_hit(strands, point) is strand,
              "hits: %s" % names(hits(strands, point)))
        check("angled %s composite highlight retains its body" % layer_name,
              strand.get_selection_path().contains(QPointF(*point)),
              "non-Boolean composite lost its body")

    shared = (by_name["2_1"].end.x(), by_name["2_1"].end.y())
    check("shared 2_1/2_2 endpoint still selects topmost 2_2",
          top_hit(strands, shared) is by_name["2_2"],
          "hits: %s" % names(hits(strands, shared)))


# ------------------------------------------------------------------- case #1:
# no invisible 120x120 square around an attached strand's start
def test_attached_strand_has_no_invisible_square():
    low = make_strand((0, 0), (400, 0), 1, "1_1")

    parent = make_strand((200, 300), (200, 40), 2, "2_1")
    attached = AttachedStrand(parent, QPointF(200, 40), 0)
    attached.end = QPointF(200, 300)
    parent.attached_strands.append(attached)

    strands = [low, parent, attached]  # attached is topmost

    # Click at (200, 0): on low's body; 40px from attached's start.
    # Attached visible radius is 27, so nothing of attached is rendered there.
    # Old code: attached's invisible 120x120 square claimed the click.
    check("click on lower strand's body is not stolen by attached start square",
          top_hit(strands, (200, 0)) is low,
          "attached strand still claims clicks it doesn't render")

    # Clicking on the attached strand's real start circle still works.
    check("attached strand start circle (r=27) still selectable at 20px",
          top_hit(strands, (200, 30)) is attached,
          "attached start no longer selectable")

    # 40px from start, past the visible circle, on nothing else -> no hit
    # (points x-offset so it's off low's body and off attached's body).
    check("40px away from attached start (empty pixel) is a miss",
          top_hit([parent, attached], (160, 0)) is None,
          "invisible zone still active around attached start")


# ------------------------------------------------------------------- case #3:
# masked strand clickable on full rendered footprint incl. stroke edge
def test_mask_stroke_edge_is_clickable():
    s1 = make_strand((0, 0), (400, 0), 1, "1_1")
    s2 = make_strand((200, -200), (200, 200), 2, "2_1")
    mask = MaskedStrand(s1, s2)
    strands = [s1, s2, mask]

    fill = mask.get_mask_path()
    stroke = mask.get_mask_path_stroke()
    check("mask paths are non-empty", not fill.isEmpty() and not stroke.isEmpty(),
          "mask geometry did not build")

    # Center of the intersection: mask is topmost -> mask wins.
    check("center of mask selects the mask",
          top_hit(strands, (200, 0)) is mask,
          "mask not selected at its center")

    # Find a rendered-stroke-only point (in stroke path, not in fill path).
    edge_point = None
    for dx in range(-30, 31):
        for dy in range(-30, 31):
            p = QPointF(200 + dx, 0 + dy)
            if stroke.contains(p) and not fill.contains(p):
                edge_point = p
                break
        if edge_point:
            break
    check("a stroke-only edge point exists", edge_point is not None,
          "could not find stroke-edge point; mask geometry unexpected")

    if edge_point:
        # Old code hit-tested only the fill path, so this fell through.
        check("click on mask's stroke edge selects the mask",
              top_hit(strands, (edge_point.x(), edge_point.y())) is mask,
              "mask stroke edge fell through to strand below")

    # Away from the intersection the component strand is selected normally.
    check("outside the mask, component strand is selected",
          top_hit(strands, (100, 0)) is s1,
          "component strand not selectable outside mask")


# ----------------------------------------------------------------------- misc
def test_hidden_strands_are_skipped():
    a = make_strand((0, 0), (400, 0), 1, "1_1")
    b = make_strand((0, 10), (400, 10), 2, "2_1")
    b.is_hidden = True
    check("hidden top strand is skipped",
          top_hit([a, b], (200, 5)) is a,
          "hidden strand still hit-tested")


def test_select_mode_press_selects_topmost():
    canvas = DummyCanvas()
    a = make_strand((0, 0), (400, 0), 1, "1_1")
    b = make_strand((0, 20), (400, 20), 2, "2_1")
    canvas.strands = [a, b]
    mode = SelectMode(canvas)

    emitted = []
    mode.strand_selected.connect(lambda idx: emitted.append(idx))

    class FakeEvent:
        def __init__(self, x, y):
            self._p = QPointF(x, y)

        def pos(self):
            return self._p

    # Overlap point: both strands contain (200, 10); topmost (b) must win.
    mode.mousePressEvent(FakeEvent(200, 10))
    check("press on overlap selects topmost strand",
          b.is_selected and not a.is_selected,
          "wrong strand selected on overlap")
    check("selection signal carries topmost index",
          emitted == [1], "emitted: %s" % emitted)

    # Empty area deselects.
    mode.mousePressEvent(FakeEvent(200, 400))
    check("press on empty area deselects",
          emitted[-1] == -1 and not b.is_selected,
          "empty-area click did not deselect")


# --------------------------------------------------- end decorations footprint
# The rendered strand includes, per end, either a cap circle (when drawn) or a
# side line band (stroke_width thick, just past the flat cap). The selection /
# hover footprint must union exactly what is drawn - for every combination.

def test_side_line_footprint_cases():
    # Default strand (100,0)-(400,0): no circles, both side lines visible.
    # Side line band: stroke 4 -> covers 4px just past each flat cap, spanning
    # the full visible width (y in [-27, 27]).
    s = make_strand((100, 0), (400, 0), 1, "1_1")

    check("start side line: 2px past the cap is a hit",
          top_hit([s], (98, 0)) is s, "side line not part of footprint")
    check("start side line: full visible width is covered (y=26)",
          top_hit([s], (98, 26)) is s, "side line band too narrow")
    check("start side line: past the band is a miss (6px)",
          top_hit([s], (94, 0)) is None, "footprint extends past the side line")
    check("end side line: 2px past the cap is a hit",
          top_hit([s], (402, 0)) is s, "end side line not part of footprint")
    check("end side line: past the band is a miss",
          top_hit([s], (406, 0)) is None, "footprint extends past the side line")

    # Side lines hidden -> the footprint ends exactly at the flat cap.
    s2 = make_strand((100, 0), (400, 0), 1, "1_2")
    s2.start_line_visible = False
    s2.end_line_visible = False
    check("hidden start side line: past the cap is a miss",
          top_hit([s2], (98, 0)) is None, "hidden side line still clickable")
    check("hidden end side line: past the cap is a miss",
          top_hit([s2], (402, 0)) is None, "hidden side line still clickable")
    check("hidden side lines: body itself still selectable",
          top_hit([s2], (250, 0)) is s2, "body lost")


def test_end_circle_footprint_cases():
    # End circle via an attached child at the end (junction circle).
    parent = make_strand((100, 0), (400, 0), 1, "1_1")
    child = AttachedStrand(parent, QPointF(400, 0), 1)
    parent.attached_strands.append(child)
    parent.has_circles[1] = True

    # Circle radius = 27; a point 20px past the end is inside the drawn circle.
    check("end circle (junction): 20px past the end is a hit",
          parent.get_selection_path().contains(QPointF(420, 0)),
          "junction end circle not part of footprint")
    check("end circle (junction): 30px past the end is a miss",
          not parent.get_selection_path().contains(QPointF(430, 0)),
          "footprint larger than the drawn circle")

    # Start circle via a closed connection.
    s = make_strand((100, 0), (400, 0), 2, "2_1")
    s.has_circles[0] = True
    s.closed_connections = [True, False]
    check("start circle (closed connection): 20px behind the start is a hit",
          top_hit([s], (80, 0)) is s, "closed-connection circle not in footprint")

    # has_circles set but the circle is NOT drawn (no junction, not closed):
    # nothing is rendered past the cap (side line is suppressed by the flag).
    s3 = make_strand((100, 0), (400, 0), 3, "3_1")
    s3.has_circles[0] = True
    check("has_circles without junction: nothing rendered past the cap",
          top_hit([s3], (80, 0)) is None and top_hit([s3], (98, 0)) is None,
          "undrawn circle or suppressed side line still clickable")

    # Transparent circle stroke suppresses the drawn circle.
    s4 = make_strand((100, 0), (400, 0), 4, "4_1")
    s4.has_circles[0] = True
    s4.closed_connections = [True, False]
    s4.start_circle_stroke_color = QColor(0, 0, 0, 0)
    check("transparent circle stroke: circle not part of footprint",
          top_hit([s4], (80, 0)) is None, "transparent circle still clickable")


def test_attached_strand_footprint_cases():
    parent = make_strand((200, 300), (200, 40), 1, "1_1")
    attached = AttachedStrand(parent, QPointF(200, 40), 0)
    attached.end = QPointF(200, 300)
    parent.attached_strands.append(attached)

    # Attached strands always draw their start circle (default): 20px behind
    # the start (radius 27) is inside it.
    check("attached start circle: 20px behind the start is a hit",
          attached.get_selection_path().contains(QPointF(200, 20)),
          "attached start circle not part of footprint")

    # End side line of the attached strand (no end circle): 2px past the end.
    attached.update_side_line()
    check("attached end side line: 2px past the end is a hit",
          attached.get_selection_path().contains(QPointF(200, 302)),
          "attached end side line not part of footprint")
    attached.end_line_visible = False
    check("attached hidden end side line: past the cap is a miss",
          not attached.get_selection_path().contains(QPointF(200, 302)),
          "hidden end side line still clickable")
    attached.end_line_visible = True

    # Folded start (stroke visible): full stroked circle, radius 27.
    check("attached folded start circle: 25px behind the start is a hit (r=27)",
          attached.get_selection_path().contains(QPointF(200, 15)),
          "folded start circle ring not in footprint")

    # Unfolded start edge (transparent stroke): draw() still renders the inner
    # fill circle (radius width/2 = 23, no stroke) so the start blends into
    # the parent - the fill circle must stay in the footprint, the stroke
    # ring must not.
    attached.start_circle_stroke_color = QColor(0, 0, 0, 0)
    check("attached unfolded start: inner fill circle is a hit (20px, r=23)",
          attached.get_selection_path().contains(QPointF(200, 20)),
          "unfolded fill circle not united into footprint")
    check("attached unfolded start: stroke ring is excluded (25px)",
          not attached.get_selection_path().contains(QPointF(200, 15)),
          "unfolded footprint still includes the hidden stroke ring")
    attached.start_circle_stroke_color = QColor(0, 0, 0, 255)

    # Attached draw() keeps the inner end-cap fill whenever the end circle is
    # enabled, even if that circle's outline is transparent.  The selection
    # overlay must cover that visible fill instead of stopping at the flat body.
    attached.has_circles[1] = True
    attached.end_circle_stroke_color = QColor(0, 0, 0, 0)
    check("attached transparent end: inner fill circle is a hit (20px, r=23)",
          attached.get_selection_path().contains(QPointF(200, 320)),
          "transparent end fill is missing from the footprint")
    check("attached transparent end: hidden stroke ring is excluded (25px)",
          not attached.get_selection_path().contains(QPointF(200, 325)),
          "transparent end footprint includes the hidden stroke ring")


def test_hover_covers_decorations():
    """Hover (select mode) must trigger on decorations, and the yellow
    highlight uses the same footprint path, so they can never disagree."""
    canvas = DummyCanvas()
    s = make_strand((100, 0), (400, 0), 1, "1_1")
    s.has_circles[1] = True
    child = AttachedStrand(s, QPointF(400, 0), 1)
    s.attached_strands.append(child)
    canvas.strands = [s, child]
    mode = SelectMode(canvas)

    class FakeMove:
        def __init__(self, x, y):
            self._p = QPointF(x, y)

        def pos(self):
            return self._p

    mode.mouseMoveEvent(FakeMove(98, 0))     # start side line band
    check("hover on start side line highlights the strand",
          mode.hovered_strand is s,
          "hovered: %r" % (mode.hovered_strand and mode.hovered_strand.layer_name))

    mode.mouseMoveEvent(FakeMove(420, 0))    # end junction circle
    check("hover on end circle highlights a strand at that point",
          mode.hovered_strand in (s, child),
          "hovered: %r" % (mode.hovered_strand and mode.hovered_strand.layer_name))

    mode.mouseMoveEvent(FakeMove(250, 200))  # empty area
    check("hover on empty area clears the highlight",
          mode.hovered_strand is None, "hover not cleared")


def test_composite_highlight_border_has_no_internal_seams():
    """The overlay border follows the union silhouette, not each component."""
    footprint = QPainterPath()
    footprint.addRect(20, 20, 100, 20)
    cap = QPainterPath()
    cap.addEllipse(QPointF(20, 30), 10, 10)
    footprint.addPath(cap)

    outline = selection_outline_path(footprint, 2)
    check("highlight border includes the outside silhouette",
          outline.contains(QPointF(9, 30)),
          "outside edge is missing")
    check("highlight border excludes the internal cap seam",
          not outline.contains(QPointF(30, 30)),
          "overlapping cap edge was outlined inside the body")


# ------------------------------------------------------------------ mask mode
class FakePress:
    def __init__(self, x, y):
        self._p = QPointF(x, y)

    def pos(self):
        return self._p


def test_mask_mode_overlap_selects_topmost():
    """Overlapping strands no longer cancel the click (old '== 1' rule)."""
    canvas = DummyCanvas()
    a = make_strand((0, 0), (400, 0), 1, "1_1")
    b = make_strand((0, 20), (400, 20), 2, "2_1")
    canvas.strands = [a, b]
    mode = MaskMode(canvas, None)

    # (200, 10) is inside both strands - old code cleared the selection here.
    mode.handle_mouse_press(FakePress(200, 10))
    check("mask mode: overlap click selects the topmost strand",
          mode.selected_strands == [b],
          "selected: %s" % [s.layer_name for s in mode.selected_strands])

    # Second click on the other strand completes the pair (no crash without
    # a connected mask_created handler).
    mode.handle_mouse_press(FakePress(200, -20))
    check("mask mode: second click adds the second strand",
          mode.selected_strands == [b, a],
          "selected: %s" % [s.layer_name for s in mode.selected_strands])

    # Empty area clears.
    mode.clear_selection()
    mode.handle_mouse_press(FakePress(200, 400))
    check("mask mode: empty-area click clears selection",
          mode.selected_strands == [],
          "selection not cleared")


def test_mask_mode_matches_select_mode():
    """Mask mode hit-testing must equal select mode minus masked strands."""
    canvas = DummyCanvas()
    s1 = make_strand((0, 0), (400, 0), 1, "1_1")
    s2 = make_strand((200, -200), (200, 200), 2, "2_1")
    mask = MaskedStrand(s1, s2)
    hidden = make_strand((0, 5), (400, 5), 3, "3_1")
    hidden.is_hidden = True
    canvas.strands = [s1, s2, mask, hidden]

    select = SelectMode(canvas)
    mode = MaskMode(canvas, None)

    for point in [(200, 0), (100, 0), (200, 100), (200, 22), (350, -10)]:
        p = QPointF(*point)
        from_select = [(s, t) for s, t in select.find_strands_at_point(p)
                       if not isinstance(s, MaskedStrand)]
        from_mask = mode.find_strands_at_point(p)
        check("mask mode == select mode (minus masks) at %s" % (point,),
              from_mask == from_select,
              "select: %s mask: %s" % ([s.layer_name for s, _ in from_select],
                                       [s.layer_name for s, _ in from_mask]))

    # At the mask center, mask mode must pick the topmost component strand,
    # never the masked strand itself.
    mode.handle_mouse_press(FakePress(200, 0))
    check("mask mode: click over a mask selects topmost component strand",
          mode.selected_strands == [s2],
          "selected: %s" % [s.layer_name for s in mode.selected_strands])

    # Hidden strands are skipped (old mask mode did not filter them).
    mode.clear_selection()
    mode.handle_mouse_press(FakePress(300, 5))
    check("mask mode: hidden strand is not selected",
          mode.selected_strands == [s1],
          "selected: %s" % [s.layer_name for s in mode.selected_strands])


# ----------------------------------------------------------------------- main
def main():
    test_body_matches_rendered_thickness()
    test_top_strand_stroke_edge_wins_over_lower_body()
    test_angled_touching_decorations_do_not_destroy_body_hits()
    test_attached_strand_has_no_invisible_square()
    test_mask_stroke_edge_is_clickable()
    test_hidden_strands_are_skipped()
    test_select_mode_press_selects_topmost()
    test_side_line_footprint_cases()
    test_end_circle_footprint_cases()
    test_attached_strand_footprint_cases()
    test_hover_covers_decorations()
    test_composite_highlight_border_has_no_internal_seams()
    test_mask_mode_overlap_selects_topmost()
    test_mask_mode_matches_select_mode()

    print("\n%d passed, %d failed" % (_PASS, _FAIL))
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
