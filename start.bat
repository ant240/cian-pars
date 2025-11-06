@echo off
echo ==========================================
echo   Cian Parser - Starting...
echo ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [!] Installing dependencies...
    echo This may take a few minutes...
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies.
        echo Check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed successfully!
    echo.
) else (
    echo [OK] Dependencies already installed
    echo.
)

echo ==========================================
echo   Starting application...
echo ==========================================
echo.
echo Application will open in your browser
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo ==========================================
echo.

python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start application.
    echo.
    pause
    exit /b 1
)
