@echo off
chcp 65001 > nul
echo.
echo ======================================================
echo      MenZ翻訳サーバー - 起動中...
echo ======================================================
echo.

:: 仮想環境の存在確認
if not exist venv (
    echo [ERROR] 仮想環境が見つかりません。
    echo         setup.bat を先に実行してください。
    pause
    exit /b 1
)

:: 設定ファイルの確認
if not exist config\translator.ini (
    echo [ERROR] 設定ファイルが見つかりません。
    echo         setup.bat を先に実行してください。
    pause
    exit /b 1
)

echo [INFO] 仮想環境をアクティベート中...
call venv\Scripts\activate.bat

echo [INFO] 依存関係を確認中...
pip show torch >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 必要なライブラリがインストールされていません。
    echo         setup.bat を実行してください。
    pause
    exit /b 1
)

echo [INFO] サーバーを起動中...
echo.
echo ======================================================
echo   ポート: 55001
echo   URL: ws://127.0.0.1:55001
echo   終了: Ctrl + C
echo ======================================================
echo.

:: サーバー起動
python main.py

:: 異常終了時の処理
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] サーバーが異常終了しました。
    echo         エラーログを確認してください: logs\translator.log
    echo.
    pause
)

echo.
echo [INFO] サーバーが停止しました。
pause 