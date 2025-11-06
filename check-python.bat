@echo off
echo ==========================================
echo   Checking Python Installation
echo ==========================================
echo.

python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python is NOT installed or NOT in PATH!
    echo.
    echo You need to install Python first:
    echo 1. Download from: https://www.python.org/downloads/
    echo 2. Run installer
    echo 3. CHECK the box "Add Python to PATH"
    echo 4. Complete installation
    echo 5. Restart your computer
    echo 6. Run this check again
    echo.
) else (
    echo.
    echo [OK] Python is installed correctly!
    echo.
    echo Location:
    where python
    echo.
    echo pip version:
    python -m pip --version
    echo.
    echo You can now run: start.bat
    echo.
)

pause
