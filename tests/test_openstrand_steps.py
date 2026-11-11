"""openstrand draw-steps: a tutorial drawn step by step, each step its own picture.

Asked for a slip knot or a crochet stitch in steps, the agent drew one design
per picture, with the hook and the arrows as cords (which were then woven into
the design), and called an overhand knot a slip knot. Tools (hook, needle,
stick), arrows and heights are now part of a drawing, and draw_steps draws a
whole sequence in one call. The slip knot in the drawing guide is built here,
so the guide the agent learns from can never hold steps that do not draw.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openstrand import agent, check, draw, identify, project, steps, storyboard  # noqa: E402

GUIDE = ROOT / ".claude" / "skills" / "openstrand-designer" / "drawing.md"

LOOP = {"label": "Loop", "color": "white", "width": 20,
        "points": [[380, 600], [400, 480], [430, 300], [500, 180], [600, 200], [640, 320], [620, 470], [640, 600]],
        "heights": [0, 0, 0, 0, 20, 20, 20, 20]}
HOOK = {"tool": "hook", "from": [250, 290], "to": [900, 340], "height": 10}
ARROW = {"points": [[700, 520], [760, 420], [860, 380], [960, 420]]}


def strands_of(data, hidden=False):
    return [s for s in data["strands"] if s["type"] != "MaskedStrand" and bool(s.get("is_hidden")) == hidden]


# ------------------------------------------------------------------- tools
def test_a_hook_is_a_straight_stick_with_a_shaped_tip_woven_by_height():
    data, report = draw.build({"cords": [HOOK, LOOP]})
    # The loop's far side (0) is under the hook (10), its near side (20) over it.
    assert "cord 1 over cord 2" in report and "cord 2 over cord 1" in report and "conflicts: 0" in report
    hook = [s for s in strands_of(data) if s["set_number"] == 1]
    assert len(hook) == 1 and set(project.describe(data)["groups"]) == {"Hook", "Loop"}
    handle, tip = hook[0]["end_styles"]
    assert handle["shape"] == "rounded" and tip["shape"] == "rounded" and tip["tilt"] == 45 and tip["depth"] == 1.0
    assert (hook[0]["start"]["x"], hook[0]["end"]["x"]) == (250, pytest.approx(900, abs=1))
    assert hook[0]["width"] == draw.TOOL_WIDTH and project.hex_color(hook[0]["color"]) == "#95a5a6"
    assert check.problems(data) == []


def test_a_needle_is_pointed_and_a_tool_can_dip_from_handle_to_tip():
    data, report = draw.build({"cords": [
        {"tool": "needle", "from": [250, 290], "to": [900, 340], "heights": [30, -30], "width": 20, "color": "ink"},
        {"label": "Left", "points": [[400, 100], [400, 500]], "height": 0},
        {"label": "Right", "points": [[750, 100], [750, 500]], "height": 0}]})
    needle = strands_of(data)[[s["set_number"] for s in strands_of(data)].index(1)]
    assert needle["end_styles"][1]["shape"] == "pointed" and needle["width"] == 20
    # Above the left cord near its handle, below the right one near its tip.
    assert "cord 1 over cord 2" in report and "cord 3 over cord 1" in report


@pytest.mark.parametrize("cord, message", [
    ({"tool": "spoon", "from": [0, 0], "to": [100, 0]}, 'unknown tool "spoon"; use hook, needle, stick'),
    ({"tool": "hook", "from": [0, 0]}, 'needs "from" \\(its handle end\\) and "to" \\(its tip\\)'),
    ({"tool": "hook", "from": [5, 5], "to": [5, 5]}, "the same point"),
    ({"tool": "hook", "from": [0, 0], "to": [300, 0], "heights": [1, 2, 3]}, "two numbers"),
    ({"tool": "hook", "from": [0, 0], "to": [300, 0], "points": [[0, 0], [1, 1]]}, "exactly one"),
    ({"points": [[0, 0], [300, 0]], "heights": [0, 5], "height": 3}, "not both"),
    ({"shape": "circle", "center": [0, 0], "radius": 90, "heights": [1]}, 'use "height"'),
])
def test_bad_tools_and_heights_say_what_to_change(cord, message):
    with pytest.raises(draw.DrawError, match=message):
        draw.centerline(cord, 0)


def test_one_height_serves_any_kind_of_cord():
    wave = {"x": "300 + 100*t", "y": "400 + 150*sin(t)", "t0": "-pi/2", "t1": "5*pi/2"}  # crosses the line 3 times
    for top, heights in (("cord 1 over cord 2", (30, 0)), ("cord 2 over cord 1", (0, 30))):
        _, report = draw.build({"cords": [dict(wave, height=heights[0]),
                                          {"points": [[100, 400], [1100, 400]], "height": heights[1]}]})
        assert report.count(top) == 3 and "conflicts: 0" in report, report  # not alternating: the higher on top


# ------------------------------------------------------------------ arrows
def test_an_arrow_is_a_hidden_strand_with_its_full_arrow_on_top_and_never_woven():
    plain, _ = draw.build({"cords": [HOOK, LOOP]})
    data, report = draw.build({"cords": [HOOK, LOOP], "arrows": [
        {"points": [[520, 420], [520, 100]]}, dict(ARROW, color="blue", label="Pull")]})
    assert "2 arrows drawn on top" in report
    assert report.count("crossing at") == 2  # the first arrow runs across the hook and crosses nothing
    arrows = strands_of(data, hidden=True)
    assert arrows and all(s["full_arrow_visible"] and s["type"] == "Strand" for s in arrows)
    assert data["strands"][-len(arrows):] == arrows  # above everything, masks included
    assert [s for s in data["strands"] if s["type"] == "MaskedStrand"] == \
        [s for s in plain["strands"] if s["type"] == "MaskedStrand"]
    assert {project.hex_color(s["arrow_color"]) for s in arrows} == {"#c83e4d", "#2e86de"}
    assert sum(s["arrow_head_visible"] for s in arrows) == 2  # one head per arrow, on its last strand
    assert {"Arrow 1", "Pull"} <= set(project.describe(data)["groups"])
    assert data["project_settings"]["arrow_head_length"] == draw.ARROW_SETTINGS["arrow_head_length"]
    assert "arrow_head_length" not in plain["project_settings"]  # a design without arrows is as before
    assert check.problems(data) == []
    # The head is drawn beyond the strand: the shaft stops a head short of the last point.
    straight = arrows[0]
    assert straight["end"]["y"] == pytest.approx(100 + draw.ARROW_SETTINGS["arrow_head_length"], abs=6)


@pytest.mark.parametrize("arrows, message", [
    ([{"points": [[0, 0]]}], "2 to 12 points"),
    ([{"points": [[0, 0], [20, 0]]}], "only 20 px long"),
    ([{"points": [[0, 0], [9000, 0]]}], "keep every point"),
    ([{"points": [[0, 0], [200, 0]]}] * 9, "at most 8 arrows"),
    ("up", "at most 8 arrows"),
])
def test_bad_arrows_say_what_to_change(arrows, message):
    with pytest.raises(draw.DrawError, match=message):
        draw.build({"cords": [LOOP], "arrows": arrows})


def test_arrows_are_no_part_of_the_knot_or_of_a_design_shown_bit_by_bit():
    cord = {"label": "Pretzel", "points": [[420, 640], [500, 420], [640, 300], [760, 360], [740, 480], [600, 520],
                                           [460, 480], [440, 360], [560, 300], [700, 420], [780, 640]]}
    plain, _ = draw.build({"cords": [cord]})
    data, _ = draw.build({"cords": [cord], "arrows": [{"points": [[300, 300], [380, 200], [500, 180]]}]})
    assert identify.summary(data) == identify.summary(plain) and "overhand" in identify.summary(data)
    made = steps.make(data, count=3)
    assert [len(strands_of(d, hidden=True)) for _, d in made] == [0, 0, 1]  # the arrow comes with the whole design


# ------------------------------------------------------------------- steps
def two_steps():
    return [{"title": "A loop", "cords": [LOOP]},
            {"title": "Hook through it", "keep": ["Loop"], "cords": [HOOK], "arrows": [ARROW]}]


def test_a_step_keeps_redraws_and_adds_cords_by_label():
    moved = dict(LOOP, color="gold")
    resolved = storyboard.resolve([
        {"title": "one", "cords": [LOOP, HOOK]},
        {"title": "two", "keep": "all", "cords": [{"label": "Yarn", "points": [[0, 0], [300, 0]]}]},
        {"title": "three", "keep": ["Yarn"], "cords": [moved]},     # the loop moved, the hook is gone
        {"cords": [{"points": [[0, 0], [300, 0]]}]}])
    assert [[c["label"] for c in s["cords"]] for s in resolved] == \
        [["Loop", "Hook"], ["Loop", "Hook", "Yarn"], ["Loop", "Yarn"], ["Cord 1"]]
    assert resolved[2]["cords"][0]["color"] == "gold" and resolved[1]["cords"][0]["color"] == "white"
    assert [s["title"] for s in resolved] == ["one", "two", "three", "Step 4"]
    assert resolved[1]["arrows"] == []  # arrows belong to their step only


@pytest.mark.parametrize("change, message", [
    (lambda s: s[1].update(keep=["Lop"]), "step 2 keeps 'Lop', but the step before has \"Loop\""),
    (lambda s: s[0].update(keep=["Loop"]), "no cords \\(it is the first step\\)"),
    (lambda s: s[1].update(cords=[HOOK, HOOK]), 'step 2 has two cords labelled "Hook"'),
    (lambda s: s[1].update(keep=[], cords=[]), "step 2 has no cords"),
    (lambda s: s[1].update(keep=3), '"keep" lists the labels'),
    (lambda s: s.extend([s[1]] * 12), "1 to 12 steps"),
])
def test_steps_that_cannot_be_resolved_name_the_step(change, message):
    story = two_steps()
    change(story)
    with pytest.raises(storyboard.StepsError, match=message):
        storyboard.resolve(story)


def test_every_step_is_its_own_design():
    made = storyboard.build({"steps": two_steps()})
    assert [m["title"] for m in made] == ["A loop", "Hook through it"]
    first, second = (m["data"] for m in made)
    assert len(project.describe(first)["sets"]) == 1 and not strands_of(first, hidden=True)
    assert set(project.describe(second)["groups"]) == {"Loop", "Hook", "Arrow 1"}
    assert check.problems(first) == [] and check.problems(second) == []
    # The kept cord runs exactly where it ran in the step before (its strands may be cut elsewhere:
    # joins keep clear of the hook's crossings).
    from sample_geometry import segment_distance
    before, after = (identify.cords(d)[0]["cord"][:, :2].tolist() for d in (first, second))
    apart = max(min(segment_distance(p, a, b) for a, b in zip(after, after[1:])) for p in before)
    assert apart < 4, apart
    text = storyboard.summary(made)
    assert 'step 2 "Hook through it" (Loop, Hook):' in text and "cord 2 over cord 1" in text
    assert "masks: no problems" in text and "built in" not in text


def test_a_step_that_cannot_be_drawn_is_named():
    story = two_steps()
    story[1]["cords"] = [{"tool": "hook", "from": [250, 290], "to": [260, 290]}]
    with pytest.raises(storyboard.StepsError, match='step 2 \\("Hook through it"\\): cord 2 is only'):
        storyboard.build({"steps": story})


def test_replace_changes_single_steps_and_adds_one():
    story = two_steps()
    changed = storyboard.replace(story, [{"step": 2, "title": "Needle through it", "keep": ["Loop"],
                                          "cords": [dict(HOOK, tool="needle")]},
                                         {"step": 3, "title": "Out again", "keep": ["Loop"]}])
    assert [s["title"] for s in changed] == ["A loop", "Needle through it", "Out again"]
    assert story[1]["title"] == "Hook through it" and "step" not in changed[1]  # the sent steps stay as sent
    with pytest.raises(storyboard.StepsError, match="a number from 1 to 3"):
        storyboard.replace(story, [{"step": 5, "title": "x"}])
    with pytest.raises(storyboard.StepsError, match='send the whole sequence in "steps" first'):
        storyboard.replace(None, [{"step": 1}])


# --------------------------------------------------------- the guide's steps
def guide_steps():
    text = GUIDE.read_text(encoding="utf-8")
    found = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S)]
    return [spec for spec in found if isinstance(spec.get("steps"), list)]


def test_the_guide_has_a_slip_knot_in_steps():
    assert [spec["name"] for spec in guide_steps()] == ["Slip knot on a hook"]


@pytest.mark.parametrize("spec", guide_steps(), ids=lambda s: s["name"])
def test_every_step_sequence_in_the_drawing_guide_draws_cleanly(spec):
    made = storyboard.build(spec)
    assert len(made) == len(spec["steps"])
    for step in made:
        assert "conflicts: 0" in step["report"] and "warning" not in step["report"], step["report"]
        assert "masks left" not in step["report"], step["report"]
        assert check.problems(step["data"]) == []


def test_the_guides_slip_knot_is_one_and_not_an_overhand_knot():
    made = storyboard.build(guide_steps()[0])
    for step in made:
        yarn = identify.cords(step["data"])[0]
        assert yarn["knot"] == "unknot", (step["title"], yarn["knot"])  # pulling the working end undoes it
    assert "would slip free" in identify.summary(made[-1]["data"])
    last = made[-1]["data"]
    assert len(strands_of(last, hidden=True)) == 2 and "Hook" in project.describe(last)["groups"]
    # The loop is on the hook: the hook passes over one of its legs and under the other.
    assert made[-1]["report"].count("cord 2 over cord 1") == 1 and made[-1]["report"].count("cord 1 over cord 2") == 1


# ---------------------------------------------------------------- command
def test_the_draw_steps_command_writes_each_step_and_one_picture_of_all(tmp_path):
    spec = tmp_path / "steps.json"
    spec.write_text(json.dumps({"steps": two_steps()}), encoding="utf-8")
    out = tmp_path / "out"
    result = subprocess.run([sys.executable, "-m", "openstrand", "draw-steps", str(spec), "--out-dir", str(out)],
                            cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr
    assert "step_1.json · A loop" in result.stdout and "all 2 steps side by side" in result.stdout
    assert 'step 2 "Hook through it" (Loop, Hook):' in result.stdout
    assert len(project.describe(project.read(out / "step_2.json"))["sets"]) >= 3
    from PyQt5.QtGui import QImage
    sheet = QImage(str(out / "steps.png"))
    assert (sheet.width(), sheet.height()) == (2 * 430, 320 + 34)  # two steps side by side, a title bar each
    assert (out / "step_1.png").exists() and (out / "step_2.png").exists()

    spec.write_text(json.dumps({"steps": [{"title": "x", "keep": ["Yarn"]}]}), encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "openstrand", "draw-steps", str(spec), "--no-sheet"],
                            cwd=tmp_path, capture_output=True, text=True, timeout=300,
                            env=dict(os.environ, PYTHONPATH=str(ROOT)))
    assert result.returncode == 1 and "error: step 1 keeps 'Yarn'" in result.stderr


def test_the_sheet_lays_steps_out_in_reading_order():
    assert [storyboard.columns_for(n) for n in (1, 2, 3, 4, 5, 6, 9, 10, 12)] == [1, 2, 3, 2, 3, 3, 3, 4, 4]


# ------------------------------------------------------------------ agent
def usage():
    return SimpleNamespace(input_tokens=1000, output_tokens=200, cache_creation_input_tokens=0,
                           cache_read_input_tokens=0)


def reply(*blocks, stop="tool_use"):
    return SimpleNamespace(content=list(blocks), stop_reason=stop, usage=usage())


def tool(id_, tool_name, **inp):
    return SimpleNamespace(type="tool_use", id=id_, name=tool_name, input=inp)


class ScriptedClient:
    def __init__(self, replies):
        self.replies, self.calls = list(replies), []
        self.messages = SimpleNamespace(create=self._create)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **params):
        self.calls.append(dict(params, messages=list(params["messages"])))
        return self.replies.pop(0)


def test_the_agent_draws_a_whole_tutorial_in_one_call_and_fixes_one_step(tmp_path):
    client = ScriptedClient([
        reply(tool("t1", "draw_steps", name="Hook through a loop", steps=two_steps())),
        reply(tool("t2", "draw_steps", replace=[{"step": 2, "title": "Needle through it", "keep": ["Loop"],
                                                 "cords": [dict(HOOK, tool="needle")]},
                                                {"step": 3, "title": "Loop on the needle", "keep": "all"}])),
        reply(tool("t3", "render", step=2)),
        reply(SimpleNamespace(type="text", text="Three steps."), stop="end_turn")])
    events = []
    runner = agent.Agent(client, tmp_path, model="claude-haiku-5-5", on_event=events.append)
    result = runner.run("how do I put a hook through a loop")

    assert result["ok"] and result["changed"] and result["new"]
    first = client.calls[1]["messages"][-1]["content"][0]["content"]
    assert [part["type"] for part in first] == ["text", "image"]  # the report, and all the steps in one picture
    assert 'step 2 "Hook through it" (Loop, Hook):' in first[0]["text"]
    assert 'Saved as "step 1" to "step 2"' in first[0]["text"] and '"replace"' in first[0]["text"]
    ends = [e for e in events if e["type"] == "tool_end"]
    assert [e["summary"] for e in ends[:2]] == ["Hook through a loop · 2 steps", "steps · 3 steps"]
    assert any(e["type"] == "tool_progress" and e["stage"] == "draw_step" and e["steps"] == 2 for e in events)
    # The second call sent only the changed step and a new one: the first step is as before.
    assert [title for title, _ in runner.workspace.steps] == ["A loop", "Needle through it", "Loop on the needle"]
    shown = project.read(tmp_path / "step_2.json")
    assert [s["end_styles"][1]["shape"] for s in strands_of(shown) if s["set_number"] == 2] == ["pointed"]
    assert project.read(result["project"]) == project.read(tmp_path / "step_3.json")  # the last step is current
    assert (tmp_path / "steps.png").exists() and (tmp_path / "step_2.png").exists()
    looked = client.calls[3]["messages"][-1]["content"][0]["content"]
    assert looked[0]["type"] == "image" and result["png"] is None  # a step's picture is not the design's


def test_a_step_that_fails_is_fixed_with_replace_alone(tmp_path):
    story = two_steps()
    story[1]["cords"] = [{"tool": "hook", "from": [250, 290], "to": [260, 290]}]
    client = ScriptedClient([
        reply(tool("t1", "draw_steps", steps=story)),
        reply(tool("t2", "draw_steps", replace=[{"step": 2, "title": "Hook through it", "keep": ["Loop"],
                                                 "cords": [HOOK]}])),
        reply(tool("t3", "draw_steps")),
        reply(SimpleNamespace(type="text", text="Done."), stop="end_turn")])
    runner = agent.Agent(client, tmp_path, model="claude-haiku-5-5")
    runner.run("steps")
    failed = client.calls[1]["messages"][-1]["content"][0]
    assert failed["is_error"] and 'step 2 ("Hook through it"): cord 2 is only' in failed["content"]
    assert len(runner.workspace.steps) == 2 and (tmp_path / "step_2.json").exists()
    neither = client.calls[3]["messages"][-1]["content"][0]
    assert neither["is_error"] and '"steps"' in neither["content"] and '"replace"' in neither["content"]


def test_the_agent_is_told_when_to_draw_steps():
    from openstrand.app import APP_INSTRUCTIONS
    names = [t["name"] for t in agent.TOOLS]
    assert "draw_steps" in names and "draw_steps" in agent.IMAGE_TOOLS
    assert "draw_steps" not in agent.PLAN_TOOLS  # plan mode builds nothing
    text = agent.INSTRUCTIONS
    assert "in ONE draw_steps call, never one draw_design per picture" in text
    assert "never cords\n  drawn to look like them" in text
    assert "A slip knot is not an overhand knot" in text and "would slip free" in text
    assert "every crochet and knitting stitch" in text and 'fix only the steps that are off with "replace"' in text
    assert "draw_steps when the pictures differ from step to\n  step" in APP_INSTRUCTIONS
    described = next(t for t in agent.TOOLS if t["name"] == "draw_steps")
    assert set(described["input_schema"]["properties"]) == {"name", "steps", "replace"}
    assert "Steps drawn one by one" in described["description"]
    assert "## Steps drawn one by one" in GUIDE.read_text(encoding="utf-8")
    drawn = next(t for t in agent.TOOLS if t["name"] == "draw_design")
    assert "arrows" in drawn["input_schema"]["properties"] and '"tool": "hook"' in drawn["description"]


def test_the_panel_shows_draw_steps_as_a_drawing_tool():
    sys.path.insert(0, str(ROOT / "src"))
    import agent_panel
    assert agent_panel.TOOL_CHIPS["draw_steps"] == agent_panel.TOOL_CHIPS["draw_design"]
    assert "draw_steps" in agent_panel.PICTURE_TOOLS
