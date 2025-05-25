@echo off
cls

echo ==========================================
echo      AI Game Master - Simple Launcher
echo ==========================================
echo.

:: Check if we're in the right directory
if not exist "app" (
    echo ERROR: Please run this script from the AI Game Master root directory.
    echo Expected to find 'app' directory in current location.
    pause
    exit /b 1
)

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
echo Python found.

echo.
echo [2/5] Setting up virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [3/5] Installing Python dependencies...
echo Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
echo Installing packages from requirements.txt - this may take a few minutes...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)
echo Python dependencies installed.

echo.
echo [4/5] Setting up frontend...
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env from template...
        copy ".env.example" ".env" >nul
    )
)

echo Checking Node.js...
call npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js/npm is not installed
    echo Please install Node.js from nodejs.org
    pause
    exit /b 1
)
echo Node.js found.

cd frontend
echo Installing frontend dependencies - this may take a few minutes...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    cd ..
    pause
    exit /b 1
)

echo Building frontend for production...
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend setup complete.

echo.
echo [5/5] Starting AI Game Master...
echo.
echo ==========================================
echo  AI Game Master Server
echo  
echo  Starting Flask server...
echo  Browser will open automatically in a few seconds
echo  
echo  Press Ctrl+C to stop the server
echo ==========================================
echo.

:: Open browser in background after a delay
start /B powershell -Command "Start-Sleep -Seconds 5; Start-Process 'http://localhost:5000'"

:: Run Flask server directly in foreground so Ctrl+C works
.venv\Scripts\python.exe run.py

:: This will only be reached when the server is stopped
echo.
echo Server stopped.
echo Thanks for using AI Game Master!
pause
