"""Capture the README screenshot: the main window with the box stitch sample
loaded, one group in the group column, and the column's collapse chevron
(the 1.110 group-column toggle) visible at the bottom right.

Writes docs/readme/main_window.png. Run offscreen:

    QT_QPA_PLATFORM=offscreen python automation_tests/capture_readme_screenshot.py
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import _bootstrap, _force_available_size, _wait

SAMPLE = os.path.join(SRC_DIR, "samples", "box_stitch.json")
OUT_PATH = os.path.join(ROOT_DIR, "docs", "readme", "main_window.png")
WIDTH, HEIGHT = 1920, 1030


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QPixmap, QWindow

    # Never-mapped windows report isExposed() False, and the canvas then skips
    # blitting its supersampled buffer (see record_tutorial_videos.py).
    QWindow.isExposed = lambda self: True
    app, window = _bootstrap()
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()
    _force_available_size(window, WIDTH, HEIGHT)

    # Load the sample exactly the way Load does for a history export.
    undo_mgr = window.layer_panel.undo_redo_manager
    window.toggle_shadow_button.setChecked(False)
    window.canvas.shadow_enabled = False
    assert undo_mgr.import_history(SAMPLE), "sample did not import"
    window.canvas.layer_panel.refresh()
    window.canvas.update()
    app.processEvents()
    _wait(400)

    # One group so the column shows the tree, not just Create Group.
    glm = window.layer_panel.group_layer_manager
    glm.create_group_with_params("Box Stitch", ["1", "2"], skip_dialog=True)
    app.processEvents()
    _wait(400)

    # Clean presentation: view mode (no attach targets), no control-point
    # markers, nothing selected.
    window.set_view_mode()
    window.toggle_control_points_button.setChecked(False)
    window.canvas.show_control_points = False
    window.canvas.deselect_all_strands()
    window.canvas.update()
    app.processEvents()
    _wait(400)

    lp = window.layer_panel
    assert not lp.group_panel_collapsed and lp.group_toggle_button.isVisible(), \
        "group column must be expanded with its chevron showing"

    pix = QPixmap(window.size())
    pix.fill(Qt.white)
    window.render(pix)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    pix.save(OUT_PATH, "PNG")
    print("[readme] wrote %s (%dx%d)" % (OUT_PATH, pix.width(), pix.height()), flush=True)

    # Tear-down of the offscreen window hangs in QApplication shutdown, and
    # nothing needs flushing once the PNG is on disk.
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
