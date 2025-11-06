@echo off
chcp 65001 >nul
echo ==========================================
echo   Установка зависимостей
echo ==========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python найден
python --version
echo.

echo Обновление pip...
python -m pip install --upgrade pip
echo.

echo Установка зависимостей...
echo.
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Установка не удалась.
    echo.
) else (
    echo.
    echo [✓] Все зависимости успешно установлены!
    echo.
    echo Теперь запустите приложение файлом start.bat
    echo или командой: python -m streamlit run app.py
    echo.
)

pause
