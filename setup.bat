@echo off
chcp 65001 > nul
echo.
echo ======================================================
echo     MenZ翻訳サーバー - Windows セットアップ
echo ======================================================
echo.

:: 管理者権限チェック
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] 管理者権限で実行されています
) else (
    echo [WARNING] 管理者権限で実行することを推奨します
    echo           （ファイアウォール設定のため）
)

echo.
echo [1/6] Python のバージョンを確認中...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python が見つかりません。
    echo         Python 3.8以上をインストールしてPATHに追加してください。
    echo         https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

echo.
echo [2/6] 仮想環境を作成中...
if exist venv (
    echo [INFO] 既存の仮想環境が見つかりました。削除して再作成しますか？ (y/N)
    set /p recreate=
    if /i "!recreate!"=="y" (
        echo [INFO] 既存の仮想環境を削除中...
        rmdir /s /q venv
    )
)

if not exist venv (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 仮想環境の作成に失敗しました。
        pause
        exit /b 1
    )
    echo [SUCCESS] 仮想環境を作成しました。
)

echo.
echo [3/6] 仮想環境をアクティベート中...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 仮想環境のアクティベートに失敗しました。
    pause
    exit /b 1
)

echo.
echo [4/6] 依存関係をインストール中...
echo [INFO] これには数分かかる場合があります...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依存関係のインストールに失敗しました。
    echo [HINT] インターネット接続を確認してください。
    pause
    exit /b 1
)

echo.
echo [5/6] 必要なディレクトリを作成中...
if not exist config mkdir config
if not exist logs mkdir logs

echo.
echo [6/6] 設定ファイルを作成中...
if not exist config\translator.ini (
    echo [INFO] デフォルト設定ファイルを作成中...
    copy /y config_windows_sample.ini config\translator.ini > nul
    if %errorlevel% neq 0 (
        echo [INFO] サンプル設定が見つからないため、基本設定を作成します...
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
            echo use_context = false
            echo.
            echo [CONTEXT]
            echo max_context_per_speaker = 3
            echo context_cleanup_interval = 3600
            echo max_context_length = 256
            echo.
            echo [LOGGING]
            echo level = INFO
            echo file = logs/translator.log
            echo max_file_size = 10485760
            echo backup_count = 3
        ) > config\translator.ini
    )
    echo [SUCCESS] 設定ファイルを作成しました: config\translator.ini
) else (
    echo [INFO] 既存の設定ファイルを使用します: config\translator.ini
)

echo.
echo ======================================================
echo セットアップが完了しました！
echo ======================================================
echo.
echo 次のステップ:
echo   1. 必要に応じて config\translator.ini を編集
echo      - NVIDIA GPU搭載PC: device = cuda
echo      - CPU使用: device = cpu
echo.
echo   2. サーバーを起動: run.bat をダブルクリック
echo.
echo ※ ファイアウォールの警告が表示された場合は「アクセスを許可」してください
echo.
pause 