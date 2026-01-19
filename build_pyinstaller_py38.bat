@echo off
setlocal enabledelayedexpansion
echo ==================================================
echo Building Internet 2000 with PyInstaller (Python 3.8 / Win7)
echo ==================================================

:: 1. Cleanup old builds
echo [1/4] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 2. Run PyInstaller
echo [2/4] Running PyInstaller...
d:\net2000\py38_env\python.exe -m PyInstaller --noconfirm --onedir --console --name "Internet2000_Server_Win7" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "locale;locale" ^
    --add-data "manager/templates;manager/templates" ^
    --hidden-import "waitress" ^
    --hidden-import "whitenoise" ^
    --hidden-import "whitenoise.middleware" ^
    --hidden-import "django.core.management" ^
    --hidden-import "django.db.backends.sqlite3" ^
    --collect-all "manager" ^
    --collect-all "core" ^
    --collect-all "whitenoise" ^
    --collect-all "setuptools" ^
    --collect-all "jaraco.text" ^
    --copy-metadata "setuptools" ^
    run_cafe.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed during PyInstaller execution.
    pause
    exit /b %ERRORLEVEL%
)

:: 3. Copy Data Files
echo [3/4] Copying data files (Database and Media)...
set DIST_DIR=dist\Internet2000_Server_Win7

if exist db.sqlite3 (
    copy db.sqlite3 "%DIST_DIR%\"
    echo   - db.sqlite3 copied.
)

if exist media (
    xcopy /e /i /y media "%DIST_DIR%\media"
    echo   - media folder copied.
)

:: 4. Create specialized Dist-scripts (Launching the EXE)
echo [4/5] Creating service scripts for production...

(
echo @echo off
echo cd /d %%~dp0
echo TITLE Internet 2000 - Cafe Server Manager
echo echo [ACTION] Checking for existing instances...
echo taskkill /F /IM Internet2000_Server_Win7.exe /T 2^>nul
echo timeout /t 2 /nobreak ^>nul
echo echo [ACTION] Starting Server...
echo start "" "Internet2000_Server_Win7.exe"
) > "%DIST_DIR%\START_SERVER.bat"

(
echo @echo off
echo TITLE Internet 2000 - Database Backup
echo if not exist "backups" mkdir backups
echo set datestr=%%date:~10,4%%%%date:~4,2%%%%date:~7,2%%
echo set timestr=%%time:~0,2%%%%time:~3,2%%
echo set timestr=%%timestr: =0%%
echo echo [ACTION] Backing up to backups\db_backup_%%datestr%%_%%timestr%%.sqlite3...
echo copy db.sqlite3 backups\db_backup_%%datestr%%_%%timestr%%.sqlite3 /y
echo timeout /t 3
) > "%DIST_DIR%\BACKUP_DATABASE.bat"

if exist manual.md (
    copy manual.md "%DIST_DIR%\"
    echo   - manual.md copied.
)

:: 5. Finalizing
echo [5/5] Finishing up...
echo ==================================================
echo BUILD COMPLETE!
echo --------------------------------------------------
echo The production folder is located at:
echo %cd%\dist\Internet2000_Server_Win7
echo --------------------------------------------------
echo Ready for Windows 7 deployment.
echo ==================================================
pause
