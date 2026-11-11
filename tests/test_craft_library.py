"""The craft library: every entry can be found and made, and none of it reaches
the app's own Samples page.

craft_library/ is a backend library for the openstrand command and the agent.
The Samples page of the settings dialog stays the short list it is however
large the library grows.
"""
import ast
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openstrand import agent, bends, check, generators, identify, invariants, library, masks, tying
from openstrand.cli import main

CATALOG = library.read_catalog()
LISTED = CATALOG["entries"]
BY_NAME = {e["name"]: e for e in LISTED}


def dialog_samples():
    """SettingsDialog.SAMPLES as written in the source: the files on the Samples page."""
    tree = ast.parse((ROOT / "src" / "settings_dialog.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "SAMPLES" for t in node.targets):
            return [row[3] for row in ast.literal_eval(node.value)]
    raise AssertionError("SettingsDialog.SAMPLES not found")


# ------------------------------------------------------------- the catalog
def test_every_entry_is_complete_and_named_once():
    names = [e["name"] for e in LISTED]
    assert len(names) == len(set(names))
    assert not set(names) & set(generators.samples()), "an entry would hide a published file of the same name"
    for entry in LISTED:
        assert re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", entry["name"]), entry["name"]
        assert entry["craft"] in CATALOG["crafts"], entry["name"]
        assert entry["title"] and entry["about"].endswith("."), entry["name"]
        assert len(entry["build"]) == 1 and next(iter(entry["build"])) in library.BUILDS, entry["name"]


def test_no_two_entries_answer_to_the_same_name():
    seen = {}
    for entry in LISTED:
        for name in [entry["name"], entry["title"]] + entry.get("also", []):
            key = tuple(library.words(name))
            # A whole craft's word ("scoubidou") may lead to several stitches; a name may not.
            if key in seen and seen[key] != entry["name"]:
                assert name.lower() in CATALOG["crafts"] or len(key) == 1, (name, seen[key], entry["name"])
            seen.setdefault(key, entry["name"])


@pytest.mark.parametrize("entry", LISTED, ids=[e["name"] for e in LISTED])
def test_every_entry_can_be_made(entry):
    kind, value = next(iter(entry["build"].items()))
    if kind == "tie":
        assert bends.find(value) or tying.find(value), f'tie does not know "{value}"'
        return
    if kind == "make":
        assert value in ("mxn", "turks_head")
        return
    data, _, _ = generators.sample(entry["name"])
    assert data["strands"]
    assert check.problems(data) == []
    if "patterns" in entry:
        # The design is the knot its entry says, crossing for crossing: each cord's over
        # and under in order, read back from the strands, masks and layers as the app draws them.
        code = identify.code(data)
        assert [invariants.pattern(code, k) for k in range(len(code["passes"]))] == entry["patterns"]
        assert masks.check(data)["problems"] == []


def test_files_of_the_library_are_all_listed():
    files = {p.resolve() for p in library.FOLDER.glob("**/json/*.json")}
    listed = {library.path_of(e) for e in LISTED if "file" in e["build"]}
    assert files <= listed, "a project in craft_library/ has no entry in catalog.json"


# -------------------------------------------------------------- the lookup
@pytest.mark.parametrize("asked, name", [
    ("boondoggle", "box_stitch"),
    ("scoubidou box stitch", "box_stitch"),
    ("square stitch", "box_stitch"),
    ("brick", "brick_stitch"),
    ("mystic knot", "chinese_pan_chang"),
    ("endless knot", "chinese_pan_chang"),
    ("double coin", "chinese_double_coin"),
    ("how to tie a magic knot", "magic_knot"),
    ("cobra knot", "macrame square knot"),
    ("lark's head", "larks_head_knot"),
    ("cow hitch", "larks_head_knot"),
    ("josephine", "josephine_knot"),
    ("carrick bend", "josephine_knot"),
    ("reverse larks head knot", "reverse_larks_head_knot"),
    ("Macramé", "macrame square knot"),
    ("weaver's knot", "sheet bend"),
    ("bowline", "bowline"),
])
def test_search_finds_a_design_by_the_names_people_use(asked, name):
    assert library.search(asked)[0]["name"] == name


def test_search_by_craft_lists_that_craft():
    assert {e["name"] for e in library.search("chinese knot")} == {
        "chinese_double_coin", "chinese_cloverleaf", "chinese_good_luck", "chinese_pan_chang"}
    assert library.search("crochet") == [] and library.search("4x3 bracelet") == []


def test_a_match_ends_with_the_call_that_makes_it():
    assert library.line(BY_NAME["box_stitch"]).endswith("get it: make_mxn m=1, n=1")
    assert library.line(BY_NAME["box_stitch"], cli=True).endswith("get it: make mxn --m 1 --n 1")
    assert library.line(BY_NAME["chinese_pan_chang"]).endswith('get it: load_sample name="chinese_pan_chang"')
    assert library.line(BY_NAME["magic_knot"]).endswith('tie_knot name="fisherman\'s knot" (with its tying steps)')


def test_make_sample_takes_any_name_of_an_entry():
    by_name, _, _ = generators.sample("chinese_pan_chang")
    by_other_name, _, _ = generators.sample("Mystic knot")
    assert by_name == by_other_name
    box, _, source = generators.sample("square stitch")
    assert source == "mxn_lh_1x1" and box == generators.mxn(1, 1)[0]
    with pytest.raises(ValueError, match="tie_knot"):
        generators.sample("magic knot")


def test_the_samples_command_lists_entries_then_files(capsys):
    assert main(["samples", "boondoggle"]) in (0, None)
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("box_stitch · boondoggle · Box stitch") and out[0].endswith("make mxn --m 1 --n 1")
    assert main(["samples", "hopf"]) in (0, None)
    assert capsys.readouterr().out.splitlines() == ["hopf_link"]


def test_the_agent_looks_designs_up_in_the_library(tmp_path):
    workspace = agent.Workspace(tmp_path)
    _, found = workspace.run("search_samples", {"text": "scoubidou"})
    assert "box_stitch · boondoggle" in found and "get it: make_mxn m=1, n=1" in found
    _, found = workspace.run("search_samples", {"text": "turks"})
    assert "Published files" in found and "turks_head_3x5" in found
    _, crafts = workspace.run("search_samples", {"text": ""})
    assert "chinese knotting:" in crafts and "mxn_lh_1x1" in crafts
    _, nothing = workspace.run("search_samples", {"text": "zzzz"})
    assert "nothing matches" in nothing
    workspace.run("load_sample", {"name": "chinese_good_luck"})
    assert workspace.data["strands"]


# ------------------------------------------- never on the app's Samples page
def test_the_samples_page_lists_nothing_from_the_library():
    on_page = dialog_samples()
    assert len(on_page) == 18, ("the Samples page changed: a design for the agent's craft library goes in "
                                "craft_library/catalog.json, not in SettingsDialog.SAMPLES")
    folder = ROOT / "src" / "samples"
    assert sorted(p.name for p in folder.glob("**/*.json")) == sorted(on_page), \
        "src/samples/ holds exactly the Samples page's files: library designs go in craft_library/"
    for entry in LISTED:
        if "file" in entry["build"]:
            path = library.path_of(entry)
            assert folder.resolve() not in path.parents or path.name in on_page, entry["name"]


def test_the_library_is_not_part_of_the_app():
    assert not (ROOT / "src" / "craft_library").exists()
    for spec in (ROOT / "src").glob("*.spec"):
        assert "craft_library" not in spec.read_text(encoding="utf-8"), spec.name
    for source in (ROOT / "src").glob("*.py"):
        if source.name == "agent_panel.py":  # shows the agent's tool rows, by tool name only
            continue
        assert "craft_library" not in source.read_text(encoding="utf-8", errors="ignore"), source.name
