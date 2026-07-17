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


def draw_toggle_panel(ax, x, y, w):
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
    fig, ax = new_fig(12.4, 10.4)
    text(ax, 0.45, 0.42, "Copying — right-click the numbered layer button",
         size=FS + 3, weight="bold")

    # layer panel strip
    rounded_box(ax, 0.45, 0.85, 1.5, 9.1, "#e6e6ea", "#b5b5b5", lw=1.1, z=1)
    text(ax, 1.2, 1.15, "Layer Panel", size=FS - 2, color=MENU_DIM,
         ha="center", weight="bold")
    names = [("1_1", "#7e57c2", False, False), ("1_2", "#7e57c2", True, False),
             ("1_3", "#7e57c2", False, False), ("2_1", "#66a05b", False, False),
             ("1_2_2_1", "#555555", False, True)]
    for i, (nm, col, sel, masked) in enumerate(names):
        layer_button(ax, 0.72, 1.45 + i * 0.62, nm, selected=sel,
                     masked=masked, fill=col)

    # context menu of button 1_2 (existing items + new Copy entry)
    m = Menu(ax, 2.35, 1.55, 3.35)
    m.item("Hide Layer")
    m.item("Shadow Only")
    m.item("Hide Shadow")
    m.item("Edit Shadows")
    m.sep()
    m.item("Change Color", swatch="#c8aae6")
    m.item("Change Stroke Color", swatch="#000000")
    m.item("Change Width")
    m.sep()
    m.item("Line / Arrow options …", dim=True)
    m.sep()
    m.item("Copy Strand Data", hilite=True, arrow=True, badge="NEW")
    m.draw()

    # connector from menu row to the flyout panel
    ax.annotate("", xy=(6.45, 5.30), xytext=(5.72, 5.30),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.3))

    draw_toggle_panel(ax, 6.5, 0.95, 5.35)
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
    fig, ax = new_fig(12.4, 7.0)
    text(ax, 0.45, 0.42,
         "Pasting — right-click another strand (strand or attached strand, not masked)",
         size=FS + 3, weight="bold")

    canvas_panel(ax, 0.45, 0.95, 7.1, 5.6)

    # source strand (copied) — purple
    draw_strand(ax, (1.1, 5.5), (2.0, 3.4), (3.4, 5.6), (4.3, 3.6), width=14)
    text(ax, 1.05, 5.95, "1_2  — data copied ✓", size=FS - 1,
         color="#5b3f8f", weight="bold")

    # target strand — green, straight-ish
    tgt = draw_strand(ax, (2.1, 2.0), (3.2, 1.7), (4.6, 1.9), (6.3, 2.5),
                      width=14, fill=STRAND_FILL2)
    text(ax, 1.85, 1.5, "2_1  — paste target", size=FS - 1,
         color="#3c6b33", weight="bold")
    cursor(ax, 4.55, 2.05)

    # context menu on the target strand
    m = Menu(ax, 5.1, 2.6, 3.2, title="strand 2_1")
    m.item("Paste Copied Data", hilite=True, arrow=True, badge="NEW")
    m.sep()
    m.item("Clipboard: 12 properties from 1_2", dim=True)
    m.draw()

    # submenu: anchor choice
    m2 = Menu(ax, 8.5, 2.95, 3.4)
    m2.item("Angle from Start Point", hilite=True)
    m2.item("Angle from End Point")
    m2.sep()
    m2.item("Geometry re-anchored at the", dim=True)
    m2.item("chosen point, rotated to the", dim=True)
    m2.item("target's own angle there", dim=True)
    m2.draw()
    ax.annotate("", xy=(8.45, 3.15), xytext=(8.05, 3.02),
                arrowprops=dict(arrowstyle="-|>", color="#666666", lw=1.3))

    # masked strands: option disabled
    m3 = Menu(ax, 8.5, 5.35, 3.4, title="masked layer 1_2_2_1")
    m3.item("Paste Copied Data  (unavailable)", dim=True)
    m3.draw()
    text(ax, 8.5, 6.55, "Masked layers never offer the paste entry.",
         size=FS - 2, color=MENU_DIM)
    save(fig, os.path.join(OUT, "03_paste_context_menu.png"))


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
        ("1", "Right-click the numbered\nlayer button of the\nsource strand"),
        ("2", "Toggle the properties to\ncopy (or Select All),\npress  Copy"),
        ("3", "Right-click the target\nstrand — strand or\nattached, never masked"),
        ("4", "Paste Copied Data ▸\nAngle from Start Point /\nAngle from End Point"),
        ("✓", "Selected data applied,\nre-anchored & rotated;\none undo step"),
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
    img_paste_geometry()
    img_workflow()
    print("done ->", OUT)
