"""UI sound effects.

All sounds live in src/sounds as short WAV files and are played through one
SoundManager so every control family plays the same file everywhere.

Two ways sounds get triggered:
  * UiSoundFilter, installed on the QApplication, maps generic controls by
    type (buttons, checkboxes, sliders, dropdowns, menus, dialogs) to a cue.
  * Direct play() calls for actions that are not a widget click, such as
    dragging on the canvas, attaching a strand, undo/redo and saving.

A widget can override the filter with the dynamic property "soundCue": a cue
name, a toggle's pair as "name_{state}" (played as name_on / name_off),
or "none" when the sound is played elsewhere (e.g. from its clicked
signal, so keyboard shortcuts that call click() sound too).
"""

import os
import sys
import time

from PyQt5.QtCore import QObject, QEvent, Qt, QTimer, QUrl
from PyQt5.QtWidgets import (
    QAbstractButton, QAbstractSlider, QApplication, QCheckBox, QComboBox,
    QDialog, QMenu, QMessageBox,
)

try:
    from PyQt5.QtMultimedia import QSoundEffect
except ImportError:  # QtMultimedia missing: the app runs silently
    QSoundEffect = None


# cue -> minimum gap in ms between two plays of the same cue
CUES = {
    'ui_click': 40,
    'ui_toggle_on': 40, 'ui_toggle_off': 40,
    'toggle_blue_on': 40, 'toggle_blue_off': 40,
    'toggle_green_on': 40, 'toggle_green_off': 40,
    'layer_select': 40,
    'ui_hover': 80,
    'canvas_hover_point': 80,
    'mode_view': 60, 'mode_select': 60, 'mode_move': 60, 'mode_attach': 60,
    'mode_rotate': 60, 'mode_angle': 60,
    'toolbar_action': 40, 'toolbar_image': 40, 'toolbar_settings': 40,
    'toggle_shadow_on': 40, 'toggle_shadow_off': 40,
    'toggle_tabs_on': 40, 'toggle_tabs_off': 40,
    'layer_state_on': 40, 'layer_state_off': 40,
    'toggle_points_on': 40, 'toggle_points_off': 40,
    'drag_pickup': 60, 'drag_drop': 60,
    'snap_grid': 60,
    'attach_start': 60, 'attach_complete': 60,
    'new_strand': 80,
    'delete': 80,
    'undo': 60, 'redo': 60,
    'save_done': 200,
    'denied': 150,
    'dialog_open': 120, 'dialog_close': 120,
    'menu_open': 80,
    'stepper_plus': 70, 'stepper_minus': 70,
    'tab_switch': 60,
}
HOVER_CUES = {'ui_hover', 'canvas_hover_point'}
SLIDER_TICK_CUE = 'snap_grid'
SLIDER_TICK_GAP_MS = 40

# Settings lines in user_settings.txt
SETTING_ENABLED = 'SoundEnabled'
SETTING_VOLUME = 'SoundVolume'
SETTING_HOVER = 'SoundHover'


def sounds_dir():
    if getattr(sys, 'frozen', False):
        # Same layout as the app's other bundled files (icons, flags, guide images)
        if sys.platform.startswith('darwin'):
            return os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'sounds')
        return os.path.join(sys._MEIPASS, 'sounds')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')


def settings_file_path():
    app_name = "OpenStrandStudio"
    if sys.platform.startswith('darwin'):
        base = os.path.expanduser('~/Library/Application Support')
    else:
        base = os.environ.get('APPDATA', '')
    return os.path.join(base, app_name, 'user_settings.txt')


class SoundManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.volume = 70  # 0-100
        self.hover_enabled = True
        self._effects = {}
        self._last_played = {}
        self._load_settings()
        if QSoundEffect is None:
            return
        folder = sounds_dir()
        for cue in CUES:
            path = os.path.join(folder, f'{cue}.wav')
            if os.path.exists(path):
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(path))
                self._effects[cue] = effect
        self._apply_volume()

    def _load_settings(self):
        path = settings_file_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    key, _, value = line.partition(':')
                    value = value.strip().lower()
                    if key == SETTING_ENABLED:
                        self.enabled = value == 'true'
                    elif key == SETTING_VOLUME:
                        self.volume = max(0, min(100, int(float(value))))
                    elif key == SETTING_HOVER:
                        self.hover_enabled = value == 'true'
        except (OSError, ValueError):
            pass

    def settings_lines(self):
        """Lines the settings dialog writes into user_settings.txt."""
        return [
            f"{SETTING_ENABLED}: {str(self.enabled).lower()}",
            f"{SETTING_VOLUME}: {self.volume}",
            f"{SETTING_HOVER}: {str(self.hover_enabled).lower()}",
        ]

    def _apply_volume(self):
        level = self.volume / 100.0
        for effect in self._effects.values():
            effect.setVolume(level)

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)

    def set_volume(self, volume):
        self.volume = max(0, min(100, int(volume)))
        self._apply_volume()

    def set_hover_enabled(self, enabled):
        self.hover_enabled = bool(enabled)

    def preview(self, cue, volume):
        """Play cue once at a volume that is not applied yet (the settings slider)."""
        effect = self._effects.get(cue)
        if effect is None:
            return
        effect.setVolume(max(0, min(100, int(volume))) / 100.0)
        effect.play()
        QTimer.singleShot(400, self._apply_volume)

    def play(self, cue):
        if not self.enabled or self.volume == 0:
            return
        if cue in HOVER_CUES and not self.hover_enabled:
            return
        effect = self._effects.get(cue)
        if effect is None:
            return
        now = time.monotonic() * 1000
        if now - self._last_played.get(cue, -1e9) < CUES.get(cue, 40):
            return
        self._last_played[cue] = now
        effect.play()


_manager = None


def manager():
    global _manager
    if _manager is None:
        _manager = SoundManager(QApplication.instance())
    return _manager


def play(cue):
    """Play a cue. Safe to call from anywhere, before or after setup."""
    if QApplication.instance() is None:
        return
    manager().play(cue)


def set_cue(widget, cue):
    """Give one widget a fixed cue, "name_{state}" for a toggle's on/off pair,
    or "none" to keep the filter quiet for it."""
    widget.setProperty('soundCue', cue)


def play_on_click(button, cue):
    """Play cue from the button's clicked signal (covers keyboard shortcuts that call click())."""
    set_cue(button, 'none')
    button.clicked.connect(lambda *_: play(cue))


class UiSoundFilter(QObject):
    """App-wide filter that gives every generic control its family sound.

    main_window: toggles in it use the toolbar toggle sound, and only its
        buttons play hover sounds.
    green_windows: window classes whose toggles use the green palette.
    green_buttons: single buttons that use the green palette.
    Every other toggle (dialogs, menus) uses the blue palette.
    """

    STEPPER_PLUS = {'+', '++'}
    STEPPER_MINUS = {'-', '--', '−', '−−'}

    def __init__(self, main_window, green_windows=(), green_buttons=(), parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.green_windows = tuple(green_windows)
        self.green_buttons = list(green_buttons)
        self._closed_since_click = []  # dialogs hidden since the last button release

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _explicit_cue(widget):
        cue = widget.property('soundCue')
        return cue if isinstance(cue, str) and cue else None

    def _toggle_cue(self, button, checked):
        state = 'on' if checked else 'off'
        window = button.window()
        if any(button is b for b in self.green_buttons) or isinstance(window, self.green_windows):
            return f'toggle_green_{state}'
        if window is self.main_window:
            return f'ui_toggle_{state}'
        return f'toggle_blue_{state}'

    def _stepper_cue(self, button):
        text = button.text().strip()
        if text in self.STEPPER_PLUS:
            return 'stepper_plus'
        if text in self.STEPPER_MINUS:
            return 'stepper_minus'
        return None

    def _play_after_click(self, button):
        """Decide once the click has been handled, so toggles report their new state
        and a click that closed a dialog stays silent (dialog_close already played)."""
        was_checkable = button.isCheckable()
        window = button.window()
        self._closed_since_click = []

        def decide():
            # The click closed the window it was in (OK, Cancel, Close): dialog_close
            # already played. Any other window closing does not silence the click.
            if any(closed is window for closed in self._closed_since_click):
                return
            try:
                cue = self._explicit_cue(button)
                if cue is not None and '{state}' in cue:
                    cue = cue.format(state='on' if button.isChecked() else 'off')
                elif cue is None:
                    if was_checkable or isinstance(button, QCheckBox):
                        cue = self._toggle_cue(button, button.isChecked())
                    else:
                        cue = 'ui_click'
            except RuntimeError:  # the button was deleted by its own click
                cue = 'ui_click'
            play(cue)

        QTimer.singleShot(0, decide)

    def _hook_slider(self, slider):
        if slider.property('_soundHooked'):
            return
        slider.setProperty('_soundHooked', True)
        state = {'last': 0.0}

        def on_action(_action):
            now = time.monotonic() * 1000
            if now - state['last'] >= SLIDER_TICK_GAP_MS:
                state['last'] = now
                play(SLIDER_TICK_CUE)

        # actionTriggered fires only for user input, never for setValue()
        slider.actionTriggered.connect(on_action)

    def _hook_stepper(self, button, cue):
        # Auto-repeat buttons click many times per press: sound each step
        if button.property('_soundHooked'):
            return
        button.setProperty('_soundHooked', True)
        button.clicked.connect(lambda *_: play(cue))

    # -- event filter ------------------------------------------------------
    def eventFilter(self, obj, event):
        etype = event.type()
        if not obj.isWidgetType():
            return False
        try:
            if etype == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._on_press(obj)
            elif etype == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._on_release(obj)
            elif etype == QEvent.Enter:
                self._on_enter(obj)
            elif etype == QEvent.Show and not event.spontaneous():
                self._on_show(obj)
            elif etype == QEvent.Hide and not event.spontaneous():
                self._on_hide(obj)
        except RuntimeError:
            pass
        return False

    def _on_press(self, obj):
        if isinstance(obj, QAbstractSlider):
            self._hook_slider(obj)
        elif isinstance(obj, QComboBox) and obj.isEnabled():
            play('menu_open')
        elif isinstance(obj, QAbstractButton) and obj.isEnabled() and self._explicit_cue(obj) is None:
            cue = self._stepper_cue(obj)
            if cue is None:
                return
            if obj.autoRepeat():
                self._hook_stepper(obj, cue)
                obj.setProperty('soundCue', 'none')
            else:
                # one sound per press for custom press-and-hold steppers
                play(cue)

    def _on_release(self, obj):
        if isinstance(obj, QAbstractButton):
            if not obj.isEnabled() or not obj.isDown() or self._stepper_cue(obj):
                return
            cue = self._explicit_cue(obj)
            if cue == 'none':
                return
            self._play_after_click(obj)
            return
        # A value picked from a dropdown's popup list
        window = obj.window()
        if window is not None and window.metaObject().className() == 'QComboBoxPrivateContainer':
            play('ui_click')
            return
        # An item chosen from a context menu
        if isinstance(obj, QMenu):
            action = obj.activeAction()
            if action is not None and action.isEnabled() and action.menu() is None and not action.isSeparator():
                play('ui_click')
            return
        cue = self._explicit_cue(obj)
        if cue and cue != 'none':
            play(cue)

    def _on_enter(self, obj):
        if not isinstance(obj, QAbstractButton) or not obj.isEnabled():
            return
        if obj.window() is self.main_window:
            play('ui_hover')

    def _on_show(self, obj):
        if isinstance(obj, QMessageBox):
            icon = obj.icon()
            play('denied' if icon in (QMessageBox.Warning, QMessageBox.Critical) else 'dialog_open')
        elif isinstance(obj, QDialog):
            play('dialog_open')
        elif isinstance(obj, QMenu):
            if not isinstance(obj.parentWidget(), QMenu):  # submenus open on hover: stay quiet
                play('menu_open')

    def _on_hide(self, obj):
        if isinstance(obj, QDialog):
            self._closed_since_click.append(obj)
            play('dialog_close')


def install(main_window, **kwargs):
    """Create the manager and install the app-wide filter. Returns the filter."""
    app = QApplication.instance()
    manager()
    ui_filter = UiSoundFilter(main_window, parent=app, **kwargs)
    app.installEventFilter(ui_filter)
    return ui_filter
