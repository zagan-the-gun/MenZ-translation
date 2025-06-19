@echo off
chcp 65001 > nul
echo.
echo ======================================================
echo     MenZ翻訳サーバー - GPU対応インストール
echo ======================================================
echo.

:: 仮想環境の確認
if not exist venv (
    echo [ERROR] 仮想環境が見つかりません。
    echo         setup.bat を先に実行してください。
    pause
    exit /b 1
)

echo [WARNING] NVIDIA GPU対応のPyTorchをインストールします。
echo           NVIDIA GPU搭載PCでのみ使用してください。
echo.
echo 続行しますか？ (y/N)
set /p confirm=
if /i not "%confirm%"=="y" (
    echo [INFO] インストールをキャンセルしました。
    pause
    exit /b 0
)

echo.
echo [INFO] 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

echo.
echo [INFO] 既存のPyTorchをアンインストール中...
pip uninstall torch torchvision torchaudio -y

echo.
echo [INFO] CUDA対応PyTorchをインストール中...
echo [INFO] これには数分かかる場合があります...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

if %errorlevel% neq 0 (
    echo [ERROR] GPU対応PyTorchのインストールに失敗しました。
    echo         CPU版に戻します...
    pip install torch torchvision torchaudio
    pause
    exit /b 1
)

echo.
echo [INFO] 設定ファイルをGPU用に更新中...
if exist config\translator.ini (
    powershell -Command "(Get-Content config\translator.ini) -replace 'device = cpu', 'device = cuda' | Set-Content config\translator.ini"
    echo [SUCCESS] 設定を 'device = cuda' に変更しました。
) else (
    echo [WARNING] 設定ファイルが見つかりません。手動で device = cuda に設定してください。
)

echo.
echo ======================================================
echo GPU対応のインストールが完了しました！
echo ======================================================
echo.
echo 次回サーバー起動時からGPUが使用されます。
echo GPUメモリ不足エラーが発生する場合は、
echo config\translator.ini で device = cpu に戻してください。
echo.
pause 