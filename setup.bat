@echo off
echo.
echo ======================================================
echo     MenZ Translation Server - Windows Setup
echo ======================================================
echo.

:: Check admin privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with administrator privileges
) else (
    echo [WARNING] Administrator privileges recommended
    echo           ^(for firewall configuration^)
)

echo.
echo [1/6] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    echo         Please install Python 3.8+ and add to PATH.
    echo         https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

echo.
echo [2/6] Creating virtual environment...
if exist venv (
    echo [INFO] Existing virtual environment found. Recreate? ^(y/N^)
    set /p recreate=
    if /i "!recreate!"=="y" (
        echo [INFO] Removing existing virtual environment...
        rmdir /s /q venv
    )
)

if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
)

echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo.
echo [4/6] Installing dependencies...
echo [INFO] This may take several minutes...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    echo [HINT] Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo [5/6] Creating necessary directories...
if not exist config mkdir config
if not exist logs mkdir logs

echo.
echo [6/6] Creating configuration file...
if not exist config\translator.ini (
    echo [INFO] Creating default configuration file...
    copy /y config_windows_sample.ini config\translator.ini > nul
    if %errorlevel% neq 0 (
        echo [INFO] Sample config not found, creating basic config...
        (
            echo [SERVER]
            echo host = 127.0.0.1
            echo port = 55001
            echo max_connections = 10
            echo.
            echo [TRANSLATION]
            echo model_name = facebook/nllb-200-distilled-1.3B
            echo device = cpu
            echo max_length = 128
            echo.
            echo [LOGGING]
            echo level = INFO
            echo file = logs/translator.log
            echo max_file_size = 10485760
            echo backup_count = 3
        ) > config\translator.ini
    )
    echo [SUCCESS] Configuration file created: config\translator.ini
) else (
    echo [INFO] Using existing configuration: config\translator.ini
)

echo.
echo ======================================================
echo Setup completed successfully!
echo ======================================================
echo.
echo Next steps:
echo   1. Edit config\translator.ini if needed
echo      - NVIDIA GPU PC: device = cuda
echo      - CPU only: device = cpu
echo.
echo   2. Start server: Double-click run.bat
echo.
echo Note: Allow access if Windows Firewall asks for permission
echo.
pause 