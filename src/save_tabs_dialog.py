"""The dialog Save opens when several tabs are open: which of them to save.

Every tab is listed with a checkbox, all ticked to begin with; the row at the
top ticks or clears them all. The ticked tabs go into one file (one tab alone
is saved as an ordinary single-tab project).

It looks like the app's other dialogs - the Create Mask Grid dialog's
background, bordered list, blue checkboxes with the painted white tick, and
bold buttons - and mirrors for Hebrew the way they do.

Use ``ask_which_tabs``: it shows the dialog, returns the answer and frees the
dialog. Nothing keeps a closed dialog alive.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QStyle, QStyleOptionButton,
                             QVBoxLayout, QWidget)

from checkbox_style import apply_large_indicator
from shrinkable_dialog import allow_shrinking, cap_to_screen, relax, scroll_area
from translations import translations

INDICATOR_SIZE = 20

# The checkbox colours of MaskGridDialog._style_mask_checkbox, per theme.
_CHECKBOX = {
    'dark': dict(text='#FFFFFF', border='#666666', bg='#2A2A2A',
                 hover_border='#888888', hover_bg='#454545',
                 on_bg='#4A6FA5', on_border='#6A9FD5',
                 on_hover_bg='#5A7FB5', on_hover_border='#7AAFF5'),
    'light': dict(text='#000000', border='#AAAAAA', bg='#FFFFFF',
                  hover_border='#888888', hover_bg='#F8F8F8',
                  on_bg='#A0C0E0', on_border='#7090C0',
                  on_hover_bg='#B0D0F0', on_hover_border='#8AA0D0'),
}

# The rest follows MaskGridDialog._apply_theme: dialog, bordered body, buttons.
_DIALOG = {
    'dark': """
        QDialog { background-color: #2C2C2C; color: white; }
        QLabel { color: white; background: transparent; }
        QLabel#saveTabsDetail { color: #B0B0B0; }
        QLabel#saveTabsTag { color: #D0D0D0; background-color: #2C2C2C;
                             border: 1px solid #555555; border-radius: 3px; padding: 1px 6px; }
        QFrame#saveTabsList { background-color: #3D3D3D; border: 1px solid #555555; }
        QWidget#saveTabsAllRow { background-color: #2C2C2C; border-bottom: 1px solid #555555; }
        QWidget#saveTabsRows { background-color: #3D3D3D; }
        QWidget#saveTabsRow { background-color: #3D3D3D; }
        QWidget#saveTabsRow[alternate="true"] { background-color: #383838; }
        QPushButton { background-color: #252525; color: white; border: 2px solid #000000;
                      padding: 6px 12px; border-radius: 4px; font-weight: bold; }
        QPushButton:hover { background-color: #353535; border: 2px solid #4A6FA5; }
        QPushButton:pressed { background-color: #1A1A1A; }
        QPushButton:disabled { color: #777777; border: 2px solid #1A1A1A; }
    """,
    'light': """
        QDialog { background-color: #F5F5F5; color: black; }
        QLabel { color: black; background: transparent; }
        QLabel#saveTabsDetail { color: #666666; }
        QLabel#saveTabsTag { color: #444444; background-color: #E0E0E0;
                             border: 1px solid #CCCCCC; border-radius: 3px; padding: 1px 6px; }
        QFrame#saveTabsList { background-color: white; border: 1px solid #CCCCCC; }
        QWidget#saveTabsAllRow { background-color: #E0E0E0; border-bottom: 1px solid #CCCCCC; }
        QWidget#saveTabsRows { background-color: white; }
        QWidget#saveTabsRow { background-color: white; }
        QWidget#saveTabsRow[alternate="true"] { background-color: #FAFAFA; }
        QPushButton { background-color: #FFFFFF; color: black; border: 2px solid #CCCCCC;
                      padding: 6px 12px; border-radius: 4px; font-weight: bold; }
        QPushButton:hover { background-color: #E8E8E8; border: 2px solid #A0C0E0; }
        QPushButton:pressed { background-color: #D0D0D0; }
        QPushButton:disabled { color: #AAAAAA; border: 2px solid #DDDDDD; }
    """,
}


def _checkbox_stylesheet(theme):
    c = _CHECKBOX[theme]
    size = INDICATOR_SIZE
    return f"""
        QCheckBox {{ color: {c['text']}; spacing: 8px; background-color: transparent; }}
        QCheckBox::indicator {{
            width: {size}px; height: {size}px; min-width: {size}px; min-height: {size}px;
            border: 2px solid {c['border']}; border-radius: 4px; background-color: {c['bg']};
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {c['hover_border']}; background-color: {c['hover_bg']};
        }}
        QCheckBox::indicator:checked, QCheckBox::indicator:indeterminate {{
            background-color: {c['on_bg']}; border: 2px solid {c['on_border']};
        }}
        QCheckBox::indicator:checked:hover, QCheckBox::indicator:indeterminate:hover {{
            background-color: {c['on_hover_bg']}; border: 2px solid {c['on_hover_border']};
        }}
    """


class TickCheckBox(QCheckBox):
    """The app's blue checkbox: a white tick painted over the indicator (the
    path and pen of MaskGridDialog._setup_custom_checkmark), and a white dash
    while only some of what it stands for is ticked."""

    def __init__(self, text='', theme='light', parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(_checkbox_stylesheet(theme))
        apply_large_indicator(self, INDICATOR_SIZE)
        self.setMinimumHeight(INDICATOR_SIZE + 6)

    def nextCheckState(self):
        # A click on a part-ticked box ticks everything; it never leaves the
        # box part-ticked, which only the rows below can make it.
        self.setCheckState(Qt.Unchecked if self.checkState() == Qt.Checked else Qt.Checked)

    def paintEvent(self, event):
        super().paintEvent(event)
        state = self.checkState()
        if state == Qt.Unchecked:
            return
        option = QStyleOptionButton()
        self.initStyleOption(option)
        rect = self.style().subElementRect(QStyle.SE_CheckBoxIndicator, option, self)
        left, top, width, height = rect.left(), rect.top(), rect.width(), rect.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255), max(1.6, height * 0.16),
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QPainterPath()
        if state == Qt.Checked:
            path.moveTo(left + width * 0.25, top + height * 0.55)
            path.lineTo(left + width * 0.42, top + height * 0.72)
            path.lineTo(left + width * 0.78, top + height * 0.28)
        else:
            path.moveTo(left + width * 0.28, top + height * 0.5)
            path.lineTo(left + width * 0.72, top + height * 0.5)
        painter.drawPath(path)
        painter.end()


class _TabRow(QWidget):
    """One tab in the list. A click anywhere on the row ticks its checkbox."""

    def __init__(self, checkbox, parent=None):
        super().__init__(parent)
        self.checkbox = checkbox
        self.setObjectName('saveTabsRow')
        self.setAttribute(Qt.WA_StyledBackground, True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.checkbox.toggle()
        event.accept()


class SaveTabsDialog(QDialog):
    """Lists the open tabs with a checkbox each.

    ``tabs`` is a list of dicts, in tab-bar order: ``id``, ``title``, and
    optionally ``layers`` (a count, or None when unknown), ``dirty`` and
    ``active``. ``selected_ids()`` is the answer."""

    def __init__(self, tabs, language_code='en', theme='default', parent=None):
        super().__init__(parent)
        self._ = translations.get(language_code, translations['en'])
        self._tab_ids = [tab['id'] for tab in tabs]
        theme = 'dark' if theme == 'dark' else 'light'
        _ = self._

        self.setWindowTitle(_['save_tabs_title'])
        self.setModal(True)
        # Strip the Windows context-help button so only the close button remains
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        rtl = language_code == 'he'
        if rtl:
            self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(_DIALOG[theme])

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        info_label = QLabel(_['save_tabs_info'])
        info_label.setWordWrap(True)
        relax(info_label)
        main_layout.addWidget(info_label)

        # The bordered body: the "All tabs" row pinned on top, the tabs scrolling under it
        body = QFrame()
        body.setObjectName('saveTabsList')
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(1, 1, 1, 1)
        body_layout.setSpacing(0)

        all_row = QWidget()
        all_row.setObjectName('saveTabsAllRow')
        all_row.setAttribute(Qt.WA_StyledBackground, True)
        all_layout = QHBoxLayout(all_row)
        all_layout.setContentsMargins(10, 8, 10, 8)
        self.all_checkbox = TickCheckBox(_['all_tabs'], theme)
        self.all_checkbox.setTristate(True)
        bold = self.all_checkbox.font()
        bold.setBold(True)
        self.all_checkbox.setFont(bold)
        self.count_label = QLabel()
        self.count_label.setObjectName('saveTabsDetail')
        all_layout.addWidget(self.all_checkbox)
        all_layout.addStretch()
        all_layout.addWidget(self.count_label)
        body_layout.addWidget(all_row)

        rows = QWidget()
        rows.setObjectName('saveTabsRows')
        rows.setAttribute(Qt.WA_StyledBackground, True)
        rows_layout = QVBoxLayout(rows)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(0)
        self.checkboxes = []
        for index, tab in enumerate(tabs):
            checkbox = TickCheckBox('', theme)
            checkbox.setChecked(True)
            row = _TabRow(checkbox)
            row.setProperty('alternate', index % 2 == 1)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 6, 10, 6)
            row_layout.setSpacing(8)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(0)
            title_label = QLabel(tab['title'])
            title_label.setTextFormat(Qt.PlainText)
            if rtl:
                # A file name is Latin text, which a label starts from the left
                # whatever the layout direction: pin it to the right edge, in
                # line with the Hebrew details under it (see TabChip's label).
                title_label.setAlignment(Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter)
            relax(title_label)
            text_layout.addWidget(title_label)
            details = []
            if tab.get('layers') is not None:
                details.append(_['save_tabs_layers'].format(tab['layers']))
            if tab.get('dirty'):
                details.append(_['save_tabs_unsaved'])
            if details:
                detail_label = QLabel('  •  '.join(details))
                detail_label.setObjectName('saveTabsDetail')
                small = detail_label.font()
                small.setPointSizeF(small.pointSizeF() * 0.9)
                detail_label.setFont(small)
                text_layout.addWidget(detail_label)

            row_layout.addWidget(checkbox)
            row_layout.addLayout(text_layout, 1)
            if tab.get('active'):
                tag = QLabel(_['save_tabs_active'])
                tag.setObjectName('saveTabsTag')
                small = tag.font()
                small.setPointSizeF(small.pointSizeF() * 0.85)
                tag.setFont(small)
                row_layout.addWidget(tag, 0, Qt.AlignVCenter)
            rows_layout.addWidget(row)
            checkbox.stateChanged.connect(self._sync)
            self.checkboxes.append(checkbox)
        rows_layout.addStretch()

        self.rows_area = scroll_area(horizontal=Qt.ScrollBarAlwaysOff)
        self.rows_area.setWidget(rows)
        body_layout.addWidget(self.rows_area, 1)
        main_layout.addWidget(body, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton()
        self.save_button.setMinimumWidth(80)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        self.cancel_button = QPushButton(_['cancel'])
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.all_checkbox.clicked.connect(self._toggle_all)
        self._sync()

        # The list scrolls, so many tabs never push Save / Cancel off screen
        allow_shrinking(self, minimum=(320, 220), keep_whole=[button_layout], fit=False)
        row_height = rows.sizeHint().height()
        wanted = self.sizeHint().height() - self.rows_area.sizeHint().height() + row_height + 2
        cap_to_screen(self, 400, wanted, fraction=0.8)

    # ------------------------------------------------------------------ state
    def _toggle_all(self):
        ticked = sum(box.isChecked() for box in self.checkboxes)
        value = ticked != len(self.checkboxes)
        for box in self.checkboxes:
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        self._sync()

    def _sync(self, *_args):
        _ = self._
        ticked = sum(box.isChecked() for box in self.checkboxes)
        total = len(self.checkboxes)
        self.all_checkbox.blockSignals(True)
        self.all_checkbox.setCheckState(
            Qt.Checked if ticked == total else Qt.Unchecked if ticked == 0 else Qt.PartiallyChecked)
        self.all_checkbox.blockSignals(False)
        self.count_label.setText(_['save_tabs_count'].format(ticked, total))
        if ticked == 0:
            self.save_button.setText(_['save'])
        elif ticked == 1:
            self.save_button.setText(_['save_tabs_button_one'])
        else:
            self.save_button.setText(_['save_tabs_button_many'].format(ticked))
        self.save_button.setEnabled(ticked > 0)

    def selected_ids(self):
        """The ids of the ticked tabs, in tab-bar order."""
        return [tab_id for tab_id, box in zip(self._tab_ids, self.checkboxes) if box.isChecked()]


def ask_which_tabs(tabs, language_code='en', theme='default', parent=None):
    """Show the dialog. Returns the ticked tab ids, or None when it was
    cancelled (Cancel, Esc or the window's X).

    The dialog is gone once this returns: nothing stores it, and it is deleted
    as soon as it closes, whichever way it was closed. A dialog with a parent
    belongs to that parent, so without the deleteLater() every closed one would
    stay alive, hidden, until the main window itself is destroyed."""
    dialog = SaveTabsDialog(tabs, language_code, theme, parent)
    try:
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selected_ids()
        return None
    finally:
        dialog.deleteLater()
