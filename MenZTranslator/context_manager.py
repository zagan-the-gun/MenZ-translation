"""
文脈管理モジュール
"""

import time
import logging
from typing import Dict, List, Tuple, Optional
import threading
from collections import defaultdict


class SpeakerContextManager:
    """話者ベースの文脈管理クラス"""
    
    def __init__(self, max_context_per_speaker: int = 5, cleanup_interval: int = 3600):
        self.max_context_per_speaker = max_context_per_speaker
        self.cleanup_interval = cleanup_interval
        self.speaker_contexts: Dict[str, Dict] = defaultdict(lambda: {
            'buffer': [],
            'last_updated': time.time(),
            'total_translations': 0,
            'created_at': time.time()
        })
        self._lock = threading.RLock()
        self._start_cleanup_timer()
    
    def get_context_for_speaker(self, context_id: str) -> List[Tuple[str, str]]:
        """指定された話者の文脈を取得"""
        with self._lock:
            if context_id in self.speaker_contexts:
                return self.speaker_contexts[context_id]['buffer'].copy()
            return []
    
    def add_translation_to_context(self, 
                                   context_id: str, 
                                   original: str, 
                                   translated: str):
        """翻訳結果を話者の文脈に追加"""
        with self._lock:
            speaker_context = self.speaker_contexts[context_id]
            speaker_context['buffer'].append((original, translated))
            speaker_context['last_updated'] = time.time()
            speaker_context['total_translations'] += 1
            
            # バッファサイズを制限
            if len(speaker_context['buffer']) > self.max_context_per_speaker:
                speaker_context['buffer'].pop(0)
            
            logging.debug(f"文脈を更新: {context_id}, 翻訳数: {speaker_context['total_translations']}")
    
    def translate_with_speaker_context(self, 
                                       translator,
                                       text: str, 
                                       context_id: Optional[str] = None,
                                       source_lang: str = "eng_Latn", 
                                       target_lang: str = "jpn_Jpan",
                                       max_length: int = 256) -> str:
        """話者の文脈を考慮した翻訳"""
        try:
            if context_id is None:
                # 文脈IDがない場合は単純翻訳
                return translator.translate(text, source_lang, target_lang, max_length)
            
            # 話者の文脈を取得
            context_buffer = self.get_context_for_speaker(context_id)
            
            # 文脈を考慮した翻訳
            if context_buffer:
                result = translator.translate_with_context(
                    text, context_buffer, source_lang, target_lang, max_length
                )
            else:
                result = translator.translate(text, source_lang, target_lang, max_length)
            
            # 翻訳結果を文脈に追加
            self.add_translation_to_context(context_id, text, result)
            
            return result
            
        except Exception as e:
            logging.error(f"文脈翻訳エラー ({context_id}): {e}")
            # フォールバック: 単純翻訳
            return translator.translate(text, source_lang, target_lang, max_length)
    
    def get_speaker_stats(self, context_id: str) -> Optional[Dict]:
        """話者の統計情報を取得"""
        with self._lock:
            if context_id in self.speaker_contexts:
                context_data = self.speaker_contexts[context_id]
                return {
                    'context_id': context_id,
                    'total_translations': context_data['total_translations'],
                    'context_buffer_size': len(context_data['buffer']),
                    'last_updated': context_data['last_updated'],
                    'created_at': context_data['created_at'],
                    'active_duration': time.time() - context_data['created_at']
                }
        return None
    
    def get_all_speakers(self) -> List[str]:
        """全ての話者IDを取得"""
        with self._lock:
            return list(self.speaker_contexts.keys())
    
    def clear_speaker_context(self, context_id: str) -> bool:
        """指定された話者の文脈をクリア"""
        with self._lock:
            if context_id in self.speaker_contexts:
                del self.speaker_contexts[context_id]
                logging.info(f"話者の文脈をクリアしました: {context_id}")
                return True
            return False
    
    def cleanup_old_contexts(self, max_age_seconds: Optional[int] = None) -> int:
        """古い文脈をクリーンアップ"""
        if max_age_seconds is None:
            max_age_seconds = self.cleanup_interval
        
        current_time = time.time()
        cleaned_count = 0
        
        with self._lock:
            expired_contexts = [
                context_id for context_id, data in self.speaker_contexts.items()
                if current_time - data['last_updated'] > max_age_seconds
            ]
            
            for context_id in expired_contexts:
                del self.speaker_contexts[context_id]
                cleaned_count += 1
            
            if cleaned_count > 0:
                logging.info(f"期限切れの文脈をクリーンアップしました: {cleaned_count}件")
        
        return cleaned_count
    
    def get_system_stats(self) -> Dict:
        """システム全体の統計情報を取得"""
        with self._lock:
            total_speakers = len(self.speaker_contexts)
            total_translations = sum(
                data['total_translations'] for data in self.speaker_contexts.values()
            )
            total_context_entries = sum(
                len(data['buffer']) for data in self.speaker_contexts.values()
            )
            
            oldest_context = None
            newest_context = None
            
            if self.speaker_contexts:
                times = [data['created_at'] for data in self.speaker_contexts.values()]
                oldest_context = min(times)
                newest_context = max(times)
            
            return {
                'total_speakers': total_speakers,
                'total_translations': total_translations,
                'total_context_entries': total_context_entries,
                'oldest_context': oldest_context,
                'newest_context': newest_context,
                'cleanup_interval': self.cleanup_interval,
                'max_context_per_speaker': self.max_context_per_speaker
            }
    
    def _start_cleanup_timer(self):
        """定期クリーンアップタイマーを開始"""
        def cleanup_task():
            self.cleanup_old_contexts()
            # 次のクリーンアップをスケジュール
            timer = threading.Timer(self.cleanup_interval, cleanup_task)
            timer.daemon = True
            timer.start()
        
        # 初回実行
        timer = threading.Timer(self.cleanup_interval, cleanup_task)
        timer.daemon = True
        timer.start()
        
        logging.info(f"文脈クリーンアップタイマーを開始しました (間隔: {self.cleanup_interval}秒)")
    
    def export_context_for_speaker(self, context_id: str) -> Optional[Dict]:
        """話者の文脈をエクスポート（デバッグ用）"""
        with self._lock:
            if context_id in self.speaker_contexts:
                return {
                    'context_id': context_id,
                    'buffer': self.speaker_contexts[context_id]['buffer'].copy(),
                    'stats': self.get_speaker_stats(context_id)
                }
        return None 