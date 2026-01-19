@echo off
TITLE Stop Cafe Server
echo Stopping Cafe Server background processes...

:: Find and kill the process running run_cafe.py
wmic process where "commandline like '%%run_cafe.py%%'" delete

echo Server stopped.
pause
