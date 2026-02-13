---
type: deep-research-output
source: claude-codex-gemini/sessionANDresearch.md (lines 1-872)
researcher: gemini-pro-3
iterations: 3 (initial → Python 3.13 correction → final with benchmarks)
created: 2026-02-11
topic: local-llm-inference
---

# Research 1: Local LLM Inference Stack for Win11 RTX 4090 (16GB)

## Executive Summary

ExLlamaV2 is the recommended inference engine for native Win11 + Python 3.13 + RTX 4090 Laptop (16GB VRAM). It offers EXL2 variable-bitrate quantization for precise VRAM tuning, native Windows execution without WSL2, and Python 3.13 compatibility.

## Engine Comparison

| Engine | Win11 Native | Python 3.13 | VRAM Efficiency | Speed | Verdict |
|--------|-------------|-------------|-----------------|-------|---------|
| **ExLlamaV2** | ✅ | ✅ | Excellent (EXL2 6.0bpw) | High | **RECOMMENDED** |
| TensorRT-LLM | ✅ (complex) | Build required | Best | 30-70% faster | Runner-up (rigid setup) |
| llama-cpp-python | ✅ (wheels) | ✅ (community wheels) | Good (GGUF) | Moderate | Fallback only |
| vLLM | WSL2 required | ✅ | Good (PagedAttention) | Best batch | Avoid on Win11 |
| ONNX RT GenAI | ✅ | ❌ (Py 3.12 max) | Unknown | Unknown | Dead end |

## Hardware Reality: RTX 4090 Laptop ≠ Desktop

- **Die:** AD103 (not AD102) — closer to desktop RTX 4080
- **VRAM:** 16GB GDDR6 (not 24GB GDDR6X)
- **Bandwidth:** ~576 GB/s (not 1,008 GB/s) — **43% slower memory**
- **Usable VRAM:** ~14.5GB after Win11 DWM overhead (0.8-1.5GB)
- **Implication:** FP16 models (16GB weights alone) are IMPOSSIBLE. Quantization is mandatory.

## VRAM Budget for Llama-3-8B

| Quantization | Weight Size | Headroom for KV Cache | Feasible? |
|-------------|------------|----------------------|-----------|
| FP16 | ~16.0 GB | None | ❌ Impossible |
| 8-bit (Q8) | ~8.5 GB | ~6 GB | ✅ Feasible |
| EXL2 6.0bpw | ~6.5 GB | ~8 GB | ✅ **Optimal** |
| 4-bit (Q4) | ~5.0 GB | ~9.5 GB | ✅ Excellent headroom |

## Installation (ExLlamaV2)

```powershell
# 1. PyTorch with CUDA 12.4
uv pip install torch torchvision torchaudio --torch-backend=cu124
uv pip install pandas tqdm numpy safetensors

# 2. ExLlamaV2 (requires VS 2022 Build Tools + "Desktop dev with C++")
uv pip install https://github.com/turboderp/exllamav2/archive/master.zip --no-build-isolation
```

## Key Model: Llama-3.1-8B-Instruct-EXL2-6.0bpw

- ~6.5GB VRAM for weights
- Leaves ~8GB for KV cache and batching
- 8192 context window with batch size 8
- Optimal balance between quality and VRAM

## Python 3.13 Compatibility Notes

- **PyTorch:** ✅ Source builds and nightly wheels work
- **ExLlamaV2:** ✅ Builds against PyTorch, no C++ standard issues
- **llama-cpp-python:** ❌ MSVC compilation fails (C2039/C3083 errors). Community pre-compiled wheels now available from `dougeeai/llama-cpp-python-wheels`
- **ONNX RT GenAI:** ❌ Official wheels only Python ≤3.12
- **uv:** ✅ `--torch-backend=auto` or `--torch-backend=cu124` handles CUDA resolution

## Code Skeleton (ExLlamaV2 Batch Processor)

See source document lines 742-871 for full production-grade batch processor code.
Key pattern:
```python
from exllamav2 import ExLlamaV2, ExLlamaV2Config, ExLlamaV2Cache, ExLlamaV2Tokenizer
from exllamav2.generator import ExLlamaV2DynamicGenerator

config = ExLlamaV2Config(MODEL_PATH)
config.max_seq_len = 8192
config.max_batch_size = 8

model = ExLlamaV2(config)
model.load(gpu_split=[16.0])
cache = ExLlamaV2Cache(model, max_seq_len=8192, lazy=True)
generator = ExLlamaV2DynamicGenerator(model=model, cache=cache, tokenizer=tokenizer)

outputs = generator.generate(prompt=batch_prompts, max_new_tokens=512, add_bos=False)
```

## Thermal Warning

Overnight batch processing (8500+ files) = sustained GPU load. RTX 4090 Laptop shares heat pipes between CPU and GPU. Monitor for thermal throttling during extended runs.
