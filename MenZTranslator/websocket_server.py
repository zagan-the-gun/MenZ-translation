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
from .config import Config


class TranslationWebSocketServer:
    """翻訳専用WebSocketサーバー"""
    
    def __init__(self, config: Config):
        self.config = config
        self.translator = None
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
            
            logging.info("サーバーコンポーネントの初期化が完了しました")
            
        except Exception as e:
            logging.error(f"コンポーネント初期化エラー: {e}")
            raise
    
    async def start_server(self, stop_event: asyncio.Event):
        """サーバーを開始"""
        try:
            # サーバー起動
            self.server = await websockets.serve(
                lambda websocket, path: self.handle_client(websocket, path, stop_event),
                self.config.server_host,
                self.config.server_port,
                max_size=1024*1024,  # 1MB
                ping_interval=30,
                ping_timeout=10
            )
            
            logging.info(f"WebSocketサーバーが起動しました: ws://{self.config.server_host}:{self.config.server_port}")
            
            # 停止イベントを待機
            await stop_event.wait()
            
        except Exception as e:
            logging.error(f"サーバー起動エラー: {e}")
            raise
        finally:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                logging.info("WebSocketサーバーが停止しました")
    
    async def handle_client(self, websocket, path, stop_event: asyncio.Event):
        """クライアント接続の処理"""
        client_id = str(uuid.uuid4())[:8]
        
        try:
            self.connected_clients.add(websocket)
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            logging.info(f"クライアント接続: {client_id} ({client_info})")
            
            # 接続情報を送信
            await self.send_response(websocket, {
                "type": "connection",
                "client_id": client_id,
                "server_info": {
                    "model": self.config.model_name,
                    "device": str(self.translator.device) if self.translator else "unknown",
                    "status": "ready"
                }
            })
            
            # メッセージ処理ループ
            async for message in websocket:
                await self.handle_message(websocket, message, client_id)
                
        except ConnectionClosed:
            logging.info(f"クライアント切断: {client_id}")
        except Exception as e:
            logging.error(f"クライアント処理エラー ({client_id}): {e}")
        finally:
            self.connected_clients.discard(websocket)
            # このクライアントのアクティブリクエストをクリーンアップ
            to_remove = [req_id for req_id, req_data in self.active_requests.items() 
                        if req_data.get('client_id') == client_id]
            for req_id in to_remove:
                self.active_requests.pop(req_id, None)
    
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
            priority = data.get('priority', 'normal')
            source_lang = data.get('source_lang', 'eng_Latn')
            target_lang = data.get('target_lang', 'jpn_Jpan')
            max_length = data.get('max_length', self.config.max_length)
            
            # リクエスト記録
            self.active_requests[request_id] = {
                'client_id': client_id,
                'priority': priority,
                'start_time': time.time(),
                'websocket': websocket
            }
            
            # 翻訳実行
            start_time = time.time()
            
            translated_text = self.translator.translate(
                text,
                source_lang,
                target_lang,
                max_length
            )
            
            processing_time = (time.time() - start_time) * 1000  # ミリ秒
            
            # レスポンス送信
            response = {
                "request_id": request_id,
                "translated": translated_text,
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
                "translator_ready": self.translator.is_ready() if self.translator else False
            }
            
            await self.send_response(websocket, stats)
            
        except Exception as e:
            await self.send_error(websocket, f"統計情報取得エラー: {e}")
    
    async def send_response(self, websocket, data: Dict):
        """レスポンス送信"""
        try:
            await websocket.send(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logging.error(f"レスポンス送信エラー: {e}")
    
    async def send_error(self, websocket, error_message: str, request_id: Optional[str] = None):
        """エラーレスポンス送信"""
        error_data = {
            "error": error_message,
            "status": "error"
        }
        
        if request_id:
            error_data["request_id"] = request_id
        
        await self.send_response(websocket, error_data)
    
    async def shutdown(self):
        """サーバーのシャットダウン"""
        try:
            # 全てのクライアント接続を閉じる
            if self.connected_clients:
                logging.info(f"{len(self.connected_clients)}個の接続を終了中...")
                disconnect_tasks = []
                for client in self.connected_clients.copy():
                    try:
                        await client.close()
                    except Exception as e:
                        logging.warning(f"クライアント切断エラー: {e}")
                
                self.connected_clients.clear()
                
            # サーバーを停止
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                
            logging.info("サーバーのシャットダウンが完了しました")
            
        except Exception as e:
            logging.error(f"シャットダウンエラー: {e}") 