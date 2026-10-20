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
or "none" when the sound is played elsewhere. A dialog can swap its open or
close sound with the properties "soundOpen" and "soundClose" (e.g. from its clicked
signal, so keyboard shortcuts that call click() sound too). A menu can swap its
open, item hover and item pick sounds with "soundOpen", "hoverCue" and "soundPick";
a submenu takes its parent menu's.
"""

import os
import sys
import time
import weakref

from PyQt5.QtCore import QIODevice, QObject, QEvent, Qt, QTimer, QUrl
from PyQt5.QtWidgets import (
    QAbstractButton, QAbstractItemView, QAbstractSlider, QApplication, QCheckBox, QComboBox,
    QDialog, QMenu, QMessageBox, QStyle, QStyleOptionComboBox, QWidgetAction,
)

try:
    from PyQt5.QtMultimedia import QAudio, QAudioDeviceInfo, QAudioFormat, QAudioOutput, QSoundEffect
except ImportError:  # QtMultimedia missing: the app runs silently
    QSoundEffect = None


# cue -> minimum gap in ms between two plays of the same cue
CUES = {
    'ui_click': 40, 'right_click': 40,
    'ui_toggle_on': 40, 'ui_toggle_off': 40,
    'toggle_blue_on': 40, 'toggle_blue_off': 40,
    'toggle_green_on': 40, 'toggle_green_off': 40,
    'layer_select': 40,
    'hover_toolbar': 80, 'hover_panel_top': 80, 'hover_layer': 80, 'hover_panel_bottom': 80,
    'hover_level': 80, 'hover_level_fold': 80, 'level_select': 40, 'level_fold': 40,
    'hover_group': 80, 'hover_dialog': 80, 'hover_menu': 80, 'hover_menu_group': 80, 'hover_settings': 80,
    'hover_attach_point': 80, 'hover_move_point': 80, 'hover_rotate_point': 80, 'hover_combo': 80,
    'mode_view': 60, 'mode_select': 60, 'mode_move': 60, 'mode_attach': 60,
    'mode_view_off': 60, 'mode_select_off': 60, 'mode_attach_off': 60,
    'mode_rotate': 60, 'mode_angle': 60,
    'toolbar_action': 40, 'toolbar_image': 40, 'toolbar_settings': 40,
    'toggle_shadow_on': 40, 'toggle_shadow_off': 40,
    'toggle_tabs_on': 40, 'toggle_tabs_off': 40,
    'layer_state_on': 40, 'layer_state_off': 40,
    'toggle_points_on': 40, 'toggle_points_off': 40,
    'drag_pickup': 60, 'drag_drop': 60,
    'rotate_grab': 60, 'rotate_release': 60,
    'dial_pin': 25, 'dial_pin_quarter': 40,
    'snap_grid': 60,
    'attach_start': 60, 'attach_complete': 60,
    'new_strand': 80,
    'delete': 80,
    'undo': 60, 'redo': 60,
    'save_done': 200,
    'denied': 150,
    'dialog_open': 120, 'dialog_close': 120,
    'menu_open': 80,
    'hover_dropdown': 80, 'dropdown_pick': 40,
    'menu_open_level': 80, 'hover_menu_level': 80, 'menu_pick_level': 40,
    'strand_select': 40, 'strand_deselect': 40, 'hover_strand': 80,
    'group_new': 80, 'group_panel_off': 80, 'group_panel_on': 80,
    'stepper_plus': 70, 'stepper_minus': 70,
    'tab_switch': 60, 'hover_tab': 80, 'hover_tab_button': 80,
    'tab_new': 60, 'tab_duplicate': 60, 'tab_close': 60,
}
HOVER_CUES = {'hover_toolbar', 'hover_panel_top', 'hover_layer', 'hover_panel_bottom',
              'hover_level', 'hover_level_fold', 'hover_strand',
              'hover_group', 'hover_dialog', 'hover_menu', 'hover_menu_group', 'hover_menu_level', 'hover_settings',
              'hover_attach_point', 'hover_move_point', 'hover_rotate_point', 'hover_combo', 'hover_dropdown',
              'hover_tab', 'hover_tab_button'}
# Layer panel buttons whose hover is the layer one (matched by class name, so this module
# does not import the layer panel)
LAYER_BUTTON_CLASSES = {'NumberedLayerButton'}
SLIDER_TICK_CUE = 'snap_grid'
SLIDER_TICK_GAP_MS = 40

# Settings lines in user_settings.txt
SETTING_ENABLED = 'SoundEnabled'
SETTING_VOLUME = 'SoundVolume'
SETTING_HOVER = 'SoundHover'

# Output device
DEVICE_POLL_MS = 1500  # how often to look for a new default output device
STUCK_MS = 2000  # a sound still playing this long after its last play lost its device
KEEP_AWAKE_S = 120  # how long the device keeps streaming silence after the last sound


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


class _Silence(QIODevice):
    """Silence streamed between sounds. Monitor speakers (HDMI, DisplayPort) fall asleep after
    a moment without audio and swallow the start of the next sound, which for a short UI
    sound is most or all of it."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.until = 0.0
        self.open(QIODevice.ReadOnly | QIODevice.Unbuffered)

    def readData(self, maxlen):
        # out of data once the time is up: the output goes idle and is stopped
        return bytes(maxlen) if time.monotonic() < self.until else b''

    def writeData(self, data):
        return 0


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
        self._silence = _Silence(self)
        self._silence_output = None
        self._silence_moved = (0, 0.0)  # its last processedUSecs() and when that changed
        # On macOS a sound keeps the output device that was the default when it loaded (on
        # Windows Qt opens the current default for every play), and Qt5 has no signal for a
        # new default, so look for one.
        self._device = QAudioDeviceInfo.defaultOutputDevice()
        self._device_timer = QTimer(self)
        self._device_timer.timeout.connect(self._check_output_device)
        self._device_timer.start(DEVICE_POLL_MS)

    @staticmethod
    def _reload(effect):
        """Give an effect a new audio output, on the current default device."""
        source = effect.source()
        effect.setSource(QUrl())
        effect.setSource(source)

    def _check_output_device(self):
        device = QAudioDeviceInfo.defaultOutputDevice()
        if device.isNull() or device == self._device:
            return
        self._device = device
        self._drop_silence()
        for effect in self._effects.values():
            self._reload(effect)

    def _keep_awake(self):
        """Stream silence until KEEP_AWAKE_S from now, so the next sound plays in full."""
        now = time.monotonic()
        self._silence.until = now + KEEP_AWAKE_S
        output = self._silence_output
        if output is not None and output.state() != QAudio.StoppedState:
            done = output.processedUSecs()
            if done != self._silence_moved[0]:
                self._silence_moved = (done, now)
            if now - self._silence_moved[1] < 1:
                return
            self._drop_silence()  # stopped moving: its device went away
        if self._silence_output is None:
            fmt = QAudioFormat()
            fmt.setSampleRate(44100)
            fmt.setChannelCount(1)
            fmt.setSampleSize(16)
            fmt.setCodec('audio/pcm')
            fmt.setByteOrder(QAudioFormat.LittleEndian)
            fmt.setSampleType(QAudioFormat.SignedInt)
            self._silence_output = QAudioOutput(fmt, self)
            self._silence_output.stateChanged.connect(self._on_silence_state)
        self._silence_moved = (0, now)
        self._silence_output.start(self._silence)
        if self._silence_output.state() == QAudio.StoppedState:
            self._drop_silence()  # no device to open; try again with the next sound

    def _on_silence_state(self, state):
        # the signal can arrive late (PulseAudio sends it from its own thread)
        output = self._silence_output
        if output is not None and output.state() == QAudio.IdleState:
            output.stop()

    def _drop_silence(self):
        if self._silence_output is not None:
            self._silence_output.stateChanged.disconnect(self._on_silence_state)
            self._silence_output.stop()  # deleting a running output can crash Qt's PulseAudio backend
            self._silence_output.deleteLater()
            self._silence_output = None

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
                        try:
                            self.volume = max(0, min(100, int(float(value))))
                        except (ValueError, OverflowError):
                            pass  # a hand-edited bad value keeps the default; later lines still load
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
        self._keep_awake()
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
        last = self._last_played.get(cue, -1e9)
        if now - last < CUES.get(cue, 40):
            return
        self._last_played[cue] = now
        if effect.isPlaying() and now - last > STUCK_MS:
            # its output lost the device mid-sound and never finished, which would keep
            # this sound silent from now on
            self._reload(effect)
        self._keep_awake()
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


# button -> function that plays the button's sound itself, once its click has been handled
_RESOLVERS = weakref.WeakKeyDictionary()


def set_cue_resolver(button, resolver):
    """Let a button work out its own sound after each click: resolver() is called right after
    the click's handlers have run (or, when a handler opens a modal dialog, as the dialog opens)
    and plays whatever fits."""
    _RESOLVERS[button] = resolver


def set_hover_cue(widget, cue):
    """Give one button its own hover sound."""
    widget.setProperty('hoverCue', cue)


def set_hover_area(container, cue):
    """Every button inside this widget hovers with this sound, including buttons added later."""
    container.setProperty('hoverArea', cue)


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

    def __init__(self, main_window, green_windows=(), green_buttons=(), dialog_hover=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.green_windows = tuple(green_windows)
        self.green_buttons = list(green_buttons)
        # dialog class -> hover cue for its buttons; other dialogs use hover_dialog
        self.dialog_hover = dict(dialog_hover or {})
        self._closed_since_click = []  # dialogs hidden since the last button release
        self._menu_last_action = weakref.WeakKeyDictionary()  # menu -> action last hovered
        self._view_last_row = weakref.WeakKeyDictionary()  # list/tree view -> row last hovered
        self._combo_in_arrow = weakref.WeakKeyDictionary()  # dropdown -> pointer is on its arrow section
        self._combo_list_open = weakref.WeakSet()  # dropdowns whose list is open

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
            resolver = _RESOLVERS.get(button)
            if resolver is not None:
                resolver()
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

    def _hook_combo(self, combo):
        # activated() is a value chosen by the user; only one chosen from the open list
        # sounds, not the wheel or arrow keys on a closed dropdown
        if combo.property('_soundHooked'):
            return
        combo.setProperty('_soundHooked', True)
        combo.activated.connect(lambda _index, combo=combo: self._on_combo_activated(combo))

    def _on_combo_activated(self, combo):
        if combo in self._combo_list_open:
            play('dropdown_pick')

    def play_click(self, button):
        """The sound a mouse click on button plays, for keyboard shortcuts that call click()."""
        if button.isEnabled():
            self._play_after_click(button)

    # -- event filter ------------------------------------------------------
    def eventFilter(self, obj, event):
        etype = event.type()
        if not obj.isWidgetType():
            return False
        try:
            if etype == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self._on_press(obj)
            elif etype == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self._on_release(obj, event.pos())
            elif etype == QEvent.Enter:
                self._on_enter(obj)
            elif etype in (QEvent.MouseMove, QEvent.HoverMove):
                if isinstance(obj, QComboBox):
                    self._on_combo_move(obj, event.pos())
                else:
                    self._on_view_move(obj, event)
            elif etype == QEvent.Leave and isinstance(obj, QComboBox):
                self._combo_in_arrow.pop(obj, None)
            elif etype == QEvent.Leave and isinstance(obj.parentWidget(), QAbstractItemView):
                self._view_last_row.pop(obj.parentWidget(), None)
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

    def _on_release(self, obj, pos):
        if isinstance(obj, QAbstractButton):
            if not obj.isEnabled() or not obj.isDown() or self._stepper_cue(obj):
                return
            if obj in _RESOLVERS:
                self._play_after_click(obj)
                return
            cue = self._explicit_cue(obj)
            if cue == 'none':
                return
            self._play_after_click(obj)
            return
        # An item chosen from a context menu
        if isinstance(obj, QMenu):
            action = obj.activeAction()
            if action is not None and action.isEnabled() and action.menu() is None and not action.isSeparator():
                play(self._menu_prop(obj, 'soundPick', 'ui_click'))
            return
        # Custom controls (the document tabs) act only on a release over them, like buttons,
        # and a list (the Settings sidebar) only on a release over one of its rows
        cue = self._explicit_cue(obj)
        if not cue or cue == 'none' or not obj.rect().contains(pos):
            return
        view = obj.parentWidget()
        if isinstance(view, QAbstractItemView) and view.viewport() is obj and not view.indexAt(pos).isValid():
            return
        play(cue)

    def _on_enter(self, obj):
        if not obj.isEnabled():
            return
        if not isinstance(obj, QAbstractButton):
            # custom-painted controls (the document tabs) opt in with set_hover_cue
            cue = obj.property('hoverCue')
            if isinstance(cue, str) and cue and cue != 'none':
                play(cue)
            return
        cue = self._hover_cue(obj)
        if cue:
            play(cue)

    def _on_combo_move(self, combo, pos):
        """A dropdown's arrow section lights up on hover like a button, so it hovers like one:
        one sound each time the pointer reaches it."""
        option = QStyleOptionComboBox()
        combo.initStyleOption(option)
        arrow = combo.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxArrow, combo)
        inside = combo.isEnabled() and arrow.contains(pos)
        if inside and not self._combo_in_arrow.get(combo):
            play('hover_combo')
        self._combo_in_arrow[combo] = inside

    def _on_view_move(self, viewport, event):
        """Rows of lists and trees (groups and their layers, the Settings sidebar) hover like
        buttons: one sound each time the pointer reaches another row."""
        view = viewport.parentWidget()
        if not isinstance(view, QAbstractItemView) or view.viewport() is not viewport:
            return
        index = view.indexAt(event.pos())
        row = (index.row(), index.internalId()) if index.isValid() else None
        if self._view_last_row.get(view) == row:
            return
        self._view_last_row[view] = row
        if row is not None:
            cue = self._area_cue(view, include_self=True)
            if cue:
                play(cue)

    def _hover_cue(self, button):
        """The button's own hover, else its area's (the nearest parent marked with set_hover_area),
        else its window's: hover_settings or hover_dialog in sub-windows."""
        cue = button.property('hoverCue')
        if isinstance(cue, str) and cue:
            return None if cue == 'none' else cue
        if type(button).__name__ in LAYER_BUTTON_CLASSES:
            return 'hover_layer'
        return self._area_cue(button)

    def _area_cue(self, widget, include_self=False):
        """Hover cue of the area a widget sits in, or of its window."""
        source = widget
        widget = widget if include_self else widget.parentWidget()
        # stop at the window: a sub-window opened from the group panel is not part of it
        while widget is not None and not widget.isWindow():
            area = widget.property('hoverArea')
            if isinstance(area, str) and area:
                return area
            widget = widget.parentWidget()
        window = source.window()
        if window.metaObject().className() == 'QComboBoxPrivateContainer':  # a dropdown's open list
            return 'hover_dropdown'
        if isinstance(window, QMenu):  # a button inside a menu row, e.g. Show Start Dash
            return self._menu_prop(window, 'hoverCue', 'hover_menu')
        if window is self.main_window:
            return None if include_self else 'hover_toolbar'
        if isinstance(window, QDialog):
            for cls, dialog_cue in self.dialog_hover.items():
                if isinstance(window, cls):
                    return dialog_cue
            return 'hover_dialog'
        return None

    def _on_menu_hover(self, menu, action):
        """A menu item became highlighted: one hover per item, not one per mouse move.
        A row made of its own buttons (Dash: Show Start Dash, Show End Dash) stays quiet
        here; each of its buttons hovers when the pointer reaches it."""
        if action is None or action.isSeparator() or not action.isEnabled():
            return
        if self._menu_last_action.get(menu) is action:
            return
        self._menu_last_action[menu] = action
        if isinstance(action, QWidgetAction):
            widget = action.defaultWidget()
            if widget is not None and widget.findChildren(QAbstractButton):
                return
        play(self._menu_prop(menu, 'hoverCue', 'hover_menu'))

    @staticmethod
    def _menu_prop(menu, prop, default):
        """A menu's sound property (hoverCue, soundOpen, soundPick): its own, else its
        parent menu's, else *default*."""
        while isinstance(menu, QMenu):
            cue = menu.property(prop)
            if isinstance(cue, str) and cue:
                return cue
            menu = menu.parentWidget()
        return default

    def _on_show(self, obj):
        if obj.metaObject().className() == 'QComboBoxPrivateContainer':  # a dropdown's list opened
            combo = obj.parentWidget()
            if isinstance(combo, QComboBox):
                self._hook_combo(combo)
                self._combo_list_open.add(combo)
            play('menu_open')
        elif isinstance(obj, QMessageBox):
            icon = obj.icon()
            play('denied' if icon in (QMessageBox.Warning, QMessageBox.Critical) else 'dialog_open')
        elif isinstance(obj, QDialog):
            self._play_dialog_cue(obj, 'soundOpen', 'dialog_open')
        elif isinstance(obj, QMenu):
            if not obj.property('_soundHoverHooked'):
                obj.setProperty('_soundHoverHooked', True)
                obj.hovered.connect(lambda action, menu=obj: self._on_menu_hover(menu, action))
            self._menu_last_action.pop(obj, None)
            if not isinstance(obj.parentWidget(), QMenu):  # submenus open on hover: stay quiet
                play(self._menu_prop(obj, 'soundOpen', 'menu_open'))

    def _on_hide(self, obj):
        if obj.metaObject().className() == 'QComboBoxPrivateContainer':
            # the list hides just before activated() reports the chosen value
            combo = obj.parentWidget()
            if isinstance(combo, QComboBox):
                QTimer.singleShot(0, lambda: self._combo_list_open.discard(combo))
        elif isinstance(obj, QDialog):
            self._closed_since_click.append(obj)
            self._play_dialog_cue(obj, 'soundClose', 'dialog_close')

    @staticmethod
    def _play_dialog_cue(dialog, prop, default):
        cue = dialog.property(prop)
        cue = cue if isinstance(cue, str) and cue else default
        if cue != 'none':
            play(cue)


def install(main_window, **kwargs):
    """Create the manager and install the app-wide filter. Returns the filter."""
    app = QApplication.instance()
    manager()
    ui_filter = UiSoundFilter(main_window, parent=app, **kwargs)
    app.installEventFilter(ui_filter)
    return ui_filter
