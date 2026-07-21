"""
Automation test for the three Hebrew (RTL) layer-panel fixes:

1. Arrow "Adjust" popup — every row shows its Hebrew label on the RIGHT of
   the segmented +/- spin box (the RTL context menu mirrors the rows).
2. Copy badge / paste chips — the ■ end chip (whose spot the copy badge
   reuses) hugs the outer LEFT edge of the layer button, the ▲ start chip
   sits inward, mirroring the English right-edge arrangement.
3. Lock mode — the layer-name text keeps the exact same position when lock
   mode is toggled on, so it never drifts over the paste chips.

Launches the real app in Hebrew, drives it with QTest, and writes proof
PNGs to docs/hebrew_rtl_fixes_feature/.

Run headless (default) or visible:
    python automation_tests/test_hebrew_rtl_fixes.py
    python automation_tests/test_hebrew_rtl_fixes.py --visible
"""
import os
import sys
import argparse
import faulthandler

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

DOCS_DIR = os.path.join(ROOT_DIR, "docs", "hebrew_rtl_fixes_feature")
ARROW_POPUP_PNG = os.path.join(DOCS_DIR, "arrow_adjust_popup_he.png")
LOCK_COMPARE_PNG = os.path.join(DOCS_DIR, "lock_mode_text_compare_he.png")
PANEL_SCENARIO_PNG = os.path.join(DOCS_DIR, "layer_panel_lock_paste_he.png")

FAILURES = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"[automation] {status}: {message}", flush=True)
    if not condition:
        FAILURES.append(message)


def _qt_imports():
    from PyQt5.QtCore import QPoint, Qt, QTimer
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtTest import QTest
    return QPoint, Qt, QTimer, QApplication, QTest


def _draw_new_strand(window, start_xy, end_xy, set_number=1):
    QPoint, Qt, _, _, QTest = _qt_imports()
    canvas = window.canvas
    canvas.start_new_strand_mode(set_number)
    QTest.qWait(300)
    start = QPoint(*start_xy)
    end = QPoint(*end_xy)
    QTest.mousePress(canvas, Qt.LeftButton, pos=start)
    QTest.qWait(200)
    QTest.mouseMove(canvas, pos=end)
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=end)
    QTest.qWait(600)


def _attach_from_point(window, attach_xy, end_xy):
    QPoint, Qt, _, _, QTest = _qt_imports()
    canvas = window.canvas
    window.set_attach_mode()
    QTest.qWait(200)
    QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(*attach_xy))
    QTest.qWait(200)
    QTest.mouseMove(canvas, pos=QPoint(*end_xy))
    QTest.qWait(200)
    QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(*end_xy))
    QTest.qWait(600)


def _strand_by_name(canvas, layer_name):
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == layer_name:
            return strand
    return None


def _button_by_name(layer_panel, layer_name):
    for button in layer_panel.layer_buttons:
        if button.text() == layer_name:
            return button
    return None


def _bootstrap_real_app(language_code="he"):
    """Create QApplication + MainWindow mirroring src/main.py, forcing language."""
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    from main import setup_crash_logging, load_user_settings
    setup_crash_logging()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, False)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    settings = load_user_settings()
    theme = settings[0]

    from main_window import MainWindow
    window = MainWindow()

    if hasattr(window, 'layer_panel') and window.layer_panel:
        window.layer_panel.update_default_colors()

    window.set_language(language_code)
    window.apply_theme(theme)
    return app, window


# ---------------------------------------------------------------------------
# Fix 2: copy badge / paste chip geometry
# ---------------------------------------------------------------------------

def _check_chip_geometry(button):
    """Style B: one 26px sharp-square column — badge and ▲/● stack edge-aligned."""
    start_rect, end_rect = button.paste_chip_rects()
    badge_rect = button.copy_badge_rect()
    lock_rect = button.lock_button_rect()
    width, height = button.width(), button.height()

    print(f"[automation] indicators on '{button.text()}' (w={width} h={height}): "
          f"start={start_rect}, end={end_rect}, badge={badge_rect}, "
          f"lock={lock_rect}", flush=True)

    check(button._is_rtl(), "layer button reports RTL in Hebrew")
    check(start_rect.x() == 15 and end_rect.x() == 15 and badge_rect.x() == 15,
          "RTL: badge and ▲/● stack share one edge-aligned column (x == 15, "
          "clear of the 2px selection border)")
    check(badge_rect.width() == 26 and badge_rect.height() == 26,
          "copy badge is a sharp 26px square (padlock-sized)")
    check(start_rect.width() == 26 and end_rect.width() == 26,
          "paste cells span the full 26px column width")
    check(start_rect.size() == end_rect.size(),
          "the ▲ and ● cells are exactly the same size")
    check(end_rect.y() == start_rect.y() + start_rect.height(),
          "segmented stack: ▲ on top, ● directly below")
    expected_cell = min(26, (height - 8) // 2)
    check(start_rect.height() == expected_cell,
          f"cell height scales with the button (c == {expected_cell})")
    stack = start_rect.united(end_rect)
    check(stack.top() >= 3 and stack.bottom() <= height - 3,
          "the stack fits inside the button with margin at every size")
    check(lock_rect.x() == width - 6 - 26,
          "RTL: padlock sits at the right edge, clear of the selection border")


# ---------------------------------------------------------------------------
# Fix 3: lock mode must not move the layer-name text
# ---------------------------------------------------------------------------

def _has_text_pixels(image, x0, x1):
    """Whether columns x0..x1 contain pixels clearly darker than the button
    background (the anti-aliased text outline)."""
    for y in range(image.height()):
        for x in range(x0, x1):
            color = image.pixelColor(x, y)
            if color.red() + color.green() + color.blue() < 480:
                return True
    return False


def _check_lock_text_stable(layer_panel, button):
    from PyQt5.QtGui import QImage, QPainter
    from PyQt5.QtCore import Qt as QtCore_Qt
    _, _, _, _, QTest = _qt_imports()

    before = button.grab().toImage()

    layer_panel.lock_layers_button.setChecked(True)
    layer_panel.toggle_lock_mode()
    QTest.qWait(300)
    check(layer_panel.lock_mode, "lock mode is active")
    after = button.grab().toImage()

    # Compare only the span that excludes the green strip (left, RTL) and the
    # padlock (right, RTL): with the fix, the text keeps its position and the
    # region is pixel-identical in both modes.
    x0, x1 = 12, button.width() - 33
    check(_has_text_pixels(before, x0, x1) and _has_text_pixels(after, x0, x1),
          "layer-name text found in both snapshots")
    diff_pixels = sum(
        1
        for y in range(min(before.height(), after.height()))
        for x in range(x0, x1)
        if before.pixelColor(x, y) != after.pixelColor(x, y)
    )
    print(f"[automation] differing pixels in text region: {diff_pixels}",
          flush=True)
    check(diff_pixels == 0,
          "layer-name text does not move when lock mode turns on")

    # Side-by-side proof PNG: normal mode on top, lock mode below.
    gap = 6
    combined = QImage(max(before.width(), after.width()),
                      before.height() + gap + after.height(),
                      QImage.Format_ARGB32)
    combined.fill(QtCore_Qt.darkGray)
    painter = QPainter(combined)
    painter.drawImage(0, 0, before)
    painter.drawImage(0, before.height() + gap, after)
    painter.end()
    combined.save(LOCK_COMPARE_PNG)
    print(f"[automation] snapshot saved -> {LOCK_COMPARE_PNG}", flush=True)


# ---------------------------------------------------------------------------
# Fix 2 (visual): badge + chips + lock all visible, names intact
# ---------------------------------------------------------------------------

def _grab_panel_scenario(layer_panel, source_button, target_button):
    from PyQt5.QtCore import Qt as QtCore_Qt, QRect as QtCore_QRect
    _, _, _, _, QTest = _qt_imports()

    layer_panel.multi_select_mode = True
    source_index = layer_panel.layer_buttons.index(source_button)
    copied = layer_panel.copy_strand_data(source_index)
    check(copied, "strand data copied from source layer (badge visible)")

    check(layer_panel.is_strand_data_copy_source(source_button),
          "source layer reports the copy badge")

    # Hover the target so its ▲ / ■ paste chips paint.
    QTest.mouseMove(target_button, target_button.rect().center())
    QTest.qWait(200)
    if not target_button.underMouse():
        target_button.setAttribute(QtCore_Qt.WA_UnderMouse, True)
    for button in layer_panel.layer_buttons:
        button.update()
    QTest.qWait(200)

    # Crop the grab to the layer buttons (the list is bottom-aligned inside a
    # tall scroll area, so a full grab is mostly empty space).
    buttons_rect = None
    for button in layer_panel.layer_buttons:
        rect = QtCore_QRect(button.mapTo(layer_panel.scroll_content,
                                         button.rect().topLeft()),
                            button.rect().size())
        buttons_rect = rect if buttons_rect is None else buttons_rect.united(rect)
    pixmap = layer_panel.scroll_content.grab()
    if buttons_rect is not None:
        pixmap = pixmap.copy(buttons_rect.adjusted(-8, -8, 8, 8))
    pixmap.save(PANEL_SCENARIO_PNG)
    print(f"[automation] snapshot saved -> {PANEL_SCENARIO_PNG}", flush=True)

    target_button.setAttribute(QtCore_Qt.WA_UnderMouse, False)
    layer_panel.clear_strand_data_clipboard()
    layer_panel.multi_select_mode = False


# ---------------------------------------------------------------------------
# Fix 1: arrow "Adjust" popup rows in RTL
# ---------------------------------------------------------------------------

def _check_combo_rtl_alignment(open_menus):
    """Style fix: in Hebrew the texture/shaft combo text must hug the RIGHT
    edge (10-11px gap), mirroring the English flush-left label."""
    from PyQt5.QtWidgets import QComboBox
    combos = []
    for menu in open_menus:
        combos.extend(menu.findChildren(QComboBox))
    check(len(combos) >= 2,
          f"arrow menu has the texture and shaft combos (got {len(combos)})")
    for combo in combos:
        parent = combo.parentWidget()
        image = parent.grab().toImage()
        geo = combo.geometry()
        xs = [x for x in range(geo.left(), geo.right())
              for y in range(geo.top(), geo.bottom())
              if image.pixelColor(x, y).red() > 220
              and image.pixelColor(x, y).green() > 220
              and image.pixelColor(x, y).blue() > 220]
        if not xs:
            check(False, f"combo '{combo.currentText()}' shows no text")
            continue
        right_gap = geo.right() - max(xs)
        print(f"[automation] combo '{combo.currentText()}' "
              f"w={geo.width()} right_gap={right_gap}px", flush=True)
        check(6 <= right_gap <= 14,
              f"combo '{combo.currentText()}' text hugs the right edge "
              f"(gap {right_gap}px, mirrors the English ~10px)")

    # The Arrow Sizes "Adjust" tool button: ▼ zone on the left, text centered
    # in the remaining field — the mirror of English (text left, ▼ right).
    from PyQt5.QtWidgets import QToolButton
    for menu in open_menus:
        for tool_button in menu.findChildren(QToolButton):
            if tool_button.menu() is None:
                continue
            parent = tool_button.parentWidget()
            image = parent.grab().toImage()
            geo = tool_button.geometry()
            xs = [x for x in range(geo.left(), geo.right())
                  for y in range(geo.top(), geo.bottom())
                  if image.pixelColor(x, y).red() > 220
                  and image.pixelColor(x, y).green() > 220
                  and image.pixelColor(x, y).blue() > 220]
            if not xs:
                check(False, "Adjust button shows no text")
                continue
            left_gap = min(xs) - geo.left()
            right_gap = geo.right() - max(xs)
            print(f"[automation] adjust '{tool_button.text()}' w={geo.width()} "
                  f"left_gap={left_gap} right_gap={right_gap}", flush=True)
            check(right_gap < left_gap and 10 <= right_gap <= 24,
                  "Adjust text sits right of center with the ▼ zone on the "
                  "left (mirrors English)")


def _inspect_arrow_popup(app):
    """Runs from a timer while the (blocking) context menu is open."""
    from PyQt5.QtWidgets import (QApplication, QMenu, QToolButton, QLabel,
                                 QSpinBox, QDoubleSpinBox)
    from translations import translations
    _, _, _, _, QTest = _qt_imports()

    adjust_text = translations['he']['adjust']
    sizes_button = None
    open_menus = [w for w in QApplication.topLevelWidgets()
                  if isinstance(w, QMenu) and w.isVisible()]
    _check_combo_rtl_alignment(open_menus)
    for menu in open_menus:
        for tool_button in menu.findChildren(QToolButton):
            if tool_button.text() == adjust_text and tool_button.menu() is not None:
                sizes_button = tool_button
                break
        if sizes_button:
            break

    check(sizes_button is not None, "found the Hebrew 'Adjust' arrow-sizes button")
    if sizes_button is not None:
        sizes_menu = sizes_button.menu()
        sizes_menu.popup(sizes_button.mapToGlobal(
            sizes_button.rect().bottomLeft()))
        QTest.qWait(400)

        spins = [s for s in sizes_menu.findChildren(QSpinBox)
                 + sizes_menu.findChildren(QDoubleSpinBox)]
        labels = sizes_menu.findChildren(QLabel)
        check(len(spins) == 6, f"arrow popup has 6 spin boxes (got {len(spins)})")
        check(len(labels) == 6, f"arrow popup has 6 labels (got {len(labels)})")

        rows_ok = bool(spins) and bool(labels)
        for spin in spins:
            row_label = min(
                labels,
                key=lambda l: abs(l.geometry().center().y()
                                  - spin.geometry().center().y()),
            )
            label_x = row_label.geometry().center().x()
            spin_x = spin.geometry().center().x()
            print(f"[automation] row '{row_label.text()}': "
                  f"label_cx={label_x} spin_cx={spin_x}", flush=True)
            if label_x <= spin_x:
                rows_ok = False
        check(rows_ok, "every arrow-size row shows the Hebrew label RIGHT of "
                       "its spin box")

        pixmap = sizes_menu.grab()
        pixmap.save(ARROW_POPUP_PNG)
        print(f"[automation] snapshot saved -> {ARROW_POPUP_PNG}", flush=True)

        QTest.qWait(150)
        sizes_menu.close()

    # Close the (blocking) context menu(s) so show_context_menu returns.
    for menu in open_menus:
        menu.close()


def _check_arrow_popup(app, window, button, strand):
    QPoint, _, QTimer, _, QTest = _qt_imports()
    # The arrow customization section only exists while the full arrow is shown.
    strand.full_arrow_visible = True
    QTimer.singleShot(900, lambda: _inspect_arrow_popup(app))
    button.show_context_menu(QPoint(10, 10))  # blocks until the timer closes it
    QTest.qWait(300)


# ---------------------------------------------------------------------------

def _run_automation(window, app):
    _, _, _, _, QTest = _qt_imports()
    try:
        os.makedirs(DOCS_DIR, exist_ok=True)
        print("[automation] starting Hebrew RTL fixes flow...", flush=True)

        _draw_new_strand(window, start_xy=(140, 140), end_xy=(360, 140))
        canvas = window.canvas
        strand_11 = _strand_by_name(canvas, "1_1")
        assert strand_11 is not None, "1_1 missing"

        attach_xy = (int(strand_11.end.x()), int(strand_11.end.y()))
        _attach_from_point(window, attach_xy=attach_xy, end_xy=(360, 320))
        assert _strand_by_name(canvas, "1_2") is not None, "1_2 missing"
        print("[automation] strands 1_1 + 1_2 ready", flush=True)

        layer_panel = window.layer_panel
        check(layer_panel.language_code == 'he', "layer panel language is Hebrew")
        button_11 = _button_by_name(layer_panel, "1_1")
        button_12 = _button_by_name(layer_panel, "1_2")
        assert button_11 is not None and button_12 is not None

        print("[automation] --- fix 2: chip / badge geometry ---", flush=True)
        _check_chip_geometry(button_12)

        print("[automation] --- fix 3: lock mode text stability ---", flush=True)
        _check_lock_text_stable(layer_panel, button_11)

        print("[automation] --- fix 2 (visual): lock + copy + paste chips ---",
              flush=True)
        _grab_panel_scenario(layer_panel, button_11, button_12)

        print("[automation] --- fix 1: arrow Adjust popup RTL ---", flush=True)
        _check_arrow_popup(app, window, button_11, strand_11)

        for path in (ARROW_POPUP_PNG, LOCK_COMPARE_PNG, PANEL_SCENARIO_PNG):
            check(os.path.exists(path), f"snapshot exists: {os.path.basename(path)}")

        if FAILURES:
            print(f"[automation] {len(FAILURES)} CHECK(S) FAILED:", flush=True)
            for failure in FAILURES:
                print(f"[automation]   - {failure}", flush=True)
        else:
            print("[automation] ALL CHECKS PASSED", flush=True)
    except Exception as exc:
        FAILURES.append(str(exc))
        print(f"[automation] FAILED: {exc}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        faulthandler.cancel_dump_traceback_later()
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, app.quit)


def test_hebrew_rtl_fixes(visible=False):
    if not visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    else:
        os.environ.pop("QT_QPA_PLATFORM", None)

    app, window = _bootstrap_real_app(language_code="he")
    _, _, QTimer, _, _ = _qt_imports()

    window.show()
    window.showMaximized()
    window.raise_()
    window.activateWindow()
    if hasattr(window, 'set_initial_splitter_sizes'):
        window.set_initial_splitter_sizes()

    QTimer.singleShot(600, lambda: _run_automation(window, app))
    app.exec_()
    os._exit(1 if FAILURES else 0)


if __name__ == "__main__":
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true",
                        help="Show real app window while running the flow")
    args = parser.parse_args()
    test_hebrew_rtl_fixes(visible=args.visible)
