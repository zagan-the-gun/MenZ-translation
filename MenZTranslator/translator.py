"""
NLLB翻訳エンジンモジュール
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import logging
from typing import Optional, Dict, Any
import time


class NLLBTranslator:
    """NLLB翻訳エンジンクラス"""
    
    def __init__(self, model_name: str = "facebook/nllb-200-distilled-1.3B", device: str = "auto", gpu_id: int = 0):
        self.model_name = model_name
        self.gpu_id = gpu_id
        self.device = self._get_device(device)
        self.model = None
        self.tokenizer = None
        self._initialize_model()
        
    def _get_device(self, device_config: str) -> torch.device:
        """デバイスを自動選択または指定"""
        if device_config == "auto":
            if torch.backends.mps.is_available():
                device = torch.device("mps")
                logging.info("Apple Silicon MPS デバイスを使用します")
            elif torch.cuda.is_available():
                if self.gpu_id < torch.cuda.device_count():
                    device = torch.device(f"cuda:{self.gpu_id}")
                    logging.info(f"NVIDIA CUDA GPU {self.gpu_id} を使用します: {torch.cuda.get_device_name(self.gpu_id)}")
                else:
                    logging.warning(f"指定されたGPU ID {self.gpu_id} は利用できません。GPU 0を使用します")
                    device = torch.device("cuda:0")
                    logging.info(f"NVIDIA CUDA GPU 0 を使用します: {torch.cuda.get_device_name(0)}")
            else:
                device = torch.device("cpu")
                logging.info("GPU が利用できません。CPUを使用します")
        elif device_config.startswith("cuda"):
            # cuda:N の形式で指定された場合
            if torch.cuda.is_available():
                if ":" in device_config:
                    # cuda:N の形式
                    device = torch.device(device_config)
                else:
                    # cudaのみの場合、gpu_idを付加
                    device = torch.device(f"cuda:{self.gpu_id}")
                
                # 指定されたGPUが利用可能かチェック
                gpu_id = int(str(device).split(":")[-1])
                if gpu_id < torch.cuda.device_count():
                    logging.info(f"指定されたGPU {gpu_id} を使用します: {torch.cuda.get_device_name(gpu_id)}")
                else:
                    logging.warning(f"指定されたGPU {gpu_id} は利用できません。GPU 0を使用します")
                    device = torch.device("cuda:0")
                    logging.info(f"NVIDIA CUDA GPU 0 を使用します: {torch.cuda.get_device_name(0)}")
            else:
                logging.warning("CUDA が利用できません。CPUを使用します")
                device = torch.device("cpu")
        else:
            device = torch.device(device_config)
            logging.info(f"指定されたデバイスを使用します: {device}")
        
        return device
    
    def _initialize_model(self):
        """モデルとトークナイザーを初期化"""
        try:
            logging.info(f"モデルを読み込み中: {self.model_name}")
            start_time = time.time()
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            
            load_time = time.time() - start_time
            logging.info(f"モデルの読み込みが完了しました ({load_time:.2f}秒)")
            
        except Exception as e:
            logging.error(f"モデルの初期化に失敗しました: {e}")
            raise
    
    def translate(self, 
                  text: str, 
                  source_lang: str = "eng_Latn", 
                  target_lang: str = "jpn_Jpan",
                  max_length: int = 256) -> str:
        """テキストを翻訳"""
        try:
            if not text.strip():
                return ""
            
            # トークナイザーの言語設定
            self.tokenizer.src_lang = source_lang
            
            # 入力をトークン化
            inputs = self.tokenizer(text, return_tensors="pt", padding=True).to(self.device)
            
            # 翻訳実行
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(target_lang),
                    max_length=max_length,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            
            # デコード
            translation = self.tokenizer.batch_decode(
                generated_tokens, 
                skip_special_tokens=True
            )[0]
            
            return translation.strip()
            
        except Exception as e:
            logging.error(f"翻訳エラー: {e}")
            return f"翻訳エラー: {str(e)}"
    
    def get_supported_languages(self) -> Dict[str, str]:
        """サポートされている言語コードを取得"""
        # 主要な言語コードのマッピング
        return {
            "日本語": "jpn_Jpan",
            "英語": "eng_Latn", 
            "中国語（簡体字）": "zho_Hans",
            "中国語（繁体字）": "zho_Hant",
            "韓国語": "kor_Hang",
            "フランス語": "fra_Latn",
            "ドイツ語": "deu_Latn",
            "スペイン語": "spa_Latn",
            "イタリア語": "ita_Latn",
            "ロシア語": "rus_Cyrl",
            "アラビア語": "arb_Arab",
            "ヒンディー語": "hin_Deva",
            "タイ語": "tha_Thai",
            "ベトナム語": "vie_Latn"
        }
    
    def is_ready(self) -> bool:
        """翻訳エンジンが準備完了かチェック"""
        return self.model is not None and self.tokenizer is not None 