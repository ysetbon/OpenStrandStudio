@echo off
REM Build script for MxN CAD Generator
REM This script builds the standalone executable using PyInstaller

echo ============================================
echo Building MxN CAD Generator Executable
echo ============================================

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set MXN_STARTINGS_DIR=%SCRIPT_DIR%..
set ROOT_DIR=%SCRIPT_DIR%..\..\..\..

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Check if PyQt5 is installed
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo PyQt5 not found. Installing...
    pip install PyQt5
    if errorlevel 1 (
        echo ERROR: Failed to install PyQt5
        pause
        exit /b 1
    )
)

REM Navigate to installer directory
cd /d "%SCRIPT_DIR%"

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Run PyInstaller with the spec file
echo Running PyInstaller...
pyinstaller --clean mxn_cad_ui.spec

if errorlevel 1 (
    echo ============================================
    echo ERROR: Build failed!
    echo ============================================
    pause
    exit /b 1
)

echo ============================================
echo Build completed successfully!
echo Executable location: %SCRIPT_DIR%dist\MxN_CAD_Generator.exe
echo ============================================

REM Check if executable was created
if exist "dist\MxN_CAD_Generator.exe" (
    echo.
    echo Would you like to test the executable? (Y/N)
    set /p TESTEXE=
    if /i "%TESTEXE%"=="Y" (
        start "" "dist\MxN_CAD_Generator.exe"
    )
)

pause
