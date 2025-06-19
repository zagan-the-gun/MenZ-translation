#!/usr/bin/env python3
"""
MenZ翻訳サーバー セットアップスクリプト
依存関係のインストールと初期設定を行います
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_banner():
    """セットアップバナー表示"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║            MenZ翻訳サーバー セットアップ v0.1.0           ║
    ║               自動インストール・設定スクリプト             ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Python バージョンチェック"""
    print("Python バージョンを確認中...")
    version = sys.version_info
    
    if version.major != 3 or version.minor < 8:
        print(f"エラー: Python 3.8 以上が必要です (現在: {version.major}.{version.minor}.{version.micro})")
        print("https://www.python.org/downloads/ から最新版をダウンロードしてください")
        return False
    
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} - 対応しています")
    return True


def install_requirements():
    """依存関係をインストール"""
    print("\n" + "="*60)
    print("依存関係をインストール中...")
    print("="*60)
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("エラー: requirements.txt が見つかりません")
        return False
    
    try:
        # pip アップグレード
        print("pip をアップグレード中...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        
        # 依存関係インストール
        print("パッケージをインストール中...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        
        print("✓ 依存関係のインストールが完了しました")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"エラー: パッケージのインストールに失敗しました: {e}")
        return False


def create_directories():
    """必要なディレクトリを作成"""
    print("\n必要なディレクトリを作成中...")
    
    directories = [
        "config",
        "logs",
        "MenZTranslator"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ {directory} ディレクトリを作成しました")


def create_config_file():
    """設定ファイルを作成"""
    print("\nデフォルト設定ファイルを作成中...")
    
    config_path = Path("config/translator.ini")
    
    if config_path.exists():
        print("⚠ 設定ファイルが既に存在します。スキップしています。")
        return True
    
    # 設定ファイルを作成するため、Configクラスを一時的にインポート
    try:
        sys.path.insert(0, str(Path.cwd()))
        from MenZTranslator.config import Config
        
        # 設定インスタンス作成（自動的にデフォルト設定ファイルが作成される）
        config = Config()
        print("✓ デフォルト設定ファイルが作成されました")
        return True
        
    except Exception as e:
        print(f"エラー: 設定ファイルの作成に失敗しました: {e}")
        return False


def check_gpu_support():
    """GPU サポートをチェック"""
    print("\nGPU サポートを確認中...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✓ NVIDIA CUDA GPU が利用可能です: {gpu_name}")
            return "cuda"
        elif torch.backends.mps.is_available():
            print("✓ Apple Silicon MPS が利用可能です")
            return "mps"
        else:
            print("⚠ GPU が利用できません。CPU を使用します")
            return "cpu"
            
    except ImportError:
        print("⚠ PyTorch がインストールされていません")
        return "unknown"


def download_model():
    """モデルの事前ダウンロード"""
    print("\n" + "="*60)
    print("翻訳モデルを事前ダウンロード中...")
    print("初回は数GB のダウンロードが発生します。しばらくお待ちください...")
    print("="*60)
    
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        
        model_name = "facebook/nllb-200-distilled-1.3B"
        print(f"モデル: {model_name}")
        
        print("トークナイザーをダウンロード中...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        print("翻訳モデルをダウンロード中...")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        print("✓ モデルのダウンロードが完了しました")
        return True
        
    except Exception as e:
        print(f"エラー: モデルのダウンロードに失敗しました: {e}")
        print("インターネット接続を確認してください")
        return False


def main():
    """メインセットアップ処理"""
    try:
        print_banner()
        
        # Python バージョンチェック
        if not check_python_version():
            return False
        
        # ディレクトリ作成
        create_directories()
        
        # 依存関係インストール
        if not install_requirements():
            return False
        
        # 設定ファイル作成
        if not create_config_file():
            return False
        
        # GPU サポートチェック
        device = check_gpu_support()
        
        # モデルダウンロード
        if not download_model():
            print("⚠ モデルのダウンロードに失敗しましたが、セットアップは継続します")
            print("後で手動でダウンロードされます")
        
        # セットアップ完了
        print("\n" + "="*60)
        print("✓ セットアップが正常に完了しました！")
        print("="*60)
        print()
        print("次のステップ:")
        print("1. config/translator.ini を必要に応じて編集してください")
        print("2. python main.py でサーバーを起動してください")
        print()
        print(f"推奨デバイス: {device}")
        if device == "cpu":
            print("⚠ CPU使用のため処理速度が遅くなる可能性があります")
        print()
        
        return True
        
    except KeyboardInterrupt:
        print("\nセットアップが中断されました")
        return False
    except Exception as e:
        print(f"\nセットアップエラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print("セットアップ完了。何かキーを押してください...")
        input()
        sys.exit(0)
    else:
        print("セットアップに失敗しました。何かキーを押してください...")
        input()
        sys.exit(1) 