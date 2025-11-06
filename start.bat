@echo off
chcp 65001 >nul
echo ==========================================
echo   Парсер квартир Циан - Запуск
echo ==========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Пожалуйста, установите Python 3.8 или выше:
    echo https://www.python.org/downloads/
    echo.
    echo При установке обязательно поставьте галочку "Add Python to PATH"!
    echo.
    pause
    exit /b 1
)

echo [✓] Python найден
python --version
echo.

REM Проверка наличия зависимостей
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [!] Зависимости не установлены. Начинаем установку...
    echo.
    echo Это может занять несколько минут...
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ОШИБКА] Не удалось установить зависимости.
        echo Проверьте подключение к интернету и попробуйте снова.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [✓] Зависимости успешно установлены!
    echo.
) else (
    echo [✓] Зависимости уже установлены
    echo.
)

echo ==========================================
echo   Запуск приложения...
echo ==========================================
echo.
echo Приложение откроется в браузере автоматически
echo Адрес: http://localhost:8501
echo.
echo Для остановки нажмите Ctrl+C
echo ==========================================
echo.

REM Запуск приложения
python -m streamlit run app.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Не удалось запустить приложение.
    echo.
    pause
    exit /b 1
)
