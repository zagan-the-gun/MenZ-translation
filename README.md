# MenZ翻訳サーバー

リアルタイム翻訳専用AI WebSocketサーバー

## 概要

Unity アプリケーションやその他のクライアントアプリケーション向けに、リアルタイム翻訳サービスを提供するローカルWebSocketサーバーです。

**主な特徴:**
- facebook/nllb-200-distilled-1.3B モデルを使用したオフライン翻訳
- WebSocket通信によるリアルタイム処理
- 多言語対応（200以上の言語）
- GPU/MPS/CPU 自動選択対応

## 機能

### ✅ 実装済み機能
- 基本的な多言語翻訳
- WebSocket通信インターフェース
- 優先度別リクエスト処理
- 自動設定ファイル生成
- ログ機能
- 統計情報取得API

### 🔄 開発予定機能
- プライオリティキュー実装
- バッチ処理最適化
- 翻訳品質向上のための追加学習
- REST API エンドポイント
- Web管理画面

## システム要件

- **Python**: 3.8 以上
- **メモリ**: 8GB以上推奨
- **GPU**: NVIDIA GPU (CUDA対応) またはApple Silicon推奨
- **ストレージ**: 5GB以上の空き容量

## インストール

### 自動インストール（推奨）

1. **プロジェクトをダウンロード**
   ```bash
   git clone https://github.com/yourusername/MenZ-translation.git
   cd MenZ-translation
   ```

2. **自動セットアップを実行**
   ```bash
   python setup.py
   ```

3. **サーバーを起動**
   ```bash
   python main.py
   ```

### 手動インストール

1. **依存関係をインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **必要なディレクトリを作成**
   ```bash
   mkdir -p config logs
   ```

3. **設定ファイルを作成**
   ```bash
   python -c "from MenZTranslator import Config; Config()"
   ```

## 設定

設定ファイル `config/translator.ini` を編集して、サーバーの動作をカスタマイズできます。

### 主要設定

```ini
[SERVER]
host = 127.0.0.1
port = 55001
max_connections = 50

[TRANSLATION]
model_name = facebook/nllb-200-distilled-1.3B
device = auto  # auto, cpu, cuda, mps
max_length = 256

[LOGGING]
level = INFO
file = logs/translator.log
```

## 使用方法

### WebSocket接続

```javascript
const ws = new WebSocket('ws://127.0.0.1:55001');
```

### 翻訳リクエスト

```json
{
    "request_id": "unique-request-id",
    "priority": "high",
    "text": "Hello, how are you?",
    "source_lang": "eng_Latn",
    "target_lang": "jpn_Jpan"
}
```

### レスポンス

```json
{
    "request_id": "unique-request-id",
    "translated": "こんにちは、元気ですか？",
    "processing_time_ms": 250.5,
    "status": "completed"
}
```

## 言語コード

### 主要言語

| 言語 | コード |
|------|--------|
| 日本語 | jpn_Jpan |
| 英語 | eng_Latn |
| 中国語（簡体字） | zho_Hans |
| 中国語（繁体字） | zho_Hant |
| 韓国語 | kor_Hang |
| フランス語 | fra_Latn |
| ドイツ語 | deu_Latn |
| スペイン語 | spa_Latn |

## Unity での使用例

```csharp
using System;
using System.Threading.Tasks;
using UnityEngine;
using WebSocketSharp;

public class MenZTranslationClient : MonoBehaviour
{
    private WebSocket ws;
    
    void Start()
    {
        ws = new WebSocket("ws://127.0.0.1:55001");
        ws.Connect();
    }
    
    public async Task<string> TranslateAsync(string text)
    {
        var request = new
        {
            request_id = Guid.NewGuid().ToString(),
            text = text,
            source_lang = "eng_Latn",
            target_lang = "jpn_Jpan"
        };
        
        ws.Send(JsonUtility.ToJson(request));
        
        // レスポンス待機処理
        // ...
        
        return translatedText;
    }
}
```



## トラブルシューティング

### GPU が認識されない
- CUDAドライバーが正しくインストールされているか確認
- `nvidia-smi` コマンドでGPUの状態確認

### 翻訳が遅い
- `config/translator.ini` の `device` を `cuda` または `mps` に設定
- `max_length` の値を下げる

### 接続エラー
- ファイアウォールの設定を確認
- ポート番号が使用されていないか確認

## 開発者向け情報

### プロジェクト構造

```
MenZ-translation/
├── MenZTranslator/              # メインパッケージ
│   ├── __init__.py
│   ├── translator.py            # 翻訳エンジン
│   ├── context_manager.py       # 文脈管理
│   ├── websocket_server.py      # WebSocketサーバー
│   └── config.py               # 設定管理
├── config/
│   └── translator.ini          # 設定ファイル
├── logs/                       # ログファイル
├── main.py                     # エントリーポイント
├── setup.py                    # セットアップスクリプト
├── requirements.txt            # 依存関係
└── README.md                   # このファイル
```

### API エンドポイント

- `type: "translation"` - 翻訳リクエスト
- `type: "ping"` - 接続確認
- `type: "stats"` - 統計情報取得

## ライセンス

MIT License

## 参考プロジェクト

- [YukariWhisper](https://github.com/tyapa0/YukariWhisper) - ゆかりねっと用のFaster-Whisper音声認識エンジン
- [NLLB](https://github.com/facebookresearch/fairseq/tree/nllb) - Facebook の多言語翻訳モデル

## 貢献

プルリクエストやイシューの報告を歓迎します。

## サポート

問題が発生した場合は、GitHub Issues でお知らせください。
