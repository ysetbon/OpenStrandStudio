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

REM Build with PyInstaller using spec file
echo Building executable...
pyinstaller OpenStrandStudio.spec

echo Build complete!
deactivate
pause