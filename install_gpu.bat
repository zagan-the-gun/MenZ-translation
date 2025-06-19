@echo off
echo.
echo ======================================================
echo     MenZ Translation Server - GPU Support Install
echo ======================================================
echo.

:: Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found.
    echo         Please run setup.bat first.
    pause
    exit /b 1
)

echo [WARNING] Installing NVIDIA GPU-enabled PyTorch.
echo           Only use on PCs with NVIDIA GPU.
echo.
echo Continue? ^(y/N^)
set /p confirm=
if /i not "%confirm%"=="y" (
    echo [INFO] Installation cancelled.
    pause
    exit /b 0
)

echo.
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [INFO] Uninstalling existing PyTorch...
pip uninstall torch torchvision torchaudio -y

echo.
echo [INFO] Installing CUDA-enabled PyTorch...
echo [INFO] This may take several minutes...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install GPU-enabled PyTorch.
    echo         Reverting to CPU version...
    pip install torch torchvision torchaudio
    pause
    exit /b 1
)

echo.
echo [INFO] Updating configuration for GPU use...
if exist config\translator.ini (
    powershell -Command "(Get-Content config\translator.ini) -replace 'device = cpu', 'device = cuda' | Set-Content config\translator.ini"
    echo [SUCCESS] Changed setting to 'device = cuda'.
) else (
    echo [WARNING] Configuration file not found. Please set device = cuda manually.
)

echo.
echo ======================================================
echo GPU support installation completed!
echo ======================================================
echo.
echo GPU will be used from next server startup.
echo If GPU memory errors occur, change device = cpu
echo in config\translator.ini.
echo.
pause 