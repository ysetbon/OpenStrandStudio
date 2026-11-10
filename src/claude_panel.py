"""Claude in the app: the box floating over the canvas, the Claude button
next to Settings that shows and hides it, and the Settings > Claude page.

The panel sends a request to the openstrand agent (python -m openstrand agent),
which runs in its own background process with the user's API key and model
from Settings > Claude. Its progress arrives as JSON lines; when it finishes,
the design opens in a new tab through MainWindow.load_project_file, the same
path as Load, so strands, masks, groups and the layer panel come out as in
any saved project. With "Start from the canvas" the current canvas goes to
the agent as its starting design.
"""
import html
import json
import logging
import math
import os
import re
import shutil
import sys
import threading
import time
from contextlib import contextmanager

from PyQt5.QtCore import (QDate, QEvent, QLocale, QPoint, QPointF, QProcess, QProcessEnvironment, QRect,
                          QRectF, QSize, Qt, QTimer, QUrl, pyqtSignal)
from PyQt5.QtGui import (QColor, QDesktopServices, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QRegion,
                         QTextDocument)
from PyQt5.QtWidgets import (QAction, QActionGroup, QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                             QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QToolButton, QSizePolicy, QStyle,
                             QStyleOptionComboBox, QTextBrowser, QTextEdit, QVBoxLayout,
                             QWidget)

import claude_settings
import claude_sharing
from translations import translations

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each tool shows as a chip in the colors of the app's own button for that job.
TOOL_CHIPS = {
    'make_turks_head': ('add_new_strand', '#93e993', '#1a1a1a'),
    'make_mxn': ('add_new_strand', '#93e993', '#1a1a1a'),
    'make_heart': ('add_new_strand', '#93e993', '#1a1a1a'),
    'draw_design': ('add_new_strand', '#93e993', '#1a1a1a'),
    'load_sample': ('load', '#a07a6a', '#1a1a1a'),
    'search_samples': ('load', '#a07a6a', '#1a1a1a'),
    'render': ('save_image', '#8a3a55', '#ffffff'),
    'make_steps': ('add_new_strand', '#93e993', '#1a1a1a'),
    # The app's own tabs, through the bridge: the colors of the Tabs button.
    'list_tabs': ('tabs', '#a04f9a', '#ffffff'),
    'read_tab': ('tabs', '#a04f9a', '#ffffff'),
    'open_in_new_tab': ('tabs', '#a04f9a', '#ffffff'),
    'rename_tab': ('tabs', '#a04f9a', '#ffffff'),
    'switch_tab': ('tabs', '#a04f9a', '#ffffff'),
    'edit_mask_in_tab': ('claude_tool_edit_mask', '#a04f9a', '#ffffff'),
    'read_tab_step': ('tabs', '#a04f9a', '#ffffff'),
    'edit_strand_in_tab': ('claude_tool_edit_strand', '#a04f9a', '#ffffff'),
    # The layer panel's right-click menu, the group panel, the main window and Settings.
    'edit_layers_in_tab': ('claude_tool_layers', '#a04f9a', '#ffffff'),
    'edit_groups_in_tab': ('claude_tool_groups', '#a04f9a', '#ffffff'),
    'show_group': ('claude_tool_groups', '#a04f9a', '#ffffff'),
    'app_window': ('claude_tool_window', '#a04f9a', '#ffffff'),
    'app_settings': ('claude_tool_settings', '#a04f9a', '#ffffff'),
    'read_settings': ('claude_tool_settings', '#a04f9a', '#ffffff'),
    # Knots and masks: tie_knot makes a design, the others look and fix.
    'tie_knot': ('claude_tool_tie_knot', '#93e993', '#1a1a1a'),
    'check_masks': ('claude_tool_check_masks', '#d4d4d4', '#1a1a1a'),
    'edit_mask': ('claude_tool_edit_mask', '#d4d4d4', '#1a1a1a'),
    'identify_knot': ('claude_tool_identify_knot', '#d4d4d4', '#1a1a1a'),
    'knot_library': ('claude_tool_knot_library', '#d4d4d4', '#1a1a1a'),
}
OTHER_CHIP = ('#d4d4d4', '#1a1a1a')
ACCENT = '#D97757'  # Claude's orange: the running mark and the progress bars
# A running tool's row: the picture of what it works on, and its progress bar (px).
FRAME_SIZE = (132, 78)
BAR_SIZE = (170, 8)
# The picture under the mouse, larger: about 2.7 times the row's, the same
# shape, big enough to follow every crossing and small enough to leave the
# conversation in view.
PREVIEW_SIZE = (360, 213)
# App tools whose finished row shows the app as they left it (the agent sends the
# picture for its own tools, see openstrand.agent.IMAGE_TOOLS): the canvas after an
# edit or a view change, the group panel, the window after a setting (the settings
# dialog when it was opened). Lists and readings get no picture.
CANVAS_TOOLS = {'open_in_new_tab', 'switch_tab', 'edit_strand_in_tab', 'edit_mask_in_tab', 'edit_layers_in_tab',
                'edit_groups_in_tab', 'app_window'}
# The automatic Refresh models: once a day, checked hourly, first a little after the app starts.
AUTO_REFRESH_HOURS = 24
AUTO_REFRESH_CHECK_MS = 60 * 60 * 1000
AUTO_REFRESH_FIRST_MS = 15 * 1000
# Tools that can take up to a minute: the panel says so when they start.
SLOW_TOOLS = {'draw_design', 'make_heart', 'make_turks_head'}


def _tr(language, key):
    table = translations.get(language) or translations['en']
    return table.get(key) or translations['en'].get(key, key)


# An Allow/Deny card's words, by the bridge action that asks (src/claude_bridge).
CONFIRM_KEYS = {'rename_tab': 'claude_confirm_rename', 'edit_mask': 'claude_confirm_mask',
                'edit_strand': 'claude_confirm_strand', 'edit_layers': 'claude_confirm_layers',
                'edit_groups': 'claude_confirm_groups', 'window': 'claude_confirm_window',
                'settings': 'claude_confirm_settings'}


def confirm_text(language, what):
    """'Claude wants to delete 1_5, 2_5 (tab “Ring”).': what an Allow/Deny card asks."""
    action, current, new = what
    return _tr(language, CONFIRM_KEYS.get(action, 'claude_confirm_switch')).format(old=current, new=new)


def model_tags(model, t):
    """'new · price estimated', 'retiring 2026-12-01'... for a model in the menus."""
    info = claude_settings.model_info(model)
    if info is None:
        return ''
    tags = [t('models_tag_new')] if info.new else []
    if info.estimated:
        tags.append(t('models_tag_estimated'))
    if info.retiring:
        tags.append(t('models_tag_retiring_soon') if info.retiring == 'soon'
                    else t('models_tag_retiring').format(date=info.retiring))
    return ' · '.join(tags)


def menu_style(theme):
    """The drop-downs drawn like the layer panel's menus: the theme's menu colors, and the
    row under the mouse in the opposite ones (dark on light, light on dark)."""
    if str(theme).lower() == 'dark':
        bg, fg, sel_bg, sel_fg = '#333333', '#FFFFFF', '#F0F0F0', '#000000'
    else:
        bg, fg, sel_bg, sel_fg = '#F0F0F0', '#000000', '#333333', '#FFFFFF'
    return (f'QMenu {{ background-color: {bg}; color: {fg}; border: 1px solid {sel_bg}; padding: 2px 0px; }}'
            f'QMenu::item {{ background-color: transparent; color: {fg}; padding: 5px 24px 5px 22px; }}'
            f'QMenu::item:selected {{ background-color: {sel_bg}; color: {sel_fg}; }}'
            f'QMenu::item:disabled {{ color: #888888; }}'
            f'QMenu::separator {{ height: 1px; background: #888888; margin: 3px 6px; }}')


def short_provider_name(name):
    """'Anthropic' for 'Anthropic (Claude)': the company alone, for the status line."""
    return name.split(' (')[0]


def mode_icon(mode, theme):
    """The mode's symbol (ask: one arrow, auto: two, plan: pause) in its color for the theme."""
    shade = 'dark' if str(theme).lower() == 'dark' else 'light'
    return QIcon(resource_path(os.path.join('images', f'mode_{mode}_on_{shade}.png')))


def icon_path(name):
    """A picture in images/, as a style sheet url() wants it (forward slashes on Windows too)."""
    return resource_path(os.path.join('images', name)).replace('\\', '/')


def shade_of(theme):
    """'dark' on the dark theme, 'light' on the default and light themes: which picture to use."""
    return 'dark' if str(theme).lower() == 'dark' else 'light'


def image_icon(theme):
    """The Image button's picture: images/image_icon_*.png, white on the dark theme, black otherwise."""
    name = 'image_icon_white.png' if str(theme).lower() == 'dark' else 'image_icon_black.png'
    return QIcon(resource_path(os.path.join('images', name)))


def agent_command(prompt, model, out_dir, images=(), start=None, web=True, max_cost=None, effort=None,
                  plan=False, app=False, history=None):
    """The program and arguments that run one agent request."""
    # --log: the agent's step-by-step log on stderr, which the panel prints in the terminal (terminal_log).
    args = ['-m', 'openstrand', 'agent', prompt, '--model', model, '--out-dir', out_dir, '--json-events', '--log']
    if history:  # the session so far: Claude remembers it
        args += ['--history', history]
    if app:  # the app answers its tab tools through the bridge
        args.append('--app')
    if not web:
        args.append('--no-web')
    if effort:
        args += ['--effort', effort]
    if plan:
        args.append('--plan')
    if max_cost is not None:
        args += ['--max-cost', f'{max_cost:.2f}']
    for image in images:
        args += ['--image', image]
    if start:
        args += ['--start', start]
    return sys.executable, args


def duration_text(seconds, t):
    """'12s', '5m 39s', as the language writes them (t: the panel's translate)."""
    s = max(0, int(round(seconds)))
    if s < 60:
        return t('claude_seconds').format(n=s)
    return t('claude_minutes').format(m=s // 60, s=s % 60)


def paint_bar(painter, rect, fraction, track, fill, phase=0.0):
    """A rounded progress bar in rect. fraction None: the total is not known,
    so a piece slides along it (phase 0 to 1) to show the tool is working."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    radius = rect.height() / 2
    painter.setBrush(QColor(track))
    painter.drawRoundedRect(rect, radius, radius)
    if fraction is None:
        size = rect.width() * 0.3
        left = rect.left() + (rect.width() + size) * (phase % 1.0) - size
        piece = QRectF(left, rect.top(), size, rect.height()).intersected(rect)
    elif fraction > 0:
        piece = QRectF(rect.left(), rect.top(), max(rect.height(), rect.width() * min(1.0, fraction)), rect.height())
    else:
        piece = None
    if piece is not None and piece.width() > 0:
        painter.setBrush(QColor(fill))
        painter.drawRoundedRect(piece, radius, radius)
    painter.restore()


def bar_image(fraction, track, fill, phase=0.0, size=BAR_SIZE, ratio=2.0):
    image = QImage(int(size[0] * ratio), int(size[1] * ratio), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(ratio)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    paint_bar(painter, QRectF(0, 0, size[0], size[1]), fraction, track, fill, phase)
    painter.end()
    return image


def frame_image(frame, size=FRAME_SIZE, ratio=2.0):
    """The picture a tool sends with its progress (openstrand.progress.picture),
    drawn small: each cord with a darker edge, then the over part of every
    crossing again on top, so over and under read as in the app."""
    image = QImage(int(size[0] * ratio), int(size[1] * ratio), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(ratio)
    image.fill(Qt.transparent)
    cords = [c for c in frame.get('cords') or [] if len(c.get('points') or []) >= 2]
    if not cords:
        return image
    xs = [p[0] for c in cords for p in c['points']]
    ys = [p[1] for c in cords for p in c['points']]
    wide, tall = max(xs) - min(xs), max(ys) - min(ys)
    cord_width = float(frame.get('width') or 20)
    room_w, room_h = size[0] - 6, size[1] - 6
    scale = min(room_w / max(wide + cord_width, 1e-6), room_h / max(tall + cord_width, 1e-6))
    pen_width = max(1.6, cord_width * scale)
    middle = QPointF((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
    centre = QPointF(size[0] / 2, size[1] / 2)

    def path(points, closed=False):
        made = QPainterPath(centre + (QPointF(*points[0]) - middle) * scale)
        for p in points[1:]:
            made.lineTo(centre + (QPointF(*p) - middle) * scale)
        if closed:
            made.closeSubpath()
        return made

    def stroke(painter, made, color, cap):
        # The edge with cap; the body round-ended, so a redrawn over part
        # covers the seam where it ends (same color as the cord under it).
        for pen_color, width, end in ((QColor(color).darker(175), pen_width + 1.6, cap),
                                      (QColor(color), pen_width, Qt.RoundCap)):
            pen = QPen(pen_color, width)
            pen.setCapStyle(end)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(made)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    for c in cords:
        stroke(painter, path(c['points'], c.get('closed')), c.get('color') or ACCENT, Qt.RoundCap)
    for over in frame.get('overs') or []:
        k = over.get('cord', 0)
        if 0 <= k < len(cords) and len(over.get('points') or []) >= 2:
            stroke(painter, path(over['points']), cords[k].get('color') or ACCENT, Qt.FlatCap)
    painter.end()
    return image


def fitted_image(source, size=FRAME_SIZE, ratio=2.0):
    """A finished tool's picture (a PNG's path, or a QImage), fitted into size, its
    shape kept, centred on a clear background."""
    image = QImage(int(size[0] * ratio), int(size[1] * ratio), QImage.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(ratio)
    image.fill(Qt.transparent)
    picture = source if isinstance(source, QImage) else QImage(str(source or ''))
    if picture.isNull():
        return image
    scaled = picture.scaled(int(size[0] * ratio), int(size[1] * ratio), Qt.KeepAspectRatio, Qt.SmoothTransformation)
    scaled.setDevicePixelRatio(ratio)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.drawImage(QPointF((size[0] - scaled.width() / ratio) / 2, (size[1] - scaled.height() / ratio) / 2), scaled)
    painter.end()
    return image


def picture_image(source, size):
    """Any tool picture drawn at size: a progress frame (a dict) or a finished picture."""
    return frame_image(source, size) if isinstance(source, dict) else fitted_image(source, size)


LOG_PREFIX = 'log '  # the agent's log lines (openstrand/debuglog.py)


def terminal_log(text):
    """A line in the terminal the app was started from, for debugging Claude."""
    out = sys.__stderr__
    if out is None:  # no console (pythonw, a packaged app)
        return
    try:
        print(f'[Claude] {text}', file=out, flush=True)
    except (OSError, ValueError):
        pass


def money(value):
    """$0.041 for small amounts, $12.50 once it is over a dollar."""
    return f'${value:.2f}' if value >= 1 else f'${value:.3f}'


def lines(text):
    """Text for the transcript's HTML, keeping its line breaks (numbered plans, paragraphs)."""
    return html.escape(text.strip()).replace('\n', '<br>')


def short_url(url):
    """'animatedknots.com/butterfly-stitch' from a full link."""
    url = re.sub(r'^https?://(www\.)?', '', url or '')
    return url if len(url) <= 48 else url[:47] + '…'


def design_name(prompt):
    """A file name from the request: '5x3 bracelet in teal' -> '5x3_bracelet_in_teal'."""
    words = re.findall(r'[\w×]+', prompt.lower(), re.UNICODE)[:6]
    return '_'.join(words).replace('×', 'x')[:48] or 'claude_design'


class PromptBox(QTextEdit):
    """The chat box: Enter sends, Shift+Enter starts a new line, and the box
    grows with what is typed up to MAX_LINES, then scrolls."""
    submitted = pyqtSignal()
    cycle_mode = pyqtSignal()  # Shift+Tab, as in Claude Code
    MAX_LINES = 8

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)  # pasted text arrives plain
        self.setTabChangesFocus(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setObjectName('claudePrompt')
        self.setStyleSheet('QTextEdit#claudePrompt { border: 1px solid palette(mid); border-radius: 8px;'
                           ' padding: 4px 6px; }'  # colors come from the app's theme
                           'QTextEdit#claudePrompt:focus { border-color: #d97757; }')
        self.document().setDocumentMargin(2)
        self.document().contentsChanged.connect(self.fit_height)
        self.fit_height()

    # The QLineEdit calls the rest of the panel and the tests use.
    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)
        self.moveCursor(self.textCursor().End)

    def event(self, event):
        # Shift+Tab switches the mode; caught before Qt moves the focus with it.
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backtab:
            self.cycle_mode.emit()
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.textCursor().insertText('\n')
            else:
                self.submitted.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_height()

    def line_height(self):
        return self.fontMetrics().lineSpacing()

    def fit_height(self):
        doc = self.document()
        doc.setTextWidth(self.viewport().width())
        # Whatever the style puts around the text: frame, border, padding.
        frame = self.height() - self.viewport().height()
        content = doc.size().height()
        most = self.MAX_LINES * self.line_height() + 2 * doc.documentMargin()
        height = int(min(max(content, self.line_height() + 2 * doc.documentMargin()), most)) + frame
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if content > most else Qt.ScrollBarAlwaysOff)
        if height != self.height():
            self.setFixedHeight(height)
        self.ensureCursorVisible()


def load_knot():
    """The working line's knot: a closed overhand knot drawn strand by strand
    by OpenStrand Studio (scripts/build_knot_spinner.py), as frames and how
    long each shows. Empty when the files are missing."""
    try:
        with open(resource_path('claude_knot.json'), encoding='utf-8') as f:
            info = json.load(f)
        strip = QPixmap(resource_path('claude_knot.png'))
        size, durations = int(info['frame']), [int(d) for d in info['durations_ms']]
    except (OSError, ValueError, KeyError, TypeError):
        return [], []
    if strip.isNull() or strip.width() < size * len(durations):
        return [], []
    return [strip.copy(i * size, 0, size, size) for i in range(len(durations))], durations


class FramePreview(QLabel):
    """A running tool's picture, larger, while the mouse is over it in the
    conversation. Drawn again from each new frame, so it moves with the tool."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAlignment(Qt.AlignCenter)
        self.key = None  # the step whose picture it shows

    def style_for(self, colors):
        self.setStyleSheet(f"QLabel {{ background-color: {colors['log']}; border: 1px solid {colors['border']};"
                           " border-radius: 8px; padding: 6px; }")

    def show_frame(self, key, frame, cursor):
        """frame: the tool's picture (progress data, or a finished picture's path);
        cursor: the mouse, in screen coordinates."""
        self.key = key
        self.setPixmap(QPixmap.fromImage(picture_image(frame, PREVIEW_SIZE)))
        self.adjustSize()
        # Above the mouse (Claude sits at the bottom of the canvas), kept on screen.
        screen = QApplication.screenAt(cursor) or QApplication.primaryScreen()
        area = screen.availableGeometry() if screen is not None else QRect(0, 0, 10000, 10000)
        x = min(max(area.left(), cursor.x() - self.width() // 2), area.right() - self.width())
        y = cursor.y() - self.height() - 16
        if y < area.top():
            y = cursor.y() + 20
        self.move(x, y)
        self.show()
        self.raise_()

    def update_frame(self, frame):
        self.setPixmap(QPixmap.fromImage(picture_image(frame, PREVIEW_SIZE)))

    def hide_frame(self):
        self.key = None
        self.hide()


class WorkingLine(QWidget):
    """Claude at work, the OpenStrand way: a closed overhand knot drawn strand
    by strand, over and over, then what Claude is doing, how far a long tool
    has got (a bar, how much is left) and the time so far. (Without its
    frames it falls back to a turning trefoil.)"""

    SIZE = 28  # px of the knot

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.frames, self.durations = load_knot()
        self.frame = 0
        self.label = ''
        self.started = time.monotonic()
        self.phase = 0.0
        self.text_color = QColor('#FFFFFF')
        self.muted = QColor('#9A9A9A')
        self.track = QColor('#5A5A5A')
        self.progress = None  # (fraction or None, text) while a tool says how far it has got
        self.format_time = lambda seconds: f'{int(seconds)}s'  # the panel gives the language's
        # The trefoil: x = sin t + 2 sin 2t, y = cos t - 2 cos 2t, fitted to SIZE.
        n = 150
        self.points = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x, y = math.sin(t) + 2 * math.sin(2 * t), math.cos(t) - 2 * math.cos(2 * t)
            self.points.append(QPointF(x, y))
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.tick)
        self.hide()

    def start(self, label):
        self.label, self.started = label, time.monotonic()
        self.progress = None
        self.frame = 0
        self.show()
        self.timer.start(self.durations[0] if self.durations else 40)

    def set_label(self, label):
        self.label = label
        self.update()

    def set_progress(self, fraction, text):
        """A long tool's progress: fraction (None while it cannot tell) and
        what to say after the bar ("58% · about 20s left")."""
        self.progress = (fraction, text)
        self.update()

    def clear_progress(self):
        self.progress = None
        self.update()

    def stop(self):
        self.timer.stop()
        self.hide()

    def tick(self):
        self.phase = (self.phase + 0.012) % 1.0
        if self.frames:
            self.frame = (self.frame + 1) % len(self.frames)
            self.timer.setInterval(self.durations[self.frame])
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        box = self.SIZE
        if self.frames:
            pixmap = self.frames[self.frame]
            painter.drawPixmap(QRectF(2, (self.height() - box) / 2, box, box), pixmap, QRectF(pixmap.rect()))
        else:
            self.draw_trefoil(painter, box)
        self.draw_label(painter, box)
        painter.end()

    def draw_trefoil(self, painter, box):
        painter.save()
        painter.translate(2 + box / 2, self.height() / 2)
        painter.rotate(self.phase * 120)  # a slow turn
        painter.scale(box / 6.4, box / 6.4)
        orange = QColor('#D97757')
        dim = QColor(orange)
        dim.setAlpha(110)
        path = QPainterPath(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        path.closeSubpath()
        pen = QPen(dim, 0.55)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
        # The bright stretch running along the cord.
        n = len(self.points)
        head = int(self.phase * 3 * n) % n
        run = QPainterPath(self.points[(head - 50) % n])
        for k in range(-49, 1):
            run.lineTo(self.points[(head + k) % n])
        pen = QPen(orange, 0.85)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(run)
        painter.restore()

    BAR = 96  # px of the progress bar

    def draw_label(self, painter, box):
        x = box + 12
        metrics = painter.fontMetrics()
        elapsed = self.format_time(time.monotonic() - self.started)
        tail = metrics.horizontalAdvance(elapsed) + 4
        room = self.width() - x - tail - 10
        fraction, text = self.progress if self.progress else (None, '')
        # The bar and its text first; the label gets what is left (at least 60 px).
        bar = self.BAR + 10 if self.progress and room > self.BAR + 140 else 0
        text = metrics.elidedText(text, Qt.ElideRight, max(0, room - bar - 70)) if bar else ''
        extra = bar + (metrics.horizontalAdvance(text) + 10 if text else 0)
        label = metrics.elidedText(self.label, Qt.ElideRight, max(60, room - extra))
        painter.setPen(self.text_color)
        painter.drawText(QRectF(x, 0, self.width() - x, self.height()), Qt.AlignVCenter, label)
        x += metrics.horizontalAdvance(label) + 10
        if bar:
            paint_bar(painter, QRectF(x, (self.height() - 6) / 2, self.BAR, 6), fraction, self.track, ACCENT,
                      self.phase * 4)
            x += bar
            if text:
                painter.setPen(self.muted)
                painter.drawText(QRectF(x, 0, metrics.horizontalAdvance(text) + 4, self.height()),
                                 Qt.AlignVCenter, text)
                x += metrics.horizontalAdvance(text) + 10
        painter.setPen(self.muted)
        painter.drawText(QRectF(x, 0, tail + 8, self.height()), Qt.AlignVCenter, elapsed)


class ClaudePanel(QWidget):
    """Claude, floating over the bottom of the canvas: the conversation, the
    chat box and its buttons. The Claude button next to Settings shows and
    hides it."""

    design_ready = pyqtSignal(str)  # path of the finished project file
    spending_changed = pyqtSignal()  # a request's cost was added to the saved total
    open_changed = pyqtSignal(bool)  # Claude was shown or hidden
    activity_changed = pyqtSignal()  # a run started or ended: the Claude button shows it
    models_fetched = pyqtSignal(object)  # the daily, silent Refresh models: what the providers said
    MARGIN = 12  # px between Claude and the canvas edges

    def __init__(self, main_window, canvas=None, language_code='en'):
        # Claude floats over the bottom of the canvas: a child of the canvas,
        # so the canvas keeps its size and the drawing never moves.
        super().__init__(canvas if canvas is not None else main_window)
        # Its own arrow: as a child of the canvas it would show the canvas mode's cursor
        # (a cross, an open hand) over the conversation and its buttons.
        self.setCursor(Qt.ArrowCursor)
        self.main_window = main_window
        self.language = language_code
        self.process = None
        self.run_cost, self.total_before = 0.0, claude_settings.load()['spent']
        self.design_waiting = False  # a design opened while Claude was hidden
        self.image_path = None
        self.out_dir = None
        self.prompt = ''
        self.done_event = None
        self.stdout_buffer = b''
        self.stderr_text = ''
        self.entries = []  # the conversation: drawn as HTML each time it changes
        # The conversation keeps its newest line in view (where an Allow/Deny card waits),
        # unless the person scrolled up to read: then it stays where they put it.
        self.follow_end = True
        self.kept_scroll = 0
        self.scrolling = False  # the panel moves the scroll bar itself: not the person scrolling
        self.bridge = None  # set by the main window: Claude's tab tools run through it
        # The session: what was asked and answered so far, sent with each request
        # so Claude remembers it. "New session" (or /clear, /new) starts again.
        self.history = []
        self.shown_prompt = ''
        self.run_design = None
        self.session_spent = 0.0  # since the app opened; held to the session limit
        self.mode = claude_settings.load()['mode']  # 'ask', 'auto', or 'plan' (never saved)
        self.last_mode = self.mode
        self.run_mode = self.mode
        self.run_texts = []
        self.run_files = (None, None)  # the design this request made, and its picture (in out_dir)
        self.share_asked = False  # whether to share with the developer: asked once while the app runs
        self.shared_event = None  # the request last shared (or asked about): each one goes once
        self.stopping = False  # the person pressed Stop: the run ends without an answer, as asked
        self.step_keys = 0  # each tool step's pictures get their own name in the transcript
        # While a tool runs, its row's time and time left move on every second.
        self.tick = QTimer(self)
        self.tick.setInterval(1000)
        self.tick.timeout.connect(self.refresh_running)
        # Refresh models on its own once a day, silently: shortly after the app starts,
        # then checked every hour while it stays open. No window, no note: the lists update.
        self.models_fetched.connect(self.apply_fetched_models)
        self.fetching_models = False
        self.model_clock = QTimer(self)
        self.model_clock.setInterval(AUTO_REFRESH_CHECK_MS)
        self.model_clock.timeout.connect(self.auto_refresh_models)
        self.model_clock.start()
        QTimer.singleShot(AUTO_REFRESH_FIRST_MS, self.auto_refresh_models)
        self._build()
        self.setVisible(False)  # closed each time the app starts: the Claude button opens it
        self.retranslate(language_code)

    # ------------------------------------------------------------------ UI
    def _build(self):
        self.setObjectName('claudePanel')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.apply_theme(getattr(self.main_window, 'current_theme', 'default'))
        self.body = self
        body = QVBoxLayout(self)
        body.setContentsMargins(8, 8, 8, 8)
        body.setSpacing(6)
        # The conversation shows above the box once there is one.
        self.transcript = QTextBrowser(self)
        self.transcript.setOpenLinks(False)  # its links fold steps, open designs, build plans
        self.transcript.anchorClicked.connect(self.follow_link)
        # A running tool's picture grows under the mouse (FramePreview).
        self.preview = FramePreview(self)
        self.preview.style_for(self.colors)
        self.transcript.viewport().setMouseTracking(True)
        self.transcript.viewport().installEventFilter(self)
        self.transcript.setMinimumHeight(60)
        self.transcript.setMaximumHeight(170)
        bar = self.transcript.verticalScrollBar()
        bar.rangeChanged.connect(self.keep_scroll)
        bar.valueChanged.connect(self.scrolled)
        self.transcript.hide()
        body.addWidget(self.transcript)
        self.working = WorkingLine(self)
        body.addWidget(self.working)

        self.image_row = QWidget(self)
        image_row = QHBoxLayout(self.image_row)
        image_row.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(self.image_row)
        self.remove_image_button = QPushButton(self.image_row)
        self.remove_image_button.clicked.connect(lambda: self.set_image(None))
        image_row.addWidget(self.image_label)
        image_row.addWidget(self.remove_image_button)
        image_row.addStretch()
        body.addWidget(self.image_row)

        self.prompt_edit = PromptBox(self)
        self.prompt_edit.submitted.connect(self.send)
        self.prompt_edit.cycle_mode.connect(self.cycle_mode)
        self.attach_button = QPushButton(self)
        self.attach_button.setObjectName('claudeChip')
        self.attach_button.clicked.connect(self.choose_image)
        # A toggle like the toolbar's (Points, Shadow): a black frame while on.
        self.use_canvas_check = QPushButton(self)
        self.use_canvas_check.setObjectName('claudeToggle')
        self.use_canvas_check.setCheckable(True)
        self.use_canvas_check.setChecked(True)  # an empty canvas sends nothing
        self.use_canvas_check.toggled.connect(lambda _: self.show_use_canvas())
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet('color: gray;')
        self.session_label = QLabel(self)  # what this session has spent, beside Send
        self.session_label.setObjectName('claudeSession')
        self.send_button = QPushButton(self)
        self.send_button.setStyleSheet('QPushButton { background: #d97757; color: #1f1e1d; font-weight: bold; font-size: 12px;'
                                       ' padding: 5px 16px; border: none; border-radius: 6px; }'
                                       'QPushButton:hover { background: #E58D6F; } QPushButton:pressed { background: #C4623F; }')
        self.send_button.clicked.connect(self.send_or_stop)
        # A chat box: the text across the whole width, growing upward as
        # lines are added, with the buttons and the cost on a row under it.
        body.addWidget(self.prompt_edit)
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(self.attach_button)
        row.addWidget(self.use_canvas_check)
        row.addStretch()
        row.addWidget(self.status_label)
        row.addWidget(self.session_label)  # created below, with the status line
        row.addWidget(self.send_button)
        body.addLayout(row)

        # The status line, as in Claude Code: New session and the mode on the left
        # (Shift+Tab switches it), then the model and the effort.
        status = QHBoxLayout()
        status.setSpacing(6)
        self.mode_button = QToolButton(self)
        self.mode_button.setObjectName('claudeMode')
        self.mode_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.mode_button.setIconSize(QSize(13, 13))
        self.mode_button.clicked.connect(self.cycle_mode)
        self.mode_key = QToolButton(self)  # the key that switches the mode: Shift + Tab
        self.mode_key.setObjectName('claudeKey')
        self.mode_key.setText('Tab')
        self.mode_key.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.mode_key.setIconSize(QSize(11, 11))
        self.mode_key.clicked.connect(self.cycle_mode)
        # The company, its model and the effort: each its own drop-down.
        self.provider_button = QToolButton(self)
        self.provider_button.setObjectName('claudePick')
        self.provider_button.setPopupMode(QToolButton.InstantPopup)
        self.provider_menu = QMenu(self.provider_button)
        self.provider_button.setMenu(self.provider_menu)
        self.model_button = QToolButton(self)
        self.model_button.setObjectName('claudePick')
        self.model_button.setPopupMode(QToolButton.InstantPopup)
        self.model_menu = QMenu(self.model_button)
        self.model_button.setMenu(self.model_menu)
        self.effort_button = QToolButton(self)
        self.effort_button.setObjectName('claudePick')
        self.effort_button.setPopupMode(QToolButton.InstantPopup)
        self.effort_menu = QMenu(self.effort_button)
        self.effort_button.setMenu(self.effort_menu)
        self.new_button = QToolButton(self)
        self.new_button.setObjectName('claudeChip')
        self.new_button.clicked.connect(self.new_session)
        status.addWidget(self.new_button)
        status.addWidget(self.mode_button)
        status.addWidget(self.mode_key)
        status.addStretch()
        status.addWidget(self.provider_button)
        status.addWidget(self.model_button)
        status.addWidget(self.effort_button)
        body.addLayout(status)
        for menu in (self.provider_menu, self.model_menu, self.effort_menu):
            menu.setStyleSheet(menu_style(self.theme_name))
        self.attach_button.setIcon(image_icon(self.theme_name))
        self.attach_button.setIconSize(QSize(16, 16))
        self.mode_key.setIcon(QIcon(icon_path(f'shift_on_{shade_of(self.theme_name)}.png')))
        self.use_canvas_check.setIconSize(QSize(14, 14))

    # Its own colors for each app theme: as a child of the canvas it would
    # otherwise take the canvas background (white in every theme).
    THEMES = {
        'dark': dict(bg='#2C2C2C', fg='#FFFFFF', border='#5A5A5A', button='#3A3A3A', hover='#474747',
                     log='#262626', log_border='#3F3F3F', muted='#9A9A9A', user_bg='#393937',
                     user_fg='#F5F4EF', ok='#4FC06F', bad='#E05A4B', auto='#B39DF0', plan='#3CC2B0',
                     pressed='#2F2F2F', frame='#FFFFFF', on='#4A3B33'),
        'light': dict(bg='#FFFFFF', fg='#000000', border='#B8B8B8', button='#ECECEC', hover='#DCDCDC',
                      log='#FAFAFA', log_border='#D0D0D0', muted='#6F6F6F', user_bg='#ECE9E2',
                      user_fg='#1F1E1D', ok='#2F9E4F', bad='#C0392B', auto='#7457D6', plan='#16897A',
                      pressed='#CFCFCF', frame='#000000', on='#FBE4D8'),
        'default': dict(bg='#ECECEC', fg='#000000', border='#A8A8A8', button='#E0E0E0', hover='#D2D2D2',
                        log='#FFFFFF', log_border='#C8C8C8', muted='#6F6F6F', user_bg='#E2DED6',
                        user_fg='#1F1E1D', ok='#2F9E4F', bad='#C0392B', auto='#7457D6', plan='#16897A',
                        pressed='#C2C2C2', frame='#000000', on='#F6DCCD'),
    }

    def apply_theme(self, theme_name):
        c = self.THEMES.get(str(theme_name).lower(), self.THEMES['default'])
        self.colors = c
        self.theme_name = str(theme_name).lower()
        if hasattr(self, 'working'):
            self.working.text_color, self.working.muted = QColor(c['fg']), QColor(c['muted'])
            self.working.track = QColor(c['log_border'])
            self.preview.style_for(c)
            self.render_transcript()
            self.refresh_controls()
        self.setStyleSheet(f"""
            QWidget#claudePanel {{ background-color: {c['bg']}; border: 1px solid {c['border']}; border-radius: 10px; }}
            #claudePanel QWidget {{ background-color: {c['bg']}; color: {c['fg']}; }}
            #claudePanel QLabel, #claudePanel QCheckBox {{ background-color: transparent; color: {c['fg']}; }}
            #claudePanel QPushButton {{ background-color: {c['button']}; color: {c['fg']}; border: none;
                                        border-radius: 4px; padding: 5px 10px; }}
            #claudePanel QPushButton:hover {{ background-color: {c['hover']}; }}
            #claudePanel QTextBrowser {{ background-color: {c['log']}; color: {c['fg']};
                                         border: 1px solid {c['log_border']}; border-radius: 6px; }}
            #claudePanel QToolButton {{ background-color: transparent; border: none; padding: 1px 2px;
                                        color: {c['muted']}; font-size: 12px; }}
            #claudePanel QToolButton:hover {{ color: {c['fg']}; }}
            #claudePanel QToolButton::menu-indicator {{ image: none; width: 0px; }}
            #claudePanel QLabel#claudeSession {{ color: {c['muted']}; font-size: 12px; }}
            /* As the toolbar's buttons: bold, square-ish corners; a frame while a toggle is on. */
            #claudePanel QPushButton#claudeChip, #claudePanel QToolButton#claudeChip,
            #claudePanel QPushButton#claudeToggle {{
                background-color: {c['button']}; color: {c['fg']}; border: 1px solid {c['border']};
                border-radius: 6px; padding: 4px 10px; font-weight: bold; font-size: 12px; }}
            #claudePanel QToolButton#claudeChip {{ padding: 2px 8px; }}
            #claudePanel QPushButton#claudeChip:hover, #claudePanel QToolButton#claudeChip:hover,
            #claudePanel QPushButton#claudeToggle:hover {{ background-color: {c['hover']}; }}
            #claudePanel QPushButton#claudeChip:pressed, #claudePanel QToolButton#claudeChip:pressed,
            #claudePanel QPushButton#claudeToggle:pressed {{ background-color: {c['pressed']}; }}
            #claudePanel QToolButton#claudeChip:disabled {{ color: {c['muted']}; }}
            #claudePanel QPushButton#claudeToggle:checked {{ background-color: {c['on']};
                border: 2px solid {c['frame']}; padding: 3px 9px; }}
            #claudePanel QToolButton#claudePick {{ background-color: {c['button']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px; padding: 2px 22px 2px 8px; font-size: 12px; }}
            #claudePanel QToolButton#claudePick::menu-indicator {{
                image: url({icon_path(f"menu_arrow_on_{shade_of(theme_name)}.png")});
                subcontrol-origin: padding; subcontrol-position: right center; width: 10px; height: 6px; right: 7px; }}
            #claudePanel QToolButton#claudePick:hover {{ background-color: {c['hover']}; }}
            #claudePanel QToolButton#claudePick:pressed {{ background-color: {c['pressed']}; }}
            #claudePanel QToolButton#claudeKey {{ color: {c['muted']}; background-color: {c['log']};
                border: 1px solid {c['border']}; border-radius: 4px; padding: 1px 5px; font-size: 11px; }}
        """)
        if hasattr(self, 'model_menu'):
            for menu in (self.provider_menu, self.model_menu, self.effort_menu):
                menu.setStyleSheet(menu_style(self.theme_name))
            self.attach_button.setIcon(image_icon(self.theme_name))
            self.mode_key.setIcon(QIcon(icon_path(f'shift_on_{shade_of(self.theme_name)}.png')))

    def is_open(self):
        return self.isVisibleTo(self.parentWidget())

    def set_open(self, opened):
        """Show or hide Claude (for this run only: it starts closed every time)."""
        opened = bool(opened)
        if not opened:
            self.preview.hide_frame()  # its own window: it would stay up with Claude hidden
        if opened:
            self.design_waiting = False
        self.setVisible(opened)
        if opened:
            self.place()
            self.stack()
            self.prompt_edit.setFocus()
        self.open_changed.emit(opened)
        self.activity_changed.emit()

    def place(self):
        """Across the bottom of the canvas, as tall as what it holds, never taller than the canvas."""
        canvas = self.parentWidget()
        if canvas is None:
            return
        area = self.visible_canvas()
        m = self.MARGIN
        width = max(240, area.width() - 2 * m)
        layout = self.layout()
        height = layout.totalHeightForWidth(width) if layout.hasHeightForWidth() else -1
        if height < 0:
            height = layout.totalSizeHint().height()
        # Always the bottom of the canvas: Claude never moves for the tab strip,
        # which floats over it (see stack).
        bottom = area.bottom() + 1 - m
        height = min(height, max(80, bottom - area.top() - m))
        self.setGeometry(area.left() + m, bottom - height, width, height)

    def visible_canvas(self):
        """The part of the canvas on screen: it has a minimum width, so a narrow
        column hides some of it under the layer panel."""
        canvas = self.parentWidget()
        area = canvas.rect()
        widget = canvas.parentWidget()
        while widget is not None:
            corner = canvas.mapFrom(widget, QPoint(0, 0))
            area = area.intersected(QRect(corner, widget.size()))
            if widget.isWindow():
                break
            widget = widget.parentWidget()
        return area if area.width() > 0 and area.height() > 0 else canvas.rect()

    def watch_layout(self):
        """Follow the canvas and the widgets around it as they resize."""
        widget = self.parentWidget()
        while widget is not None:
            widget.installEventFilter(self)
            if widget.isWindow():
                break
            widget = widget.parentWidget()

    def eventFilter(self, obj, event):
        if hasattr(self, 'transcript') and obj is self.transcript.viewport():
            if event.type() == QEvent.MouseMove:
                self.hover(self.transcript.anchorAt(event.pos()), event.globalPos())
            elif event.type() == QEvent.Leave:
                self.preview.hide_frame()
            return False
        if event.type() == QEvent.Resize and self.isVisible():
            self.place()
        return False

    def hover(self, anchor, cursor):
        """Over a running tool's picture: show it larger; anywhere else: hide it."""
        step = None
        if anchor.startswith('os:frame/'):
            try:
                i, j = (int(n) for n in anchor[len('os:frame/'):].split('/'))
                step = self.entries[i]['steps'][j]
            except (ValueError, IndexError, KeyError):
                step = None
        shown = step.get('frame_data') if step is not None and step.get('running') else \
            (step or {}).get('picture')
        if step is None or not shown:
            self.preview.hide_frame()
            return
        if self.preview.key != step['key']:
            self.preview.show_frame(step['key'], shown, cursor)

    def stack(self):
        """Above the canvas's other overlays, but under the tab strip: the
        strip floats over Claude and can be dragged anywhere, Claude stays put."""
        self.raise_()
        edge = getattr(self.main_window, 'tab_edge', None)
        if edge is not None and edge.isVisible():
            edge.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        self.watch_layout()  # the canvas is in its column by now
        self.place()

    def event(self, event):
        # The box grew a line, the conversation appeared, a picture was attached.
        if event.type() == QEvent.LayoutRequest and self.isVisible():
            result = super().event(event)
            self.place()
            return result
        return super().event(event)

    def retranslate(self, language_code):
        self.language = language_code
        t = lambda key: _tr(language_code, key)
        self.working.format_time = lambda seconds: duration_text(seconds, t)
        self.prompt_edit.setPlaceholderText(t('claude_prompt_placeholder'))
        self.prompt_edit.setToolTip(t('claude_prompt_keys'))
        self.attach_button.setText(t('claude_attach'))
        self.remove_image_button.setText(t('claude_remove_image'))
        self.show_use_canvas()
        self.send_button.setText(t('claude_stop') if self.running() else t('claude_send'))
        self.setLayoutDirection(Qt.RightToLeft if language_code == 'he' else Qt.LeftToRight)
        self.set_image(self.image_path)
        self.refresh_controls()
        self.render_transcript()

    def show_use_canvas(self):
        """Start from the canvas: a check mark (images/check.png) in front while it is on."""
        self.use_canvas_check.setText(_tr(self.language, 'claude_use_canvas'))
        self.use_canvas_check.setIcon(QIcon(icon_path('check.png')) if self.use_canvas_check.isChecked() else QIcon())

    def set_image(self, path):
        self.image_path = path
        self.image_row.setVisible(bool(path))
        if path:
            self.image_label.setText(os.path.basename(path))

    def choose_image(self):
        path, _ = QFileDialog.getOpenFileName(self, _tr(self.language, 'claude_attach_title'), '',
                                              'Images (*.png *.jpg *.jpeg *.gif *.webp)')
        if path:
            self.set_image(path)

    # ---------------------------------------------------------- transcript
    # The conversation is a list of entries, drawn as HTML each time it
    # changes, so step groups fold and open like Claude Code's: while Claude
    # works its steps show in a box under a live line; once it has answered
    # they fold into one line ("6 steps · 50s ›") that opens again on a click.
    def add_entry(self, entry):
        self.entries.append(entry)
        self.render_transcript()

    def add_user(self, text):
        self.close_group()
        self.follow_end = True  # a new request: show it, and what Claude does with it
        self.add_entry({'kind': 'user', 'text': text})

    def add_claude(self, text):
        self.close_group()
        self.add_entry({'kind': 'claude', 'text': text})

    def add_note(self, text, color=None):
        self.add_entry({'kind': 'note', 'text': text, 'color': color})

    def add_html(self, fragment):  # older callers
        self.add_entry({'kind': 'html', 'html': fragment})

    def open_group(self):
        last = self.entries[-1] if self.entries else None
        if last and last['kind'] == 'group' and last['end'] is None:
            return last
        group = {'kind': 'group', 'steps': [], 'start': time.monotonic(), 'end': None, 'open': True,
                 'toggled': False}
        self.entries.append(group)
        return group

    def add_step(self, step):
        self.open_group()['steps'].append(step)
        self.render_transcript()

    def close_group(self):
        """Fold this request's step groups: a note (Stopped, no web search)
        may have come after a group, so not only the last entry."""
        changed = False
        for entry in reversed(self.entries):
            if entry['kind'] == 'user':
                break
            if entry['kind'] == 'group' and entry['end'] is None:
                entry['end'] = time.monotonic()
                for step in entry['steps']:
                    step['running'] = False
                if not entry['toggled']:
                    entry['open'] = False  # folded once Claude has answered
                changed = True
        if changed:
            self.render_transcript()

    def render_transcript(self):
        if not hasattr(self, 'transcript'):
            return
        c = self.colors
        body = ''.join(self.entry_html(i, e, c) for i, e in enumerate(self.entries))
        with self.own_scroll():
            self.transcript.setHtml(f'<div style="color:{c["fg"]};">{body}</div>')
            self.transcript.setVisible(bool(self.entries))
            bar = self.transcript.verticalScrollBar()
            bar.setValue(bar.maximum() if self.follow_end else self.kept_scroll)

    @contextmanager
    def own_scroll(self):
        """The panel moves the scroll bar itself, not the person (it nests: keep_scroll runs
        inside setHtml)."""
        was, self.scrolling = self.scrolling, True
        try:
            yield
        finally:
            self.scrolling = was

    def keep_scroll(self, _minimum, maximum):
        """Qt lays a long conversation out a little at a time after setHtml, so the scroll bar's
        range keeps growing after render_transcript has scrolled: scroll again as it grows. Without
        this the view stopped short of the end, and an Allow/Deny card there went unseen."""
        target = maximum if self.follow_end else min(self.kept_scroll, maximum)
        bar = self.transcript.verticalScrollBar()
        if bar.value() != target:
            with self.own_scroll():
                bar.setValue(target)

    def scrolled(self, value):
        """The person scrolled: stay where they put it, or follow the end again from the bottom."""
        if self.scrolling:
            return
        self.kept_scroll = value
        self.follow_end = value >= self.transcript.verticalScrollBar().maximum() - 4

    def entry_html(self, i, e, c):
        t = lambda key: _tr(self.language, key)
        esc = html.escape
        kind = e['kind']
        if kind == 'user':
            return (f'<p style="margin:6px 0 4px 0;"><span style="background-color:{c["user_bg"]};'
                    f' color:{c["user_fg"]};">&nbsp;{esc(e["text"])}&nbsp;</span></p>')
        if kind == 'claude':
            return (f'<p style="margin:5px 0;"><span style="color:#D97757; font-size:9px;">●</span>&nbsp; '
                    f'{lines(e["text"])}</p>')
        if kind == 'note':
            return f'<p style="margin:4px 0; color:{e.get("color") or c["muted"]};">{esc(e["text"])}</p>'
        if kind == 'html':
            return e['html']
        if kind == 'design':
            picture = ''
            if e.get('png') and os.path.exists(e['png']):
                picture = (f'<td valign="middle"><img src="{QUrl.fromLocalFile(e["png"]).toString()}"'
                           f' width="96"></td>')
            action = (f'<span style="color:{c["muted"]};">{esc(t("claude_opened_short"))}</span>' if e['opened']
                      else f'<a href="os:open/{i}" style="color:#D97757; font-weight:bold;'
                           f' text-decoration:none;">{esc(t("claude_open_design"))} ›</a>')
            return (f'<table cellspacing="0" cellpadding="6" style="margin:4px 0 4px 18px;'
                    f' border:1px solid {c["log_border"]};"><tr>{picture}<td valign="middle">'
                    f'{esc(t("claude_design_ready").format(name=e["name"]))}<br>{action}</td></tr></table>')
        if kind == 'confirm':
            text = esc(confirm_text(self.language, e['what']))
            if e['state'] is None:
                choice = (f'<a href="os:allow/{i}" style="color:#D97757; font-weight:bold; text-decoration:none;">'
                          f'{esc(t("claude_allow"))}</a>&nbsp;&nbsp;&nbsp;<a href="os:deny/{i}" '
                          f'style="color:{c["muted"]}; text-decoration:none;">{esc(t("claude_deny"))}</a>')
            else:
                word = {'allowed': 'claude_allowed', 'denied': 'claude_denied'}.get(e['state'], 'claude_stopped')
                choice = f'<span style="color:{c["muted"]};">{esc(t(word))}</span>'
            return (f'<table cellspacing="0" cellpadding="6" style="margin:4px 0 4px 18px;'
                    f' border:1px solid {c["log_border"]};"><tr><td>{text}<br>{choice}</td></tr></table>')
        if kind == 'share':
            if e['state'] is None:
                text = f'{esc(t("claude_share_ask"))}<br>'
                choice = (f'<a href="os:share/{i}" style="color:#D97757; font-weight:bold; text-decoration:none;">'
                          f'{esc(t("claude_share_yes"))}</a>&nbsp;&nbsp;&nbsp;<a href="os:noshare/{i}" '
                          f'style="color:{c["muted"]}; text-decoration:none;">{esc(t("claude_share_no"))}</a>')
            else:
                text = ''
                said = 'claude_share_on' if e['state'] == 'shared' else 'claude_share_off'
                choice = f'<span style="color:{c["muted"]};">{esc(t(said))}</span>'
            return (f'<table cellspacing="0" cellpadding="6" style="margin:4px 0 4px 18px;'
                    f' border:1px solid {c["log_border"]};"><tr><td>{text}{choice}</td></tr></table>')
        if kind == 'plan':
            if e['built']:
                return f'<p style="margin:4px 0 4px 18px; color:{c["muted"]};">{esc(t("claude_plan_built"))}</p>'
            return (f'<p style="margin:6px 0 6px 18px;"><a href="os:plan/{i}" style="color:{c["plan"]};'
                    f' font-weight:bold; text-decoration:none;">▶ {esc(t("claude_build_plan"))}</a></p>')
        # A group of steps.
        steps = e['steps']
        if e['end'] is None:
            current = self.step_label(steps[-1], running=True) if steps else t('claude_working')
            head = f'<span style="color:#D97757; font-size:9px;">●</span>&nbsp; {esc(current)}'
        else:
            seconds = max(1, int(round(e['end'] - e['start'])))
            head = esc(t('claude_steps').format(count=len(steps), seconds=seconds))
        arrow = '⌄' if e['open'] else '›'
        out = (f'<p style="margin:5px 0 2px 0;"><a href="os:group/{i}" style="color:{c["muted"]};'
               f' text-decoration:none;">{head}&nbsp; {arrow}</a></p>')
        if e['open'] and steps:
            rows = ''.join(f'<tr><td style="border-bottom:1px solid {c["log_border"]};">'
                           f'{self.step_html(i, j, s, c)}</td></tr>' for j, s in enumerate(steps))
            out += (f'<table width="100%" cellspacing="0" cellpadding="5" style="margin:0 0 4px 18px;'
                    f' border:1px solid {c["log_border"]}; border-collapse:collapse;">{rows}</table>')
        return out

    def step_label(self, step, running=False):
        t = lambda key: _tr(self.language, key)
        kind = step['kind']
        if kind == 'thinking':
            return t('claude_thinking') + ('…' if running else '')
        if kind == 'search':
            return t('claude_searching' if running else 'claude_step_searched').format(query=step['text'])
        if kind == 'fetch':
            return t('claude_reading' if running else 'claude_step_read').format(url=short_url(step['text']))
        name = step['name']
        key = TOOL_CHIPS.get(name, (None,))[0]
        label = t(key) if key else name
        if step.get('running') and step.get('waiting'):
            return f'{label} · {self.waiting_text()}'
        if step.get('running') and step.get('stage'):
            return f'{label} · {self.stage_text(step)}'
        if step.get('running') and name in SLOW_TOOLS:
            return t('claude_drawing')
        return label + (f': {step["summary"]}' if step.get('summary') else '…')

    def stage_text(self, step):
        """What a tool says it is doing, in the person's language ("drawing step 3 of 5")."""
        stage = str(step.get('stage') or '')
        text = _tr(self.language, f'claude_stage_{stage}')
        if text == f'claude_stage_{stage}':
            return stage.replace('_', ' ')
        try:
            return text.format(**step.get('numbers', {}))
        except (KeyError, IndexError, ValueError):
            return text

    def step_html(self, i, j, step, c):
        t = lambda key: _tr(self.language, key)
        esc = html.escape
        kind = step['kind']
        if kind == 'thinking':
            arrow = '⌄' if step['open'] else '›'
            out = (f'<a href="os:think/{i}/{j}" style="color:{c["muted"]}; text-decoration:none;">'
                   f'<i>{esc(t("claude_step_thought"))}</i>&nbsp; {arrow}</a>')
            if step['open']:
                out += f'<br><i style="color:{c["muted"]};">{lines(step["text"])}</i>'
            return out
        if kind in ('search', 'fetch'):
            return f'<span style="color:{c["muted"]};">{esc(self.step_label(step))}</span>'
        key, bg, fg = TOOL_CHIPS.get(step['name'], (None, *OTHER_CHIP))
        label = t(key) if key else step['name']
        if step.get('running'):
            mark = f'<span style="color:{ACCENT};">●</span>'
            detail = (self.waiting_text() if step.get('waiting') else
                      self.stage_text(step) if step.get('stage') else '…')
        else:
            # Done or failed: the panel's check and cross pictures (images/), not font characters.
            mark = f'<img src="{icon_path("check.png" if step.get("ok") else "cross.png")}" width="12" height="12">'
            detail = t('claude_stopped').rstrip('.。') if step.get('stopped') else step.get('summary') or ''
            took = step.get('seconds')
            if took is not None and took >= 1:  # how long it took, once it is worth saying
                detail = (detail + ' · ' if detail else '') + duration_text(took, t)
        out = (f'{mark}&nbsp; <span style="background-color:{bg}; color:{fg}; font-weight:bold;">'
               f'&nbsp;{esc(label)}&nbsp;</span>&nbsp; <span style="color:{c["muted"]};">{esc(detail)}</span>')
        if step.get('running'):
            if not step.get('waiting'):  # a moving bar and clock would say Claude is busy: it waits for the person
                out += self.progress_html(step, c, i, j)
        elif step.get('picture'):
            image = (f'<a href="os:frame/{i}/{j}" style="text-decoration:none;"><img src="claude-frame:{step["key"]}"'
                     f' width="{FRAME_SIZE[0]}" height="{FRAME_SIZE[1]}"></a>')
            out += f'<table cellspacing="0" cellpadding="0" style="margin:4px 0 2px 22px;"><tr><td>{image}</td></tr></table>'
        return out

    # ------------------------------------------------------------ progress
    # A long tool (tie_knot, draw_design) says how far it has got: a picture
    # of what it works on, about once a second, and the fraction done. Its
    # row shows them with a bar, how much is left and its time so far; the
    # working line under the transcript shows the bar too.
    def progress_html(self, step, c, i=None, j=None):
        t = lambda key: _tr(self.language, key)
        elapsed = time.monotonic() - step.get('start', time.monotonic())
        if not (step.get('stage') or step.get('frame')) and elapsed < 2:
            return ''  # a quick tool: nothing more to show
        words = [w for w in (self.progress_words(step), duration_text(elapsed, t)) if w]
        bar = f'claude-bar:{step["key"]}'
        self.transcript.document().addResource(
            QTextDocument.ImageResource, QUrl(bar),
            bar_image(step.get('fraction'), c['log_border'], ACCENT, phase=elapsed / 4))  # redrawn every second
        picture = ''
        if step.get('frame'):
            image = (f'<img src="claude-frame:{step["key"]}" width="{FRAME_SIZE[0]}" height="{FRAME_SIZE[1]}">')
            if i is not None:  # the mouse over it shows it larger (hover)
                image = f'<a href="os:frame/{i}/{j}" style="text-decoration:none;">{image}</a>'
            picture = f'<td valign="middle" style="padding-right:10px;">{image}</td>'
        return (f'<table cellspacing="0" cellpadding="0" style="margin:4px 0 2px 22px;"><tr>{picture}'
                f'<td valign="middle"><img src="{bar}" width="{BAR_SIZE[0]}" height="{BAR_SIZE[1]}"><br>'
                f'<span style="color:{c["muted"]};">{html.escape(" · ".join(words))}</span></td></tr></table>')

    def progress_words(self, step):
        """'58% · about 20s left' (or nothing while the tool cannot tell)."""
        t = lambda key: _tr(self.language, key)
        fraction = step.get('fraction')
        if fraction is None:
            return ''
        words = [f'{int(100 * fraction)}%']
        eta = step.get('eta')
        if eta is not None:
            left = eta[0] - (time.monotonic() - eta[1])
            if left < 3:
                words.append(t('claude_almost_done'))
            else:
                left = math.ceil(left / 5) * 5 if left < 60 else math.ceil(left / 15) * 15
                words.append(t('claude_left').format(time=duration_text(left, t)))
        return ' · '.join(words)

    @staticmethod
    def update_eta(step, now):
        """Time left from the time so far and the fraction done, smoothed so
        it counts down instead of jumping with every event."""
        fraction, elapsed = step.get('fraction'), now - step.get('start', now)
        if fraction is None or fraction < 0.03 or elapsed < 1.0:
            return
        estimate = elapsed * (1 - fraction) / fraction
        if step.get('eta') is not None:
            before, at = step['eta']
            estimate = 0.6 * max(0.0, before - (now - at)) + 0.4 * estimate
        step['eta'] = (estimate, now)

    def running_step(self, name=None):
        """The tool running now (named name, when given), or None."""
        for entry in reversed(self.entries):
            if entry['kind'] == 'user':
                return None
            if entry['kind'] == 'group' and entry['end'] is None:
                for step in reversed(entry['steps']):
                    if step['kind'] == 'tool' and step.get('running') and name in (None, step['name']):
                        return step
        return None

    def show_progress(self, event):
        step = self.running_step(event.get('name'))
        if step is None:
            return
        now = time.monotonic()
        if event.get('fraction') is not None:
            step['fraction'] = max(step.get('fraction') or 0.0, min(1.0, float(event['fraction'])))
            self.update_eta(step, now)
        if event.get('stage'):
            step['stage'] = event['stage']
            step['numbers'] = {k: v for k, v in event.items()
                               if k not in ('type', 'name', 'stage', 'fraction', 'frame')}
        if event.get('frame'):
            try:
                image = frame_image(event['frame'])
            except (KeyError, TypeError, ValueError, IndexError, AttributeError):
                image = None  # a picture that cannot be drawn: keep the last one
            if image is not None:
                self.transcript.document().addResource(
                    QTextDocument.ImageResource, QUrl(f'claude-frame:{step["key"]}'), image)
                step['frame'], step['frame_data'] = True, event['frame']
                if self.preview.key == step['key']:  # open under the mouse: it moves on too
                    self.preview.update_frame(event['frame'])
        self.render_transcript()
        self.show_working(step)

    def show_working(self, step):
        self.working.set_label(self.step_label(step, running=True))
        if step.get('stage') or step.get('fraction') is not None:
            self.working.set_progress(step.get('fraction'), self.progress_words(step))

    def refresh_running(self):
        """Every second while a tool runs: its time, and the time left, move on."""
        step = self.running_step()
        if step is None:
            self.tick.stop()
            return
        if step.get('waiting'):
            return  # nothing moves while Claude waits for the person's Allow or Deny
        if time.monotonic() - step.get('start', 0) >= 2:
            self.render_transcript()
            self.show_working(step)

    def release_pictures(self, step):
        """A finished tool's progress picture and bar are freed (attach_picture then puts
        its finished picture in, when it has one)."""
        step.pop('frame_data', None)
        if self.preview.key is not None and self.preview.key == step.get('key'):
            self.preview.hide_frame()
        if step.get('key') is not None:
            for kind in ('claude-frame', 'claude-bar'):
                self.transcript.document().addResource(QTextDocument.ImageResource,
                                                       QUrl(f'{kind}:{step["key"]}'), QImage())

    def attach_picture(self, step, event):
        """The finished tool's picture in its row: what the agent sent (the design it
        made, changed, checked or read), or the app as the tool left it."""
        if step.get('key') is None:
            return  # no name for its picture in the transcript
        path = event.get('image')
        if not path and event.get('ok'):
            try:
                path = self.grab_for(step)
            except (RuntimeError, AttributeError) as e:  # a window gone or not there: no picture
                terminal_log(f'no picture for {step.get("name")}: {e}')
                path = None
        if not path or not os.path.exists(path):
            return
        step['picture'] = path
        self.transcript.document().addResource(QTextDocument.ImageResource, QUrl(f'claude-frame:{step["key"]}'),
                                               fitted_image(path))

    def grab_for(self, step):
        """The app as an app tool left it, saved in this request's folder: the canvas
        (without Claude floating over it), the group panel, or the window after a
        setting. None for the tools that only list or read."""
        name, window = step.get('name'), self.main_window
        if name in CANVAS_TOOLS:
            canvas = window.canvas
            image = QImage(canvas.size(), QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            canvas.render(painter, QPoint(), QRegion(), QWidget.RenderFlags(QWidget.DrawWindowBackground))
            painter.end()
        elif name == 'show_group':
            image = window.group_layer_manager.group_panel.grab().toImage()
        elif name == 'app_settings':
            dialog = getattr(window, 'settings_dialog', None)
            shown = (step.get('input') or {}).get('op') == 'show' and dialog is not None and dialog.isVisible()
            image = (dialog if shown else window).grab().toImage()
        else:
            return None
        if image.isNull() or not self.out_dir:
            return None
        folder = os.path.join(self.out_dir, 'frames')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f'app_{step["key"]}.png')
        return path if image.save(path) else None

    def follow_link(self, url):
        link = url.toString()
        if not link.startswith('os:'):
            QDesktopServices.openUrl(url)
            return
        what, *ids = link[3:].split('/')
        if what == 'frame':
            return  # a tool's picture: the mouse over it shows it larger, a click does nothing
        try:
            ids = [int(n) for n in ids]
            entry = self.entries[ids[0]]
        except (ValueError, IndexError):
            return
        if what == 'group':
            entry['open'], entry['toggled'] = not entry['open'], True
        elif what == 'think':
            step = entry['steps'][ids[1]]
            step['open'] = not step['open']
        elif what == 'open' and not entry['opened']:
            entry['opened'] = True
            if entry.get('title') and self.bridge is not None:
                try:
                    self.bridge.open_in_new_tab(entry['path'], entry['title'])
                except Exception as e:
                    self.add_note(_tr(self.language, 'claude_failed').format(error=e), self.colors['bad'])
            else:
                self.design_ready.emit(entry['path'])
        elif what in ('allow', 'deny') and entry['state'] is None:
            allowed = what == 'allow'
            entry['state'] = 'allowed' if allowed else 'denied'
            terminal_log(f'{"allowed" if allowed else "declined"} by the person: {confirm_text("en", entry["what"])}')
            self.stop_waiting()
            if self.bridge is not None:
                reply = self.bridge.decide(entry['id'], allowed)
                if reply is not None:
                    self.answer(reply)
        elif what == 'plan' and not entry['built'] and not self.running():
            self.build_plan(entry)
            return
        elif what in ('share', 'noshare') and entry['kind'] == 'share' and entry['state'] is None:
            shared = what == 'share'
            entry['state'] = 'shared' if shared else 'declined'
            claude_settings.save(share=shared)  # Settings > Models shows it, and changes it
            record = entry.pop('record', None)
            if shared and record is not None:
                self.send_share(record)
        self.render_transcript()

    # -------------------------------------------------------- status line
    # Each mode's color and words; its symbol is images/mode_<mode>_on_<dark|light>.png, a picture
    # rather than a font character, so it looks the same everywhere (no emoji, no missing glyph).
    MODE_LOOK = {'ask': ('muted', 'claude_mode_ask'), 'auto': ('auto', 'claude_mode_auto'),
                 'plan': ('plan', 'claude_mode_plan')}

    def cycle_mode(self):
        """Shift+Tab, as in Claude Code: ask before opening, open automatically, plan."""
        order = ('ask', 'auto', 'plan')
        self.set_mode(order[(order.index(self.mode) + 1) % len(order)])

    def set_mode(self, mode):
        self.mode = mode
        if mode != 'plan':
            self.last_mode = mode
            claude_settings.save(mode=mode)  # plan mode is never kept
        self.refresh_controls()

    def refresh_controls(self):
        """The status line from the saved settings: mode, model, effort, session."""
        if not hasattr(self, 'mode_button'):
            return
        t = lambda key: _tr(self.language, key)
        c = self.colors
        saved = claude_settings.load()
        if not saved['models_on'] and self.running():
            terminal_log('AI models were turned off in Settings > Models: ending the agent')
            self.send_or_stop()  # stops it, as Stop does: nothing more goes to the model
        self.new_button.setText('＋ ' + t('claude_new_session'))
        self.new_button.setEnabled(not self.running())
        color, key = self.MODE_LOOK[self.mode]
        # The mode as a tinted tag in its own color; the Shift+Tab key cap beside it switches it.
        tint = QColor(c[color])
        self.mode_button.setIcon(mode_icon(self.mode, self.theme_name))
        self.mode_button.setText(t(key))
        self.mode_button.setToolTip(t('claude_mode_cycle'))
        self.mode_key.setToolTip(t('claude_mode_cycle'))
        self.mode_key.setAccessibleName('Shift+Tab')
        self.mode_button.setStyleSheet(
            f'QToolButton {{ color: {c[color]}; background-color: rgba({tint.red()}, {tint.green()}, {tint.blue()}, 38);'
            f' border: 1px solid rgba({tint.red()}, {tint.green()}, {tint.blue()}, 110); border-radius: 6px;'
            f' padding: 2px 8px; font-weight: bold; font-size: 12px; }}'
            f'QToolButton:hover {{ background-color: rgba({tint.red()}, {tint.green()}, {tint.blue()}, 70); }}')
        offered = claude_settings.models()
        names = dict(offered)
        # The company drop-down lists the providers (and whether each key is still missing,
        # Settings > Models); the model drop-down lists the chosen company's models.
        by_provider = {}
        for model, label in offered:
            by_provider.setdefault(claude_settings.provider_of(model), []).append((model, label))
        current = claude_settings.provider_of(saved['model'])
        self.provider_menu.clear()
        group = QActionGroup(self.provider_menu)
        for provider, entries in by_provider.items():
            spec = claude_settings.PROVIDERS.get(provider)
            keyed = provider in saved['keys'] or (spec is not None and os.environ.get(spec.env))
            title = spec.name if spec else provider
            action = QAction(title if keyed else f'{title}   ({t("models_no_key")})', self.provider_menu, checkable=True)
            action.setChecked(provider == current)
            action.triggered.connect(lambda _=False, m=entries[0][0], p=provider:
                                     None if p == claude_settings.provider_of(claude_settings.load()['model'])
                                     else self.choose(model=m))
            group.addAction(action)
            self.provider_menu.addAction(action)
        spec = claude_settings.PROVIDERS.get(current)
        self.provider_button.setText(short_provider_name(spec.name if spec else current))
        self.model_menu.clear()
        group = QActionGroup(self.model_menu)
        for model, label in by_provider.get(current, []):
            tags = model_tags(model, t)
            action = QAction(f'{label}   ({tags})' if tags else label, self.model_menu, checkable=True)
            action.setChecked(model == saved['model'])
            action.triggered.connect(lambda _=False, m=model: self.choose(model=m))
            group.addAction(action)
            self.model_menu.addAction(action)
        self.model_button.setText(names.get(saved['model'], saved['model']))
        self.effort_menu.clear()
        group = QActionGroup(self.effort_menu)
        for effort in claude_settings.EFFORTS:
            action = QAction(t(f'claude_effort_{effort}'), self.effort_menu, checkable=True)
            action.setChecked(effort == saved['effort'])
            action.triggered.connect(lambda _=False, e=effort: self.choose(effort=e))
            group.addAction(action)
            self.effort_menu.addAction(action)
        self.effort_button.setText(t(f'claude_effort_{saved["effort"]}'))
        self.show_session()

    def auto_refresh_models(self):
        """The daily Refresh models, in the background and without a word: only when a
        day has passed since the last one and some provider has a key."""
        if self.fetching_models or getattr(sys, 'frozen', False) or not claude_settings.refresh_due(AUTO_REFRESH_HOURS):
            return
        self.fetching_models = True

        def ask():
            try:
                found = claude_settings.fetch_catalog()
            except Exception as e:  # noqa: BLE001 - silent: the terminal says it, the lists stay
                terminal_log(f'refresh models failed: {type(e).__name__}: {e}')
                found = None
            self.models_fetched.emit(found)
        threading.Thread(target=ask, daemon=True).start()

    def apply_fetched_models(self, found):
        self.fetching_models = False
        if not found or not found.get('providers'):
            return
        result = claude_settings.apply_catalog(found)
        terminal_log(f"models refreshed: {len(result['new'])} new, {len(result['retiring'])} retiring, "
                     f"{len(result['hidden'])} no longer offered"
                     + (f", now using {result['switched']}" if result['switched'] else ''))
        self.refresh_controls()

    def choose(self, **change):
        claude_settings.save(**change)
        self.refresh_controls()

    def session_left(self):
        return claude_settings.load()['session_limit'] - self.session_spent

    def show_session(self):
        limit = claude_settings.load()['session_limit']
        spent = self.session_spent + self.run_cost
        self.session_label.setText(_tr(self.language, 'claude_session').format(spent=money(spent),
                                                                                  limit=money(limit)))
        near = spent >= 0.8 * limit
        self.session_label.setStyleSheet(f'color: {self.colors["bad"] if near else self.colors["muted"]};')

    # ------------------------------------------------------------- running
    def running(self):
        return self.process is not None and self.process.state() != QProcess.NotRunning

    def send_or_stop(self):
        if self.running():
            terminal_log('Stop pressed: ending the agent')
            self.stopping = True
            self.stop_steps()
            self.close_group()
            self.process.kill()
            self.add_note(_tr(self.language, 'claude_stopped'))
        else:
            self.send()

    def build_plan(self, entry):
        """Build the plan Claude wrote in plan mode, in the mode used before it."""
        entry['built'] = True
        self.set_mode(self.last_mode)
        prompt = (entry['prompt'] + '\n\nBuild it now, following this plan, which I approved:\n' + entry['plan'])
        self.send(prompt=prompt, shown=_tr(self.language, 'claude_build_plan'))

    def send(self, prompt=None, shown=None):
        typed = prompt is None
        prompt = (self.prompt_edit.text() if typed else prompt).strip()
        if typed and prompt.lower() in ('/clear', '/new'):  # as in Claude Code
            self.prompt_edit.clear()
            self.new_session()
            return
        if not prompt or self.running():
            return
        self.set_open(True)
        if getattr(sys, 'frozen', False):
            self.add_note(_tr(self.language, 'claude_source_only'), '#c0392b')
            return
        settings = claude_settings.load()
        if not settings['models_on']:  # Settings > Models: nothing is ever sent to a model
            self.add_note(_tr(self.language, 'models_off_note'), '#c0392b')
            return
        provider = claude_settings.provider_of(settings['model'])
        spec = claude_settings.PROVIDERS.get(provider)
        key_env = spec.env if spec else 'ANTHROPIC_API_KEY'
        key = settings['keys'].get(provider, '')
        if not key and not os.environ.get(key_env, '').strip():
            self.add_note(_tr(self.language, 'models_need_key').format(provider=spec.name if spec else 'Anthropic'),
                          '#c0392b')
            return
        left = settings['session_limit'] - self.session_spent
        if left < 0.05:
            self.add_note(_tr(self.language, 'claude_session_reached').format(
                limit=money(settings['session_limit'])), self.colors['bad'])
            return
        self.prompt = prompt
        stamp = time.strftime('%Y%m%d-%H%M%S')
        self.out_dir = os.path.join(claude_settings.settings_directory(), 'claude_designs', stamp)
        os.makedirs(self.out_dir, exist_ok=True)
        start = None
        if self.use_canvas_check.isChecked():
            start = self.write_canvas(os.path.join(self.out_dir, 'canvas.json'))
        history = None
        if self.history:
            history = os.path.join(self.out_dir, 'history.json')
            with open(history, 'w', encoding='utf-8') as f:
                json.dump(self.history, f)
        self.shown_prompt, self.run_design = (shown or prompt), None
        # One request may spend its own limit, but never past what the session has left.
        program, args = agent_command(prompt, settings['model'], self.out_dir,
                                      [self.image_path] if self.image_path else [], start,
                                      web=settings['web'], max_cost=min(settings['max_cost'], left),
                                      effort=settings['effort'], plan=self.mode == 'plan',
                                      app=self.bridge is not None, history=history)
        env = QProcessEnvironment.systemEnvironment()
        if key:  # the chosen model's provider: its key, as its own environment variable
            env.insert(key_env, key)
        env.insert('QT_QPA_PLATFORM', 'offscreen')
        env.insert('PYTHONUNBUFFERED', '1')
        env.insert('PYTHONIOENCODING', 'utf-8')
        self.process = QProcess(self)
        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(REPO_ROOT)
        self.process.readyReadStandardOutput.connect(self.read_events)
        self.process.readyReadStandardError.connect(self.read_errors)
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(self.failed_to_start)
        self.done_event, self.stdout_buffer, self.stderr_text = None, b'', ''
        self.stopping = False
        # What this request has cost so far; the total keeps counting from
        # everything earlier requests cost, saved in claude.json.
        self.run_cost, self.total_before = 0.0, claude_settings.load()['spent']
        self.run_mode, self.run_texts, self.run_files = self.mode, [], (None, None)
        self.add_user((shown or prompt) + (f'  [{os.path.basename(self.image_path)}]' if self.image_path else ''))
        if typed:
            self.prompt_edit.clear()
        self.set_image(None)
        self.status_label.setText(_tr(self.language, 'claude_working'))
        self.working.start(_tr(self.language, 'claude_thinking') + '…')
        self.activity_changed.emit()
        self.send_button.setText(_tr(self.language, 'claude_stop'))
        terminal_log(f'request starts: {prompt[:80]!r}; its files and agent.log are in {self.out_dir}')
        self.process.start(program, args)
        self.new_button.setEnabled(False)  # not while Claude works

    def stop_steps(self, by_person=True):
        """The tools still running end here: stopped by the person, or the agent ended."""
        now = time.monotonic()
        while True:
            step = self.running_step()
            if step is None:
                return
            step.update(running=False, ok=False, stopped=by_person, seconds=now - step.get('start', now))
            self.release_pictures(step)

    def cost_line(self):
        """'this request $0.041 · total $1.27': the total never starts again from zero."""
        return _tr(self.language, 'claude_cost_line').format(
            request=money(self.run_cost), total=money(self.total_before + self.run_cost))

    def save_spending(self):
        """Add this request to the saved total once, finished, stopped or failed."""
        if self.run_cost:
            claude_settings.add_spending(self.run_cost)
            self.total_before += self.run_cost
            self.session_spent += self.run_cost
            self.run_cost = 0.0
            self.spending_changed.emit()
        self.show_session()

    def failed_to_start(self, error):
        if error != QProcess.FailedToStart:
            return  # a crash or kill still ends in finished()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        self.status_label.setText('')
        self.working.stop()
        self.add_note(_tr(self.language, 'claude_failed').format(error=self.process.errorString()), '#c0392b')
        self.activity_changed.emit()

    def write_canvas(self, path):
        """Save what is on the canvas now as the agent's starting design; None when empty."""
        data = self.main_window.claude_canvas_snapshot()
        if not data or not data.get('strands'):
            return None
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return path

    def read_events(self, flush=False):
        if self.process is not None:
            self.stdout_buffer += bytes(self.process.readAllStandardOutput())
        *lines, self.stdout_buffer = self.stdout_buffer.split(b'\n')
        if flush:  # the last line may come without a newline
            lines.append(self.stdout_buffer)
            self.stdout_buffer = b''
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line.decode('utf-8'))
            except ValueError:
                continue  # not an event (stray output from a library)
            try:
                self.handle_event(event)
            except Exception:  # noqa: BLE001
                # Logged, and the read goes on: an error here used to lose the lines after it,
                # an app_call among them, and Claude then waited for an answer that never came.
                logging.exception('the Claude panel could not show a %s event', event.get('type'))

    def read_errors(self):
        if self.process is None:
            return
        new = bytes(self.process.readAllStandardError()).decode('utf-8', 'replace')
        # Complete lines go to the terminal as they come: the agent's log, and any error.
        start = self.stderr_text.rfind('\n') + 1
        self.stderr_text += new
        complete = self.stderr_text[start:self.stderr_text.rfind('\n') + 1] if '\n' in new else ''
        for line in complete.splitlines():
            if line.strip():
                terminal_log(line[len(LOG_PREFIX):] if line.startswith(LOG_PREFIX) else line)

    def handle_event(self, event):
        kind = event.get('type')
        t = lambda key: _tr(self.language, key)
        if kind == 'text':
            text = event.get('text', '')
            self.run_texts.append(text)
            self.add_claude(text)
            self.working.set_label(t('claude_working'))
        elif kind == 'thinking':
            text = event.get('text', '')
            text = text if len(text) <= 2000 else text[:2000].rsplit(' ', 1)[0] + '…'
            self.add_step({'kind': 'thinking', 'text': text, 'open': False})
            self.working.set_label(t('claude_thinking') + '…')
        elif kind == 'search':
            fetch = event.get('name') == 'web_fetch'
            step = {'kind': 'fetch' if fetch else 'search', 'text': event.get('query', '')}
            self.add_step(step)
            self.working.set_label(self.step_label(step, running=True))
        elif kind == 'note':
            self.add_note(event.get('text', ''))
        elif kind == 'tool_start':
            self.step_keys += 1
            step = {'kind': 'tool', 'name': event.get('name', ''), 'running': True, 'ok': None, 'summary': '',
                    'start': time.monotonic(), 'key': self.step_keys, 'input': event.get('input') or {}}
            self.add_step(step)
            self.working.clear_progress()
            self.working.set_label(self.step_label(step, running=True))
            self.tick.start()
        elif kind == 'tool_progress':
            self.show_progress(event)
        elif kind == 'tool_end':
            name = event.get('name', '')
            # Its row, in whichever group it started: a card (Allow/Deny, a design to open)
            # may have come after it, and the steps after a card go in a new group.
            step = self.running_step(name)
            if step is None:
                self.step_keys += 1
                step = {'kind': 'tool', 'name': name, 'key': self.step_keys}
                self.open_group()['steps'].append(step)
            if step.pop('waiting', None):
                # Its card was never answered and Claude gave up waiting (the app's answer came
                # too late): a late Allow would make a change Claude no longer knows of.
                self.expire_cards()
            step.update(running=False, ok=bool(event.get('ok')), summary=event.get('summary', ''))
            if step.get('start') is not None:
                step['seconds'] = time.monotonic() - step['start']
            self.release_pictures(step)
            self.attach_picture(step, event)
            self.render_transcript()
            self.working.clear_progress()
            self.working.set_label(t('claude_working'))
        elif kind == 'usage':
            self.run_cost = max(self.run_cost, float(event.get('cost') or 0))
            self.status_label.setText(self.cost_line())
            self.show_session()
        elif kind == 'app_call':
            self.app_call(event)
        elif kind == 'done':
            self.done_event = event

    # ------------------------------------------------------------- bridge
    def app_call(self, call):
        """A request from Claude's app tools: the bridge runs it with the app's own code."""
        if self.bridge is None:
            reply = {'id': call.get('id'), 'ok': False, 'error': 'the app bridge is not available'}
        else:
            reply = self.bridge.handle(call)
        if reply is not None:  # None: the person decides with Allow or Deny
            self.answer(reply)

    def answer(self, reply):
        if self.running():
            self.process.write((json.dumps(reply) + '\n').encode('utf-8'))

    def add_design_card(self, path, title):
        """Ask mode: a design Claude wants in a tab of its own, opened when the person says so."""
        png = path[:-5] + '.png'
        self.add_entry({'kind': 'design', 'path': path, 'png': png if os.path.exists(png) else None,
                        'opened': False, 'name': title, 'title': title})

    def add_confirm_card(self, call_id, what):
        """Ask mode: a change Claude asked for waits for the person's Allow or Deny, and Claude
        waits with it (its tool runs until they answer). So the card comes into view, the tool's
        row and the working line say Claude waits for them, and so does the terminal."""
        self.design_waiting = self.design_waiting or not self.is_open()
        step = self.running_step()
        if step is not None:
            step['waiting'] = True
        self.follow_end = True
        self.add_entry({'kind': 'confirm', 'id': call_id, 'what': what, 'state': None})
        self.working.clear_progress()
        self.working.set_label(self.waiting_text())
        terminal_log(f'waiting for the person to click Allow or Deny in the panel: {confirm_text("en", what)}')
        self.activity_changed.emit()

    def waiting_text(self):
        """'Waiting for you: Allow or Deny', in the card's own words."""
        t = lambda key: _tr(self.language, key)
        return t('claude_waiting_for_you').format(allow=t('claude_allow'), deny=t('claude_deny'))

    def stop_waiting(self):
        """The person answered a card: the tool that waited for it runs on."""
        step = self.running_step()
        if step is not None and step.pop('waiting', None):
            self.show_working(step)

    def expire_cards(self):
        """Cards no one answered, once Claude no longer waits for them: they do nothing now."""
        for entry in self.entries:
            if entry['kind'] == 'confirm' and entry['state'] is None:
                entry['state'] = 'expired'
                if self.bridge is not None:
                    self.bridge.pending.pop(entry['id'], None)

    def finished(self, *_):
        if self.process is not None and hasattr(self.process, 'exitCode'):
            terminal_log(f'the agent process ended (exit code {self.process.exitCode()}'
                         f'{", stopped by the person" if self.stopping else ""})')
        try:
            self._finish()
            self.remember_turn()
            try:
                self.share_run()
            except Exception:  # noqa: BLE001 - sharing never gets in the way of the answer
                logging.exception('could not prepare this request for sharing')
        finally:
            self.new_button.setEnabled(True)
            self.activity_changed.emit()  # the Claude button stops turning

    def remember_turn(self):
        """Keep this request and Claude's answer for the next one in the session."""
        event = self.done_event or {}
        answer = '\n\n'.join(self.run_texts) or event.get('text') or event.get('error') or ''
        design = self.run_design
        if event.get('opened_tabs'):
            design = 'opened in tabs: ' + ', '.join(event['opened_tabs'])
        elif self.run_mode == 'plan':
            design = 'a plan, nothing built yet'
        turn = {'user': self.shown_prompt or self.prompt, 'claude': answer, 'design': design}
        tools = self.run_tools()
        if tools:  # which tools ran and how each ended: Claude can say what happened
            turn['tools'] = tools
        self.history.append(turn)

    # ------------------------------------------------- sharing with the developer
    def share_run(self):
        """What this request made, for the developer (claude_sharing): sent when the person
        said yes; while they have not said, a card asks, once while the app runs. Nothing
        for a request they stopped, or one that made nothing; nothing at all until the
        developer has set sharing up."""
        event = self.done_event
        design, picture = self.run_files
        if event is not None and event.get('changed') is False:
            design = picture = None  # still the person's own canvas, as it came: theirs, not Claude's
        if (event is None or event is self.shared_event or self.stopping or not (self.run_texts or design)
                or not claude_sharing.available()):
            return
        self.shared_event = event
        settings = claude_settings.load()
        choice = settings['share']
        if not settings['models_on'] or choice is False or (choice is None and self.share_asked):
            return
        record = self.share_record(event, design, picture)
        if choice:
            self.send_share(record)
            return
        self.share_asked = True
        self.add_entry({'kind': 'share', 'state': None, 'record': record})

    def share_record(self, event, design, picture):
        project = png = None
        if design and os.path.exists(design):
            with open(design, 'r', encoding='utf-8') as f:
                project = json.load(f)
        if picture and os.path.exists(picture):
            with open(picture, 'rb') as f:
                png = f.read()
        return claude_sharing.record(self.run_texts, project, png, model=event.get('model'), language=self.language,
                                     ok=bool(event.get('ok')) and not event.get('error'))

    def send_share(self, record):
        """Seal it and send it, off the main thread. The terminal says how it went, never what
        it held; a share that fails is dropped (it never holds the panel up)."""
        def send():
            try:
                sealed = claude_sharing.seal(record)
                if not claude_settings.sharing_on():  # turned off since it was queued: it stays here
                    terminal_log('not shared: sharing was turned off')
                    return
                status = claude_sharing.send(sealed)
                terminal_log(f'shared with the developer, encrypted (the server answered {status})')
            except Exception as e:  # noqa: BLE001
                terminal_log(f'could not share with the developer: {type(e).__name__}: {e}')
        threading.Thread(target=send, daemon=True).start()

    def run_tools(self):
        """This request's tool calls, for the next request: name, how it ended, time, summary."""
        out = []
        for entry in reversed(self.entries):
            if entry['kind'] == 'user':
                break
            if entry['kind'] != 'group':
                continue
            for step in reversed(entry['steps']):
                if step['kind'] != 'tool':
                    continue
                state = 'stopped by the person' if step.get('stopped') else 'ok' if step.get('ok') else 'failed'
                took = f", {int(round(step['seconds']))} s" if step.get('seconds') is not None else ''
                summary = f": {step['summary']}" if step.get('summary') and not step.get('stopped') else ''
                out.append(f"{step['name']} ({state}{took}){summary}"[:160])
        return out[::-1][-12:]

    def new_session(self):
        """Start again from nothing: no conversation, nothing Claude remembers,
        the session's spending back to $0. The canvas stays as it is; untick
        "Start from the canvas" to leave it out too."""
        if self.running():
            return
        self.preview.hide_frame()
        self.entries.clear()
        self.history.clear()
        self.session_spent = self.run_cost = 0.0
        self.design_waiting = False
        self.status_label.setText('')
        self.set_image(None)
        if self.bridge is not None:
            self.bridge.forget()
        self.add_note(_tr(self.language, 'claude_new_session_note'))
        self.show_session()
        self.activity_changed.emit()
        self.prompt_edit.setFocus()

    def _finish(self):
        self.run_files = (None, None)  # set below when this request made a design
        self.read_events(flush=True)
        self.read_errors()
        if self.bridge is not None:
            self.bridge.forget()
        self.expire_cards()  # Claude has stopped; nothing waits any more
        self.stop_steps(by_person=self.stopping)
        self.tick.stop()
        self.working.stop()
        self.close_group()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        event = self.done_event
        if event is not None:
            self.run_cost = max(self.run_cost, float(event.get('cost') or 0))
        spent, line = self.run_cost, self.cost_line()
        self.save_spending()
        if event is None:
            self.status_label.setText(line if spent else '')
            if not self.stopping:  # stopped by the person: "Stopped." says it already
                lines = [l for l in self.stderr_text.splitlines() if l.strip() and not l.startswith(LOG_PREFIX)]
                message = lines[-1] if lines else 'the agent stopped without an answer'
                self.add_note(_tr(self.language, 'claude_failed').format(error=message.removeprefix('error: ')),
                              '#c0392b')
            return
        self.status_label.setText(line)  # the model is on the status line below
        if event.get('error'):
            self.add_note(_tr(self.language, 'claude_failed').format(error=event['error']), '#c0392b')
        if event.get('plan') or self.run_mode == 'plan':
            if self.run_texts and not event.get('error'):
                self.add_entry({'kind': 'plan', 'prompt': self.prompt, 'plan': '\n\n'.join(self.run_texts),
                                'built': False})
            return
        project = event.get('project')
        if event.get('opened_tabs'):
            if project and os.path.exists(project):  # still what this request made: shared as such
                png = event.get('png')
                self.run_files = (project, png if png and os.path.exists(png) else None)
            project = None  # Claude opened its tabs itself, through the bridge
        if project and os.path.exists(project):
            named = os.path.join(self.out_dir, design_name(self.prompt) + '.json')
            shutil.copyfile(project, named)
            self.run_design = os.path.basename(named)
            png = event.get('png')
            picture = None
            if png and os.path.exists(png):
                picture = named[:-5] + '.png'
                shutil.copyfile(png, picture)
            self.run_files = (named, picture)
            self.design_waiting = not self.is_open()
            if self.run_mode == 'ask':  # wait for "Open in new tab"
                self.add_entry({'kind': 'design', 'path': named, 'png': picture, 'opened': False,
                                'name': os.path.basename(named)})
            else:
                self.add_note(_tr(self.language, 'claude_opened').format(name=os.path.basename(named)))
                self.design_ready.emit(named)


def knot_mark_path():
    """The button's mark, in a 24 px box: one cord, its ends up, crossing itself
    above a loop (an overhand loop), as OpenStrand draws a strand. Returns the
    whole cord and the part that goes over at the crossing."""
    a, b, c, d = QPointF(2.5, 3.5), QPointF(7.0, 7.0), QPointF(12.5, 10.5), QPointF(16.0, 14.0)
    whole = QPainterPath(a)  # from the left end down over the crossing,
    whole.cubicTo(b, c, d)
    whole.cubicTo(QPointF(19.0, 17.5), QPointF(17.5, 21.2), QPointF(12.0, 21.2))  # round the loop
    whole.cubicTo(QPointF(6.5, 21.2), QPointF(5.0, 17.5), QPointF(8.0, 14.0))
    whole.cubicTo(QPointF(11.5, 10.5), QPointF(17.0, 7.0), QPointF(21.5, 3.5))  # and up under it to the right end
    # The first curve from a third of the way along (de Casteljau): the part over the crossing.
    t = 0.3
    mix = lambda p, q: p + (q - p) * t  # noqa: E731
    ab, bc, cd = mix(a, b), mix(b, c), mix(c, d)
    abc, bcd = mix(ab, bc), mix(bc, cd)
    over = QPainterPath(mix(abc, bcd))
    over.cubicTo(bcd, cd, d)
    return whole, over


def paint_knot_mark(painter, box, fill=QColor('#A65400'), outline=QColor('#111111'), width=4.2, stroke=0.9):
    """The mark in box (a QRectF): the cord with its outline, the part from the left end
    redrawn on top where it crosses, so it reads over and under as in the app."""
    whole, over = knot_mark_path()
    scale = min(box.width(), box.height()) / 24.0
    painter.save()
    painter.translate(box.center().x() - 12 * scale, box.center().y() - 12 * scale)
    painter.scale(scale, scale)

    def cord(path, body_cap):
        for color, size, cap in ((outline, width + 2 * stroke, Qt.FlatCap), (fill, width, body_cap)):
            pen = QPen(color, size)
            pen.setCapStyle(cap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
    cord(whole, Qt.FlatCap)  # the ends cut square, as a strand's ends
    cord(over, Qt.RoundCap)  # over at the crossing; its round body ends hide the seams
    painter.restore()


class ClaudeButton(QPushButton):
    """The assistant's button next to Settings: shows and hides the assistant.

    A small OpenStrand knot (the assistant runs on many providers' models, so the
    button is the app's own mark, not one provider's), drawn here so it answers the
    mouse: a little lighter under the pointer, smaller while pressed and, while the
    assistant is open, a ring in the cord's color. While it is hidden it also shows
    what the assistant is doing: an arc turns around it during a run, and a green dot
    waits on it when a design has opened."""

    # Ember: a burnt-orange face and a cream cord, as strong as the toolbar's other buttons.
    FACE = QColor('#A65400')
    HOVER = QColor('#BC6A17')
    PRESSED = QColor('#7A3D00')
    OPEN = QColor('#8A4500')
    EDGE = QColor('#6E3700')
    CORD = QColor('#FFE9CF')
    RADIUS = 7  # corner radius of the 32 px square

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.setObjectName('claudeButton')
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setAccessibleName('Assistant')
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor)
        self.angle = 0
        self.spin = QTimer(self)
        self.spin.setInterval(50)
        self.spin.timeout.connect(self.turn)
        self.setChecked(panel.is_open())
        self.toggled.connect(panel.set_open)
        panel.open_changed.connect(self.follow)
        panel.activity_changed.connect(self.show_activity)

    def follow(self, opened):
        self.blockSignals(True)
        self.setChecked(opened)
        self.blockSignals(False)
        self.show_activity()

    def busy(self):
        return self.panel.running() and not self.panel.is_open()

    def show_activity(self):
        if self.busy():
            self.spin.start()
        else:
            self.spin.stop()
        self.update()

    def turn(self):
        self.angle = (self.angle - 24) % 360
        self.update()

    def enterEvent(self, event):
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.update()

    def color(self):
        if self.isDown():
            return self.PRESSED
        if self.isChecked():
            return self.OPEN
        if self.underMouse():
            return self.HOVER
        return self.FACE

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        square = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self.isDown():  # pressed in: a touch smaller
            square = square.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(QPen(self.CORD if self.isChecked() else self.EDGE, 1.5 if self.isChecked() else 1.0))
        painter.setBrush(self.color())
        painter.drawRoundedRect(square, self.RADIUS, self.RADIUS)
        inset = square.width() * 0.12
        paint_knot_mark(painter, square.adjusted(inset, inset, -inset, -inset), fill=self.CORD)
        if self.busy():
            pen = QPen(self.CORD, 2.5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRectF(self.rect()).adjusted(2.5, 2.5, -2.5, -2.5), self.angle * 16, 100 * 16)
        if self.panel.design_waiting and not self.panel.is_open():
            painter.setPen(QPen(QColor('#1f1e1d'), 1.5))
            painter.setBrush(QColor('#4fc06f'))
            painter.drawEllipse(QRectF(self.width() - 11, 1, 10, 10))
        painter.end()


def resource_path(name):
    """A file next to this module, or in the bundle of a frozen build."""
    base = getattr(sys, '_MEIPASS', None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)


class ClaudeSettingsPage(QWidget):
    """Settings > Claude: whether Claude shows, the Anthropic API key, the
    model, web search, the spending limit and what Claude has cost."""

    show_button_changed = pyqtSignal(bool)  # the main window shows or hides the Claude button
    settings_changed = pyqtSignal()  # model, effort or limits: the Claude status line follows
    refreshed = pyqtSignal(object, object)  # Refresh models: (what the providers said, or an error)

    def __init__(self, language_code='en', parent=None):
        super().__init__(parent)
        self.language = language_code
        self.theme = None
        self.setObjectName('claudeSettings')
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        self.intro = QLabel(self)
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

        self.show_check = QCheckBox(self)
        self.show_check.toggled.connect(self.set_show_button)
        layout.addWidget(self.show_check)
        self.show_hint = QLabel(self)
        self.show_hint.setWordWrap(True)
        self.show_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.show_hint)

        # Off: OpenStrand never connects to any AI model (providers.POLICY refuses every request).
        self.models_check = QCheckBox(self)
        self.models_check.toggled.connect(self.set_models_on)
        layout.addWidget(self.models_check)
        self.models_hint = QLabel(self)
        self.models_hint.setWordWrap(True)
        self.models_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.models_hint)
        # The providers based in China: off until the person allows them.
        self.china_check = QCheckBox(self)
        self.china_check.toggled.connect(self.set_allow_china)
        layout.addWidget(self.china_check)
        self.china_hint = QLabel(self)
        self.china_hint.setWordWrap(True)
        self.china_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.china_hint)
        self.refreshing = False  # Refresh models is asking the providers

        provider_row = QHBoxLayout()
        self.key_label = QLabel(self)
        self.provider_combo = QComboBox(self)
        for provider in claude_settings.PROVIDERS.values():
            self.provider_combo.addItem(provider.name, provider.key)
        self.provider_combo.currentIndexChanged.connect(lambda _: self.show_provider())
        self.provider_combo.currentIndexChanged.connect(self.fit_combos)
        provider_row.addWidget(self.key_label)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        layout.addLayout(provider_row)
        # The key field, with an eye in it that shows what was typed (a pasted key can be
        # checked before saving; once saved the field empties and only its ends are shown).
        key_row = QHBoxLayout()
        self.key_edit = QLineEdit(self)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText('sk-ant-…')
        self.key_edit.returnPressed.connect(self.save_key)
        self.show_key_action = self.key_edit.addAction(QIcon(), QLineEdit.TrailingPosition)
        self.show_key_action.setCheckable(True)
        self.show_key_action.toggled.connect(self.toggle_shown)
        self.save_button = QPushButton(self)
        self.save_button.clicked.connect(self.save_key)
        self.remove_button = QPushButton(self)
        self.remove_button.clicked.connect(self.remove_key)
        key_row.addWidget(self.key_edit, 1)
        key_row.addWidget(self.save_button)
        key_row.addWidget(self.remove_button)
        layout.addLayout(key_row)
        self.key_status = QLabel(self)
        layout.addWidget(self.key_status)
        self.get_key = QLabel(self)
        self.get_key.setOpenExternalLinks(True)
        self.get_key.setTextFormat(Qt.RichText)
        layout.addWidget(self.get_key)

        self.model_label = QLabel(self)
        layout.addWidget(self.model_label)
        # The model and Refresh models on one row. The list sizes to a short name, not to its
        # longest entry, so the page never grows wider than the dialog; its popup shows all.
        self.model_combo = QComboBox(self)
        self.model_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.model_combo.setMinimumContentsLength(24)
        self.model_combo.currentIndexChanged.connect(self.save_model)
        self.model_combo.currentIndexChanged.connect(self.fit_combos)
        self.refresh_button = QPushButton(self)
        self.refresh_button.clicked.connect(self.refresh_models)
        model_row = QHBoxLayout()
        model_row.addWidget(self.model_combo)
        model_row.addWidget(self.refresh_button)
        model_row.addStretch(1)
        layout.addLayout(model_row)
        self.refresh_status = QLabel(self)
        self.refresh_status.setWordWrap(True)
        self.refresh_status.setStyleSheet('color: gray;')
        layout.addWidget(self.refresh_status)
        self.refreshed.connect(self.show_refresh)

        self.effort_label = QLabel(self)
        layout.addWidget(self.effort_label)
        self.effort_combo = QComboBox(self)
        self.effort_combo.currentIndexChanged.connect(self.save_effort)
        self.effort_combo.currentIndexChanged.connect(self.fit_combos)
        effort_row = QHBoxLayout()
        effort_row.addWidget(self.effort_combo)
        effort_row.addStretch()
        layout.addLayout(effort_row)
        self.effort_hint = QLabel(self)
        self.effort_hint.setWordWrap(True)
        self.effort_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.effort_hint)

        self.web_check = QCheckBox(self)
        self.web_check.toggled.connect(lambda on: claude_settings.save(web=on))
        layout.addWidget(self.web_check)
        self.web_hint = QLabel(self)
        self.web_hint.setWordWrap(True)
        self.web_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.web_hint)

        # The two spending limits in a grid: labels in one column, the $ − / + controls lined
        # up in the next, each wide enough for its largest amount.
        limits = QGridLayout()
        limits.setHorizontalSpacing(10)
        limits.setVerticalSpacing(6)
        self.limit_label = QLabel(self)
        self.limit_spin = QDoubleSpinBox(self)
        self.limit_spin.setRange(*claude_settings.MAX_COST_RANGE)
        self.limit_spin.setDecimals(2)
        self.limit_spin.setSingleStep(0.50)
        self.limit_spin.setPrefix('$')
        self.limit_spin.valueChanged.connect(lambda value: self.changed_setting(max_cost=value))
        limits.addWidget(self.limit_label, 0, 0)
        limits.addWidget(self.limit_spin, 0, 1)

        self.session_limit_label = QLabel(self)
        self.session_spin = QDoubleSpinBox(self)
        self.session_spin.setRange(*claude_settings.SESSION_LIMIT_RANGE)
        self.session_spin.setDecimals(2)
        self.session_spin.setSingleStep(1.00)
        self.session_spin.setPrefix('$')
        self.session_spin.valueChanged.connect(lambda value: self.changed_setting(session_limit=value))
        limits.addWidget(self.session_limit_label, 1, 0)
        limits.addWidget(self.session_spin, 1, 1)
        limits.setColumnStretch(2, 1)
        layout.addLayout(limits)

        # What Claude has cost in all on this computer, kept across requests.
        spent_row = QHBoxLayout()
        self.spent_label = QLabel(self)
        self.spent_label.setStyleSheet('font-weight: bold;')
        self.reset_spent_button = QPushButton(self)
        self.reset_spent_button.clicked.connect(self.reset_spending)
        spent_row.addWidget(self.spent_label)
        spent_row.addWidget(self.reset_spent_button)
        spent_row.addStretch()
        layout.addLayout(spent_row)
        self.spent_hint = QLabel(self)
        self.spent_hint.setWordWrap(True)
        self.spent_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.spent_hint)

        # Sharing what Claude makes with the developer: only once the developer set it up.
        self.share_check = QCheckBox(self)
        self.share_check.toggled.connect(lambda on: claude_settings.save(share=on))
        layout.addWidget(self.share_check)
        self.share_hint = QLabel(self)
        self.share_hint.setWordWrap(True)
        self.share_hint.setStyleSheet('color: gray;')
        layout.addWidget(self.share_hint)

        self.storage = QLabel(self)
        self.storage.setWordWrap(True)
        self.storage.setStyleSheet('color: gray;')
        layout.addWidget(self.storage)
        layout.addStretch()
        self.retranslate(language_code)
        self.apply_theme()

    def retranslate(self, language_code):
        self.language = language_code
        t = lambda key: _tr(language_code, key)
        self.intro.setText(t('models_settings_intro'))
        self.key_label.setText(t('models_key_label'))
        self.toggle_shown(self.show_key_action.isChecked())
        self.save_button.setText(t('claude_save_key'))
        self.remove_button.setText(t('claude_remove_key'))
        self.model_label.setText(t('claude_model_label'))
        self.storage.setText(t('claude_key_storage_keychain' if claude_settings.key_storage() == 'keychain'
                               else 'claude_key_storage'))
        self.share_check.setText(t('models_share_label'))
        self.share_hint.setText(t('models_share_hint'))
        self.models_check.setText(t('models_use_label'))
        self.models_hint.setText(t('models_use_hint'))
        self.china_check.setText(t('models_china_label'))
        self.china_hint.setText(t('models_china_hint'))
        saved = claude_settings.load()
        self.fill_models(saved)
        self.refresh_button.setText(t('models_refresh'))
        if not self.refreshing:
            refreshed = (saved.get('catalog') or {}).get('refreshed')
            self.refresh_status.setText(t('models_last_refresh').format(date=refreshed) if refreshed
                                        else t('models_never_refreshed'))
        self.effort_label.setText(t('claude_effort_label'))
        self.effort_hint.setText(t('claude_effort_hint'))
        self.session_limit_label.setText(t('claude_session_limit_label'))
        self.web_check.setText(t('claude_web_label'))
        self.web_hint.setText(t('claude_web_hint') + ' ' + t('models_web_claude_only'))
        self.limit_label.setText(t('claude_limit_label'))
        self.web_check.blockSignals(True)
        self.web_check.setChecked(saved['web'])
        self.web_check.blockSignals(False)
        self.limit_spin.blockSignals(True)
        self.limit_spin.setValue(saved['max_cost'])
        self.limit_spin.blockSignals(False)
        self.show_choices()
        self.show_provider(claude_settings.provider_of(saved['model']))
        self.show_check.setText(t('claude_show_button'))
        self.show_hint.setText(t('claude_show_button_hint'))
        self.show_check.blockSignals(True)
        self.show_check.setChecked(saved['show_button'])
        self.show_check.blockSignals(False)
        self.reset_spent_button.setText(t('claude_spent_reset'))
        self.spent_hint.setText(t('claude_spent_hint'))
        self.show_spending()
        self.show_share()
        self.show_switches()
        self.setLayoutDirection(Qt.RightToLeft if language_code == 'he' else Qt.LeftToRight)

    # The dialog's own look: its buttons' colors, border and hover and pressed states are kept
    # exactly (the dialog's style sheet); only their size is made compact (the dialog's are 48 px
    # tall with a 120 px minimum). The key field gets a border and padding.
    def apply_theme(self, theme=None):
        theme = str(theme or getattr(self.window(), 'current_theme', None) or 'default').lower()
        self.theme = theme
        c = ClaudePanel.THEMES.get(theme, ClaudePanel.THEMES['default'])
        self.setStyleSheet(f"""
            #claudeSettings QLineEdit {{ background-color: {c['log']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px; padding: 5px 6px; font-size: 13px; }}
            #claudeSettings QLineEdit:focus {{ border: 1px solid #D97757; }}
            #claudeSettings QPushButton {{ padding: 5px 14px; height: 18px; min-width: 0px; }}
        """)
        # The drop-downs exactly like Settings > General's Theme: its own style sheet.
        theme_combo = getattr(self.window(), 'theme_combobox', None)
        for combo in (self.provider_combo, self.model_combo, self.effort_combo):
            combo.setStyleSheet(theme_combo.styleSheet() if theme_combo is not None else '')
        self.toggle_shown(self.show_key_action.isChecked())
        self.show_provider()  # the link's color follows the theme
        self.fit_money_spins()
        self.fit_combos()

    def fit_combos(self, *_):
        """Each drop-down as wide as the item it shows (not its longest one, and not the whole
        row), so there is no empty gap before the arrow; capped so the page still fits."""
        for combo in (self.provider_combo, self.model_combo, self.effort_combo):
            combo.ensurePolished()
            # What the style keeps for the arrow, padding and border: the combo's width less the
            # field its text is drawn in (measured, so it holds for any style sheet).
            option = QStyleOptionComboBox()
            combo.initStyleOption(option)
            option.rect = QRect(0, 0, 400, max(combo.height(), 30))
            field = combo.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxEditField, combo)
            overhead = 400 - field.width()
            icon = 0 if combo.itemIcon(combo.currentIndex()).isNull() else combo.iconSize().width() + 4
            text = combo.fontMetrics().horizontalAdvance(combo.currentText())
            combo.setFixedWidth(min(overhead + icon + text + 8, 460))

    def fit_money_spins(self):
        """The $ − / + controls: room for the largest amount between the buttons (the dialog's
        stepper is a fixed 110 px, where $10.00 touched the +), both the same width."""
        widest = 0
        for spin in (self.limit_spin, self.session_spin):
            text = spin.prefix() + spin.textFromValue(spin.maximum())
            widest = max(widest, spin.fontMetrics().horizontalAdvance(text))
        width = 2 * 31 + widest + 28  # the two 30 px buttons and their hairlines, the value, its margins
        for spin in (self.limit_spin, self.session_spin):
            spin.setFixedWidth(width)

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_theme()  # the theme may have changed on another page
        self.fill_models()  # the daily refresh may have changed the models offered
        self.show_spending()  # requests may have run since the page was built
        self.show_choices()  # the status line may have changed the model or effort
        self.show_share()  # the panel's card may have changed it
        self.show_switches()

    def show_choices(self):
        """Model, effort and the session limit as saved."""
        t = lambda key: _tr(self.language, key)
        saved = claude_settings.load()
        for combo in (self.model_combo, self.effort_combo):
            combo.blockSignals(True)
        self.model_combo.setCurrentIndex(max(0, self.model_combo.findData(saved['model'])))
        self.effort_combo.clear()
        for effort in claude_settings.EFFORTS:
            self.effort_combo.addItem(t(f'claude_effort_{effort}'), effort)
        self.effort_combo.setCurrentIndex(max(0, self.effort_combo.findData(saved['effort'])))
        for combo in (self.model_combo, self.effort_combo):
            combo.blockSignals(False)
        self.session_spin.blockSignals(True)
        self.session_spin.setValue(saved['session_limit'])
        self.session_spin.blockSignals(False)
        self.fit_combos()

    def show_spending(self):
        saved = claude_settings.load()
        t = lambda k: _tr(self.language, k)
        if saved['spent'] or saved['spent_since']:
            since = QDate.fromString(saved['spent_since'], Qt.ISODate)
            when = QLocale(self.language).toString(since, QLocale.ShortFormat) if since.isValid() else ''
            self.spent_label.setText(t('claude_spent').format(total=money(saved['spent']), date=when))
        else:
            self.spent_label.setText(t('claude_spent_none'))
        self.reset_spent_button.setEnabled(saved['spent'] > 0)

    def reset_spending(self):
        claude_settings.reset_spending()
        self.show_spending()

    def show_switches(self):
        """The two switches as saved. With models off nothing can ask a provider anything, so
        Refresh models waits; keys can still be removed."""
        saved = claude_settings.load()
        for check, on in ((self.models_check, saved['models_on']), (self.china_check, saved['allow_china'])):
            check.blockSignals(True)
            check.setChecked(on)
            check.blockSignals(False)
        self.refresh_button.setEnabled(saved['models_on'] and not self.refreshing)

    def set_models_on(self, on):
        claude_settings.save(models_on=on)
        self.show_switches()
        self.settings_changed.emit()  # the panel stops a request that is running

    def set_allow_china(self, allowed):
        claude_settings.save(allow_china=allowed)
        self.fill_models()  # their models shown or hidden; the saved model may have moved off them
        self.show_choices()
        self.show_provider(claude_settings.provider_of(claude_settings.load()['model']))
        self.settings_changed.emit()

    def show_share(self):
        """The share box as saved (off until the person says yes), shown once sharing is set up."""
        shown = claude_sharing.available()
        self.share_check.setVisible(shown)
        self.share_hint.setVisible(shown)
        self.share_check.blockSignals(True)
        self.share_check.setChecked(claude_settings.load()['share'] is True)
        self.share_check.blockSignals(False)

    def set_show_button(self, shown):
        claude_settings.save(show_button=shown)
        self.show_button_changed.emit(bool(shown))

    def provider(self):
        return self.provider_combo.currentData() or 'anthropic'

    def show_provider(self, provider=None):
        """The key field for one provider: its saved key, what its keys look like, where to get one."""
        if provider is not None:
            self.provider_combo.blockSignals(True)
            self.provider_combo.setCurrentIndex(max(0, self.provider_combo.findData(provider)))
            self.provider_combo.blockSignals(False)
        spec = claude_settings.PROVIDERS.get(self.provider())
        self.key_edit.setPlaceholderText(spec.key_hint if spec else 'sk-ant-…')
        if spec and spec.keys_url:
            host = spec.keys_url.split('//', 1)[-1].split('/', 1)[0]
            link_color = '#E8892F' if shade_of(self.theme) == 'dark' else '#A65400'  # readable on the theme
            self.get_key.setText(_tr(self.language, 'models_get_key').format(
                link=f'<a href="{spec.keys_url}" style="color:{link_color};">{host}</a>'))
        self.show_saved(claude_settings.load()['keys'].get(self.provider(), ''))

    def show_saved(self, key):
        t = lambda k: _tr(self.language, k)
        self.key_status.setText(t('claude_key_saved').format(key=claude_settings.masked(key)) if key
                                else t('claude_key_none'))
        self.remove_button.setEnabled(bool(key))

    def toggle_shown(self, shown):
        """The eye in the key field: show what was typed, or hide it again."""
        self.key_edit.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        eye = f"eye_{'open' if shown else 'closed'}_on_{shade_of(self.theme)}.png"
        self.show_key_action.setIcon(QIcon(icon_path(eye)))
        self.show_key_action.setToolTip(_tr(self.language, 'claude_hide_key' if shown else 'claude_show_key'))

    def save_key(self):
        key = self.key_edit.text().strip()
        if not key:
            return
        claude_settings.save(provider_key=(self.provider(), key))
        self.key_edit.clear()
        self.show_saved(key)
        self.settings_changed.emit()  # the model menu says which providers have a key

    def remove_key(self):
        claude_settings.save(provider_key=(self.provider(), ''))
        self.show_saved('')
        self.settings_changed.emit()
        self.key_status.setText(_tr(self.language, 'claude_key_removed'))

    def changed_setting(self, **change):
        claude_settings.save(**change)
        self.settings_changed.emit()

    def save_effort(self, index):
        effort = self.effort_combo.itemData(index)
        if effort:
            self.changed_setting(effort=effort)

    def fill_models(self, saved=None):
        """The model list: every model offered now, its provider and tags."""
        t = lambda k: _tr(self.language, k)
        saved = saved or claude_settings.load()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model, label in claude_settings.models():
            spec = claude_settings.PROVIDERS.get(claude_settings.provider_of(model))
            words = [label] + [w for w in (spec.name if spec else '', model_tags(model, t)) if w]
            self.model_combo.addItem('  ·  '.join(words), model)
        self.model_combo.setCurrentIndex(max(0, self.model_combo.findData(saved['model'])))
        self.model_combo.blockSignals(False)
        view = self.model_combo.view()  # the popup wide enough for every entry
        view.setMinimumWidth(view.sizeHintForColumn(0) + 32)
        self.fit_combos()

    def refresh_models(self):
        """Refresh models (by hand only): each provider with a key says which models it
        offers now. The asking runs off the main thread; show_refresh takes the answer."""
        self.refreshing = True
        self.refresh_button.setEnabled(False)
        self.refresh_status.setText(_tr(self.language, 'models_refreshing'))

        def ask():
            try:
                self.refreshed.emit(claude_settings.fetch_catalog(), None)
            except Exception as e:  # noqa: BLE001 - said on the page, the list stays as it was
                self.refreshed.emit(None, f'{type(e).__name__}: {e}')
        threading.Thread(target=ask, daemon=True).start()

    def show_refresh(self, found, error):
        t = lambda k: _tr(self.language, k)
        self.refreshing = False
        self.refresh_button.setEnabled(claude_settings.load()['models_on'])
        if error or not found:
            self.refresh_status.setText(error or '')
            return
        if not found.get('providers'):
            self.refresh_status.setText(t('models_refresh_none'))
            return
        result = claude_settings.apply_catalog(found)
        lines = [t('models_refreshed').format(date=found.get('refreshed', ''), new=len(result['new']),
                                              retiring=len(result['retiring']), hidden=len(result['hidden']))]
        for provider, answer in found['providers'].items():
            if answer.get('error'):
                spec = claude_settings.PROVIDERS.get(provider)
                lines.append(f"{spec.name if spec else provider}: {answer['error']}")
        if result['switched']:
            lines.append(t('models_switched').format(model=dict(claude_settings.models()).get(result['switched'],
                                                                                              result['switched'])))
        self.refresh_status.setText('\n'.join(lines))
        self.fill_models()
        self.show_provider(claude_settings.provider_of(claude_settings.load()['model']))
        self.settings_changed.emit()  # the status line's model menu follows

    def save_model(self, index):
        model = self.model_combo.itemData(index)
        if model:
            self.changed_setting(model=model)
            self.show_provider(claude_settings.provider_of(model))  # where this model's key goes
