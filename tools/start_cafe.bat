@echo off
TITLE Cafe Management System Server
cd /d "%~dp0\.."

:: Check if server is already running
wmic process where "commandline like '%%run_cafe.py%%'" get processid /format:list | find "ProcessId" > nul
if %ERRORLEVEL% == 0 (
    echo [STATUS] Cafe Server is already running.
    echo [ACTION] Restarting service...
    :: Kill the existing server process
    wmic process where "commandline like '%%run_cafe.py%%'" delete > nul 2>&1
    :: Wait a moment for the port to be released
    timeout /t 2 /nobreak > nul
) else (
    echo [STATUS] Server is not running.
    echo [ACTION] Starting Cafe Service...
)

:: Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv folder.
    echo Please make sure you are in the correct directory.
    pause
    exit /b
)

echo Activating environment and starting server...
echo Access the app from other devices using this PC's IP address.
echo Press Ctrl+C to stop the server.

:: Run the server using the python executable in the venv
".venv\Scripts\python.exe" run_cafe.py

pause

