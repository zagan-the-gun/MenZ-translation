@echo off
echo.
echo ======================================================
echo    MenZ Translation Server - GPU Status Check
echo ======================================================
echo.

:: Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking GPU status...
echo.
python check_gpu.py

echo.
pause 