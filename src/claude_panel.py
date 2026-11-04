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
import math
import os
import re
import shutil
import sys
import time

from PyQt5.QtCore import (QDate, QEvent, QLocale, QPoint, QPointF, QProcess, QProcessEnvironment, QRect,
                          QRectF, Qt, QTimer, QUrl, pyqtSignal)
from PyQt5.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import (QAction, QActionGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                             QHBoxLayout, QLabel, QLineEdit, QMenu, QPushButton, QToolButton, QSizePolicy, QTextBrowser, QTextEdit, QVBoxLayout,
                             QWidget)

import claude_settings
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
}
OTHER_CHIP = ('#d4d4d4', '#1a1a1a')
# Tools that can take up to a minute: the panel says so when they start.
SLOW_TOOLS = {'draw_design', 'make_heart', 'make_turks_head'}


def _tr(language, key):
    table = translations.get(language) or translations['en']
    return table.get(key) or translations['en'].get(key, key)


def agent_command(prompt, model, out_dir, images=(), start=None, web=True, max_cost=None, effort=None,
                  plan=False, app=False):
    """The program and arguments that run one agent request."""
    args = ['-m', 'openstrand', 'agent', prompt, '--model', model, '--out-dir', out_dir, '--json-events']
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


class WorkingLine(QWidget):
    """Claude at work, the OpenStrand way: a closed overhand knot drawn strand
    by strand, over and over, then what Claude is doing and the seconds so
    far. (Without its frames it falls back to a turning trefoil.)"""

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
        self.frame = 0
        self.show()
        self.timer.start(self.durations[0] if self.durations else 40)

    def set_label(self, label):
        self.label = label
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

    def draw_label(self, painter, box):
        seconds = int(time.monotonic() - self.started)
        x = box + 12
        painter.setPen(self.text_color)
        metrics = painter.fontMetrics()
        label = metrics.elidedText(self.label, Qt.ElideRight, max(40, self.width() - x - 60))
        painter.drawText(QRectF(x, 0, self.width() - x, self.height()), Qt.AlignVCenter, label)
        painter.setPen(self.muted)
        painter.drawText(QRectF(x + metrics.horizontalAdvance(label) + 10, 0, 60, self.height()),
                         Qt.AlignVCenter, f'{seconds}s')


class ClaudePanel(QWidget):
    """Claude, floating over the bottom of the canvas: the conversation, the
    chat box and its buttons. The Claude button next to Settings shows and
    hides it."""

    design_ready = pyqtSignal(str)  # path of the finished project file
    spending_changed = pyqtSignal()  # a request's cost was added to the saved total
    open_changed = pyqtSignal(bool)  # Claude was shown or hidden
    activity_changed = pyqtSignal()  # a run started or ended: the Claude button shows it
    MARGIN = 12  # px between Claude and the canvas edges

    def __init__(self, main_window, canvas=None, language_code='en'):
        # Claude floats over the bottom of the canvas: a child of the canvas,
        # so the canvas keeps its size and the drawing never moves.
        super().__init__(canvas if canvas is not None else main_window)
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
        self.bridge = None  # set by the main window: Claude's tab tools run through it
        self.session_spent = 0.0  # since the app opened; held to the session limit
        self.mode = claude_settings.load()['mode']  # 'ask', 'auto', or 'plan' (never saved)
        self.last_mode = self.mode
        self.run_mode = self.mode
        self.run_texts = []
        self._build()
        saved = claude_settings.load()
        self.setVisible(saved['show_button'] and saved['panel_open'])
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
        self.transcript.setMinimumHeight(60)
        self.transcript.setMaximumHeight(170)
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
        self.attach_button.clicked.connect(self.choose_image)
        self.use_canvas_check = QCheckBox(self)
        self.use_canvas_check.setChecked(True)  # an empty canvas sends nothing
        self.status_label = QLabel(self)
        self.status_label.setStyleSheet('color: gray;')
        self.send_button = QPushButton(self)
        self.send_button.setStyleSheet('QPushButton { background: #d97757; color: #1f1e1d; font-weight: bold; padding: 4px 14px; }')
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
        row.addWidget(self.send_button)
        body.addLayout(row)

        # The status line, as in Claude Code: the mode on the left (Shift+Tab
        # switches it), then the model, the effort and the session's spending.
        status = QHBoxLayout()
        status.setSpacing(10)
        self.mode_button = QToolButton(self)
        self.mode_button.setObjectName('claudeMode')
        self.mode_button.clicked.connect(self.cycle_mode)
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
        self.session_label = QLabel(self)
        self.session_label.setObjectName('claudeSession')
        status.addWidget(self.mode_button)
        status.addStretch()
        status.addWidget(self.model_button)
        status.addWidget(self.effort_button)
        status.addWidget(self.session_label)
        body.addLayout(status)

    # Its own colors for each app theme: as a child of the canvas it would
    # otherwise take the canvas background (white in every theme).
    THEMES = {
        'dark': dict(bg='#2C2C2C', fg='#FFFFFF', border='#5A5A5A', button='#3A3A3A', hover='#474747',
                     log='#262626', log_border='#3F3F3F', muted='#9A9A9A', user_bg='#393937',
                     user_fg='#F5F4EF', ok='#4FC06F', bad='#E05A4B', auto='#B39DF0', plan='#3CC2B0'),
        'light': dict(bg='#FFFFFF', fg='#000000', border='#B8B8B8', button='#ECECEC', hover='#DCDCDC',
                      log='#FAFAFA', log_border='#D0D0D0', muted='#6F6F6F', user_bg='#ECE9E2',
                      user_fg='#1F1E1D', ok='#2F9E4F', bad='#C0392B', auto='#7457D6', plan='#16897A'),
        'default': dict(bg='#ECECEC', fg='#000000', border='#A8A8A8', button='#E0E0E0', hover='#D2D2D2',
                        log='#FFFFFF', log_border='#C8C8C8', muted='#6F6F6F', user_bg='#E2DED6',
                        user_fg='#1F1E1D', ok='#2F9E4F', bad='#C0392B', auto='#7457D6', plan='#16897A'),
    }

    def apply_theme(self, theme_name):
        c = self.THEMES.get(str(theme_name).lower(), self.THEMES['default'])
        self.colors = c
        if hasattr(self, 'working'):
            self.working.text_color, self.working.muted = QColor(c['fg']), QColor(c['muted'])
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
        """)

    def is_open(self):
        return self.isVisibleTo(self.parentWidget())

    def set_open(self, opened):
        """Show or hide Claude, and remember it for the next time the app opens."""
        opened = bool(opened)
        if opened:
            self.design_waiting = False
        self.setVisible(opened)
        if opened:
            self.place()
            self.raise_()
            self.prompt_edit.setFocus()
        if claude_settings.load()['panel_open'] != opened:
            claude_settings.save(panel_open=opened)
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
        bottom = area.bottom() + 1 - m
        edge = getattr(self.main_window, 'tab_edge', None)
        if edge is not None and edge.isVisible():
            # The tab strip floats over the canvas too: when it is in the lower
            # half, in Claude's way, Claude sits just above it.
            g = edge.geometry()
            if (g.center().y() > area.center().y() and g.top() < bottom
                    and g.right() > area.left() + m and g.left() < area.left() + m + width):
                bottom = g.top() - 6
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
        """Follow the canvas and the widgets around it as they resize, and the
        tab strip as it shows, hides or is dragged."""
        edge = getattr(self.main_window, 'tab_edge', None)
        if edge is not None:
            edge.installEventFilter(self)
        widget = self.parentWidget()
        while widget is not None:
            widget.installEventFilter(self)
            if widget.isWindow():
                break
            widget = widget.parentWidget()

    def eventFilter(self, obj, event):
        if self.isVisible() and (event.type() == QEvent.Resize or (
                obj is getattr(self.main_window, 'tab_edge', None)
                and event.type() in (QEvent.Move, QEvent.Show, QEvent.Hide))):
            self.place()
        return False

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
        self.prompt_edit.setPlaceholderText(t('claude_prompt_placeholder'))
        self.prompt_edit.setToolTip(t('claude_prompt_keys'))
        self.attach_button.setText(t('claude_attach'))
        self.remove_image_button.setText(t('claude_remove_image'))
        self.use_canvas_check.setText(t('claude_use_canvas'))
        self.send_button.setText(t('claude_stop') if self.running() else t('claude_send'))
        self.setLayoutDirection(Qt.RightToLeft if language_code == 'he' else Qt.LeftToRight)
        self.set_image(self.image_path)
        self.refresh_controls()
        self.render_transcript()

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
        last = self.entries[-1] if self.entries else None
        if last and last['kind'] == 'group' and last['end'] is None:
            last['end'] = time.monotonic()
            for step in last['steps']:
                step['running'] = False
            if not last['toggled']:
                last['open'] = False  # folded once Claude has answered
            self.render_transcript()

    def render_transcript(self):
        if not hasattr(self, 'transcript'):
            return
        bar = self.transcript.verticalScrollBar()
        at_end = bar.value() >= bar.maximum() - 4
        keep = bar.value()
        c = self.colors
        body = ''.join(self.entry_html(i, e, c) for i, e in enumerate(self.entries))
        self.transcript.setHtml(f'<div style="color:{c["fg"]};">{body}</div>')
        self.transcript.setVisible(bool(self.entries))
        bar.setValue(bar.maximum() if at_end else keep)

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
            action, current, new = e['what']
            key = 'claude_confirm_rename' if action == 'rename_tab' else 'claude_confirm_switch'
            text = esc(t(key).format(old=current, new=new))
            if e['state'] is None:
                choice = (f'<a href="os:allow/{i}" style="color:#D97757; font-weight:bold; text-decoration:none;">'
                          f'{esc(t("claude_allow"))}</a>&nbsp;&nbsp;&nbsp;<a href="os:deny/{i}" '
                          f'style="color:{c["muted"]}; text-decoration:none;">{esc(t("claude_deny"))}</a>')
            else:
                word = {'allowed': 'claude_allowed', 'denied': 'claude_denied'}.get(e['state'], 'claude_stopped')
                choice = f'<span style="color:{c["muted"]};">{esc(t(word))}</span>'
            return (f'<table cellspacing="0" cellpadding="6" style="margin:4px 0 4px 18px;'
                    f' border:1px solid {c["log_border"]};"><tr><td>{text}<br>{choice}</td></tr></table>')
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
        if step.get('running') and name in SLOW_TOOLS:
            return t('claude_drawing')
        key = TOOL_CHIPS.get(name, (None,))[0]
        return (t(key) if key else name) + (f': {step["summary"]}' if step.get('summary') else '…')

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
            mark = f'<span style="color:#D97757;">●</span>'
        elif step.get('ok'):
            mark = f'<span style="color:{c["ok"]};">✓</span>'
        else:
            mark = f'<span style="color:{c["bad"]};">✗</span>'
        detail = step.get('summary') or ('…' if step.get('running') else '')
        return (f'{mark}&nbsp; <span style="background-color:{bg}; color:{fg}; font-weight:bold;">'
                f'&nbsp;{esc(label)}&nbsp;</span>&nbsp; <span style="color:{c["muted"]};">{esc(detail)}</span>')

    def follow_link(self, url):
        link = url.toString()
        if not link.startswith('os:'):
            QDesktopServices.openUrl(url)
            return
        what, *ids = link[3:].split('/')
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
            if self.bridge is not None:
                reply = self.bridge.decide(entry['id'], allowed)
                if reply is not None:
                    self.answer(reply)
        elif what == 'plan' and not entry['built'] and not self.running():
            self.build_plan(entry)
            return
        self.render_transcript()

    # -------------------------------------------------------- status line
    MODE_LOOK = {'ask': ('⏵', 'muted', 'claude_mode_ask'), 'auto': ('⏵⏵', 'auto', 'claude_mode_auto'),
                 'plan': ('⏸', 'plan', 'claude_mode_plan')}

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
        glyph, color, key = self.MODE_LOOK[self.mode]
        self.mode_button.setText(f'{glyph} {t(key)}  ·  {t("claude_mode_cycle")}')
        self.mode_button.setStyleSheet(f'QToolButton {{ color: {c[color]}; }}')
        names = dict(claude_settings.MODELS)
        self.model_menu.clear()
        group = QActionGroup(self.model_menu)
        for model, label_key in claude_settings.MODELS:
            action = QAction(t(label_key), self.model_menu, checkable=True)
            action.setChecked(model == saved['model'])
            action.triggered.connect(lambda _=False, m=model: self.choose(model=m))
            group.addAction(action)
            self.model_menu.addAction(action)
        self.model_button.setText(('Sonnet 5.5' if 'sonnet' in saved['model'] else 'Haiku 5.5') + ' ▾')
        self.effort_menu.clear()
        group = QActionGroup(self.effort_menu)
        for effort in claude_settings.EFFORTS:
            action = QAction(t(f'claude_effort_{effort}'), self.effort_menu, checkable=True)
            action.setChecked(effort == saved['effort'])
            action.triggered.connect(lambda _=False, e=effort: self.choose(effort=e))
            group.addAction(action)
            self.effort_menu.addAction(action)
        self.effort_button.setText(t(f'claude_effort_{saved["effort"]}') + ' ▾')
        self.show_session()

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
        if not prompt or self.running():
            return
        self.set_open(True)
        if getattr(sys, 'frozen', False):
            self.add_note(_tr(self.language, 'claude_source_only'), '#c0392b')
            return
        settings = claude_settings.load()
        if not settings['api_key']:
            self.add_note(_tr(self.language, 'claude_need_key'), '#c0392b')
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
        # One request may spend its own limit, but never past what the session has left.
        program, args = agent_command(prompt, settings['model'], self.out_dir,
                                      [self.image_path] if self.image_path else [], start,
                                      web=settings['web'], max_cost=min(settings['max_cost'], left),
                                      effort=settings['effort'], plan=self.mode == 'plan',
                                      app=self.bridge is not None)
        env = QProcessEnvironment.systemEnvironment()
        env.insert('ANTHROPIC_API_KEY', settings['api_key'])
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
        # What this request has cost so far; the total keeps counting from
        # everything earlier requests cost, saved in claude.json.
        self.run_cost, self.total_before = 0.0, claude_settings.load()['spent']
        self.run_mode, self.run_texts = self.mode, []
        self.add_user((shown or prompt) + (f'  [{os.path.basename(self.image_path)}]' if self.image_path else ''))
        if typed:
            self.prompt_edit.clear()
        self.set_image(None)
        self.status_label.setText(_tr(self.language, 'claude_working'))
        self.working.start(_tr(self.language, 'claude_thinking') + '…')
        self.activity_changed.emit()
        self.send_button.setText(_tr(self.language, 'claude_stop'))
        self.process.start(program, args)

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
            self.handle_event(event)

    def read_errors(self):
        if self.process is not None:
            self.stderr_text += bytes(self.process.readAllStandardError()).decode('utf-8', 'replace')

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
            step = {'kind': 'tool', 'name': event.get('name', ''), 'running': True, 'ok': None, 'summary': ''}
            self.add_step(step)
            self.working.set_label(self.step_label(step, running=True))
        elif kind == 'tool_end':
            name = event.get('name', '')
            group = self.open_group()
            step = next((s for s in reversed(group['steps'])
                         if s['kind'] == 'tool' and s['name'] == name and s.get('running')), None)
            if step is None:
                step = {'kind': 'tool', 'name': name}
                group['steps'].append(step)
            step.update(running=False, ok=bool(event.get('ok')), summary=event.get('summary', ''))
            self.render_transcript()
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
        self.design_waiting = self.design_waiting or not self.is_open()
        self.add_entry({'kind': 'confirm', 'id': call_id, 'what': what, 'state': None})
        self.activity_changed.emit()

    def finished(self, *_):
        try:
            self._finish()
        finally:
            self.activity_changed.emit()  # the Claude button stops turning

    def _finish(self):
        self.read_events(flush=True)
        self.read_errors()
        if self.bridge is not None:
            self.bridge.forget()
        for entry in self.entries:
            if entry['kind'] == 'confirm' and entry['state'] is None:
                entry['state'] = 'expired'  # Claude has stopped; nothing waits any more
        self.working.stop()
        self.close_group()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        event = self.done_event
        if event is not None:
            self.run_cost = max(self.run_cost, float(event.get('cost') or 0))
        spent, line = self.run_cost, self.cost_line()
        self.save_spending()
        if event is None:
            lines = [l for l in self.stderr_text.splitlines() if l.strip()]
            message = lines[-1] if lines else 'the agent stopped without an answer'
            self.status_label.setText(line if spent else '')
            self.add_note(_tr(self.language, 'claude_failed').format(error=message.removeprefix('error: ')), '#c0392b')
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
            project = None  # Claude opened its tabs itself, through the bridge
        if project and os.path.exists(project):
            named = os.path.join(self.out_dir, design_name(self.prompt) + '.json')
            shutil.copyfile(project, named)
            png = event.get('png')
            picture = None
            if png and os.path.exists(png):
                picture = named[:-5] + '.png'
                shutil.copyfile(png, picture)
            self.design_waiting = not self.is_open()
            if self.run_mode == 'ask':  # wait for "Open in new tab"
                self.add_entry({'kind': 'design', 'path': named, 'png': picture, 'opened': False,
                                'name': os.path.basename(named)})
            else:
                self.add_note(_tr(self.language, 'claude_opened').format(name=os.path.basename(named)))
                self.design_ready.emit(named)


class ClaudeButton(QPushButton):
    """The Claude button next to Settings: shows and hides Claude.

    The Claude app icon at the size of the Settings button, drawn here so it
    answers the mouse the way Claude's own buttons do: lighter under the
    pointer, a little smaller and darker while pressed, and, while Claude is
    open, darker with a light ring. While Claude is hidden it also shows what
    Claude is doing: an arc turns around it during a run, and a green dot
    waits on it when a design has opened."""

    ORANGE = QColor('#D97757')
    HOVER = QColor('#E3896B')
    PRESSED = QColor('#C2613F')
    OPEN = QColor('#B9583A')
    RADIUS = 7  # corner radius of the 32 px square, as the Claude app icon

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.setObjectName('claudeButton')
        self.setCheckable(True)
        self.setFixedSize(32, 32)
        self.setAccessibleName('Claude')
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor)
        self.mark = QPixmap(resource_path('claude_mark_white.png'))
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
        return self.ORANGE

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        square = QRectF(self.rect())
        if self.isDown():  # pressed in: a touch smaller
            square = square.adjusted(1.5, 1.5, -1.5, -1.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.color())
        painter.drawRoundedRect(square, self.RADIUS, self.RADIUS)
        if self.isChecked():  # Claude is open
            painter.setPen(QPen(QColor(255, 255, 255, 170), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(square.adjusted(1.5, 1.5, -1.5, -1.5), self.RADIUS - 1.5, self.RADIUS - 1.5)
        if not self.mark.isNull():
            inset = square.width() * 0.17
            painter.drawPixmap(square.adjusted(inset, inset, -inset, -inset), self.mark, QRectF(self.mark.rect()))
        else:
            painter.setPen(Qt.white)
            painter.drawText(square, Qt.AlignCenter, '✳')
        if self.busy():
            pen = QPen(QColor(255, 255, 255, 230), 2.5)
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

    def __init__(self, language_code='en', parent=None):
        super().__init__(parent)
        self.language = language_code
        layout = QVBoxLayout(self)
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

        self.key_label = QLabel(self)
        layout.addWidget(self.key_label)
        key_row = QHBoxLayout()
        self.key_edit = QLineEdit(self)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText('sk-ant-…')
        self.show_button = QPushButton(self)
        self.show_button.setCheckable(True)
        self.show_button.toggled.connect(self.toggle_shown)
        self.save_button = QPushButton(self)
        self.save_button.clicked.connect(self.save_key)
        self.remove_button = QPushButton(self)
        self.remove_button.clicked.connect(self.remove_key)
        layout.addWidget(self.key_edit)
        key_row.addWidget(self.show_button)
        key_row.addWidget(self.save_button)
        key_row.addWidget(self.remove_button)
        key_row.addStretch()
        layout.addLayout(key_row)
        self.key_status = QLabel(self)
        layout.addWidget(self.key_status)
        self.get_key = QLabel(self)
        self.get_key.setOpenExternalLinks(True)
        self.get_key.setTextFormat(Qt.RichText)
        layout.addWidget(self.get_key)

        self.model_label = QLabel(self)
        layout.addWidget(self.model_label)
        self.model_combo = QComboBox(self)
        self.model_combo.currentIndexChanged.connect(self.save_model)
        layout.addWidget(self.model_combo)

        self.effort_label = QLabel(self)
        layout.addWidget(self.effort_label)
        self.effort_combo = QComboBox(self)
        self.effort_combo.currentIndexChanged.connect(self.save_effort)
        layout.addWidget(self.effort_combo)
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

        limit_row = QHBoxLayout()
        self.limit_label = QLabel(self)
        self.limit_spin = QDoubleSpinBox(self)
        self.limit_spin.setRange(*claude_settings.MAX_COST_RANGE)
        self.limit_spin.setDecimals(2)
        self.limit_spin.setSingleStep(0.50)
        self.limit_spin.setPrefix('$')
        self.limit_spin.valueChanged.connect(lambda value: self.changed_setting(max_cost=value))
        limit_row.addWidget(self.limit_label)
        limit_row.addWidget(self.limit_spin)
        limit_row.addStretch()
        layout.addLayout(limit_row)

        session_row = QHBoxLayout()
        self.session_limit_label = QLabel(self)
        self.session_spin = QDoubleSpinBox(self)
        self.session_spin.setRange(*claude_settings.SESSION_LIMIT_RANGE)
        self.session_spin.setDecimals(2)
        self.session_spin.setSingleStep(1.00)
        self.session_spin.setPrefix('$')
        self.session_spin.valueChanged.connect(lambda value: self.changed_setting(session_limit=value))
        session_row.addWidget(self.session_limit_label)
        session_row.addWidget(self.session_spin)
        session_row.addStretch()
        layout.addLayout(session_row)

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

        self.storage = QLabel(self)
        self.storage.setWordWrap(True)
        self.storage.setStyleSheet('color: gray;')
        layout.addWidget(self.storage)
        layout.addStretch()
        self.retranslate(language_code)

    def retranslate(self, language_code):
        self.language = language_code
        t = lambda key: _tr(language_code, key)
        self.intro.setText(t('claude_settings_intro'))
        self.key_label.setText(t('claude_api_key_label'))
        self.show_button.setText(t('claude_hide_key') if self.show_button.isChecked() else t('claude_show_key'))
        self.save_button.setText(t('claude_save_key'))
        self.remove_button.setText(t('claude_remove_key'))
        self.get_key.setText(t('claude_get_key'))
        self.model_label.setText(t('claude_model_label'))
        self.storage.setText(t('claude_key_storage'))
        saved = claude_settings.load()
        self.model_combo.blockSignals(True)
        self.model_combo.clear()
        for model, key in claude_settings.MODELS:
            self.model_combo.addItem(t(key), model)
        self.model_combo.setCurrentIndex(max(0, self.model_combo.findData(saved['model'])))
        self.model_combo.blockSignals(False)
        self.effort_label.setText(t('claude_effort_label'))
        self.effort_hint.setText(t('claude_effort_hint'))
        self.session_limit_label.setText(t('claude_session_limit_label'))
        self.web_check.setText(t('claude_web_label'))
        self.web_hint.setText(t('claude_web_hint'))
        self.limit_label.setText(t('claude_limit_label'))
        self.web_check.blockSignals(True)
        self.web_check.setChecked(saved['web'])
        self.web_check.blockSignals(False)
        self.limit_spin.blockSignals(True)
        self.limit_spin.setValue(saved['max_cost'])
        self.limit_spin.blockSignals(False)
        self.show_choices()
        self.show_saved(saved['api_key'])
        self.show_check.setText(t('claude_show_button'))
        self.show_hint.setText(t('claude_show_button_hint'))
        self.show_check.blockSignals(True)
        self.show_check.setChecked(saved['show_button'])
        self.show_check.blockSignals(False)
        self.reset_spent_button.setText(t('claude_spent_reset'))
        self.spent_hint.setText(t('claude_spent_hint'))
        self.show_spending()
        self.setLayoutDirection(Qt.RightToLeft if language_code == 'he' else Qt.LeftToRight)

    def showEvent(self, event):
        super().showEvent(event)
        self.show_spending()  # requests may have run since the page was built
        self.show_choices()  # the status line may have changed the model or effort

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

    def set_show_button(self, shown):
        claude_settings.save(show_button=shown)
        self.show_button_changed.emit(bool(shown))

    def show_saved(self, key):
        t = lambda k: _tr(self.language, k)
        self.key_status.setText(t('claude_key_saved').format(key=claude_settings.masked(key)) if key
                                else t('claude_key_none'))
        self.remove_button.setEnabled(bool(key))

    def toggle_shown(self, shown):
        self.key_edit.setEchoMode(QLineEdit.Normal if shown else QLineEdit.Password)
        self.show_button.setText(_tr(self.language, 'claude_hide_key' if shown else 'claude_show_key'))

    def save_key(self):
        key = self.key_edit.text().strip()
        if not key:
            return
        claude_settings.save(api_key=key)
        self.key_edit.clear()
        self.show_saved(key)

    def remove_key(self):
        claude_settings.save(api_key='')
        self.show_saved('')
        self.key_status.setText(_tr(self.language, 'claude_key_removed'))

    def changed_setting(self, **change):
        claude_settings.save(**change)
        self.settings_changed.emit()

    def save_effort(self, index):
        effort = self.effort_combo.itemData(index)
        if effort:
            self.changed_setting(effort=effort)

    def save_model(self, index):
        model = self.model_combo.itemData(index)
        if model:
            self.changed_setting(model=model)
