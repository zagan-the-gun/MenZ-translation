@echo off
echo.
echo ======================================================
echo   MenZ Translation Server - Cache Clear Tool
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

echo [INFO] Activating virtual environment (%VENV_DIR%)...
call %VENV_DIR%\Scripts\activate.bat

echo [INFO] Checking Python installation...
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in virtual environment.
    echo         Please run setup.bat.
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version

echo.
echo ======================================================
echo   Hugging Face Cache Clear - Starting...
echo ======================================================
echo.
echo [WARNING] This will delete all cached translation models
echo           and require re-downloading (2-5GB) on next use.
echo.

python clear_model_cache_windows.py
set EXIT_CODE=%ERRORLEVEL%

REM Handle exit conditions
echo.
echo ======================================================
if %EXIT_CODE% == 0 (
    echo [SUCCESS] Cache clear completed successfully.
) else (
    echo [ERROR] Cache clear failed (Exit code: %EXIT_CODE%).
)
echo ======================================================

REM Deactivate virtual environment
deactivate

echo.
echo Press any key to close...
pause > nul
exit /b %EXIT_CODE% 