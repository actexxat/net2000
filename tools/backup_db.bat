@echo off
TITLE Internet 2000 - Database Backup
cd /d "%~dp0\.."

:: Create backups directory if it doesn't exist
if not exist "backups" mkdir backups

:: Get current date and time for filename
set datestr=%date:~10,4%%date:~4,2%%date:~7,2%
set timestr=%time:~0,2%%time:~3,2%
set timestr=%timestr: =0%

set filename=backups\db_backup_%datestr%_%timestr%.sqlite3

echo [ACTION] Backing up database to %filename%...
copy db.sqlite3 %filename% /y

if %ERRORLEVEL% == 0 (
    echo [SUCCESS] Backup complete.
) else (
    echo [ERROR] Backup failed.
)
timeout /t 3
