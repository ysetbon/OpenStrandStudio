MxN CAD Generator - Installer Build Instructions
================================================

This folder contains all files needed to build a standalone Windows
executable and installer for the MxN CAD Generator application.

PREREQUISITES
-------------
1. Python 3.8 or higher installed and in PATH
2. pip (Python package manager)
3. Inno Setup 6 (for creating the installer)
   Download from: https://jrsoftware.org/isinfo.php

QUICK BUILD
-----------
Option 1: Build executable only
   Double-click: build.bat

Option 2: Build executable + installer
   Double-click: build_installer.bat

MANUAL BUILD STEPS
------------------

1. Install dependencies:
   pip install -r requirements.txt

2. Build the executable:
   pyinstaller --clean mxn_cad_ui.spec

3. Build the installer (requires Inno Setup):
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_setup.iss

OUTPUT FILES
------------
After building:
- dist\MxN_CAD_Generator.exe     - Standalone executable
- output\MxN_CAD_Generator_Setup_1.0.0.exe - Windows installer

FILES IN THIS FOLDER
--------------------
- mxn_cad_ui.spec    - PyInstaller specification file
- installer_setup.iss - Inno Setup script
- build.bat          - Script to build executable only
- build_installer.bat - Script to build exe + installer
- requirements.txt   - Python dependencies
- README.txt         - This file

TROUBLESHOOTING
---------------

Q: PyInstaller gives "module not found" errors
A: Make sure all dependencies are installed. The spec file includes
   hidden imports, but you may need to add more if you encounter errors.

Q: The executable crashes on startup
A: Run build.bat with console=True in the spec file to see error messages.
   Edit mxn_cad_ui.spec and change: console=False to console=True

Q: Inno Setup is not found
A: Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
   Or manually compile installer_setup.iss from the Inno Setup IDE.

Q: The built exe is very large
A: This is normal for PyQt5 applications. The exe includes Python
   and all required libraries. You can reduce size by:
   - Using UPX compression (enabled by default in spec)
   - Excluding unused PyQt5 modules

VERSION HISTORY
---------------
1.0.0 - Initial release
