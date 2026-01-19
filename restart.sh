#!/bin/bash

# Cafe Management System Restart Script
# Restarts the server regardless of current state.

echo "--------------------------------------------------"
echo "Internet 2000 - Cafe Server Manager"
echo "--------------------------------------------------"

# Find the process running run_cafe.py
PID=$(pgrep -f "run_cafe.py")

if [ -n "$PID" ]; then
    echo "[STATUS] Cafe Server is running (PID: $PID)."
    echo "[ACTION] Restarting service..."
    pkill -f "run_cafe.py"
    sleep 2
else
    echo "[STATUS] Server is not running."
    echo "[ACTION] Starting Cafe Service..."
fi

# Check for virtual environment
if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    echo "[WARNING] Virtual environment not found. Using system python."
    PYTHON="python"
fi

echo "[INFO] Launching server..."
$PYTHON run_cafe.py
