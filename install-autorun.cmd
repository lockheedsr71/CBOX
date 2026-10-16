@echo off
REM ===========================================================================
REM  CBOX AutoRun installer
REM
REM  Registers cbox.cmd as the Command Processor AutoRun value for the current
REM  user, so every new cmd.exe window opens inside CBOX. This is OPTIONAL
REM  and off by default: it changes the behaviour of every cmd window on this
REM  account.
REM
REM    install-autorun.cmd             register AutoRun
REM    install-autorun.cmd /uninstall  remove AutoRun and restore cmd
REM ===========================================================================
setlocal

set "KEY=HKCU\Software\Microsoft\Command Processor"
set "VALUE=AutoRun"
set "CBOX=%~dp0cbox.cmd"

if not exist "%CBOX%" (
    echo [CBOX] Could not find "%CBOX%".
    echo        Run this script from inside the CBOX folder.
    exit /b 1
)

if /i "%~1"=="/uninstall" goto :uninstall

:install
reg query "%KEY%" /v "%VALUE%" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [CBOX] AutoRun is already set. Current value:
    for /f "tokens=2,*" %%a in ('reg query "%KEY%" /v "%VALUE%"') do echo         %%b
    echo.
    choice /c YN /n /m "Overwrite it? [Y/N]: "
    if errorlevel 2 (
        echo [CBOX] Cancelled.
        exit /b 0
    )
)

reg add "%KEY%" /v "%VALUE%" /t REG_SZ /d "\"%CBOX%\"" /f >nul
if errorlevel 1 (
    echo [CBOX] Failed to write the registry value.
    exit /b 1
)

echo [CBOX] AutoRun installed: "%CBOX%"
echo        Every new Command Prompt window will now start CBOX.
echo        Remove it again with:  install-autorun.cmd /uninstall
exit /b 0

:uninstall
reg query "%KEY%" /v "%VALUE%" >nul 2>&1
if errorlevel 1 (
    echo [CBOX] AutoRun was not set. Nothing to do.
    exit /b 0
)

echo [CBOX] Current AutoRun value:
for /f "tokens=2,*" %%a in ('reg query "%KEY%" /v "%VALUE%"') do echo         %%b
echo.
choice /c YN /n /m "Remove it and restore a normal cmd prompt? [Y/N]: "
if errorlevel 2 (
    echo [CBOX] Cancelled.
    exit /b 0
)

REM Delete the value rather than setting it to an empty string: an empty
REM AutoRun is still executed by cmd.exe and would open a second console.
reg delete "%KEY%" /v "%VALUE%" /f >nul
if errorlevel 1 (
    echo [CBOX] Failed to remove the registry value.
    exit /b 1
)

echo [CBOX] AutoRun removed. New cmd windows are back to normal.
exit /b 0