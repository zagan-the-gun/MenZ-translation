"""
MenZ翻訳サーバー メインエントリーポイント
リアルタイム翻訳専用AI WebSocketサーバー
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from MenZTranslator import Config, TranslationWebSocketServer


def setup_logging(config: Config):
    """ログ設定を初期化"""
    # ログディレクトリ作成
    log_file = Path(config.log_file)
    log_file.parent.mkdir(exist_ok=True)
    
    # ログレベル設定
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"ログ設定完了: レベル={config.log_level}, ファイル={config.log_file}")


def print_banner():
    """起動バナー表示"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                MenZ翻訳サーバー v0.1.0                    ║
    ║           リアルタイム翻訳専用AI WebSocketサーバー          ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """メイン処理"""
    server = None
    
    try:
        # バナー表示
        print_banner()
        
        # 設定読み込み
        print("設定ファイルを読み込み中...")
        config = Config()
        
        # ログ設定
        setup_logging(config)
        logging.info("MenZ翻訳サーバーを起動中...")
        
        # サーバー設定表示
        logging.info(f"サーバー設定:")
        logging.info(f"  ホスト: {config.server_host}")
        logging.info(f"  ポート: {config.server_port}")
        logging.info(f"  翻訳モデル: {config.model_name}")
        logging.info(f"  デバイス: {config.device}")
        logging.info(f"  文脈管理: {'有効' if config.use_context else '無効'}")
        
        # サーバー初期化
        logging.info("サーバーを初期化中...")
        server = TranslationWebSocketServer(config)
        
        # シグナルハンドラー設定
        def signal_handler(signum, frame):
            logging.info(f"シグナル {signum} を受信しました。サーバーを停止します...")
            asyncio.create_task(shutdown(server))
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # サーバー起動
        logging.info("=" * 60)
        logging.info("翻訳サーバーが準備完了しました！")
        logging.info(f"WebSocket URL: ws://{config.server_host}:{config.server_port}")
        logging.info("Ctrl+C で停止できます")
        logging.info("=" * 60)
        
        await server.start_server()
        
    except KeyboardInterrupt:
        logging.info("ユーザーによる中断を検出しました")
    except Exception as e:
        logging.error(f"サーバー実行エラー: {e}")
        sys.exit(1)
    finally:
        if server:
            await shutdown(server)


async def shutdown(server: TranslationWebSocketServer):
    """サーバー終了処理"""
    try:
        logging.info("サーバーの終了処理を開始します...")
        await server.stop_server()
        logging.info("サーバーが正常に終了しました")
    except Exception as e:
        logging.error(f"終了処理エラー: {e}")


def check_dependencies():
    """依存関係チェック"""
    try:
        import torch
        import transformers
        import websockets
        logging.info("必要なライブラリが確認できました")
        return True
    except ImportError as e:
        print(f"エラー: 必要なライブラリが不足しています: {e}")
        print("pip install -r requirements.txt を実行してください")
        return False


if __name__ == "__main__":
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    # Windowsでのイベントループポリシー設定
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # サーバー実行
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"致命的エラー: {e}")
        sys.exit(1)

