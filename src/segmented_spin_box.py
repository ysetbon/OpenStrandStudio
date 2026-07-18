"""
Segmented +/- spin box upgrade (v1.109).

Turns a plain QSpinBox / QDoubleSpinBox into a single "segmented stepper"
control:  [ - | value | + ]  — one rounded container with hairline
separators, flat minus/plus buttons and press-and-hold auto-repeat,
matching the button language of the Edit Strand Angles dialog.

The native Qt up/down arrows are hidden and two QToolButtons are embedded
inside the spin box itself, so every existing reference to the spin box
widget (layouts, signals, findChildren passes) keeps working unchanged.

Theme styling (default / light / dark) and direction (LTR / RTL) are applied
with style_segmented_spinbox(); in RTL the buttons swap sides so "+" sits on
the left, mirroring the approved mockup.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractSpinBox, QBoxLayout, QDoubleSpinBox, QHBoxLayout, QSizePolicy,
    QSpinBox, QToolButton
)

# Palette per app theme, matching the settings dialog stylesheets
# (dark: #2C2C2C/#3D3D3D/#505050, light: white/#CCCCCC, default: #F5F5F5/#ADADAD).
_THEME_COLORS = {
    'dark': {
        'bg': '#3D3D3D', 'fg': '#FFFFFF', 'border': '#505050',
        'btn_bg': '#333333', 'btn_fg': '#FFFFFF',
        'btn_hover': '#454545', 'btn_pressed': '#222222',
        'sep': '#505050',
        'dis_bg': '#2F2F2F', 'dis_fg': '#808080', 'dis_border': '#454545',
        'btn_dis_bg': '#2A2A2A', 'btn_dis_fg': '#666666',
    },
    'light': {
        'bg': '#FFFFFF', 'fg': '#000000', 'border': '#CCCCCC',
        'btn_bg': '#F5F5F5', 'btn_fg': '#000000',
        'btn_hover': '#E4E4E4', 'btn_pressed': '#D0D0D0',
        'sep': '#D5D5D5',
        'dis_bg': '#F5F5F5', 'dis_fg': '#AAAAAA', 'dis_border': '#DDDDDD',
        'btn_dis_bg': '#EFEFEF', 'btn_dis_fg': '#BBBBBB',
    },
    'default': {
        'bg': '#FFFFFF', 'fg': '#000000', 'border': '#ADADAD',
        'btn_bg': '#F5F5F5', 'btn_fg': '#000000',
        'btn_hover': '#E4E4E4', 'btn_pressed': '#D0D0D0',
        'sep': '#D5D5D5',
        'dis_bg': '#F5F5F5', 'dis_fg': '#AAAAAA', 'dis_border': '#DDDDDD',
        'btn_dis_bg': '#EFEFEF', 'btn_dis_fg': '#BBBBBB',
    },
}

# Geometry based on the approved HTML mockup, with the whitespace between
# the value and the buttons halved per user feedback:
# [ 30px button | ~48px value | 30px button ] inside a 1px border, 28px tall.
_BUTTON_WIDTH = 30
_FIXED_HEIGHT = 28
_FIXED_WIDTH = 110


def upgrade_spinbox(spinbox):
    """Embed flat -/+ buttons inside the spin box (idempotent)."""
    if spinbox.property('segmented'):
        return
    spinbox.setProperty('segmented', True)
    spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
    spinbox.setAlignment(Qt.AlignCenter)
    # Numeric fields always stay LTR (matches the dialog's convention);
    # button sides are mirrored explicitly via the internal layout direction.
    spinbox.setLayoutDirection(Qt.LeftToRight)
    spinbox.setFixedHeight(_FIXED_HEIGHT)
    spinbox.setFixedWidth(_FIXED_WIDTH)

    layout = QHBoxLayout(spinbox)
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(0)

    minus_button = QToolButton(spinbox)
    minus_button.setText('−')  # proper minus sign
    plus_button = QToolButton(spinbox)
    plus_button.setText('+')
    for button in (minus_button, plus_button):
        button.setFocusPolicy(Qt.NoFocus)
        button.setFixedWidth(_BUTTON_WIDTH)
        # Stretch to the full inner height of the control
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button.setCursor(Qt.PointingHandCursor)
        # Press-and-hold keeps stepping, like the Edit Strand Angles buttons
        button.setAutoRepeat(True)
        button.setAutoRepeatDelay(400)
        button.setAutoRepeatInterval(60)
    minus_button.clicked.connect(spinbox.stepDown)
    plus_button.clicked.connect(spinbox.stepUp)

    layout.addWidget(minus_button)
    layout.addStretch()
    layout.addWidget(plus_button)

    spinbox._segmented_minus = minus_button
    spinbox._segmented_plus = plus_button
    spinbox._segmented_layout = layout


def style_segmented_spinbox(spinbox, theme_name, is_rtl=False):
    """Apply theme + direction styling to an upgraded spin box."""
    if not spinbox.property('segmented'):
        return
    c = _THEME_COLORS.get(theme_name, _THEME_COLORS['default'])

    spinbox._segmented_layout.setDirection(
        QBoxLayout.RightToLeft if is_rtl else QBoxLayout.LeftToRight)

    spinbox.setStyleSheet(f"""
        QAbstractSpinBox {{
            background-color: {c['bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 5px;
            padding-left: {_BUTTON_WIDTH + 1}px;
            padding-right: {_BUTTON_WIDTH + 1}px;
        }}
        QAbstractSpinBox:disabled {{
            background-color: {c['dis_bg']};
            color: {c['dis_fg']};
            border: 1px solid {c['dis_border']};
        }}
    """)

    minus_side = 'right' if is_rtl else 'left'
    plus_side = 'left' if is_rtl else 'right'
    for button, side in ((spinbox._segmented_minus, minus_side),
                         (spinbox._segmented_plus, plus_side)):
        separator_side = 'left' if side == 'right' else 'right'
        button.setStyleSheet(f"""
            QToolButton {{
                background-color: {c['btn_bg']};
                color: {c['btn_fg']};
                border: none;
                border-{separator_side}: 1px solid {c['sep']};
                border-top-{side}-radius: 4px;
                border-bottom-{side}-radius: 4px;
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }}
            QToolButton:hover {{
                background-color: {c['btn_hover']};
            }}
            QToolButton:pressed {{
                background-color: {c['btn_pressed']};
            }}
            QToolButton:disabled {{
                background-color: {c['btn_dis_bg']};
                color: {c['btn_dis_fg']};
            }}
        """)


def upgrade_and_style_all(root_widget, theme_name, is_rtl=False):
    """Upgrade (if needed) and restyle every QSpinBox/QDoubleSpinBox under root_widget."""
    for spinbox in root_widget.findChildren(QAbstractSpinBox):
        if isinstance(spinbox, (QSpinBox, QDoubleSpinBox)):
            upgrade_spinbox(spinbox)
            style_segmented_spinbox(spinbox, theme_name, is_rtl)
