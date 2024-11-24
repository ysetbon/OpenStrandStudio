# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('settings_icon.png', '.'),
        ('mp4', 'mp4'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

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

# Try using the default icon temporarily
app = BUNDLE(
    coll,
    name='OpenStrand Studio.app',
    icon='box_stitch.icns',
    bundle_identifier='com.openstrand.studio',
    info_plist={
        'CFBundleName': 'OpenStrand Studio',
        'CFBundleDisplayName': 'OpenStrand Studio',
        'CFBundleGetInfoString': "OpenStrand Studio",
        'CFBundleIdentifier': "com.openstrand.studio",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'NSAppleEventsUsageDescription': 'OpenStrand Studio needs to access system features.',
        'NSDesktopFolderUsageDescription': 'OpenStrand Studio needs access to save files.',
        'NSDocumentsFolderUsageDescription': 'OpenStrand Studio needs access to save files.',
    },
)
