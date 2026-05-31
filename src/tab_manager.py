"""Tab session management for OpenStrand Studio.

MVP rule: there is only ONE live canvas. Each tab is, conceptually, a separate
OpenStrand session backed by its own project JSON. Switching tabs serializes the
current tab into memory (like a save) and restores the selected tab into the
existing canvas / layer panel (like a load).
"""

import copy
import os
from dataclasses import dataclass
from typing import Optional

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QMessageBox

from save_load_manager import serialize_project_state, apply_project_state
from translations import translations


@dataclass
class TabSession:
    id: str
    title: str
    file_path: Optional[str] = None
    dirty: bool = False
    project_state: Optional[dict] = None
    history_payload: Optional[dict] = None
    # When set, this is an unsaved "Untitled N" tab whose title is derived from
    # the current language (so it re-translates when the language changes). Tabs
    # with a file or a custom (renamed/duplicated) title leave this as None.
    untitled_index: Optional[int] = None


class TabManager(QObject):
    """Owns the list of TabSession objects and drives capture/restore against the
    single live canvas held by the main window."""

    # Emitted whenever the tab list or the active tab changes so the tab bar can
    # rebuild itself.
    changed = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.tabs = []
        self.active_tab_id = None
        self._id_seq = 0
        self._untitled_counter = 0
        # Guards reentrancy: while capturing/restoring we ignore the undo
        # manager's state_saved signal so tab switches don't mark tabs dirty.
        self._busy = False

        # The first tab represents whatever is already on the canvas at startup.
        first = self._make_untitled_session()
        self.tabs.append(first)
        self.active_tab_id = first.id

    # ------------------------------------------------------------------ utils
    def _new_id(self):
        self._id_seq += 1
        return "tab-%d" % self._id_seq

    def _make_untitled_session(self):
        self._untitled_counter += 1
        idx = self._untitled_counter
        return TabSession(id=self._new_id(), title="", untitled_index=idx)

    def _tr(self, key, fallback=""):
        lang = getattr(self.main_window, 'language_code', 'en')
        return translations.get(lang, translations['en']).get(key, fallback)

    def title_for(self, session):
        """Resolve a tab's display title, translating "Untitled N" into the
        active language (file-backed/renamed tabs keep their stored title)."""
        if session.untitled_index is not None:
            return "%s %d" % (self._tr('untitled', 'Untitled'), session.untitled_index)
        return session.title

    def retranslate(self):
        """Called when the UI language changes so untitled tab titles refresh."""
        self.changed.emit()

    @property
    def canvas(self):
        return self.main_window.canvas

    @property
    def undo_mgr(self):
        lp = getattr(self.main_window, 'layer_panel', None)
        return getattr(lp, 'undo_redo_manager', None)

    def find(self, tab_id):
        for t in self.tabs:
            if t.id == tab_id:
                return t
        return None

    def get_active(self):
        return self.find(self.active_tab_id)

    # -------------------------------------------------------------- capturing
    def capture_active_session(self):
        """Serialize the current canvas into the active tab (in memory).

        Returns True on success. On failure, the corrupted snapshot is set to
        None (so a later restore degrades to an empty canvas instead of silently
        reverting to a *stale* snapshot) and False is returned so callers can
        refuse to switch away and warn the user.
        """
        active = self.get_active()
        if active is None:
            return True
        prev_busy = self._busy
        self._busy = True
        ok = True
        try:
            undo = self.undo_mgr
            if undo is not None:
                try:
                    payload = undo.export_history_payload()
                    if payload is None:
                        raise ValueError("export_history_payload returned None")
                    active.history_payload = payload
                except Exception:
                    active.history_payload = None
                    ok = False
            try:
                groups = {}
                glm = getattr(self.main_window, 'group_layer_manager', None)
                if glm is not None:
                    groups = glm.get_group_data()
                active.project_state = serialize_project_state(
                    self.canvas.strands, groups, self.canvas)
            except Exception:
                active.project_state = None
                ok = False
        finally:
            self._busy = prev_busy
        return ok

    def _capture_or_warn(self):
        """Capture the active tab; on failure warn the user and report False so
        the caller can abort (keeping the live canvas on the current tab)."""
        if self.capture_active_session():
            return True
        QMessageBox.warning(
            self.main_window,
            self._tr('unsaved_tab_title', 'Unsaved changes'),
            self._tr('tab_capture_failed',
                     "This tab's contents could not be saved in memory, so "
                     "switching tabs was canceled to avoid losing work. Save "
                     "the project to a file first."))
        return False

    # -------------------------------------------------------------- restoring
    def restore_session(self, tab_id):
        """Load the given tab's serialized state back into the live canvas."""
        session = self.find(tab_id)
        if session is None:
            return
        prev_busy = self._busy
        self._busy = True
        try:
            undo = self.undo_mgr
            payload = session.history_payload
            loaded = False
            if undo is not None and payload and payload.get("states"):
                try:
                    loaded = undo.import_history_payload(payload)
                except Exception:
                    loaded = False

            if loaded:
                self._post_restore_refresh()
            elif session.project_state and session.project_state.get("strands"):
                self._apply_project_state(session.project_state)
            else:
                self._load_empty_workspace()
        finally:
            self._busy = prev_busy

    def _post_restore_refresh(self):
        """Refresh layer panel and sync toolbar button state after a history
        payload restore (import_history_payload already loaded the canvas)."""
        mw = self.main_window
        canvas = self.canvas
        if hasattr(canvas, 'layer_panel') and canvas.layer_panel:
            canvas.layer_panel.refresh()
        self._sync_toolbar_buttons()
        canvas.update()

    def _apply_project_state(self, state):
        mw = self.main_window
        meta = apply_project_state(self.canvas, state)
        # Sync toolbar buttons from the loaded metadata
        if hasattr(mw, 'toggle_shadow_button'):
            mw.toggle_shadow_button.setChecked(meta.get("shadow_enabled", False))
        if hasattr(mw, 'toggle_control_points_button'):
            mw.toggle_control_points_button.setChecked(meta.get("show_control_points", False))
        # Restore layer lock state (the history-payload path does this via the
        # full state JSON; the project_state fallback must do it explicitly).
        lp = getattr(mw, 'layer_panel', None)
        if lp is not None:
            try:
                lp.lock_mode = meta.get("lock_mode", False)
                lp.locked_layers = set(meta.get("locked_layers", []) or [])
                if hasattr(lp, 'update_layer_buttons_lock_state'):
                    lp.update_layer_buttons_lock_state()
            except Exception:
                pass
        if hasattr(self.canvas, 'layer_panel') and self.canvas.layer_panel:
            self.canvas.layer_panel.refresh()
        self.canvas.update()
        undo = self.undo_mgr
        if undo is not None:
            undo.clear_history(save_current=True)

    def _sync_toolbar_buttons(self):
        mw = self.main_window
        canvas = self.canvas
        if hasattr(mw, 'toggle_shadow_button'):
            mw.toggle_shadow_button.setChecked(getattr(canvas, 'shadow_enabled', False))
        if hasattr(mw, 'toggle_control_points_button'):
            mw.toggle_control_points_button.setChecked(getattr(canvas, 'show_control_points', False))

    def _load_empty_workspace(self):
        """Reset the live canvas / layer panel to a clean, empty session."""
        prev_busy = self._busy
        self._busy = True
        try:
            self._load_empty_workspace_impl()
        finally:
            self._busy = prev_busy

    def _load_empty_workspace_impl(self):
        mw = self.main_window
        canvas = self.canvas
        # Full canvas reset (clears strands/groups AND all transient interaction
        # state) so a new tab never inherits dangling references to the previous
        # tab's strands.
        if hasattr(canvas, 'reset_for_new_tab'):
            canvas.reset_for_new_tab()
        else:
            canvas.strands = []
            canvas.groups = {}
            canvas.selected_strand = None
            if hasattr(canvas, 'selected_strand_index'):
                canvas.selected_strand_index = None

        glm = getattr(mw, 'group_layer_manager', None)
        if glm is not None and hasattr(glm, 'group_panel'):
            try:
                glm.group_panel.clear_all()
                glm.group_panel.groups_loaded_from_json = False
            except Exception:
                pass

        lp = getattr(mw, 'layer_panel', None)
        if lp is not None:
            lp.set_counts = {}
            lp.current_set = 1
            if hasattr(lp, 'refresh'):
                lp.refresh()

        canvas.update()

        undo = self.undo_mgr
        if undo is not None:
            undo.clear_history(save_current=False)

    # ----------------------------------------------------------- tab actions
    def new_tab(self):
        if not self._capture_or_warn():
            return
        session = self._make_untitled_session()
        self.tabs.append(session)
        self.active_tab_id = session.id
        self._load_empty_workspace()
        self.changed.emit()

    def duplicate_tab(self, tab_id):
        src = self.find(tab_id)
        if src is None:
            return
        if not self._capture_or_warn():
            return
        # Re-fetch the source after capture in case it was the active tab.
        src = self.find(tab_id)
        session = TabSession(
            id=self._new_id(),
            title="%s %s" % (self.title_for(src), self._tr('tab_copy_suffix', 'copy')),
            file_path=None,
            dirty=True,
            project_state=copy.deepcopy(src.project_state),
            history_payload=copy.deepcopy(src.history_payload),
        )
        idx = self.tabs.index(src)
        self.tabs.insert(idx + 1, session)
        self.active_tab_id = session.id
        self.restore_session(session.id)
        session.dirty = True
        self.changed.emit()

    def switch_to_tab(self, tab_id):
        if tab_id == self.active_tab_id:
            return
        if self.find(tab_id) is None:
            return
        if not self._capture_or_warn():
            return
        self.active_tab_id = tab_id
        self.restore_session(tab_id)
        self.changed.emit()

    def close_tab(self, tab_id):
        session = self.find(tab_id)
        if session is None:
            return

        if session.dirty:
            box = QMessageBox(self.main_window)
            box.setIcon(QMessageBox.Warning)
            box.setWindowTitle(self._tr('unsaved_tab_title', 'Unsaved changes'))
            box.setText("%s\n\n%s" % (self.title_for(session),
                                      self._tr('unsaved_tab_title', 'Unsaved changes')))
            # Use app-translated button labels (Qt's standard Discard/Cancel
            # buttons ignore our translation table). Roles drive ordering and
            # make Esc map to Cancel.
            save_btn = box.addButton(self._tr('save', 'Save'), QMessageBox.AcceptRole)
            discard_btn = box.addButton(self._tr('discard', 'Discard'), QMessageBox.DestructiveRole)
            cancel_btn = box.addButton(self._tr('cancel', 'Cancel'), QMessageBox.RejectRole)
            box.setDefaultButton(save_btn)
            box.setEscapeButton(cancel_btn)
            # Mirror the button row for RTL languages (Hebrew).
            if getattr(self.main_window, 'language_code', 'en') == 'he':
                box.setLayoutDirection(Qt.RightToLeft)
            box.exec_()
            clicked = box.clickedButton()
            if clicked is save_btn:
                # Make sure the tab being saved is the live one, then save.
                if tab_id != self.active_tab_id:
                    self.switch_to_tab(tab_id)
                saved = False
                if hasattr(self.main_window, 'save_project'):
                    saved = self.main_window.save_project()
                # If the save dialog was canceled/failed, keep the tab and abort.
                if not saved:
                    return
            elif clicked is not discard_btn:
                # Cancel, or the dialog dismissed without an explicit choice.
                return

        idx = self.tabs.index(session)
        was_active = (tab_id == self.active_tab_id)
        self.tabs.remove(session)

        if not self.tabs:
            # Never leave the user with no workspace.
            fresh = self._make_untitled_session()
            self.tabs.append(fresh)
            self.active_tab_id = fresh.id
            self._load_empty_workspace()
        elif was_active:
            neighbor = self.tabs[min(idx, len(self.tabs) - 1)]
            self.active_tab_id = neighbor.id
            self.restore_session(neighbor.id)

        self.changed.emit()

    # ---------------------------------------------------------- dirty tracking
    def mark_active_dirty(self, *args):
        if self._busy:
            return
        active = self.get_active()
        if active is not None and not active.dirty:
            active.dirty = True
            self.changed.emit()

    def mark_active_saved(self, file_path=None):
        active = self.get_active()
        if active is not None:
            active.dirty = False
            if file_path:
                active.file_path = file_path
                # Use the file name (without extension) as the tab title; it is no
                # longer an auto-translated "Untitled N" tab.
                active.title = os.path.splitext(os.path.basename(file_path))[0]
                active.untitled_index = None
            self.changed.emit()
