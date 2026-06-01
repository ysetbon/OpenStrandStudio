"""Automated regression tests for the 1.108 tab/view-mode fixes.

Run from anywhere:
    <src>\\build_env\\Scripts\\python.exe tests\\1.108\\test_tab_fixes.py

Drives the *workflow* of each fix against a real MainWindow (no GUI event loop)
and prints [PASS]/[FAIL] lines plus a summary. Exit code is non-zero on any
failure, so it can gate CI.

Safety: APPDATA is redirected to a throwaway temp dir BEFORE any project import,
so the real user_settings.txt is never touched.

Covered:
  #1  exit warning when tabs are dirty (block + warn)
  #2a background dirty-tab close returns you to the originally-active tab
  #2b switch_to_tab() returns a success flag; a failed capture aborts the
      close/save instead of saving the wrong tab and dropping the dirty one
  #3  saving settings preserves TabEdgePosition
  HE  the same close/exit flow works with the UI switched to Hebrew (RTL)
"""

import os
import sys
import tempfile

# Windows consoles default to cp1252, which can't encode Hebrew detail strings.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# --- Protect the real settings file: redirect APPDATA before importing anything.
_TMP_APPDATA = tempfile.mkdtemp(prefix="oss_test_appdata_")
os.environ['APPDATA'] = _TMP_APPDATA

# This test lives in tests/1.108/ ; the source modules are in <repo>/src.
_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, _SRC)

from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtGui import QCloseEvent

from main_window import MainWindow
from translations import translations

# --------------------------------------------------------------------------- io
_PASS = 0
_FAIL = 0


def check(name, cond, detail=""):
    global _PASS, _FAIL
    if cond:
        _PASS += 1
        print("[PASS] %s" % name)
    else:
        _FAIL += 1
        print("[FAIL] %s  ::  %s" % (name, detail))


# ------------------------------------------------- modal dialog / file mocking
_choice_role = None


def _fake_exec(self):
    return 0


def _fake_clicked_button(self):
    if _choice_role is None:
        return None
    for btn in self.buttons():
        if self.buttonRole(btn) == _choice_role:
            return btn
    return None


def install_dialog_mocks():
    QMessageBox.exec_ = _fake_exec
    QMessageBox.clickedButton = _fake_clicked_button
    QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.Ok)


_save_path = [None]


def install_file_mocks(path):
    _save_path[0] = path
    QFileDialog.getSaveFileName = staticmethod(
        lambda *a, **k: (_save_path[0], "JSON Files (*.json)"))
    QFileDialog.getOpenFileName = staticmethod(
        lambda *a, **k: (_save_path[0], "JSON Files (*.json)"))


def reset_tabs_clean(tm):
    for t in tm.tabs:
        t.dirty = False


def build_three_tabs(tm):
    """Return (A, B, C) ids with tabs ending [..., A, B, C]; active becomes C."""
    tm.new_tab()
    tm.new_tab()
    c = tm.active_tab_id
    idx = [t.id for t in tm.tabs].index(c)
    a = tm.tabs[idx - 2].id
    b = tm.tabs[idx - 1].id
    return a, b, c


# ------------------------------------------------------------------- the tests
def test_switch_returns_bool(tm):
    same = tm.switch_to_tab(tm.active_tab_id)
    check("#2b switch_to_tab(active) -> True", same is True, "got %r" % same)
    bogus = tm.switch_to_tab("tab-does-not-exist")
    check("#2b switch_to_tab(unknown) -> False", bogus is False, "got %r" % bogus)


def test_2a_background_close_keeps_active(window):
    tm = window.tab_manager
    a, b, c = build_three_tabs(tm)
    reset_tabs_clean(tm)
    tm.find(b).dirty = True
    tm.switch_to_tab(a)
    check("#2a precondition: active is A", tm.active_tab_id == a)

    global _choice_role
    _choice_role = QMessageBox.AcceptRole  # click "Save"
    install_file_mocks(os.path.join(_TMP_APPDATA, "proj_2a.json"))

    tm.close_tab(b)

    ids = [t.id for t in tm.tabs]
    check("#2a B removed after close", b not in ids, ids)
    check("#2a A and C still present", a in ids and c in ids, ids)
    check("#2a active returns to original tab A (not a neighbor of B)",
          tm.active_tab_id == a, "active=%s" % tm.active_tab_id)


def test_2b_capture_failure_aborts_save(window):
    tm = window.tab_manager
    a, b, _c = build_three_tabs(tm)
    reset_tabs_clean(tm)
    tm.find(b).dirty = True
    tm.switch_to_tab(a)

    calls = {"n": 0}
    orig_save = window.save_project

    def counting_save():
        calls["n"] += 1
        return orig_save()
    window.save_project = counting_save

    orig_capture = tm.capture_active_session
    tm.capture_active_session = lambda: False

    global _choice_role
    _choice_role = QMessageBox.AcceptRole  # user clicks "Save"
    tm.close_tab(b)

    tm.capture_active_session = orig_capture
    window.save_project = orig_save

    ids = [t.id for t in tm.tabs]
    check("#2b dirty background tab NOT removed when capture fails", b in ids, ids)
    check("#2b live tab unchanged (still A)", tm.active_tab_id == a,
          "active=%s" % tm.active_tab_id)
    check("#2b save_project NOT called (wrong tab not saved)", calls["n"] == 0,
          "calls=%d" % calls["n"])


def test_1_exit_warning(window):
    tm = window.tab_manager
    reset_tabs_clean(tm)
    check("#1 clean workspace -> confirm returns True",
          window._confirm_close_with_dirty_tabs() is True)

    tm.get_active().dirty = True

    global _choice_role
    _choice_role = QMessageBox.RejectRole  # "Cancel"
    check("#1 dirty + Cancel -> confirm returns False",
          window._confirm_close_with_dirty_tabs() is False)

    _choice_role = QMessageBox.DestructiveRole  # "Quit anyway"
    check("#1 dirty + Quit anyway -> confirm returns True",
          window._confirm_close_with_dirty_tabs() is True)

    _choice_role = QMessageBox.RejectRole
    ev = QCloseEvent()
    ev.accept()
    window.closeEvent(ev)
    check("#1 closeEvent ignored on Cancel (quit aborted)", not ev.isAccepted())


def test_3_settings_preserve_tab_edge(window):
    settings_dir = os.path.join(_TMP_APPDATA, "OpenStrandStudio")
    os.makedirs(settings_dir, exist_ok=True)
    file_path = os.path.join(settings_dir, "user_settings.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Theme: dark\n")
        f.write("Language: en\n")
        f.write("TabEdgePosition: anchor:top_left\n")

    window.settings_dialog.save_settings_to_file()

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    check("#3 TabEdgePosition survives a settings save",
          "TabEdgePosition: anchor:top_left" in content, "file now:\n%s" % content)


def test_hebrew_rtl(window):
    """The fixes must hold with the UI switched to Hebrew (RTL)."""
    he = translations['he']
    check("HE translation keys present (quit_anyway / unsaved_tabs_on_exit)",
          'quit_anyway' in he and 'unsaved_tabs_on_exit' in he)

    window.set_language('he')
    check("HE main window reports RTL language code", window.language_code == 'he')

    tm = window.tab_manager
    a, b, c = build_three_tabs(tm)
    reset_tabs_clean(tm)

    # Untitled titles must localize to Hebrew.
    title = tm.title_for(tm.find(a))
    check("HE untitled tab title is localized", title.startswith(he['untitled']),
          "title=%r" % title)

    tm.find(b).dirty = True
    tm.switch_to_tab(a)

    global _choice_role
    _choice_role = QMessageBox.AcceptRole  # "שמירה" (Save)
    install_file_mocks(os.path.join(_TMP_APPDATA, "proj_he.json"))
    tm.close_tab(b)
    ids = [t.id for t in tm.tabs]
    check("HE background close returns to original tab (RTL)",
          tm.active_tab_id == a and b not in ids and c in ids,
          "active=%s ids=%s" % (tm.active_tab_id, ids))

    tm.get_active().dirty = True
    _choice_role = QMessageBox.RejectRole  # "ביטול" (Cancel)
    check("HE exit warning Cancel aborts quit (RTL)",
          window._confirm_close_with_dirty_tabs() is False)

    window.set_language('en')  # restore for any later checks


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    install_dialog_mocks()
    install_file_mocks(os.path.join(_TMP_APPDATA, "proj.json"))

    print("=" * 64)
    print("1.108 tab/view-mode fix regression tests")
    print("APPDATA redirected to: %s" % _TMP_APPDATA)
    print("=" * 64)

    window = MainWindow()
    tm = window.tab_manager

    test_switch_returns_bool(tm)
    test_2a_background_close_keeps_active(window)
    test_2b_capture_failure_aborts_save(window)
    test_1_exit_warning(window)
    test_3_settings_preserve_tab_edge(window)
    print("- Hebrew (RTL) " + "-" * 49)
    test_hebrew_rtl(window)

    print("-" * 64)
    print("RESULT: %d passed, %d failed" % (_PASS, _FAIL))
    print("=" * 64)

    # os._exit() skips Python's buffer flush, so flush explicitly first.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0 if _FAIL == 0 else 1)


if __name__ == "__main__":
    main()
