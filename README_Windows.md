# MenZ翻訳サーバー - Windows版セットアップガイド

## 🚀 簡単セットアップ（推奨）

### 1. 前提条件
- **Python 3.8以上** がインストール済み
  - [Python公式サイト](https://www.python.org/downloads/windows/)からダウンロード
  - インストール時に「**Add Python to PATH**」にチェック ✅

### 2. セットアップ
1. **setup.bat** をダブルクリック
2. 指示に従って待機（初回は数分かかります）
3. 「セットアップが完了しました！」と表示されたら完了

### 3. サーバー起動
- **run.bat** をダブルクリック
- ブラウザで `ws://127.0.0.1:55001` に接続可能

---

## ⚡ GPU高速化（オプション）

NVIDIA GPU搭載PCの場合、翻訳を高速化できます：

1. **install_gpu.bat** をダブルクリック
2. 「y」で確認してインストール
3. 次回起動時からGPU使用

**注意**: GeForce GTX 1060以上を推奨

---

## 📁 ファイル構成

```
MenZ-translation/
├── setup.bat          ← 初回セットアップ
├── run.bat             ← サーバー起動
├── install_gpu.bat     ← GPU対応（オプション）
├── config/
│   └── translator.ini  ← 設定ファイル
└── logs/
    └── translator.log  ← ログファイル
```

---

## ⚙️ 設定カスタマイズ

`config\translator.ini` を編集：

```ini
[SERVER]
port = 55001            # ポート番号変更

[TRANSLATION]
device = cpu            # cpu, cuda, auto
max_length = 128        # 翻訳文字数上限

[LOGGING]
level = INFO            # DEBUG, INFO, WARNING
```

---

## 🔧 トラブルシューティング

### よくある問題

| 問題 | 解決方法 |
|------|----------|
| Pythonが見つからない | PATHに追加されているか確認 |
| ポートエラー | 他のアプリが55001番を使用 |
| 翻訳が遅い | `install_gpu.bat` でGPU対応 |
| メモリ不足 | `device = cpu` に変更 |

### エラーログ確認
```
logs\translator.log
```

### 完全リセット
1. `venv` フォルダを削除
2. `setup.bat` を再実行

---

## 🌐 WebSocket接続例

### JavaScript
```javascript
const ws = new WebSocket('ws://127.0.0.1:55001');

ws.send(JSON.stringify({
    "request_id": "test1",
    "text": "Hello, world!",
    "source_lang": "eng_Latn",
    "target_lang": "jpn_Jpan"
}));
```

### Unity (C#)
```csharp
var ws = new WebSocket("ws://127.0.0.1:55001");
ws.Connect();
```

---

## 🔥 パフォーマンス調整

### 高速化設定
```ini
[TRANSLATION]
device = cuda           # GPU使用
max_length = 64         # 短文用
use_fp16 = true         # FP16（半精度）使用（メモリ削減・高速化）
use_context = false     # 文脈無効

[SERVER]
max_connections = 5     # 接続数制限
```

### 高精度設定
```ini
[TRANSLATION]
max_length = 512        # 長文対応
use_context = true      # 文脈有効

[CONTEXT]
max_context_per_speaker = 10
```

---

## 📞 サポート

- **問題報告**: GitHub Issues
- **ログファイル**: `logs\translator.log`
- **設定確認**: `config\translator.ini`

**動作確認済み環境**:
- Windows 10/11
- Python 3.8-3.12
- NVIDIA GeForce GTX 1060以上（GPU使用時） 