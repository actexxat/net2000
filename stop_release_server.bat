@echo off
TITLE Stop Internet2000 Release Server
echo Attempting to stop Internet2000 Release Server and related processes...

:: Attempt to kill by command line (most robust for PyInstaller)
wmic process where "commandline like '%%Internet2000_Server.exe%%'" delete > nul 2>&1
wmic process where "commandline like '%%D:\\net2000\\releases%%'" delete > nul 2>&1

:: Attempt to kill by image name (fallback for direct exe)
taskkill /IM Internet2000_Server.exe /F > nul 2>&1
taskkill /IM python.exe /F > nul 2>&1

:: Attempt to kill any lingering python processes associated with the project, with caution
wmic process where "commandline like '%%run_cafe.py%%'" delete > nul 2>&1


echo Internet2000 Release Server and related processes termination attempts complete.
echo If you still cannot delete the folder, a system reboot might be necessary.
pause