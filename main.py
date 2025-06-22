"""
MenZ翻訳サーバー メインエントリーポイント
リアルタイム翻訳専用AI WebSocketサーバー
"""

import asyncio
import logging
import signal
import sys
import os
import threading
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from MenZTranslator import Config, TranslationWebSocketServer

# Windows用のグローバル停止フラグ
_stop_event = None
_server_instance = None

def windows_signal_handler(signum, frame):
    """Windowsでのシグナルハンドラー（同期版）"""
    global _stop_event, _server_instance
    print("\n停止シグナルを受信しました。サーバーを停止します...")
    logging.info("Windows停止シグナルを受信しました。サーバーを停止します...")
    if _stop_event:
        _stop_event.set()


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
    global _stop_event, _server_instance
    server = None
    server_task = None
    
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

        
        # サーバー初期化
        logging.info("サーバーを初期化中...")
        server = TranslationWebSocketServer(config)
        _server_instance = server
        
        # 停止イベント作成
        stop_event = asyncio.Event()
        _stop_event = stop_event
        
        # プラットフォーム別シグナル設定（Windows対応大幅改善）
        signal_handler_installed = False
        
        if sys.platform == "win32":
            # Windows: 同期的なシグナルハンドラーを使用
            try:
                signal.signal(signal.SIGINT, windows_signal_handler)
                signal_handler_installed = True
                logging.info("Windows用シグナルハンドラーを設定しました")
            except Exception as e:
                logging.warning(f"Windows用シグナルハンドラー設定エラー: {e}")
        else:
            # Unix系: 非同期シグナルハンドラー
            def unix_signal_handler():
                logging.info("停止シグナルを受信しました。サーバーを停止します...")
                stop_event.set()
            
            try:
                loop = asyncio.get_running_loop()
                for sig in [signal.SIGINT, signal.SIGTERM]:
                    loop.add_signal_handler(sig, unix_signal_handler)
                signal_handler_installed = True
                logging.info("Unix系シグナルハンドラーを設定しました")
            except Exception as e:
                logging.warning(f"Unix系シグナルハンドラー設定エラー: {e}")
        
        if not signal_handler_installed:
            logging.warning("シグナルハンドラーが設定できませんでした - 手動停止のみ利用可能")
        
        # サーバー起動
        logging.info("=" * 60)
        logging.info("翻訳サーバーが準備完了しました！")
        logging.info(f"WebSocket URL: ws://{config.server_host}:{config.server_port}")
        logging.info("Ctrl+C で停止できます")
        logging.info("=" * 60)
        
        # サーバータスク開始
        server_task = asyncio.create_task(server.start_server(stop_event))
        
        # Windows用の追加的な停止監視タスク
        if sys.platform == "win32":
            # 定期的にstop_eventをチェックするタスク
            async def windows_stop_monitor():
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)
            
            stop_monitor_task = asyncio.create_task(windows_stop_monitor())
            
            # 停止シグナルまたはサーバー終了を待機
            done, pending = await asyncio.wait(
                [server_task, stop_monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
        else:
            # Unix系では従来通り
            done, pending = await asyncio.wait(
                [server_task, asyncio.create_task(stop_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
        
        # 実際に完了したタスクをチェック
        for task in done:
            if task.exception() is not None:
                logging.error(f"タスク例外: {type(task.exception()).__name__}: {task.exception()}")
                raise task.exception()
            elif task == server_task and not stop_event.is_set():
                # サーバータスクが予期せず終了した場合
                logging.warning("サーバータスクが予期せず終了しました")
        
        # 停止処理
        if stop_event.is_set():
            logging.info("停止シグナルによる終了処理を開始します")
            
            # サーバータスクをキャンセル
            if server_task and not server_task.done():
                server_task.cancel()
                try:
                    await asyncio.wait_for(server_task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            
            # 残りのタスクもキャンセル
            for task in pending:
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
        
        logging.info("メイン処理が正常に終了しました")
        
    except KeyboardInterrupt:
        logging.info("ユーザーによる中断を検出しました（KeyboardInterrupt）")
        print("\nユーザーによる中断を検出しました")
    except Exception as e:
        logging.error(f"サーバー実行エラー: {type(e).__name__}: {str(e)}")
        logging.exception("詳細なエラー情報:")
        raise
    finally:
        # グローバル変数をクリア
        _stop_event = None
        _server_instance = None
        
        if server:
            await shutdown(server)


async def shutdown(server: TranslationWebSocketServer):
    """サーバー終了処理"""
    try:
        logging.info("サーバーの終了処理を開始します...")
        await server.shutdown()
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
        
        # 追加の環境情報（特にWindows）
        if sys.platform == "win32":
            logging.info(f"Windows環境での実行: Python {sys.version}")
            logging.info(f"PyTorch バージョン: {torch.__version__}")
            logging.info(f"CUDA利用可能: {torch.cuda.is_available()}")
            if torch.cuda.is_available():
                logging.info(f"CUDA デバイス数: {torch.cuda.device_count()}")
                for i in range(torch.cuda.device_count()):
                    logging.info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        
        return True
    except ImportError as e:
        print(f"エラー: 必要なライブラリが不足しています: {e}")
        print("pip install -r requirements.txt を実行してください")
        return False
    except Exception as e:
        logging.error(f"依存関係チェックエラー: {e}")
        return False


if __name__ == "__main__":
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    # Windowsでのイベントループポリシー設定（改善版）
    if sys.platform == "win32":
        # Windows 10以降でのProactorEventLoopを避けてSelectorEventLoopを使用
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logging.info("WindowsSelectorEventLoopPolicyを設定しました")
        except Exception as e:
            logging.warning(f"イベントループポリシー設定エラー: {e}")
    
    # サーバー実行（Windows対応改善）
    try:
        if sys.platform == "win32":
            # Windowsでの実行時にKeyboardInterruptをより確実にキャッチ
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(main())
            except KeyboardInterrupt:
                print("\nCtrl+Cが検出されました。プログラムを終了します...")
                logging.info("KeyboardInterrupt による終了")
            finally:
                try:
                    # 残っているタスクをキャンセル
                    pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                    if pending_tasks:
                        logging.info(f"残りタスク {len(pending_tasks)} 個をキャンセル中...")
                        for task in pending_tasks:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                    
                    loop.close()
                except Exception as e:
                    logging.error(f"ループクリーンアップエラー: {e}")
        else:
            # Unix系では従来通り
            asyncio.run(main())
    
    except Exception as e:
        print(f"致命的エラー: {e}")
        logging.error(f"致命的エラー: {e}")
        sys.exit(1)
    
    print("プログラムが正常に終了しました")

