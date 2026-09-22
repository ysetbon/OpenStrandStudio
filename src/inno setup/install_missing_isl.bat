@echo off
rem Copies the bundled Inno Setup message files that older Inno Setup 6 versions
rem do not ship (Swedish.isl, ChineseSimplified.isl: both official only from 6.4)
rem into the compiler's Languages folder, so that the [Languages] lines
rem   Name: "swedish"; MessagesFile: "compiler:Languages\Swedish.isl"
rem   Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
rem compile. Run once, as administrator if Inno Setup is under Program Files.
setlocal
set "SRC=%~dp0Languages"
set "DEST="
if exist "%ProgramFiles(x86)%\Inno Setup 6\Languages\" set "DEST=%ProgramFiles(x86)%\Inno Setup 6\Languages"
if not defined DEST if exist "%ProgramFiles%\Inno Setup 6\Languages\" set "DEST=%ProgramFiles%\Inno Setup 6\Languages"
if not defined DEST if exist "%LocalAppData%\Programs\Inno Setup 6\Languages\" set "DEST=%LocalAppData%\Programs\Inno Setup 6\Languages"
if not defined DEST (
    echo Could not find the Inno Setup 6 Languages folder. Copy the files from "%SRC%" into it by hand.
    exit /b 1
)
set "FAILED="
for %%F in ("%SRC%\*.isl") do (
    if exist "%DEST%\%%~nxF" (
        echo %%~nxF is already present in "%DEST%".
    ) else (
        copy /Y "%%~fF" "%DEST%\%%~nxF" >nul && echo Copied %%~nxF into "%DEST%". || set "FAILED=1"
    )
)
if defined FAILED (
    echo A copy failed. Re-run this file as administrator, or copy the files from "%SRC%" into "%DEST%" by hand.
    exit /b 1
)
echo Done. The .iss now compiles with the compiler:Languages\ entries.
endlocal
