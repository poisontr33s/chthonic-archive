---
type: research-digest
from: gemini-pro-3-deep-research
to: copilot-cli + codex + claude
created: 2026-02-12
source: claude-codex-gemini/sessionANDresearch.md
scope: infrastructure verdicts
---

# ☥ Gemini Deep Research Digest — Structured Verdicts

> Extracted from iterative Gemini Pro 3 session (2026-02-11/12).
> Original: `claude-codex-gemini/sessionANDresearch.md` (1556 lines, ~181KB)
> **Structured outputs:** `gemini-deep-research-2026-02/` (5 files)

---

## ★ Structured Research Files

| File | Topic |
|------|-------|
| `gemini-deep-research-2026-02/00-unified-verdicts.md` | Consolidated verdicts, trajectory alignment, implementation path |
| `gemini-deep-research-2026-02/01-local-llm-inference-stack.md` | ExLlamaV2 vs all engines, VRAM budgets, code skeleton |
| `gemini-deep-research-2026-02/02-rustified-polyglot-daemon.md` | Elixir/BEAM daemon, MCP bundles, Dola.ai voice alt, mailbox validation |
| `gemini-deep-research-2026-02/03-api-gateways-and-vector-dbs.md` | TensorZero/Bifrost benchmarks, GPT-OSS 20B deep dive, Qdrant |
| `gemini-deep-research-2026-02/04-ruby-4-and-oxidized-toolchains.md` | Ruby 4.0.1, ZJIT, rv, brush, uutils |

---

## Research Phase Summary

The session ran **3 research iterations** on Q1 (local LLM stack), each refining the previous:
1. Initial deep research → raw engine comparison
2. User-corrected with Python 3.13/uv/Rustification context → updated report
3. Final deep research with Rust API gateway + Qdrant + ecosystem updates → comprehensive architecture

**Q2–Q4** from the original brief were NOT run as separate deep researches — instead, the session organically expanded into a full architectural blueprint covering all questions plus several we hadn't asked.

---

## VERDICT 1: Local LLM Inference Engine

### ✅ Recommended: ExLlamaV2

| Factor | Value |
|--------|-------|
| **Why** | Native Windows, Python 3.13 compatible, EXL2 variable-bitrate quantization, no WSL2 needed |
| **VRAM** | ~6.5GB for Llama-3.1-8B at 6.0bpw EXL2 (leaves ~8GB for KV cache + batching) |
| **Speed** | Competitive with TensorRT-LLM for batch workloads on consumer GPUs |
| **Install** | `uv pip install https://github.com/turboderp/exllamav2/archive/master.zip --no-build-isolation` |
| **Prereq** | VS 2022 Build Tools with "Desktop development with C++" |
| **Model** | `Llama-3.1-8B-Instruct-EXL2-6.0bpw` from HuggingFace |

### Runner-up: TensorRT-LLM
- 30–70% faster than llama.cpp (blazing fast)
- ~30% less RAM, ~25% smaller compiled models
- BUT: rigid environment, complex compilation, less portable

### Runner-up (NEW): mistral.rs
- Pure Rust inference engine
- Can serve GPT-OSS 20B (21B MoE, only 3.6B active/token)
- MXFP4 quantization → ~13.7GB VRAM, 42 tok/s at 60K context
- Excellent for larger models that still fit 16GB

### Avoid: llama-cpp-python
- MSVC compilation failures on Python 3.13 (C++ standard conflicts)
- Pre-compiled community wheels NOW available (Feb 2026 update) → **may be back on table**

### Avoid: vLLM (native)
- Requires WSL2 on Windows → file I/O overhead
- Native Windows fork exists (SystemPanic/vllm-windows) but not upstream yet

### Avoid: ONNX Runtime GenAI
- Requires building from source for Python 3.13
- Official wheels only support up to Python 3.12

---

## VERDICT 2: Framework vs Raw API

### ✅ Recommended: Raw API (current approach is sufficient)

The research did NOT recommend LangChain or LlamaIndex for our classification task.
Instead, the architecture naturally converged on:
- Direct HTTP to local inference server (ExLlamaV2 or mistral.rs)
- OpenAI-compatible chat/completions API surface
- Current `hf_refiner.py` pattern (50-line query function) maps directly to local backend

### Upgrade Path: TensorZero (Rust API gateway)
- Industrial-grade Rust gateway: 10,000 QPS, sub-ms latency, 100% success rate
- Alternative: Helicone (~8ms P50)
- Use WHEN we need multi-model routing or observability, not for simple classification

---

## VERDICT 3: ONNX Runtime GenAI

### ❌ Not viable for Python 3.13

- Official wheels: Python ≤3.12 only
- Building from source required for 3.13
- ExLlamaV2 and mistral.rs are both better paths given our stack

---

## VERDICT 4: Windows Scheduled Tasks

Not covered by deep research directly, but the architecture proposes:
- Elixir/BEAM orchestrator with Phoenix LiveView for telemetry (aspirational)
- PowerShell 7.5.x REST modules polling daemon status
- PSReadLine custom auto-suggestions based on daemon state

**Practical answer for NOW:** Standard Windows Task Scheduler with our existing PowerShell launcher.

---

## BONUS VERDICTS (Gemini Went Beyond Our Questions)

### New Model Discovery: GPT-OSS 20B
- OpenAI's open-source 21B MoE model (only 3.6B active/token)
- MXFP4 quantization → 13.7GB VRAM, 42 tok/s, 60K context
- **Current 16GB champion** — better than Llama 3 8B for quality at similar VRAM

### New Model Discovery: Gemma-3 12B QAT
- Google's quantization-aware trained model
- Optimized specifically for 16GB VRAM envelope
- Strong alternative to Llama 3 for classification tasks

### Rustification Ecosystem Map
| Tool | Replaces | Language | Status |
|------|----------|----------|--------|
| `uv` | pip/virtualenv/poetry | Rust | ✅ Already in our stack |
| `ruff` | flake8/black | Rust | ✅ Known, not yet integrated |
| `rumdl` | markdownlint | Rust | New — 5x faster, 57 rules |
| `rfmt` | RuboCop | Rust | New — 100ms constant time |
| `mistral.rs` | llama.cpp Python | Rust | New — native Rust inference |
| `TensorZero` | LiteLLM/API gateways | Rust | New — 10K QPS gateway |
| `Qdrant` | Pinecone/FAISS | Rust | New — sub-ms vector search |
| `tantivy` | Elasticsearch | Rust | New — full-text search |

### Mailbox Pattern Validation
Gemini independently validated our mailbox architecture as the correct pattern for:
- Air-gapped daemon ↔ external agent communication
- Pre-computed context delivery (daemon does heavy work, agent does reasoning)
- Process isolation and security

### Win11 MCP Developments
- **Windows On-Device Agent Registry (ODR)**: `odr.exe` for MCP server management
- **MCP Bundles (.mcpb)**: Standardized ZIP with manifest.json v0.3
- Can register our daemon as MCP server via `odr mcp add <manifest>`
- Proxy-mediated auth prevents token passthrough

### Hardware Reality Check: RTX 4090 Laptop
| Factor | Desktop 4090 | Laptop 4090 | Impact |
|--------|-------------|-------------|--------|
| VRAM | 24GB GDDR6X | 16GB GDDR6 | **16GB is hard ceiling** |
| Bandwidth | 1,008 GB/s | ~576 GB/s | **43% slower memory** |
| TDP | 450W+ | 80-175W | Thermal throttling risk |
| Usable VRAM | ~22.5GB | **~14.5GB** | After Win11 DWM overhead |

---

## TRAJECTORY ALIGNMENT

### What the research CONFIRMS about our current approach:

| Our Decision | Research Says | Status |
|-------------|--------------|--------|
| Zero-API overnight daemon | ✅ Correct — local inference is viable and preferred | Validated |
| HF API as interim LLM tier | ✅ Correct bridge — replace with local when ready | Validated |
| Mailbox pattern for agent coordination | ✅ Independently recommended by Gemini | Validated |
| uv for Python management | ✅ Strongly endorsed, `--torch-backend` is key | Validated |
| Python 3.13 (not 3.14) | ✅ Correct — 3.14 breaks TensorRT, 3.13 works with caveats | Validated |
| Bun for TypeScript runtime | ✅ Compatible, no conflicts noted | Validated |

### What the research ADDS to our roadmap:

| New Capability | Priority | Effort |
|---------------|----------|--------|
| ExLlamaV2 local inference | HIGH — eliminates all API dependency | Medium (model download + integration) |
| GPT-OSS 20B via mistral.rs | MEDIUM — better model for 16GB | Medium (Rust build + model download) |
| Qdrant vector DB | LOW — useful for historical baselines | Low (single binary, Rust) |
| MCP Bundle (.mcpb) packaging | LOW — future distribution | Low |
| TensorZero API gateway | LOW — only needed at scale | Low |

### What the research says we should NOT do:

1. ❌ Don't use ONNX Runtime GenAI (Python 3.12 ceiling)
2. ❌ Don't use vLLM native on Windows (WSL2 overhead, not upstream)
3. ❌ Don't use LangChain for simple classification (overkill)
4. ❌ Don't run FP16 models on 16GB (impossible after DWM overhead)
5. ❌ Don't rely on llama-cpp-python builds (MSVC failures, though community wheels exist)

---

## IMMEDIATE NEXT STEPS (Priority Order)

1. **Install ExLlamaV2** — `uv pip install` with PyTorch CUDA 12.4
2. **Download model** — Llama-3.1-8B-Instruct-EXL2-6.0bpw (~6.5GB)
3. **Write local refiner** — Replace `hf_refiner.py` HF API calls with local ExLlamaV2
4. **Add `-Local` flag** to `run_archaeology.ps1` for fully air-gapped overnight runs
5. **Validate** — Run full 22-domain classification locally, compare quality vs HF API

### Future (Post-Validation)
6. Evaluate GPT-OSS 20B via mistral.rs (better quality, same VRAM envelope)
7. Consider Qdrant for historical baseline tracking
8. Package daemon as .mcpb bundle for Windows ODR registration

---

*This digest was structured by Copilot CLI from the raw Gemini session log.
The original 105KB session is preserved at `claude-codex-gemini/sessionANDresearch.md` for full reference chain.*
