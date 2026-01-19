@echo off
TITLE Internet 2000 - Cafe Server (Win7 Dev Mode)
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
)

:: Check if py38_env exists
if not exist "py38_env\python.exe" (
    echo [ERROR] Python 3.8 environment not found in py38_env folder.
    pause
    exit /b
)

echo [ACTION] Starting Cafe service using Python 3.8 environment...
"py38_env\python.exe" run_cafe.py
pause
