@echo off
rem Copies the bundled Swedish.isl into the Inno Setup 6 Languages folder so that
rem   Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"
rem compiles on Inno Setup versions older than 6.4 (which do not ship Swedish).
rem Run once, as administrator if Inno Setup is installed under Program Files.
setlocal
set "SRC=%~dp0Languages\Swedish.isl"
set "DEST="
if exist "%ProgramFiles(x86)%\Inno Setup 6\Languages\" set "DEST=%ProgramFiles(x86)%\Inno Setup 6\Languages"
if not defined DEST if exist "%ProgramFiles%\Inno Setup 6\Languages\" set "DEST=%ProgramFiles%\Inno Setup 6\Languages"
if not defined DEST if exist "%LocalAppData%\Programs\Inno Setup 6\Languages\" set "DEST=%LocalAppData%\Programs\Inno Setup 6\Languages"
if not defined DEST (
    echo Could not find the Inno Setup 6 Languages folder. Copy "%SRC%" into it by hand.
    exit /b 1
)
if exist "%DEST%\Swedish.isl" (
    echo Swedish.isl is already present in "%DEST%". Nothing to do.
    exit /b 0
)
copy /Y "%SRC%" "%DEST%\Swedish.isl" >nul
if errorlevel 1 (
    echo Copy failed. Re-run this file as administrator, or copy "%SRC%" into "%DEST%" by hand.
    exit /b 1
)
echo Copied Swedish.isl into "%DEST%". The .iss now compiles with compiler:Languages\Swedish.isl.
endlocal
