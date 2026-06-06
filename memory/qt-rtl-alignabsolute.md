---
name: qt-rtl-alignabsolute
description: Qt gotcha — under RTL layout direction, AlignRight flips to visual left; need AlignAbsolute
metadata:
  type: reference
---

In PyQt5, when a widget (e.g. QLabel) has `setLayoutDirection(Qt.RightToLeft)`, a plain `Qt.AlignRight` is resolved *relative to* the reading direction and flips to the **visual left**. To pin alignment to the real right edge under RTL, use `Qt.AlignRight | Qt.AlignAbsolute`.

Hit this in `src/tab_bar_widget.py` (TabChip): Hebrew tab titles hugged the left edge of their label despite AlignRight, because the label was RTL for correct BiDi shaping. Fix: add `Qt.AlignAbsolute` in the RTL branch.

Quick way to verify alignment fixes: render the widget to a QPixmap, draw red lines at `label.geometry()` left/right edges, scale up, and inspect the PNG. Related: [[rtl-ltr-settings-alignment]] pattern in settings_dialog.py.
