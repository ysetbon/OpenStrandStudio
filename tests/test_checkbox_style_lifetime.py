"""Destroy styled controls and verify the shared application style survives."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('module,owner', [
    ('group_layers', 'StrandAngleEditDialog'),
    ('mask_grid_dialog', 'MaskGridDialog'),
    ('shadow_editor_dialog', 'ShadowListItem'),
])
def test_checkbox_destruction_preserves_shared_style(module, owner):
    # Isolate native faults from pytest, and exercise normal interpreter exit.
    script = f'''
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QCheckBox, QDialog, QStyle
from {module} import {owner}
app = QApplication([])
shared = app.style()
original_parent = shared.parent()
for themed in (False, True):
    for _ in range(12):
        dialog = QDialog()
        if themed:
            dialog.setStyleSheet('QCheckBox {{ color: white; background: #333; }}')
        boxes = [QCheckBox('Example', dialog) for _ in range(3)]
        for box in boxes:
            {owner}._apply_large_indicator(None, box, 24)
            proxy = box._large_indicator_style
            {owner}._apply_large_indicator(None, box, 24)
            assert box._large_indicator_style is proxy
            assert proxy.parent() is box
            assert proxy.baseStyle() is not shared
            assert proxy.pixelMetric(QStyle.PM_IndicatorWidth) == 24
            assert shared.parent() is original_parent
        dialog.show()
        app.processEvents()
        dialog.grab()
        dialog.close()
        dialog.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()
        assert sip.isdeleted(proxy)
        assert not sip.isdeleted(shared)
        assert app.style() is shared
        survivor = QCheckBox('Still paints')
        survivor.show()
        app.processEvents()
        survivor.grab()
        survivor.close()
        sip.delete(survivor)
'''
    env = dict(os.environ)
    env.setdefault('QT_QPA_PLATFORM', 'offscreen')
    result = subprocess.run(
        [sys.executable, '-X', 'faulthandler', '-c', script],
        cwd=Path(__file__).resolve().parents[1] / 'src',
        env=env, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('platform', ['offscreen', 'windows'] if sys.platform == 'win32' else ['offscreen'])
def test_group_selection_rotate_duplicate_move(platform, tmp_path):
    script = '''
from PyQt5 import sip
from PyQt5.QtCore import QPointF, QTimer, QCoreApplication, QEvent
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtTest import QTest
from main_window import MainWindow
from strand import Strand
from attached_strand import AttachedStrand
from group_layers import GroupMoveDialog, GroupRotateDialog

app = QApplication([])
window = MainWindow()
window.show()
QTest.qWait(100)
canvas = window.canvas
manager = window.layer_panel.group_layer_manager
panel = manager.group_panel
shared = app.style()
original_parent = shared.parent()
strand = Strand(QPointF(100, 100), QPointF(300, 100), 46,
                set_number=1, layer_name='1_1')
canvas.add_strand(strand)
attached = AttachedStrand(strand, QPointF(strand.end), 1)
attached.end = QPointF(400, 200)
attached.layer_name = '1_2'
attached.update_shape()
if attached not in strand.attached_strands:
    strand.attached_strands.append(attached)
canvas.add_strand(attached)

# Exercise the real checkbox construction and native destruction, including
# more openings than the old hidden-dialog retention limit.
for _ in range(8):
    dialog, boxes = manager._build_strand_selection_dialog(['1'])
    assert boxes
    for _, checkbox in boxes:
        checkbox.setChecked(True)
    QTimer.singleShot(10, dialog.accept)
    assert dialog.exec_() == QDialog.Accepted
    assert shared.parent() is original_parent
    dialog.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    QTest.qWait(20)
    assert not sip.isdeleted(shared)
    canvas.grab()

manager._create_group_inner('ghj', ['1'])
QTest.qWait(100)

def rotate():
    d = app.activeModalWidget()
    assert isinstance(d, GroupRotateDialog)
    d.angle_input.setText('79')
    d.on_ok_clicked()
QTimer.singleShot(30, rotate)
panel.start_group_rotation('ghj')
QTest.qWait(100)
panel.duplicate_group('ghj')
QTest.qWait(100)
assert 'ghj(1)' in panel.groups
target = next(s for s in canvas.strands if s.layer_name == '2_1')
before = QPointF(target.start)

def move():
    d = app.activeModalWidget()
    assert isinstance(d, GroupMoveDialog)
    for value in (12, 116, 178, 263, 331, 349):
        d.dx_slider.setValue(value)
    d.on_ok_clicked()
QTimer.singleShot(30, move)
panel.start_group_move('ghj(1)')
QTest.qWait(150)
assert abs(target.start.x() - before.x() - 349) < 0.001
assert abs(target.start.y() - before.y()) < 0.001

# Every close path completes after the callback, with accepted-only undo saves.
from copy import deepcopy
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton
from translations import translations
history = window.layer_panel.undo_redo_manager
save_state = history.save_state
saves = []
def record_save(*args, **kwargs):
    if kwargs.get('action') == 'group.move':
        saves.append(kwargs)
    return save_state(*args, **kwargs)
history.save_state = record_save
finish_move = panel.finish_group_move
finished = []
def record_finish(name):
    assert app.activeModalWidget() is None
    finished.append(name)
    return finish_move(name)
panel.finish_group_move = record_finish
fields = ('start', 'end', 'control_point1', 'control_point2', 'control_point_center')
for action in ('cancel', 'escape', 'close', 'ok', 'snap'):
    members = panel.resolve_group_data('ghj(1)')['strands']
    initial = [(strand, {k: deepcopy(getattr(strand, k)) for k in fields
                         if hasattr(strand, k)}) for strand in members]
    finished_before, saves_before = len(finished), len(saves)
    def exercise(action=action):
        d = app.activeModalWidget()
        updates = []
        d.move_updated.connect(lambda *args: updates.append(args))
        d.dx_slider.setValue(25)
        assert len(updates) == 1
        d.dy_input.setText('37')
        assert len(updates) == 2
        # Grid motion may exceed the pixel slider range without being clamped
        # by its reciprocal input handler.
        d.x_grid_input.setText('50')
        d.apply_x_grid_movement()
        assert len(updates) == 3
        assert d.total_dx == 25 + 50 * canvas.grid_size
        d.y_grid_input.setText('2')
        d.apply_y_grid_movement()
        assert len(updates) == 4
        assert len(finished) == finished_before
        if action == 'cancel':
            button = next(b for b in d.findChildren(QPushButton)
                          if b.text() == translations[d.language_code]['cancel'])
            button.click()
        elif action == 'escape':
            QTest.keyClick(d, Qt.Key_Escape)
        elif action == 'close':
            d.close()
        elif action == 'ok':
            d.on_ok_clicked()
        else:
            d.snap_to_grid()
        assert len(finished) == finished_before
    QTimer.singleShot(20, exercise)
    panel.start_group_move('ghj(1)')
    accepted = action in ('ok', 'snap')
    assert len(finished) == finished_before + int(accepted)
    assert len(saves) == saves_before + int(accepted)
    for strand, state in initial:
        if not accepted:
            for key, value in state.items():
                assert getattr(strand, key) == value, (action, key)
        for key in ('original_start', 'original_end', 'original_control_point1',
                    'original_control_point2', 'original_control_point_center'):
            assert not hasattr(strand, key), key
    assert panel._move_dialog_ref is None
    QTest.qWait(30)

# Both rotation entry points share cleanup; no timer from an earlier session
# may clear a new rotation of the same group.
for owner in (panel, manager):
    QTimer.singleShot(20, rotate)
    owner.start_group_rotation('ghj')
    assert panel.active_group_name is None
    assert panel._rotation_dialog_ref is None
    assert not canvas._suppress_repaint
    QTest.qWait(60)
# Angle-editor completion also runs outside its close callback.
from group_layers import StrandAngleEditDialog
for owner in (panel, manager):
    def close_angles():
        d = app.activeModalWidget()
        assert isinstance(d, StrandAngleEditDialog)
        d.reject()
    QTimer.singleShot(20, close_angles)
    owner.edit_strand_angles('ghj')
    assert not history._skip_save
    QTest.qWait(30)

# Masks keep their rectangle metadata and edited centers on cancellation.
from masked_strand import MaskedStrand
from types import SimpleNamespace
from group_layers import GroupPanel
crossing = Strand(QPointF(100, 50), QPointF(100, 250), 46,
                  set_number=3, layer_name='3_1')
mask = MaskedStrand(strand, crossing)
mask.deletion_rectangles = [dict(top_left=(90, 90), top_right=(110, 90),
    bottom_left=(90, 110), bottom_right=(110, 110),
    offset_x=2, offset_y=3, x=90, y=90, width=20, height=20)]
mask.edited_center_point = QPointF(101, 102)
mask_members = [strand, crossing, mask]
canvas.groups['mask-rollback'] = {'strands': mask_members}
mask_fields = fields + ('deletion_rectangles', 'base_center_point', 'edited_center_point')
mask_before = [(s, {k: deepcopy(getattr(s, k)) for k in mask_fields if hasattr(s, k)})
               for s in mask_members]
d = GroupMoveDialog(canvas, 'mask-rollback', window)
proxy_panel = SimpleNamespace(canvas=canvas,
    resolve_group_data=lambda name: canvas.groups[name])
d.move_updated.connect(lambda name, x, y: GroupPanel.update_group_move(proxy_panel, name, x, y))
d.dx_slider.setValue(35)
d.dy_slider.setValue(17)
d.restore_initial_positions()
canvas.reset_group_move('mask-rollback')
for s, state in mask_before:
    for key, value in state.items():
        assert getattr(s, key) == value, ('mask rollback', key)
    assert not hasattr(s, 'original_start')
    assert not hasattr(s, 'original_deletion_rectangles')
d.deleteLater()
del canvas.groups['mask-rollback']
assert not sip.isdeleted(shared)
assert shared.parent() is original_parent
canvas.grab()
window._confirm_close_with_dirty_tabs = lambda *a, **k: True
window.close()
window.deleteLater()
QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
QTest.qWait(100)
print('group flow and native teardown passed')
'''
    env = dict(os.environ, QT_QPA_PLATFORM=platform, APPDATA=str(tmp_path))
    result = subprocess.run(
        [sys.executable, '-X', 'faulthandler', '-c', script],
        cwd=Path(__file__).resolve().parents[1] / 'src',
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
