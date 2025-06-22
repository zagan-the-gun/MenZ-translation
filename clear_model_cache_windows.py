#!/usr/bin/env python3
"""
Windows用 Hugging Face モデルキャッシュクリアスクリプト
"""

import os
import shutil
import sys
from pathlib import Path

def clear_huggingface_cache():
    """Hugging Faceのキャッシュをクリアする"""
    print("="*60)
    print("Hugging Face キャッシュクリア (Windows)")
    print("="*60)
    
    # Windows のキャッシュディレクトリ
    user_profile = os.environ.get('USERPROFILE')
    if not user_profile:
        print("エラー: USERPROFILE環境変数が見つかりません")
        return False
    
    cache_dirs = [
        os.path.join(user_profile, '.cache', 'huggingface'),
        os.path.join(user_profile, '.cache', 'transformers'),
        # 環境変数で指定されている場合
        os.environ.get('HF_HOME'),
        os.environ.get('TRANSFORMERS_CACHE')
    ]
    
    # Noneを除去
    cache_dirs = [d for d in cache_dirs if d is not None]
    
    print("チェック対象のキャッシュディレクトリ:")
    for cache_dir in cache_dirs:
        print(f"  - {cache_dir}")
    
    print()
    
    deleted_dirs = []
    total_freed_space = 0
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            print(f"📁 {cache_dir}")
            
            # サイズを計算
            dir_size = get_dir_size(cache_dir)
            print(f"   サイズ: {dir_size / (1024*1024*1024):.2f} GB")
            
            # NLLBモデルを特定
            nllb_dirs = find_nllb_models(cache_dir)
            if nllb_dirs:
                print(f"   見つかったNLLBモデル: {len(nllb_dirs)}個")
                for nllb_dir in nllb_dirs:
                    print(f"     - {os.path.basename(nllb_dir)}")
            
            # 削除確認
            response = input(f"\n❓ {cache_dir} を削除しますか？ (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                try:
                    print(f"🗑️  削除中: {cache_dir}")
                    shutil.rmtree(cache_dir)
                    print(f"✅ 削除完了")
                    deleted_dirs.append(cache_dir)
                    total_freed_space += dir_size
                except Exception as e:
                    print(f"❌ 削除エラー: {e}")
            else:
                print("⏭️  スキップしました")
        else:
            print(f"📁 {cache_dir} (存在しません)")
    
    print()
    print("="*60)
    print("クリア結果:")
    print(f"  削除したディレクトリ数: {len(deleted_dirs)}")
    print(f"  解放された容量: {total_freed_space / (1024*1024*1024):.2f} GB")
    
    if deleted_dirs:
        print("\n削除されたディレクトリ:")
        for deleted_dir in deleted_dirs:
            print(f"  ✓ {deleted_dir}")
        
        print("\n📝 注意:")
        print("  - 次回のモデル読み込み時に再ダウンロードが発生します")
        print("  - インターネット接続が必要です")
        print("  - ダウンロードには時間がかかる場合があります")
    
    return len(deleted_dirs) > 0

def get_dir_size(directory):
    """ディレクトリのサイズを取得"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception:
        pass
    return total_size

def find_nllb_models(cache_dir):
    """NLLBモデルのディレクトリを検索"""
    nllb_dirs = []
    try:
        transformers_cache = os.path.join(cache_dir, 'transformers')
        if os.path.exists(transformers_cache):
            for item in os.listdir(transformers_cache):
                item_path = os.path.join(transformers_cache, item)
                if os.path.isdir(item_path) and 'nllb' in item.lower():
                    nllb_dirs.append(item_path)
    except Exception:
        pass
    return nllb_dirs

def create_test_translation():
    """キャッシュクリア後のテスト翻訳"""
    print("\n" + "="*60)
    print("テスト翻訳実行")
    print("="*60)
    
    try:
        # プロジェクトルートをパスに追加
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from MenZTranslator import Config, NLLBTranslator
        
        print("モデルを再読み込み中...")
        config = Config()
        translator = NLLBTranslator(
            model_name=config.model_name,
            device=config.device,
            gpu_id=config.gpu_id
        )
        
        # テスト翻訳
        test_cases = [
            "どうしようかな",
            "困った", 
            "助けて"
        ]
        
        print("\nテスト結果:")
        for text in test_cases:
            result = translator.translate(
                text=text,
                source_lang="jpn_Jpan",
                target_lang="eng_Latn"
            )
            print(f"  '{text}' → '{result}'")
            
            if "car" in result.lower() or "auto" in result.lower():
                print(f"    ⚠️  まだ車関連の問題があります")
        
        print("\nテスト完了")
        
    except Exception as e:
        print(f"テストエラー: {e}")

if __name__ == "__main__":
    print("Windows用 Hugging Face キャッシュクリアツール")
    print("\n⚠️  重要:")
    print("  - このツールはモデルキャッシュを削除します")
    print("  - 削除後は再ダウンロードが必要です")
    print("  - 数GB のダウンロードが発生する可能性があります")
    
    response = input("\n続行しますか？ (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        cache_cleared = clear_huggingface_cache()
        
        if cache_cleared:
            test_response = input("\nキャッシュクリア後にテスト翻訳を実行しますか？ (y/N): ").strip().lower()
            if test_response in ['y', 'yes']:
                create_test_translation()
    else:
        print("キャンセルしました") 