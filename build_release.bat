@echo off
REM ========================================
REM Internet 2000 - Build and Release Script
REM ========================================
REM This script builds the application and prepares it for GitHub release

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

REM Update version.py
echo Updating version.py...
python -c "import datetime; version_file = open('version.py', 'w'); version_file.write('\"\"\"\\nVersion information for Internet 2000 application.\\nThis file is automatically updated during the build process.\\n\"\"\"\\n\\n__version__ = \"%VERSION%\"\\n__build_date__ = \"' + datetime.datetime.now().strftime('%%Y-%%m-%%d') + '\"\\n__github_repo__ = \"YOUR_USERNAME/net2000\"  # Update this with your actual GitHub repo\\n\\ndef get_version():\\n    \"\"\"Returns the current version string.\"\"\"\\n    return __version__\\n\\ndef get_build_date():\\n    \"\"\"Returns the build date.\"\"\"\\n    return __build_date__\\n\\ndef get_version_info():\\n    \"\"\"Returns a dictionary with all version information.\"\"\"\\n    return {\\n        \'version\': __version__,\\n        \'build_date\': __build_date__,\\n        \'github_repo\': __github_repo__,\\n    }\\n'); version_file.close()"

REM Check Python version
python -c "import sys; print(f'Python Version: {sys.version}'); sys.exit(1) if sys.version_info >= (3, 9) else sys.exit(0)"
if %ERRORLEVEL% EQU 1 (
    echo.
    echo WARNING: You are building with Python 3.9 or newer.
    echo This executable will NOT run on standard Windows 7.
    echo To support Windows 7, you must build this project using Python 3.8.
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
)

echo.
echo Building executable with PyInstaller...
echo.

pyinstaller --noconfirm --onedir --console --name "Internet2000_Server" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "locale;locale" ^
    --add-data "manager/templates;manager/templates" ^
    --add-data "version.py;." ^
    --add-data "updater.py;." ^
    --hidden-import "waitress" ^
    --hidden-import "whitenoise" ^
    --hidden-import "whitenoise.middleware" ^
    --hidden-import "django.core.management" ^
    --hidden-import "django.db.backends.sqlite3" ^
    --collect-all "manager" ^
    --collect-all "core" ^
    --collect-all "whitenoise" ^
    run_cafe.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful!
echo.

REM Create release package
echo Creating release package...
set RELEASE_NAME=Internet2000_v%VERSION%
set RELEASE_DIR=releases\%RELEASE_NAME%

if exist "releases\%RELEASE_NAME%.zip" del "releases\%RELEASE_NAME%.zip"
if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"

mkdir "%RELEASE_DIR%" 2>nul

REM Copy built files
echo Copying files...
xcopy "dist\Internet2000_Server\*.*" "%RELEASE_DIR%\" /E /I /Y >nul

REM Create README for release
echo Creating release README...
(
echo Internet 2000 - Version %VERSION%
echo =====================================
echo.
echo Installation:
echo 1. Extract this ZIP file to a folder
echo 2. Run Internet2000_Server.exe
echo 3. The application will open in your default browser
echo.
echo System Requirements:
echo - Windows 7 or later
echo - No additional software required
echo.
echo For support, visit: https://github.com/YOUR_USERNAME/net2000
) > "%RELEASE_DIR%\README.txt"

REM Create ZIP file
echo Creating ZIP archive...
powershell -command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath 'releases\%RELEASE_NAME%.zip' -Force"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Release package created successfully!
    echo ========================================
    echo.
    echo Package: releases\%RELEASE_NAME%.zip
    echo.
    echo Next steps:
    echo 1. Test the release package
    echo 2. Create a git tag: git tag v%VERSION%
    echo 3. Push the tag: git push origin v%VERSION%
    echo 4. Create a GitHub release and upload: releases\%RELEASE_NAME%.zip
    echo.
    echo GitHub Release Instructions:
    echo 1. Go to: https://github.com/YOUR_USERNAME/net2000/releases/new
    echo 2. Tag version: v%VERSION%
    echo 3. Release title: Internet 2000 v%VERSION%
    echo 4. Upload: releases\%RELEASE_NAME%.zip
    echo 5. Publish release
    echo.
) else (
    echo Failed to create ZIP archive!
)

pause
