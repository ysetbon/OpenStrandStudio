"""Screenshot the live app across screen resolutions, display scales,
languages and layer-panel modes, and check each shot for layout faults.

One process handles one display scale (Qt reads QT_SCALE_FACTOR before the
QApplication exists), so run it once per scale::

    python automation_tests/capture_screen_matrix.py --scale 1.5 --out DIR

Each shot is saved as ``DIR/<preset>__<lang>__<mode>.png`` at the screen's
physical pixel size, and ``DIR/results_<scale>.json`` records the measured
geometry plus a list of failed checks per shot (empty when the shot is fine).
``tests/test_screen_matrix.py`` runs this per scale and asserts no failures.

Options:
    --scale 1.5            display scale (100% = 1, 150% = 1.5, 200% = 2)
    --out DIR              output directory (created)
    --languages en,he      subset of languages (default: all)
    --presets 1080p,...    subset of preset ids for this scale (default: all)
    --modes normal,lock    subset of modes (default: normal,lock,copy)
    --font "Liberation Sans"  UI font family (stand-in for Segoe UI off Windows)
"""
import argparse
import json
import os
import sys
import tempfile

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Physical screens paired with the display scale Windows/macOS would typically
# run them at. ``chrome`` is the logical height the OS keeps (taskbar, or
# menu bar + dock); the app gets the rest as its available geometry.
PRESETS = [
    # id, title, physical width, physical height, scale, chrome (logical px)
    ("mac13_1280x800_100", 'MacBook 13" 1280x800', 1280, 800, 1.0, 95),
    ("laptop_1366x768_100", "Laptop 1366x768", 1366, 768, 1.0, 40),
    ("laptop_1366x768_125", "Laptop 1366x768 @125%", 1366, 768, 1.25, 40),
    ("1080p_1920x1080_100", "1080p 1920x1080", 1920, 1080, 1.0, 40),
    ("1080p_1920x1080_125", "1080p 1920x1080 @125%", 1920, 1080, 1.25, 40),
    ("1080p_1920x1080_150", "1080p 1920x1080 @150%", 1920, 1080, 1.5, 40),
    ("ultrawide_2560x1080_100", "Ultrawide 2560x1080", 2560, 1080, 1.0, 40),
    ("1440p_2560x1440_100", "1440p 2560x1440", 2560, 1440, 1.0, 40),
    ("1440p_2560x1440_150", "1440p 2560x1440 @150%", 2560, 1440, 1.5, 40),
    ("retina_2880x1800_200", "Retina 2880x1800 @200%", 2880, 1800, 2.0, 40),
    ("4k_3840x2160_150", "4K 3840x2160 @150%", 3840, 2160, 1.5, 40),
    ("4k_3840x2160_200", "4K 3840x2160 @200%", 3840, 2160, 2.0, 40),
]

MODES = ("normal", "lock", "copy")

# Bottom-panel buttons: "padding: 5px 10px" plus a 1px border each side.
BOTTOM_LABEL_PADDING = 10 * 2 + 2
CREATE_GROUP_LABEL_PADDING = 8


def presets_for_scale(scale):
    return [p for p in PRESETS if abs(p[4] - scale) < 1e-6]


def all_scales():
    return sorted({p[4] for p in PRESETS})


def _bootstrap(scale, font_family=None):
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QGuiApplication
    from PyQt5.QtWidgets import QApplication

    # Same DPI setup as src/main.py.
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication.instance() or QApplication(sys.argv)
    if font_family:
        # Stand in for the target platform's UI font (Windows: Segoe UI)
        # when capturing on another OS; metrics differ per family.
        from PyQt5.QtGui import QFont
        app.setFont(QFont(font_family))

    from main_window import MainWindow

    window = MainWindow()
    if getattr(window, "layer_panel", None) is not None:
        window.layer_panel.update_default_colors()
    window.set_language("en")
    window.show()
    app.processEvents()
    return app, window


def _wait(ms):
    from PyQt5.QtTest import QTest

    QTest.qWait(ms)


def _force_available_size(window, width, height):
    """Lay the live window out as if this were the screen's available area."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    window.setWindowState(Qt.WindowNoState)
    window.setMinimumSize(0, 0)
    window.setMaximumSize(16777215, 16777215)
    window.setGeometry(0, 0, width, height)
    window.setFixedSize(width, height)
    QApplication.processEvents()
    window.set_initial_splitter_sizes()
    QApplication.processEvents()
    _wait(150)
    QApplication.processEvents()


def _drag(canvas, x0, y0, x1, y1):
    from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt5.QtGui import QMouseEvent
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication

    QTest.mousePress(canvas, Qt.LeftButton, Qt.NoModifier, QPoint(x0, y0))
    QApplication.processEvents()
    steps = 6
    for i in range(1, steps + 1):
        p = QPointF(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
        QApplication.sendEvent(
            canvas,
            QMouseEvent(QEvent.MouseMove, p, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier),
        )
        QApplication.processEvents()
        _wait(20)
    QTest.mouseRelease(canvas, Qt.LeftButton, Qt.NoModifier, QPoint(x1, y1))
    _wait(150)


def _draw_sample_layers(window):
    """Create layers 1_1, 1_2 (attached), the mask 1_1_1_2 and 2_1 so the
    layer panel shows short, long and masked names."""
    canvas = window.canvas
    cw, ch = max(canvas.width(), 500), max(canvas.height(), 500)

    window.create_new_strand()
    _wait(80)
    _drag(canvas, int(cw * 0.18), int(ch * 0.30), int(cw * 0.50), int(ch * 0.34))

    window.set_attach_mode()
    _wait(80)
    s11 = next((s for s in canvas.strands if getattr(s, "layer_name", "") == "1_1"), None)
    if s11 is not None:
        _drag(canvas, int(s11.end.x()), int(s11.end.y()), int(cw * 0.55), int(ch * 0.66))

    window.create_new_strand()
    _wait(80)
    _drag(canvas, int(cw * 0.22), int(ch * 0.62), int(cw * 0.60), int(ch * 0.40))

    by_name = {getattr(s, "layer_name", ""): s for s in canvas.strands}
    if "1_1" in by_name and "1_2" in by_name:
        window.handle_mask_created(by_name["1_1"], by_name["1_2"])
        _wait(150)
    window.set_attach_mode()
    _wait(100)
    return sorted(getattr(s, "layer_name", "") for s in canvas.strands)


def _enter_mode(window, mode):
    lp = window.layer_panel
    if mode == "lock":
        lp.lock_layers_button.setChecked(True)
        lp.toggle_lock_mode()
        lp.toggle_layer_lock(0)  # one padlock closed, the rest open
    elif mode == "copy":
        if not lp.multi_select_mode:
            lp.toggle_multi_select_mode()
        lp.multi_selected_layers.add(1)
        lp.update_layer_button_multi_select_display()
        lp.copy_strand_data(0)  # copy badge on 1_1, paste chips on targets
    _wait(120)


def _leave_mode(window, mode):
    lp = window.layer_panel
    if mode == "lock":
        lp.toggle_layer_lock(0)
        lp.lock_layers_button.setChecked(False)
        lp.toggle_lock_mode()
        lp.previously_locked_layers.clear()
    elif mode == "copy":
        lp.clear_strand_data_clipboard()
        lp.multi_selected_layers.clear()
        if lp.multi_select_mode:
            lp.toggle_multi_select_mode()
    _wait(80)


def _toolbar_buttons(window):
    return [
        window.view_button,
        window.mask_button,
        window.select_strand_button,
        window.attach_button,
        window.move_button,
        window.rotate_button,
        window.toggle_grid_button,
        window.angle_adjust_button,
        window.save_button,
        window.load_button,
        window.save_image_button,
        window.toggle_control_points_button,
        window.toggle_shadow_button,
        window.tabs_button,
        window.layer_state_button,
        window.settings_button,
    ]


def _text_width(widget):
    from PyQt5.QtGui import QFontMetrics

    return QFontMetrics(widget.font()).horizontalAdvance(widget.text())


def _rect_in(widget, ancestor):
    from PyQt5.QtCore import QRect

    return QRect(widget.mapTo(ancestor, widget.rect().topLeft()), widget.size())


def _check(window, mode, target):
    """Measure the laid-out window and return (metrics, failures)."""
    from numbered_layer_button import NumberedLayerButton

    lp = window.layer_panel
    failures = []
    win_w, win_h = window.width(), window.height()
    if (win_w, win_h) != target:
        failures.append(f"window is {win_w}x{win_h}, expected {target[0]}x{target[1]}")

    # Toolbar: every button inside the left column, none overlapping, and
    # none squeezed below its natural width. The buttons have an Expanding
    # policy, so a row that is too narrow never overflows: Qt shrinks the
    # buttons under their sizeHint (label + the stylesheet's padding, which
    # equals the checked border + padding) and the centred label is cut at
    # both ends. Comparing against Qt's own hint therefore catches exactly
    # the clipping a user would see, whatever the platform font.
    left_rect = _rect_in(window.left_widget, window)
    rects = []
    for btn in _toolbar_buttons(window):
        r = _rect_in(btn, window)
        name = btn.text() or "settings"
        if not left_rect.contains(r):
            failures.append(f"toolbar '{name}' extends outside the left column")
        if btn.text():
            shortfall = btn.sizeHint().width() - btn.width()
            if shortfall > 0:
                failures.append(f"toolbar '{name}' squeezed {shortfall}px below its label width")
        rects.append((name, r))
    # Buttons on the same row (a wrapped toolbar has two) must not overlap.
    rects.sort(key=lambda t: (t[1].top(), t[1].left()))
    for (n1, r1), (n2, r2) in zip(rects, rects[1:]):
        if r1.top() == r2.top() and r1.right() >= r2.left():
            failures.append(f"toolbar '{n1}' overlaps '{n2}'")

    # Layer panel: at or above its floor, list column keeps the button
    # width plus gutter, every layer button fully visible, labels fit.
    if lp.width() < lp.minimumWidth():
        failures.append(f"layer panel {lp.width()}px is below its minimum {lp.minimumWidth()}px")
    list_min = lp.list_column_min_width()
    if lp.scroll_area.width() < list_min:
        failures.append(f"layer list column {lp.scroll_area.width()}px < {list_min}px")
    viewport = lp.scroll_area.viewport()
    layer_buttons = [b for b in lp.findChildren(NumberedLayerButton) if b.isVisible()]
    for b in layer_buttons:
        r = _rect_in(b, viewport)
        if r.left() < 0 or r.right() >= viewport.width():
            failures.append(f"layer button '{b.text()}' is clipped horizontally")
    create_group = lp.group_layer_manager.create_group_button
    if create_group.isVisible():
        room = create_group.width() - CREATE_GROUP_LABEL_PADDING
        need = _text_width(create_group)
        if room < need:
            failures.append(f"'Create Group' label needs {need}px, has {room}px")
    for attr in ("draw_names_button", "lock_layers_button", "add_new_strand_button",
                 "delete_strand_button", "deselect_all_button", "delete_all_button"):
        btn = getattr(lp, attr, None)
        if btn is None or not btn.isVisible():
            continue
        room = btn.width() - BOTTOM_LABEL_PADDING
        need = _text_width(btn)
        if room < need:
            failures.append(f"bottom button '{btn.text()}' needs {need}px, has {room}px")
    # The panel sits on the right in LTR and on the left in Hebrew (RTL),
    # so compare rectangles rather than sides.
    panel_rect = _rect_in(lp, window)
    if not window.rect().contains(panel_rect):
        failures.append("layer panel extends past the window's edge")
    if lp.isVisible() and left_rect.intersects(panel_rect):
        failures.append("canvas column overlaps the layer panel")

    metrics = {
        "window": [win_w, win_h],
        "device_pixel_ratio": round(window.devicePixelRatioF(), 3),
        "canvas": [window.canvas.width(), window.canvas.height()],
        "toolbar_spacing": window.toolbar_button_layout.spacing(),
        "toolbar_rows": 2 if getattr(window, "_toolbar_two_rows", False) else 1,
        "layer_panel": lp.width(),
        "layer_panel_min": lp.minimumWidth(),
        "list_column": lp.scroll_area.width(),
        "group_column": lp.right_panel.width(),
        "layer_buttons": [b.text() for b in layer_buttons],
        "mode": mode,
        "lock_mode": bool(getattr(lp, "lock_mode", False)),
        "multi_select_mode": bool(getattr(lp, "multi_select_mode", False)),
    }
    return metrics, failures


def _grab(window, path):
    pix = window.grab()
    pix.save(path, "PNG")
    return pix.width(), pix.height()


def run(scale, out_dir, languages=None, preset_ids=None, modes=None, font_family=None):
    from translations import translations

    os.makedirs(out_dir, exist_ok=True)
    # Keep the app's settings file out of the repository while capturing.
    work = tempfile.mkdtemp(prefix="screen_matrix_")
    os.chdir(work)
    os.environ.setdefault("APPDATA", work)

    app, window = _bootstrap(scale, font_family)
    languages = languages or list(translations.keys())
    modes = modes or list(MODES)
    presets = presets_for_scale(scale)
    if preset_ids:
        presets = [p for p in presets if p[0] in preset_ids]

    # A generous first layout so the sample strands land on the canvas.
    _force_available_size(window, 1600, 900)
    layer_names = _draw_sample_layers(window)

    results = {"scale": scale, "font": font_family or app.font().family(),
               "layers": layer_names, "shots": []}
    for pid, title, pw, ph, _s, chrome in presets:
        lw = int(round(pw / scale))
        lh = int(round(ph / scale)) - chrome
        for lang in languages:
            window.set_language(lang)
            _wait(80)
            _force_available_size(window, lw, lh)
            for mode in modes:
                _enter_mode(window, mode)
                app.processEvents()
                _wait(120)
                metrics, failures = _check(window, mode, (lw, lh))
                png = os.path.join(out_dir, f"{pid}__{lang}__{mode}.png")
                pix_w, pix_h = _grab(window, png)
                _leave_mode(window, mode)
                results["shots"].append({
                    "preset": pid, "title": title,
                    "physical": [pw, ph], "scale": scale, "logical": [lw, lh],
                    "language": lang, "mode": mode,
                    "file": os.path.basename(png), "image": [pix_w, pix_h],
                    "metrics": metrics, "failures": failures,
                })
                status = "OK " if not failures else "FAIL"
                print(f"[{status}] {pid} {lang} {mode}: {'; '.join(failures) or 'ok'}", flush=True)
    results["failed"] = sum(1 for s in results["shots"] if s["failures"])
    json_path = os.path.join(out_dir, f"results_{scale:g}.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)
    print(f"{len(results['shots'])} shots, {results['failed']} failed -> {json_path}", flush=True)
    window._confirm_close_with_dirty_tabs = lambda *a, **k: True
    window.close()
    app.processEvents()
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--languages", default="")
    parser.add_argument("--presets", default="")
    parser.add_argument("--modes", default="")
    parser.add_argument("--platform", default="offscreen",
                        help="QT_QPA_PLATFORM to use (offscreen by default)")
    parser.add_argument("--font", default="",
                        help="UI font family to capture with (default: platform font)")
    args = parser.parse_args(argv)

    # Both must be in the environment before Qt is imported.
    os.environ["QT_SCALE_FACTOR"] = f"{args.scale:g}"
    os.environ.setdefault("QT_QPA_PLATFORM", args.platform)

    split = lambda s: [x for x in s.split(",") if x]  # noqa: E731
    results = run(args.scale, os.path.abspath(args.out), split(args.languages),
                  split(args.presets), split(args.modes), args.font or None)
    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
