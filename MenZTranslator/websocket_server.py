"""
WebSocketサーバーモジュール
"""

import asyncio
import websockets
import json
import logging
import uuid
import sys
from typing import Dict, Set, Optional, Any
import time
from websockets.exceptions import ConnectionClosed

from .translator import NLLBTranslator
from .context_manager import SpeakerContextManager
from .config import Config


class TranslationWebSocketServer:
    """翻訳専用WebSocketサーバー"""
    
    def __init__(self, config: Config):
        self.config = config
        self.translator = None
        self.context_manager = None
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.active_requests: Dict[str, Dict] = {}
        self.server = None
        self._initialize_components()
    
    def _initialize_components(self):
        """コンポーネントを初期化"""
        try:
            # 翻訳エンジン初期化
            logging.info("翻訳エンジンを初期化中...")
            self.translator = NLLBTranslator(
                model_name=self.config.model_name,
                device=self.config.device,
                gpu_id=self.config.gpu_id
            )
            
            # 文脈管理初期化
            if self.config.use_context:
                logging.info("文脈管理を初期化中...")
                self.context_manager = SpeakerContextManager(
                    max_context_per_speaker=self.config.max_context_per_speaker,
                    cleanup_interval=self.config.context_cleanup_interval
                )
            
            logging.info("サーバーコンポーネントの初期化が完了しました")
            
        except Exception as e:
            logging.error(f"コンポーネント初期化エラー: {e}")
            raise
    
    async def handle_client(self, websocket):
        """クライアント接続の処理"""
        client_id = f"client_{uuid.uuid4().hex[:8]}"
        path = getattr(websocket, 'path', '/')
        self.connected_clients.add(websocket)
        
        try:
            logging.info(f"新しいクライアントが接続しました: {client_id}")
            
            # 接続確認メッセージを送信
            await self.send_message(websocket, {
                "type": "connection",
                "status": "connected",
                "client_id": client_id,
                "server_info": {
                    "model": self.config.model_name,
                    "device": str(self.translator.device),
                    "gpu_id": self.config.gpu_id,
                    "context_enabled": self.config.use_context,
                    "supported_languages": self.translator.get_supported_languages()
                }
            })
            
            # メッセージ処理ループ
            async for message in websocket:
                await self.handle_message(websocket, message, client_id)
                
        except ConnectionClosed:
            logging.info(f"クライアントが切断されました: {client_id}")
        except Exception as e:
            logging.error(f"クライアント処理エラー ({client_id}): {e}")
            await self.send_error(websocket, str(e))
        finally:
            self.connected_clients.discard(websocket)
    
    async def handle_message(self, websocket, message: str, client_id: str):
        """メッセージの処理"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'translation')
            
            if message_type == 'translation':
                await self.handle_translation_request(websocket, data, client_id)
            elif message_type == 'ping':
                await self.handle_ping(websocket, data)
            elif message_type == 'stats':
                await self.handle_stats_request(websocket, data)
            elif message_type == 'context_clear':
                await self.handle_context_clear(websocket, data)
            else:
                await self.send_error(websocket, f"不明なメッセージタイプ: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "無効なJSONフォーマット")
        except Exception as e:
            logging.error(f"メッセージ処理エラー: {e}")
            await self.send_error(websocket, str(e))
    
    async def handle_translation_request(self, websocket, data: Dict, client_id: str):
        """翻訳リクエストの処理"""
        try:
            # 必須パラメータの確認
            request_id = data.get('request_id')
            text = data.get('text', '').strip()
            
            if not request_id:
                await self.send_error(websocket, "request_id が必要です")
                return
            
            if not text:
                await self.send_response(websocket, {
                    "request_id": request_id,
                    "translated": "",
                    "status": "completed",
                    "message": "空のテキストです"
                })
                return
            
            # パラメータ取得
            context_id = data.get('context_id')
            priority = data.get('priority', 'normal')
            source_lang = data.get('source_lang', 'eng_Latn')
            target_lang = data.get('target_lang', 'jpn_Jpan')
            max_length = data.get('max_length', self.config.max_length)
            
            # リクエスト記録
            self.active_requests[request_id] = {
                'client_id': client_id,
                'context_id': context_id,
                'priority': priority,
                'start_time': time.time(),
                'websocket': websocket
            }
            
            # 翻訳実行
            start_time = time.time()
            
            if self.context_manager and context_id:
                # 文脈考慮翻訳
                translated_text = self.context_manager.translate_with_speaker_context(
                    self.translator,
                    text,
                    context_id,
                    source_lang,
                    target_lang,
                    max_length
                )
                translation_type = "contextual"
            else:
                # 単純翻訳
                translated_text = self.translator.translate(
                    text,
                    source_lang,
                    target_lang,
                    max_length
                )
                translation_type = "simple"
            
            processing_time = (time.time() - start_time) * 1000  # ミリ秒
            
            # レスポンス送信
            response = {
                "request_id": request_id,
                "translated": translated_text,
                "translation_type": translation_type,
                "context_id": context_id,
                "processing_time_ms": round(processing_time, 2),
                "status": "completed"
            }
            
            await self.send_response(websocket, response)
            
            # ログ出力
            logging.info(f"翻訳完了 [{client_id}]: {text[:50]}... -> {translated_text[:50]}... ({processing_time:.1f}ms)")
            
        except Exception as e:
            logging.error(f"翻訳処理エラー: {e}")
            await self.send_error(websocket, str(e), request_id)
        finally:
            # リクエスト記録をクリーンアップ
            self.active_requests.pop(request_id, None)
    
    async def handle_ping(self, websocket, data: Dict):
        """Pingの処理"""
        await self.send_response(websocket, {
            "type": "pong",
            "timestamp": time.time(),
            "server_status": "running"
        })
    
    async def handle_stats_request(self, websocket, data: Dict):
        """統計情報リクエストの処理"""
        try:
            stats = {
                "type": "stats",
                "connected_clients": len(self.connected_clients),
                "active_requests": len(self.active_requests),
                "translator_ready": self.translator.is_ready() if self.translator else False,
                "context_enabled": self.config.use_context
            }
            
            if self.context_manager:
                stats["context_stats"] = self.context_manager.get_system_stats()
            
            await self.send_response(websocket, stats)
            
        except Exception as e:
            await self.send_error(websocket, f"統計情報取得エラー: {e}")
    
    async def handle_context_clear(self, websocket, data: Dict):
        """文脈クリアリクエストの処理"""
        try:
            if not self.context_manager:
                await self.send_error(websocket, "文脈管理が無効です")
                return
            
            context_id = data.get('context_id')
            if not context_id:
                await self.send_error(websocket, "context_id が必要です")
                return
            
            success = self.context_manager.clear_speaker_context(context_id)
            
            response = {
                "type": "context_clear",
                "context_id": context_id,
                "success": success,
                "status": "completed" if success else "not_found"
            }
            
            await self.send_response(websocket, response)
            
        except Exception as e:
            await self.send_error(websocket, f"文脈クリアエラー: {e}")
    
    async def send_message(self, websocket, message: Dict):
        """メッセージ送信"""
        try:
            await websocket.send(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logging.error(f"メッセージ送信エラー: {e}")
    
    async def send_response(self, websocket, response: Dict):
        """レスポンス送信"""
        await self.send_message(websocket, response)
    
    async def send_error(self, websocket, error_message: str, request_id: Optional[str] = None):
        """エラーメッセージ送信"""
        error_response = {
            "type": "error",
            "error": error_message,
            "status": "error"
        }
        
        if request_id:
            error_response["request_id"] = request_id
        
        await self.send_message(websocket, error_response)
    
    async def start_server(self):
        """サーバー開始"""
        try:
            logging.info(f"WebSocketサーバーを開始中: {self.config.server_host}:{self.config.server_port}")
            
            # Windowsでの特別なサーバー設定
            server_kwargs = {
                'max_size': 1024*1024,  # 1MB
                'ping_interval': 30,
                'ping_timeout': 10
            }
            
            # Windows特有の問題回避
            if sys.platform == "win32":
                server_kwargs['reuse_port'] = False
            
            self.server = await websockets.serve(
                self.handle_client,
                self.config.server_host,
                self.config.server_port,
                **server_kwargs
            )
            
            logging.info(f"サーバーが起動しました: ws://{self.config.server_host}:{self.config.server_port}")
            
            # サーバーが終了するまで待機（キャンセル可能）
            try:
                await self.server.wait_closed()
            except asyncio.CancelledError:
                logging.info("サーバータスクがキャンセルされました")
                raise
            
        except asyncio.CancelledError:
            logging.info("サーバー起動がキャンセルされました")
            raise
        except OSError as e:
            # ポート使用中やネットワークエラーの詳細情報
            if e.errno == 10048:  # Windows: Address already in use
                logging.error(f"ポート {self.config.server_port} は既に使用されています")
            elif e.errno == 10013:  # Windows: Permission denied
                logging.error(f"ポート {self.config.server_port} への接続が拒否されました（管理者権限が必要な可能性があります）")
            else:
                logging.error(f"ネットワークエラー: {type(e).__name__}: {e}")
            logging.exception("ネットワークエラーの詳細:")
            raise
        except Exception as e:
            logging.error(f"サーバー起動エラー: {type(e).__name__}: {e}")
            logging.exception("サーバー起動エラーの詳細:")
            raise
    
    async def stop_server(self):
        """サーバー停止"""
        if self.server:
            logging.info("サーバーを停止中...")
            
            # 接続中のクライアントを全て切断
            if self.connected_clients:
                logging.info(f"{len(self.connected_clients)}個のクライアント接続を切断中...")
                disconnect_tasks = []
                for websocket in self.connected_clients.copy():
                    try:
                        # より確実にクライアントを切断
                        if not websocket.closed:
                            disconnect_tasks.append(websocket.close(code=1001, reason="Server shutdown"))
                    except Exception as e:
                        logging.warning(f"クライアント切断エラー: {e}")
                
                if disconnect_tasks:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*disconnect_tasks, return_exceptions=True),
                            timeout=3.0  # タイムアウトを短縮
                        )
                    except asyncio.TimeoutError:
                        logging.warning("クライアント切断がタイムアウトしました")
                    except Exception as e:
                        logging.warning(f"クライアント切断処理エラー: {e}")
            
            # サーバーを停止
            try:
                self.server.close()
                logging.info("サーバークローズを要求しました")
            except Exception as e:
                logging.error(f"サーバークローズエラー: {e}")
            
            # サーバーの完全停止を待機（Windows対応改善）
            try:
                await asyncio.wait_for(self.server.wait_closed(), timeout=5.0)
                logging.info("サーバーが正常に停止しました")
            except asyncio.TimeoutError:
                logging.warning("サーバー停止がタイムアウトしました（強制終了）")
                # Windows環境では強制的にサーバーを None にして終了を促進
                if sys.platform == "win32":
                    self.server = None
            except Exception as e:
                logging.error(f"サーバー停止エラー: {e}")
                if sys.platform == "win32":
                    self.server = None
        else:
            logging.info("サーバーは既に停止しています")
    
    def get_server_info(self) -> Dict:
        """サーバー情報を取得"""
        return {
            "host": self.config.server_host,
            "port": self.config.server_port,
            "model": self.config.model_name,
            "device": self.config.device,
            "context_enabled": self.config.use_context,
            "connected_clients": len(self.connected_clients),
            "active_requests": len(self.active_requests)
        } 