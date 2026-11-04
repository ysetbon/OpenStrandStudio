"""The Claude panel under the canvas, and the Settings > Claude page.

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

from PyQt5.QtCore import QProcess, QProcessEnvironment, Qt, pyqtSignal
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSizePolicy, QTextBrowser, QToolButton, QVBoxLayout, QWidget)

import claude_settings
from translations import translations

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each tool shows as a chip in the colors of the app's own button for that job.
TOOL_CHIPS = {
    'make_turks_head': ('add_new_strand', '#93e993', '#1a1a1a'),
    'make_mxn': ('add_new_strand', '#93e993', '#1a1a1a'),
    'make_heart': ('add_new_strand', '#93e993', '#1a1a1a'),
    'load_sample': ('load', '#a07a6a', '#1a1a1a'),
    'search_samples': ('load', '#a07a6a', '#1a1a1a'),
    'render': ('save_image', '#8a3a55', '#ffffff'),
}
OTHER_CHIP = ('#d4d4d4', '#1a1a1a')


def _tr(language, key):
    table = translations.get(language) or translations['en']
    return table.get(key) or translations['en'].get(key, key)


def agent_command(prompt, model, out_dir, images=(), start=None):
    """The program and arguments that run one agent request."""
    args = ['-m', 'openstrand', 'agent', prompt, '--model', model, '--out-dir', out_dir, '--json-events']
    for image in images:
        args += ['--image', image]
    if start:
        args += ['--start', start]
    return sys.executable, args


def design_name(prompt):
    """A file name from the request: '5x3 bracelet in teal' -> '5x3_bracelet_in_teal'."""
    words = re.findall(r'[\w×]+', prompt.lower(), re.UNICODE)[:6]
    return '_'.join(words).replace('×', 'x')[:48] or 'claude_design'


class ClaudePanel(QWidget):
    """A slim bar under the canvas that opens into the conversation with Claude."""

    design_ready = pyqtSignal(str)  # path of the finished project file

    def __init__(self, main_window, language_code='en'):
        super().__init__(main_window)
        self.main_window = main_window
        self.language = language_code
        self.process = None
        self.image_path = None
        self.out_dir = None
        self.prompt = ''
        self.done_event = None
        self.stdout_buffer = b''
        self.stderr_text = ''
        self._build()
        self.set_open(False)
        self.retranslate(language_code)

    # ------------------------------------------------------------------ UI
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = QWidget(self)
        header = QHBoxLayout(self.header)
        header.setContentsMargins(8, 3, 8, 3)
        header.setSpacing(8)
        self.toggle_button = QToolButton(self.header)
        self.toggle_button.setAutoRaise(True)
        self.toggle_button.clicked.connect(lambda: self.set_open(not self.body.isVisible()))
        self.title_label = QLabel('Claude', self.header)
        self.title_label.setStyleSheet('font-weight: bold; color: #d97757;')
        self.hint_label = QLabel(self.header)
        self.hint_label.setStyleSheet('color: gray;')
        self.status_label = QLabel(self.header)
        self.status_label.setStyleSheet('color: gray;')
        header.addWidget(self.toggle_button)
        header.addWidget(self.title_label)
        header.addWidget(self.hint_label)
        header.addStretch()
        header.addWidget(self.status_label)
        layout.addWidget(self.header)

        self.body = QWidget(self)
        body = QVBoxLayout(self.body)
        body.setContentsMargins(8, 0, 8, 8)
        body.setSpacing(6)
        self.transcript = QTextBrowser(self.body)
        self.transcript.setOpenExternalLinks(True)
        self.transcript.setMinimumHeight(120)
        self.transcript.setMaximumHeight(220)
        body.addWidget(self.transcript)

        self.image_row = QWidget(self.body)
        image_row = QHBoxLayout(self.image_row)
        image_row.setContentsMargins(0, 0, 0, 0)
        self.image_label = QLabel(self.image_row)
        self.remove_image_button = QPushButton(self.image_row)
        self.remove_image_button.clicked.connect(lambda: self.set_image(None))
        image_row.addWidget(self.image_label)
        image_row.addWidget(self.remove_image_button)
        image_row.addStretch()
        body.addWidget(self.image_row)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.prompt_edit = QLineEdit(self.body)
        self.prompt_edit.returnPressed.connect(self.send)
        self.attach_button = QPushButton(self.body)
        self.attach_button.clicked.connect(self.choose_image)
        self.use_canvas_check = QCheckBox(self.body)
        self.use_canvas_check.setChecked(True)  # an empty canvas sends nothing
        self.send_button = QPushButton(self.body)
        self.send_button.setStyleSheet('QPushButton { background: #d97757; color: #1f1e1d; font-weight: bold; padding: 4px 14px; }')
        self.send_button.clicked.connect(self.send_or_stop)
        row.addWidget(self.prompt_edit, 1)
        row.addWidget(self.attach_button)
        row.addWidget(self.use_canvas_check)
        row.addWidget(self.send_button)
        body.addLayout(row)
        layout.addWidget(self.body)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def set_open(self, opened):
        self.body.setVisible(opened)
        self.toggle_button.setArrowType(Qt.DownArrow if opened else Qt.UpArrow)
        self.toggle_button.setToolTip(_tr(self.language, 'claude_hide_panel' if opened else 'claude_show_panel'))
        if opened:
            self.prompt_edit.setFocus()

    def retranslate(self, language_code):
        self.language = language_code
        t = lambda key: _tr(language_code, key)
        self.hint_label.setText(t('claude_panel_hint'))
        self.prompt_edit.setPlaceholderText(t('claude_prompt_placeholder'))
        self.attach_button.setText(t('claude_attach'))
        self.remove_image_button.setText(t('claude_remove_image'))
        self.use_canvas_check.setText(t('claude_use_canvas'))
        self.send_button.setText(t('claude_stop') if self.running() else t('claude_send'))
        self.toggle_button.setToolTip(t('claude_hide_panel' if self.body.isVisible() else 'claude_show_panel'))
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
                                      [self.image_path] if self.image_path else [], start)
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
        self.add_user(prompt + (f'  [{os.path.basename(self.image_path)}]' if self.image_path else ''))
        self.prompt_edit.clear()
        self.set_image(None)
        self.status_label.setText(_tr(self.language, 'claude_working'))
        self.send_button.setText(_tr(self.language, 'claude_stop'))
        self.process.start(program, args)

    def failed_to_start(self, error):
        if error != QProcess.FailedToStart:
            return  # a crash or kill still ends in finished()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        self.status_label.setText('')
        self.add_note(_tr(self.language, 'claude_failed').format(error=self.process.errorString()), '#c0392b')

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
        elif kind == 'tool_end':
            self.add_tool(event.get('name', ''), event.get('ok', False), event.get('summary', ''))
        elif kind == 'usage':
            self.status_label.setText(f"{_tr(self.language, 'claude_working')}  ${event.get('cost', 0):.3f}")
        elif kind == 'done':
            self.done_event = event

    def finished(self, *_):
        self.read_events(flush=True)
        self.read_errors()
        self.send_button.setText(_tr(self.language, 'claude_send'))
        event = self.done_event
        if event is None:
            lines = [l for l in self.stderr_text.splitlines() if l.strip()]
            message = lines[-1] if lines else 'the agent stopped without an answer'
            self.status_label.setText('')
            self.add_note(_tr(self.language, 'claude_failed').format(error=message.removeprefix('error: ')), '#c0392b')
            return
        model = 'Sonnet 5.5' if 'sonnet' in event.get('model', '') else 'Haiku 5.5'
        self.status_label.setText(f"{model} · ${event.get('cost', 0):.3f}")
        if event.get('error'):
            self.add_note(_tr(self.language, 'claude_failed').format(error=event['error']), '#c0392b')
        project = event.get('project')
        if project and os.path.exists(project):
            named = os.path.join(self.out_dir, design_name(self.prompt) + '.json')
            shutil.copyfile(project, named)
            self.add_note(_tr(self.language, 'claude_opened').format(name=os.path.basename(named)))
            self.design_ready.emit(named)


class ClaudeSettingsPage(QWidget):
    """Settings > Claude: the Anthropic API key and the model."""

    def __init__(self, language_code='en', parent=None):
        super().__init__(parent)
        self.language = language_code
        layout = QVBoxLayout(self)
        self.intro = QLabel(self)
        self.intro.setWordWrap(True)
        layout.addWidget(self.intro)

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
        self.show_saved(saved['api_key'])
        self.setLayoutDirection(Qt.RightToLeft if language_code == 'he' else Qt.LeftToRight)

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
