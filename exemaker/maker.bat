@echo off
setlocal enabledelayedexpansion
cls
title 🚀 PyInstaller EXE Builder (Reliable Version File)
color 0A

echo.
echo =====================================================
echo            💻  PYINSTALLER AUTO BUILDER  💻
echo =====================================================
echo.

:: Ask for script name
set /p SCRIPT="📄 Enter your Python script name (with .py extension): "
if not exist "%SCRIPT%" (
    echo [❌ ERROR] File "%SCRIPT%" not found!
    pause
    exit /b
)

:: Extract base name
for %%F in ("%SCRIPT%") do set BASENAME=%%~nF

:: Ask for version
set /p VERSION="🔢 Enter version number (e.g. 1.0.7): "

:: Ask for company and description
set /p COMPANY="🏢 Enter company name (default My Company): "
if "!COMPANY!"=="" set COMPANY=My Company
set /p DESC="📝 Enter description (default Simple App): "
if "!DESC!"=="" set DESC=Simple App

:: Convert version to numeric tuple
set "NUMVER=!VERSION:.=,!"

:: ===============================
:: Write version.txt line by line
:: ===============================
echo # UTF-8 > version.txt
echo VSVersionInfo( >> version.txt
echo   ffi=FixedFileInfo( >> version.txt
echo     filevers=(!NUMVER!,0), >> version.txt
echo     prodvers=(!NUMVER!,0), >> version.txt
echo     mask=0x3f, >> version.txt
echo     flags=0x0, >> version.txt
echo     OS=0x40004, >> version.txt
echo     fileType=0x1, >> version.txt
echo     subtype=0x0, >> version.txt
echo     date=(0, 0) >> version.txt
echo   ), >> version.txt
echo   kids=[ >> version.txt
echo     StringFileInfo([ >> version.txt
echo       StringTable('040904B0',[ >> version.txt
echo         StringStruct('CompanyName','!COMPANY!'), >> version.txt
echo         StringStruct('FileDescription','!DESC!'), >> version.txt
echo         StringStruct('FileVersion','!VERSION!'), >> version.txt
echo         StringStruct('InternalName','!BASENAME!'), >> version.txt
echo         StringStruct('OriginalFilename','!BASENAME!.exe'), >> version.txt
echo         StringStruct('ProductName','!BASENAME!'), >> version.txt
echo         StringStruct('ProductVersion','!VERSION!')]) >> version.txt
echo       ]), >> version.txt
echo     VarFileInfo([VarStruct('Translation',[1033,1200])]) >> version.txt
echo   ] >> version.txt
echo ) >> version.txt

echo ✅ version.txt created successfully!
echo.

:: Delete old spec if exists
if exist "!BASENAME!.spec" del "!BASENAME!.spec"

:: Build EXE with PyInstaller
cls
echo =====================================================
echo ⚙️  Building "!SCRIPT!" (v!VERSION!) ...
echo =====================================================
echo.

if exist "icon.ico" (
    pyinstaller --onefile --noconsole --clean --icon=icon.ico --add-data "icon.ico;." --add-data "icon.png;." --version-file=version.txt "!SCRIPT!"
) else (
    echo [⚠️ WARNING] icon.ico not found — building without icon.
    pyinstaller --onefile --noconsole --clean --version-file=version.txt "!SCRIPT!"
)

:: Remove temporary version file
del version.txt >nul 2>&1

echo.
echo =====================================================
echo ✅  BUILD COMPLETE!
echo 📦  Version: !VERSION!
echo 🎯  Output: dist\!BASENAME!.exe
echo =====================================================
pause
