@echo off
TITLE Cafe Management System [DEVELOPMENT MODE]
cd /d %~dp0

:: Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv folder.
    exit /b
)

echo [STATUS] Starting Development Server with Auto-Reload...
echo [INFO] Changes to code will be reflected live.
echo [INFO] Opening browser to http://127.0.0.1:8000...

:: Start the browser in a separate process
start "" "http://127.0.0.1:8000"

:: Run the Django development server
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
pause
