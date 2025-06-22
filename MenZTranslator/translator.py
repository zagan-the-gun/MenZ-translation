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
    
    def __init__(self, model_name: str = "facebook/nllb-200-distilled-1.3B", device: str = "auto"):
        self.model_name = model_name
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
                device = torch.device("cuda")
                logging.info(f"NVIDIA CUDA デバイスを使用します: {torch.cuda.get_device_name(0)}")
            else:
                device = torch.device("cpu")
                logging.info("GPU が利用できません。CPUを使用します")
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
    
    def translate_with_context(self, 
                               text: str, 
                               context_buffer: list = None,
                               source_lang: str = "eng_Latn", 
                               target_lang: str = "jpn_Jpan",
                               max_length: int = 256) -> str:
        """文脈を考慮した翻訳"""
        try:
            if not context_buffer:
                return self.translate(text, source_lang, target_lang, max_length)
            
            # 文脈を含むプロンプトを構築
            context_prompt = self._build_context_prompt(
                text, context_buffer, source_lang, target_lang
            )
            
            # 翻訳実行
            result = self.translate(context_prompt, source_lang, target_lang, max_length)
            
            # プロンプト部分を除去して翻訳結果のみを抽出
            return self._extract_translation_result(result, context_prompt)
            
        except Exception as e:
            logging.error(f"文脈翻訳エラー: {e}")
            # フォールバック: 文脈なしで翻訳
            return self.translate(text, source_lang, target_lang, max_length)
    
    def _build_context_prompt(self, 
                              current_text: str, 
                              context_buffer: list, 
                              source_lang: str, 
                              target_lang: str) -> str:
        """文脈を含むプロンプトを構築"""
        context_examples = ""
        
        # 最新の2-3件の文脈を追加（翻訳品質向上のため）
        for orig, trans in context_buffer[-3:]:
            context_examples += f"{orig} | {trans}\n"
        
        # 現在の翻訳対象を追加（区切り文字で明確に分離）
        if context_examples:
            prompt = f"{context_examples}---\n{current_text}"
        else:
            prompt = current_text
        
        return prompt
    
    def _extract_translation_result(self, result: str, prompt: str) -> str:
        """プロンプトから翻訳結果のみを抽出"""
        try:
            # 区切り文字"---"がある場合、その後の部分のみを対象とする
            if "---" in prompt:
                # プロンプトの構造を理解
                prompt_parts = prompt.split("---")
                if len(prompt_parts) >= 2:
                    original_text = prompt_parts[-1].strip()
                    
                    # 結果から区切り文字以降の部分を探す
                    if "---" in result:
                        result_parts = result.split("---")
                        if len(result_parts) >= 2:
                            new_translation = result_parts[-1].strip()
                            # さらにパイプ文字区切りがある場合は最後の部分
                            if "|" in new_translation:
                                translation_parts = new_translation.split("|")
                                return translation_parts[-1].strip()
                            return new_translation
                    
                    # 区切り文字がない場合、結果の最後の部分を取得
                    result_lines = result.split('\n')
                    # 文脈行をスキップして新しい翻訳のみを取得
                    context_line_count = len(prompt.split('\n')) - 1
                    if len(result_lines) > context_line_count:
                        new_lines = result_lines[context_line_count:]
                        return '\n'.join(new_lines).strip()
            
            # プロンプトに"|"区切りがある場合の処理
            if "|" in result:
                # 結果の最後の"|"以降の部分を取得
                parts = result.split("|")
                return parts[-1].strip()
            
            # フォールバック：最後の行を返す
            lines = result.split('\n')
            if lines:
                return lines[-1].strip()
                
        except Exception as e:
            logging.warning(f"翻訳結果抽出エラー: {e}")
            # エラー時は結果全体を返す
            return result.strip()
        
        return result.strip()
    
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