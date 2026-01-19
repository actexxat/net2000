@echo off
echo Building Internet 2000 Executable (Standalone Server) - Manual Includes...
python -m nuitka --standalone ^
    --include-package=core ^
    --include-package=manager ^
    --include-package=django ^
    --include-package=waitress ^
    --include-data-dir=manager/templates=manager/templates ^
    --include-data-dir=templates=templates ^
    --include-data-dir=static=static ^
    --include-data-dir=locale=locale ^
    --output-filename=Internet2000_Server ^
    run_cafe.py

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Executable is in run_cafe.dist\Internet2000_Server.exe
) else (
    echo Build failed!
)
pause
