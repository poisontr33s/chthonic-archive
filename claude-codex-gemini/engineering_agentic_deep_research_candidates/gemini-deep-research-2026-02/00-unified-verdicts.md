---
type: research-index
source: claude-codex-gemini/sessionANDresearch.md (181KB, 1556 lines)
created: 2026-02-13
status: structured
---

# Gemini Deep Research Index — February 2026

> Extracted and structured from the monolithic Gemini session log.
> Original preserved at: `claude-codex-gemini/sessionANDresearch.md`

---

## Research Outputs (7 Documents)

| # | File | Topic | Source | Priority |
|---|------|-------|--------|----------|
| 1 | `01-local-llm-inference-stack.md` | ExLlamaV2 vs TensorRT-LLM vs llama.cpp vs vLLM | Gemini session | HIGH |
| 2 | `02-rustified-polyglot-daemon.md` | Elixir+Rust daemon, mailbox pattern, mistral.rs, Qdrant, MCP bundles | Gemini session | HIGH |
| 3 | `03-api-gateways-and-vector-dbs.md` | TensorZero/Bifrost (Rust/Go gateways), GPT-OSS 20B deep dive, Qdrant benchmarks | Gemini session | MEDIUM |
| 4 | `04-ruby-4-and-oxidized-toolchains.md` | Ruby 4.0.1, ZJIT, rv (Rust Ruby manager), brush shell, uutils | Gemini session | LOW |
| 5 | `05-batch-classification-infrastructure.md` | Full Win11 RTX 4090 batch classification architecture (321 lines) | Gemini research-dump002 | HIGH |
| 6 | `06-field-tested-corrections-and-frontier.md` | **Research vs reality corrections**, LocalAI/Dola.ai analysis, upgrade path | Claude live testing | **CRITICAL** |
| 7 | `00-unified-verdicts.md` | Consolidated verdicts & trajectory alignment (THIS FILE) | — | — |

---

## Consolidated Verdicts (Updated with ALL Research)

### Engine Stack (Final Answer)

| Tier | Engine | Model | VRAM | Speed | Status |
|------|--------|-------|------|-------|--------|
| **Recommended** | ExLlamaV2 | Llama-3.1-8B EXL2 6.0bpw | ~6.5GB | Fast | Native Win11, Py 3.13 ✅ |
| **Upgrade path** | mistral.rs | GPT-OSS 20B (MoE, MXFP4) | ~13.7GB | 42 tok/s | Pure Rust, 16GB champion |
| **High-perf alt** | TensorRT-LLM | Any supported | Varies | 30-70% faster | Complex setup, rigid |
| **Fallback** | llama-cpp-python | GGUF Q4_K_M | ~5GB | Moderate | Community wheels NOW available for Py 3.13 |
| **Server-grade** | vLLM (native Win) | Any | Varies | Best batch throughput | PR #14891 upstream, experimental |

### API Gateway (If Needed Later)

| Gateway | Language | Latency | Throughput | Use Case |
|---------|----------|---------|------------|----------|
| **TensorZero** | Rust | 0.37ms mean | 10,000 QPS | Multi-model routing |
| **Bifrost** | Go | 11µs overhead | 5,000 RPS | Ultra-low latency |
| **Helicone** | Rust | 8ms P50 | Scalable | Observability focus |
| ~~LiteLLM~~ | Python | Crashes >1K QPS | — | **AVOID** |

### Vector Database

| Engine | Language | Latency | Filter Overhead | Verdict |
|--------|----------|---------|----------------|---------|
| **Qdrant** | Rust | 1ms P99 | 1.1x | ✅ Recommended |
| pgvector | C (PostgreSQL) | 2.48ms | 2.3x | Good baseline, degrades with filters |

### Models for 16GB VRAM (Ranked)

| Model | Params | Active/Token | VRAM | Speed | Quality |
|-------|--------|-------------|------|-------|---------|
| **GPT-OSS 20B** | 21B MoE | 3.6B | 13.7GB | 42 t/s | Frontier-class |
| **Gemma-3 12B QAT** | 12B | 12B | ~14GB | ~30 t/s | Google optimized |
| Llama-3.1-8B (EXL2 6.0) | 8B | 8B | 6.5GB | ~35 t/s | Good, more headroom |
| Llama-3.1-8B (Q4_K_M) | 8B | 8B | 5GB | ~30 t/s | Acceptable quality |

### Framework Decision

**Raw API wins.** No LangChain needed for classification tasks. Current `hf_refiner.py` pattern (direct HTTP to chat/completions) maps 1:1 to local backends.

### Uncensored/Privacy Models

| Model | Source | Notes |
|-------|--------|-------|
| **GPT-OSS 20B** | OpenAI (open weights) | Open-weight, locally deployable, no content filtering |
| **PrivateGPT** | Private ecosystem | Full RAG pipeline, local-only, document QA |
| **Gemma-3** | Google | Uncensored variants available on HF |
| **DeepSeek** | DeepSeek AI | Referenced but not deeply benchmarked in this research |

### Ruby 4.0 Ecosystem (Side Discovery)

| Tool | What It Does | Win11 Status |
|------|-------------|-------------|
| **Ruby 4.0.1** | Latest stable, ZJIT experimental | `winget install "Ruby 4.0"` ✅ |
| **rv** (Rust) | Ruby version manager (like uv for Ruby) | Win support in development |
| **ZJIT** | Next-gen Rust JIT compiler for Ruby | Experimental, `--zjit` flag |
| **brush** | Rust bash-compatible shell | Experimental Win support |
| **uutils coreutils** | Rust GNU coreutils replacement | Cross-platform ✅ |

### Windows MCP Infrastructure

| Component | Status | Command |
|-----------|--------|---------|
| On-Device Agent Registry | Available | `odr.exe` |
| MCP Bundle format | Standardized | `.mcpb` (ZIP + manifest.json v0.3) |
| Server registration | Working | `odr mcp add <manifest>` |
| Proxy auth | Built-in | Prevents token passthrough |

### Dola.ai / Voice Scheduling

Gemini proposed a **fully local voice assistant** as Dola.ai alternative:
- STT: Parakeet V3 or Whisper (local)
- LLM: Qwen3 Omni or quantized Llama via mistral.rs
- TTS: Pocket-TTS or Kokoro (minimal CPU)
- Transport: LiveKit or Pipecat (WebRTC, VAD, barge-in)
- **Status:** Aspirational — not an immediate priority

---

## What Answers Our Trajectory

| Original Question | Answered? | Where |
|------------------|-----------|-------|
| Q1: Local LLM engine | ✅ ExLlamaV2 → GPT-OSS 20B upgrade | 01, 03 |
| Q2: Framework needed? | ✅ No, raw API sufficient | 01, 02 |
| Q3: ONNX GenAI? | ✅ Dead end (Py 3.12 max) | 01 |
| Q4: Task Scheduler | Partially — PowerShell scheduled task | 02 |
| Uncensored models? | ✅ GPT-OSS 20B is open-weight | 03 |
| PrivateGPT? | ✅ Referenced, local RAG focus | 02 |
| Dola.ai alternative? | ✅ Full local voice pipeline proposed | 02 |
| Ruby 4 status? | ✅ Comprehensive analysis | 04 |
| LocalAI? | Referenced as TTS/inference backend | 02 |
| DeepSeek? | Referenced in benchmarks | 03 |

---

## Immediate Implementation Path

```
1. Install PyTorch CUDA 12.4:  uv pip install torch --torch-backend=cu124
2. Install ExLlamaV2:          uv pip install exllamav2 (or from source)
3. Download model:             Llama-3.1-8B-Instruct-EXL2-6.0bpw (~6.5GB)
4. Write local_refiner.py:     Replace HF API calls with ExLlamaV2 inference
5. Add -Local flag:            run_archaeology.ps1 for fully air-gapped runs
6. Validate:                   22-domain classification, compare vs HF API quality
```

### Future Upgrade (When Validated)
```
7. Install mistral.rs:         cargo install (pure Rust)
8. Download GPT-OSS 20B:       MXFP4 quantized (~13.7GB)
9. Swap backend:               ExLlamaV2 → mistral.rs for better quality
10. Add Qdrant:                Historical baseline tracking
```
