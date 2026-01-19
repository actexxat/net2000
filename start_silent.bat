@echo off
cd /d %~dp0

:: Kill any existing server process
wmic process where "commandline like '%%run_cafe.py%%'" delete > nul 2>&1
timeout /t 2 /nobreak > nul

:: Run the server without pause
".venv\Scripts\python.exe" run_cafe.py
