#!/usr/bin/env python3
"""
モデルキャッシュとファイル状態をチェックするスクリプト
"""

import os
import sys
from pathlib import Path
import hashlib

# プロジェクトルートをパスに追加  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_model_cache():
    """モデルキャッシュの状態をチェック"""
    print("="*60)
    print("モデルキャッシュチェック")
    print("="*60)
    
    # Hugging Face キャッシュディレクトリの確認
    hf_cache_dir = os.path.expanduser("~/.cache/huggingface")
    print(f"Hugging Face キャッシュディレクトリ: {hf_cache_dir}")
    
    if os.path.exists(hf_cache_dir):
        print(f"  ✓ キャッシュディレクトリ存在")
        
        # transformersキャッシュ
        transformers_cache = os.path.join(hf_cache_dir, "transformers")
        if os.path.exists(transformers_cache):
            dirs = [d for d in os.listdir(transformers_cache) if os.path.isdir(os.path.join(transformers_cache, d))]
            print(f"  Transformersキャッシュ内のモデル数: {len(dirs)}")
            
            # NLLBモデルを検索
            nllb_models = [d for d in dirs if "nllb" in d.lower()]
            print(f"  NLLBモデル: {len(nllb_models)}個")
            for model in nllb_models:
                print(f"    - {model}")
                
                model_dir = os.path.join(transformers_cache, model)
                if os.path.exists(model_dir):
                    files = os.listdir(model_dir)
                    config_files = [f for f in files if f.startswith("config")]
                    model_files = [f for f in files if f.endswith(".bin") or f.endswith(".safetensors")]
                    
                    print(f"      設定ファイル: {len(config_files)}個")
                    print(f"      モデルファイル: {len(model_files)}個")
                    
                    # ファイルサイズの確認
                    total_size = 0
                    for file in files:
                        file_path = os.path.join(model_dir, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            total_size += size
                    
                    print(f"      総サイズ: {total_size / (1024*1024*1024):.2f} GB")
    else:
        print("  ✗ キャッシュディレクトリが見つかりません")
    
    print()
    print("-" * 60)
    
    # 環境変数の確認
    print("環境変数:")
    hf_cache_env = os.environ.get('HF_HOME')
    transformers_cache_env = os.environ.get('TRANSFORMERS_CACHE')
    
    print(f"  HF_HOME: {hf_cache_env}")
    print(f"  TRANSFORMERS_CACHE: {transformers_cache_env}")
    
    print()
    print("-" * 60)
    
    # 実際にモデルを読み込んで確認
    print("実際のモデル読み込みテスト:")
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        model_name = "facebook/nllb-200-distilled-1.3B"
        print(f"モデル名: {model_name}")
        
        # トークナイザー読み込み
        print("トークナイザー読み込み中...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # モデル読み込み
        print("モデル読み込み中...")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        print(f"  ✓ 読み込み成功")
        print(f"  モデルクラス: {type(model).__name__}")
        print(f"  パラメータ数: {model.num_parameters():,}")
        
        # モデルの設定情報
        config = model.config
        print(f"  モデル設定:")
        print(f"    - アーキテクチャ: {config.architectures}")
        print(f"    - 語彙サイズ: {config.vocab_size}")
        print(f"    - モデル名: {getattr(config, '_name_or_path', 'N/A')}")
        
        # 簡単な翻訳テスト（問題の再現テスト）
        print("\n問題再現テスト:")
        test_text = "どうしようかな"
        tokenizer.src_lang = "jpn_Jpan"
        
        inputs = tokenizer(test_text, return_tensors="pt")
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn"),
            max_length=256,
            num_beams=4,
            early_stopping=True,
            do_sample=False
        )
        
        translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        print(f"  '{test_text}' → '{translation}'")
        
        if "car" in translation.lower():
            print("  ⚠️  車関連の問題が再現されました！")
        else:
            print("  ✓ 正常な翻訳です")
        
    except Exception as e:
        print(f"  ✗ エラー: {e}")
    
    print()
    print("チェック完了")

if __name__ == "__main__":
    check_model_cache() 