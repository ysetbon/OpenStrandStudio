# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MxN CAD UI
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

# Paths
# SPECPATH is already the directory containing the spec file, not the file path itself
INSTALLER_DIR = os.path.abspath(SPECPATH)
MXN_STARTINGS_DIR = os.path.dirname(INSTALLER_DIR)
CAD_MXN_DIR = os.path.dirname(os.path.dirname(MXN_STARTINGS_DIR))
ROOT_DIR = os.path.dirname(CAD_MXN_DIR)
SRC_DIR = os.path.join(ROOT_DIR, 'src')

block_cipher = None

# Collect PyQt5 data files and plugins
pyqt5_datas = collect_data_files('PyQt5', include_py_files=False)
pyqt5_binaries = collect_dynamic_libs('PyQt5')
pyqt5_hiddenimports = collect_submodules('PyQt5')

# Collect all Python files from mxn_startings directory
mxn_modules = []
for f in os.listdir(MXN_STARTINGS_DIR):
    if f.endswith('.py') and f != '__init__.py':
        mxn_modules.append((os.path.join(MXN_STARTINGS_DIR, f), '.'))

# Collect all Python files from src directory
src_modules = []
for f in os.listdir(SRC_DIR):
    if f.endswith('.py'):
        src_modules.append((os.path.join(SRC_DIR, f), '.'))

# Collect Twemoji PNG assets used by mxn_emoji_renderer
emoji_assets = []
EMOJI_ASSETS_DIR = os.path.join(MXN_STARTINGS_DIR, 'emoji_assets', 'twemoji_72')
if os.path.isdir(EMOJI_ASSETS_DIR):
    for f in os.listdir(EMOJI_ASSETS_DIR):
        if f.lower().endswith('.png'):
            emoji_assets.append(
                (
                    os.path.join(EMOJI_ASSETS_DIR, f),
                    os.path.join('emoji_assets', 'twemoji_72')
                )
            )

a = Analysis(
    [os.path.join(MXN_STARTINGS_DIR, 'mxn_cad_ui.py')],
    pathex=[MXN_STARTINGS_DIR, SRC_DIR],
    binaries=pyqt5_binaries,
    datas=mxn_modules + src_modules + emoji_assets + pyqt5_datas,
    hiddenimports=pyqt5_hiddenimports + [
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.sip',
        'mxn_lh',
        'mxn_rh',
        'mxn_lh_strech',
        'mxn_rh_stretch',
        'mxn_lh_continuation',
        'mxn_rh_continuation',
        'mxn_emoji_renderer',
        'export_mxn_images',
        'main_window',
        'strand',
        'strand_drawing_canvas',
        'layer_panel',
        'layer_state_manager',
        'attached_strand',
        'masked_strand',
        'save_load_manager',
        'undo_redo_manager',
        'translations',
        'settings_dialog',
        'move_mode',
        'select_mode',
        'attach_mode',
        'rotate_mode',
        'angle_adjust_mode',
        'mask_mode',
        'view_mode',
        'render_utils',
        'shader_utils',
        'splitter_handle',
        'numbered_layer_button',
        'group_layers',
        'curvature_bias_control',
        'mask_grid_dialog',
        'shadow_editor_dialog',
        'update_flags',
        'safe_logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MxN_CAD_Generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['qwindows.dll', 'Qt5*.dll', 'PyQt5*.dll'],  # Don't compress Qt DLLs
    runtime_tmpdir=None,
    console=True,  # Set to True for debugging - change to False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT_DIR, 'box_stitch.ico'),
)
