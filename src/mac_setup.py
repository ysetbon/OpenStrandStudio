import os
import sys
import subprocess
from setuptools import setup

# Define constants
APP_NAME = "OpenStrand Studio"
APP_VERSION = "1.03"
APP_PUBLISHER = "Yonatan Setbon"
APP_CONTACT = "ysetbon@gmail.com"
APP_COMMENTS = "The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com"
ICON_FILE = 'box_stitch.icns'
ORIGINAL_ICON = r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\box_stitch.ico'
MAIN_SCRIPT = r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\main.py'
OUTPUT_DIR = r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\mac'

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Add the src directory to Python path
sys.path.append(r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src')

def convert_icon():
    if not os.path.exists(os.path.join(OUTPUT_DIR, ICON_FILE)):
        if not os.path.exists(ORIGINAL_ICON):
            raise FileNotFoundError(f"Original icon file {ORIGINAL_ICON} not found.")
        
        print(f"Converting {ORIGINAL_ICON} to {ICON_FILE}...")
        
        # Create a temporary iconset directory in the output directory
        iconset_dir = os.path.join(OUTPUT_DIR, 'box_stitch.iconset')
        os.makedirs(iconset_dir, exist_ok=True)
        
        # Convert ico to png if needed
        png_path = os.path.join(OUTPUT_DIR, 'box_stitch.png')
        if not os.path.exists(png_path):
            subprocess.run(['sips', '-s', 'format', 'png', ORIGINAL_ICON, '--out', png_path])
        
        # Generate different sizes
        sizes = [16, 32, 128, 256, 512]
        for size in sizes:
            subprocess.run(['sips', '-z', str(size), str(size), png_path, '--out', os.path.join(iconset_dir, f'icon_{size}x{size}.png')])
            if size <= 256:
                subprocess.run(['sips', '-z', str(size*2), str(size*2), png_path, '--out', os.path.join(iconset_dir, f'icon_{size}x{size}@2x.png')])
        
        # Create icns file
        subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', os.path.join(OUTPUT_DIR, ICON_FILE)])
        
        # Clean up
        subprocess.run(['rm', '-rf', iconset_dir])
        os.remove(png_path)
        
        print(f"Icon conversion complete. {ICON_FILE} created in {OUTPUT_DIR}.")
    else:
        print(f"{ICON_FILE} already exists in {OUTPUT_DIR}. Skipping conversion.")

# Convert icon
convert_icon()

APP = [MAIN_SCRIPT]
DATA_FILES = [os.path.join(OUTPUT_DIR, ICON_FILE)]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt5'],
    'iconfile': os.path.join(OUTPUT_DIR, ICON_FILE),
    'dist_dir': os.path.join(OUTPUT_DIR, 'dist'),
    'bdist_base': os.path.join(OUTPUT_DIR, 'build'),
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': APP_COMMENTS,
        'CFBundleIdentifier': "com.yonatansetbon.OpenStrandStudio",
        'CFBundleVersion': APP_VERSION,
        'CFBundleShortVersionString': APP_VERSION,
        'NSHumanReadableCopyright': f"Copyright © 2024, {APP_PUBLISHER}, All Rights Reserved",
        'NSHighResolutionCapable': True,
        'NSAppleScriptEnabled': False,
        'NSPrincipalClass': 'NSApplication',
        'NSRequiresAquaSystemAppearance': False,  # Allows dark mode support
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'OpenStrand Studio Document',
                'CFBundleTypeExtensions': ['osd'],
                'CFBundleTypeRole': 'Editor',
            }
        ],
        'CFBundleURLTypes': [
            {
                'CFBundleURLName': 'com.yonatansetbon.OpenStrandStudio',
                'CFBundleURLSchemes': ['openstrandstudio'],
            }
        ],
    },
    'includes': [
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version=APP_VERSION,
    author=APP_PUBLISHER,
    author_email=APP_CONTACT,
    description=APP_COMMENTS,
)