"""
Headless check of the UI zoom (Settings > Display).

Runs the real main window at several zoom levels and asserts that the
toolbar, side buttons, layer buttons, right-click menu, application font and
cursor all scale by the zoom, that a runtime zoom change re-applies live, and
that 100 % leaves every size exactly as it was before the feature.

    xvfb-run -a -s "-screen 0 3840x2160x24 -dpi 192" python automation_tests/test_ui_zoom.py
    python automation_tests/test_ui_zoom.py            (Windows / macOS, on screen)

Optional: OPENSTRAND_TEST_SCREENSHOT_DIR=/some/dir saves a PNG per zoom.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'src')
sys.path.insert(0, SRC)
os.chdir(SRC)
os.environ.setdefault('QT_LOGGING_RULES', '*=false')

import logging
logging.disable(logging.CRITICAL)

from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QApplication, QMenu
from PyQt5.QtTest import QTest

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)

import ui_zoom
import display_settings

ui_zoom.install(app)
info = display_settings.detect()
ui_zoom.state.screen_info = info
display_settings.choose_startup_zoom({}, info)

from main import load_user_settings
settings = load_user_settings()
from main_window import MainWindow

BASE = {'toolbar_h': 32, 'gear': 32, 'round': 40, 'layer_w': 146, 'layer_h': 40, 'menu_row': 35}
ZOOMS = [100, 125, 150, 200]
failures = []


def check(label, got, expected, tol=1):
    if abs(got - expected) > tol:
        failures.append(f"{label}: got {got}, expected {expected}")


def build_window():
    w = MainWindow()
    ui_zoom.apply_all()
    w.set_language('en')
    w.apply_theme(settings[0])
    screen = app.primaryScreen().availableGeometry()
    w.resize(min(1920, screen.width()), min(1080, screen.height()))
    w.show()
    app.processEvents()
    QTest.qWait(250)
    canvas = w.canvas
    canvas.start_new_strand_mode(1)
    QTest.qWait(80)
    QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(300, 400))
    QTest.mouseMove(canvas, pos=QPoint(500, 300))
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(500, 300))
    QTest.qWait(150)
    app.processEvents()
    return w


def measure(w):
    lp = w.layer_panel
    btns = list(getattr(lp, 'layer_buttons', []))
    m = {
        'toolbar_h': w.move_button.height(),
        'gear': w.settings_button.height(),
        'round': lp.zoom_in_button.height(),
        'layer_w': btns[0].width() if btns else 0,
        'layer_h': btns[0].height() if btns else 0,
        'app_font_pt': round(app.font().pointSizeF(), 2),
    }
    # right-click menu row height: open the layer menu, read the first action's rect
    if btns:
        b = btns[0]
        result = {}

        def grab_menu():
            for tl in app.topLevelWidgets():
                if tl.isVisible() and isinstance(tl, QMenu):
                    acts = [a for a in tl.actions() if not a.isSeparator()]
                    if acts:
                        result['menu_row'] = tl.actionGeometry(acts[0]).height()
                    tl.close()
        QTimer.singleShot(400, grab_menu)
        ev = QContextMenuEvent(QContextMenuEvent.Mouse, b.rect().center(), b.mapToGlobal(b.rect().center()))
        app.postEvent(b, ev)
        QTest.qWait(700)
        app.processEvents()
        m['menu_row'] = result.get('menu_row', 0)
    return m


def expect_for(zoom, base_pt):
    f = zoom / 100.0
    return {k: round(v * f) for k, v in BASE.items()} | {'app_font_pt': round(base_pt * f / ui_zoom.state.point_dpi_scale, 2)}


shots = os.environ.get('OPENSTRAND_TEST_SCREENSHOT_DIR')
base_pt = ui_zoom.state.base_font.pointSizeF()
report = {}

for zoom in ZOOMS:
    ui_zoom.state.zoom = zoom
    ui_zoom.apply_all()
    w = build_window()
    m = measure(w)
    exp = expect_for(zoom, base_pt)
    for k in ('toolbar_h', 'gear', 'round', 'layer_w', 'layer_h', 'menu_row'):
        check(f"zoom {zoom} {k}", m[k], exp[k])
    check(f"zoom {zoom} app font", m['app_font_pt'], exp['app_font_pt'], tol=0.3)
    report[zoom] = m
    if shots:
        os.makedirs(shots, exist_ok=True)
        w.grab().save(os.path.join(shots, f'ui_zoom_{zoom}.png'), 'PNG')

    if zoom == ZOOMS[0]:
        # live change on the same window
        ui_zoom.set_zoom(200)
        app.processEvents()
        QTest.qWait(150)
        check("live 100->200 toolbar_h", w.move_button.height(), 64)
        ui_zoom.set_multiplier('toolbar', 150)
        app.processEvents()
        check("toolbar fine-tune 150 at 200 %", w.move_button.height(), 96)
        check("layer button unaffected by toolbar fine-tune", w.layer_panel.layer_buttons[0].height(), 80)
        ui_zoom.set_multiplier('toolbar', 100)
        ui_zoom.set_zoom(100)
        app.processEvents()
        check("live back to 100 toolbar_h", w.move_button.height(), 32)
        # cursor
        ui_zoom.set_cursor(size=48)
        app.processEvents()
        check("cursor pixmap 48", w.canvas.cursor().pixmap().width() if not w.canvas.cursor().pixmap().isNull() else 0, 48)
        ui_zoom.set_cursor(size=32)
        # settings dialog Display page opens and is index 1
        w.open_display_settings()
        app.processEvents()
        QTest.qWait(300)
        d = w._settings_dialog
        if d.stacked_widget.currentIndex() != 1 or d.categories_list.item(1).text() != 'Display':
            failures.append("Display page is not category 1")
        if shots:
            d.grab().save(os.path.join(shots, 'ui_zoom_display_page.png'), 'PNG')
        d.hide()
    # hide instead of close: closeEvent would ask to save the drawing
    w.hide()
    w.deleteLater()
    app.processEvents()

print(json.dumps({'screen': {k: info[k] for k in ('platform', 'width', 'height', 'os_scale')},
                  'suggested': ui_zoom.state.suggested, 'point_dpi_scale': ui_zoom.state.point_dpi_scale,
                  'measured': report}, indent=1))
if failures:
    print("FAILED:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("OK: all sizes follow the zoom")
sys.exit(0)
