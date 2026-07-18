"""Generate the concept mockup PNGs for the Copy/Paste Strand Data feature.

Usage:  python3 generate_mockups.py [output_dir]

Documentation helper only — not part of the application. Requires
matplotlib + numpy (pip install matplotlib).
"""

import os
import sys
import numpy as np

from mockup_common import (
    new_fig, save, rounded_box, shadow_box, text, checkbox, submenu_arrow,
    color_swatch, Menu, draw_strand, bezier_pts, point_marker, annotate,
    canvas_panel, layer_button,
    MENU_BG, MENU_BORDER, MENU_TEXT, MENU_DIM, MENU_SEP, HILITE_BG,
    HILITE_TEXT, NEW_BADGE, STRAND_FILL, STRAND_FILL2, FS,
)

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "..", "mockups")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

# Pixel-exact UI pieces rendered from the app's real widgets by
# render_ui_qt.py (run that script first).
QT = os.path.join(OUT, "qt")

import matplotlib.pyplot as plt


def place_png(ax, name, x, y, height):
    """Place a Qt-rendered PNG at (x, y) with the given height in inches;
    returns (w, h) in axis units. Adds a soft drop shadow."""
    img = plt.imread(os.path.join(QT, name))
    h_px, w_px = img.shape[0], img.shape[1]
    width = height * w_px / h_px
    from mockup_common import rounded_box
    rounded_box(ax, x + 0.05, y + 0.06, width, height, "#00000022", "none",
                r=0.02, z=3)
    ax.imshow(img, extent=(x, x + width, y + height, y), zorder=4,
              interpolation="lanczos")
    return width, height


ACCENT = "#7c4dbe"

# The app's real layer-panel icons (multi_select_on/off.png live here)
ICONS = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "src", "layer_panel_icons"))


def ms_button(ax, cx, cy, d=0.62, checked=True):
    """The REAL Multi-Layer Select button: a 40x40 circular button
    (border-radius 20, tan when off / dark brown when checked —
    src/layer_panel.py:700-744) with the real multi_select_*.png icon."""
    from matplotlib.patches import Circle
    ax.add_patch(Circle((cx, cy), d / 2,
                        facecolor="#654321" if checked else "#D2B48C",
                        edgecolor="#A0522D", lw=1.8, zorder=15))
    name = "multi_select_on.png" if checked else "multi_select_off.png"
    icon = plt.imread(os.path.join(ICONS, name))
    s = d * 0.66  # same icon_scale the app uses
    ax.imshow(icon, extent=(cx - s / 2, cx + s / 2, cy + s / 2, cy - s / 2),
              zorder=16, interpolation="lanczos")


def msel_border(ax, fx, fy, idx):
    """Multi-selection highlight exactly as the app draws it: a 3px gold
    #FFD700 border around the selected button
    (update_layer_button_multi_select_display, src/layer_panel.py:1887)."""
    rounded_box(ax, fx(14), fy(14 + 92 * idx), fx(318) - fx(14),
                fy(106) - fy(14), "none", "#FFD700", lw=3.2, r=0.04, z=18)


def paste_chip(ax, x, y, w, h, kind):
    """One Option A hover paste chip: ⇤ (from start) or ⇥ (from end)."""
    rounded_box(ax, x, y, w, h, "white", ACCENT, lw=1.5, r=0.05, z=20)
    ym = y + h / 2
    pad = w * 0.22
    if kind == "start":       # arrow into a left bar
        ax.plot([x + pad, x + pad], [ym - h * 0.28, ym + h * 0.28],
                color=ACCENT, lw=2.2, zorder=21)
        ax.annotate("", xy=(x + pad + w * 0.06, ym),
                    xytext=(x + w - pad * 0.6, ym),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.8),
                    zorder=21)
    else:                     # arrow into a right bar
        ax.plot([x + w - pad, x + w - pad], [ym - h * 0.28, ym + h * 0.28],
                color=ACCENT, lw=2.2, zorder=21)
        ax.annotate("", xy=(x + w - pad - w * 0.06, ym),
                    xytext=(x + pad * 0.6, ym),
                    arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.8),
                    zorder=21)


def copy_badge(ax, x, y, s):
    """Option A's copy badge (two overlapping squares) at (x, y), size s."""
    from matplotlib.patches import Rectangle
    rounded_box(ax, x, y, s, s, "white", ACCENT, lw=1.6, r=0.05, z=20)
    q = s * 0.42
    ax.add_patch(Rectangle((x + s * 0.32, y + s * 0.14), q, q,
                           facecolor="white", edgecolor=ACCENT, lw=1.3,
                           zorder=21))
    ax.add_patch(Rectangle((x + s * 0.16, y + s * 0.36), q, q,
                           facecolor="white", edgecolor=ACCENT, lw=1.3,
                           zorder=22))


# ==========================================================================
# 1. Strand anatomy — every property the copy panel can pick up
# ==========================================================================
def img_anatomy():
    fig, ax = new_fig(12.0, 6.4)
    canvas_panel(ax, 0.4, 0.75, 11.2, 5.3,
                 title="Anatomy of a strand — everything “Copy Strand Data” can capture")

    p0, cp1, cpc, cp2, p3 = ((2.2, 4.6), (3.4, 1.6), (5.9, 3.3),
                             (8.6, 5.2), (10.2, 2.2))
    # two chained cubics through the center control point (like the app's
    # cp1 / center / cp2 arrangement)
    draw_strand(ax, p0, cp1, (cpc[0] - 0.9, cpc[1] - 0.35), cpc, width=15)
    draw_strand(ax, cpc, (cpc[0] + 0.9, cpc[1] + 0.35), cp2, p3, width=15)

    # tangent guides to the control points
    for a, b in ((p0, cp1), (p3, cp2)):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#777777", lw=0.9,
                linestyle=(0, (2, 2)), zorder=8)

    point_marker(ax, p0, "circle", color="#1a7f37", s=0.13)
    point_marker(ax, p3, "circle", color="#c0392b", s=0.13)
    point_marker(ax, cp1, "square", color="#2f6fd0")
    point_marker(ax, cp2, "square", color="#2f6fd0")
    point_marker(ax, cpc, "triangle", color="#8e44ad")
    # bias controls: small triangle + circle riding near the curve middle
    bias_t, bias_c = (5.0, 3.55), (6.8, 3.35)
    point_marker(ax, bias_t, "triangle", color="#e67e22", s=0.085)
    point_marker(ax, bias_c, "circle", color="#e67e22", s=0.075)

    annotate(ax, "Start point  (start)\n+ start circle / cap, circle stroke color",
             p0, (0.85, 5.75), ha="left")
    annotate(ax, "End point  (end)\n+ end circle / cap, arrows",
             p3, (9.3, 1.15), ha="left")
    annotate(ax, "Control point — start\n(control_point1)", cp1,
             (2.1, 1.0), ha="left")
    annotate(ax, "Control point — end\n(control_point2)", cp2,
             (8.9, 5.9), ha="left")
    annotate(ax, "Control point — middle\n(control_point_center)", cpc,
             (4.6, 5.5), ha="left")
    annotate(ax, "Bias control points\n(triangle & circle bias)", bias_t,
             (3.6, 2.35), ha="left")
    annotate(ax, "Width / stroke width,\nstrand color, stroke color,\nshadow color",
             (7.6, 4.55), (6.3, 1.35), ha="left")
    save(fig, os.path.join(OUT, "01_strand_anatomy.png"))


# ==========================================================================
# 2. Copy — layer-number-button menu + the toggle dropdown panel
# ==========================================================================
TOGGLES = [
    ("group", "GEOMETRY"),
    ("row", "Start Point", True, "start"),
    ("row", "End Point", True, "end"),
    ("group", "CURVE SHAPE"),
    ("row", "Control Point — Start", True, "control_point1"),
    ("row", "Control Point — Middle", True, "control_point_center"),
    ("row", "Control Point — End", True, "control_point2"),
    ("row", "Bias Control Points", True, "triangle / circle bias"),
    ("row", "Curve Tuning", False, "tension, response…"),
    ("group", "SIZE"),
    ("row", "Width", True, "width"),
    ("row", "Stroke Width", True, "stroke_width"),
    ("group", "COLORS"),
    ("row", "Strand Color", True, "fill"),
    ("row", "Stroke Color", True, "outline"),
    ("row", "Circle Stroke Colors", False, "start / end circles"),
    ("row", "Shadow Color", False, "shadow_color"),
    ("group", "EXTRAS"),
    ("row", "Arrow Settings", False, "visibility, color, texture…"),
    ("row", "Line & Extension Visibility", False, "start / end / dashed"),
    ("row", "End Caps / Circles", False, "has_circles"),
]


def _unused_draw_toggle_panel(ax, x, y, w):
    n_rows = sum(1 for t in TOGGLES if t[0] == "row")
    n_groups = sum(1 for t in TOGGLES if t[0] == "group")
    ROW, GRP = 0.315, 0.30
    h = 0.62 + 0.46 + n_rows * ROW + n_groups * GRP + 0.62
    shadow_box(ax, x, y, w, h)
    rounded_box(ax, x, y, w, h, MENU_BG, MENU_BORDER, lw=1.2, z=2)

    cy = y + 0.34
    text(ax, x + 0.22, cy, "Copy Strand Data", weight="bold", size=FS + 1)
    text(ax, x + w - 0.22, cy, "from  1_2", color=MENU_DIM, ha="right",
         size=FS - 1)
    cy += 0.30
    ax.plot([x + 0.14, x + w - 0.14], [cy, cy], color=MENU_SEP, lw=1, zorder=4)

    n_all = sum(1 for t in TOGGLES if t[0] == "row")
    n_on = sum(1 for t in TOGGLES if t[0] == "row" and t[2])
    cy += 0.28
    checkbox(ax, x + 0.24, cy, 0.20, False, tri_state=True)
    text(ax, x + 0.56, cy, "Select All", weight="bold")
    text(ax, x + w - 0.22, cy, f"{n_on} of {n_all} selected", color=MENU_DIM,
         ha="right", size=FS - 2)
    cy += 0.22
    ax.plot([x + 0.14, x + w - 0.14], [cy, cy], color=MENU_SEP, lw=1, zorder=4)

    n_sel = 0
    for t in TOGGLES:
        if t[0] == "group":
            cy += GRP
            text(ax, x + 0.24, cy - 0.03, t[1], size=FS - 3, color=MENU_DIM,
                 weight="bold")
        else:
            _, label, on, hint = t
            cy += ROW
            checkbox(ax, x + 0.42, cy - 0.06, 0.185, on)
            text(ax, x + 0.72, cy - 0.06, label)
            text(ax, x + w - 0.22, cy - 0.05, hint, color=MENU_DIM,
                 ha="right", size=FS - 3)
            n_sel += on

    cy += 0.30
    bw, bh = 1.9, 0.40
    rounded_box(ax, x + w - bw - 0.22, cy - bh / 2 + 0.08, bw, bh, HILITE_BG,
                "none", r=0.08, z=5)
    text(ax, x + w - bw / 2 - 0.22, cy + 0.08, f"Copy  ({n_sel} selected)",
         color="white", ha="center", weight="bold", size=FS - 0.5)
    text(ax, x + 0.24, cy + 0.08, "toggles are remembered", color=MENU_DIM,
         size=FS - 3)


def img_copy_menu():
    W, H = 15.4, 11.2
    fig, ax = new_fig(W, H)
    text(ax, 0.45, 0.42, "Copying — the multi-select context menu",
         size=FS + 3, weight="bold")
    text(ax, 0.45, 0.80,
         "right-clicking in multi-select mode already shows the small batch menu "
         "— Hide Selected Layers / Shadow Only Selected (show_multi_select_"
         "context_menu,\nsrc/layer_panel.py:1914) — the proposal appends the "
         "Copy / Paste rows to it; the normal menu is untouched.",
         size=FS - 1, color=MENU_DIM)

    # layer panel in multi-select mode; right-click the ticked source layer
    bx, by = 0.45, 2.25
    bw, bh = place_png(ax, "layer_buttons.png", bx, by, 4.4)
    ms_button(ax, bx + 0.34, by - 0.46, checked=True)
    text(ax, bx + 0.78, by - 0.56,
         "the round Multi-Layer Select\nbutton — pressed (mode ON)",
         size=FS - 2, color="#654321", weight="bold")

    def fx(p):
        return bx + p / 332.0 * bw

    def fy(p):
        return by + p / 488.0 * bh

    msel_border(ax, fx, fy, 1)
    cursor(ax, fx(190), fy(138))
    text(ax, bx, by + bh + 0.32,
         "tick + right-click the source layer 1_2\n(gold border = multi-selected)",
         size=FS - 2, color="#5b3f8f", weight="bold")

    # the NEW small menu — opens collapsed; paste dimmed (nothing copied yet)
    col_h, col_w = plt.imread(
        os.path.join(QT, "ms_menu_copy_collapsed.png")).shape[:2]
    exp_h = plt.imread(os.path.join(QT, "ms_menu_copy_expanded.png")).shape[0]
    qw_t = 2.6                       # target width; heights follow px scale
    qx = bx + bw + 1.05
    qw, qh = place_png(ax, "ms_menu_copy_collapsed.png", qx, by,
                       qw_t * col_h / col_w)
    text(ax, qx + qw / 2, by - 0.20, "the batch menu + NEW rows — collapsed",
         size=FS - 1, ha="center", weight="bold", color="#1a7f37")
    ax.annotate("", xy=(qx - 0.10, by + qh * 0.40),
                xytext=(fx(220) + 0.15, fy(140)),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.5))
    ax.annotate("Paste is dimmed —\nnothing copied yet",
                xy=(qx + qw * 0.5, by + qh * 0.99),
                xytext=(qx - 0.25, by + qh + 0.80),
                fontsize=FS - 2, color="#888888", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.0))

    # press ▾ -> the six-essential toggle panel expands inline
    px = qx + qw + 1.7
    pw, ph = place_png(ax, "ms_menu_copy_expanded.png", px, by,
                       (qw_t * col_h / col_w) * exp_h / col_h)
    text(ax, px + pw / 2, by - 0.20, "after pressing ▾ — EXPANDED",
         size=FS - 1, ha="center", weight="bold", color="#1a7f37")
    ax.annotate("press ▾", xy=(px - 0.12, by + qh * 0.35),
                xytext=(qx + qw + 0.18, by + qh * 0.35),
                fontsize=FS - 1, color="#1a7f37", weight="bold", va="bottom",
                arrowprops=dict(arrowstyle="-|>", color="#1a7f37", lw=1.6))

    def callout(frac, s, color="#1a7f37"):
        yy = by + ph * frac
        ax.annotate(s, xy=(px + pw, yy), xytext=(px + pw + 0.28, yy),
                    fontsize=FS - 1, color=color, va="center",
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1))

    # collapsed menu = 4 rows: Hide / Shadow Only (existing) + Copy + Paste
    row_h = col_h / 4.0
    panel_h = exp_h - col_h          # injected toggle panel, capture pixels
    callout(1.0 * row_h / exp_h,
            "the existing batch entries —\nHide Selected Layers /\n"
            "Shadow Only Selected — unchanged", "#444444")
    callout(2.5 * row_h / exp_h, "Copy Strand Data — expanded (▴)")
    callout((2.9 * row_h + panel_h * 0.06) / exp_h,
            "Select All — tri-state master toggle")
    callout((2.9 * row_h + panel_h * 0.52) / exp_h,
            "the six essentials — start / end /\ncontrol points / width /\n"
            "strand color / stroke color")
    callout((2.9 * row_h + panel_h * 0.94) / exp_h,
            "Copy (6) — snapshots & closes")
    callout((exp_h - 0.5 * row_h) / exp_h,
            "Paste — dimmed until Copy is pressed", "#888888")

    # reference: the normal-mode menu stays exactly as it is today
    ny = by + max(bh, ph) + 0.85
    nw, nh = place_png(ax, "current_context_menu.png", 0.45, ny, 2.5)
    text(ax, 0.45 + nw + 0.40, ny + nh * 0.45,
         "normal mode (multi-select OFF): the usual right-click menu,\n"
         "exactly as today — Copy / Paste Strand Data is NOT added here.",
         size=FS - 1, color=MENU_DIM)

    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    save(fig, os.path.join(OUT, "02_copy_menu_toggles.png"))


# ==========================================================================
# 3. Paste — right-click on the target strand
# ==========================================================================
def cursor(ax, x, y, z=40):
    pts = [(x, y), (x, y + 0.42), (x + 0.10, y + 0.33), (x + 0.17, y + 0.48),
           (x + 0.24, y + 0.44), (x + 0.17, y + 0.30), (x + 0.30, y + 0.30)]
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(pts, closed=True, facecolor="white",
                         edgecolor="black", lw=1.2, zorder=z))


def img_paste_menu():
    W, H = 15.4, 8.6
    fig, ax = new_fig(W, H)
    text(ax, 0.45, 0.42,
         "Pasting — tick target layers in multi-select, right-click, paste onto ALL of them",
         size=FS + 3, weight="bold")
    text(ax, 0.45, 0.80,
         "the clipboard holds 1_2's six properties; masked or locked layers in "
         "the selection are simply skipped. The normal menu stays unchanged.",
         size=FS - 1, color=MENU_DIM)

    # layer panel in multi-select mode: source badge + two ticked targets
    bx, by = 0.45, 2.25
    bw, bh = place_png(ax, "layer_buttons.png", bx, by, 4.4)
    ms_button(ax, bx + 0.34, by - 0.46, checked=True)
    text(ax, bx + 0.78, by - 0.56,
         "Multi-Layer Select button\n— pressed (mode ON)",
         size=FS - 2, color="#654321", weight="bold")

    def fx(p):
        return bx + p / 332.0 * bw

    def fy(p):
        return by + p / 488.0 * bh

    copy_badge(ax, fx(278), fy(114), fx(310) - fx(278))   # source 1_2
    msel_border(ax, fx, fy, 2)                            # target 1_3
    msel_border(ax, fx, fy, 3)                            # target 2_1
    text(ax, bx, by + bh + 0.32,
         "source 1_2 (badge) · targets 1_3 + 2_1 multi-selected\n"
         "(gold border) — right-click either of them",
         size=FS - 2, color="#3c6b33", weight="bold")

    # WAY 2 — the Option A hover chips, right on the hovered target button
    cw_ = fx(268) - fx(238)
    ch_ = fy(356) - fy(316)
    paste_chip(ax, fx(234), fy(316), cw_, ch_, "start")
    paste_chip(ax, fx(270), fy(316), cw_, ch_, "end")
    cursor(ax, fx(286), fy(338))
    ax.annotate("WAY 2 — one-click chips (Option A): hover a target →\n"
                "⇤ pastes with Angle from Start, ⇥ with Angle from End;\n"
                "with layers ticked, one chip click pastes onto them all",
                xy=(fx(232), fy(336)), xytext=(bx, by + bh + 1.10),
                fontsize=FS - 2, color=ACCENT, weight="bold", va="top",
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.2))

    # the same small multi-select menu — Paste now active, opens collapsed
    col_h, col_w = plt.imread(
        os.path.join(QT, "ms_menu_paste_collapsed.png")).shape[:2]
    exp_h = plt.imread(os.path.join(QT, "ms_menu_paste_expanded.png")).shape[0]
    qw_t = 2.6
    qx = bx + bw + 1.05
    qw, qh = place_png(ax, "ms_menu_paste_collapsed.png", qx, by,
                       qw_t * col_h / col_w)
    text(ax, qx + qw / 2, by - 0.20, "WAY 1 — the batch menu, Paste active",
         size=FS - 1, ha="center", weight="bold", color="#1a7f37")
    ax.annotate("", xy=(qx - 0.10, by + qh * 0.40),
                xytext=(fx(320), fy(250)),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.5))

    # press ▾ -> clipboard hint + the two anchor choices inline
    px = qx + qw + 1.7
    pw, ph = place_png(ax, "ms_menu_paste_expanded.png", px, by,
                       (qw_t * col_h / col_w) * exp_h / col_h)
    text(ax, px + pw / 2, by - 0.20, "after pressing ▾ — choose & it pastes",
         size=FS - 1, ha="center", weight="bold", color="#1a7f37")
    ax.annotate("press ▾", xy=(px - 0.12, by + qh * 0.75),
                xytext=(qx + qw + 0.18, by + qh * 0.75),
                fontsize=FS - 1, color="#1a7f37", weight="bold", va="bottom",
                arrowprops=dict(arrowstyle="-|>", color="#1a7f37", lw=1.6))

    body_h = exp_h - col_h            # hint + two anchor rows, capture pixels
    ax.annotate("what's in the clipboard",
                xy=(px + pw, by + ph * (col_h + body_h * 0.15) / exp_h),
                xytext=(px + pw + 0.28,
                        by + ph * (col_h + body_h * 0.15) / exp_h),
                fontsize=FS - 2, color="#444444", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#444444", lw=1.1))
    ax.annotate("click a choice → pastes onto ALL\nticked layers (1_3 & 2_1) in one\n"
                "undo step; the menu closes",
                xy=(px + pw, by + ph * (col_h + body_h * 0.65) / exp_h),
                xytext=(px + pw + 0.28,
                        by + ph * (col_h + body_h * 0.65) / exp_h),
                fontsize=FS - 2, color="#1a7f37", weight="bold", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#1a7f37", lw=1.1))
    text(ax, qx, by + max(qh, ph) + 0.55,
         "the clipboard is NOT consumed — tick other layers and paste again and "
         "again;\nClear ✕ on the source badge (Option A indicators) ends the copy.",
         size=FS - 2, color="#1a7f37")

    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    save(fig, os.path.join(OUT, "03_paste_context_menu.png"))


# ==========================================================================
# 3b. Chosen indicator design — Option A: badge + hover paste icons
# ==========================================================================
def img_indicators():
    """Option A drawn over the real layer-button strip: a copy badge on the
    source (top-right corner, clear of the left-side padlock), and two
    hover-only one-click paste chips on eligible targets."""
    W, H = 14.6, 8.0
    fig, ax = new_fig(W, H)
    text(ax, 0.45, 0.42,
         "Layer-panel indicators — CHOSEN: Option A (corner badge + hover paste icons)",
         size=FS + 3, weight="bold")
    text(ax, 0.45, 0.80,
         "drawn over the real layer buttons — the lock-mode padlock lives on the "
         "LEFT side, so the badge (top-right) never clashes with it.",
         size=FS - 1, color=MENU_DIM)

    bx, by = 0.7, 1.55
    bw, bh = place_png(ax, "layer_buttons.png", bx, by, 4.6)
    text(ax, bx + bw / 2, by - 0.14, "Layer Panel", size=FS - 2,
         color=MENU_DIM, ha="center", weight="bold")

    # px->axes helpers for the 332x488 strip (buttons: y = 20 + 92*i, h=80)
    def fx(p):
        return bx + p / 332.0 * bw

    def fy(p):
        return by + p / 488.0 * bh

    ACC = "#7c4dbe"

    # --- copy badge on the source button 1_2 (index 1), top-right corner ---
    bx0, by0, bs = fx(278), fy(114), fx(310) - fx(278)
    rounded_box(ax, bx0, by0, bs, bs, "white", ACC, lw=1.6, r=0.05, z=20)
    # classic "copy" glyph: two overlapping little squares
    from matplotlib.patches import Rectangle
    s = bs * 0.42
    ax.add_patch(Rectangle((bx0 + bs * 0.32, by0 + bs * 0.14), s, s,
                           facecolor="white", edgecolor=ACC, lw=1.3, zorder=21))
    ax.add_patch(Rectangle((bx0 + bs * 0.16, by0 + bs * 0.36), s, s,
                           facecolor="white", edgecolor=ACC, lw=1.3, zorder=22))

    # its popup: click the badge -> clear
    pxp, pyp, pw_, ph_ = fx(332) + 0.45, fy(96), 3.45, 0.62
    shadow_box(ax, pxp, pyp, pw_, ph_, r=0.08)
    rounded_box(ax, pxp, pyp, pw_, ph_, "white", MENU_BORDER, lw=1.1, r=0.08,
                z=20)
    text(ax, pxp + 0.18, pyp + ph_ / 2 + 0.045, "6 properties from 1_2",
         size=FS - 1, z=21)
    text(ax, pxp + pw_ - 0.18, pyp + ph_ / 2 + 0.045, "Clear ✕",
         size=FS - 1, color="#c0392b", weight="bold", ha="right", z=21)
    ax.annotate("", xy=(pxp - 0.04, pyp + ph_ / 2),
                xytext=(fx(312) + 0.04, by0 + bs / 2),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.2))

    # --- hover paste chips on the target button 2_1 (index 3) ---
    def chip(px_left, kind):
        cx, cy = fx(px_left), fy(316)
        cw_, ch_ = fx(px_left + 30) - fx(px_left), fy(356) - fy(316)
        rounded_box(ax, cx, cy, cw_, ch_, "white", ACC, lw=1.5, r=0.05, z=20)
        ym = cy + ch_ / 2
        pad = cw_ * 0.22
        if kind == "start":       # ⇤  arrow into a left bar
            ax.plot([cx + pad, cx + pad], [ym - ch_ * 0.28, ym + ch_ * 0.28],
                    color=ACC, lw=2.2, zorder=21)
            ax.annotate("", xy=(cx + pad + cw_ * 0.06, ym),
                        xytext=(cx + cw_ - pad * 0.6, ym),
                        arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8),
                        zorder=21)
        else:                     # ⇥  arrow into a right bar
            ax.plot([cx + cw_ - pad, cx + cw_ - pad],
                    [ym - ch_ * 0.28, ym + ch_ * 0.28],
                    color=ACC, lw=2.2, zorder=21)
            ax.annotate("", xy=(cx + cw_ - pad - cw_ * 0.06, ym),
                        xytext=(cx + pad * 0.6, ym),
                        arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.8),
                        zorder=21)
        return cx, cy, cw_, ch_

    c1 = chip(238, "start")
    c2 = chip(274, "end")
    cursor(ax, c2[0] + c2[2] * 0.55, c2[1] + c2[3] * 0.55)

    # --- callouts ---
    ax.annotate("source 1_2 — the copy badge, top-right corner\n"
                "(the padlock toggle is on the LEFT, no clash);\n"
                "click it → the popup — Clear ✕ ENDS the copy",
                xy=(bx0 + bs / 2, by0 - 0.04), xytext=(fx(332) + 0.45, fy(30)),
                fontsize=FS - 1, color=ACC, va="center",
                arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.2))
    ax.annotate("hover an eligible layer → two one-click paste chips:\n"
                "⇤ Angle from Start Point   ·   ⇥ Angle from End Point\n"
                "(hover-only; never on masked or locked layers)",
                xy=(c1[0] - 0.05, c1[1] + c1[3] / 2),
                xytext=(fx(332) + 0.45, fy(336)),
                fontsize=FS - 1, color="#1a7f37", va="center",
                arrowprops=dict(arrowstyle="-|>", color="#1a7f37", lw=1.2))
    ms_button(ax, 0.95, by + bh + 0.62, d=0.5, checked=True)
    text(ax, 1.35, by + bh + 0.42,
         "Badge and chips exist only while the clipboard is non-empty. The "
         "Copy / Paste rows live in the multi-select batch menu\n(the round "
         "Multi-Layer Select button turns the mode on); the chips give "
         "one-click pasting without opening it, and act on the\nwhole "
         "selection when several layers are ticked. Clear ✕ ends the copy.",
         size=FS - 1, color=MENU_DIM)
    save(fig, os.path.join(OUT, "06_panel_indicators.png"))


# ==========================================================================
# 4. Paste geometry semantics — anchor at start vs anchor at end
# ==========================================================================
SRC_LOCAL = dict(p0=np.array([0.0, 0.0]), cp1=np.array([0.9, -1.1]),
                 cp2=np.array([2.1, 0.9]), p3=np.array([3.1, -0.5]))


def rot(v, deg):
    a = np.radians(deg)
    m = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    return m @ v


def paste_panel(ax, ox, oy, anchor_end):
    """One canvas panel: dashed target before, solid result after paste."""
    canvas_panel(ax, ox, oy, 5.6, 4.6,
                 title=("Angle from End Point" if anchor_end
                        else "Angle from Start Point"))
    # small source reference in the corner
    s0 = np.array([ox + 0.55, oy + 0.75])
    for k, scale in (("ghost", 0.55),):
        p = {n: s0 + SRC_LOCAL[n] * scale for n in SRC_LOCAL}
        draw_strand(ax, p["p0"], p["cp1"], p["cp2"], p["p3"], width=7,
                    fill="#bbbbbb", stroke="#888888")
    text(ax, s0[0], oy + 0.42, "copied shape (source 1_2)", size=FS - 3,
         color="#666666")

    # target baseline: T0 -> T1
    T0 = np.array([ox + 1.15, oy + 3.75])
    T1 = np.array([ox + 4.9, oy + 2.2])
    d = T1 - T0
    theta_t = np.degrees(np.arctan2(d[1], d[0]))

    # target before paste (single dashed green line, its own mild curve)
    before = bezier_pts(T0, T0 + rot(np.array([1.2, 0.25]), theta_t),
                        T0 + rot(np.array([2.4, -0.25]), theta_t), T1)
    ax.plot(before[:, 0], before[:, 1], color="#4c8a41", lw=4.5,
            linestyle=(0, (4, 3)), zorder=6, alpha=0.8,
            solid_capstyle="round")

    # source local geometry, measured from the chosen anchor
    src_anchor = SRC_LOCAL["p3"] if anchor_end else SRC_LOCAL["p0"]
    src_base = ((SRC_LOCAL["p0"] - SRC_LOCAL["p3"]) if anchor_end
                else (SRC_LOCAL["p3"] - SRC_LOCAL["p0"]))
    theta_s = np.degrees(np.arctan2(src_base[1], src_base[0]))

    tgt_anchor = T1 if anchor_end else T0
    tgt_base = (T0 - T1) if anchor_end else (T1 - T0)
    theta_ta = np.degrees(np.arctan2(tgt_base[1], tgt_base[0]))
    dtheta = theta_ta - theta_s

    res = {n: tgt_anchor + rot(SRC_LOCAL[n] - src_anchor, dtheta)
           for n in SRC_LOCAL}
    draw_strand(ax, res["p0"], res["cp1"], res["cp2"], res["p3"], width=12,
                z=12)

    point_marker(ax, tgt_anchor, "star", s=0.10)
    if anchor_end:
        text(ax, tgt_anchor[0] - 0.18, tgt_anchor[1] - 0.32,
             "anchor stays put", size=FS - 2, color="#8a6d00",
             weight="bold", ha="right")
    else:
        text(ax, tgt_anchor[0] + 0.10, tgt_anchor[1] + 0.42,
             "anchor stays put", size=FS - 2, color="#8a6d00",
             weight="bold")
    moved = res["p0"] if anchor_end else res["p3"]
    free_before = T0 if anchor_end else T1
    ax.annotate("", xy=moved, xytext=free_before,
                arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.2,
                                linestyle=(0, (3, 2))))
    if anchor_end:
        text(ax, moved[0] - 0.55, moved[1] + 0.62,
             "free end follows\nthe copied shape", size=FS - 3,
             color="#c0392b", ha="center")
    else:
        text(ax, moved[0] - 0.15, moved[1] - 0.62,
             "free end follows\nthe copied shape", size=FS - 3,
             color="#c0392b", ha="center")


def img_paste_geometry():
    fig, ax = new_fig(12.4, 6.1)
    text(ax, 0.45, 0.40,
         "What pasting does — copied geometry is re-expressed relative to the chosen anchor",
         size=FS + 3, weight="bold")
    text(ax, 0.45, 0.78,
         "dashed = target before      solid purple = target after paste      "
         "the copied offsets are rotated by the target's own baseline angle at the anchor",
         size=FS - 1, color=MENU_DIM)
    paste_panel(ax, 0.45, 1.35, anchor_end=False)
    paste_panel(ax, 6.5, 1.35, anchor_end=True)
    save(fig, os.path.join(OUT, "04_paste_anchor_semantics.png"))


# ==========================================================================
# 5. End-to-end workflow storyboard
# ==========================================================================
def img_workflow():
    fig, ax = new_fig(12.4, 3.4)
    steps = [
        ("1", "Press the round Multi-\nLayer Select button —\nmulti-select mode ON"),
        ("2", "Right-click the source\nlayer → Copy Strand Data ▾\ntoggle & press  Copy (6)"),
        ("3", "Tick the target layer(s)\n— any number of them\n(or use the hover ⇤ / ⇥)"),
        ("4", "Right-click → Paste ▾ →\nAngle from Start / End —\npastes onto ALL ticked"),
        ("✓", "One undo step; clipboard\nstays — Clear ✕ on the\nsource badge ends the copy"),
    ]
    x, w, h, y = 0.45, 2.14, 1.9, 0.85
    for i, (num, s) in enumerate(steps):
        bx = x + i * (w + 0.28)
        shadow_box(ax, bx, y, w, h, r=0.09)
        rounded_box(ax, bx, y, w, h, MENU_BG if num != "✓" else "#e7f2e4",
                    MENU_BORDER, lw=1.1, r=0.09, z=2)
        from matplotlib.patches import Circle
        ax.add_patch(Circle((bx + 0.30, y + 0.32), 0.155,
                            facecolor=HILITE_BG if num != "✓" else "#3c8c46",
                            edgecolor="none", zorder=4))
        text(ax, bx + 0.30, y + 0.335, num, color="white", weight="bold",
             ha="center", size=FS)
        text(ax, bx + 0.16, y + 1.18, s, size=FS - 2.2, va="center")
        if i < len(steps) - 1:
            ax.annotate("", xy=(bx + w + 0.26, y + h / 2),
                        xytext=(bx + w + 0.04, y + h / 2),
                        arrowprops=dict(arrowstyle="-|>", color="#666666",
                                        lw=1.4))
    text(ax, 0.45, 0.45, "Copy → Paste workflow", size=FS + 3,
         weight="bold")
    save(fig, os.path.join(OUT, "05_workflow.png"))


if __name__ == "__main__":
    img_anatomy()
    img_copy_menu()
    img_paste_menu()
    img_indicators()
    img_paste_geometry()
    img_workflow()
    print("done ->", OUT)
