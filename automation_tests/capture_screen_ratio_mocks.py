"""Capture full-program mock screenshots at real Mac / desktop screen sizes.

The window is forced to the available geometry of each simulated screen
(menu bar + dock/taskbar reserved), using the live MainWindow layout so
the images show how the toolbar and layer panel actually behave.

Run:
    python automation_tests/capture_screen_ratio_mocks.py
"""
import os
import sys
import math

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

OUT_DIR = os.path.join(ROOT_DIR, "docs", "screen_ratio_layout_feature", "screenshots")

# Simulated screens. Width/height are logical pixels of the whole display.
# chrome_top / chrome_bottom mimic macOS menu bar + dock, or a Windows taskbar.
# The app is laid out in the remaining "available geometry".
SCREENS = [
    {
        "id": "01_macbook13_16x10_small",
        "title": 'MacBook 13" (smallest scaled)',
        "ratio": "16:10",
        "width": 1280,
        "height": 800,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "02_macbook_air13_intel_16x10",
        "title": 'MacBook Air 13" Intel',
        "ratio": "16:10",
        "width": 1440,
        "height": 900,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "03_macbook_air13_m2_more_space",
        "title": 'MacBook Air 13" M2  (More Space)',
        "ratio": "3:2",
        "width": 1280,
        "height": 832,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "04_macbook_air13_m2_default",
        "title": 'MacBook Air 13" M2  (default)',
        "ratio": "3:2",
        "width": 1470,
        "height": 956,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "05_macbook_pro14_default",
        "title": 'MacBook Pro 14"  (default)',
        "ratio": "3:2",
        "width": 1512,
        "height": 982,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "06_macbook_pro16_default",
        "title": 'MacBook Pro 16"  (default)',
        "ratio": "3:2",
        "width": 1728,
        "height": 1117,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "07_imac24_16x9",
        "title": 'iMac 24"  (default scaled)',
        "ratio": "16:9",
        "width": 2240,
        "height": 1260,
        "chrome_top": 25,
        "chrome_bottom": 70,
        "family": "Mac",
    },
    {
        "id": "08_external_1080p_16x9",
        "title": "External display 1080p",
        "ratio": "16:9",
        "width": 1920,
        "height": 1080,
        "chrome_top": 0,
        "chrome_bottom": 40,
        "family": "PC",
    },
    {
        "id": "09_external_1440p_16x9",
        "title": "External display 1440p",
        "ratio": "16:9",
        "width": 2560,
        "height": 1440,
        "chrome_top": 0,
        "chrome_bottom": 40,
        "family": "PC",
    },
    {
        "id": "10_ultrawide_21x9",
        "title": "Ultrawide 21:9",
        "ratio": "21:9",
        "width": 2560,
        "height": 1080,
        "chrome_top": 0,
        "chrome_bottom": 40,
        "family": "PC",
    },
]

CAPTION_H = 42
FOOTER_H = 36
LAYER_PANEL_TARGET_MIN = 350


def _bootstrap():
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
    if hasattr(window, "layer_panel") and window.layer_panel:
        window.layer_panel.update_default_colors()
    window.set_language("en")
    window.apply_theme(theme)
    return app, window


def _wait(ms):
    from PyQt5.QtTest import QTest
    QTest.qWait(ms)


def _force_available_size(window, width, height):
    """Size the live window to a simulated availableGeometry, ignoring the
    window-level minimum so small Mac screens can actually be represented.
    Child widget minimums (canvas 700, layer panel 350) stay in place."""
    from PyQt5.QtCore import Qt

    window.setWindowState(Qt.WindowNoState)
    window.setMinimumSize(0, 0)
    window.setMaximumSize(16777215, 16777215)
    window.resize(width, height)
    window.setFixedSize(width, height)
    from PyQt5.QtWidgets import QApplication
    QApplication.processEvents()
    if hasattr(window, "set_initial_splitter_sizes"):
        window.set_initial_splitter_sizes()
    QApplication.processEvents()
    _wait(180)
    QApplication.processEvents()


def _draw_sample_strands(window):
    from PyQt5.QtCore import QPoint, Qt
    from PyQt5.QtTest import QTest

    canvas = window.canvas
    cw = max(canvas.width(), 400)
    ch = max(canvas.height(), 400)

    def drag(x0, y0, x1, y1):
        canvas.start_new_strand_mode(1)
        QTest.qWait(200)
        QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(x0, y0))
        QTest.qWait(120)
        QTest.mouseMove(canvas, pos=QPoint(x1, y1))
        QTest.qWait(120)
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(x1, y1))
        QTest.qWait(350)

    drag(int(cw * 0.18), int(ch * 0.28), int(cw * 0.55), int(ch * 0.32))
    window.set_attach_mode()
    QTest.qWait(150)
    s11 = None
    for strand in canvas.strands:
        if getattr(strand, "layer_name", None) == "1_1":
            s11 = strand
            break
    if s11 is not None:
        ax, ay = int(s11.end.x()), int(s11.end.y())
        QTest.mousePress(canvas, Qt.LeftButton, pos=QPoint(ax, ay))
        QTest.qWait(120)
        QTest.mouseMove(canvas, pos=QPoint(int(cw * 0.58), int(ch * 0.62)))
        QTest.qWait(120)
        QTest.mouseRelease(canvas, Qt.LeftButton, pos=QPoint(int(cw * 0.58), int(ch * 0.62)))
        QTest.qWait(350)


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


def _measure(window):
    from PyQt5.QtCore import QRect

    left = window.left_widget
    panel = window.layer_panel
    target_min = panel.minimumWidth()
    left_w = left.width()
    panel_w = panel.width()
    win_w = window.width()
    win_h = window.height()

    clipped = []
    left_rect = QRect(left.mapTo(window, left.rect().topLeft()), left.size())
    for btn in _toolbar_buttons(window):
        top_left = btn.mapTo(window, btn.rect().topLeft())
        btn_rect = QRect(top_left, btn.size())
        visible = left_rect.intersected(btn_rect)
        if visible.width() < btn_rect.width() - 1 or visible.height() < btn_rect.height() - 1:
            clipped.append(btn.text() or btn.objectName() or "settings")
        elif btn_rect.right() > left_rect.right() - 1:
            clipped.append(btn.text() or btn.objectName() or "settings")

    # Buttons narrower than their label needs: the toolbar buttons expand to
    # fill the row, so they never overflow it geometrically — instead they
    # shrink and the centered label gets cut at both ends.
    squeezed = []
    for btn in _toolbar_buttons(window):
        if not btn.text():
            continue
        shortfall = btn.sizeHint().width() - btn.width()
        if shortfall > 0:
            squeezed.append((btn.text(), shortfall))

    return {
        "window": (win_w, win_h),
        "left": left_w,
        "panel": panel_w,
        "canvas": (window.canvas.width(), window.canvas.height()),
        "clipped": clipped,
        "squeezed": squeezed,
        "target_min": target_min,
        "group_panel": panel.right_panel.width() if hasattr(panel, "right_panel") else 0,
        "panel_over_min": panel_w - target_min,
    }


def _grab_window(window):
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import Qt

    size = window.size()
    pix = QPixmap(size)
    pix.fill(Qt.white)
    window.render(pix)
    return pix


def _compose_screen(spec, app_pix, metrics):
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush
    from PyQt5.QtCore import Qt, QRect, QRectF

    screen_w, screen_h = spec["width"], spec["height"]
    top, bottom = spec["chrome_top"], spec["chrome_bottom"]
    out_w = screen_w
    out_h = CAPTION_H + screen_h + FOOTER_H
    out = QPixmap(out_w, out_h)
    out.fill(QColor("#1c1c1e"))
    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)

    # Caption
    painter.fillRect(0, 0, out_w, CAPTION_H, QColor("#111113"))
    painter.setPen(QColor("#f5f5f7"))
    font = QFont("Segoe UI", 11)
    font.setBold(True)
    painter.setFont(font)
    caption = f'{spec["title"]}   ·   {spec["ratio"]}   ·   {screen_w}×{screen_h} px'
    painter.drawText(QRect(16, 0, out_w - 32, CAPTION_H), Qt.AlignVCenter | Qt.AlignLeft, caption)
    font.setBold(False)
    painter.setFont(QFont("Segoe UI", 10))
    painter.setPen(QColor("#a1a1a6"))
    family = spec["family"]
    painter.drawText(
        QRect(16, 0, out_w - 32, CAPTION_H),
        Qt.AlignVCenter | Qt.AlignRight,
        family,
    )

    screen_y = CAPTION_H

    # Desktop background
    painter.fillRect(0, screen_y, screen_w, screen_h, QColor("#3a3a3c"))

    # Menu bar (Mac) or nothing (PC)
    if top > 0:
        painter.fillRect(0, screen_y, screen_w, top, QColor("#e8e8ed"))
        painter.setPen(QColor("#1d1d1f"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(
            QRect(12, screen_y, screen_w - 24, top),
            Qt.AlignVCenter | Qt.AlignLeft,
            "OpenStrand Studio        File     Edit     View     Window     Help",
        )

    # Dock / taskbar
    if bottom > 0:
        dock_y = screen_y + screen_h - bottom
        color = QColor("#d8d8de") if spec["family"] == "Mac" else QColor("#1a1a1a")
        painter.fillRect(0, dock_y, screen_w, bottom, color)
        painter.setPen(QColor("#3a3a3c") if spec["family"] == "Mac" else QColor("#9a9a9a"))
        painter.setFont(QFont("Segoe UI", 8))
        label = "Dock" if spec["family"] == "Mac" else "Taskbar"
        painter.drawText(
            QRect(0, dock_y, screen_w, bottom),
            Qt.AlignCenter,
            label,
        )

    # App content into available geometry
    avail_x = 0
    avail_y = screen_y + top
    avail_w = screen_w
    avail_h = screen_h - top - bottom
    scaled = app_pix.scaled(avail_w, avail_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    painter.drawPixmap(avail_x, avail_y, scaled)

    # Thin window border
    painter.setPen(QPen(QColor("#000000"), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(avail_x, avail_y, avail_w - 1, avail_h - 1)

    # Footer metrics
    footer_y = CAPTION_H + screen_h
    painter.fillRect(0, footer_y, out_w, FOOTER_H, QColor("#111113"))
    clipped = metrics["clipped"]
    panel_w = metrics["panel"]
    left_w = metrics["left"]
    got_w, got_h = metrics["window"]
    target_min = metrics.get("target_min", LAYER_PANEL_TARGET_MIN)
    group_w = metrics.get("group_panel", 0)
    squeezed = metrics.get("squeezed", [])
    warning = bool(clipped) or bool(squeezed) or panel_w > target_min + 40
    painter.setPen(QColor("#ff453a") if warning else QColor("#30d158"))
    font = QFont("Segoe UI", 10)
    font.setBold(True)
    painter.setFont(font)
    status = "BUTTONS CLIPPED" if clipped else (
        "LABELS CUT" if squeezed else (
            "LAYER PANEL NOT MINIMIZED" if panel_w > target_min + 40 else "OK"
        )
    )
    clip_txt = ""
    if clipped:
        clip_txt = "  |  hidden: " + ", ".join(clipped[:6])
        if len(clipped) > 6:
            clip_txt += "…"
    elif squeezed:
        clip_txt = "  |  cut: " + ", ".join(f"{lbl} -{sh}px" for lbl, sh in squeezed[:5])
        if len(squeezed) > 5:
            clip_txt += "…"
    compact_txt = "  ·  compact" if target_min < LAYER_PANEL_TARGET_MIN else ""
    metrics_line = (
        f"app {got_w}×{got_h}   ·   canvas pane {left_w}px   ·   "
        f"layer panel {panel_w}px (target min {target_min}, group {group_w}px)"
        f"{compact_txt}   ·   {status}{clip_txt}"
    )
    painter.drawText(QRect(16, footer_y, out_w - 32, FOOTER_H), Qt.AlignVCenter | Qt.AlignLeft, metrics_line)

    painter.end()
    return out, warning


def _contact_sheet(paths):
    from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
    from PyQt5.QtCore import Qt, QRect

    thumbs = []
    thumb_w = 560
    for path in paths:
        src = QPixmap(path)
        if src.isNull():
            continue
        scaled = src.scaledToWidth(thumb_w, Qt.SmoothTransformation)
        thumbs.append(scaled)
    if not thumbs:
        return None

    cols = 2
    rows = math.ceil(len(thumbs) / cols)
    pad = 16
    header = 56
    cell_h = max(t.height() for t in thumbs)
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = header + rows * (cell_h + pad) + pad
    sheet = QPixmap(sheet_w, sheet_h)
    sheet.fill(QColor("#0f0f12"))
    painter = QPainter(sheet)
    painter.setPen(QColor("#f5f5f7"))
    font = QFont("Segoe UI", 14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(
        QRect(pad, 0, sheet_w - 2 * pad, header),
        Qt.AlignVCenter | Qt.AlignLeft,
        "OpenStrand Studio  ·  full-window layout at real screen ratios",
    )
    for i, thumb in enumerate(thumbs):
        r, c = divmod(i, cols)
        x = pad + c * (thumb_w + pad)
        y = header + r * (cell_h + pad)
        painter.fillRect(x, y, thumb_w, cell_h, QColor("#1c1c1e"))
        painter.drawPixmap(x, y, thumb)
    painter.end()
    return sheet


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    app, window = _bootstrap()

    # Skip MainWindow.showEvent maximize / full-screen geometry.
    from PyQt5.QtCore import Qt
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()

    # Draw sample content at a comfortable size first.
    _force_available_size(window, 1600, 900)
    _draw_sample_strands(window)
    window.canvas.deselect_all_strands()
    app.processEvents()

    written = []
    problems = []
    for spec in SCREENS:
        avail_w = spec["width"]
        avail_h = spec["height"] - spec["chrome_top"] - spec["chrome_bottom"]
        print(f"[capture] {spec['id']}: available {avail_w}x{avail_h}  ({spec['ratio']})", flush=True)
        window.setFixedSize(16777215, 16777215)
        window.setMaximumSize(16777215, 16777215)
        _force_available_size(window, avail_w, avail_h)
        metrics = _measure(window)
        print(
            f"         left={metrics['left']}  panel={metrics['panel']}  "
            f"canvas={metrics['canvas']}  clipped={metrics['clipped']}",
            flush=True,
        )
        app_pix = _grab_window(window)
        composed, warning = _compose_screen(spec, app_pix, metrics)
        path = os.path.join(OUT_DIR, spec["id"] + ".png")
        composed.save(path, "PNG")
        written.append(path)
        if warning:
            problems.append(spec["id"])
        print(f"         wrote {path}", flush=True)

    sheet = _contact_sheet(written)
    if sheet is not None:
        sheet_path = os.path.join(OUT_DIR, "00_contact_sheet.png")
        sheet.save(sheet_path, "PNG")
        print(f"[capture] contact sheet {sheet_path}", flush=True)

    print("[capture] problems:", problems if problems else "none", flush=True)
    window.close()
    app.quit()
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
