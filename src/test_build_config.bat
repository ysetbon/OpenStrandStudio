@echo off
echo Testing build configuration...
echo.

echo Checking for required files:
echo ===========================

if exist "box_stitch.ico" (
    echo [OK] box_stitch.ico found
) else (
    echo [ERROR] box_stitch.ico not found
)

if exist "settings_icon.png" (
    echo [OK] settings_icon.png found
) else (
    echo [ERROR] settings_icon.png not found
)

if exist "images\*.svg" (
    echo [OK] SVG files found in images folder:
    dir /b images\*.svg
) else (
    echo [ERROR] No SVG files found in images folder
)

if exist "flags" (
    echo [OK] flags folder found
) else (
    echo [ERROR] flags folder not found
)

if exist "mp4" (
    echo [OK] mp4 folder found
) else (
    echo [ERROR] mp4 folder not found
)

if exist "samples" (
    echo [OK] samples folder found
) else (
    echo [ERROR] samples folder not found
)

if exist "OpenStrandStudio.spec" (
    echo [OK] OpenStrandStudio.spec found
    echo.
    echo Spec file includes:
    findstr /C:"images/*.svg" OpenStrandStudio.spec
) else (
    echo [ERROR] OpenStrandStudio.spec not found
)

echo.
echo Test complete!
pause