"""
設定管理モジュール
"""

import os
import configparser
from typing import Any


class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: str = "config/translator.ini"):
        self.config_path = config_file
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(config_file):
            self._create_default_config()
        else:
            self.config.read(config_file, encoding='utf-8')
    
    def _create_default_config(self):
        """デフォルト設定を作成"""
        self.config['SERVER'] = {
            'host': '127.0.0.1',
            'port': '8765',
            'max_connections': '50'
        }
        
        self.config['TRANSLATION'] = {
            'model_name': 'facebook/nllb-200-distilled-1.3B',
            'device': 'auto',  # auto, cpu, cuda, mps
            'gpu_id': '0',  # GPU ID (0, 1, 2, ...) for multi-GPU systems
            'max_length': '256'
        }
        
        self.config['LOGGING'] = {
            'level': 'INFO',
            'file': 'logs/translator.log',
            'max_file_size': '10485760',  # 10MB
            'backup_count': '5'
        }
        
        # ディレクトリ作成
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # 設定ファイル保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """設定値を取得"""
        return self.config.get(section, key, fallback=fallback)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """設定値を整数として取得"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """設定値をブール値として取得"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """設定値を浮動小数として取得"""
        return self.config.getfloat(section, key, fallback=fallback)
    
    @property
    def server_host(self) -> str:
        return self.get('SERVER', 'host', '127.0.0.1')
    
    @property
    def server_port(self) -> int:
        return self.getint('SERVER', 'port', 8765)
    
    @property
    def max_connections(self) -> int:
        return self.getint('SERVER', 'max_connections', 50)
    
    @property
    def model_name(self) -> str:
        return self.get('TRANSLATION', 'model_name', 'facebook/nllb-200-distilled-1.3B')
    
    @property
    def device(self) -> str:
        return self.get('TRANSLATION', 'device', 'auto')
    
    @property
    def gpu_id(self) -> int:
        return self.getint('TRANSLATION', 'gpu_id', 0)
    
    @property
    def max_length(self) -> int:
        return self.getint('TRANSLATION', 'max_length', 256)
    
    @property
    def log_level(self) -> str:
        return self.get('LOGGING', 'level', 'INFO')
    
    @property
    def log_file(self) -> str:
        return self.get('LOGGING', 'file', 'logs/translator.log') 