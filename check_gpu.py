#!/usr/bin/env python3
"""
GPU使用状況確認スクリプト
MenZ翻訳サーバーでGPUが使用できるかチェックします
"""

import torch
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from MenZTranslator import Config

def check_gpu_status():
    """GPU使用状況を確認"""
    print("=" * 60)
    print("    MenZ翻訳サーバー GPU使用状況チェック")
    print("=" * 60)
    print()
    
    # PyTorchの基本情報
    print(f"PyTorchバージョン: {torch.__version__}")
    print(f"CUDA利用可能: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDAバージョン: {torch.version.cuda}")
        print(f"cuDNNバージョン: {torch.backends.cudnn.version()}")
        print(f"GPU数: {torch.cuda.device_count()}")
        print()
        
        # 各GPUの詳細情報
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}:")
            print(f"  名前: {torch.cuda.get_device_name(i)}")
            
            # メモリ情報
            memory_allocated = torch.cuda.memory_allocated(i) / 1024**3  # GB
            memory_cached = torch.cuda.memory_reserved(i) / 1024**3      # GB
            memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3  # GB
            
            print(f"  総メモリ: {memory_total:.1f} GB")
            print(f"  使用中メモリ: {memory_allocated:.1f} GB")
            print(f"  キャッシュメモリ: {memory_cached:.1f} GB")
            print()
    else:
        print("CUDA GPUが利用できません")
        print()
    
    # 設定ファイルの確認
    try:
        config = Config()
        print("設定ファイル確認:")
        print(f"  設定されたデバイス: {config.device}")
        print(f"  設定されたGPU ID: {config.gpu_id}")
        print(f"  モデル名: {config.model_name}")
        print()
        
        # 実際に使用されるデバイスをテスト
        from MenZTranslator.translator import NLLBTranslator
        
        print("翻訳エンジンでのデバイス確認:")
        translator = NLLBTranslator(config.model_name, config.device, config.gpu_id)
        print(f"  実際に使用されるデバイス: {translator.device}")
        
        # 簡単な翻訳テスト
        print()
        print("翻訳テスト実行中...")
        test_result = translator.translate("Hello", "eng_Latn", "jpn_Jpan")
        print(f"  テスト結果: Hello → {test_result}")
        
    except Exception as e:
        print(f"設定確認エラー: {e}")
    
    print("=" * 60)
    print("チェック完了")
    print("=" * 60)

if __name__ == "__main__":
    check_gpu_status() 