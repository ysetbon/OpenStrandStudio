@echo off
REM Build complete installer for MxN CAD Generator
REM This script builds the exe and then creates the installer

echo ============================================
echo MxN CAD Generator - Full Installer Build
echo ============================================
echo.

set SCRIPT_DIR=%~dp0

REM Step 1: Build the executable
echo Step 1: Building executable with PyInstaller...
echo.
call "%SCRIPT_DIR%build.bat"
if errorlevel 1 (
    echo ERROR: Executable build failed
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "%SCRIPT_DIR%dist\MxN_CAD_Generator.exe" (
    echo ERROR: Executable not found after build
    pause
    exit /b 1
)

REM Step 2: Build the installer with Inno Setup
echo.
echo Step 2: Building installer with Inno Setup...
echo.

REM Create output directory
if not exist "%SCRIPT_DIR%output" mkdir "%SCRIPT_DIR%output"

REM Try common Inno Setup paths
set ISCC_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
)

if "%ISCC_PATH%"=="" (
    echo.
    echo WARNING: Inno Setup not found in standard locations.
    echo.
    echo Please install Inno Setup from: https://jrsoftware.org/isinfo.php
    echo Or manually run the Inno Setup compiler on: installer_setup.iss
    echo.
    echo The executable was built successfully at:
    echo %SCRIPT_DIR%dist\MxN_CAD_Generator.exe
    echo.
    pause
    exit /b 0
)

echo Using Inno Setup: %ISCC_PATH%
"%ISCC_PATH%" "%SCRIPT_DIR%installer_setup.iss"

if errorlevel 1 (
    echo ERROR: Installer build failed
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build Complete!
echo ============================================
echo.
echo Executable: %SCRIPT_DIR%dist\MxN_CAD_Generator.exe
echo Installer:  %SCRIPT_DIR%output\MxN_CAD_Generator_Setup_1.0.0.exe
echo.

pause
