"""Shared drawing helpers for the Copy/Paste Strand Data concept mockups.

These are documentation helpers only — they render PNG mockups with
matplotlib and are not part of the OpenStrandStudio application.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon
from matplotlib.path import Path
import matplotlib.patches as mpatches
import numpy as np

# ---------------------------------------------------------------- palette --
MENU_BG = "#f7f7f9"
MENU_BORDER = "#a9a9b0"
MENU_TEXT = "#1d1d1f"
MENU_DIM = "#8e8e93"
MENU_SEP = "#d4d4d8"
HILITE_BG = "#2f6fd0"
HILITE_TEXT = "#ffffff"
NEW_BADGE = "#e8590c"
CHECK_ON = "#2f6fd0"
CHECK_OFF_BORDER = "#9a9aa0"
CANVAS_BG = "#efefef"
GRID_DOT = "#c8c8c8"

# default strand look from src/strand.py (fill 200,170,230; black stroke)
STRAND_FILL = (200 / 255, 170 / 255, 230 / 255)
STRAND_STROKE = "#000000"
STRAND_FILL2 = (170 / 255, 205 / 255, 160 / 255)

FS = 11  # base font size


# ------------------------------------------------------------ primitives --
def new_fig(w, h, dpi=140):
    fig = plt.figure(figsize=(w, h), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.invert_yaxis()  # y grows downward, like screen coordinates
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def save(fig, path):
    fig.savefig(path, facecolor="white", bbox_inches=None)
    plt.close(fig)
    print(f"wrote {path}")


def rounded_box(ax, x, y, w, h, fc, ec, lw=1.0, r=0.06, z=2):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z,
        mutation_aspect=1,
    )
    ax.add_patch(box)
    return box


def shadow_box(ax, x, y, w, h, r=0.06, z=1):
    rounded_box(ax, x + 0.045, y + 0.055, w, h, "#00000022", "none", r=r, z=z)


def text(ax, x, y, s, size=FS, color=MENU_TEXT, weight="normal",
         ha="left", va="center", style="normal", z=5, family="DejaVu Sans"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
            ha=ha, va=va, fontstyle=style, zorder=z, family=family)


def checkbox(ax, x, y, size, checked, z=5, tri_state=False):
    """Draw a small checkbox centred vertically on y."""
    s = size
    if checked:
        rounded_box(ax, x, y - s / 2, s, s, CHECK_ON, CHECK_ON, r=0.03, z=z)
        ax.plot([x + 0.22 * s, x + 0.42 * s, x + 0.80 * s],
                [y + 0.02 * s, y + 0.25 * s, y - 0.28 * s],
                color="white", lw=1.6, zorder=z + 1, solid_capstyle="round")
    elif tri_state:
        rounded_box(ax, x, y - s / 2, s, s, CHECK_ON, CHECK_ON, r=0.03, z=z)
        ax.plot([x + 0.25 * s, x + 0.75 * s], [y, y],
                color="white", lw=1.8, zorder=z + 1, solid_capstyle="round")
    else:
        rounded_box(ax, x, y - s / 2, s, s, "white", CHECK_OFF_BORDER,
                    lw=1.1, r=0.03, z=z)


def submenu_arrow(ax, x, y, color=MENU_TEXT, s=0.085, z=6):
    ax.add_patch(Polygon([(x, y - s), (x, y + s), (x + 1.4 * s, y)],
                         closed=True, facecolor=color, edgecolor="none",
                         zorder=z))


def color_swatch(ax, x, y, w, h, color, z=6):
    rounded_box(ax, x, y - h / 2, w, h, color, "#666666", lw=0.8, r=0.02, z=z)


# ------------------------------------------------------------- menu block --
class Menu:
    """Vertical menu drawn top-down from (x, y)."""

    ROW = 0.34

    def __init__(self, ax, x, y, w, title=None):
        self.ax, self.x, self.w = ax, x, w
        self.top = y
        self.cy = y + 0.16
        self.rows = []  # deferred so we can size the surrounding box first
        if title:
            self.rows.append(("title", title))

    def item(self, label, dim=False, hilite=False, arrow=False, badge=None,
             check=None, swatch=None, indent=0.0):
        self.rows.append(("item", label, dim, hilite, arrow, badge, check,
                          swatch, indent))

    def sep(self):
        self.rows.append(("sep",))

    def height(self):
        h = 0.16
        for r in self.rows:
            h += 0.16 if r[0] == "sep" else (0.30 if r[0] == "title" else self.ROW)
        return h + 0.12

    def draw(self):
        h = self.height()
        shadow_box(self.ax, self.x, self.top, self.w, h)
        rounded_box(self.ax, self.x, self.top, self.w, h, MENU_BG, MENU_BORDER,
                    lw=1.2, z=2)
        cy = self.cy
        for r in self.rows:
            if r[0] == "sep":
                cy += 0.08
                self.ax.plot([self.x + 0.12, self.x + self.w - 0.12], [cy, cy],
                             color=MENU_SEP, lw=1.0, zorder=4)
                cy += 0.08
            elif r[0] == "title":
                cy += 0.15
                text(self.ax, self.x + 0.16, cy, r[1], size=FS - 1.5,
                     color=MENU_DIM, weight="bold")
                cy += 0.15
            else:
                _, label, dim, hilite, arrow, badge, check, swatch, ind = r
                cy += self.ROW / 2
                tx = self.x + 0.18 + ind
                if hilite:
                    rounded_box(self.ax, self.x + 0.06, cy - self.ROW / 2 + 0.02,
                                self.w - 0.12, self.ROW - 0.04, HILITE_BG,
                                "none", r=0.045, z=3)
                col = HILITE_TEXT if hilite else (MENU_DIM if dim else MENU_TEXT)
                if check is not None:
                    checkbox(self.ax, tx, cy, 0.185, check)
                    tx += 0.30
                text(self.ax, tx, cy, label, color=col,
                     weight="bold" if hilite else "normal")
                if swatch:
                    color_swatch(self.ax, self.x + self.w - 0.52, cy, 0.30,
                                 0.18, swatch)
                if badge:
                    bw = 0.16 * len(badge) * 0.62 + 0.14
                    bx = self.x + self.w - (0.62 if arrow else 0.24) - bw
                    rounded_box(self.ax, bx, cy - 0.115, bw, 0.23, NEW_BADGE,
                                "none", r=0.09, z=4)
                    text(self.ax, bx + bw / 2, cy + 0.004, badge, size=FS - 3.5,
                         color="white", weight="bold", ha="center")
                if arrow:
                    submenu_arrow(self.ax, self.x + self.w - 0.26, cy,
                                  color=HILITE_TEXT if hilite else MENU_TEXT)
                cy += self.ROW / 2
        return self.top + h  # bottom y


# --------------------------------------------------------------- strands --
def bezier_pts(p0, p1, p2, p3, n=120):
    t = np.linspace(0, 1, n)[:, None]
    pts = ((1 - t) ** 3 * np.array(p0) + 3 * (1 - t) ** 2 * t * np.array(p1)
           + 3 * (1 - t) * t ** 2 * np.array(p2) + t ** 3 * np.array(p3))
    return pts


def draw_strand(ax, p0, cp1, cp2, p3, width=16, fill=STRAND_FILL,
                stroke=STRAND_STROKE, z=10, alpha=1.0, dashed=False):
    pts = bezier_pts(p0, cp1, cp2, p3)
    ls = (0, (4, 3)) if dashed else "-"
    ax.plot(pts[:, 0], pts[:, 1], color=stroke, lw=width, zorder=z,
            solid_capstyle="round", alpha=alpha, linestyle=ls)
    ax.plot(pts[:, 0], pts[:, 1], color=fill, lw=width * 0.62, zorder=z + 1,
            solid_capstyle="round", alpha=alpha, linestyle=ls)
    return pts


def point_marker(ax, p, kind, z=20, s=0.11, color="#2f6fd0", label=None,
                 lab_dxy=(0.22, -0.18), lab_color=None, fs=FS - 1):
    x, y = p
    if kind == "square":
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, facecolor="white",
                               edgecolor=color, lw=1.8, zorder=z))
    elif kind == "circle":
        ax.add_patch(Circle((x, y), s, facecolor="white", edgecolor=color,
                            lw=1.8, zorder=z))
    elif kind == "dot":
        ax.add_patch(Circle((x, y), s * 0.75, facecolor=color,
                            edgecolor="white", lw=1.2, zorder=z))
    elif kind == "triangle":
        ax.add_patch(Polygon([(x, y - 1.25 * s), (x - 1.1 * s, y + 0.85 * s),
                              (x + 1.1 * s, y + 0.85 * s)], closed=True,
                             facecolor="white", edgecolor=color, lw=1.8,
                             zorder=z))
    elif kind == "star":
        ang = np.linspace(-np.pi / 2, 1.5 * np.pi, 11)
        rr = np.where(np.arange(11) % 2 == 0, 1.6 * s, 0.7 * s)
        ax.add_patch(Polygon(np.c_[x + rr * np.cos(ang), y + rr * np.sin(ang)],
                             closed=True, facecolor="#ffd43b",
                             edgecolor="#b8860b", lw=1.4, zorder=z))
    if label:
        text(ax, x + lab_dxy[0], y + lab_dxy[1], label, size=fs,
             color=lab_color or color, weight="bold", z=z + 1)


def annotate(ax, txt, xy, xytext, color="#444444", fs=FS - 1, z=30,
             ha="left"):
    ax.annotate(txt, xy=xy, xytext=xytext, fontsize=fs, color=color,
                ha=ha, va="center", zorder=z,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1,
                                shrinkA=2, shrinkB=4))


def canvas_panel(ax, x, y, w, h, title=None):
    rounded_box(ax, x, y, w, h, CANVAS_BG, "#b5b5b5", lw=1.2, r=0.05, z=1)
    xs = np.arange(x + 0.3, x + w - 0.15, 0.42)
    ys = np.arange(y + 0.3, y + h - 0.15, 0.42)
    gx, gy = np.meshgrid(xs, ys)
    ax.scatter(gx, gy, s=1.6, color=GRID_DOT, zorder=1.5)
    if title:
        text(ax, x + w / 2, y - 0.22, title, size=FS + 1, weight="bold",
             ha="center", color="#333333")


def layer_button(ax, x, y, name, w=0.95, h=0.42, selected=False,
                 masked=False, fill="#7e57c2"):
    fc = "#555555" if masked else fill
    rounded_box(ax, x, y, w, h, fc, "#333333" if selected else "#777777",
                lw=2.0 if selected else 1.0, r=0.08, z=3)
    text(ax, x + w / 2, y + h / 2 + 0.01, name, color="white", ha="center",
         weight="bold", size=FS - 1)
