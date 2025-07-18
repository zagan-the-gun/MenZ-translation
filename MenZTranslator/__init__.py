"""
MenZ Translation Server Package
リアルタイム翻訳専用AI WebSocketサーバー
"""

__version__ = "0.1.0"
__author__ = "MenZ Translation Team"

from .translator import NLLBTranslator
from .websocket_server import TranslationWebSocketServer
from .config import Config

__all__ = [
    "NLLBTranslator",
    "TranslationWebSocketServer",
    "Config"
] 