@echo off
echo.
echo ======================================================
echo      MenZ Translation Server - Windows Debug Mode
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

echo [INFO] System Information...
echo   Windows Version: 
for /f "tokens=2 delims=:" %%i in ('systeminfo ^| findstr /c:"OS Name"') do echo   %%i
echo   Python Version:
python --version

echo.
echo [INFO] Checking Python libraries...
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import websockets; print(f'WebSockets: {websockets.__version__}')"

echo.
echo [INFO] CUDA Information...
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

echo.
echo [INFO] Network Test...
netstat -an | findstr :55001
if %errorlevel% equ 0 (
    echo [WARNING] Port 55001 is already in use!
    echo           Please stop other services using this port.
) else (
    echo [OK] Port 55001 is available.
)

echo.
echo [INFO] Starting server with detailed logging...
echo       Check logs\translator.log for detailed error information.
echo.
echo ======================================================
echo   Port: 55001
echo   URL: ws://127.0.0.1:55001
echo   Stop: Ctrl + C
echo ======================================================
echo.

:: Start server with detailed error handling
python main.py
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% neq 0 (
    echo [ERROR] Server exited with code: %EXIT_CODE%
    echo.
    echo [INFO] Showing last 20 lines of log file:
    if exist logs\translator.log (
        echo ----------------------------------------
        powershell "Get-Content logs\translator.log | Select-Object -Last 20"
        echo ----------------------------------------
    ) else (
        echo [WARNING] Log file not found.
    )
    echo.
    echo [HELP] Troubleshooting steps:
    echo   1. Check if port 55001 is available
    echo   2. Verify CUDA drivers if using GPU
    echo   3. Try setting device = cpu in config\translator.ini
    echo   4. Check Windows Firewall settings
    echo.
) else (
    echo [INFO] Server stopped normally.
)

pause 