# OpenStrand Studio - macOS Installation Guide

This guide provides instructions for building and packaging OpenStrand Studio for macOS.

## Prerequisites

Before starting, ensure you have the following installed:

- Python 3.9+ (recommended: 3.13)
- pip (Python package manager)
- Xcode Command Line Tools

## Step 1: Install Required Dependencies

Install all required Python packages:

```bash
pip3 install PyQt5==5.15.4 Pillow numpy pyinstaller
```

## Step 2: Build the Application

From the root directory of the project, run the following command to create the application bundle:

```bash
cd src
pyinstaller --name="OpenStrandStudio" --windowed --icon=box_stitch.icns --add-data="box_stitch.icns:." --add-data="settings_icon.png:." --hidden-import=PyQt5 --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtGui --hidden-import=PyQt5.QtWidgets --hidden-import=numpy --hidden-import=PIL main.py
```

This will create the application bundle in the `dist` directory.

## Step 3: Create the Installer Package

Make the installer script executable:

```bash
chmod +x build_installer.sh
```

Run the installer script:

```bash
./build_installer.sh
```

This will create an installer package in the `installer_output` directory.

## Step 4: Distribute the Application

You can distribute the installer package (`OpenStrand Studio_1_100.pkg`) to users. When they run it, it will:

1. Install the application to their Applications folder
2. Create a desktop icon
3. Offer to launch the application after installation

## Troubleshooting

If you encounter issues with missing dependencies:

1. Ensure all required packages are installed
2. Check the application log for errors
3. For PyQt5 issues, run the application from Terminal to see detailed error output:
   ```bash
   /Applications/OpenStrand\ Studio.app/Contents/MacOS/OpenStrandStudio
   ```

## Optional: Updating the Application

When updating the application:

1. Update the version number in `build_installer.sh`
2. Update the welcome message in `build_installer.sh` with new features
3. Follow Steps 2-4 to rebuild and package

## Notes for Developers

- The installer package includes scripts that handle setup and configuration
- The PyInstaller command bundles all dependencies into the application
- The final application should run on macOS 10.13 or later 