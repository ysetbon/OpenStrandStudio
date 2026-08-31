"""Every undo/redo state records what produced it.

The stack used to store snapshots and nothing else, so a step could not say
which mode, panel, dialog or menu entry created it. These tests cover the
record itself (undo_redo_metadata.py), the fact that it is written into the
state file — so it survives a restart, an export/import and session recovery —
and that the manager keeps a journal of what was done, undos included.
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtWidgets import QApplication

import undo_redo_metadata as meta
from undo_redo_manager import UndoRedoManager

APP = QApplication.instance() or QApplication([])


class FakeMode:
    pass


class MoveMode(FakeMode):
    pass


class FakeStrand:
    def __init__(self, layer_name):
        self.layer_name = layer_name


class FakeLayerPanel:
    def __init__(self):
        self.locked_layers = set()
        self.lock_mode = False
        self.language_code = "en"


class FakeCanvas:
    """The little of a canvas that saving a state actually touches."""

    def __init__(self, strands=None):
        self.strands = strands or []
        self.groups = {}
        self.strand_colors = {}
        self.selected_strand = None
        self.shadow_enabled = True
        self.show_control_points = False
        self.layer_panel = FakeLayerPanel()
        self.current_mode = MoveMode()
        self.current_mode_name = "move"


def make_manager(tmp_path):
    canvas = FakeCanvas()
    manager = UndoRedoManager(canvas, canvas.layer_panel, str(tmp_path))
    return manager, canvas


# ----------------------------------------------------------------- the record

def test_the_active_mode_is_recorded_even_when_the_caller_says_nothing():
    canvas = FakeCanvas()
    record = meta.build_metadata(canvas=canvas, origin="layer_panel.py:some_handler")
    assert record["mode"] == "move"
    assert record["source"] == "mode"
    assert record["origin"] == "layer_panel.py:some_handler"


def test_the_mode_falls_back_to_the_mode_object_class():
    canvas = FakeCanvas()
    del canvas.current_mode_name
    assert meta.infer_mode(canvas) == "move"


def test_a_described_action_names_what_it_touched_and_where_it_came_from():
    record = meta.build_metadata("move.strand", source="mode", targets=["1_2"], detail="start")
    record["mode"] = "move"
    assert meta.describe(record) == "Moved a point - 1_2, start  ·  move mode"
    assert meta.short_label(record) == "Moved a point (1_2)"


def test_an_uncatalogued_action_still_reads_as_words():
    record = meta.build_metadata("made.up_thing", source="panel")
    assert meta.describe(record) == "Made up thing  ·  panel"


def test_a_state_with_no_record_says_so_rather_than_rendering_blank():
    assert meta.describe(None) == "Unrecorded change"
    assert meta.short_label(None) == ""


def test_targets_accept_names_strands_or_a_bare_string():
    record = meta.build_metadata("layer.delete", targets=[FakeStrand("2_1"), "3_1", None])
    assert record["targets"] == ["2_1", "3_1"]
    assert meta.build_metadata("layer.delete", targets="1_1")["targets"] == ["1_1"]


def test_layer_names_resolves_indices_and_skips_ones_that_are_gone():
    canvas = FakeCanvas([FakeStrand("1_1"), FakeStrand("1_2")])
    assert meta.layer_names(canvas, [0, 1, 7]) == ["1_1", "1_2"]


# ------------------------------------------------------- it lives in the file

def test_the_record_round_trips_through_the_state_file(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"strands": [], "groups": {}}), encoding="utf-8")
    record = meta.build_metadata("mask.create", source="mode", targets=["1_1", "2_1"])

    assert meta.write_metadata(str(path), record) is True
    assert meta.read_metadata(str(path)) == record
    # The drawing itself is untouched by the injection.
    assert json.loads(path.read_text(encoding="utf-8"))["strands"] == []


def test_a_state_file_without_a_record_reads_back_as_none(tmp_path):
    path = tmp_path / "old_state.json"
    path.write_text(json.dumps({"strands": []}), encoding="utf-8")
    assert meta.read_metadata(str(path)) is None
    assert meta.read_metadata(str(tmp_path / "missing.json")) is None


# ------------------------------------------------------------ via the manager

def test_saving_a_state_writes_its_provenance_into_the_state_file(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="layer.delete", source="panel",
                       targets=["1_1"], detail="deleted")

    assert manager.current_step == 1
    stored = meta.read_metadata(manager._get_state_filename(1))
    assert stored["action"] == "layer.delete"
    assert stored["source"] == "panel"
    assert stored["targets"] == ["1_1"]
    assert stored["mode"] == "move"          # the tool that was held, recorded either way
    assert stored["origin"].endswith("test_saving_a_state_writes_its_provenance_into_the_state_file")


def test_an_unannotated_save_still_records_the_mode_and_the_call_site(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True)
    stored = manager.metadata_for_step(1)
    assert stored["action"] == "system.unknown"
    assert stored["mode"] == "move"
    assert "test_undo_redo_metadata.py" in stored["origin"]


def test_the_record_is_read_back_from_disk_when_it_is_not_cached(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    manager._state_metadata = {}          # a session recovered from disk starts empty
    assert manager.metadata_for_step(1)["action"] == "attach.new"


def test_the_history_lists_every_step_with_what_produced_it(tmp_path):
    manager, canvas = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    canvas.strands.append(FakeStrand("1_1"))          # so the next save is not identical
    manager.save_state(allow_empty=True, action="strand.hidden", source="menu",
                       targets=["1_1"], detail="hidden")

    entries = manager.get_history_entries()
    assert [e["step"] for e in entries] == [1, 2]
    assert entries[0]["description"].startswith("Drew a new strand - 1_1")
    assert entries[1]["description"].startswith("Toggled layer visibility - 1_1, hidden")
    assert entries[1]["is_current"] is True
    assert manager.current_state_description().startswith("Toggled layer visibility")


def test_dropping_the_future_drops_its_records_too(tmp_path):
    manager, canvas = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    canvas.strands.append(FakeStrand("1_1"))
    manager.save_state(allow_empty=True, action="strand.hidden", targets=["1_1"])

    manager.current_step = 1                          # as an undo leaves it
    manager._clear_future_states()
    assert manager.max_step == 1
    assert 2 not in manager._state_metadata


def test_the_journal_records_edits_and_the_undos_and_redos_themselves(tmp_path):
    manager, canvas = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    canvas.strands.append(FakeStrand("1_1"))
    manager.save_state(allow_empty=True, action="strand.hidden", targets=["1_1"])

    # Stand in for the real load, which needs a live canvas: what is under test
    # here is that undo()/redo() journal the action they moved across.
    manager._undo_impl = lambda: setattr(manager, "current_step", manager.current_step - 1) or True
    manager._redo_impl = lambda: setattr(manager, "current_step", manager.current_step + 1) or True

    manager.undo()
    manager.redo()

    journal = manager.get_session_journal()
    assert [e["kind"] for e in journal] == ["edit", "edit", "undo", "redo"]
    # An undo reverses the action that made the state it left...
    assert journal[2]["metadata"]["action"] == "strand.hidden"
    # ...and a redo replays the action of the state it re-enters.
    assert journal[3]["metadata"]["action"] == "strand.hidden"
    assert "UNDO" in meta.journal_line("undo", journal[2]["metadata"])


def test_an_undo_that_moved_nowhere_journals_nothing(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    before = len(manager.history_journal)
    manager._undo_impl = lambda: False          # e.g. nothing to undo
    manager.undo()
    assert len(manager.history_journal) == before


def test_the_journal_is_mirrored_to_a_readable_log_next_to_the_states(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="mask.create", source="mode",
                       targets=["1_1", "2_1"])
    assert os.path.exists(manager.journal_path)
    line = Path(manager.journal_path).read_text(encoding="utf-8").strip()
    assert "Created a mask - 1_1, 2_1" in line


def test_the_button_tooltip_names_the_action_and_survives_an_unrecorded_state():
    record = meta.build_metadata("layer.delete", source="panel", targets=["2_1"])
    assert UndoRedoManager._with_action("Undo", record) == "Undo\nDeleted a layer (2_1)"
    assert UndoRedoManager._with_action("Undo", None) == "Undo"
