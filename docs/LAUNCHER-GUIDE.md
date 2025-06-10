# AI Game Master - Simple Launcher Guide

This guide covers the simplified launcher system designed to provide an easy one-click setup and launch experience for the AI Game Master application.

## Quick Start

Simply double-click the appropriate launcher for your operating system:

```bash
# Windows
launch.bat

# Linux/macOS
./launch.sh
```

That's it! The launcher will handle everything automatically.

## Launcher Files

| File | Platform | Purpose |
|------|----------|---------|
| `launch.bat` | Windows | One-click launcher with complete setup |
| `launch.sh` | Linux/macOS | One-click launcher with complete setup |

## What the Launcher Does

The launcher automatically handles all setup steps:

1. **[1/5] Checking Python** - Verifies Python 3.8+ is installed
2. **[2/5] Setting up virtual environment** - Creates and activates Python virtual environment
3. **[3/5] Installing Python dependencies** - Installs all required Python packages
4. **[4/5] Setting up frontend** - Installs Node.js dependencies and builds the frontend
5. **[5/5] Starting AI Game Master** - Launches the application and opens your browser

### First Run Setup

On the first run, the launcher will:
- Create a Python virtual environment (`.venv` folder)
- Install all Python dependencies from `requirements.txt`
- Install all Node.js dependencies for the frontend
- Create a `.env` file from `.env.example` if it doesn't exist
- Build the optimized frontend for production
- Start the Flask server on port 5000
- Automatically open http://localhost:5000 in your browser

### Subsequent Runs

On later runs, the launcher will:
- Use the existing virtual environment
- Skip dependency installation if packages are up to date
- Rebuild the frontend
- Start the server and open the browser

## Troubleshooting

### Common Issues

#### "Python is not installed or not in PATH"
**Solution:**
- Install Python 3.8+ from [python.org](https://python.org)
- During installation, make sure to check "Add Python to PATH"
- Restart your terminal/command prompt after installation

#### "Node.js/npm is not installed"
**Solution:**
- Install Node.js from [nodejs.org](https://nodejs.org)
- Download the LTS (Long Term Support) version
- Restart your terminal after installation

#### "Failed to create virtual environment"
**Solution:**
- Make sure you have sufficient disk space (at least 1GB free)
- On Linux/Ubuntu: `sudo apt install python3-venv`
- Try running as administrator/sudo if permissions are an issue

#### "Frontend build failed"
**Solution:**
- Make sure you have a stable internet connection
- Try deleting the `frontend/node_modules` folder and run the launcher again
- Ensure you have sufficient disk space

#### Launcher hangs at "Checking Node.js..."
**Solution:**
This issue has been fixed in the latest version. The launcher now shows progress during npm operations instead of running them silently. If you're still experiencing this:
- Make sure you have the latest launcher files
- Ensure you have a stable internet connection
- Try deleting `frontend/node_modules` and run again

#### Port 5000 is already in use
**Solution:**
- Close any other applications using port 5000
- Look for other Flask applications or web servers running
- Restart your computer if needed

### Getting Detailed Error Information

If you encounter issues:

1. **Windows**: The launcher will pause on errors so you can read the error message
2. **Linux/macOS**: Check the terminal output for specific error details
3. Make sure you're running the launcher from the AI Game Master project root directory (where the `app` folder is located)

## Manual Setup (Advanced Users)

If you prefer to set up manually or the launcher fails:

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows:
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Create environment file
# Windows:
copy .env.example .env
# Linux/macOS:
cp .env.example .env

# 5. Install and build frontend
cd frontend
npm install
npm run build
cd ..

# 6. Start the application
python run.py
```
