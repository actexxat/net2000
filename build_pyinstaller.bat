@echo off
echo Building Internet 2000 with PyInstaller...

python -c "import sys; print(f'Python Version: {sys.version}'); sys.exit(1) if sys.version_info >= (3, 9) else sys.exit(0)"
if %ERRORLEVEL% EQU 1 (
    echo.
    echo WARNING: You are building with Python 3.9 or newer.
    echo This executable will NOT run on standard Windows 7.
    echo To support Windows 7, you must build this project using Python 3.8.
    echo.
    pause
)

pyinstaller --noconfirm --onedir --console --name "Internet2000_Server" ^
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
    run_cafe.py

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Executable is in dist\Internet2000_Server\Internet2000_Server.exe
    echo.
    echo REMINDER: If you built this with Python 3.10+, it will only run on Windows 8.1/10/11.
) else (
    echo Build failed!
)
pause
