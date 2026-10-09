"""A framed group of two actions under one plain word, for the layer panel's
bottom buttons: New [Strand | Level], Delete [Strand | All], and the same
for masks.

The word is a label, not a button, so it is written once for both actions.
The two buttons keep their own colours and their 14 px bold text; each is as
wide as its word needs (the row's spare room is shared in proportion), so
long translations fit without shrinking the text. The full names ("New
Level", "Delete All") are the buttons' tooltips.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

FONT_PX = 14          # the bottom buttons' size
BUTTON_SIDE_PADDING = 4
FRAME_COLOR = "#ffffff"
LABEL_COLOR = "#303030"


class ActionGroupRow(QFrame):
    """One bottom-panel row: a white frame holding *label_text* and two
    *buttons*. *height* is the row height (that of a plain bottom button)."""

    # Appended to each button's own stylesheet, after a marker so it can be
    # re-applied when something resets the button's style (themes do).
    MARK = "/* action-group-row */"
    BUTTON_STYLE = """
        QPushButton { padding: 0px %dpx; border: none; border-radius: 3px; }
        QPushButton:disabled { border: none; }
        QPushButton:checked { border: 2px solid #3c3c3c; padding: 0px %dpx; }
    """ % (BUTTON_SIDE_PADDING, BUTTON_SIDE_PADDING - 2)

    def __init__(self, label_text, buttons, height, parent=None):
        super().__init__(parent)
        self.setObjectName("actionGroupRow")
        self.setStyleSheet(
            "QFrame#actionGroupRow { background-color: %s; border: 1px solid #888;"
            " border-radius: 4px; }" % FRAME_COLOR)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        self.label = QLabel(label_text)
        self.label.setStyleSheet(
            "QLabel { font-weight: bold; font-size: %dpx; color: %s; background: transparent;"
            " border: none; padding: 0px 1px 0px 3px; }" % (FONT_PX, LABEL_COLOR))
        # No indent or margin of Qt's own: the word starts at its 3 px padding
        self.label.setIndent(0)
        self.label.setMargin(0)
        self.label.setContentsMargins(0, 0, 0, 0)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(self.label)

        self.buttons = tuple(buttons)
        for button in self.buttons:
            # Ignored: the width comes from the stretch (the word's need)
            button.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
            layout.addWidget(button)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(height)
        self.restyle()

    @classmethod
    def base_style(cls, button):
        """*button*'s own stylesheet, without this row's additions."""
        return button.styleSheet().split(cls.MARK)[0]

    def restyle(self):
        """Put the in-group look back on both buttons (after a theme or any
        other code has replaced their stylesheets) and refit the widths."""
        for button in self.buttons:
            button.setStyleSheet(self.base_style(button) + self.MARK + self.BUTTON_STYLE)
        self.refit()

    def set_label(self, text):
        self.label.setText(text)
        self.refit()

    @staticmethod
    def text_width(widget, text):
        """Advance of *text* in *widget*'s font family at 14 px bold."""
        font = QFont(widget.font())
        font.setBold(True)
        font.setPixelSize(FONT_PX)
        return QFontMetrics(font).horizontalAdvance(text)

    def needed_width(self, button):
        """Width *button* needs for its text at 14 px bold, with its padding."""
        return self.text_width(button, button.text()) + 2 * BUTTON_SIDE_PADDING

    def refit(self):
        """Size the word to its text, then share the rest of the row between
        the two buttons in proportion to their words."""
        # Measured in the 14 px bold the stylesheet gives it (the widget's own
        # font may not have it yet), plus its 3 + 1 px padding and 1 px of air:
        # QLabel's size hint adds slack the row has none to spare for
        self.label.setFixedWidth(self.text_width(self.label, self.label.text()) + 5)
        layout = self.layout()
        for button in self.buttons:
            layout.setStretch(layout.indexOf(button), max(1, self.needed_width(button)))
        layout.invalidate()
