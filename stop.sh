#!/bin/bash

# Cafe Management System Stop Script

echo "--------------------------------------------------"
echo "Internet 2000 - Cafe Server Manager"
echo "--------------------------------------------------"

# Find the process running run_cafe.py
PID=$(pgrep -f "run_cafe.py")

if [ -n "$PID" ]; then
    echo "[STATUS] Cafe Server is running (PID: $PID)."
    echo "[ACTION] Stopping service..."
    pkill -f "run_cafe.py"
    echo "[STATUS] Server stopped."
else
    echo "[STATUS] Server is not running."
fi
