@echo off
echo Setting up environment for PyInstaller build...

REM Add Anaconda's Qt binaries to PATH
set PATH=C:\ProgramData\Anaconda3\Library\bin;%PATH%
set PATH=C:\ProgramData\Anaconda3\Lib\site-packages\PyQt5\Qt5\bin;%PATH%

REM Clean previous builds
echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build with PyInstaller
echo Building executable...
pyinstaller --onefile --windowed --name OpenStrandStudio --icon=box_stitch.ico --add-data "box_stitch.ico;." --add-data "settings_icon.png;." --add-binary "C:\ProgramData\Anaconda3\Library\bin\*.dll;." main.py

echo Build complete!
pause