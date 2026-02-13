# Deep Research Candidates — Phase Learning & Next Frontier
## For: Gemini 3 Pro Deep Research
## Context: chthonic-archive overnight intelligence pipeline, Win11 + RTX 4090 Laptop 16GB VRAM

---

## Question 1: HAGS Viability (Hardware Accelerated GPU Scheduling)

**Current state:** HAGS is ON (HwSchMode=2) on Win11 24H2, RTX 4090 Laptop GPU (AD103), CUDA 12.6/13.0/13.1 installed. We run overnight GPU inference (llama-cpp-python, 6-7 minute batch jobs at 04:00 CET via Task Scheduler).

**Research question:** Is disabling HAGS (HwSchMode=1) still recommended for CUDA compute workloads on Win11 24H2 with RTX 40-series mobile GPUs in 2026? Specifically:
- Has NVIDIA resolved the CUDA race conditions that HAGS caused with earlier drivers?
- Does HAGS impact llama-cpp-python / GGUF inference throughput or stability?
- Are there driver version thresholds where HAGS became safe for compute?
- What's the current consensus among ML practitioners running local inference on Win11?
- Our driver: check latest Game Ready / Studio driver release notes for HAGS + CUDA stability fixes.

**Why we care:** We have an unattended overnight GPU job. A CUDA crash at 04:00 means lost data. If HAGS is now safe, we skip a reboot. If not, we need admin intervention.

---

## Question 2: GPT-OSS 20B MoE Structured Output (The "Chatty" Problem)

**Current state:** We downloaded `OpenAI-20B-NEOPlus-Uncensored-IQ4_NL.gguf` (11.8GB, DavidAU's abliterated GPT-OSS 20B). It's a Mixture-of-Experts (MoE) architecture — 21B total, 3.6B active parameters. When we prompt it for JSON classification, it outputs channel tokens and verbose reasoning instead of clean JSON:

```
<|channel|>analysis<|message|>We need to classify the file as PROMOTE, FLAG...
```

Our Qwen 2.5 14B works perfectly with `response_format={"type": "json_object", "schema": ...}` (GBNF grammar-constrained decoding in llama-cpp-python). But when we try the same with GPT-OSS 20B, the model fights the grammar.

**Research question:** How do you get clean structured JSON output from GPT-OSS 20B / GPT-4o-mini-based abliterated MoE models via llama-cpp-python?
- Does GPT-OSS 20B support the ChatML template that llama-cpp uses for `create_chat_completion`?
- What chat template does this model actually expect? (It appears to use `<|channel|>` tokens)
- Is there a specific prompt format or system prompt that makes MoE models comply with JSON schema constraints?
- Does GBNF grammar-constrained decoding work correctly with MoE GGUF models in llama-cpp-python, or is there a known incompatibility?
- Alternative: Should we use a different quant/variant from DavidAU's repo (e.g., the CODE variants which may be more instruction-following)?

**Why we care:** Qwen 14B is our production model but censored. GPT-OSS 20B is uncensored (critical for classifying exploit/vuln/security files that censored models refuse). We need it to output the same structured JSON.

---

## Question 3: Optimal Chat Template for Mixed Model Hot-Swap

**Current state:** Our `local_refiner_v2.py` uses `llm.create_chat_completion()` which auto-detects chat template from GGUF metadata. This works for Qwen 2.5 (ChatML-based). When we swap models, the template may not match.

**Research question:** What's the current best practice for multi-model structured inference with llama-cpp-python on Windows?
- How does llama-cpp-python determine which chat template to use? (GGUF metadata? tokenizer_config.json? manual override?)
- Can you override the chat template per-call or per-model-load in llama-cpp-python?
- For models that don't have embedded chat templates (some community quants strip this), how do you inject the correct template?
- Is there a universal "instruction-following" prompt format that works across Qwen, Llama, Mistral, and GPT-OSS architectures for JSON output?

---

## Question 4: Embedding Model Landscape (Beyond MiniLM)

**Current state:** Using `sentence-transformers/all-MiniLM-L6-v2` (22.7M params, 384-dim, ~80MB). Works great for 8,558 ore file descriptions. Stored in Qdrant embedded mode.

**Research question:** What are the current best embedding models for code/file-description semantic search in 2026?
- Is MiniLM-L6-v2 still competitive, or have newer models (nomic-embed, jina-embeddings-v3, mxbai-embed, gte-Qwen2) significantly improved?
- Specifically for code-aware embeddings: any models trained on code + documentation that would better capture programming concepts?
- VRAM budget: We have 16GB total but run LLM inference alongside. Embedding model must be tiny (<500MB) or CPU-only.
- Can we run embeddings on CPU while LLM uses GPU? Performance implications?
- Does Qdrant embedded mode (our setup) have any limitations vs server mode we should know about?

---

## Question 5: Windows Task Scheduler + GPU Jobs Best Practices

**Current state:** Created `ChthonicNightly` task at 03:00 UTC. Runs `pwsh -NoProfile -File nightly-scheduled.ps1` which calls `run_archaeology.ps1 -Local`. This loads Qwen 14B onto GPU, runs ~7 min inference, exits.

**Research question:** What are the gotchas for GPU-bound Task Scheduler jobs on Win11?
- Does Task Scheduler Session 0 isolation affect CUDA/GPU access?
- Does the job need "Run with highest privileges" for GPU access, or does standard user suffice? (We couldn't set /RL HIGHEST without admin)
- If the user is logged out or screen locked at 03:00, does GPU compute still work?
- Power plan considerations: does Win11 put the GPU to sleep? Should we set a power plan to prevent this?
- Are there better alternatives to Task Scheduler for GPU workloads? (e.g., NSSM, Windows Service wrapper)

---

## Question 6: ExLlamaV2 vs llama-cpp-python Long-Term (2026 Trajectory)

**Current state:** We have both engines installed. ExLlamaV2 v0.3.2 (v1 refiner, 67 tok/s with 8B) and llama-cpp-python 0.3.16 (v2 refiner, 26 tok/s with 14B). We chose llama-cpp for structured JSON output (GBNF grammar).

**Research question:** What's the 2026 trajectory for these two engines?
- Has ExLlamaV2 added grammar-constrained / structured output since v0.3.x?
- Has llama-cpp-python's CUDA performance improved in recent versions? (We're on 0.3.16, built from source for Python 3.13)
- Are there newer engines we should watch? (e.g., vLLM on Windows, TensorRT-LLM, mistral.rs, candle)
- For our use case (batch overnight classification, not real-time), which engine gives best quality-per-VRAM?
- Python 3.13 compatibility status for each engine?

---

## Meta-Notes for Researcher

**Our hardware:** RTX 4090 Laptop 16GB VRAM, i9-14900HX, Win11 24H2, CUDA 12.6 (active)
**Our stack:** Python 3.13.11, llama-cpp-python 0.3.16 (CUDA, built from source), ExLlamaV2 0.3.2, sentence-transformers 5.2.2, qdrant-client 1.16.2
**Our use case:** Unattended overnight file classification (8,558 files across 22 domains, ~7 min total)
**Key constraint:** Zero API cost, fully air-gapped, no Docker, no WSL — native Win11 only
