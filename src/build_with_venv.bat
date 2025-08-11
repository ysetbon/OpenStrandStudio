@echo off
echo Creating virtual environment for clean build...

REM Create a new virtual environment
python -m venv build_env

REM Activate it
call build_env\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install PyQt5 pillow pyinstaller

REM Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build with PyInstaller
echo Building executable...
pyinstaller --onefile --windowed --name OpenStrandStudio --icon=box_stitch.ico --add-data "box_stitch.ico;." --add-data "settings_icon.png;." --add-data "flags;flags" --add-data "mp4;mp4" --add-data "samples;samples" main.py

echo Build complete!
deactivate
pause