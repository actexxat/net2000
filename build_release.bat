@echo off
REM ========================================
REM Internet 2000 - Build and Release Script
REM ========================================
REM This script builds the application for Windows 10+ Production Environment

echo.
echo ========================================
echo Internet 2000 Build and Release
echo ========================================
echo.

REM Get version from user
set /p VERSION="Enter version number (e.g., 1.0.1): "
if "%VERSION%"=="" (
    echo Error: Version number is required!
    pause
    exit /b 1
)

REM Safe Version Update
echo Updating version.py...
python scripts\update_version.py "%VERSION%"
if %ERRORLEVEL% NEQ 0 (
    echo Error updating version file!
    pause
    exit /b 1
)

REM Collect Static Files
echo Collecting static files...
python manage.py collectstatic --no-input

echo.
echo Building executable with PyInstaller...
echo.

REM Clean previous build
echo Clearing previous build directories...
if exist "dist\Internet2000_Server" rmdir /s /q "dist\Internet2000_Server"
if exist "dist\Internet2000_win10" rmdir /s /q "dist\Internet2000_win10"
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
timeout /t 2 /nobreak >nul
echo.
echo IMPORTANT: If the build fails with 'PermissionError', please ensure no programs (like Explorer or a previous instance of the app) are accessing the 'dist' folder.
pause

pyinstaller --noconfirm "Internet2000_win10.spec"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful!
echo.

REM Post-Build Setup
echo Setting up production environment...
set TARGET_DIR=dist\Internet2000_win10

REM 1. Copy Database (Safe Update Strategy)
if exist "db.sqlite3" (
    echo Copying database safely...
    copy "db.sqlite3" "%TARGET_DIR%\db.sqlite3" >nul
    python scripts\clean_db.py "%TARGET_DIR%\db.sqlite3"
) else (
    echo WARNING: db.sqlite3 not found! No initial database will be included.
)

REM 2. Setup Media Directory
if not exist "%TARGET_DIR%\media" mkdir "%TARGET_DIR%\media"
if exist "media" (
    echo Copying media files...
    xcopy "media\*.*" "%TARGET_DIR%\media\" /E /I /Y >nul
)

REM Create release package
echo Creating release package...
set RELEASE_NAME=Internet2000_v%VERSION%
set RELEASE_DIR=releases\%RELEASE_NAME%

if exist "releases\%RELEASE_NAME%.zip" del "releases\%RELEASE_NAME%.zip"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"

mkdir "%RELEASE_DIR%" 2>nul

REM Copy built files
echo Copying files to release folder...
xcopy "%TARGET_DIR%\*.*" "%RELEASE_DIR%\" /E /I /Y >nul



REM Create README for release
echo Creating release README...
(
echo Internet 2000 - Version %VERSION%
echo =====================================
echo.
echo Installation:
echo 1. Extract this ZIP file to a folder
echo 2. Run Internet2000_win10.exe
echo 3. The application will open in your default browser
echo.
echo System Requirements:
echo - Windows 10 or later
echo - No additional software required
echo.
echo For support, visit: https://github.com/actexxat/net2000
) > "%RELEASE_DIR%\README.txt"

REM Create ZIP file
echo Skipping ZIP archive creation for testing...
REM powershell -command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath 'releases\%RELEASE_NAME%.zip' -Force"

echo.
echo ========================================
echo Release directory created successfully!
echo ========================================
echo.
echo Test Directory: releases\%RELEASE_NAME%
echo.
echo Next steps:
echo 1. Test the Executable in the directory above.
echo 2. Once verified, manually ZIP the folder.
echo 3. Create a git tag: git tag v%VERSION%
echo 4. Push the tag: git push origin v%VERSION%
echo 5. Create a GitHub release and upload the ZIP.
echo.
echo GitHub Release Instructions:
echo 1. Go to: https://github.com/actexxat/net2000/releases/new
echo 2. Tag version: v%VERSION%
echo 3. Release title: Internet 2000 v%VERSION%
echo 4. Upload your manually created ZIP file.
echo 5. Publish release
echo.

pause
