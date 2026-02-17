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

pyinstaller --noconfirm --clean "Internet2000_win10.spec"

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Executable is in dist\Internet2000_win10\Internet2000_win10.exe
    echo.
    echo REMINDER: If you built this with Python 3.10+, it will only run on Windows 8.1/10/11.
) else (
    echo Build failed!
)
pause
