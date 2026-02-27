# Rustification: mistral.rs as Canonical Inference Engine

**@SID:** `ARCH_RUSTIFICATION_V1`
**@Status:** ACTIVE
**@Date:** 2026-02-27
**@Supersedes:** llama-cpp-python as primary inference backend

---

## Decision

**mistral.rs** replaces **llama-cpp-python** as the universal local inference layer.

All Python scripts become thin HTTP clients consuming the OpenAI-compatible API
at `http://localhost:8080/v1/chat/completions`. No ML framework imports in
application code.

## Rationale

| Factor | llama-cpp-python (old) | mistral.rs (new) |
|--------|----------------------|-------------------|
| Language | Python bindings → C++ | Pure Rust + CUDA |
| Startup | Per-script model load (~30s) | Persistent server (preloaded) |
| Schema output | GBNF grammar | `response_format: json_schema` |
| Quantization | GGUF only | ISQ (any safetensor → Q4K/Q8 on load) |
| Model source | Local GGUF files only | Any HuggingFace model ID |
| Flash Attention | Manual compile flag | Built-in |
| Prefix caching | No | Yes (sequence-level) |
| Multi-request | Single-threaded per script | Concurrent server |
| Model swap | Kill script, reload | Server restart, cached weights |

## Architecture

```
┌──────────────────────────────────────────┐
│ mistral.rs serve (Rust, CUDA, FlashAttn) │
│ Port 8080 · ISQ Q4K · Prefix caching    │
└─────────────┬────────────────────────────┘
              │ OpenAI-compatible API
              │
   ┌──────────┼──────────────────────┐
   │          │                      │
   ▼          ▼                      ▼
Python     Browser UI           Any client
scripts    (apps/mistralrs-ui)  (curl, bun, rust)
   │
   └── scripts/mistralrs_client.py
       (stdlib urllib only, zero ML deps)
       │
       ├── local_refiner_v2.py  → chat_json() with schema
       ├── genre_extractor.py   → chat_json() with schema
       ├── benchmark scripts    → chat() with timing
       └── embed_ore.py         → separate concern (embeddings)
```

## Migration Path

### Phase 1: Parallel (NOW)
- mistral.rs serves dense models (Qwen2.5-7B, Phi-4, etc.) via ISQ
- `mistralrs_client.py` provides drop-in API
- Existing llama-cpp-python scripts still work for MoE models (Qwen3-30B-A3B)

### Phase 2: Migration
- Refactor `local_refiner_v2.py` to use `MistralRsClient` instead of `Llama`
- Refactor `genre_extractor.py` same way
- Refactor `benchmark_local_uncensored_lanes.py` same way
- Test with schema-constrained output on real overnight runs

### Phase 3: Deprecation
- Remove `llama-cpp-python` from `pyproject.toml`
- Remove local GGUF model loading code
- All inference through `localhost:8080`
- MoE support: tracked upstream (mistral.rs `indexed_moe_forward`)

## Known Limitations (v0.7.0)

| Issue | Impact | Workaround |
|-------|--------|------------|
| MoE `indexed_moe_forward` unimplemented | Qwen3-30B-A3B won't load | Use dense models with ISQ |
| IQ4_NL dtype unsupported | GPT-OSS-20B GGUF won't load | Use HF model ID + ISQ |
| Split GGUF parsing broken | Multi-file GGUF fails | Use HF model ID + ISQ |

**Key insight:** ISQ (In-Situ Quantization) bypasses all GGUF format issues.
Load any HF model by ID → mistral.rs downloads safetensors → quantizes on load.

## File Inventory

| File | Purpose |
|------|---------|
| `scripts/mistralrs_client.py` | Universal thin client (stdlib only) |
| `scripts/mistralrs_model_manager.py` | Server lifecycle CLI (start/stop/swap/search) |
| `scripts/install_mistralrs_cuda.ps1` | Build from source with CUDA (Codex-authored) |
| `apps/mistralrs-ui/index.html` | Browser chat UI with HF search |

## Commands

```bash
# Status check
python scripts/mistralrs_model_manager.py status

# Search HuggingFace models
python scripts/mistralrs_model_manager.py search "qwen 14b instruct"

# Start server with model
python scripts/mistralrs_model_manager.py start "Qwen/Qwen2.5-7B-Instruct"

# Swap to different model (stop + start)
python scripts/mistralrs_model_manager.py swap "microsoft/Phi-4-mini-instruct"

# Quick inference test
python scripts/mistralrs_model_manager.py ask "What is the meaning of life?"

# Client smoke test
python scripts/mistralrs_client.py
```

## Embeddings

`embed_ore.py` uses `sentence-transformers` for embeddings (Snowflake arctic-embed-xs).
This is a **separate concern** — mistral.rs is for text generation, not embeddings.
Embeddings stay in Python until a Rust embedding server is warranted.
