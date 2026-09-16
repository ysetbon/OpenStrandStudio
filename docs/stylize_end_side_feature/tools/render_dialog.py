"""Qt mockup of the proposed 'Stylize End Side' dialog.

It reuses the app's REAL control styles rather than imitating them:
- dialog stylesheet: WidthConfigDialog's default theme (numbered_layer_button.py)
- toggles: MaskGridDialog's large blue checkbox (LargeIndicatorStyle proxy,
  _style_mask_checkbox stylesheet, _setup_custom_checkmark white tick)
- sliders: the Move Group dialog rows (label / QSlider / value label / QLineEdit)
- +/- steppers: segmented_spin_box.upgrade_spinbox + style_segmented_spinbox, the
  same segmented [ - | value | + ] control the Settings dialog uses
The preview is drawn by the geometry prototype. Documentation helper only.
"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")
sys.argv = sys.argv[:1]
from end_styles import *  # noqa (creates the QApplication, imports Strand)
from end_styles import _stroked
from PyQt5.QtWidgets import (QStyleFactory, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox, QLineEdit,
                             QCheckBox, QPushButton, QToolButton, QFrame, QButtonGroup, QWidget)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QIcon, QIntValidator
from mask_grid_dialog import MaskGridDialog, LargeIndicatorStyle
from segmented_spin_box import upgrade_spinbox, style_segmented_spinbox

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mockups'))
os.makedirs(OUT, exist_ok=True)
THEME = 'default'

# WidthConfigDialog default-theme stylesheet (numbered_layer_button.py:4070-4138), verbatim
# apart from the section frame used to group the controls.
LIGHT = """
QDialog { background-color: #F5F5F5; color: black; }
QLabel { color: black; }
QLineEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #CCCCCC; border-radius: 4px; padding: 2px 4px; }
QPushButton, QDialogButtonBox QPushButton { background-color: #F0F0F0; color: #000000; border: 1px solid #BBBBBB; border-radius: 5px; padding: 10px; min-width: 80px; font-weight: bold; }
QPushButton:hover, QDialogButtonBox QPushButton:hover { background-color: #E0E0E0; }
QPushButton:pressed, QDialogButtonBox QPushButton:pressed { background-color: #D0D0D0; }
QToolButton { background-color: #FFFFFF; color: black; border: 1px solid #CCC; border-radius: 5px; padding: 4px; }
QToolButton:checked { background-color: #A0C0E0; border: 2px solid #7090C0; }
QToolButton:hover { border: 1px solid #999; }
QFrame#section { background-color: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 6px; }
QLabel#sectionTitle { font-weight: bold; color: #333; }
QLabel#hint { color: #666; }
"""


def app_checkbox(text, checked, enabled=True):
    """The Create Mask Grid dialog's checkbox, built with its own helpers."""
    cb = QCheckBox(text)
    cb.setChecked(checked); cb.setEnabled(enabled)
    # same proxy the app installs, on a private base style so nothing shared gets owned/deleted
    cb.setStyle(LargeIndicatorStyle(QStyleFactory.create('Fusion'), 20)); cb.setMinimumHeight(26)
    MaskGridDialog._setup_custom_checkmark(None, cb)
    MaskGridDialog._style_mask_checkbox(None, cb, False, enabled, 8)
    return cb


def app_stepper(value, lo, hi, suffix=''):
    """The Settings dialog's segmented [ - | value | + ] spin box."""
    sp = QSpinBox(); sp.setRange(lo, hi); sp.setValue(value)
    if suffix:
        sp.setSuffix(suffix)
    upgrade_spinbox(sp)
    style_segmented_spinbox(sp, THEME, False)
    return sp


def slider_row(label_text, lo, hi, value, fmt, enabled=True):
    """A Move Group dialog row: label (min 100) / QSlider / value label (min 30) / QLineEdit (max 60)."""
    row = QHBoxLayout()
    lab = QLabel(label_text); lab.setMinimumWidth(100)
    sl = QSlider(Qt.Horizontal); sl.setRange(lo, hi); sl.setValue(value)
    val = QLabel(fmt(value)); val.setMinimumWidth(30)
    inp = QLineEdit(); inp.setValidator(QIntValidator(lo, hi)); inp.setText(str(value)); inp.setMaximumWidth(60)
    for w in (lab, sl, val, inp):
        w.setEnabled(enabled)
    row.addWidget(lab); row.addWidget(sl); row.addWidget(val); row.addWidget(inp)
    return row


def shape_icon(shape, amount=0.5, tilt=0.0, size=(56, 34)):
    """Tiny real-geometry icon of a strand end for the shape picker."""
    w, h = size
    img = QImage(w * 2, h * 2, QImage.Format_ARGB32_Premultiplied); img.fill(Qt.transparent)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(2, 2)
    s = Strand(QPointF(-30, h / 2), QPointF(w - 16, h / 2), 16, QColor(200, 170, 230), QColor(0, 0, 0), 2)
    s.control_point1 = QPointF(-10, h / 2); s.control_point2 = QPointF(w - 30, h / 2)
    s.update_shape(); s.update_side_line()
    geo = styled_end_geometry(s, 1, dict(shape=shape, amount=amount, tilt=tilt))
    paint_styled(p, s, geo)
    p.end()
    return QIcon(QPixmap.fromImage(img))


def preview_pixmap(style, side_color=None, w=380, h=120):
    img = QImage(w * 2, h * 2, QImage.Format_ARGB32_Premultiplied); img.fill(QColor(255, 255, 255))
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(2, 2)
    p.setPen(QPen(QColor(0, 0, 0, 18), 1))
    for gx in range(0, w, 27): p.drawLine(gx, 0, gx, h)
    for gy in range(0, h, 27): p.drawLine(0, gy, w, gy)
    under = make_strand((w - 95, -10), (w - 95, h + 10), (w - 95, 30), (w - 95, 90), (120, 200, 170))
    under.draw(p)
    s = make_strand((-40, h / 2), (w - 88, h / 2), (60, h / 2 - 30), (w - 150, h / 2 + 30), (200, 170, 230))
    s.has_circles = [True, False]
    geo = styled_end_geometry(s, 1, style)
    p.save(); p.setClipPath(_stroked(under))
    for j in range(3):
        p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 30)); p.drawPath(dilate(geo['outer'], 20 - j * 6))
    p.restore()
    paint_styled(p, s, geo, side_color)
    p.setPen(QPen(QColor(59, 164, 36), 1.5, Qt.DashLine)); p.setBrush(Qt.NoBrush); p.drawEllipse(s.end, 6, 6)
    p.end()
    pm = QPixmap.fromImage(img); pm.setDevicePixelRatio(2)
    return pm


def section(title):
    f = QFrame(); f.setObjectName('section')
    v = QVBoxLayout(f); v.setContentsMargins(12, 10, 12, 12); v.setSpacing(8)
    t = QLabel(title); t.setObjectName('sectionTitle'); v.addWidget(t)
    return f, v


def build_dialog(state):
    d = QDialog(); d.setWindowTitle('Stylize End Side'); d.setStyleSheet(LIGHT)
    d.setMinimumWidth(640)
    root = QVBoxLayout(d); root.setSpacing(10)

    head = QLabel(f"Layer <b>{state['layer']}</b> — <b>{state['side']}</b> side")
    root.addWidget(head)

    # Preview
    pf, pv = section('Preview')
    pl = QLabel(); pl.setPixmap(preview_pixmap(state['style'], state.get('side_color')))
    pl.setAlignment(Qt.AlignCenter); pv.addWidget(pl)
    hint = QLabel('Changes show on the canvas immediately. Cancel puts the end back exactly as it was.')
    hint.setObjectName('hint'); hint.setWordWrap(True); pv.addWidget(hint)
    root.addWidget(pf)

    # End shape
    sf, sv = section('End Shape')
    row = QHBoxLayout(); row.setSpacing(6)
    group = QButtonGroup(d); group.setExclusive(True)
    shapes = [('flat', 'Straight'), ('angled', 'Angled'), ('rounded', 'Rounded'),
              ('pointed', 'Pointed'), ('notched', 'Notched'), ('concave', 'Concave')]
    for key, text in shapes:
        b = QToolButton(); b.setCheckable(True); b.setText(text)
        b.setIcon(shape_icon(key, 0.6, 30 if key == 'angled' else 0)); b.setIconSize(QSize(56, 34))
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon); b.setFixedSize(92, 76)
        b.setChecked(key == state['style']['shape'])
        group.addButton(b); row.addWidget(b)
    sv.addLayout(row)

    st = state['style']
    sv.addLayout(slider_row('Tilt', -60, 60, int(st.get('tilt', 0)), lambda v: f"{v:+d}°"))
    depth_enabled = st['shape'] in ('rounded', 'pointed', 'notched', 'concave')
    sv.addLayout(slider_row('Depth', 0, 100, int(st.get('amount', 0.5) * 100), lambda v: f"{v} %", depth_enabled))

    ext_row = QHBoxLayout()
    el = QLabel('Extend / Trim'); el.setMinimumWidth(100); ext_row.addWidget(el)
    ext_row.addWidget(app_stepper(int(st.get('offset', 0)), -54, 108)); ext_row.addWidget(QLabel('px'))
    ext_row.addStretch()
    sv.addLayout(ext_row)
    eh = QLabel('+ extends past the endpoint, − trims. The endpoint itself never moves.')
    eh.setObjectName('hint'); eh.setWordWrap(True); sv.addWidget(eh)
    root.addWidget(sf)

    # Side line
    lf, lv = section('Side Line')
    lv.addWidget(app_checkbox('Show side line', state.get('line_visible', True)))
    th_row = QHBoxLayout()
    tl = QLabel('Thickness'); tl.setMinimumWidth(100); th_row.addWidget(tl)
    th_row.addWidget(app_stepper(state.get('line_width', 4), 1, 40)); th_row.addWidget(QLabel('px')); th_row.addStretch()
    lv.addLayout(th_row)
    c_row = QHBoxLayout()
    cl = QLabel('Color'); cl.setMinimumWidth(100); c_row.addWidget(cl)
    swatch = QPushButton(); swatch.setFixedSize(44, 28)
    c = state.get('side_color') or QColor(0, 0, 0)
    swatch.setStyleSheet(f'background-color: {c.name()}; border: 1px solid #666; border-radius: 3px; min-width: 0; padding: 0;')
    c_row.addWidget(swatch); c_row.addSpacing(12)
    c_row.addWidget(app_checkbox('Use stroke color', state.get('side_color') is None)); c_row.addStretch()
    lv.addLayout(c_row)
    root.addWidget(lf)

    if state.get('two_free_ends'):
        root.addWidget(app_checkbox('Apply to both free ends', False))

    br = QHBoxLayout()
    reset = QPushButton('Reset to Straight'); br.addWidget(reset); br.addStretch()
    ok = QPushButton('OK'); cancel = QPushButton('Cancel'); br.addWidget(ok); br.addWidget(cancel)
    root.addLayout(br)
    return d


_keep = []
def grab(widget, name):
    _keep.append(widget)
    widget.show(); app.processEvents()
    widget.layout().activate(); widget.adjustSize(); app.processEvents(); app.processEvents()
    widget.resize(widget.sizeHint()); app.processEvents()
    pm = widget.grab(); path = os.path.join(OUT, name); pm.save(path); widget.hide()
    print('wrote', path, pm.width(), pm.height())


if __name__ == '__main__':
    grab(build_dialog(dict(layer='1_2', side='End', style=dict(shape='pointed', amount=0.5, tilt=15, offset=0),
                           line_visible=True, line_width=4, side_color=None, two_free_ends=False)),
         'dialog_pointed.png')
    grab(build_dialog(dict(layer='1_1', side='Start', style=dict(shape='angled', tilt=-35, offset=12),
                           line_visible=True, line_width=6, side_color=QColor(190, 40, 40), two_free_ends=True)),
         'dialog_angled_two_ends.png')
    grab(build_dialog(dict(layer='1_2', side='End', style=dict(shape='flat', tilt=0, offset=0),
                           line_visible=True, line_width=4, side_color=None, two_free_ends=False)),
         'dialog_default.png')
