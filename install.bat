@echo off
echo ==========================================
echo   Installing Dependencies
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Installing dependencies...
echo.
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed.
    echo.
) else (
    echo.
    echo [OK] All dependencies installed successfully!
    echo.
    echo Now run the application using start.bat
    echo or command: python -m streamlit run app.py
    echo.
)

pause
