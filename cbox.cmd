@echo off
cls
setlocal enabledelayedexpansion

:: ===========================================
:: FOXNET CBOX v1.0 with ANSI colors
:: ===========================================

:: -------- Banner ---------------
echo [37m#################################[0m
echo [37mWelcome to CBOX v1.0[0m
echo [37mCopyright (c) 1992-2026 by FOXNET[0m
echo [37mhttps://software.foxnet.ir[0m
echo [37m#################################[0m
echo.
echo [32mType "?" for command list.[0m
echo.   

:: -------- Command History Setup -----------
set "history="

:loop
:: Pre-prompt message
echo.
echo [31;44mCBOX> type ? for command list[0m
for /f "delims=" %%d in ('cd') do set "currentDir=%%d"
echo [37;44mCurrent Directory: !currentDir![0m
set /p cmdInput=[31mCBOX ^> [0m


:: Save history
if defined cmdInput (
    set history=!history!^|%cmdInput%
)

:: Exit
if /i "%cmdInput%"=="exit" goto end
if /i "%cmdInput%"=="quit" goto end

:: Help Command
if /i "%cmdInput%"=="?" (
    call :helpScreen
    goto loop
)

:: Execute command
call :executeCommand "%cmdInput%"
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
    echo [33mListing directory:[0m
    dir
    goto :eof
)

echo !cmd! | findstr /b /i "ls " >nul
if !errorlevel!==0 (
    for /f "tokens=2*" %%a in ("!cmd!") do (
        call :showHelp "ls" "List files and folders" "ls [path]"
        echo [33mListing directory: %%a[0m
        dir %%a
    )
    goto :eof
)

:: ---------- PING ----------
echo !cmd! | findstr /b /i "pi " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "p" "Ping a host" "p [host]"
        echo [33mPinging %%a...[0m
        ping %%a
    )
    goto :eof
)


:: ---------- PING WITH COUNT ----------
echo !cmd! | findstr /b /i "pnc " >nul
if !errorlevel!==0 (
    for /f "tokens=2,3" %%a in ("!cmd!") do (
        call :showHelp "pnc" "Ping host with count" "pnc [host] [count]"
        echo [33mPinging %%a %%b times...[0m
        ping -n %%b %%a
    )
    goto :eof
)

:: ---------- TRACERT ----------
echo !cmd! | findstr /b /i "tr " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "tr" "Trace route to a host" "tr [host]"
        echo [33mTracing route to %%a...[0m
        tracert %%a
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
echo !cmd! | findstr /b /i "rm " >nul
if !errorlevel!==0 (
    for /f "tokens=2" %%a in ("!cmd!") do (
        call :showHelp "rm" "Delete file" "rm filename"
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
 
call :showHelp "!cmd!" "THIS IS NOT A CBOX COMMAND " "!cmd!"
echo [33mOutput:[0m
!cmd!
echo.
goto :eof

:: ============================================
:: ========== SHOW MINI-HELP FUNCTION =========
:: ============================================
:showHelp
echo.
echo [32m***************** %~1 Help ******************[0m
echo [36mDescription : %~2[0m
echo [36mCommand     : %~3[0m
echo [32m*********************************************[0m
echo.
exit /b

:: ============================================
:: ========== HELP SCREEN =====================
:: ============================================
:helpScreen
cls
echo.
echo [37m===============CBOX v1.0 HELP ======================[0m
echo.
echo [37mShort commands for common tasks by CMD  [0m
echo [37mCopyright (c) 1992-2026 by FOXNET[0m
echo [37mhttps://software.foxnet.ir[0m
echo [37m====================================================[0m
echo.
echo [32mls[0m            - List files and folders
echo [32mp [host][0m      - Ping host
echo [32mtr [host][0m     - Trace route host
echo [32mcp a b[0m        - Copy file a to b
echo [32mmv a b[0m        - Move or rename file a to b
echo [32mrm file[0m       - Delete file
echo [32mmdx folder[0m    - Create directory
echo [32mip[0m            - Show network info
echo [32mipconfigall[0m   - Show detailed network info
echo [32mps / task[0m     - Show running processes
echo [32mkill [pid][0m    - Kill process by PID
echo [32mendtask[0m       - Kill process by name
echo [32mdf[0m            - Show disk free info
echo [32msys[0m           - Show system info
echo [32msinfo[0m         - Quick system info (OS Name/Version/System Type)
echo [32mwho[0m           - Show current user
echo [32mver[0m           - Show Windows version
echo [32mnetstat[0m       - Show network connections
echo [32marp[0m           - Show ARP cache
echo [32mnslookup[0m      - Query DNS servers
echo [32mcl[0m            - Clear screen
echo [32mexplore[0m       - Built-in file explorer
echo [32m?[0m           - Show this help screen
echo [32mexit[0m          - Quit CBOX
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

