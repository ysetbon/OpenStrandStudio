"""The openstrand command: make, info, validate, recolor and render projects.

The make commands that fit a new curve take a minute, so these tests use the
designs that come from published samples, plus one render through the real
canvas.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openstrand import colors, edit, project
from openstrand.cli import main


def run(*args):
    """Run the command in a child process, as a person or an agent would."""
    result = subprocess.run([sys.executable, "-m", "openstrand", *args], cwd=ROOT,
                            capture_output=True, text=True, timeout=300)
    return result.returncode, result.stdout, result.stderr


def test_read_takes_the_current_state_of_a_history_file():
    data = project.read(ROOT / "mxn_samples/lh/stretched/json/mxn_lh_stretch_4x3.json")
    assert isinstance(data["strands"], list) and data["strands"]


def test_read_rejects_a_file_that_is_not_a_project(tmp_path):
    path = tmp_path / "x.json"
    path.write_text('{"hello": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="not an OpenStrand Studio project"):
        project.read(path)


def test_describe_tells_vertical_from_horizontal_ribbons():
    data = project.read(ROOT / "mxn_samples/lh/stretched/json/mxn_lh_stretch_4x3.json")
    runs = [s["runs"] for s in project.describe(data)["sets"].values()]
    assert runs.count("vertical") == 4 and runs.count("horizontal") == 3


def test_recolor_changes_the_set_its_masks_and_the_color_table():
    data = project.read(ROOT / "knot_samples/links/json/hopf_link.json")
    edit.recolor(data, {1: "red"})
    red = colors.rgba("red")
    for s in data["strands"]:
        if project.set_of(s) == 1:
            assert s["color"] == red
        else:
            assert s["color"] != red
    assert data["strand_colors"]["1"] == red


def test_recolor_names_the_sets_a_project_has():
    data = project.read(ROOT / "knot_samples/links/json/hopf_link.json")
    with pytest.raises(ValueError, match="no set 9"):
        edit.recolor(data, {9: "red"})


def test_colors_accept_names_and_hex_and_explain_the_rest():
    assert colors.parse("Gold") == colors.NAMES["gold"]
    assert colors.parse("C83E4D") == "#c83e4d"
    with pytest.raises(ValueError, match="unknown color"):
        colors.parse("sparkly")


def test_make_mxn_info_validate_recolor(tmp_path, capsys):
    out = tmp_path / "bracelet.json"
    assert main(["make", "mxn", "--m", "4", "--n", "3", "--stretch", "--out", str(out)]) == 0
    assert "7 sets" in capsys.readouterr().out
    assert main(["validate", str(out)]) == 0
    assert capsys.readouterr().out.startswith("valid")
    assert main(["recolor", str(out), "--set", "1,2,3", "--color", "gold"]) == 0
    assert "sets 4, 5, 6, 7 unchanged" in capsys.readouterr().out
    info = project.describe(project.read(out))
    assert all(info["sets"][n]["colors"] == [colors.NAMES["gold"]] for n in (1, 2, 3))
    assert main(["info", str(out), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["masks"] > 0


def test_make_turks_head_copies_a_published_size(tmp_path, capsys):
    out = tmp_path / "mat.json"
    assert main(["make", "turks_head", "--leads", "3", "--bights", "5", "--color", "red", "--out", str(out)]) == 0
    assert "turks_head_3x5" in capsys.readouterr().out
    assert project.describe(project.read(out))["sets"][1]["colors"] == [colors.NAMES["red"]]


def test_errors_say_what_to_do_and_exit_with_1():
    code, _, err = run("make", "turks_head", "--leads", "3", "--bights", "6")
    assert code == 1 and "share a factor of 3" in err and "7 bights" in err
    code, _, err = run("make", "sample", "no_such_design")
    assert code == 1 and "no sample named" in err


def test_render_draws_the_project_with_the_real_canvas(tmp_path):
    out = tmp_path / "hopf.png"
    code, stdout, err = run("render", str(ROOT / "knot_samples/links/json/hopf_link.json"), "--out", str(out))
    assert code == 0, err
    assert stdout.startswith("rendered") and out.stat().st_size > 10_000
