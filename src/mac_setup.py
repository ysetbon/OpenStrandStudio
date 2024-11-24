import os
import sys
import shutil
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
ICON_ICO_PATH = r'/Users/hedyrutman/Documents/Github/OpenStrandStudio/src/box_stitch.ico'
ICON_ICNS_PATH = 'box_stitch.icns'
MAIN_SCRIPT = 'run.py'

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
    shutil.rmtree(iconset_dir)

    return True

def remove_readonly(func, path, excinfo):
    os.chmod(path, os.stat(path).st_mode | 0o200)
    func(path)

def force_remove_path(path):
    if os.path.isfile(path) or os.path.islink(path):
        try:
            os.chmod(path, 0o777)
            os.unlink(path)
            print(f"Removed file: {path}")
        except Exception as e:
            print(f"Error removing file {path}: {e}")
    elif os.path.isdir(path):
        try:
            shutil.rmtree(path, onerror=remove_readonly)
            print(f"Removed directory: {path}")
        except Exception as e:
            print(f"Error removing directory {path}: {e}")

def clean_build():
    paths_to_remove = ['build', 'dist', '__pycache__'] + [f for f in os.listdir() if f.endswith('.pyc')]
    for path in paths_to_remove:
        force_remove_path(path)

    # Remove all directories containing 'dist-info' or ending with '.egg-info'
    for root, dirs, files in os.walk('.', topdown=False):
        for dir_name in dirs:
            if 'dist-info' in dir_name or dir_name.endswith('.egg-info'):
                force_remove_path(os.path.join(root, dir_name))

# Clean up any existing build artifacts
clean_build()

# Convert the .ico file to .icns
if not os.path.exists(ICON_ICNS_PATH):
    print("Converting .ico to .icns...")
    success = convert_ico_to_icns(ICON_ICO_PATH, ICON_ICNS_PATH)
    if not success:
        print("Failed to convert icon.")
        sys.exit(1)
else:
    print(".icns file already exists.")

# Create run.py
with open('run.py', 'w') as f:
    f.write('''
import sys
import os

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Add the bundle's lib directory to sys.path
sys.path.insert(0, os.path.join(bundle_dir, 'lib'))

# Now import and run your main script
import main
main.main()  # Assuming your main.py has a main() function, adjust if necessary
''')

OPTIONS = {
    'argv_emulation': False,
    'iconfile': ICON_ICNS_PATH,
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
        'NSRequiresAquaSystemAppearance': False,
        'LSBackgroundOnly': False,
        'LSUIElement': False,
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
    'packages': ['PyQt5', 'numpy', 'PIL'],
    'includes': ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'numpy', 'PIL'],
    'excludes': ['tkinter'],
    'frameworks': [],
}

def run_setup():
    try:
        setup(
            name=APP_NAME,
            app=[MAIN_SCRIPT],
            data_files=[],
            options={'py2app': OPTIONS},
            setup_requires=['py2app'],
            version=APP_VERSION,
            author=APP_PUBLISHER,
            author_email=APP_CONTACT,
            description=APP_COMMENTS,
        )
    except Exception as e:
        print(f"An error occurred during setup: {e}")
        return False
    return True

# Main execution
if __name__ == "__main__":
    print("Starting setup process...")
    clean_build()
    print("Build directory cleaned.")

    retry_count = 3
    for attempt in range(retry_count):
        print(f"Attempt {attempt + 1} of {retry_count}")
        if run_setup():
            print("Setup completed successfully!")
            break
        else:
            print("Setup failed. Cleaning up and retrying...")
            clean_build()
    else:
        print(f"Setup failed after {retry_count} attempts. Please check your environment and try again.")
        sys.exit(1)
