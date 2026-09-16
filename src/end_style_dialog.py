"""The "Stylize End Side" dialog.

Opened from a layer button's right-click menu for one free end of a strand.
It edits the end's style record (see end_style.py) and previews every change
live on the canvas, like the shadow editor: Cancel restores the snapshot taken
when the dialog opened, OK keeps the result and saves one undo step.

The controls are the app's own: the Create Mask Grid dialog's large blue
checkbox, the Move Group dialog's slider rows (label / slider / value / text
field) and the Settings dialog's segmented [ - | value | + ] spin box.
"""

import math

from PyQt5.QtCore import Qt, QPointF, QSize, QTimer
from PyQt5.QtGui import (QColor, QIcon, QImage, QIntValidator, QPainter, QPainterPath,
                         QPainterPathStroker, QPen, QPixmap)
from PyQt5.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QColorDialog, QDialog,
                             QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QSizePolicy, QSlider, QSpinBox, QStyleFactory,
                             QToolButton, QVBoxLayout, QWidget)

import end_style
from mask_grid_dialog import LargeIndicatorStyle, MaskGridDialog
from segmented_spin_box import upgrade_spinbox, style_segmented_spinbox
from translations import translations


ANGLED_DEFAULT_TILT = 30  # what Angled starts at when picked with Tilt still at 0

SHAPE_KEYS = (
    ('straight', 'end_shape_straight', 'Straight'),
    ('angled', 'end_shape_angled', 'Angled'),
    ('rounded', 'end_shape_rounded', 'Rounded'),
    ('pointed', 'end_shape_pointed', 'Pointed'),
    ('notched', 'end_shape_notched', 'Notched'),
    ('concave', 'end_shape_concave', 'Concave'),
)


def _tr(_, key, fallback):
    return _[key] if key in _ else fallback


def total_width(strand):
    return float(strand.width) + 2.0 * float(strand.stroke_width)


def _dialog_stylesheet(theme):
    """WidthConfigDialog's theme stylesheet plus the Move Group slider rows and
    the section frames used to group the controls."""
    if theme == 'dark':
        return """
            QDialog { background-color: #2C2C2C; color: white; }
            QLabel { color: white; }
            QLineEdit { background-color: #2B2B2B; color: white; border: 1px solid #555555; border-radius: 4px; padding: 2px 4px; }
            QLineEdit:disabled { color: #808080; border: 1px solid #444444; }
            QSlider::groove:horizontal { background: #555555; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #AAAAAA; width: 14px; margin: -4px 0; border-radius: 7px; }
            QSlider::handle:horizontal:hover { background: #CCCCCC; }
            QSlider::handle:horizontal:disabled { background: #666666; }
            QPushButton { background-color: #252525; color: white; font-weight: bold; border: 2px solid #000000; padding: 10px; border-radius: 4px; min-width: 80px; }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #151515; border: 2px solid #000000; }
            QPushButton#colorSwatch { min-width: 0px; padding: 0px; border: 1px solid #888888; border-radius: 3px; }
            QPushButton#colorSwatch:disabled { border: 1px solid #444444; }
            QToolButton { background-color: #3D3D3D; color: white; border: 1px solid #555555; border-radius: 5px; padding: 4px; }
            QToolButton:checked { background-color: #4A6FA5; border: 2px solid #6A9FD5; }
            QToolButton:hover { border: 1px solid #888888; }
            QFrame#section { background-color: #333333; border: 1px solid #555555; border-radius: 6px; }
            QLabel#sectionTitle { font-weight: bold; color: #FFFFFF; }
            QLabel#hint { color: #AAAAAA; }
            QLabel#header { font-size: 11pt; }
        """
    return """
        QDialog { background-color: #F5F5F5; color: black; }
        QLabel { color: black; }
        QLineEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC; border-radius: 4px; padding: 2px 4px; }
        QLineEdit:disabled { color: #AAAAAA; border: 1px solid #DDDDDD; }
        QPushButton { background-color: #F0F0F0; color: #000000; border: 1px solid #BBBBBB; border-radius: 5px; padding: 10px; min-width: 80px; font-weight: bold; }
        QPushButton:hover { background-color: #E0E0E0; }
        QPushButton:pressed { background-color: #D0D0D0; }
        QPushButton#colorSwatch { min-width: 0px; padding: 0px; border: 1px solid #666666; border-radius: 3px; }
        QPushButton#colorSwatch:disabled { border: 1px solid #CCCCCC; }
        QToolButton { background-color: #FFFFFF; color: black; border: 1px solid #CCCCCC; border-radius: 5px; padding: 4px; }
        QToolButton:checked { background-color: #A0C0E0; border: 2px solid #7090C0; }
        QToolButton:hover { border: 1px solid #999999; }
        QFrame#section { background-color: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 6px; }
        QLabel#sectionTitle { font-weight: bold; color: #333333; }
        QLabel#hint { color: #666666; }
        QLabel#header { font-size: 11pt; }
    """


class EndPreview(QWidget):
    """The preview picture, painted at whatever size the layout gives it.

    ``pixmap()`` renders the same picture at a fixed 380 x 120 (2x) for tests
    and for anyone who wants an image of it."""

    LOGICAL = (380, 120)

    def __init__(self, dialog):
        super().__init__(dialog)
        self._dialog = dialog
        self.setMinimumHeight(70)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def sizeHint(self):
        return QSize(*self.LOGICAL)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._dialog._paint_preview(painter, self.width(), self.height())
        painter.end()

    def pixmap(self):
        w, h = self.LOGICAL
        ratio = 2
        image = QImage(w * ratio, h * ratio, QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(ratio, ratio)
        self._dialog._paint_preview(painter, w, h)
        painter.end()
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(ratio)
        return pixmap


class ShapeGrid(QWidget):
    """The six shape buttons in one row when there is room, otherwise two
    rows of three, so a narrow dialog never has to elide their labels."""

    BUTTON = (88, 72)

    def __init__(self, buttons, parent=None):
        super().__init__(parent)
        self._buttons = buttons
        self._columns = 0
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(6)
        for button in buttons:
            button.setFixedSize(*self.BUTTON)
        self._reflow(6)

    def _reflow(self, columns):
        if columns == self._columns:
            return
        self._columns = columns
        for button in self._buttons:
            self._grid.removeWidget(button)
        for index, button in enumerate(self._buttons):
            self._grid.addWidget(button, index // columns, index % columns, Qt.AlignLeft)
        self._grid.setColumnStretch(columns, 1)
        self.updateGeometry()

    def resizeEvent(self, event):
        needed = len(self._buttons) * (self.BUTTON[0] + 6)
        self._reflow(6 if event.size().width() >= needed else 3)
        super().resizeEvent(event)


class EndStyleDialog(QDialog):
    """Edit the end style of one free end of ``strand`` (side 0 = start, 1 = end)."""

    def __init__(self, strand, side, layer_panel, parent=None):
        super().__init__(parent)
        self.strand = strand
        self.side = side
        self.layer_panel = layer_panel
        self.canvas = getattr(layer_panel, 'canvas', None)
        self._updating = False
        self._accepted = False

        self.language_code = getattr(layer_panel, 'language_code', 'en')
        _ = translations.get(self.language_code, translations['en'])
        self.is_rtl = self.language_code == 'he'
        if self.is_rtl:
            self.setLayoutDirection(Qt.RightToLeft)

        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        self.theme = main_window.current_theme if main_window and hasattr(main_window, 'current_theme') else 'default'
        self.is_dark = self.theme == 'dark'

        self.setWindowTitle(_tr(_, 'stylize_end_side', 'Stylize End Side'))
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(_dialog_stylesheet(self.theme))
        # Freely resizable: the body scrolls, the header and buttons stay put
        self.setMinimumSize(440, 300)
        self.setSizeGripEnabled(True)

        # Snapshot for Cancel: both ends' styles and both side-line flags
        self._snapshot = {
            'styles': [end_style.copy_style(strand.get_end_style(0)),
                       end_style.copy_style(strand.get_end_style(1))],
            'start_line_visible': bool(getattr(strand, 'start_line_visible', True)),
            'end_line_visible': bool(getattr(strand, 'end_line_visible', True)),
        }

        current = end_style.normalize_style(strand.get_end_style(side)) or end_style.default_style()
        self._shape = current['shape']
        self._pinned_color = QColor(current['line_color']) if current['line_color'] is not None else QColor(strand.stroke_color)

        self._build_ui(_, current)
        self._sync_enabled_state()
        self._refresh_preview()
        self._fit_to_screen()

        if self.canvas is not None and hasattr(self.canvas, 'language_changed'):
            try:
                self.canvas.language_changed.connect(self.update_translations)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # App-native control helpers
    # ------------------------------------------------------------------
    def _checkbox(self, text, checked):
        """The Create Mask Grid dialog's checkbox, built with its own helpers."""
        box = QCheckBox(text)
        box.setChecked(checked)
        box.setStyle(LargeIndicatorStyle(QStyleFactory.create('Fusion'), 20))
        box.setMinimumHeight(26)
        MaskGridDialog._setup_custom_checkmark(None, box)
        MaskGridDialog._style_mask_checkbox(None, box, self.is_dark, True, 8)
        return box

    def _restyle_checkbox(self, box):
        MaskGridDialog._style_mask_checkbox(None, box, self.is_dark, box.isEnabled(), 8)

    def _stepper(self, value, lo, hi):
        """The Settings dialog's segmented [ - | value | + ] spin box."""
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setValue(value)
        upgrade_spinbox(spin)
        style_segmented_spinbox(spin, self.theme, self.is_rtl)
        return spin

    def _slider_row(self, label_text, lo, hi, value, fmt):
        """A Move Group dialog row: label / slider / live value / text field."""
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(value)
        value_label = QLabel(fmt(value))
        value_label.setMinimumWidth(30)
        field = QLineEdit()
        field.setValidator(QIntValidator(lo, hi))
        field.setText(str(value))
        field.setMaximumWidth(60)
        row.addWidget(label)
        row.addWidget(slider)
        row.addWidget(value_label)
        row.addWidget(field)

        def on_slider(v):
            value_label.setText(fmt(v))
            if field.text() != str(v):
                field.blockSignals(True)
                field.setText(str(v))
                field.blockSignals(False)
            self._apply_live()

        def on_field():
            text = field.text().strip()
            try:
                v = int(text)
            except ValueError:
                return
            v = max(lo, min(hi, v))
            if slider.value() != v:
                slider.setValue(v)
            else:
                value_label.setText(fmt(v))

        slider.valueChanged.connect(on_slider)
        field.editingFinished.connect(on_field)
        field.textEdited.connect(lambda _t: on_field())
        return row, label, slider, value_label, field

    def _section(self, title):
        frame = QFrame()
        frame.setObjectName('section')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName('sectionTitle')
        layout.addWidget(label)
        return frame, layout, label

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self, _, current):
        outer = QVBoxLayout(self)
        outer.setSpacing(10)

        self.header_label = QLabel()
        self.header_label.setObjectName('header')
        outer.addWidget(self.header_label)

        # Everything between the header and the buttons scrolls, so the
        # dialog can be made as small as the user likes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        root = QVBoxLayout(content)
        root.setContentsMargins(0, 0, 8, 0)
        root.setSpacing(10)
        self.scroll_area.setWidget(content)
        outer.addWidget(self.scroll_area, 1)

        # Preview
        frame, layout, self.preview_title = self._section(_tr(_, 'end_style_preview', 'Preview'))
        self.preview_label = EndPreview(self)
        layout.addWidget(self.preview_label)
        self.preview_hint = QLabel()
        self.preview_hint.setObjectName('hint')
        self.preview_hint.setWordWrap(True)
        layout.addWidget(self.preview_hint)
        root.addWidget(frame)

        # End shape
        frame, layout, self.shape_title = self._section(_tr(_, 'end_shape', 'End Shape'))
        self.shape_group = QButtonGroup(self)
        self.shape_group.setExclusive(True)
        self.shape_buttons = {}
        for key, tr_key, fallback in SHAPE_KEYS:
            button = QToolButton()
            button.setCheckable(True)
            button.setText(_tr(_, tr_key, fallback))
            button.setIcon(self._shape_icon(key))
            button.setIconSize(QSize(56, 34))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setChecked(key == current['shape'])
            button.clicked.connect(lambda checked=False, k=key: self._on_shape(k))
            self.shape_group.addButton(button)
            self.shape_buttons[key] = button
        self.shape_grid = ShapeGrid(list(self.shape_buttons.values()))
        layout.addWidget(self.shape_grid)

        tilt_row, self.tilt_label, self.tilt_slider, self.tilt_value, self.tilt_field = self._slider_row(
            _tr(_, 'end_tilt', 'Tilt'), -int(end_style.TILT_MAX), int(end_style.TILT_MAX),
            int(round(current['tilt'])), lambda v: f"{v:+d}°")
        self.tilt_slider.setToolTip(_tr(_, 'end_tilt_tooltip', 'Rotate the end edge around the endpoint. 0° is square to the strand.'))
        layout.addLayout(tilt_row)

        depth_row, self.depth_label, self.depth_slider, self.depth_value, self.depth_field = self._slider_row(
            _tr(_, 'end_depth', 'Depth'), 0, 100, int(round(current['depth'] * 100)), lambda v: f"{v} %")
        self.depth_slider.setToolTip(_tr(_, 'end_depth_tooltip', "How far the shape reaches, as a share of the strand's width."))
        layout.addLayout(depth_row)

        total_width = float(self.strand.width) + 2.0 * float(self.strand.stroke_width)
        offset_min = -int(math.floor(total_width / 2.0))
        offset_max = int(math.ceil(total_width * 2.0))
        offset_value = int(round(max(offset_min, min(offset_max, current['offset']))))
        extend_row = QHBoxLayout()
        self.extend_label = QLabel(_tr(_, 'end_extend_trim', 'Extend / Trim'))
        self.extend_label.setMinimumWidth(100)
        extend_row.addWidget(self.extend_label)
        self.offset_spin = self._stepper(offset_value, offset_min, offset_max)
        self.offset_spin.valueChanged.connect(lambda _v: self._apply_live())
        extend_row.addWidget(self.offset_spin)
        self.extend_px = QLabel(_tr(_, 'px', 'px'))
        extend_row.addWidget(self.extend_px)
        extend_row.addStretch()
        layout.addLayout(extend_row)
        self.extend_hint = QLabel()
        self.extend_hint.setObjectName('hint')
        self.extend_hint.setWordWrap(True)
        layout.addWidget(self.extend_hint)
        root.addWidget(frame)

        # Side line
        frame, layout, self.line_title = self._section(_tr(_, 'side_line_section', 'Side Line'))
        line_visible = self._snapshot['start_line_visible'] if self.side == 0 else self._snapshot['end_line_visible']
        self.show_line_box = self._checkbox(_tr(_, 'show_side_line', 'Show side line'), line_visible)
        self.show_line_box.toggled.connect(self._on_show_line)
        layout.addWidget(self.show_line_box)

        thickness_row = QHBoxLayout()
        self.thickness_label = QLabel(_tr(_, 'side_line_thickness', 'Thickness'))
        self.thickness_label.setMinimumWidth(100)
        thickness_row.addWidget(self.thickness_label)
        stroke_width = int(round(float(self.strand.stroke_width)))
        thickness = int(round(current['line_width'])) if current['line_width'] is not None else stroke_width
        self.thickness_spin = self._stepper(max(1, thickness), 1, 40)
        self.thickness_spin.valueChanged.connect(lambda _v: self._apply_live())
        thickness_row.addWidget(self.thickness_spin)
        self.thickness_px = QLabel(_tr(_, 'px', 'px'))
        thickness_row.addWidget(self.thickness_px)
        thickness_row.addStretch()
        layout.addLayout(thickness_row)

        color_row = QHBoxLayout()
        self.color_label = QLabel(_tr(_, 'side_line_color', 'Color'))
        self.color_label.setMinimumWidth(100)
        color_row.addWidget(self.color_label)
        self.color_swatch = QPushButton()
        self.color_swatch.setObjectName('colorSwatch')
        self.color_swatch.setFixedSize(44, 28)
        self.color_swatch.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_swatch)
        color_row.addSpacing(12)
        self.use_stroke_color_box = self._checkbox(_tr(_, 'use_stroke_color', 'Use stroke color'),
                                                   current['line_color'] is None)
        self.use_stroke_color_box.toggled.connect(lambda _c: (self._sync_enabled_state(), self._apply_live()))
        color_row.addWidget(self.use_stroke_color_box)
        color_row.addStretch()
        layout.addLayout(color_row)
        root.addWidget(frame)

        # Apply to both free ends (two free ends only)
        self.both_ends_box = None
        if self._has_two_free_ends():
            self.both_ends_box = self._checkbox(_tr(_, 'apply_to_both_free_ends', 'Apply to both free ends'), False)
            root.addWidget(self.both_ends_box)
        root.addStretch()

        # Buttons (outside the scroll area: always reachable)
        button_row = QHBoxLayout()
        self.reset_button = QPushButton(_tr(_, 'reset_to_straight', 'Reset to Straight'))
        self.reset_button.clicked.connect(self._reset_to_straight)
        button_row.addWidget(self.reset_button)
        button_row.addStretch()
        self.ok_button = QPushButton(_tr(_, 'ok', 'OK'))
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton(_tr(_, 'cancel', 'Cancel'))
        self.cancel_button.clicked.connect(self.reject)
        button_row.addWidget(self.ok_button)
        button_row.addWidget(self.cancel_button)
        outer.addLayout(button_row)

        self._update_swatch()
        self.update_translations()

    def _fit_to_screen(self):
        """Open at the content's natural size, but never larger than the
        available screen area (the body scrolls instead)."""
        hint = self.sizeHint()
        width, height = hint.width(), hint.height()
        screen = None
        try:
            screen = self.screen()
        except AttributeError:
            pass
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, int(available.width() * 0.9))
            height = min(height, int(available.height() * 0.9))
        self.resize(max(width, self.minimumWidth()), max(height, self.minimumHeight()))

    def _has_two_free_ends(self):
        if hasattr(self.strand, 'parent'):
            return False
        circles = getattr(self.strand, 'has_circles', [False, False])
        return not circles[0] and not circles[1]

    # ------------------------------------------------------------------
    # Icons / preview
    # ------------------------------------------------------------------
    def _shape_icon(self, shape):
        """Tiny real-geometry icon of a strand end for the shape picker."""
        from strand import Strand
        w, h = 56, 34
        image = QImage(w * 2, h * 2, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(2, 2)
        sample = Strand(QPointF(-30, h / 2), QPointF(w - 16, h / 2), 16,
                        QColor(self.strand.color), QColor(self.strand.stroke_color), 2)
        sample.control_point1 = QPointF(-10, h / 2)
        sample.control_point2 = QPointF(w - 30, h / 2)
        sample.update_shape()
        sample.update_side_line()
        style = dict(shape=shape, depth=0.6, tilt=30.0 if shape == 'angled' else 0.0)
        if shape == 'straight':
            style['offset'] = 0.001  # any non-default value so the styled path is used
        sample.set_end_style(1, style)
        self._paint_strand_body(painter, sample)
        painter.end()
        return QIcon(QPixmap.fromImage(image))

    def _refresh_preview(self):
        self.preview_label.update()

    def _paint_preview(self, painter, w, h):
        """Draw the real end with the current settings, exactly as the canvas
        draws it and in the canvas's own orientation, centred on the endpoint
        (marked with a dashed green circle), into a w x h picture."""
        painter.fillRect(0, 0, w, h, QColor('#2C2C2C') if self.is_dark else QColor('#FFFFFF'))
        painter.setPen(QPen(QColor(255, 255, 255, 25) if self.is_dark else QColor(0, 0, 0, 18), 1))
        for gx in range(0, w, 27):
            painter.drawLine(gx, 0, gx, h)
        for gy in range(0, h, 27):
            painter.drawLine(0, gy, w, gy)

        strand = self.strand
        total = float(strand.width) + 2.0 * float(strand.stroke_width)
        scale = min(1.6, 0.6 * h / max(total, 1.0))
        point = strand.start if self.side == 0 else strand.end
        painter.translate(w / 2.0, h / 2.0)
        painter.scale(scale, scale)
        painter.translate(-point.x(), -point.y())

        self._paint_strand_body(painter, strand)

        painter.setPen(QPen(QColor(59, 164, 36), 1.5 / scale, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(point, 6 / scale, 6 / scale)

    @staticmethod
    def _paint_strand_body(painter, strand):
        """The strand body as Strand.draw paints it (no shadow, no
        decorations): styled footprint when an end is styled, otherwise the
        classic flat-capped stroke and fill plus the side lines."""
        painter.setPen(Qt.NoPen)
        geometry = strand._end_geometry()
        if geometry is not None:
            stroke_path, fill_path = geometry.body, geometry.fill_body()
        else:
            path = strand.get_path()
            stroke_stroker = QPainterPathStroker()
            stroke_stroker.setWidth(total_width(strand))
            stroke_stroker.setJoinStyle(Qt.MiterJoin)
            stroke_stroker.setCapStyle(Qt.FlatCap)
            stroke_path = stroke_stroker.createStroke(path)
            fill_stroker = QPainterPathStroker()
            fill_stroker.setWidth(strand.width)
            fill_stroker.setJoinStyle(Qt.MiterJoin)
            fill_stroker.setCapStyle(Qt.FlatCap)
            fill_path = fill_stroker.createStroke(path)
        for body_path in (stroke_path, fill_path):
            body_path.setFillRule(Qt.WindingFill)
        strand._paint_body_paths(painter, stroke_path, fill_path, geometry)
        # Side lines: the classic stroke_width line or the styled band, both
        # through the same routine the canvas uses
        if hasattr(strand, '_draw_side_lines'):
            strand._draw_side_lines(painter)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    def current_style(self):
        """The style record described by the controls (may normalize to None)."""
        stroke_width = float(self.strand.stroke_width)
        thickness = float(self.thickness_spin.value())
        line_width = None if abs(thickness - stroke_width) < 1e-6 else thickness
        line_color = None if self.use_stroke_color_box.isChecked() else QColor(self._pinned_color)
        return {
            'shape': self._shape,
            'tilt': float(self.tilt_slider.value()),
            'depth': self.depth_slider.value() / 100.0,
            'offset': float(self.offset_spin.value()),
            'line_width': line_width,
            'line_color': line_color,
        }

    def _sync_enabled_state(self):
        # Straight is always square to the strand: Tilt belongs to Angled and
        # to the shaped ends
        tilt_enabled = self._shape != 'straight'
        for widget in (self.tilt_label, self.tilt_slider, self.tilt_value, self.tilt_field):
            widget.setEnabled(tilt_enabled)
        depth_enabled = self._shape in end_style.DEPTH_SHAPES
        for widget in (self.depth_label, self.depth_slider, self.depth_value, self.depth_field):
            widget.setEnabled(depth_enabled)
        line_on = self.show_line_box.isChecked()
        for widget in (self.thickness_label, self.thickness_spin, self.thickness_px, self.color_label,
                       self.color_swatch, self.use_stroke_color_box):
            widget.setEnabled(line_on)
        self._restyle_checkbox(self.use_stroke_color_box)
        self.color_swatch.setEnabled(line_on and not self.use_stroke_color_box.isChecked())
        self._update_swatch()

    def _update_swatch(self):
        color = QColor(self.strand.stroke_color) if self.use_stroke_color_box.isChecked() else QColor(self._pinned_color)
        self.color_swatch.setStyleSheet(
            f"QPushButton#colorSwatch {{ background-color: rgba({color.red()}, {color.green()}, "
            f"{color.blue()}, {color.alpha()}); min-width: 0px; padding: 0px; "
            f"border: 1px solid {'#888888' if self.is_dark else '#666666'}; border-radius: 3px; }}")

    def _on_shape(self, key):
        previous = self._shape
        self._shape = key
        self._updating = True
        try:
            if key == 'straight':
                self.tilt_slider.setValue(0)
            elif key == 'angled' and previous == 'straight' and self.tilt_slider.value() == 0:
                # Angled is the slanted cut: start it visibly slanted
                self.tilt_slider.setValue(ANGLED_DEFAULT_TILT)
        finally:
            self._updating = False
        self._sync_enabled_state()
        self._apply_live()

    def _on_show_line(self, checked):
        if self.side == 0:
            self.strand.start_line_visible = bool(checked)
        else:
            self.strand.end_line_visible = bool(checked)
        self._sync_enabled_state()
        self._apply_live()

    def _pick_color(self):
        _ = translations.get(self.language_code, translations['en'])
        dialog = QColorDialog(QColor(self._pinned_color), self)
        dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        dialog.setWindowTitle(_tr(_, 'side_line_color', 'Color'))
        parent_button = self.parent()
        if parent_button is not None and hasattr(parent_button, 'translate_color_dialog'):
            try:
                parent_button.translate_color_dialog(dialog, _)
            except Exception:
                pass
        if dialog.exec_() == QDialog.Accepted:
            color = dialog.selectedColor()
            if color.isValid():
                self._pinned_color = QColor(color)
                self._update_swatch()
                self._apply_live()

    def _reset_to_straight(self):
        self._updating = True
        try:
            self._shape = 'straight'
            self.shape_buttons['straight'].setChecked(True)
            self.tilt_slider.setValue(0)
            self.depth_slider.setValue(50)
            self.offset_spin.setValue(0)
            self.thickness_spin.setValue(max(1, int(round(float(self.strand.stroke_width)))))
            self.use_stroke_color_box.setChecked(True)
            self.show_line_box.setChecked(True)
        finally:
            self._updating = False
        self._sync_enabled_state()
        self._apply_live()

    # ------------------------------------------------------------------
    # Live apply / accept / cancel
    # ------------------------------------------------------------------
    def _apply_live(self):
        if self._updating:
            return
        self.strand.set_end_style(self.side, self.current_style())
        self._refresh_canvas()
        self._refresh_preview()

    def _refresh_canvas(self):
        strand = self.strand
        if hasattr(strand, 'update_shape'):
            try:
                strand.update_shape()
            except Exception:
                pass
        canvas = self.canvas
        if canvas is None:
            return
        # Masks built on this strand recompute from its live footprint; drop
        # their cached shadow blockers so the intersection follows the end.
        for other in getattr(canvas, 'strands', []) or []:
            if (getattr(other, 'first_selected_strand', None) is strand
                    or getattr(other, 'second_selected_strand', None) is strand):
                if hasattr(other, 'force_shadow_update'):
                    try:
                        other.force_shadow_update()
                    except Exception:
                        pass
                if hasattr(other, '_shadow_blocker_cache'):
                    try:
                        delattr(other, '_shadow_blocker_cache')
                    except Exception:
                        pass
        canvas.update()

    def accept(self):
        self._accepted = True
        if self.both_ends_box is not None and self.both_ends_box.isChecked():
            other = 1 - self.side
            self.strand.set_end_style(other, end_style.copy_style(self.strand.get_end_style(self.side)))
            visible = self.show_line_box.isChecked()
            if other == 0:
                self.strand.start_line_visible = visible
            else:
                self.strand.end_line_visible = visible
        self._refresh_canvas()
        canvas = self.canvas
        if canvas is not None:
            QTimer.singleShot(0, canvas.update)
            manager = getattr(canvas, 'undo_redo_manager', None)
            if manager is not None:
                manager._last_save_time = 0
                manager.save_state(
                    action='strand.end_style', source='dialog',
                    targets=[getattr(self.strand, 'layer_name', None)],
                    detail='start' if self.side == 0 else 'end')
        super().accept()

    def reject(self):
        self.restore_snapshot()
        super().reject()

    def restore_snapshot(self):
        """Put both ends back exactly as they were when the dialog opened."""
        snapshot = self._snapshot
        self.strand.set_end_style(0, end_style.copy_style(snapshot['styles'][0]))
        self.strand.set_end_style(1, end_style.copy_style(snapshot['styles'][1]))
        self.strand.start_line_visible = snapshot['start_line_visible']
        self.strand.end_line_visible = snapshot['end_line_visible']
        self._refresh_canvas()

    def closeEvent(self, event):
        if not self._accepted:
            self.restore_snapshot()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Translations
    # ------------------------------------------------------------------
    def update_translations(self):
        self.language_code = getattr(self.layer_panel, 'language_code', self.language_code)
        _ = translations.get(self.language_code, translations['en'])
        layer = getattr(self.strand, 'layer_name', '')
        side_text = _tr(_, 'side_start', 'Start') if self.side == 0 else _tr(_, 'side_end', 'End')
        header = _tr(_, 'end_style_header', 'Layer {layer} — {side} side')
        try:
            header = header.format(layer=layer, side=side_text)
        except (KeyError, IndexError):
            header = f"Layer {layer} — {side_text} side"
        self.setWindowTitle(_tr(_, 'stylize_end_side', 'Stylize End Side'))
        self.header_label.setText(header)
        self.preview_title.setText(_tr(_, 'end_style_preview', 'Preview'))
        self.preview_hint.setText(_tr(_, 'end_style_live_hint',
                                      'Changes show on the canvas immediately. Cancel puts the end back exactly as it was.'))
        self.shape_title.setText(_tr(_, 'end_shape', 'End Shape'))
        for key, tr_key, fallback in SHAPE_KEYS:
            self.shape_buttons[key].setText(_tr(_, tr_key, fallback))
        self.tilt_label.setText(_tr(_, 'end_tilt', 'Tilt'))
        self.tilt_slider.setToolTip(_tr(_, 'end_tilt_tooltip', 'Rotate the end edge around the endpoint. 0° is square to the strand.'))
        self.depth_label.setText(_tr(_, 'end_depth', 'Depth'))
        self.depth_slider.setToolTip(_tr(_, 'end_depth_tooltip', "How far the shape reaches, as a share of the strand's width."))
        self.extend_label.setText(_tr(_, 'end_extend_trim', 'Extend / Trim'))
        self.extend_px.setText(_tr(_, 'px', 'px'))
        self.extend_hint.setText(_tr(_, 'end_extend_trim_hint',
                                     '+ extends past the endpoint, − trims. The endpoint itself never moves.'))
        self.line_title.setText(_tr(_, 'side_line_section', 'Side Line'))
        self.show_line_box.setText(_tr(_, 'show_side_line', 'Show side line'))
        self.thickness_label.setText(_tr(_, 'side_line_thickness', 'Thickness'))
        self.thickness_px.setText(_tr(_, 'px', 'px'))
        self.color_label.setText(_tr(_, 'side_line_color', 'Color'))
        self.use_stroke_color_box.setText(_tr(_, 'use_stroke_color', 'Use stroke color'))
        if self.both_ends_box is not None:
            self.both_ends_box.setText(_tr(_, 'apply_to_both_free_ends', 'Apply to both free ends'))
        self.reset_button.setText(_tr(_, 'reset_to_straight', 'Reset to Straight'))
        self.ok_button.setText(_tr(_, 'ok', 'OK'))
        self.cancel_button.setText(_tr(_, 'cancel', 'Cancel'))
