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


class AttachMode(FakeMode):
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


def test_the_mode_comes_from_the_mode_object_class():
    canvas = FakeCanvas()
    del canvas.current_mode_name
    assert meta.infer_mode(canvas) == "move"


def test_the_live_mode_object_beats_a_remembered_name_that_went_stale():
    # select_strand swaps current_mode straight to attach mode without going
    # through set_mode, so the remembered name lags behind the real tool.
    canvas = FakeCanvas()
    canvas.current_mode = AttachMode()
    canvas.current_mode_name = "rotate"          # stale
    assert meta.infer_mode(canvas) == "attach"


def test_the_remembered_name_covers_what_no_mode_object_can_express():
    canvas = FakeCanvas()
    canvas.current_mode = None                   # set_mode("new_strand")
    canvas.current_mode_name = "new_strand"
    assert meta.infer_mode(canvas) == "new_strand"
    canvas.current_mode = "control_points"       # set_mode stores a bare string
    assert meta.infer_mode(canvas) == "control_points"
    canvas.current_mode = None
    canvas.current_mode_name = None
    assert meta.infer_mode(canvas) is None


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


def test_a_failed_metadata_rewrite_leaves_the_snapshot_intact(tmp_path, monkeypatch):
    """The record is an annotation; losing it must never cost the undo step."""
    path = tmp_path / "state.json"
    original = json.dumps({"strands": [{"layer_name": "1_1"}], "groups": {}})
    path.write_text(original, encoding="utf-8")

    def explode(*args, **kwargs):
        raise OSError("no space left on device")

    monkeypatch.setattr(meta.json, "dump", explode)
    assert meta.write_metadata(str(path), meta.build_metadata("attach.new")) is False
    # The drawing is still there, byte for byte, and no debris was left behind.
    assert path.read_text(encoding="utf-8") == original
    assert [p.name for p in tmp_path.iterdir()] == ["state.json"]


def test_the_readable_log_follows_the_session_being_worked_on(tmp_path):
    manager, _ = make_manager(tmp_path)
    first = manager.journal_path
    assert manager.session_id in first

    # load_specific_state adopts another session's id mid-run; the log has to
    # follow it rather than keep appending to the session we left.
    manager.session_id = "20200101000000"
    assert manager.journal_path != first
    assert "20200101000000_history.log" in manager.journal_path


def test_adopting_a_session_leaves_none_of_the_old_one_in_the_journal(tmp_path):
    """The journal is "this session's activity" — after a switch it must be its."""
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    assert [e["kind"] for e in manager.history_journal] == ["edit"]

    manager.session_id = "20200101000000"
    manager._adopt_session("session 20200101000000 at step 3")

    kinds = [e["kind"] for e in manager.history_journal]
    assert kinds == ["load"]                      # nothing carried over
    entry = manager.get_session_journal()[0]
    assert entry["metadata"]["action"] == "system.load"
    assert "20200101000000" in entry["description"]
    # ...and the line went to the adopted session's log, not the one we left.
    assert "20200101000000_history.log" in manager.journal_path
    assert "Loaded a document" in Path(manager.journal_path).read_text(encoding="utf-8")


def test_adopting_another_session_rebuilds_the_records_from_its_files(tmp_path):
    manager, canvas = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    assert manager.metadata_for_step(1)["action"] == "attach.new"

    # A second session writes its own step 1 with a different action.
    other = "20200101000000"
    manager.session_id = other
    canvas.strands.append(FakeStrand("2_1"))
    manager.current_step = 0
    manager.max_step = 0
    manager.save_state(allow_empty=True, action="mask.create", targets=["2_1"])

    # Back to the first session: the cache must not answer with the other one's.
    manager._reload_metadata_from_files()
    assert manager.metadata_for_step(1)["action"] == "mask.create"


def test_a_whole_set_edit_names_every_layer_in_the_set():
    canvas = FakeCanvas([FakeStrand("1_1"), FakeStrand("1_2"), FakeStrand("2_1"),
                         FakeStrand("1_3_2_1")])
    # Masks built on the set carry its prefix and are repainted with it.
    assert meta.set_member_names(canvas, 1) == ["1_1", "1_2", "1_3_2_1"]
    assert meta.set_member_names(canvas, "1") == ["1_1", "1_2", "1_3_2_1"]
    assert meta.set_member_names(canvas, 2) == ["2_1"]
    assert meta.set_member_names(canvas, 9) == []


def test_a_journalled_undo_is_stamped_when_it_happened(tmp_path):
    """An undo replays a record made earlier; the log is a log of events."""
    made_earlier = meta.build_metadata("attach.new", targets=["1_1"])
    made_earlier["at"] = "2020-01-01T00:00:00"

    line = meta.journal_line("undo", made_earlier, at="2026-08-31T18:30:00")
    assert line.startswith("2026-08-31T18:30:00  UNDO")
    assert "2020-01-01" not in line

    # With no event time it still writes a line, stamped now rather than never.
    assert meta.journal_line("edit", made_earlier).startswith("20")


def test_the_manager_logs_each_event_at_its_own_time(tmp_path):
    manager, _ = make_manager(tmp_path)
    manager.save_state(allow_empty=True, action="attach.new", targets=["1_1"])
    manager._undo_impl = lambda: setattr(manager, "current_step", 0) or True
    manager.undo()

    lines = Path(manager.journal_path).read_text(encoding="utf-8").strip().split("\n")
    stamps = [line.split("  ")[0] for line in lines]
    assert stamps == sorted(stamps)          # the log reads in the order it happened
    assert lines[-1].split("  ")[1].startswith("UNDO")
