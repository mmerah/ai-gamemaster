@echo off
echo ==========================================
echo       AI Game Master - Server Killer
echo ==========================================
echo.

echo Searching for AI Game Master server processes...
echo.

:: Method 1: Try to kill by command line filter
echo [Method 1] Attempting to kill by command line pattern...
taskkill /F /IM python.exe /FI "COMMANDLINE eq *run.py*" 2>nul
if not errorlevel 1 (
    echo Found and stopped processes using command line filter.
    goto :success
)

:: Method 2: Try to kill all python.exe processes (more aggressive)
echo [Method 2] Checking for python.exe processes...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if not errorlevel 1 (
    echo Found python.exe processes. Attempting to stop them...
    taskkill /F /IM python.exe 2>nul
    if not errorlevel 1 (
        echo Python processes stopped.
        goto :success
    )
)

:: Method 3: Use PowerShell to find processes by port
echo [Method 3] Checking for processes using port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000"') do (
    if not "%%a"=="0" (
        echo Found process using port 5000: PID %%a
        taskkill /F /PID %%a 2>nul
        if not errorlevel 1 (
            echo Process %%a stopped.
            goto :success
        )
    )
)

:: Method 4: Manual process listing
echo [Method 4] Listing all current python.exe processes for manual review...
echo.
tasklist /FI "IMAGENAME eq python.exe" 2>nul
echo.
echo If you see Python processes above, you can manually kill them using:
echo taskkill /F /PID [process_id]
echo.
goto :not_found

:success
echo.
echo ==========================================
echo  AI Game Master server stopped successfully!
echo ==========================================
echo.
goto :end

:not_found
echo.
echo ==========================================
echo  No AI Game Master server processes found.
echo  The server may already be stopped.
echo ==========================================
echo.

:end
pause
