"""Render pixel-exact UI pieces for the Copy/Paste Strand Data concept doc.

This script drives the REAL OpenStrandStudio widgets offscreen:
- `NumberedLayerButton.show_context_menu` builds the actual context menu
  (same code path the app runs), which we screenshot as-is and again with the
  proposed "Copy Strand Data" entry + options panel injected.
- The proposed paste menus are built with the app's own `HoverLabel` class and
  the exact stylesheet from `show_context_menu`.
- Layer-panel buttons are real `NumberedLayerButton` instances.

Documentation helper only — it imports the app read-only and changes nothing.

Usage:  QT_QPA_PLATFORM=offscreen python3 render_ui_qt.py [output_dir]
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")  # 2x pixels for crisp doc images

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "..", "src"))
sys.path.insert(0, SRC)

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "mockups", "qt")
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QMenu, QWidgetAction, QFrame,
)
from PyQt5.QtCore import Qt, QPoint, QPointF
from PyQt5.QtGui import QColor

app = QApplication(sys.argv[:1])

from numbered_layer_button import NumberedLayerButton, HoverLabel
from strand import Strand
from masked_strand import MaskedStrand
from translations import translations

_ = translations["en"]
THEME = "default"  # get_parent_theme() fallback -> light colors


# The exact stylesheet show_context_menu builds for the light theme
# (src/numbered_layer_button.py:243-281)
def menu_base_style():
    style = """
        QMenu {{
            background-color: {bg};
            color: {fg};
            font-size: 8pt;
        }}
        QMenu::item {{
            background-color: transparent;
            color: {fg};
        }}
        QMenu::item:selected, QMenu::item:hover {{
            background-color: {sel_bg};
            color: {sel_fg};
        }}
        QMenu::item:selected QWidget,
        QMenu::item:hover QWidget {{
             background-color: {sel_bg};
        }}
        QMenu::item:selected QLabel,
        QMenu::item:hover QLabel {{
             color: {sel_fg};
             background-color: transparent;
        }}
    """.format(bg="#F0F0F0", fg="#000000", sel_bg="#333333", sel_fg="#ffffff")
    style += "QMenu::item { padding:3px 30px 3px 3px; min-height: 35px; }"
    return style


class LayerPanel(QWidget):
    """Minimal stand-in so show_context_menu finds what it looks up
    (multi_select_mode, layer_buttons, canvas.strands, language_code)."""

    def __init__(self):
        super().__init__()
        self.multi_select_mode = False
        self.layer_buttons = []
        self.language_code = "en"

        class _Canvas:
            strands = []

        self.canvas = _Canvas()

    # no-op slots the menu wires up
    def toggle_layer_visibility(self, i): pass
    def toggle_layer_shadow_only(self, i): pass
    def toggle_layer_hide_shadow(self, i): pass
    def on_edit_mask_click(self, m, i): pass
    def reset_mask(self, i): pass


def grab(widget, name):
    widget.show()
    app.processEvents()
    widget.adjustSize()
    app.processEvents()
    pm = widget.grab()
    path = os.path.join(OUT, name)
    pm.save(path)
    widget.hide()
    print(f"wrote {path}  ({pm.width()}x{pm.height()})")


def capture_context_menu(strand, inject=None):
    """Run the REAL show_context_menu and screenshot the QMenu it builds."""
    panel = LayerPanel()
    btn = NumberedLayerButton(strand.layer_name, 1, QColor("purple"), parent=panel)
    panel.layer_buttons.append(btn)
    panel.canvas.strands.append(strand)

    captured = []
    real_exec = QMenu.exec_
    QMenu.exec_ = lambda self, *a, **k: (captured.append(self), None)[1]
    try:
        btn.show_context_menu(QPoint(5, 5))
    finally:
        QMenu.exec_ = real_exec
    menu = captured[0]
    if inject:
        inject(menu)
    return menu, btn


def rehost_menu(menu, btn):
    """Re-host the QMenu's rows in a plain container.

    The offscreen platform's tiny virtual screen makes QMenu reflow into
    multiple columns, so a straight menu.grab() is useless. Every row of this
    menu is a QWidgetAction carrying the app's own widgets (HoverLabel or
    label+button rows), so stacking those exact widgets in a menu-styled frame
    reproduces the app's menu one-to-one; only the outer border and separator
    lines are redrawn (matching the Fusion menu look).
    """
    # Same dynamic width the app computes (calculate_menu_width, min 150/cap 350)
    texts = []
    for action in menu.actions():
        w = action.defaultWidget() if isinstance(action, QWidgetAction) else None
        if w is not None and hasattr(w, "text"):
            texts.append(w.text())
        elif w is not None and w.layout() is not None:
            for i in range(w.layout().count()):
                child = w.layout().itemAt(i).widget()
                if child and hasattr(child, "text"):
                    texts.append(child.text())
        elif action.text():
            texts.append(action.text())
    width = btn.calculate_menu_width(texts) + 30  # + QMenu::item right pad

    frame = QFrame()
    frame.setObjectName("menuFrame")
    frame.setStyleSheet(
        "#menuFrame { background-color: #F0F0F0; border: 1px solid #ABABAB; }")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(1, 3, 1, 3)
    outer.setSpacing(0)
    for action in menu.actions():
        if action.isSeparator():
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet(
                "background-color: #C6C6C6; border: none; margin: 0px 4px;")
            outer.addSpacing(2)
            outer.addWidget(line)
            outer.addSpacing(2)
        elif isinstance(action, QWidgetAction) and action.defaultWidget():
            w = action.defaultWidget()
            w.setParent(None)  # take it out of the QWidgetAction's control
            outer.addWidget(w)
            w.setVisible(True)  # QWidgetAction keeps it hidden outside a menu
    frame.setFixedWidth(max(width, frame.sizeHint().width()))
    frame.adjustSize()
    frame.setFixedHeight(frame.sizeHint().height())
    return frame


def make_strand(layer_name="1_2"):
    s = Strand(QPointF(0, 0), QPointF(120, 40), 46,
               set_number=1, layer_name=layer_name)
    return s


# ----------------------------------------------------------------------
# The proposed "Copy Strand Data" options panel, built exactly like the
# existing Arrow Customization block (src/numbered_layer_button.py:617-769):
# QWidget + QVBoxLayout(10,5,10,5, spacing 5), label left / control right,
# labels styled "color:#000000; padding:5px;", panel bg #F0F0F0 radius 5px.
# ----------------------------------------------------------------------
# v1 keeps the panel to the six essentials; the rest is a possible
# "Advanced…" follow-up (concept doc section 7).
COPY_ROWS = [
    ("row", "Start Point", True),
    ("row", "End Point", True),
    ("row", "Control Points", True),
    ("row", "Width", True),
    ("row", "Strand Color", True),
    ("row", "Stroke Color", True),
]


def build_copy_panel():
    w = QWidget()
    v = QVBoxLayout()
    v.setContentsMargins(10, 5, 10, 5)
    v.setSpacing(5)

    n_on = sum(1 for r in COPY_ROWS if r[0] == "row" and r[2])
    n_all = sum(1 for r in COPY_ROWS if r[0] == "row")

    # Select All master row (tri-state, like the group shadow editor toggles)
    sel_row = QHBoxLayout()
    sel_label = QLabel(_["select_all"])
    sel_label.setStyleSheet("color: #000000; padding: 5px; font-weight: bold;")
    sel_count = QLabel(f"{n_on}/{n_all}")
    sel_count.setStyleSheet("color: #808080; padding: 5px;")
    sel_cb = QCheckBox()
    sel_cb.setTristate(True)
    sel_cb.setCheckState(Qt.Checked if n_on == n_all else Qt.PartiallyChecked)
    sel_row.addWidget(sel_label)
    sel_row.addStretch()
    sel_row.addWidget(sel_count)
    sel_row.addWidget(sel_cb)
    v.addLayout(sel_row)

    for kind, label, *state in COPY_ROWS:
        if kind == "header":
            head = QLabel(label)
            head.setStyleSheet(
                "color: #808080; padding: 5px 5px 0px 5px; font-weight: bold;")
            v.addWidget(head)
        else:
            h = QHBoxLayout()
            lab = QLabel(label)
            lab.setStyleSheet("color: #000000; padding: 5px;")
            cb = QCheckBox()
            cb.setChecked(state[0])
            h.addWidget(lab)
            h.addStretch()
            h.addWidget(cb)
            v.addLayout(h)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    copy_btn = QPushButton(f"Copy ({n_on})")
    copy_btn.setStyleSheet(
        "QPushButton { background-color: #333333; color: white;"
        " padding: 5px 14px; border: none; border-radius: 3px; }")
    btn_row.addWidget(copy_btn)
    v.addLayout(btn_row)

    w.setLayout(v)
    w.setStyleSheet("background-color: #F0F0F0; border-radius: 5px;")
    return w


def inject_copy_entry(menu, expanded=True):
    menu.addSeparator()
    arrow = "▴" if expanded else "▾"  # ▴ expanded / ▾ collapsed
    label = HoverLabel(f"Copy Strand Data  {arrow}", menu, THEME)
    label.setMinimumHeight(35)
    label.hover_style()  # show it highlighted, as under the cursor
    act = QWidgetAction(menu)
    act.setDefaultWidget(label)
    menu.addAction(act)
    if expanded:
        panel_action = QWidgetAction(menu)
        panel_action.setDefaultWidget(build_copy_panel())
        menu.addAction(panel_action)


def inject_copy_entry_collapsed(menu):
    inject_copy_entry(menu, expanded=False)


def inject_paste_entry(menu, expanded=True):
    """The proposed Paste row — appended to the target layer's normal menu.

    A dropdown like the copy row: collapsed it is a single row; expanded it
    shows the dimmed clipboard hint plus the two anchor choices inline.
    Clicking a choice applies the paste and closes the menu.
    """
    menu.addSeparator()
    arrow = "▴" if expanded else "▾"
    label = HoverLabel(f"Paste Copied Data  {arrow}", menu, THEME)
    label.setMinimumHeight(35)
    label.hover_style()  # show it highlighted, as under the cursor
    act = QWidgetAction(menu)
    act.setDefaultWidget(label)
    menu.addAction(act)
    if expanded:
        hint = HoverLabel("6 properties from 1_2", menu, THEME)
        hint.setStyleSheet(
            "background-color: #F0F0F0; color: #909090;"
            " padding: 5px 25px 5px 15px;")
        hint_act = QWidgetAction(menu)
        hint_act.setDefaultWidget(hint)
        menu.addAction(hint_act)
        for choice in ("Angle from Start Point", "Angle from End Point"):
            lab = HoverLabel("      " + choice, menu, THEME)
            lab.setMinimumHeight(35)
            cact = QWidgetAction(menu)
            cact.setDefaultWidget(lab)
            menu.addAction(cact)


def inject_paste_entry_collapsed(menu):
    inject_paste_entry(menu, expanded=False)


def build_ms_menu(state):
    """The multi-select context menu with the proposed rows appended.

    The app ALREADY shows this small batch menu on right-click in
    multi-select mode — Hide Selected Layers + Shadow Only Selected
    (show_multi_select_context_menu, src/layer_panel.py:1914). The
    proposal appends two dropdown rows after those existing entries:
    Copy Strand Data (dropdown) and Paste Copied Data (dropdown).

    state: 'copy_collapsed' | 'copy_expanded' (clipboard empty, paste dimmed)
           'paste_collapsed' | 'paste_expanded' (clipboard holds 1_2's data)

    Built directly as a menu-styled frame (same look rehost_menu produces) —
    a real QMenu this tall reflows into columns on the tiny offscreen screen.
    """
    frame = QFrame()
    frame.setObjectName("msMenu")
    frame.setStyleSheet(
        "#msMenu { background-color: #F0F0F0; border: 1px solid #ABABAB; }")
    v = QVBoxLayout(frame)
    v.setContentsMargins(1, 3, 1, 3)
    v.setSpacing(0)

    def add_row(text_, hover=False, dim=False, indent=False):
        lab = HoverLabel(text_, frame, THEME)
        lab.setMinimumHeight(35)
        if hover:
            lab.hover_style()
        if dim:
            pad_left = 15 if indent else 5
            lab.setStyleSheet(
                "background-color: #F0F0F0; color: #909090;"
                f" padding: 5px 25px 5px {pad_left}px;")
        v.addWidget(lab)
        return lab

    def add_sep():
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(
            "background-color: #C6C6C6; border: none; margin: 0px 4px;")
        v.addSpacing(2)
        v.addWidget(line)
        v.addSpacing(2)

    # the REAL existing batch entries (show_multi_select_context_menu)
    add_row(_["hide_selected_layers"])
    add_sep()
    add_row(_["enable_shadow_only_selected"])
    add_sep()

    copying = state.startswith("copy")
    add_row("Copy Strand Data  " + ("▴" if state == "copy_expanded" else "▾"),
            hover=copying)
    if state == "copy_expanded":
        v.addWidget(build_copy_panel())
    add_sep()
    if copying:
        add_row("Paste Copied Data", dim=True)   # nothing copied yet
    else:
        add_row("Paste Copied Data  "
                + ("▴" if state == "paste_expanded" else "▾"), hover=True)
        if state == "paste_expanded":
            add_row("6 properties from 1_2", dim=True, indent=True)
            add_row("      Angle from Start Point")
            add_row("      Angle from End Point")

    # same dynamic width the app computes for its menus
    wpanel = LayerPanel()
    wbtn = NumberedLayerButton("1_2", 1, QColor("purple"), parent=wpanel)
    frame.setFixedWidth(wbtn.calculate_menu_width(
        [_["hide_selected_layers"], _["enable_shadow_only_selected"],
         "Copy Strand Data  ▾", "Paste Copied Data  ▾",
         "      Angle from Start Point"]) + 30)
    frame.adjustSize()
    frame.setFixedHeight(frame.sizeHint().height())
    return frame


def hover_label_menu(rows, hover_index=None):
    """A QMenu of HoverLabel entries with the app's exact stylesheet."""
    menu = QMenu()
    menu.setStyleSheet(menu_base_style())
    for i, (text_, dim) in enumerate(rows):
        if text_ is None:
            menu.addSeparator()
            continue
        lab = HoverLabel(text_, menu, THEME)
        lab.setMinimumHeight(35)
        if i == hover_index:
            lab.hover_style()
        if dim:
            lab.setStyleSheet(
                "background-color: #F0F0F0; color: #909090;"
                " padding: 5px 25px 5px 5px;")
        act = QWidgetAction(menu)
        act.setDefaultWidget(lab)
        menu.addAction(act)
    return menu


def layer_button_strip():
    """A column of real NumberedLayerButton widgets."""
    wrap = QWidget()
    wrap.setStyleSheet("background-color: #E8E8E8;")
    v = QVBoxLayout(wrap)
    v.setContentsMargins(10, 10, 10, 10)
    v.setSpacing(6)
    purple = QColor(200, 170, 230, 255)
    for name, color, checked in [
        ("1_1", purple, False),
        ("1_2", purple, True),
        ("1_3", purple, False),
        ("2_1", QColor(150, 200, 255, 255), False),
        ("1_2_2_1", purple, False),
    ]:
        b = NumberedLayerButton(name, 1, color, parent=wrap)
        b.setChecked(checked)
        v.addWidget(b)
    return wrap


def main():
    # 1) The current normal-mode context menu — stays completely UNCHANGED
    menu_now, btn_now = capture_context_menu(make_strand("1_2"))
    grab(rehost_menu(menu_now, btn_now), "current_context_menu.png")

    # 2) The real masked-layer menu (masks are skipped by copy/paste)
    s1, s2 = make_strand("1_2"), make_strand("2_1")
    s2.set_number = 2
    masked = MaskedStrand(s1, s2)
    menu_masked, btn_masked = capture_context_menu(masked)
    grab(rehost_menu(menu_masked, btn_masked), "masked_context_menu.png")

    # 3) The proposed MULTI-SELECT context menu (today: no menu at all there).
    # These are small enough to grab as real shown QMenus — the QWidgetAction
    # widgets only get realized when the menu is actually shown.
    for state in ("copy_collapsed", "copy_expanded",
                  "paste_collapsed", "paste_expanded"):
        grab(build_ms_menu(state), f"ms_menu_{state}.png")

    # 4) Real layer-panel buttons
    grab(layer_button_strip(), "layer_buttons.png")


if __name__ == "__main__":
    main()
