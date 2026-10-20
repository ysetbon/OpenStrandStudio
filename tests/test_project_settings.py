"""Drawing settings saved inside the project JSON.

Runs the real MainWindow offscreen: a project saved with one set of Settings
dialog values must open with those values again, whatever is active when it
is opened, and each tab keeps its own.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# user_settings.txt lives under APPDATA/OpenStrandStudio; keep the tests off
# the developer's real file.
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QFileDialog

from main_window import MainWindow
from project_settings import (PROJECT_SETTINGS_KEY, apply_project_settings,
                              capture_project_settings, read_project_settings)
from save_load_manager import apply_loaded_strands, load_strands_from_data

APP = QApplication.instance() or QApplication([])

PROJECT_VALUES = {
    "num_steps": 5,
    "max_blur_radius": 12.5,
    "control_point_base_fraction": 0.7,
    "distance_multiplier": 3.5,
    "curve_response_exponent": 2.5,
    "enable_third_control_point": False,
    "extension_length": 140.0,
    "extension_dash_count": 7,
    "arrow_head_length": 33.0,
    "arrow_head_stroke_width": 6,
    "arrow_line_width": 14.0,
    "use_default_arrow_color": True,
    "default_strand_width": 30,
    "default_stroke_width": 3,
}
PROJECT_SHADOW = QColor(200, 30, 40, 90)


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


@pytest.fixture
def window(monkeypatch, tmp_path):
    win = MainWindow()
    data = json.loads((SRC_DIR / "samples" / "bridge.json").read_text(encoding="utf-8"))
    if data.get("type") == "OpenStrandStudioHistory":
        data = data["states"][data.get("current_step", 1) - 1]["data"]
    loaded = load_strands_from_data(data, win.canvas)
    apply_loaded_strands(win.canvas, loaded[0], loaded[1])
    win.layer_panel.refresh()
    project = str(tmp_path / "project.json")
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (project, "JSON Files (*.json)")))
    monkeypatch.setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (project, "JSON Files (*.json)")))
    win._test_project = project
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def set_project_values(win):
    settings = dict(PROJECT_VALUES)
    settings["shadow_color"] = {"r": 200, "g": 30, "b": 40, "a": 90}
    apply_project_settings(win.canvas, settings, win.settings_dialog)


def assert_project_values(win):
    canvas, dialog = win.canvas, win.settings_dialog
    assert canvas.num_steps == 5
    assert canvas.max_blur_radius == pytest.approx(12.5)
    assert canvas.control_point_base_fraction == pytest.approx(0.7)
    assert canvas.distance_multiplier == pytest.approx(3.5)
    assert canvas.curve_response_exponent == pytest.approx(2.5)
    assert canvas.enable_third_control_point is False
    assert canvas.enable_curvature_bias_control is False
    assert canvas.extension_length == pytest.approx(140.0)
    assert canvas.extension_dash_count == 7
    assert canvas.arrow_head_length == pytest.approx(33.0)
    assert canvas.arrow_head_stroke_width == 6
    assert canvas.use_default_arrow_color is True
    assert canvas.strand_width == 30
    assert canvas.stroke_width == 3
    assert canvas.default_shadow_color == PROJECT_SHADOW
    for strand in canvas.strands:
        assert strand.distance_multiplier == pytest.approx(3.5)
        assert strand.shadow_color == PROJECT_SHADOW
    # The dialog shows the same values, so its Apply button keeps them.
    assert dialog.distance_mult_spinbox.value() == pytest.approx(3.5)
    assert dialog.num_steps_spinbox.value() == 5
    assert dialog.third_control_checkbox.isChecked() is False
    assert dialog.extension_dash_count == 7
    assert dialog.shadow_color == PROJECT_SHADOW


def reset_to_other_values(win):
    other = capture_project_settings(win.canvas, win.settings_dialog)
    other.update({"num_steps": 2, "distance_multiplier": 1.0, "enable_third_control_point": True,
                  "extension_dash_count": 10, "default_strand_width": 46,
                  "shadow_color": {"r": 0, "g": 0, "b": 0, "a": 150}})
    apply_project_settings(win.canvas, other, win.settings_dialog)
    assert win.canvas.distance_multiplier == pytest.approx(1.0)


def test_save_writes_settings_block(window):
    set_project_values(window)
    assert window.save_project()
    data = json.loads(Path(window._test_project).read_text(encoding="utf-8"))
    settings = read_project_settings(data)
    assert settings is not None
    assert settings["distance_multiplier"] == pytest.approx(3.5)
    assert settings["shadow_color"] == {"r": 200, "g": 30, "b": 40, "a": 90}
    # Only the project file carries it, not every undo state.
    if data.get("type") == "OpenStrandStudioHistory":
        assert all(PROJECT_SETTINGS_KEY not in s["data"] for s in data["states"])


def test_load_restores_saved_settings(window):
    set_project_values(window)
    assert window.save_project()
    reset_to_other_values(window)
    window.tab_manager.mark_active_saved()
    window.load_project()
    assert_project_values(window)


def test_load_does_not_write_user_settings(window):
    settings_file = os.path.join(window.settings_dialog.get_settings_directory(), "user_settings.txt")
    set_project_values(window)
    assert window.save_project()
    reset_to_other_values(window)

    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    Path(settings_file).write_text("Theme: default\n", encoding="utf-8")
    window.tab_manager.mark_active_saved()
    window.load_project()
    assert Path(settings_file).read_text(encoding="utf-8") == "Theme: default\n"


def test_old_files_keep_current_settings(window):
    assert window.save_project()
    path = Path(window._test_project)
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop(PROJECT_SETTINGS_KEY, None)
    path.write_text(json.dumps(data), encoding="utf-8")
    set_project_values(window)
    window.tab_manager.mark_active_saved()
    window.load_project()
    assert_project_values(window)


def test_tabs_keep_their_own_settings(window):
    tm = window.tab_manager
    set_project_values(window)
    first = tm.active_tab_id
    app_settings = window.settings_dialog.app_project_settings
    assert app_settings is not None

    # A new tab starts from the app's own settings, not the project's.
    tm.new_tab()
    second = tm.active_tab_id
    assert window.canvas.distance_multiplier == pytest.approx(app_settings["distance_multiplier"])
    assert window.canvas.num_steps == app_settings["num_steps"]

    tm.switch_to_tab(first)
    assert_project_values(window)

    tm.switch_to_tab(second)
    assert window.canvas.distance_multiplier == pytest.approx(app_settings["distance_multiplier"])


def test_malformed_values_are_ignored(window):
    before = capture_project_settings(window.canvas, window.settings_dialog)
    applied = apply_project_settings(window.canvas, {
        "num_steps": "lots", "distance_multiplier": None, "shadow_color": {"r": "x"},
        "default_level_color": 7, "enable_third_control_point": 1,
    }, window.settings_dialog)
    assert applied is False
    assert capture_project_settings(window.canvas, window.settings_dialog) == before


def test_snapshot_file_restores_saved_settings(window):
    from save_load_manager import save_strands
    set_project_values(window)
    settings = capture_project_settings(window.canvas, window.settings_dialog)
    save_strands(window.canvas.strands, window.group_layer_manager.get_group_data(),
                 window._test_project, window.canvas, project_settings=settings)
    reset_to_other_values(window)
    window.tab_manager.mark_active_saved()
    window.load_project()
    assert len(window.canvas.strands) > 0
    assert_project_values(window)
