import os
import subprocess
from setuptools import setup

# Define constants
APP_NAME = "OpenStrand Studio"
APP_VERSION = "1.06"
APP_PUBLISHER = "Yonatan Setbon"
APP_CONTACT = "ysetbon@gmail.com"
APP_COMMENTS = (
    "The program is brought to you by Yonatan Setbon, you can contact me at ysetbon@gmail.com"
)
ICON_ICO_PATH = r'C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\box_stitch.ico'
ICON_ICNS_PATH = 'box_stitch.icns'
MAIN_SCRIPT = 'main.py'
OUTPUT_DIR = 'dist'

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert_ico_to_icns(ico_path, icns_path):
    """
    Converts a .ico file to .icns format.
    """
    # Convert .ico to .png
    png_path = 'icon.png'
    try:
        subprocess.run(['sips', '-s', 'format', 'png', ico_path, '--out', png_path], check=True)
    except subprocess.CalledProcessError:
        print("Error converting .ico to .png. Make sure the .ico file exists and 'sips' is available.")
        return False

    # Create iconset directory
    iconset_dir = 'icon.iconset'
    os.makedirs(iconset_dir, exist_ok=True)

    # Generate icon sizes
    sizes = [
        (16, 'icon_16x16.png'),
        (32, 'icon_16x16@2x.png'),
        (32, 'icon_32x32.png'),
        (64, 'icon_32x32@2x.png'),
        (128, 'icon_128x128.png'),
        (256, 'icon_128x128@2x.png'),
        (256, 'icon_256x256.png'),
        (512, 'icon_256x256@2x.png'),
        (512, 'icon_512x512.png'),
        (1024, 'icon_512x512@2x.png'),
    ]

    for size, filename in sizes:
        output_path = os.path.join(iconset_dir, filename)
        subprocess.run(['sips', '-z', str(size), str(size), png_path, '--out', output_path])

    # Create .icns file
    try:
        subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], check=True)
    except subprocess.CalledProcessError:
        print("Error creating .icns file.")
        return False

    # Clean up
    os.remove(png_path)
    subprocess.run(['rm', '-r', iconset_dir])

    return True

# Convert the .ico file to .icns
if not os.path.exists(ICON_ICNS_PATH):
    print("Converting .ico to .icns...")
    success = convert_ico_to_icns(ICON_ICO_PATH, ICON_ICNS_PATH)
    if not success:
        print("Failed to convert icon.")
else:
    print(".icns file already exists.")

OPTIONS = {
    'argv_emulation': True,
    'iconfile': ICON_ICNS_PATH,
    'dist_dir': OUTPUT_DIR,
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
    'packages': ['PyQt5'],
    'includes': ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
}

setup(
    name=APP_NAME,
    app=[MAIN_SCRIPT],
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    version=APP_VERSION,
    author=APP_PUBLISHER,
    author_email=APP_CONTACT,
    description=APP_COMMENTS,
)