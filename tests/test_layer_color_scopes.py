import os
import sys
import json
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QColorDialog

import numbered_layer_button as layer_button_module
from numbered_layer_button import NumberedLayerButton
from attached_strand import AttachedStrand
from save_load_manager import serialize_project_state, load_strands_from_data
from strand import Strand
from layer_state_manager import LayerStateManager
from group_layers import GroupPanel
from layer_panel import LayerPanel
from strand_drawing_canvas import StrandDrawingCanvas
from undo_redo_manager import UndoRedoManager


APP = QApplication.instance() or QApplication([])


class FakeUndoRedoManager:
    def __init__(self):
        self._last_save_time = 1
        self.save_count = 0

    def save_state(self):
        self.save_count += 1


class FakeCanvas:
    def __init__(self, strands):
        self.strands = strands
        self.undo_redo_manager = FakeUndoRedoManager()
        self.strand_colors = {1: QColor("purple"), 2: QColor("orange")}
        self.update_count = 0

    def update(self):
        self.update_count += 1


class FakePanel:
    def __init__(self, strands):
        self.language_code = "en"
        self.canvas = FakeCanvas(strands)
        self.set_colors = {1: QColor("purple"), 2: QColor("orange")}


class FakeStrand:
    def __init__(self, layer_name, fill="purple", stroke="black"):
        self.layer_name = layer_name
        self.color = QColor(fill)
        self.stroke_color = QColor(stroke)

    def set_color(self, color):
        self.color = QColor(color)


class FakeColorDialog:
    Accepted = QColorDialog.Accepted
    ShowAlphaChannel = QColorDialog.ShowAlphaChannel
    DontUseNativeDialog = QColorDialog.DontUseNativeDialog
    selected_color = QColor("black")

    def __init__(self, parent=None):
        self.current = QColor()

    def setWindowTitle(self, title):
        self.title = title

    def setOption(self, option):
        pass

    def setCurrentColor(self, color):
        self.current = QColor(color)

    def currentColor(self):
        return QColor(self.selected_color)

    def exec_(self):
        return QColorDialog.Accepted


def color_tuple(color):
    return color.getRgb()


def make_button(monkeypatch, layer_name="1_1"):
    monkeypatch.setattr(layer_button_module, "QColorDialog", FakeColorDialog)
    button = NumberedLayerButton(layer_name, 1, QColor("purple"))
    monkeypatch.setattr(button, "translate_color_dialog", lambda dialog, strings: None)
    return button


def test_set_wide_stroke_changes_only_matching_set(monkeypatch):
    strands = [
        FakeStrand("1_1"),
        FakeStrand("1_2"),
        FakeStrand("2_1"),
    ]
    panel = FakePanel(strands)
    button = make_button(monkeypatch)
    FakeColorDialog.selected_color = QColor(10, 20, 30, 200)

    button.change_stroke_color(strands[1], panel)

    assert color_tuple(strands[0].stroke_color) == (10, 20, 30, 200)
    assert color_tuple(strands[1].stroke_color) == (10, 20, 30, 200)
    assert color_tuple(strands[2].stroke_color) == (0, 0, 0, 255)
    assert panel.canvas.undo_redo_manager.save_count == 1


def test_layer_only_stroke_changes_only_clicked_strand(monkeypatch):
    strands = [FakeStrand("1_1"), FakeStrand("1_2")]
    panel = FakePanel(strands)
    button = make_button(monkeypatch, "1_2")
    FakeColorDialog.selected_color = QColor(40, 50, 60, 180)

    button.change_layer_stroke_color(strands[1], panel)

    assert color_tuple(strands[0].stroke_color) == (0, 0, 0, 255)
    assert color_tuple(strands[1].stroke_color) == (40, 50, 60, 180)
    assert panel.canvas.undo_redo_manager.save_count == 1


def test_layer_only_fill_preserves_set_maps_and_syncs_stroke_alpha(monkeypatch):
    strands = [FakeStrand("1_1"), FakeStrand("1_2")]
    panel = FakePanel(strands)
    button = make_button(monkeypatch, "1_2")
    original_set_color = color_tuple(panel.set_colors[1])
    original_canvas_set_color = color_tuple(panel.canvas.strand_colors[1])
    FakeColorDialog.selected_color = QColor(70, 80, 90, 123)

    button.change_layer_color(strands[1], panel)

    assert color_tuple(strands[0].color) == QColor("purple").getRgb()
    assert color_tuple(strands[1].color) == (70, 80, 90, 123)
    assert color_tuple(strands[1].stroke_color) == (0, 0, 0, 123)
    assert color_tuple(button.color) == (70, 80, 90, 123)
    assert color_tuple(panel.set_colors[1]) == original_set_color
    assert color_tuple(panel.canvas.strand_colors[1]) == original_canvas_set_color
    assert panel.canvas.undo_redo_manager.save_count == 1


def test_attached_circle_stroke_transparency_is_preserved():
    AttachedStrand = type("AttachedStrand", (FakeStrand,), {})
    visible = AttachedStrand("1_2")
    visible.circle_stroke_color = QColor(1, 2, 3, 255)
    transparent = AttachedStrand("1_3")
    transparent.circle_stroke_color = QColor(1, 2, 3, 0)

    NumberedLayerButton._apply_stroke_color(visible, QColor(9, 8, 7, 150))
    NumberedLayerButton._apply_stroke_color(transparent, QColor(9, 8, 7, 150))

    assert color_tuple(visible.circle_stroke_color) == (9, 8, 7, 150)
    assert color_tuple(transparent.circle_stroke_color) == (1, 2, 3, 0)


def test_real_attached_circle_strokes_update_visible_end_independently():
    parent = real_strand("1_1", "purple", "black")
    attached = AttachedStrand(parent, QPointF(100, 0), 1)
    attached.start_circle_stroke_color = QColor(1, 2, 3, 0)
    attached.end_circle_stroke_color = QColor(1, 2, 3, 255)

    NumberedLayerButton._apply_stroke_color(
        attached,
        QColor(9, 8, 7, 150),
    )

    assert color_tuple(attached.stroke_color) == (9, 8, 7, 150)
    assert color_tuple(attached.start_circle_stroke_color) == (1, 2, 3, 0)
    assert color_tuple(attached.end_circle_stroke_color) == (9, 8, 7, 150)


class PersistencePanel:
    def __init__(self):
        self.set_colors = {}
        self.locked_layers = set()
        self.lock_mode = False
        self.layer_buttons = []

    def parent(self):
        return None

    def apply_lock_state(self, locked_layers, lock_mode):
        self.locked_layers = set(locked_layers)
        self.lock_mode = lock_mode

    def update_layer_buttons_lock_state(self):
        pass

    def simulate_refresh_button_click(self):
        pass

    def refresh(self):
        pass

    def rebuild_layer_buttons(self):
        pass


class PersistenceCanvas:
    def __init__(self, strands=None):
        self.strands = strands or []
        self.groups = {}
        self.strand_colors = {}
        self.selected_strand = None
        self.selected_strand_index = None
        self.newest_strand = None
        self.shadow_enabled = True
        self.show_control_points = False
        self.strand_width = 20
        self.stroke_color = QColor("black")
        self.stroke_width = 4
        self.layer_panel = PersistencePanel()
        self.update_count = 0

    def update(self):
        self.update_count += 1

    def deselect_strand(self):
        self.selected_strand = None
        self.selected_strand_index = None

    def clear_strands(self):
        self.strands = []


def real_strand(layer_name, fill, stroke="black"):
    set_number = int(layer_name.split("_")[0])
    return Strand(
        QPointF(0, 0),
        QPointF(100, 0),
        20,
        QColor(fill),
        QColor(stroke),
        4,
        set_number,
        layer_name,
    )


def test_save_load_preserves_layer_colors_strokes_and_canonical_set_color():
    strands = [
        real_strand("1_1", "purple", "black"),
        real_strand("1_2", "red", "green"),
    ]
    canvas = PersistenceCanvas(strands)
    canvas.strand_colors = {1: QColor("purple")}
    canvas.layer_panel.set_colors = {1: QColor("purple")}

    # Exercise the same JSON conversion used for project files and undo states.
    state = json.loads(json.dumps(serialize_project_state(strands, {}, canvas)))
    loaded_canvas = PersistenceCanvas()
    loaded_strands = load_strands_from_data(state, loaded_canvas)[0]

    assert color_tuple(loaded_strands[0].color) == QColor("purple").getRgb()
    assert color_tuple(loaded_strands[1].color) == QColor("red").getRgb()
    assert color_tuple(loaded_strands[1].stroke_color) == QColor("green").getRgb()
    assert color_tuple(loaded_canvas.strand_colors[1]) == QColor("purple").getRgb()
    assert color_tuple(loaded_canvas.layer_panel.set_colors[1]) == QColor("purple").getRgb()


def test_legacy_save_without_set_color_map_infers_main_strand_color():
    strands = [
        real_strand("1_1", "purple"),
        real_strand("1_2", "purple"),
    ]
    canvas = PersistenceCanvas(strands)
    state = serialize_project_state(strands, {}, canvas)
    state.pop("strand_colors")

    loaded_canvas = PersistenceCanvas()
    load_strands_from_data(state, loaded_canvas)

    assert color_tuple(loaded_canvas.strand_colors[1]) == QColor("purple").getRgb()
    assert color_tuple(loaded_canvas.layer_panel.set_colors[1]) == QColor("purple").getRgb()


def test_partial_set_color_map_is_completed_and_stale_sets_are_removed():
    strands = [
        real_strand("1_1", "purple"),
        real_strand("2_1", "orange"),
    ]
    canvas = PersistenceCanvas(strands)
    canvas.strand_colors = {1: QColor("blue"), 99: QColor("red")}
    canvas.layer_panel.set_colors = {2: QColor("green"), 98: QColor("yellow")}

    state = serialize_project_state(strands, {}, canvas)

    assert set(state["strand_colors"]) == {"1", "2"}
    assert state["strand_colors"]["1"] == {
        "r": 0, "g": 0, "b": 255, "a": 255
    }
    assert state["strand_colors"]["2"] == {
        "r": 0, "g": 128, "b": 0, "a": 255
    }

    # Loading also ignores stale entries and infers an omitted active set.
    state["strand_colors"] = {
        "1": state["strand_colors"]["1"],
        "99": {"r": 255, "g": 0, "b": 0, "a": 255},
    }
    loaded_canvas = PersistenceCanvas()
    load_strands_from_data(state, loaded_canvas)

    assert set(loaded_canvas.strand_colors) == {1, 2}
    assert color_tuple(loaded_canvas.strand_colors[1]) == QColor("blue").getRgb()
    assert color_tuple(loaded_canvas.strand_colors[2]) == QColor("orange").getRgb()


def test_save_load_preserves_attached_fill_stroke_and_circle_transparency():
    parent = real_strand("1_1", "purple", "black")
    attached = AttachedStrand(parent, QPointF(100, 0), 1)
    attached.layer_name = "1_2"
    attached.set_number = 1
    attached.end = QPointF(160, 40)
    attached.color = QColor("red")
    attached.stroke_color = QColor("green")
    attached.start_circle_stroke_color = QColor(0, 0, 0, 0)
    attached.end_circle_stroke_color = QColor("green")
    parent.attached_strands = [attached]

    canvas = PersistenceCanvas([parent, attached])
    canvas.strand_colors = {1: QColor("purple")}
    canvas.layer_panel.set_colors = {1: QColor("purple")}
    state = json.loads(json.dumps(serialize_project_state(canvas.strands, {}, canvas)))

    loaded_canvas = PersistenceCanvas()
    loaded = load_strands_from_data(state, loaded_canvas)[0]
    loaded_attached = next(s for s in loaded if s.layer_name == "1_2")

    assert color_tuple(loaded_attached.color) == QColor("red").getRgb()
    assert color_tuple(loaded_attached.stroke_color) == QColor("green").getRgb()
    assert loaded_attached.start_circle_stroke_color.alpha() == 0
    assert color_tuple(loaded_attached.end_circle_stroke_color) == QColor("green").getRgb()
    assert color_tuple(loaded_canvas.strand_colors[1]) == QColor("purple").getRgb()


def snapshot_colors(canvas):
    return (
        tuple(color_tuple(strand.color) for strand in canvas.strands),
        tuple(color_tuple(strand.stroke_color) for strand in canvas.strands),
        color_tuple(canvas.strand_colors[1]),
        color_tuple(canvas.layer_panel.set_colors[1]),
    )


def test_real_undo_redo_restores_all_four_color_scopes_and_set_maps(tmp_path):
    strands = [
        real_strand("1_1", "purple", "black"),
        real_strand("1_2", "purple", "black"),
    ]
    canvas = PersistenceCanvas(strands)
    panel = canvas.layer_panel
    canvas.strand_colors = {1: QColor("purple")}
    panel.set_colors = {1: QColor("purple")}
    manager = UndoRedoManager(canvas, panel, str(tmp_path))
    canvas.undo_redo_manager = manager

    expected_states = []

    # Baseline.
    manager.save_state()
    expected_states.append(snapshot_colors(canvas))

    # Set-wide fill.
    for strand in canvas.strands:
        strand.set_color(QColor("blue"))
    canvas.strand_colors[1] = QColor("blue")
    panel.set_colors[1] = QColor("blue")
    manager.save_state()
    expected_states.append(snapshot_colors(canvas))

    # Layer-only fill.
    canvas.strands[1].set_color(QColor("red"))
    manager.save_state()
    expected_states.append(snapshot_colors(canvas))

    # Set-wide stroke.
    for strand in canvas.strands:
        strand.stroke_color = QColor("green")
    manager.save_state()
    expected_states.append(snapshot_colors(canvas))

    # Layer-only stroke.
    canvas.strands[1].stroke_color = QColor("yellow")
    manager.save_state()
    expected_states.append(snapshot_colors(canvas))

    assert manager.current_step == 5

    for expected in reversed(expected_states[:-1]):
        previous_step = manager.current_step
        manager.undo()
        assert manager.current_step == previous_step - 1
        assert snapshot_colors(canvas) == expected

    for expected in expected_states[1:]:
        previous_step = manager.current_step
        assert manager.redo()
        assert manager.current_step == previous_step + 1
        assert snapshot_colors(canvas) == expected


def test_undo_to_empty_clears_set_maps_and_redo_restores_them(tmp_path):
    strand = real_strand("1_1", "purple", "black")
    canvas = PersistenceCanvas([strand])
    panel = canvas.layer_panel
    canvas.strand_colors = {1: QColor("purple")}
    panel.set_colors = {1: QColor("purple")}
    manager = UndoRedoManager(canvas, panel, str(tmp_path))
    canvas.undo_redo_manager = manager

    manager.save_state()
    assert manager.current_step == 1

    manager.undo()
    assert manager.current_step == 0
    assert canvas.strands == []
    assert canvas.strand_colors == {}
    assert panel.set_colors == {}

    assert manager.redo()
    assert len(canvas.strands) == 1
    assert color_tuple(canvas.strand_colors[1]) == QColor("purple").getRgb()
    assert color_tuple(panel.set_colors[1]) == QColor("purple").getRgb()


def test_layer_state_manager_tracks_fill_stroke_alpha_and_canonical_set_color():
    first = real_strand("1_1", "purple", "black")
    second = real_strand("1_2", "red", "green")
    second.color.setAlpha(123)
    second.stroke_color.setAlpha(77)
    canvas = PersistenceCanvas([first, second])
    canvas.strand_colors = {1: QColor(20, 30, 40, 210)}

    manager = LayerStateManager(canvas)
    manager.save_current_state()

    assert color_tuple(QColor(manager.layer_state["colors"]["1_2"])) == (255, 0, 0, 123)
    assert color_tuple(QColor(manager.layer_state["stroke_colors"]["1_2"])) == (0, 128, 0, 77)
    assert color_tuple(QColor(manager.layer_state["set_colors"]["1"])) == (20, 30, 40, 210)


def test_layer_state_manager_legacy_json_apply_restores_tracked_colors():
    strand = real_strand("1_1", "red", "green")
    strand.color.setAlpha(123)
    strand.stroke_color.setAlpha(77)
    canvas = PersistenceCanvas([strand])
    canvas.strand_colors = {1: QColor(20, 30, 40, 210)}
    manager = LayerStateManager(canvas)
    manager.save_current_state()
    saved_state = json.loads(json.dumps(manager.layer_state))

    canvas.strands = []
    canvas.strand_colors = {1: QColor("white")}
    manager.apply_loaded_state(saved_state)

    assert color_tuple(canvas.strands[0].color) == (255, 0, 0, 123)
    assert color_tuple(canvas.strands[0].stroke_color) == (0, 128, 0, 77)
    assert color_tuple(canvas.strand_colors[1]) == (20, 30, 40, 210)


def test_layer_state_manager_legacy_state_infers_map_without_leaking_stale_sets():
    strand = real_strand("1_1", "purple", "black")
    canvas = PersistenceCanvas([strand])
    manager = LayerStateManager(canvas)
    manager.set_layer_panel(canvas.layer_panel)
    manager.save_current_state()
    state = json.loads(json.dumps(manager.layer_state))
    state.pop("set_colors")

    canvas.strand_colors = {99: QColor("red")}
    canvas.layer_panel.set_colors = {99: QColor("red")}
    manager.apply_loaded_state(state)

    assert set(canvas.strand_colors) == {1}
    assert set(canvas.layer_panel.set_colors) == {1}
    assert color_tuple(canvas.strand_colors[1]) == QColor("purple").getRgb()


def test_group_duplicate_initializes_new_set_from_canonical_not_outlier():
    main = real_strand("1_1", "purple", "black")
    outlier = real_strand("1_2", "red", "green")
    layer_panel = SimpleNamespace(set_colors={1: QColor("purple")})
    canvas = SimpleNamespace(
        strand_colors={1: QColor("purple")},
        layer_panel=layer_panel,
    )
    group_panel = SimpleNamespace(canvas=canvas)

    GroupPanel._initialize_duplicate_set_colors(
        group_panel,
        [main, outlier],
        {1: 2},
    )

    assert color_tuple(canvas.strand_colors[2]) == QColor("purple").getRgb()
    assert color_tuple(layer_panel.set_colors[2]) == QColor("purple").getRgb()
    assert color_tuple(outlier.color) == QColor("red").getRgb()
    assert color_tuple(outlier.stroke_color) == QColor("green").getRgb()


def test_group_save_load_keeps_mixed_layer_colors_and_set_color():
    main = real_strand("1_1", "purple", "black")
    outlier = real_strand("1_2", "red", "green")
    canvas = PersistenceCanvas([main, outlier])
    canvas.strand_colors = {1: QColor("purple")}
    canvas.layer_panel.set_colors = {1: QColor("purple")}
    groups = {
        "mixed": {
            "layers": ["1_1", "1_2"],
            "main_strands": {main},
            "strands": [main, outlier],
            "control_points": {},
        }
    }

    state = json.loads(json.dumps(serialize_project_state(canvas.strands, groups, canvas)))
    loaded_canvas = PersistenceCanvas()
    loaded_strands, loaded_groups = load_strands_from_data(state, loaded_canvas)[:2]
    loaded_by_name = {strand.layer_name: strand for strand in loaded_strands}

    assert loaded_groups["mixed"]["strands"] == ["1_1", "1_2"]
    assert color_tuple(loaded_by_name["1_1"].color) == QColor("purple").getRgb()
    assert color_tuple(loaded_by_name["1_2"].color) == QColor("red").getRgb()
    assert color_tuple(loaded_by_name["1_2"].stroke_color) == QColor("green").getRgb()
    assert color_tuple(loaded_canvas.strand_colors[1]) == QColor("purple").getRgb()


def test_group_layer_button_creation_does_not_flatten_outlier_color():
    main = real_strand("2_1", "purple", "black")
    outlier = real_strand("2_2", "red", "green")
    canvas = SimpleNamespace(
        strands=[main, outlier],
        strand_colors={2: QColor("purple")},
        update=lambda: None,
    )
    panel = SimpleNamespace(
        canvas=canvas,
        set_counts={},
        set_colors={},
        lock_mode=False,
        add_layer_button=lambda *args: None,
        scroll_layout=SimpleNamespace(update=lambda: None),
        update_layer_button_states=lambda: None,
        refresh_after_attachment=lambda: None,
    )

    LayerPanel.on_strand_created(panel, outlier, preserve_layer_color=True)

    assert color_tuple(outlier.color) == QColor("red").getRgb()
    assert color_tuple(outlier.stroke_color) == QColor("green").getRgb()
    assert color_tuple(panel.set_colors[2]) == QColor("purple").getRgb()


def test_new_strand_creation_keeps_existing_outlier_and_uses_set_color():
    existing = real_strand("1_1", "red", "black")
    new_strand = real_strand("1_2", "white", "black")

    class CreationPanel:
        def __init__(self):
            self.set_colors = {1: QColor("purple")}

        def on_strand_created(self, strand):
            pass

        def on_color_changed(self, *args):
            raise AssertionError("creation must not invoke set-wide recoloring")

        def update_attachable_states(self):
            pass

    creation_canvas = SimpleNamespace(
        strands=[existing],
        groups={},
        strand_colors={1: QColor("purple")},
        default_strand_color=QColor("purple"),
        layer_panel=CreationPanel(),
        selected_strand=None,
        undo_redo_manager=None,
        update=lambda: None,
        select_strand=lambda *args, **kwargs: None,
        strand_created=SimpleNamespace(emit=lambda *args: None),
    )

    StrandDrawingCanvas.on_strand_created(creation_canvas, new_strand)

    assert color_tuple(existing.color) == QColor("red").getRgb()
    assert color_tuple(new_strand.color) == QColor("purple").getRgb()
    assert color_tuple(creation_canvas.strand_colors[1]) == QColor("purple").getRgb()


def test_default_color_sync_does_not_create_a_phantom_set():
    canvas = SimpleNamespace(
        default_strand_color=QColor("blue"),
        strand_colors={},
    )
    panel = SimpleNamespace(
        canvas=canvas,
        set_colors={1: QColor(200, 170, 230, 255)},
    )

    LayerPanel.update_default_colors(panel)

    assert canvas.strand_colors == {}
    assert color_tuple(panel.set_colors[1]) == QColor("blue").getRgb()
