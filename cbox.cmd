::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFDZ2ZziyNWiuE6cZ+9TB6viIpkhQZO4qdZ+W6byLLOxe+FDqO8R4gDRKlsxs
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSTk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+IeA==
::cxY6rQJ7JhzQF1fEqQJhZksaHGQ=
::ZQ05rAF9IBncCkqN+0xwdVsFAlTMbAs=
::ZQ05rAF9IAHYFVzEqQITCjRsLA==
::eg0/rx1wNQPfEVWB+kM9LVsJDAeAM3P0A60ZiA==
::fBEirQZwNQPfEVWB+kM9LVsJDAeAM3Pa
::cRolqwZ3JBvQF1fEqQITKhRMDAKNLiutD7sY5//ojw==
::dhA7uBVwLU+EWH+rzGwVHHs=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATEvGF5aEoNFVbPbjvoUPUe8ajdwNKph3ldc/AwbZ+Vug==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRmw/EsjaBJHDAXCOnm/A6Id+u27/OWBtlocRudxGA==
::Zh4grVQjdCuDJHSdxFA/LwlVQRe+P2a+OrYe5/C16vKCwg==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
cls
setlocal enabledelayedexpansion

:: ===========================================
:: FOXNET CBOX v1.0 with ANSI colors
:: ===========================================

:: -------- Banner ---------------
echo [97;44m####################################################### [0m
echo [97;44mCBOX v1.0 for Windows                                   [0m
echo [97;44mAn Advanced command-line interface for Windows(CMD)     [0m
echo [97;44mCopyright (c) 1992-2026 by FOXNET Group                 [0m
echo [97;44mhttps://software.foxnet.ir                              [0m
echo [97;44m####################################################### [0m
echo [32mType "?" for command list.[0m

:: -------- Command History Setup -----------
set "history="

:loop
set "cmdInput="

:: نمایش پرومپت و دایرکتوری فعلی
echo.
echo [31;44mCBOX> type ? for command list[0m
for /f "delims=" %%d in ('cd') do set "currentDir=%%d"
echo [30;46mCurrent Directory: !currentDir![0m
set /p cmdInput=[94mCBOX ^> [0m

if not defined cmdInput (
    rem User pressed Enter with no input → do nothing, go back to prompt
    goto loop
)

:: ذخیره در تاریخچه
set history=!history!^|!cmdInput!

:: دستورات خروج
if /i "!cmdInput!"=="exit" goto end
if /i "!cmdInput!"=="quit" goto end

:: راهنما
if /i "!cmdInput!"=="?" (
    call :helpScreen
    goto loop
)

:: اجرای دستور
call :executeCommand "!cmdInput!"
goto loop

:: ============================================
:: ========== EXECUTE COMMAND FUNCTION =========
:: ============================================
:executeCommand
set "cmd=%~1"

:: ---------- CLEAR SCREEN ----------
if /i "!cmd!"=="cl" (
    call :showHelp "cl" "Clear screen" "cl"
    cls
    goto :eof
)

:: ---------- WHOAMI ----------
if /i "!cmd!"=="who" (
    call :showHelp "who" "Show current user" "who"
    echo [33mCurrent user:[0m
    whoami
    goto :eof
)

:: ---------- SYSTEM INFORMATION ----------
if /i "!cmd!"=="ver" (
    call :showHelp "ver" "Show CBOX version" "ver"
    echo [33mCBOX Version 1.0 by FOXNET[0m
    systeminfo | findstr /B /C:"OS Version"
    goto :eof
)

:: ---------- NETWORK INFORMATION ----------
if /i "!cmd!"=="netstat" (
    call :showHelp "netstat" "Show network connections" "netstat"
    echo [33mNetwork connections:[0m
    netstat
    goto :eof
)

if /i "!cmd!"=="arp" (
    call :showHelp "arp" "Show ARP cache" "arp -a"
    echo [33mARP cache:[0m
    arp -a
    goto :eof
)

if /i "!cmd!"=="nslookup" (
    call :showHelp "nslookup" "Query DNS servers" "nslookup [host]"
    set /p host=[32mEnter host ^> [0m
    echo [33mQuerying DNS for !host!:[0m
    nslookup !host!
    goto :eof
)

:: ---------- TASK/KILL RELATED ----------
if /i "!cmd!"=="task" (
    call :showHelp "task" "Show running tasks (tasklist)" "task"
    echo [33mRunning tasks:[0m
    tasklist
    goto :eof
)

if /i "!cmd!"=="endtask" (
    call :showHelp "endtask" "Kill a process by name" "endtask [processname]"
    set /p pname=[32mEnter process name ^> [0m
    taskkill /IM !pname! /F
    goto :eof
)

:: ---------- DISK COMMANDS ----------
if /i "!cmd!"=="dirfree" (
    call :showHelp "dirfree" "Show disk space of all drives" "dirfree"
    echo [33mDisk free info:[0m
    wmic logicaldisk get caption,freespace,size
    goto :eof
)


:: ---------- DIR COMMANDS ----------
if /i "!cmd!"=="ls" (
    call :showHelp "ls" "List files and folders" "ls [path]"
    echo [33mListing directory:[0m
    dir
    goto :eof
)

echo !cmd! | findstr /b /i "ls " >nul
if !errorlevel!==0 (
    for /f "tokens=2*" %%a in ("!cmd!") do (
        call :showHelp "ls" "List files and folders" "ls [path]"
        echo [33mListing directory: %%a[0m
        dir %%a
    )
    goto :eof
)

:: ---------- PING ----------
echo !cmd! | findstr /b /i "pi " >nul
if !errorlevel!==0 (
    for /f "tokens=2*" %%a in ("!cmd!") do (
        call :showHelp "pi" "Ping a host" "pi [host] [-t or /? to see options]"
        echo [33mPinging %%a with options %%b...[0m
        ping %%a %%b
    )
    goto :eof
)


 
:: ---------- TRACERT ----------
echo !cmd! | findstr /b /i "tr " >nul
if !errorlevel!==0 (
    for /f "tokens=2*" %%a in ("!cmd!") do (
        call :showHelp "tr" "Trace route to a host(No domain name resolve)" "tr [host]"
        echo [33mTracing route to %%a...[0m
        tracert -d %%a
    )
    goto :eof
)

:: ---------- COPY ----------
echo !cmd! | findstr /b /i "cp " >nul
if !errorlevel!==0 (
    for /f "tokens=2,*" %%a in ("!cmd!") do (
        call :showHelp "cp" "Copy file" "cp source target"
        echo [33mCopying %%a to %%b...[0m
        copy "%%a" "%%b"
    )
    goto :eof
)

:: ---------- MOVE ----------
echo !cmd! | findstr /b /i "mv " >nul
if !errorlevel!==0 (
    for /f "tokens=2,*" %%a in ("!cmd!") do (
        call :showHelp "mv" "Move or rename file" "mv source target"
        echo [33mMoving %%a to %%b...[0m
        move "%%a" "%%b"
    )
    goto :eof
)

:: ---------- DELETE ----------
echo !cmd! | findstr /b /i "del " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "del" "Delete file" "del filename"
        echo [33mDeleting %%a...[0m
        del "%%a"
    )
    goto :eof
)

:: ---------- MAKE DIRECTORY ----------
echo !cmd! | findstr /b /i "mkd " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "mkd" "Create directory" "mkd folder"
        echo [33mCreating directory %%a...[0m
        mkdir "%%a"
    )
    goto :eof
)

:: ---------- REMOVE DIRECTORY ----------
echo !cmd! | findstr /b /i "rmd " >nul
if !errorlevel!==0 (
    for /f "tokens=2*" %%a in ("!cmd!") do (
        call :showHelp "rmd" "Remove directory - Use /s to remove non-empty directories" "rmd [/s] dirname"
        echo [33mRemoving directory %%a %%b...[0m
        rd "%%a" %%b
    )
    goto :eof
)


:: ---------- IP CONFIG ----------
if /i "!cmd!"=="ip" (
    call :showHelp "ip" "Show network info" "ip"
    echo [33mNetwork info:[0m
    ipconfig
    goto :eof
)

:: ---------- IP CONFIG all----------
if /i "!cmd!"=="ipa" (
    call :showHelp "ipa" "Show network info for all " "ipa"
    echo [33mNetwork info:[0m
    ipconfig
    goto :eof
)


:: ---------- TASK LIST ----------
if /i "!cmd!"=="ps" (
    call :showHelp "ps" "Show running processes" "ps"
    echo [33mRunning processes:[0m
    tasklist
    goto :eof
)

:: ---------- KILL PROCESS ----------
echo !cmd! | findstr /b /i "kill " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "kill" "Kill a process by PID" "kill PID"
        echo [33mKilling process %%a...[0m
        taskkill /PID %%a
    )
    goto :eof
)

:: ---------- DISK FREE ----------
if /i "!cmd!"=="df" (
    call :showHelp "df" "Show disk free info" "df"
    echo [33mDisk free info:[0m
    wmic logicaldisk get size,freespace,caption
    goto :eof
)

:: ---------- SYSTEM INFO ----------
if /i "!cmd!"=="info" (
    call :showHelp "info" "Show system info" "info"
    echo [33mSystem info:[0m
    systeminfo
    goto :eof
)

:: ---------- BUILT-IN FILE EXPLORER ----------
if /i "!cmd!"=="explore" (
    call :showHelp "explore" "Open built-in file explorer" "explore"
    call :fileExplorer
    goto :eof
)

:: ---------- DEFAULT: Run normal Windows command ----------
 
call :showHelp "[31m!cmd![0m" "[31mTHIS IS NOT A CBOX COMMAND[0m" "[31m!cmd![0m"
echo [33mOutput:[0m
!cmd!
echo.
goto :eof

:: ============================================
:: ========== SHOW MINI-HELP FUNCTION =========
:: ============================================
:showHelp
echo.
echo [32m***************** Command Help ******************[0m
echo [36mCommand     : %~3[0m
echo [36mDescription : %~2[0m
echo [32m*************************************************[0m
echo.
exit /b

:: ============================================
:: ========== HELP SCREEN =====================
:: ============================================
:helpScreen
cls
echo.
echo [37m===============CBOX v1.0 HELP ======================[0m
echo [37mShort commands for common tasks by CMD  [0m
echo [37mCopyright (c) 1992-2026 by FOXNET[0m
echo [37mhttps://software.foxnet.ir[0m
echo [37m====================================================[0m
echo.
echo [32mls [path][0m         - List files and folders (optional path)
echo [32mpi [host][0m         - Ping host (supports additional ping options)
echo [32mtr [host][0m         - Trace route to host (no domain name resolve)
echo [32mcp src dst[0m       - Copy file from src to dst
echo [32mmv src dst[0m       - Move or rename file from src to dst
echo [32mdel file[0m        - Delete file
echo [32mmkd folder[0m      - Create directory
echo [32mrmd [/s] dirname[0m - Remove directory (use /s to remove non-empty)
echo [32mdirfree[0m       - Show disk space of all drives (wmic)
echo [32mdf[0m            - Show disk free info
echo [32mip[0m            - Show network info (ipconfig)
echo [32mipa[0m           - Show network info for all (ipconfig)
echo [32mtask[0m          - Show running tasks (tasklist)
echo [32mps[0m            - Show running processes (tasklist)
echo [32mkill [pid][0m     - Kill process by PID
echo [32mendtask[0m       - Kill process by name
echo [32minfo[0m           - Show system info (systeminfo)
echo [32mwho[0m            - Show current user
echo [32mver[0m            - Show CBOX version
echo [32mnetstat[0m       - Show network connections
echo [32marp[0m            - Show ARP cache
echo [32mnslookup[0m      - Query DNS servers
echo [32mcl[0m             - Clear screen
echo [32mexplore[0m       - Built-in file explorer
echo [32m?[0m              - Show this help screen
echo [32mexit / quit[0m   - Quit CBOX
echo [32m(any other command)[0m - Runs as a normal Windows command
echo.

goto :eof

:: ============================================
:: ========== BUILT-IN FILE EXPLORER ==========
:: ============================================
:fileExplorer
echo.
set /p folderPath=[32mEnter folder path to explore ^> [0m
if exist "%folderPath%" (
    echo [33mListing contents of %folderPath%[0m
    dir "%folderPath%"
) else (
    echo [31mFolder does not exist.[0m
)
goto :eof

:end
echo.
echo [37mExiting CBOX...[0m
echo.
exit /b

