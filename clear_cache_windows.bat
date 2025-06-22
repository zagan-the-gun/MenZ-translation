@echo off
chcp 65001
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==========================================
echo Hugging Face キャッシュクリア (Windows)
echo ==========================================
echo.

echo 現在のディレクトリ: %CD%
echo.

REM 仮想環境の確認
if exist "venv3.12\Scripts\activate.bat" (
    echo 仮想環境を有効化中...
    call venv3.12\Scripts\activate.bat
    echo.
) else (
    echo 仮想環境が見つかりません。通常のPythonを使用します。
    echo.
)

REM Pythonの確認
python --version > nul 2>&1
if errorlevel 1 (
    echo エラー: Pythonが見つかりません。
    echo Python 3.8以上がインストールされていることを確認してください。
    echo.
    pause
    exit /b 1
)

echo Pythonが見つかりました:
python --version
echo.

REM キャッシュクリアスクリプト実行
echo キャッシュクリアスクリプトを実行中...
echo.
python clear_model_cache_windows.py

echo.
echo ==========================================
echo 完了
echo ==========================================
echo.
pause 