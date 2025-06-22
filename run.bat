@echo off
echo.
echo ======================================================
echo      MenZ Translation Server - Starting...
echo ======================================================
echo.

REM 文字コードをUTF-8に設定（日本語対応）
chcp 65001 > nul

REM Check for both possible venv directories
set VENV_DIR=
if exist venv\Scripts\activate.bat (
    set VENV_DIR=venv
) else if exist venv3.12\Scripts\activate.bat (
    set VENV_DIR=venv3.12
)

if "%VENV_DIR%"=="" (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    echo         Looking for: venv\Scripts\activate.bat or venv3.12\Scripts\activate.bat
    pause
    exit /b 1
)

REM Check configuration file
if not exist config\translator.ini (
    echo [ERROR] Configuration file not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment (%VENV_DIR%)...
call %VENV_DIR%\Scripts\activate.bat

echo [INFO] Checking dependencies...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in virtual environment.
    echo         Please run setup.bat.
    pause
    exit /b 1
)

pip show torch >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Required libraries not installed.
    echo         Please run setup.bat.
    pause
    exit /b 1
)

echo [INFO] Starting server with improved Ctrl+C handling...
echo.
echo ======================================================
echo   Port: 55001
echo   URL: ws://127.0.0.1:55001
echo   Stop: Ctrl + C (improved handling)
echo ======================================================
echo.

REM Start server with unbuffered output for better Ctrl+C handling
python -u main.py
set EXIT_CODE=%ERRORLEVEL%

REM Handle exit conditions
echo.
echo ======================================================
if %EXIT_CODE% == 0 (
    echo [INFO] Server stopped normally.
) else (
    echo [ERROR] Server exited abnormally (Exit code: %EXIT_CODE%).
    echo         Check error log: logs\translator.log
)
echo ======================================================

REM Deactivate virtual environment
deactivate

echo.
echo Press any key to close...
pause > nul
exit /b %EXIT_CODE% 