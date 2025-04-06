# Box Stitch Application - Windows Installation Guide

## Installation Instructions

1. **Download the Application**
   - Download the Box Stitch installer (BoxStitch.exe) from the official website or release page.

2. **Run the Installer**
   - Locate the downloaded .exe file in your Downloads folder
   - Double-click on the file to start the installation
   - If a security warning appears, click "Run" or "Yes" to continue

3. **Launch the Application**
   - Once installed, you can launch Box Stitch from:
     - The desktop shortcut (if created during installation)
     - The Start Menu
     - The installation directory

## System Requirements

- Windows 10 or newer
- 4GB RAM (minimum)
- 100MB of free disk space

## Troubleshooting

If you encounter any issues during installation:

1. **Windows Security Alert**
   - If Windows Defender or your antivirus blocks the installation, you may need to temporarily disable it or add an exception.

2. **Missing Dependencies**
   - The application is bundled as a single executable with all dependencies included. No additional installation should be required.

3. **Application Won't Start**
   - Try running the application as administrator by right-clicking the icon and selecting "Run as administrator"

## Uninstallation

To remove the application:

1. Go to Control Panel > Programs > Programs and Features
2. Find Box Stitch in the list of installed programs
3. Select it and click "Uninstall"
4. Follow the uninstallation prompts

## For Developers: Building from Source

If you want to build the application from source code:

1. **Prerequisites**
   - Install Python 3.x
   - Install PyInstaller: `pip install pyinstaller`
   - Make sure you have the source files (main.py, box_stitch.ico, settings_icon.png)

2. **Build Command**
   - Open a command prompt in the source directory
   - Run the following command:
   ```
   pyinstaller --onefile --windowed --name OpenStrandStudio --icon=box_stitch.ico --add-data "box_stitch.ico;." --add-data "settings_icon.png;." main.py
   ```
   - The executable will be created in the `dist` folder

## Support

If you need additional help with installation, please contact our support team at support@boxstitch.com or visit our website. 