# GPU選択機能

MenZ翻訳サーバーは複数のGPUがある環境で、特定のGPUを指定して使用することができます。

## 設定方法

`config/translator.ini` ファイルの `[TRANSLATION]` セクションで以下のパラメータを設定してください：

```ini
[TRANSLATION]
model_name = facebook/nllb-200-distilled-1.3B
device = cuda
gpu_id = 0          # 使用するGPUのID (0, 1, 2, ...)
max_length = 256
use_fp16 = true     # FP16（半精度）を使用（メモリ削減・高速化）
use_context = true
```

## パラメータ説明

### `device`
- `auto`: 自動選択（MPS > CUDA > CPU の優先順位）
- `cuda`: NVIDIA CUDA GPUを使用
- `cpu`: CPUを使用
- `mps`: Apple Silicon MPS を使用（macOS のみ）

### `gpu_id`
- 使用するGPUのID番号を指定（0から開始）
- `device=cuda` または `device=auto` でCUDAが選択された場合に有効
- 指定したGPU IDが存在しない場合は、GPU 0 にフォールバックします

### `use_fp16`
- FP16（半精度浮動小数点）を使用するかどうか
- `true`: メモリ使用量を約50%削減し、推論速度を向上
- CUDA GPUでのみ有効（CPUやMPSでは自動的にFP32にフォールバック）
- 翻訳品質は若干低下する可能性があります

## 使用例

### GPU 0を使用
```ini
device = cuda
gpu_id = 0
```

### GPU 1を使用
```ini
device = cuda
gpu_id = 1
```

### 自動選択（指定したGPU IDを優先）
```ini
device = auto
gpu_id = 1
```

## 動作確認

GPU選択が正しく動作しているかを確認するには：

1. `check_gpu.py` スクリプトを実行
```bash
python check_gpu.py
```

2. ログファイルで使用デバイスを確認
```
NVIDIA CUDA GPU 1 を使用します: NVIDIA GeForce RTX 3080
```

3. WebSocket接続時のレスポンスで確認
```json
{
  "server_info": {
    "device": "cuda:1",
    "gpu_id": 1,
    ...
  }
}
```

## 注意事項

- GPU IDは0から始まります（GPU 0, GPU 1, GPU 2, ...）
- 指定したGPU IDが存在しない場合は、GPU 0 が使用されます
- `device=cpu` の場合、`gpu_id` 設定は無視されます
- GPU メモリが不足している場合は、より小さな`max_length`を設定することを推奨します 