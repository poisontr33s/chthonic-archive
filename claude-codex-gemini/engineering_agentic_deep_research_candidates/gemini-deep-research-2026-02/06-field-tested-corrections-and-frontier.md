# Field-Tested Corrections & Frontier Research

> **Source:** Claude session 2026-02-13 — live implementation findings + web research
> **Context:** Built and validated ExLlamaV2 local inference on RTX 4090 Laptop, then researched upgrade paths

---

## 1. Research vs Reality: What the Gemini Reports Got Right and Wrong

### ✅ Confirmed Accurate

| Claim | Status | Evidence |
|-------|--------|----------|
| ExLlamaV2 installs cleanly via pip on Windows | ✅ | `uv pip install exllamav2` → v0.3.2, no build needed |
| EXL2 6.0bpw Llama-3.1-8B fits in 16GB VRAM | ✅ | 6.8GB allocated, 9.2GB headroom |
| uv manages Python 3.13 environment correctly | ✅ | All scripts run via `uv run` |
| CUDA 12.4 PyTorch wheels work on Win11 | ✅ | torch 2.6.0+cu124, GPU detected |
| 8B model can classify files | ✅ | Produces PROMOTE/FLAG verdicts (basic quality) |

### ❌ Inaccurate or Misleading

| Claim | Reality | Impact |
|-------|---------|--------|
| "Flash Attention 2.5.7+ required" (implied easy) | **flash-attn does NOT build on Windows** — Linux C++ build only | CRITICAL: Forces BaseGenerator, blocks DynamicGenerator entirely |
| "ExLlamaV2DynamicGenerator for production use" | **Unusable on Windows** without flash-attn → paged attention assertion fails | Must use BaseGenerator + `generate_simple()` |
| "Lazy cache for memory efficiency" | **Broken** without flash-attn — `ExLlamaV2Cache(lazy=True)` causes `TypeError: NoneType not subscriptable` in attn.py:1091 | Must allocate full cache upfront |
| "TensorRT-LLM offers 30-70% speedup" | **Installation on Windows is a nightmare** — MPI, Python 3.10 lock-in, engine pre-compilation | Correctly flagged as overkill in dump002, but speedup claim may be overstated for batch |
| "vLLM has native Windows support" | **Still experimental** — PR exists but WSL2 is still recommended, I/O bottleneck is real | Correctly warned about in dump002 |
| "Q4_K_M on 14B ≈ 9-10GB VRAM" | Likely accurate but **untested** — our 8B EXL2 6.0bpw uses 6.8GB, extrapolation suggests ~9GB for 14B Q4 | Need to verify with actual download |

### ⚠️ Nuanced (Partially Right)

| Claim | Nuance |
|-------|--------|
| "llama-cpp-python is the recommended backend" | For **structured output** (Outlines + GBNF grammar) this is true. But ExLlamaV2 is **10-15% faster** on NVIDIA GPUs for raw generation. The real question is: do you need structured JSON or regex-parsed text? |
| "Qwen 2.5 14B best for structured output" | True for JSON classification. But for our PROMOTE/FLAG text format, the 8B Llama works — quality is the bottleneck, not structure |
| "Overnight thermal throttling" | Real concern but manageable — our 22-domain run was 143s total, not 8hrs continuous. Micro-batching naturally provides cooling gaps |
| "Session 0 isolation blocks CUDA" | True for Task Scheduler as SYSTEM. Our `-Background` flag runs as current user, which sidesteps this |

---

## 2. ExLlamaV2 vs llama-cpp-python: Practical Decision Matrix

| Factor | ExLlamaV2 (current) | llama-cpp-python (upgrade candidate) |
|--------|---------------------|--------------------------------------|
| **Raw speed on RTX 4090** | ★★★★★ Fastest (custom CUDA kernels) | ★★★★ Good (cuBLAS, ~10-15% slower) |
| **Windows stability** | ★★★ Good (no flash-attn = degraded mode) | ★★★★★ Excellent (pre-built CUDA wheels) |
| **Structured output** | ★★ None (regex parsing required) | ★★★★★ Native GBNF grammar + Outlines |
| **Model ecosystem** | ★★★ EXL2/GPTQ only | ★★★★★ GGUF universal standard |
| **Memory resilience** | ★★★ No CPU offload | ★★★★ Graceful spill to RAM |
| **Our hallucination problem** | Requires post-hoc filtering | **Solved** via grammar-constrained decoding |

### Verdict: Dual-Backend Strategy

Keep ExLlamaV2 for **speed-critical** tasks (it's already working). Add llama-cpp-python + Qwen 14B Q4_K_M for **quality-critical** tasks where structured JSON output eliminates hallucination.

---

## 3. The Optimal Upgrade Stack

### Immediate (Next Session)

```
llama-cpp-python (CUDA 12.4 wheel from HuggingFace)
  + Qwen 2.5 14B Instruct Q4_K_M GGUF (~9GB, fits in 16GB)
  + Outlines (Pydantic → GBNF grammar → deterministic JSON)
```

**Download commands:**
```powershell
# Model
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF --include "qwen2.5-14b-instruct-q4_k_m*.gguf" --local-dir models/Qwen2.5-14B-Q4KM

# Backend (pre-built wheel — NO compilation needed)
# Get wheel from: https://huggingface.co/dougeeai/llama-cpp-python-wheels
# Match: sm_89 (Ada Lovelace), Python 3.13, CUDA 12.4
uv pip install llama_cpp_python-<version>+cuda12.4.sm89-cp313-win_amd64.whl

# Structured output
uv pip install outlines pydantic
```

### Medium-Term

| Tool | Purpose | Why |
|------|---------|-----|
| **LocalAI** | OpenAI-compatible API server | Model-agnostic, hot-swap models without code changes |
| **Qwen 2.5 Coder 14B** | Code-specific variant | Better for our polyglot classification task |
| **Task Scheduler** | Zero-touch nightly | Auto-Logon + Lock workaround for CUDA access |

---

## 4. LocalAI — Deep Analysis

**What it is:** Open-source (MIT) drop-in replacement for OpenAI API, runs fully local. 40k+ GitHub stars. Go-based server.

### Why it matters for us

| Feature | Benefit for Chthonic Archive |
|---------|------------------------------|
| **OpenAI-compatible REST API** | Our `hf_refiner.py` already uses OpenAI-style chat completions format — LocalAI would be a config-only swap (change URL from HF router to `localhost:8080`) |
| **Model hot-swap** | Switch between Llama 8B, Qwen 14B, DeepSeek without restarting |
| **GGUF + GPTQ support** | Works with same model files as llama-cpp-python |
| **Embeddings API** | Future: vector DB for historical debt baselines (Qdrant path) |
| **Function calling** | Future: let the model trigger repo operations |
| **No Docker required** | Binary releases available for Windows |
| **Constrained grammar** | Built-in GBNF support for structured JSON |

### Architecture fit

```
Current:  run_archaeology.ps1 → local_refiner.py → ExLlamaV2 (direct)
LocalAI:  run_archaeology.ps1 → local_refiner.py → HTTP localhost:8080 → LocalAI → Qwen 14B
```

The HTTP layer adds ~2ms latency per request but gains model management, health checks, and graceful restarts. For overnight batch processing this is negligible.

### Risk assessment

| Risk | Mitigation |
|------|-----------|
| Go binary stability on Win11 | Community reports stable; test with small batch first |
| VRAM contention if LocalAI stays loaded | Can start/stop per batch, or dedicate to overnight only |
| Version churn (fast-moving project) | Pin version in scripts; our interface is just HTTP POST |

### Verdict: **HIGH VALUE** — Install when ready to graduate from direct-library to server-based inference. This is the path to making model choice a config file change instead of a code change.

---

## 5. Dola.ai / Dola.com — Corrected Analysis

**What it is:** GPT-4-powered AI chat assistant by a Singaporean unicorn founder. Web UI at `dola.com/chat`. Infrastructure is ByteDance/Cici AI (CDN: `ciciaicdn.com`, `ciciai.com`).

**NOT a local AI tool.** It's a cloud service wrapping GPT-4 with ByteDance optimizations.

### Why it felt advanced
The impressive language quality is GPT-4 running on ByteDance's infrastructure. The snappy UX comes from their CDN and streaming optimizations, not a novel model architecture.

### Relevance to our project

| Aspect | Assessment |
|--------|-----------|
| **Local deployment** | ❌ Not available — cloud-only service |
| **Open source** | ❌ Proprietary |
| **Model access** | ❌ GPT-4 via their API, not downloadable |
| **Overnight daemon** | ❌ No utility — requires internet + API costs |
| **Quality benchmark** | ✅ The output quality we should target with Qwen 14B locally |

### Verdict: **NO VALUE** for local inference

Dola.com is a well-polished GPT-4 wrapper, not a local AI framework. The quality bar it demonstrates is achievable locally with Qwen 2.5 14B Q4_K_M for our structured classification tasks.

---

## 6. The Rustification Wave — What's Actually Happening

The Gemini research correctly identified the "Rust speedup" trend. Here's what's real vs hype:

| Project | Status | Impact on Us |
|---------|--------|-------------|
| **uv** (Astral) | ✅ Production, we use it daily | 100x faster than pip — already benefiting |
| **ruff** (Astral) | ✅ Production | Linting speed, not yet adopted here |
| **llama.cpp** (C++ not Rust, but same spirit) | ✅ Production | Core of llama-cpp-python backend |
| **mistral.rs** (Rust LLM runtime) | ⚠️ Maturing | Could replace llama-cpp-python if it gains GGUF support |
| **candle** (Hugging Face Rust ML) | ⚠️ Maturing | Potential future for HF integration |
| **Ruby 4.x YJIT** (Rust-powered JIT) | ⚠️ In development | Interesting for tooling, not for ML inference |
| **burn** (Rust ML framework) | 🔬 Early | Too immature for production use |

### The pattern

The "staccato upwards climb" you described is accurate: each language's tooling gets a Rust rewrite that makes it 10-100x faster, which simplifies workflows because slow tools required complex workarounds. As these stabilize:

1. **uv replaced pip+poetry+venv** → one tool, instant installs
2. **ruff replaced flake8+black+isort** → one tool, instant linting
3. **llama.cpp replaced PyTorch serving** → one binary, instant inference
4. **Next:** mistral.rs or candle could replace llama-cpp-python → pure Rust inference

---

## 7. Open Research Questions (For Next Gemini Deep Research)

These are the unknowns that would benefit from deep research:

1. **Qwen 2.5 14B vs Qwen 2.5 Coder 14B for polyglot repo classification** — which variant produces better PROMOTE/FLAG judgments on mixed-language codebases?

2. **Outlines + llama-cpp-python on Windows: real-world stability** — are there known issues with GBNF grammar + CUDA on Win11 24H2? Memory leaks over 8k+ classifications?

3. **LocalAI Windows binary vs Docker vs WSL2** — which deployment mode is most stable for overnight batch on Win11? Does the native binary avoid the Session 0 CUDA issue?

4. **ExLlamaV2 flash-attn alternatives on Windows** — is there a Windows-compatible flash attention build, or a patch to make DynamicGenerator work without it?

5. **micro-batching with process restart vs persistent server** — for 8k+ files overnight, is LocalAI persistent server or PowerShell micro-batch supervisor more reliable on Windows?

---

## 8. Uncensored Model Catalog (16GB VRAM Fits)

> **Why uncensored?** Censored models refuse to classify files containing security exploits, vulnerability reports, or "sensitive" code patterns — exactly the kind of content overnight archaeology needs to surface. Local = no policy gatekeeping.

### Tier 1: Best for Our Use Case

| Model | Params | Q4_K_M VRAM | Speed | Coding Quality | Source |
|-------|--------|-------------|-------|----------------|--------|
| **GPT-OSS 20B abliterated** | 21B | ~14.5GB (tight fit!) | ~42 tok/s | ★★★★★ Top-tier | [DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf](https://huggingface.co/DavidAU/OpenAi-GPT-oss-20b-abliterated-uncensored-NEO-Imatrix-gguf) (107k downloads, 437 likes) |
| **Gemma 3 12B heretic** | 12B | ~8GB | Fast | ★★★★ Strong | [p-e-w/gemma-3-12b-it-heretic](https://huggingface.co/p-e-w/gemma-3-12b-it-heretic) (652 downloads, 41 likes) |
| **GLM 4.7 Flash Uncensored** | 30B | ~14GB (MoE, sparse) | Fast | ★★★★ | [DavidAU/GLM-4.7-Flash-Uncensored-Heretic-NEO-CODE-Imatrix-MAX-GGUF](https://huggingface.co/DavidAU/GLM-4.7-Flash-Uncensored-Heretic-NEO-CODE-Imatrix-MAX-GGUF) (66.6k downloads) |
| **Qwen3 14B abliterated** | 14B | ~9GB | Moderate | ★★★★ Structured output king | Community builds on HF |

### Tier 2: Solid Alternatives

| Model | Params | Notes |
|-------|--------|-------|
| **Mistral Nemo 12B Heretic** | 12B | Good reasoning, thinking-mode uncensored |
| **Llama 3.1 8B abliterated** | 8B | [mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF](https://huggingface.co/mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated-GGUF) — drop-in replacement for our current model |
| **Huihui GPT-OSS 20B abliterated v2** | 21B | Alternative abliteration approach |
| **GPT-OSS 20B HERETIC** | 21B | DavidAU's more aggressive variant (49k downloads) |

### VRAM Reality Check

```
Current:   Llama 3.1 8B EXL2 6.0bpw  = 6.8GB  → 9.2GB headroom  ✅ Easy
Qwen 14B:  Q4_K_M                     = ~9GB   → 7GB headroom    ✅ Comfortable
GPT-OSS:   20B Q4_K_M                 = ~14.5GB → 1.5GB headroom  ⚠️ Tight (short context only)
GLM 4.7:   30B MoE Q4                 = ~14GB  → 2GB headroom    ⚠️ Tight (MoE helps)
```

**Strategy:** Start with Qwen 14B (safe, structured output). Graduate to GPT-OSS 20B abliterated when we need maximum classification quality and can tolerate tight VRAM (our prompts are short — classification, not essay generation).

### Key Terminology
- **Abliterated** = Alignment/refusal layers surgically removed post-training
- **Heretic** = Community fine-tune specifically targeting uncensored behavior
- **Derestricted** = Similar to abliterated, different technique
- **DavidAU** = Prolific model modder, most popular uncensored GGUF source on HF

---

## 9. Corrected Dola.com Assessment

**Previous assessment was based on wrong URL.** `dola.com/chat` is NOT the scheduling app — it's a GPT-4-powered chat interface built on ByteDance/Cici AI infrastructure (`ciciaicdn.com` CDN). Singaporean company, but cloud-only with no local deployment path. Quality is GPT-4 class because it IS GPT-4. No utility for our local inference pipeline.

---

## 10. Implementation Priority Queue (Updated)

| Priority | Task | Effort | Payoff |
|----------|------|--------|--------|
| **P0** | Download Qwen 2.5 14B Q4_K_M GGUF | 30min (download) | 2x model quality |
| **P1** | Install llama-cpp-python CUDA wheel | 10min | Unlock structured output |
| **P2** | Install Outlines + write Pydantic schema | 30min | Eliminate hallucination |
| **P3** | Write `local_refiner_v2.py` with llama-cpp backend | 1hr | Production-grade overnight |
| **P4** | Download GPT-OSS 20B abliterated Q4_K_M | 30min | Maximum uncensored quality |
| **P5** | Install LocalAI, test with model hot-swap | 1hr | Model management server |
| **P6** | Task Scheduler setup | 30min | Zero-touch nightly runs |
| **P7** | Disable HAGS registry tweak | 5min | Overnight CUDA stability |

---

*Generated: 2026-02-13 | Session: ExLlamaV2 → Upgrade Path Research*
*Sources: Live implementation data, Gemini Deep Research dump002, web research (LocalAI, Dola.ai, llama-cpp-python, Outlines, ExLlamaV2 benchmarks)*
