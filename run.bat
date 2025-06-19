@echo off
echo.
echo ======================================================
echo      MenZ Translation Server - Starting...
echo ======================================================
echo.

:: Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

:: Check configuration file
if not exist config\translator.ini (
    echo [ERROR] Configuration file not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking dependencies...
pip show torch >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Required libraries not installed.
    echo         Please run setup.bat.
    pause
    exit /b 1
)

echo [INFO] Starting server...
echo.
echo ======================================================
echo   Port: 55001
echo   URL: ws://127.0.0.1:55001
echo   Stop: Ctrl + C
echo ======================================================
echo.

:: Start server
python main.py

:: Handle abnormal exit
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited abnormally.
    echo         Check error log: logs\translator.log
    echo.
    pause
)

echo.
echo [INFO] Server stopped.
pause 