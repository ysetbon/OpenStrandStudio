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
import os
import re
import shutil
import sys
import time

from PyQt5.QtCore import (QDate, QEvent, QLocale, QPoint, QProcess, QProcessEnvironment, QRect, QRectF,
                          Qt, QTimer, pyqtSignal)
from PyQt5.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSizePolicy, QTextBrowser, QTextEdit, QVBoxLayout,
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
}
OTHER_CHIP = ('#d4d4d4', '#1a1a1a')
# Tools that can take up to a minute: the panel says so when they start.
SLOW_TOOLS = {'draw_design', 'make_heart', 'make_turks_head'}


def _tr(language, key):
    table = translations.get(language) or translations['en']
    return table.get(key) or translations['en'].get(key, key)


def agent_command(prompt, model, out_dir, images=(), start=None, web=True, max_cost=None):
    """The program and arguments that run one agent request."""
    args = ['-m', 'openstrand', 'agent', prompt, '--model', model, '--out-dir', out_dir, '--json-events']
    if not web:
        args.append('--no-web')
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


def design_name(prompt):
    """A file name from the request: '5x3 bracelet in teal' -> '5x3_bracelet_in_teal'."""
    words = re.findall(r'[\w×]+', prompt.lower(), re.UNICODE)[:6]
    return '_'.join(words).replace('×', 'x')[:48] or 'claude_design'


class PromptBox(QTextEdit):
    """The chat box: Enter sends, Shift+Enter starts a new line, and the box
    grows with what is typed up to MAX_LINES, then scrolls."""
    submitted = pyqtSignal()
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
        self.transcript.setOpenExternalLinks(True)
        self.transcript.setMinimumHeight(60)
        self.transcript.setMaximumHeight(150)
        self.transcript.hide()
        body.addWidget(self.transcript)

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

    # Its own colors for each app theme: as a child of the canvas it would
    # otherwise take the canvas background (white in every theme).
    THEMES = {
        'dark': dict(bg='#2C2C2C', fg='#FFFFFF', border='#5A5A5A', button='#3A3A3A', hover='#474747',
                     log='#262626', log_border='#3F3F3F'),
        'light': dict(bg='#FFFFFF', fg='#000000', border='#B8B8B8', button='#ECECEC', hover='#DCDCDC',
                      log='#FAFAFA', log_border='#D0D0D0'),
        'default': dict(bg='#ECECEC', fg='#000000', border='#A8A8A8', button='#E0E0E0', hover='#D2D2D2',
                        log='#FFFFFF', log_border='#C8C8C8'),
    }

    def apply_theme(self, theme_name):
        c = self.THEMES.get(str(theme_name).lower(), self.THEMES['default'])
        self.setStyleSheet(f"""
            QWidget#claudePanel {{ background-color: {c['bg']}; border: 1px solid {c['border']}; border-radius: 10px; }}
            #claudePanel QWidget {{ background-color: {c['bg']}; color: {c['fg']}; }}
            #claudePanel QLabel, #claudePanel QCheckBox {{ background-color: transparent; color: {c['fg']}; }}
            #claudePanel QPushButton {{ background-color: {c['button']}; color: {c['fg']}; border: none;
                                        border-radius: 4px; padding: 5px 10px; }}
            #claudePanel QPushButton:hover {{ background-color: {c['hover']}; }}
            #claudePanel QTextBrowser {{ background-color: {c['log']}; color: {c['fg']};
                                         border: 1px solid {c['log_border']}; border-radius: 6px; }}
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
        height = min(height, max(80, area.height() - 2 * m))
        self.setGeometry(area.left() + m, area.bottom() + 1 - m - height, width, height)

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
        if event.type() == QEvent.Resize and self.isVisible():
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
    def add_html(self, fragment):
        self.transcript.show()
        self.transcript.append(fragment)
        bar = self.transcript.verticalScrollBar()
        bar.setValue(bar.maximum())

    def add_user(self, text):
        self.add_html(f'<p style="margin:6px 0;"><span style="background:#393937; color:#f5f4ef;">'
                      f'&nbsp;{html.escape(text)}&nbsp;</span></p>')

    def add_claude(self, text):
        self.add_html(f'<p style="margin:4px 0;"><b style="color:#d97757;">✳</b> {html.escape(text)}</p>')

    def add_note(self, text, color='gray'):
        self.add_html(f'<p style="margin:4px 0; color:{color};">{html.escape(text)}</p>')

    def add_tool(self, name, ok, summary):
        key, bg, fg = TOOL_CHIPS.get(name, (None, *OTHER_CHIP))
        label = _tr(self.language, key) if key else name
        mark = '<span style="color:#2f9e4f;">✓</span>' if ok else '<span style="color:#c0392b;">✗</span>'
        self.add_html(f'<p style="margin:2px 0 2px 16px;">{mark} '
                      f'<span style="background:{bg}; color:{fg}; font-weight:bold;">&nbsp;{html.escape(label)}&nbsp;</span> '
                      f'{html.escape(summary)}</p>')

    # ------------------------------------------------------------- running
    def running(self):
        return self.process is not None and self.process.state() != QProcess.NotRunning

    def send_or_stop(self):
        if self.running():
            self.process.kill()
            self.add_note(_tr(self.language, 'claude_stopped'))
        else:
            self.send()

    def send(self):
        prompt = self.prompt_edit.text().strip()
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
        self.prompt = prompt
        stamp = time.strftime('%Y%m%d-%H%M%S')
        self.out_dir = os.path.join(claude_settings.settings_directory(), 'claude_designs', stamp)
        os.makedirs(self.out_dir, exist_ok=True)
        start = None
        if self.use_canvas_check.isChecked():
            start = self.write_canvas(os.path.join(self.out_dir, 'canvas.json'))
        program, args = agent_command(prompt, settings['model'], self.out_dir,
                                      [self.image_path] if self.image_path else [], start,
                                      web=settings['web'], max_cost=settings['max_cost'])
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
        self.add_user(prompt + (f'  [{os.path.basename(self.image_path)}]' if self.image_path else ''))
        self.prompt_edit.clear()
        self.set_image(None)
        self.status_label.setText(_tr(self.language, 'claude_working'))
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
            self.run_cost = 0.0
            self.spending_changed.emit()

    def failed_to_start(self, error):
        if error != QProcess.FailedToStart:
            return  # a crash or kill still ends in finished()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        self.status_label.setText('')
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
        if kind == 'text':
            self.add_claude(event.get('text', ''))
        elif kind == 'thinking':
            text = event.get('text', '')
            text = text if len(text) <= 600 else text[:600].rsplit(' ', 1)[0] + '…'
            self.add_html(f'<p style="margin:2px 0 2px 16px; color:gray;"><i>'
                          f"{html.escape(_tr(self.language, 'claude_thinking'))}: {html.escape(text)}</i></p>")
        elif kind == 'search':
            key = 'claude_reading' if event.get('name') == 'web_fetch' else 'claude_searching'
            value = event.get('query', '')
            self.add_note(_tr(self.language, key).format(query=value, url=value))
        elif kind == 'note':
            self.add_note(event.get('text', ''))
        elif kind == 'tool_start' and event.get('name') in SLOW_TOOLS:
            self.add_note(_tr(self.language, 'claude_drawing'))
        elif kind == 'tool_end':
            self.add_tool(event.get('name', ''), event.get('ok', False), event.get('summary', ''))
        elif kind == 'usage':
            self.run_cost = max(self.run_cost, float(event.get('cost') or 0))
            self.status_label.setText(f"{_tr(self.language, 'claude_working')} · {self.cost_line()}")
        elif kind == 'done':
            self.done_event = event

    def finished(self, *_):
        try:
            self._finish()
        finally:
            self.activity_changed.emit()  # the Claude button stops turning

    def _finish(self):
        self.read_events(flush=True)
        self.read_errors()
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
        model = 'Sonnet 5.5' if 'sonnet' in event.get('model', '') else 'Haiku 5.5'
        self.status_label.setText(f"{model} · {line}")
        if event.get('error'):
            self.add_note(_tr(self.language, 'claude_failed').format(error=event['error']), '#c0392b')
        project = event.get('project')
        if project and os.path.exists(project):
            named = os.path.join(self.out_dir, design_name(self.prompt) + '.json')
            shutil.copyfile(project, named)
            self.add_note(_tr(self.language, 'claude_opened').format(name=os.path.basename(named)))
            self.design_waiting = not self.is_open()
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
        self.limit_spin.valueChanged.connect(lambda value: claude_settings.save(max_cost=value))
        limit_row.addWidget(self.limit_label)
        limit_row.addWidget(self.limit_spin)
        limit_row.addStretch()
        layout.addLayout(limit_row)

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
        self.web_check.setText(t('claude_web_label'))
        self.web_hint.setText(t('claude_web_hint'))
        self.limit_label.setText(t('claude_limit_label'))
        self.web_check.blockSignals(True)
        self.web_check.setChecked(saved['web'])
        self.web_check.blockSignals(False)
        self.limit_spin.blockSignals(True)
        self.limit_spin.setValue(saved['max_cost'])
        self.limit_spin.blockSignals(False)
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

    def save_model(self, index):
        model = self.model_combo.itemData(index)
        if model:
            claude_settings.save(model=model)
