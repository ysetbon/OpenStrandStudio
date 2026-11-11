"""Knots that join cords or make a loop: the ready-made drawings in bends.py.

A drawing here is never trusted because it looks right. Three things are
checked, each on its own evidence:

1. The references. What each knot's crossings must be was worked out from how
   the knot is tied; these tests hold that against what is known about the
   knot from elsewhere: a square knot closes to the square knot (a trefoil and
   its mirror image, its Jones polynomial the same read backwards) and the
   granny to two trefoils of one hand; a bowline with its loop cut open is a
   sheet bend; each cord of a fisherman's knot is an overhand knot with the
   other cord through it; the working cords of a macrame square knot, the
   fillers taken away, are a square knot.
2. The drawings against the references: crossing counts per cord and between
   cords, and over or under at every crossing, letter for letter.
3. The built designs: every tying step read back from its strands, masks and
   layers the way the app draws them, and its masks checked.
"""
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_bends_test_")

ROOT = Path(__file__).resolve().parents[1]
for folder in (ROOT, ROOT / "scripts", ROOT / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from openstrand import bends, check, draw, identify, invariants, masks, project  # noqa: E402

GUIDE = ROOT / ".claude" / "skills" / "openstrand-designer" / "drawing.md"
TREFOIL, CINQUEFOIL, SQUARE_OR_GRANNY = (1, -1, 1), (1, -1, 1, -1, 1), (1, -2, 3, -2, 1)

# What each drawing must show, written down apart from the drawings: how many
# cords, how often each crosses itself, how often each two cross each other,
# and over (O) or under (U) at every crossing each cord passes, in order from
# its first point.
EXPECTED = {
    "square": dict(own=(0, 0), between={(0, 1): 6}, passes=("OUOOUO", "UOUUOU")),
    "granny": dict(own=(0, 0), between={(0, 1): 6}, passes=("OUOUOU", "OUOUOU")),
    "sheet bend": dict(own=(0, 1), between={(0, 1): 6}, passes=("OUOUUO", "UOOUUOUO")),
    "bowline": dict(own=(7,), between={}, passes=("OUUOOUOUUOUOOU",)),
    "fisherman": dict(own=(3, 3), between={(0, 1): 8}, passes=("OOUUOOUUOUOOUU", "OOUUOOUUOUOOUU")),
    "double fisherman": dict(own=(5, 5), between={(0, 1): 8},
                             passes=("OOUUOOUOUUOUOOUOUU", "OOUUOOUOUUOUOOUOUU")),
    "macrame square": dict(own=(0, 0, 0, 0), between={(0, 1): 2, (0, 2): 2, (0, 3): 6, (1, 3): 2, (2, 3): 2},
                           passes=("UOOOUUOOOU", "UOUO", "UOUO", "OUUUOOUUUO")),
}
STEPS = {"square": 4, "granny": 4, "sheet bend": 4, "bowline": 4, "fisherman": 5, "double fisherman": 5,
         "macrame square": 5}


def counts(code):
    """(crossings of each cord with itself, {(a, b): crossings between cords a and b})."""
    own = [0] * len(code["passes"])
    between = {}
    for a, b in code["between"]:
        if a == b:
            own[a] += 1
        else:
            key = (min(a, b), max(a, b))
            between[key] = between.get(key, 0) + 1
    return tuple(own), between


def joined(lines):
    """Two cords made one closed cord: the first, round over the top to the
    start of the second, the second, round under the bottom to the start of
    the first. The arcs pass outside everything, so they add no crossing."""
    a, b = lines
    top, bottom = min(a[:, 1].min(), b[:, 1].min()) - 200, max(a[:, 1].max(), b[:, 1].max()) + 200
    left, right = min(a[:, 0].min(), b[:, 0].min()) - 150, max(a[:, 0].max(), b[:, 0].max()) + 150
    over = np.array([[left, (top + a[-1, 1]) / 2, 0], [600, top, 0], [right, (top + b[0, 1]) / 2, 0]], dtype=float)
    under = np.array([[right, (bottom + b[-1, 1]) / 2, 0], [600, bottom, 0], [left, (bottom + a[0, 1]) / 2, 0]],
                     dtype=float)
    return np.vstack([a, over, b, under])


def read_backwards(polynomial):
    return dict(sorted((-power, c) for power, c in polynomial.items()))


# ------------------------------------------------- the library and its names
def test_the_library_has_the_knots_people_ask_for():
    assert set(bends.LIBRARY) == set(EXPECTED)
    listed = {key: (title, kind, cords, crossings) for key, title, kind, cords, crossings, _, _ in bends.library()}
    assert listed["square"] == ("Square knot", "joins two cords", 2, 6)
    assert listed["bowline"] == ("Bowline", "a loop in one cord", 1, 7)
    assert listed["macrame square"] == ("Macrame square knot", "tied round two filler cords", 4, 14)
    assert bends.full_title("fisherman") == "Fisherman's knot (magic knot)"


@pytest.mark.parametrize("name, key", [
    ("magic knot", "fisherman"), ("Magic Knot tutorial", "fisherman"), ("fisherman's knot", "fisherman"),
    ("fishermans knot", "fisherman"), ("Fisherman’s knot", "fisherman"), ("Reef knot", "square"),
    ("square knot", "square"), ("how to tie a square knot", "square"), ("granny", "granny"),
    ("sheet bend", "sheet bend"), ("Sheet-Bend", "sheet bend"), ("weaver's knot", "sheet bend"),
    ("how to tie a bowline", "bowline"), ("how do I tie a bowline", "bowline"), ("Bowline knot", "bowline"),
    ("double fisherman's", "double fisherman"), ("double fisherman's bend", "double fisherman"),
    ("grapevine knot", "double fisherman"), ("grapevine", "double fisherman"),
    ("macrame square knot", "macrame square"), ("Macramé square knot", "macrame square"),
    ("cobra knot", "macrame square"),
    # Written as one word, or as two.
    ("sheetbend", "sheet bend"), ("squareknot", "square"), ("magicknot", "fisherman"), ("bow line", "bowline"),
    # Other knots, though their names are close: the fisherman's bend is the anchor hitch.
    ("fisherman's bend", None), ("double sheet bend", None), ("flat knot", None),
    ("zeppelin bend", None), ("overhand", None), ("double overhand", None), ("", None),
    # A knot of the craft library (craft_library/<craft>/recipes/), by its names.
    ("carrick bend", "josephine_knot"), ("cow hitch", "larks_head_knot"),
    # Bowlines of the craft library: each its own knot, not the bowline.
    ("running bowline", "running_bowline"), ("bowline on a bight", "bowline_on_a_bight"),
    ("double bowline", "double_bowline"), ("surgeon's knot", "surgeons_knot")])
def test_knots_are_found_by_the_names_people_use(name, key):
    assert bends.find(name) == key


# --------------------------------------- the drawings against their references
@pytest.mark.parametrize("key", list(EXPECTED))
def test_every_drawing_passes_its_crossings_as_its_reference_says(key):
    code = bends.reference(key)          # raises when the drawing has drifted from the library's own patterns
    want = EXPECTED[key]
    assert tuple(invariants.pattern(code, k) for k in range(len(code["passes"]))) == want["passes"]
    assert tuple(bends.LIBRARY[key]["patterns"]) == want["passes"]
    assert counts(code) == (want["own"], want["between"])
    # A drawing the fitter can follow: crossings well apart, none shallow, each clearly over or under.
    width = bends.LIBRARY[key]["width"]
    lines = bends.centrelines(key)
    found = invariants.crossings(lines)
    points = [c["point"] for c in found]
    apart = min(math.dist(p, q) for n, p in enumerate(points) for q in points[n + 1:])
    assert apart >= 2.4 * width, f"{key}: two crossings {apart:.0f} px apart"
    assert min(c["angle"] for c in found) >= 45
    assert min(abs(c["heights"][0] - c["heights"][1]) for c in found) >= 0.5


def test_a_drawing_that_drifts_from_its_reference_is_an_error(monkeypatch):
    wrong = dict(bends.LIBRARY["square"], patterns=("OUOUOU", "OUOUOU"))
    monkeypatch.setitem(bends.LIBRARY, "square", wrong)
    with pytest.raises(bends.BendError, match="not as its reference"):
        bends.reference("square")


# ------------------------------------------------------ the references themselves
def test_a_square_knot_closes_to_the_square_knot_and_a_granny_to_the_granny():
    """Joined end to end both are two overhand knots, which the Alexander
    polynomial cannot tell apart. The Jones polynomial can: the square knot is
    a trefoil and its mirror image (the polynomial reads the same backwards),
    the granny two trefoils of the same hand."""
    trefoil = {4: 1, 12: 1, 16: -1}                                    # t + t^3 - t^4
    product = lambda p, q: {a + b: sum(x * y for (i, x) in p.items() for (j, y) in q.items() if i + j == a + b)
                            for a in p for b in q}
    square = joined(bends.centrelines("square"))
    granny = joined(bends.centrelines("granny"))
    assert invariants.alexander(square, closed=True) == SQUARE_OR_GRANNY
    assert invariants.alexander(granny, closed=True) == SQUARE_OR_GRANNY
    v_square = invariants.jones(invariants.code_of([square], [True]))
    v_granny = invariants.jones(invariants.code_of([granny], [True]))
    assert v_square == product(trefoil, read_backwards(trefoil)) == read_backwards(v_square)
    assert v_granny in (product(trefoil, trefoil), read_backwards(product(trefoil, trefoil)))
    assert v_granny != read_backwards(v_granny)


def test_the_two_half_knots_of_a_square_knot_mirror_each_other_and_a_grannys_do_not():
    square, granny = bends.reference("square"), bends.reference("granny")
    # Three crossings each: the lower legs, then the upper legs (cord 1 passes them in that order).
    lower, upper = [k for k, _ in square["passes"][0][:3]], [k for k, _ in square["passes"][0][3:]]
    hands = lambda code, ks: {code["hand"][k] for k in ks}
    assert len(hands(square, lower)) == len(hands(square, upper)) == 1 and hands(square, lower) != hands(square, upper)
    assert hands(granny, lower) == hands(granny, upper)
    # The same picture, three crossings the other way round.
    found = invariants.compare(granny, square)
    assert found is not None and len(found["flipped"]) == 3
    # Woven over, under, over, as draw does unless told otherwise, the picture is the granny.
    assert all(p in ("OUOUOU", "UOUOUO") for p in (invariants.pattern(granny, 0), invariants.pattern(granny, 1)))
    assert invariants.pattern(square, 0) not in ("OUOUOU", "UOUOUO")
    # Both ends of each cord on the same side of the other's turn: over it (cord 1), under it (cord 2).
    assert [invariants.pattern(square, 0)[i] for i in (0, 5)] == ["O", "O"]
    assert [invariants.pattern(square, 1)[i] for i in (2, 3)] == ["U", "U"]


def test_the_working_cord_of_a_sheet_bend_goes_behind_both_legs_and_under_itself():
    code = bends.reference("sheet bend")
    bight, working = code["passes"]
    assert not any(code["between"][k][0] == code["between"][k][1] == 0 for k, _ in bight)   # the bight never crosses itself
    (own,) = [k for k, (a, b) in enumerate(code["between"]) if a == b == 1]
    letters = invariants.pattern(code, 1)
    first, second = [n for n, (k, _) in enumerate(working) if k == own]
    assert letters[first] == "O" and letters[second] == "U"                # tucked under its own standing part
    assert letters[0] == "U"                                               # it comes up from under the bight's turn
    assert "UU" in letters[first:second]                                   # behind both legs, one after the other
    assert letters not in ("OUOUOUOU", "UOUOUOUO")                         # so it does not alternate
    assert letters[-1] == "O"                                              # its end lies over the bight


def test_a_bowline_with_its_loop_cut_open_is_a_sheet_bend():
    """The two knots have one structure: join the working cord's end of a
    sheet bend to the bight's standing part and there is a bowline. So cutting
    the bowline's loop at its lowest point must leave the sheet bend's
    crossings, every one the same way (as its mirror image, since a bowline is
    drawn with the end going behind the standing part)."""
    (line,) = bends.centrelines("bowline")
    lowest = int(np.argmax(line[:, 1]))
    cut = invariants.code_of([line[:lowest], line[lowest + 1:]])
    found = invariants.compare(cut, bends.reference("sheet bend"))
    assert found is not None and found["flipped"] == []
    # The end lies inside the loop: between the loop's two sides at its own height.
    end = line[-1]
    level = [x for (x0, y0, _), (x1, y1, _) in zip(line[:-60], line[1:-59]) if (y0 - end[1]) * (y1 - end[1]) <= 0
             for x in [x0]]
    assert min(level) < end[0] < max(level)


@pytest.mark.parametrize("key, knot", [("fisherman", TREFOIL), ("double fisherman", CINQUEFOIL)])
def test_each_cord_of_a_fishermans_knot_is_tied_round_the_other(key, knot):
    code = bends.reference(key)
    lines = bends.centrelines(key)
    for cord, other in ((0, 1), (1, 0)):
        assert invariants.alexander(lines[cord]) == knot                 # an overhand knot (a double one) on its own
        loops = invariants.through(code, cord, other)
        assert all(abs(times) == 1 for times in loops.values())          # the other cord through every loop of it
    # The knot looks the same turned half round: each cord is the other.
    swapped = invariants.code_of([lines[1], lines[0]])
    assert invariants.compare(swapped, code) == dict(flipped=[], mirror=False, cords=[0, 1], backwards=[])
    # The other cord goes over the near side of the knot and under its far side: through its middle.
    assert invariants.pattern(code, 0).startswith("OOUU")


def test_the_working_cords_of_a_macrame_square_knot_are_a_square_knot_round_the_fillers():
    code = bends.reference("macrame square")
    workers = invariants.sub_code(code, [0, 3])
    found = invariants.compare(workers, bends.reference("square"))
    assert found is not None and found["flipped"] == []
    for filler in (1, 2):
        tops = {top for top, under in code["between"] if filler in (top, under)}
        unders = {under for top, under in code["between"] if filler in (top, under)}
        assert tops == {0, filler} and unders == {filler, 3}             # left cord in front, right cord behind
    assert (1, 2) not in counts(code)[1]                                 # the fillers do not cross each other


# -------------------------------------------------------------- comparing codes
def test_the_same_knot_is_the_same_however_it_is_numbered_run_or_seen():
    lines = bends.centrelines("sheet bend")
    code = bends.reference("sheet bend")
    same = dict(flipped=[], mirror=False)
    flip_x = lambda line: np.c_[1200 - line[:, 0], line[:, 1:]]
    for other, mirror in (([lines[1], lines[0]], False),                                   # numbered the other way
                          ([lines[0][::-1], lines[1]], False),                              # a cord run backwards
                          ([np.c_[flip_x(line)[:, :2], -line[:, 2]] for line in lines], False),   # seen from the back
                          ([flip_x(line) for line in lines], True),                         # in a mirror
                          ([np.c_[line[:, :2], -line[:, 2]] for line in lines], True)):     # every crossing turned over
        found = invariants.compare(invariants.code_of(other), code)
        assert found is not None and (found["flipped"], found["mirror"]) == (same["flipped"], mirror)
    # One crossing the other way round is found, and named by its number in the drawing compared.
    turned = [line.copy() for line in lines]
    x, y = code["points"][2]
    near = np.hypot(turned[1][:, 0] - x, turned[1][:, 1] - y) < 30
    turned[1][near, 2] *= -1
    found = invariants.compare(invariants.code_of(turned), code)
    assert found is not None and len(found["flipped"]) == 1
    assert invariants.code_of(turned)["points"][found["flipped"][0]] == pytest.approx((x, y), abs=2)
    # A different knot altogether is not compared crossing by crossing.
    assert invariants.compare(bends.reference("square"), code) is None


def test_a_cord_through_a_loop_is_told_from_one_lying_across_it():
    from sample_geometry import spline
    loop = np.array(spline([(300, 500), (500, 440), (700, 330), (780, 400), (700, 470), (500, 360), (300, 300)],
                           spacing=4.0))
    loop = np.c_[loop, np.linspace(0, 1, len(loop))]                         # it crosses itself once, the end on top
    assert len(invariants.crossings([loop])) == 1
    through = np.array([(700, 200, 5.0), (700, 395, 5.0), (700, 405, -5.0), (700, 600, -5.0)])
    across = np.array([(700, 200, 5.0), (700, 600, 5.0)])
    beside = np.array([(900, 200, 5.0), (900, 600, -5.0)])
    assert list(invariants.through(invariants.code_of([loop, through]), 0, 1).values()) in ([1.0], [-1.0])
    assert list(invariants.through(invariants.code_of([loop, across]), 0, 1).values()) == [0.0]
    assert list(invariants.through(invariants.code_of([loop, beside]), 0, 1).values()) == [0.0]


# ------------------------------------------------------------- built designs
@pytest.fixture(scope="module")
def tied():
    """Every library knot tied once for the tests that look at the built designs."""
    return {key: bends.tie(key) for key in EXPECTED}


@pytest.mark.parametrize("key", list(EXPECTED))
def test_every_knot_ties_and_every_step_reads_back_as_the_knot(tied, key):
    made = tied[key]
    assert made["ok"], made["checks"]
    assert made["key"] == key and made["crossings"] == sum(len(p) for p in EXPECTED[key]["passes"]) // 2
    steps = made["steps"]
    assert [s["title"] for s in steps] == [f"Step {n}" for n in range(1, STEPS[key] + 1)]
    assert all(s["caption"].endswith(".") and len(s["caption"]) > 20 for s in steps)
    assert [c["stage"] for c in made["checks"][1:]] == [f"step {n} as drawn in the app" for n in range(1, len(steps) + 1)]
    whole = bends.reference(key)
    shown = [len(identify.code(s["data"])["hand"]) for s in steps]
    assert shown == sorted(shown) and shown[-1] == len(whole["hand"])       # the knot grows step by step
    for n, step in enumerate(steps, start=1):
        data = step["data"]
        assert check.problems(data) == []                                   # the app loads it cleanly
        assert masks.check(data)["problems"] == []                          # every crossing drawn right all over
        assert data["project_settings"]["version"] == 1
        arrows = [s for s in data["strands"] if s.get("end_arrow_visible") or s.get("start_arrow_visible")]
        assert len(arrows) <= 1 and (not arrows or n < len(steps))          # the working end, never the finished knot
    # The finished knot, read back from its strands, masks and layers: every crossing as the reference has it.
    last = steps[-1]["data"]
    found = invariants.compare(identify.code(last), whole)
    assert found is not None and found["flipped"] == [] and not found["mirror"]
    named = identify.named(last)
    assert (named["key"], named["how"]) == (key, "exact")
    assert identify.summary(last).splitlines()[0].startswith(bends.full_title(key) + ":")
    # Its cords are numbered as the drawing's are, and run the same way: cord 1 is the library's cord 1.
    assert [c["pattern"] for c in identify.cords(last)] == list(EXPECTED[key]["passes"])
    assert set(project.describe(last)["groups"]) == {label for label, _ in bends.LIBRARY[key]["cords"]}


def test_a_step_that_does_not_come_out_as_the_knot_is_reported(monkeypatch):
    real = bends.check
    monkeypatch.setattr(bends, "check", lambda data, expected: (False, "1 crossing drawn the other way round")
                        if len(expected["hand"]) == 4 else real(data, expected))
    made = bends.tie("square")
    assert not made["ok"]
    assert [c["stage"] for c in made["checks"] if not c["ok"]] == ["step 3 as drawn in the app"]
    assert "NOT AS THE REFERENCE" in bends.checked(made)


def test_colors_and_width_can_be_chosen():
    made = bends.tie("macrame square", colors=["crimson", "sky"], width=18)
    sets = project.describe(made["steps"][-1]["data"])["sets"]
    by_color = sorted(tuple(s["colors"]) for s in sets.values())
    assert by_color == sorted([("#c83e4d",), ("#4aa3df",), ("#4aa3df",), ("#d56272",)])   # left, fillers, right (its own)
    assert {s["width"] for s in made["steps"][-1]["data"]["strands"] if s["type"] != "MaskedStrand"} == {18}
    with pytest.raises(bends.BendError, match="3 colours to choose"):
        bends.tie("macrame square", colors=["red", "gold", "teal", "pink"], build=False)
    with pytest.raises(bends.BendError, match="between 14 and 30"):
        bends.tie("square", width=50, build=False)
    with pytest.raises(bends.BendError, match="not one of the ready-made knots"):
        bends.tie("zeppelin bend")
    with pytest.raises(ValueError, match="unknown color"):
        bends.tie("square", colors=["sparkly"], build=False)


# ---------------------------------------------------------------- recognising
def guide_example(name):
    text = GUIDE.read_text(encoding="utf-8")
    specs = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S) if '"cords"' in block]
    return next(s for s in specs if s.get("name") == name)


def test_the_square_knot_in_the_drawing_guide_is_a_square_knot_and_woven_plainly_a_granny():
    spec = guide_example("square knot")
    data, report = draw.build(spec)
    assert "pattern OUOOUO" in report and "pattern UOUUOU" in report and "mask check: no problems" in report
    named = identify.named(data)
    assert (named["key"], named["how"]) == ("square", "exact")
    text = identify.summary(data)
    assert text.splitlines()[0] == "Square knot (reef knot): all 6 crossings go as in the checked drawing of this knot."
    assert "cords 1 and 2 cross 6 times" in text and "not knotted on its own" in text
    # The check numbers the cords as the drawing's report does, whichever lies lower in the layers:
    # what it says of cord 1 is about the cord the report calls cord 1.
    assert [c["pattern"] for c in identify.cords(data)] == ["OUOOUO", "UOUUOU"]
    turned = json.loads(json.dumps(spec))
    turned["cords"][0]["pattern"] = "OUOOUU"            # the first cord's last crossing the other way round
    other, report = draw.build(turned)
    assert "cord 1 (First cord): 9 strands, 6 crossings, open, pattern OUOOUU" in report
    assert identify.summary(other).splitlines()[0] == (
        "Laid like a square knot (reef knot), but 1 of its 6 crossings goes the other way round: at (296, 365) "
        "cord 1 should go over cord 2. As drawn it is not a square knot (reef knot).")
    # The same cords with no pattern: over, under, over all the way.
    plain = json.loads(json.dumps(spec))
    del plain["cords"][0]["pattern"]
    woven, _ = draw.build(plain)
    named = identify.named(woven)
    assert (named["key"], named["how"]) == ("granny", "exact")
    assert "A granny knot is not a square knot" in identify.summary(woven).splitlines()[0]


def patterns_with(code, turned):
    """The code's patterns with the given crossings the other way round."""
    return ["".join(("U" if top else "O") if k in turned else ("O" if top else "U") for k, top in row)
            for row in code["passes"]]


def drawn(key, patterns):
    cords = [{"points": [list(p[:2]) for p in points], "pattern": pattern, "width": bends.LIBRARY[key]["width"]}
             for points, pattern in zip(bends.LIBRARY[key]["layout"](), patterns)]
    return draw.build({"cords": cords})[0]


def test_a_crossing_the_wrong_way_round_is_named_with_its_place():
    code = bends.reference("sheet bend")
    wrong = 4                                       # where the working cord passes the bight's short leg
    data = drawn("sheet bend", patterns_with(code, {wrong}))
    named = identify.named(data)
    assert (named["key"], named["how"], len(named["flipped"])) == ("sheet bend", "near", 1)
    first = identify.summary(data).splitlines()[0]
    x, y = code["points"][wrong]
    assert first.startswith("Laid like a sheet bend (weaver's knot), but 1 of its 7 crossings goes the other way round")
    top, under = code["between"][wrong]             # as the reference has it: this cord over that one
    assert f"cord {top + 1} should go over cord {under + 1}" in first
    assert first.endswith("As drawn it is not a sheet bend (weaver's knot).")
    place = re.search(r"at \((\d+), (\d+)\)", first)
    assert (int(place.group(1)), int(place.group(2))) == pytest.approx((x, y), abs=3)
    # Drawn with the reference's own patterns it is the knot.
    assert identify.named(drawn("sheet bend", patterns_with(code, set())))["how"] == "exact"


def test_a_fishermans_knot_laid_another_way_is_known_by_its_structure():
    """The other cord may pass through each overhand knot from the other side:
    still each cord tied round the other, though not the library's picture."""
    code = bends.reference("fisherman")
    through_first = {k for k, _ in code["passes"][1][:4]}       # where cord 2 passes cord 1's knot
    data = drawn("fisherman", patterns_with(code, through_first))
    named = identify.named(data)
    assert (named["key"], named["how"]) == ("fisherman", "structure")
    text = identify.summary(data)
    assert text.splitlines()[0] == ("Fisherman's knot (magic knot): each cord is tied in an overhand knot with the "
                                    "other cord through it (laid differently from the library's drawing).")
    assert "cord 2 passes through a loop of cord 1" in text and "overhand knot (3_1) on its own" in text
    # The other cord laid over the whole knot instead of through it: not a fisherman's knot.
    over = {k for k, _ in code["passes"][1][2:4]}
    loose = drawn("fisherman", patterns_with(code, over))
    assert identify.named(loose)["how"] == "near"
    assert "passes through a loop of cord" not in identify.summary(loose).replace(
        "cord 1 passes through a loop of cord 2", "")


def test_cords_that_only_lie_on_each_other_are_not_joined():
    """What a freehand "bowline" came out as: a line crossed by an arc."""
    data, _ = draw.build({"cords": [
        {"points": [[200, 400], [1000, 400]], "color": "teal", "pattern": "UU"},
        {"points": [[400, 250], [600, 520], [800, 250]], "color": "gold"}]})
    text = identify.summary(data, unknown=True)
    assert identify.named(data) is None
    assert text.splitlines()[0] == "2 cords, 2 crossings: laid like none of the ready-made knots (knot_library lists them)."
    assert "cord 1 over at 0, cord 2 over at 2" in text
    assert "cord 2 lies over cord 1 everywhere" in text and "not joined" in text
    assert identify.summary(data).splitlines()[0].startswith("cord 1: ")     # said only when asked
    # Woven over and under the two are hooked, but still no knot from the library.
    woven, _ = draw.build({"cords": [
        {"points": [[200, 400], [1000, 400]], "color": "teal"},
        {"points": [[400, 250], [600, 520], [800, 250]], "color": "gold"}]})
    assert "not joined" not in identify.summary(woven) and identify.named(woven) is None


def test_one_cord_is_named_as_before_and_a_big_weave_is_left_alone():
    pretzel, _ = draw.build({"cords": [{"points": [[420, 640], [500, 420], [640, 300], [760, 360], [740, 480],
                                                   [600, 520], [460, 480], [440, 360], [560, 300], [700, 420],
                                                   [780, 640]]}]})
    assert identify.summary(pretzel) == ("cord 1: 8 strands, open (ends joined above everything to name it), "
                                         "3 crossings with itself: overhand knot (3_1)")
    stitch = project.read(ROOT / "mxn_samples/lh/stretched/json/mxn_lh_stretch_4x3.json")
    text = identify.summary(stitch)
    assert len(text.splitlines()) == 7 and all(line.startswith("cord ") for line in text.splitlines())


# ------------------------------------------------------------------ the agent
def test_the_agent_ties_a_bend_by_any_of_its_names_and_checks_it(tmp_path):
    from openstrand.agent import ToolError, Workspace
    ws = Workspace(tmp_path)
    summary, text = ws.run("knot_library", {})
    assert summary == "12 knots"
    assert "Stopper knots, tied in one cord" in text and "Knots that join cords or make a loop" in text
    for word in ("Stevedore knot", "Bowline", "magic knot", "reef knot", "Macrame square knot"):
        assert word in text
    summary, text = ws.run("tie_knot", {"knot": "Magic knot", "colors": ["crimson", "sky"]})
    assert summary == "Fisherman's knot (magic knot) · 5 steps"
    assert "joins two cords, 14 crossings" in text and "WARNING" not in text
    assert "cord 1 passes OOUUOOUUOUOOUU" in text and "steps 1 to 5" in text and "every crossing as in the reference" in text
    assert "drawn from the checked drawing, not simulated" in text
    assert [line.split(":")[0] for line in text.splitlines() if line.startswith("step ")] == [
        f"step {n}" for n in range(1, 6)]
    assert 'Saved as "step 1" to "step 5"' in text and "open_in_new_tab" in text
    assert [t for t, _ in ws.steps] == [f"Step {n}" for n in range(1, 6)] and all(p.exists() for _, p in ws.steps)
    assert project.read(ws.steps[-1][1]) == ws.data                       # the finished knot is the current design
    assert {tuple(s["colors"]) for s in project.describe(ws.data)["sets"].values()} == {("#c83e4d",), ("#4aa3df",)}
    summary, text = ws.run("identify_knot", {})
    assert summary.startswith("Fisherman's knot (magic knot): all 14 crossings go as in the checked drawing")
    # One color is the first cord's; a stopper knot still goes to the simulation.
    ws.run("tie_knot", {"knot": "how to tie a bowline", "color": "jade"})
    assert len(ws.steps) == 4 and project.describe(ws.data)["sets"][1]["colors"] == ["#399780"]
    assert ws.run("tie_knot", {"knot": "overhand"})[0] == "Overhand knot · 5 steps"
    with pytest.raises(ToolError, match="draw_design, a pattern on each cord, then make_steps"):
        ws.run("tie_knot", {"knot": "zeppelin bend"})
    with pytest.raises(ToolError, match="2 colours to choose"):
        ws.run("tie_knot", {"knot": "square knot", "colors": ["red", "gold", "teal"]})


def test_a_tutorial_for_a_bowline_is_one_tool_call_and_its_steps_in_tabs(tmp_path):
    """What asking for a tutorial comes to, with a scripted model: tie_knot by
    name, each step opened in a tab, a short answer. No drawing, no search."""
    from openstrand import agent
    usage = SimpleNamespace(input_tokens=1000, output_tokens=200, cache_creation_input_tokens=0,
                            cache_read_input_tokens=0)
    tool = lambda id_, name, **inp: SimpleNamespace(type="tool_use", id=id_, name=name, input=inp)
    reply = lambda *blocks, stop="tool_use": SimpleNamespace(content=list(blocks), stop_reason=stop, usage=usage)
    script = [reply(tool("t1", "tie_knot", knot="bowline")),
              reply(*[tool(f"o{n}", "open_in_new_tab", design=f"step {n}", title=f"Step {n} · bowline")
                      for n in range(1, 5)]),
              reply(SimpleNamespace(type="text", text="A bowline in four steps, drawn loose, not simulated."),
                    stop="end_turn")]
    sent = []

    def create(**params):
        sent.append(dict(params, messages=list(params["messages"])))
        return script.pop(0)
    client = SimpleNamespace(messages=SimpleNamespace(create=create),
                             beta=SimpleNamespace(messages=SimpleNamespace(create=create)))
    opened = []
    app = SimpleNamespace(call=lambda name, args: opened.append((name, args)) or {"opened": True})
    events = []
    runner = agent.Agent(client, tmp_path, on_event=events.append, app=app, web=False)
    result = runner.run("bowline tutorial")
    assert result["ok"] and result["opened_tabs"] == [f"Step {n} · bowline" for n in range(1, 5)]
    assert [Path(args["path"]).name for _, args in opened] == [f"step_{n}.json" for n in range(1, 5)]
    assert identify.named(project.read(result["project"]))["key"] == "bowline"
    ends = [e for e in events if e["type"] == "tool_end"]
    assert ends[0]["summary"] == "Bowline · 4 steps" and all(e["ok"] for e in ends)
    told = sent[1]["messages"][-1]["content"][0]["content"]
    assert "step 4: And back down through the small loop" in told
    progress = [e for e in events if e["type"] == "tool_progress"]
    assert progress and progress[0]["stage"] == "draw_step" and progress[0]["steps"] == 4


def test_the_steps_of_a_hand_drawn_bend_say_what_each_shows(tmp_path):
    """make_steps cuts a drawing where its strands join, so the agent used to
    title the tabs of a bend it drew by guessing what each step held."""
    from openstrand.agent import Workspace
    ws = Workspace(tmp_path)
    ws.run("draw_design", guide_example("square knot"))
    summary, text = ws.run("make_steps", {"count": 4})
    assert summary == "4 steps" and "What each shows, to title its tab by" in text
    lines = [line for line in text.splitlines() if line.startswith("step ")]
    assert len(lines) == 4
    assert re.fullmatch(r"step 1: cord 1 \(First cord\) as far as strand \d of 9, cord 2 \(Second cord\) not yet; "
                        r"the working end is at \(\d+, \d+\)", lines[0])
    assert lines[1].startswith("step 2: cord 1 (First cord) whole, cord 2 (Second cord) not yet")
    assert lines[3] == "step 4: cord 1 (First cord) whole, cord 2 (Second cord) whole"
    assert len(ws.steps) == 4


def test_the_agent_is_told_to_tie_these_knots_by_name_and_how_to_draw_the_rest():
    from openstrand.agent import INSTRUCTIONS, TOOLS, Agent
    from openstrand.app_tools import APP_INSTRUCTIONS
    knots = INSTRUCTIONS[INSTRUCTIONS.index("Knots (how one is tied"):INSTRUCTIONS.index("Masks (which strand")]
    for name in ("square or reef knot", "sheet bend", "magic knot", "double fisherman's knot", "bowline",
                 "macrame\n  square knot", "figure-eight"):
        assert name in knots, name
    assert "call tie_knot with its name, at once" in knots and "do\n  not search the web for it first" in knots
    assert "never draw tying steps or a tightened knot by hand" in knots
    assert "cannot tie" not in INSTRUCTIONS                               # it can, now
    # A bend that is not in the library is still the agent's to draw, with a pattern, and checked.
    other = knots[knots.index("that is not in\n  knot_library (a zeppelin bend"):]
    assert '"pattern"' in other and "identify_knot" in other and "make_steps" in other
    assert "never with edit_mask" in other
    tools = {t["name"]: t for t in TOOLS}
    assert "pattern" in tools["draw_design"]["description"] and "do not alternate" in tools["draw_design"]["description"]
    tie = tools["tie_knot"]["description"]
    for name in ("square or reef knot", "sheet bend", "magic knot", "bowline", "macrame"):
        assert name in tie
    assert "colors" in tools["tie_knot"]["input_schema"]["properties"]
    assert "square knot" in tools["knot_library"]["description"]
    assert "which crossings go the other way round" in tools["identify_knot"]["description"]
    assert "bends and loop\n  knots in knot_library" in APP_INSTRUCTIONS
    # The guides the agent is given name them too.
    system = Agent(SimpleNamespace(), tempfile.mkdtemp(), web=False).system()[0]["text"]
    assert 'tie "fisherman\'s knot"' in system and "Over and under by hand: `pattern`" in system


# -------------------------------------------------------------------- the cli
def test_the_command_ties_lists_and_identifies_a_bend(tmp_path):
    run = lambda *a: subprocess.run([sys.executable, "-m", "openstrand", *a], cwd=ROOT, capture_output=True,
                                    text=True, timeout=600)
    listed = run("tie", "--list")
    assert listed.returncode == 0
    for word in ("stopper knots, tied in one cord", "knots that join cords or make a loop", "bowline",
                 "magic knot", "stevedore"):
        assert word in listed.stdout
    made = run("tie", "sheet bend", "--colors", "jade,copper", "--out-dir", str(tmp_path))
    assert made.returncode == 0, made.stderr
    assert made.stdout.startswith("Sheet bend (weaver's knot): joins two cords, 7 crossings")
    assert "cord 2 passes UOOUUOUO" in made.stdout and "every mask right" in made.stdout
    files = sorted(tmp_path.glob("sheet_bend_step_*.json"))
    assert len(files) == 4
    named = run("identify", str(files[-1]))
    assert named.stdout.startswith("Sheet bend (weaver's knot): all 7 crossings go as in the checked drawing")
    assert "pattern UOOUUOUO" in named.stdout or "pattern OUOUUO" in named.stdout
    wrong = run("tie", "overhand", "--colors", "red,gold", "--out-dir", str(tmp_path))
    assert wrong.returncode == 1 and "--colors is for a knot of several cords" in wrong.stderr
