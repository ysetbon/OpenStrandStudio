# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('box_stitch.icns', '.'), 
        ('settings_icon.png', '.'),
        ('mp4/*.mp4', 'mp4/')  # Include tutorial videos
    ],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'numpy', 'PIL', 'Pillow'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpenStrandStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='box_stitch.icns',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenStrandStudio',
)

app = BUNDLE(
    coll,
    name='OpenStrandStudio.app',
    icon='box_stitch.icns',
    bundle_identifier='com.yonatan.openstrandstudio',
    info_plist={
        'CFBundleDisplayName': 'OpenStrandStudio',
        'CFBundleName': 'OpenStrandStudio',
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': '1.100',
        'CFBundleVersion': '1.100',
        'CFBundleExecutable': 'OpenStrandStudio',
        'CFBundleIconFile': 'box_stitch.icns',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.13.0',
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
    },
)