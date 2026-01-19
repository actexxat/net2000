@echo off
TITLE Cafe Management System Server
cd /d %~dp0

:: Check if server is already running
wmic process where "commandline like '%%run_cafe.py%%'" get processid /format:list | find "ProcessId" > nul
if %ERRORLEVEL% == 0 (
    echo [STATUS] Cafe Server is already running.
    echo [ACTION] Restarting service...
    wmic process where "commandline like '%%run_cafe.py%%'" delete > nul 2>&1
    timeout /t 2 /nobreak > nul
) else (
    echo [STATUS] Server is not running.
    echo [ACTION] Starting Cafe Service...
)

:: Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv folder.
    exit /b
)

echo Activating environment and starting server...
".venv\Scripts\python.exe" run_cafe.py
pause
