#!/bin/bash

clear

echo "=========================================="
echo "    AI Game Master - Simple Launcher"
echo "=========================================="
echo

# Check if we're in the right directory
if [ ! -d "app" ]; then
    echo "ERROR: Please run this script from the AI Game Master root directory."
    echo "Expected to find 'app' directory in current location."
    read -p "Press Enter to continue..."
    exit 1
fi

echo "[1/5] Checking Python..."

# Prefer python3 if available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from python.org"
    read -p "Press Enter to continue..."
    exit 1
fi

echo "Python found: $($PYTHON_CMD --version)"

echo
echo "[2/5] Setting up virtual environment..."

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press Enter to continue..."
        exit 1
    fi
fi

echo "Activating virtual environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    read -p "Press Enter to continue..."
    exit 1
fi

echo
echo "[3/5] Installing Python dependencies..."
echo "Upgrading pip..."
python -m pip install --upgrade pip > /dev/null 2>&1
echo "Installing packages from requirements.txt - this may take a few minutes..."
python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python dependencies"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "Python dependencies installed."

echo
echo "[4/5] Setting up frontend..."

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
fi

echo "Checking Node.js..."
if ! command -v npm &> /dev/null; then
    echo "ERROR: Node.js/npm is not installed"
    echo "Please install Node.js from nodejs.org"
    read -p "Press Enter to continue..."
    exit 1
fi
echo "Node.js found."

cd frontend
echo "Installing frontend dependencies - this may take a few minutes..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install frontend dependencies"
    cd ..
    read -p "Press Enter to continue..."
    exit 1
fi

echo "Building frontend for production..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed"
    cd ..
    read -p "Press Enter to continue..."
    exit 1
fi
cd ..
echo "Frontend setup complete."

echo
echo "[5/5] Starting AI Game Master..."
echo
echo "Starting Flask server..."
echo "Press Ctrl+C to stop the server."
echo

# Start the Flask application in background
python run.py &
FLASK_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 3

# Test if server is responding (using 127.0.0.1 to match Flask's actual bind address)
for i in {1..5}; do
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        echo "Server is ready!"
        echo "Opening browser at: http://localhost:5000"
        
        # Open browser
        if command -v open &> /dev/null; then
            # macOS
            open "http://localhost:5000"
        elif command -v xdg-open &> /dev/null; then
            # Linux
            xdg-open "http://localhost:5000"
        fi
        break
    fi
    
    echo "Waiting for server... (attempt $i/5)"
    sleep 1
done

# If we get here and server still not responding, open browser anyway
if ! curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
    echo "WARNING: Server may not have started properly, but opening browser anyway..."
    if command -v open &> /dev/null; then
        open "http://localhost:5000"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:5000"
    fi
fi

echo
echo "AI Game Master is now running!"
echo "You can close this window when you're done using the application."
echo

# Wait for Flask process to finish
wait $FLASK_PID

echo
echo "Thanks for using AI Game Master!"
