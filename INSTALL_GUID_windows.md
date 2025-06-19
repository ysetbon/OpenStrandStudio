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

2. **IMPORTANT: Disable Logging for Production Build**
   
   **Before building the executable, you MUST disable all logging to prevent performance issues and log file creation:**
   
   - Open `src/main.py` in a text editor
   - Find this line near the top (around line 12): 
     ```python
     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
     ```
   - Replace it with:
     ```python
     logging.basicConfig(level=logging.CRITICAL + 1, format='%(asctime)s - %(levelname)s - %(message)s')
     ```
   
   **OR for complete logging removal:**
   - Comment out or delete ALL logging configuration sections (lines ~15-230) including:
     - MoveModeFilter and move_mode logging setup
     - UndoRedoFilter and undo_redo logging setup  
     - StrandCreationFilter and strand_creation logging setup
     - MaskedStrandFilter and masked_strand logging setup
     - MaskShadowIssueFilter and mask_shadow_issues logging setup
     - CanvasBoundsFilter and canvas_bounds logging setup
   
   **This prevents:**
   - Creation of 6+ log files (move_mode.log, undo_redo.log, etc.)
   - Performance degradation from file I/O operations
   - Disk space usage from extensive logging
   - Any logging output in the final executable

3. **Build Command**
   - Open a command prompt in the source directory
   - Run the following command:
   ```
   pyinstaller --onefile --windowed --name OpenStrandStudio --icon=box_stitch.ico --add-data "box_stitch.ico;." --add-data "settings_icon.png;." main.py
   ```
   - The executable will be created in the `dist` folder

4. **Verify No Logging**
   - Test the built executable to ensure:
     - No .log files are created in the executable directory
     - No console output appears
     - Application runs smoothly without performance issues

## Support

If you need additional help with installation, please contact our support team at support@boxstitch.com or visit our website. 