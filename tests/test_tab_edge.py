"""The floating tab bar with many tabs and long titles.

Seven tabs with long titles used to be laid out wider than the bar could hold:
the tabs piled on top of each other, each tab's close button sat under its
neighbour, and the + button disappeared. These tests run the real MainWindow
offscreen and check that the tabs now share the room (shrinking, then scrolling
with a scrollbar under them), that every close button can be clicked, that a
tooltip appears only on a title that is cut off, and that tabs can be reordered.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_test_settings_")

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
os.chdir(SRC_DIR)  # the app loads icons relative to src

import pytest
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt, QTimer
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from tab_bar_widget import (TAB_EDGE_HEIGHT, TAB_EDGE_HEIGHT_SCROLLING, TAB_MAX_WIDTH,
                            TAB_MIN_WIDTH, TAB_MIN_WIDTH_ACTIVE, TabChip, fit_tab_widths,
                            tab_scrollbar_qss)

APP = QApplication.instance() or QApplication([])

LONG_TITLES = [
    "Step 1 · stitch on left needle",
    "i_mean_open_all_the_images",
    "Step 4 · pull new loop through",
    "Step 3 · wrap the yarn",
    "Step 2 · right needle into loop",
    "Step 5 · slip the old stitch off",
    "Step 6 · tighten and repeat the row",
]


def pump(ms=50):
    done = [False]
    QTimer.singleShot(ms, lambda: done.__setitem__(0, True))
    while not done[0]:
        APP.processEvents()


# --------------------------------------------------------------------- fitting
def test_fit_keeps_natural_widths_when_they_fit():
    widths, overflow = fit_tab_widths([120, 150], [96, 96], room=400, gap=8)
    assert widths == [120, 150] and not overflow


def test_fit_caps_one_huge_title():
    widths, overflow = fit_tab_widths([900, 120], [96, 96], room=2000, gap=8)
    assert widths == [TAB_MAX_WIDTH, 120] and not overflow


def test_fit_shrinks_the_widest_first_and_fills_the_room():
    widths, overflow = fit_tab_widths([300, 200, 110], [96, 96, 96], room=500, gap=8)
    assert not overflow
    assert widths[2] == 110                       # the narrow tab keeps its width
    assert abs(widths[0] - widths[1]) <= 1        # the two wide ones share the cut
    assert sum(widths) + 16 <= 500
    assert sum(widths) + 16 >= 497


def test_fit_never_goes_below_the_minimums_and_reports_overflow():
    widths, overflow = fit_tab_widths([300] * 10, [96] * 9 + [124], room=600, gap=8)
    assert overflow
    assert widths == [96] * 9 + [124]


def test_fit_with_no_tabs():
    assert fit_tab_widths([], [], room=100, gap=8) == ([], False)


def test_scrollbar_style_is_the_layer_panels():
    qss = tab_scrollbar_qss('dark')
    for colour in ('#1A1A1A', '#2D2D2D', '#4A4A4A', '#606060'):
        assert colour in qss
    assert 'height: 10px' in qss and 'border-radius: 5px' in qss
    assert '#D4D4D4' in tab_scrollbar_qss('light')
    assert '#BFBFBF' in tab_scrollbar_qss('default')


# ------------------------------------------------------------------ the window
@pytest.fixture
def window():
    win = MainWindow()
    win.show()
    win.resize(1600, 900)
    win.canvas.skip_close_tab_warning = True
    pump(200)
    yield win
    win._confirm_close_with_dirty_tabs = lambda *a, **k: True
    win.close()
    win.deleteLater()
    pump(60)


def open_tabs(win, titles, active_index=None):
    tm = win.tab_manager
    while len(tm.tabs) < len(titles):
        tm.new_tab()
    for session, title in zip(tm.tabs, titles):
        session.title = title
        session.untitled_index = None
    if active_index is not None:
        tm.switch_to_tab(tm.tabs[active_index].id)
    tm.changed.emit()
    if not win.tab_edge.isVisible():
        win.toggle_tabs_edge()
    pump(80)
    return tm


def chips(win):
    edge = win.tab_edge
    return sorted((c for c in edge.findChildren(TabChip) if c.isVisible()),
                  key=lambda c: edge.tab_manager.tabs.index(edge.tab_manager.find(c.tab_id)))


def visible_in_viewport(edge, chip):
    vp = edge._viewport.rect()
    return vp.contains(chip.geometry())


def assert_tabs_usable(win):
    """No overlap; every visible tab's close button is the widget on top at its centre."""
    edge = win.tab_edge
    cs = chips(win)
    for a, b in zip(cs, cs[1:]):
        assert not a.geometry().intersects(b.geometry()), (a.full_title, b.full_title)
    for c in cs:
        assert c.width() >= c.min_width()
        if not visible_in_viewport(edge, c):
            continue
        centre = c.close_btn.mapTo(edge._viewport, c.close_btn.rect().center())
        assert edge._viewport.childAt(centre) is c.close_btn, c.full_title
    # The edge fits on the canvas and the + button sits inside it.
    assert edge.width() <= win.canvas.width()
    assert edge.rect().contains(edge.plus_btn.geometry())


def test_seven_long_tabs_shrink_instead_of_piling_up(window):
    open_tabs(window, LONG_TITLES, active_index=4)
    window.resize(1300, 900)
    pump(150)
    edge = window.tab_edge
    assert_tabs_usable(window)
    assert all(edge._viewport.rect().contains(c.geometry()) for c in chips(window))


def test_tooltip_only_on_cut_off_titles(window):
    open_tabs(window, LONG_TITLES, active_index=4)
    window.resize(1300, 900)
    pump(150)
    cut = [c for c in chips(window) if c.is_title_cut()]
    assert cut, "with seven long titles at this width some titles must be cut"
    for c in chips(window):
        if c.is_title_cut():
            assert c.toolTip() == c.full_title
            assert c.label.text().endswith("…")
        else:
            assert c.toolTip() == ""

    open_tabs(window, ["Step %d" % i for i in range(1, 8)])
    for c in chips(window):
        assert not c.is_title_cut()
        assert c.toolTip() == ""


def test_too_many_tabs_scroll_with_a_scrollbar_under_them(window):
    titles = LONG_TITLES + ["Extra tab number %d with a long name" % i for i in range(1, 9)]
    open_tabs(window, titles, active_index=len(titles) - 1)
    window.resize(1000, 900)
    pump(150)
    edge = window.tab_edge
    assert edge._overflow
    assert edge._hbar.isVisible() and edge.more_btn.isVisible()
    assert edge.height() == TAB_EDGE_HEIGHT_SCROLLING
    assert edge._hbar.height() == 10
    assert edge._hbar.objectName() == 'tabStripScrollBar'
    # Docked at the bottom: the taller edge grows upward, its bottom stays put.
    assert edge.geometry().bottom() == window.canvas.height() - 24 - 1
    # Every tab at its minimum, and the active (last) tab scrolled into view.
    for c in chips(window):
        assert c.width() == c.min_width()
    assert visible_in_viewport(edge, chips(window)[-1])
    assert_tabs_usable(window)

    # Scrolling back to the start shows the first tab.
    edge._hbar.setValue(0)
    pump(30)
    assert visible_in_viewport(edge, chips(window)[0])
    assert not visible_in_viewport(edge, chips(window)[-1])
    assert_tabs_usable(window)

    # Fewer tabs: the scrollbar goes away and the edge is back to its height.
    tm = window.tab_manager
    tm.close_tabs([t.id for t in tm.tabs[3:]], keep_id=tm.tabs[0].id)
    pump(80)
    assert not edge._overflow and not edge._hbar.isVisible()
    assert edge.height() == TAB_EDGE_HEIGHT


def test_wheel_scrolls_the_strip(window):
    titles = ["Long tab title number %d for scrolling" % i for i in range(14)]
    open_tabs(window, titles, active_index=0)
    window.resize(1000, 900)
    pump(150)
    edge = window.tab_edge
    assert edge._overflow and edge._hbar.value() == 0
    from PyQt5.QtGui import QWheelEvent
    pos = QPointF(edge._viewport.geometry().center())
    ev = QWheelEvent(pos, QPointF(edge.mapToGlobal(pos.toPoint())), QPoint(0, 0), QPoint(0, -120),
                     Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
    QApplication.sendEvent(edge, ev)
    assert edge._hbar.value() == 120


def test_window_resize_refits_the_tabs(window):
    open_tabs(window, LONG_TITLES, active_index=0)
    window.resize(1700, 900)
    pump(150)
    wide = window.tab_edge.width()
    window.resize(1100, 900)
    pump(150)
    assert window.tab_edge.width() < wide
    assert_tabs_usable(window)


def test_duplicate_icon_only_on_the_active_tab(window):
    open_tabs(window, LONG_TITLES[:3], active_index=1)
    for c in chips(window):
        assert (c.dup_btn is not None) == c.active
        assert c.min_width() == (TAB_MIN_WIDTH_ACTIVE if c.active else TAB_MIN_WIDTH)


# ------------------------------------------------------------------ reordering
def send_mouse(widget, kind, global_pos, button=Qt.LeftButton, buttons=None):
    local = widget.mapFromGlobal(global_pos)
    if buttons is None:
        buttons = Qt.NoButton if kind == QEvent.MouseButtonRelease else button
    ev = QMouseEvent(kind, QPointF(local), QPointF(local), QPointF(global_pos), button, buttons, Qt.NoModifier)
    QApplication.sendEvent(widget, ev)


def drag_chip(chip, dx_steps):
    start = chip.mapToGlobal(QPoint(30, chip.height() // 2))
    send_mouse(chip, QEvent.MouseButtonPress, start)
    pos = start
    for dx in dx_steps:
        pos = start + QPoint(dx, 0)
        send_mouse(chip, QEvent.MouseMove, pos, button=Qt.NoButton, buttons=Qt.LeftButton)
        pump(5)
    send_mouse(chip, QEvent.MouseButtonRelease, pos)
    pump(60)


def test_drag_a_tab_to_a_new_place(window):
    tm = open_tabs(window, ["One", "Two", "Three", "Four"], active_index=0)
    first = chips(window)[0]
    moving_id = first.tab_id
    # Drop it where "Three" starts.
    distance = chips(window)[2].x() + 5 - first.x()
    drag_chip(first, [10, distance // 2, distance])
    order = [t.title for t in tm.tabs]
    assert order == ["Two", "Three", "One", "Four"], order
    assert tm.tabs[2].id == moving_id
    # Dragging did not switch tabs: the drop is not a click.
    assert tm.active_tab_id == moving_id  # it was already the active tab
    assert_tabs_usable(window)


def test_a_click_still_switches_tabs(window):
    tm = open_tabs(window, ["One", "Two", "Three"], active_index=0)
    target = chips(window)[2]
    drag_chip(target, [1])  # a 1 px wobble is a click, not a drag
    assert tm.active_tab_id == tm.tabs[2].id
    assert [t.title for t in tm.tabs] == ["One", "Two", "Three"]


def test_dropping_where_it_started_keeps_the_order(window):
    tm = open_tabs(window, ["One", "Two", "Three"], active_index=0)
    drag_chip(chips(window)[1], [20, 5, 0])
    assert [t.title for t in tm.tabs] == ["One", "Two", "Three"]
    assert_tabs_usable(window)


def test_rtl_tabs_start_on_the_right_and_drag_the_right_way(window):
    window.language_code = 'he'
    tm = open_tabs(window, ["One", "Two", "Three"], active_index=0)
    cs = chips(window)
    assert cs[0].x() > cs[1].x() > cs[2].x()
    # Drag the first tab (rightmost) to the left, onto the second one's place.
    distance = (cs[1].x() + cs[1].width()) - (cs[0].x() + cs[0].width()) - 5
    drag_chip(cs[0], [-10, distance // 2, distance])
    assert [t.title for t in tm.tabs] == ["Two", "One", "Three"]


# --------------------------------------------------------------- tab manager
def test_move_tab(window):
    tm = open_tabs(window, ["A", "B", "C", "D"])
    ids = [t.id for t in tm.tabs]
    assert tm.move_tab(ids[0], 3)
    assert [t.title for t in tm.tabs] == ["B", "C", "D", "A"]
    assert tm.move_tab(ids[0], -5)  # clamped to the start
    assert [t.title for t in tm.tabs] == ["A", "B", "C", "D"]
    assert not tm.move_tab(ids[1], 1)  # already there
    assert not tm.move_tab("no-such-tab", 0)


def test_move_and_switch_relative(window):
    tm = open_tabs(window, ["A", "B", "C"], active_index=0)
    assert tm.switch_relative(-1)  # wraps to the last tab
    assert tm.get_active().title == "C"
    assert not tm.move_active_tab(1)  # already at the end
    assert tm.move_active_tab(-1)
    assert [t.title for t in tm.tabs] == ["A", "C", "B"]


def test_close_others_and_close_after(window):
    tm = open_tabs(window, ["A", "B", "C", "D", "E"], active_index=4)
    keep = tm.tabs[1].id
    assert tm.close_tabs_after(keep) == 3
    assert [t.title for t in tm.tabs] == ["A", "B"]
    assert tm.active_tab_id == keep  # the active tab was closed: the user stays on B
    assert tm.close_other_tabs(keep) == 1
    assert [t.title for t in tm.tabs] == ["B"]


def test_cancel_stops_closing_the_rest(window):
    tm = open_tabs(window, ["A", "B", "C", "D"], active_index=0)
    for t in tm.tabs:
        t.dirty = True
    window.canvas.skip_close_tab_warning = False
    asked = []

    def fake_close(tab_id, original=tm.close_tab):
        asked.append(tab_id)
        if len(asked) == 2:
            return False  # the user pressed Cancel on the second prompt
        window.canvas.skip_close_tab_warning = True
        try:
            return original(tab_id)
        finally:
            window.canvas.skip_close_tab_warning = False

    tm.close_tab = fake_close
    try:
        assert tm.close_other_tabs(tm.tabs[0].id) == 1
    finally:
        del tm.close_tab
    assert [t.title for t in tm.tabs] == ["A", "C", "D"]


def test_middle_click_closes_a_tab(window):
    tm = open_tabs(window, ["A", "B", "C"], active_index=0)
    chip = chips(window)[1]
    pos = chip.mapToGlobal(QPoint(20, chip.height() // 2))
    send_mouse(chip, QEvent.MouseButtonPress, pos, button=Qt.MiddleButton)
    send_mouse(chip, QEvent.MouseButtonRelease, pos, button=Qt.MiddleButton)
    pump(60)
    assert [t.title for t in tm.tabs] == ["A", "C"]


def test_press_on_the_panel_outside_the_grip_does_not_move_the_edge(window):
    open_tabs(window, ["A", "B"])
    edge = window.tab_edge
    before = edge.pos()
    plus = edge.plus_btn.geometry()
    spot = QPoint(plus.left() - 4, 2)  # panel background between tabs and +
    g = edge.mapToGlobal(spot)
    send_mouse(edge, QEvent.MouseButtonPress, g)
    send_mouse(edge, QEvent.MouseMove, g + QPoint(-200, -200), button=Qt.NoButton, buttons=Qt.LeftButton)
    send_mouse(edge, QEvent.MouseButtonRelease, g + QPoint(-200, -200))
    pump(30)
    assert edge.pos() == before
