---
type: deep-research-brief
from: copilot-cli
to: gemini-pro-3
created: 2026-02-11
priority: high
scope: infrastructure
---

# ☥ Deep Research Brief — Local LLM + Overnight Pipeline Stack

## Context for the Researcher

We have a polyglot repository (Rust + Python + TypeScript + PowerShell) on Win11 with an RTX 4090 Laptop (16GB VRAM). We've built overnight daemons that scavenge 8500+ files, compute debt scores, and classify artifacts. Currently the LLM refinement step calls HuggingFace free-tier API (Meta-Llama-3-8B-Instruct), which works but depends on external availability.

**Goal:** Determine the optimal path to run LLM inference locally on this hardware, eliminating API dependency for overnight batch work.

---

## Hardware & Software Inventory

```
GPU:      NVIDIA RTX 4090 Laptop (Ada Lovelace, 16GB VRAM)
CPU:      Intel i9-14900HX
OS:       Windows 11
Python:   3.13.11 (uv-managed, NOT 3.14 — TensorRT incompatible)
Bun:      1.3.8 (TypeScript runtime)
CUDA:     12.4+ (CuPy 13.6.0 validated, CUDA runtime 12090)
cuDNN:    9.x
ONNX RT:  >=1.20.0 (declared, TensorRT EP configured)
TensorRT: 10.x (available but not directly used for LLMs yet)
uv:       Package manager (pyproject.toml + uv.lock)
```

**Already installed (GPU-side):** cupy-cuda12x, pynvml, onnx, numba, scikit-learn
**NOT installed:** torch, transformers, polars, vllm, ollama, llama-cpp-python, langchain

---

## Research Question 1: Local LLM Serving on Win11 RTX 4090

Which local LLM serving solution gives the best performance-to-complexity ratio for batch classification tasks on this exact hardware?

### Candidates to evaluate:

| Solution | Category | Key Question |
|----------|----------|-------------|
| **Ollama** | Turnkey server | Win11 native? Performance? Can Python call it? |
| **llama-cpp-python** | Python binding | CUDA support on Win11? Build from source needed? |
| **vLLM** | High-perf server | Win11 support? Python 3.13? CUDA 12.4? |
| **TensorRT-LLM** | NVIDIA native | RTX 4090 Laptop support? Stability on Win11? |
| **ONNX Runtime GenAI** | Already in stack | Can it serve LLMs? Models available? Performance? |
| **ExLlamaV2** | Quantized specialist | GPTQ/EXL2 on Win11? Python 3.13? |

### For each candidate, I need:

1. **Win11 compatibility** — does it work natively or WSL2 only?
2. **Python 3.13 compatibility** — tested? Known issues?
3. **Installation via uv** — `uv add <package>` or manual build?
4. **VRAM usage** for Llama 3 8B (Q4_K_M quantized) — will it fit in 16GB with headroom?
5. **Tokens/second** on RTX 4090 Laptop for batch inference (not interactive)
6. **Startup time** — cold start latency matters for overnight daemon (runs once, processes 22 domains)
7. **API surface** — OpenAI-compatible? Direct Python? Socket?

### Target models (pick best quantization for 16GB):

- `meta-llama/Meta-Llama-3-8B-Instruct` (currently using via HF API) *?*
- `Qwen/Qwen2.5-7B-Instruct` (alternative) *?*
- `mistralai/Mistral-7B-Instruct-v0.3` (alternative) *?*

---

## Research Question 2: Framework vs Raw API

For simple structured classification (PROMOTE/FLAG/SKIP per file with 20-word reason), is a framework worth the dependency cost?

### Current approach (working): *?*
```python
# Raw urllib POST to HF chat/completions
payload = {"model": "...", "messages": [...], "max_tokens": 300}
# Parse [PROMOTE] / [FLAG] lines from response
```

### Frameworks to evaluate:

| Framework | Concern |
|-----------|---------|
| **LangChain** | Heavyweight? Does it help for simple classification? |
| **LlamaIndex** | Designed for RAG — overkill for classification? |
| **Instructor** | Structured output via Pydantic — good fit? |
| **Outlines** | Constrained generation — forces valid output format? |
| **Raw API** | Current approach — is it already sufficient? |

### Decision criteria:
- Does it reduce code vs. the current 50-line `query_hf()` function?
- Does it abstract the backend (swap HF API ↔ local model with one config)?
- Python 3.13 + uv compatibility
- Does it handle retry/rate-limit/fallback better than my current code?

---

## Research Question 3: ONNX Runtime GenAI Path

Since ONNX Runtime is already in our GPU stack, can it serve as the LLM inference engine?

### Specific questions:
1. Does `onnxruntime-genai` support text generation with instruct models?
2. Which models have official ONNX exports? (Llama 3, Qwen 2.5, Phi-3?)
3. Performance vs llama.cpp on RTX 4090 with TensorRT EP
4. Quantization: INT4/INT8 ONNX models — available or need conversion?
5. Python 3.13 wheel availability on Win11
6. Can it do chat-completion-style API (system/user messages)?

---

## Research Question 4: Windows Task Scheduler Integration

How to schedule the nightly daemon as a zero-touch recurring task:

### Current manual launch:
```powershell
.\scripts\run_archaeology.ps1 -Background -WithHF
```

### Need:
1. Register as Windows Scheduled Task (run at 02:00 daily)
2. Environment propagation: HF_TOKEN, PATH (bun, uv, cargo)
3. Log rotation (don't fill disk — keep last 7 runs)
4. Failure surfacing: if daemon crashes, write a sentinel file or Windows notification
5. PowerShell execution policy considerations
6. User session vs SYSTEM account tradeoffs

---

## Output Format Requested

For each research question, produce:

```
## Verdict: [QUESTION TITLE]

### Recommended: [TOOL/APPROACH]
- Why: [2-3 sentence rationale]
- Install: [exact uv/pip commands]
- VRAM: [expected usage]
- Speed: [tokens/sec or time estimate]

### Runner-up: [TOOL/APPROACH]
- Why: [when you'd pick this instead]

### Avoid: [TOOL/APPROACH]
- Why: [specific incompatibility or issue]

### Code Skeleton:
```python
# Minimal working example for our use case
```

### Known Gotchas on Win11:
- [issue 1]
- [issue 2]
```

---

*Generated by Copilot CLI session, structured from validated infrastructure inventory. All hardware specs and software versions verified against running system.*
