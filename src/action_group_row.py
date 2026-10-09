"""A framed group of two actions under one plain word, for the layer panel's
bottom buttons: New [Strand | Level], Delete [Strand | All], and the same
for masks.

The word is a label, not a button, so it is written once for both actions.
The two buttons keep their own colours and their 14 px bold text; each is as
wide as its word needs (the row's spare room is shared in proportion), so
long translations fit without shrinking the text. The full names ("New
Level", "Delete All") are the buttons' tooltips.
"""

import math

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy

FONT_PX = 14          # the bottom buttons' size
BUTTON_SIDE_PADDING = 4
WORD_PADDING = 4      # the word's 3 px lead-in + 1 px tail
GAP = 1               # between the word and the buttons, and between the buttons
# The frame is an outline only: the panel's own background shows through in
# every theme, so the word never looks like a button. The word takes the
# theme's text colour.
LABEL_COLORS = {"default": "#303030", "light": "#303030", "dark": "#e8e8e8"}


class ActionGroupRow(QFrame):
    """One bottom-panel row: an outline (no fill) holding *label_text* and two
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
            "QFrame#actionGroupRow { background-color: transparent; border: 1px solid #888;"
            " border-radius: 4px; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(GAP)

        self.label = QLabel(label_text)
        self.set_theme("default")
        # No indent or margin of Qt's own; the word's 3 px lead-in and 1 px
        # tail are its contents margins (see _place_word)
        self.label.setIndent(0)
        self.label.setMargin(0)
        self._place_word()
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.label.setAlignment(Qt.AlignVCenter)
        layout.addWidget(self.label)

        self.buttons = tuple(buttons)
        for button in self.buttons:
            # Fixed: refit() sets each width from its word (see split_widths)
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            layout.addWidget(button)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(height)
        self.restyle()

    def set_theme(self, theme_name):
        """The word in the theme's text colour (the frame has no fill)."""
        color = LABEL_COLORS.get(theme_name, LABEL_COLORS["default"])
        self.label.setStyleSheet(
            "QLabel { font-weight: bold; font-size: %dpx; color: %s; background: transparent;"
            " border: none; padding: 0px; }" % (FONT_PX, color))

    def _place_word(self):
        """3 px before the word, on its reading side (left, or right in a
        right-to-left language), as CSS padding-inline does in the mockup.
        The 1 px after it stays inside the label's contents: Qt clips a
        label's painting there, and a bold last letter can overhang its
        advance by a fraction of a pixel, which the mockup paints too."""
        if self.layoutDirection() == Qt.RightToLeft:
            self.label.setContentsMargins(0, 0, 3, 0)
        else:
            self.label.setContentsMargins(3, 0, 0, 0)

    def changeEvent(self, event):
        """Hebrew turns the row round; the word's lead-in follows."""
        super().changeEvent(event)
        if event.type() == QEvent.LayoutDirectionChange:
            self._place_word()

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

    def word_width(self):
        """The word's box: its text in 14 px bold plus its 3 + 1 px padding."""
        return self.text_width(self.label, self.label.text()) + WORD_PADDING

    def inner_width(self):
        """Width inside the frame's border and its 1 px padding."""
        margins = self.layout().contentsMargins()
        return self.contentsRect().width() - margins.left() - margins.right()

    def split_widths(self, inner_width=None):
        """The two buttons' widths: what the row has left after the word and
        the gaps, shared in proportion to what each button's word needs.

        The layout rule of the mockup, to the pixel: word = text + 4; first
        button = rest * need1 / (need1 + need2), halves rounded up; second = the rest.
        (CSS flex `need 1 0` shares the same way.)"""
        if inner_width is None:
            inner_width = self.inner_width()
        rest = max(0, inner_width - self.word_width() - GAP * len(self.buttons))
        needs = [self.needed_width(button) for button in self.buttons]
        # halves round up, as in the mockup (Python's round() would go to even)
        first = int(math.floor(rest * needs[0] / float(sum(needs)) + 0.5)) if sum(needs) else rest // 2
        return [first, rest - first]

    def refit(self):
        """Size the word to its text and split the rest between the buttons."""
        # Measured in the 14 px bold the stylesheet gives it (the widget's own
        # font may not have it yet); QLabel's size hint adds slack the row has
        # none to spare for
        self.label.setFixedWidth(self.word_width())
        if self.inner_width() > 0:
            for button, width in zip(self.buttons, self.split_widths()):
                button.setFixedWidth(width)
        self.layout().invalidate()

    def resizeEvent(self, event):
        """A new row width (the panel was resized) re-splits the buttons."""
        super().resizeEvent(event)
        self.refit()
