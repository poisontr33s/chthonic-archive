# Session Trail — Local AI Infrastructure Build
## 2026-02-11 → 2026-02-13 | Overnight Intelligence Upgrade Path

---

## The Trajectory

**Origin:** Working on Win11 VS Code IDE implementation strategy for the Copilot CLI source restructure. Met an oracle (Gemini 3 Pro deep research). Made benefit of the encounter. Now possess a unique local AI agent stack born from the adventuring.

**Destination:** Fully air-gapped, zero-cost overnight intelligence pipeline running on RTX 4090 Laptop (16GB VRAM) with structured JSON output, semantic search, and uncensored fallback.

---

## What Was Built (Inventory)

### Scripts Created
| Script | Purpose | Lines |
|--------|---------|-------|
| `scripts/local_refiner_v2.py` | Production LLM refiner (llama-cpp + Pydantic structured JSON) | ~310 |
| `scripts/nightly-scheduled.ps1` | Task Scheduler wrapper for nightly runs | ~30 |
| `scripts/embed_ore.py` | Embedding utility + semantic search CLI | ~120 |
| `scripts/vector_db.py` | Qdrant vector DB (ingest/search/stats) | ~130 |

### Scripts Modified
| Script | Change |
|--------|--------|
| `scripts/run_archaeology.ps1` | Added `-LocalV2` flag, auto-detection v2/v1 fallback |

### Models Downloaded
| Model | Size | Role | VRAM |
|-------|------|------|------|
| Qwen 2.5 14B Q4_K_M GGUF | 8.38GB (3 splits) | **Production** classifier | ~9GB |
| GPT-OSS 20B NEOPlus IQ4_NL | 11.8GB (single) | **Uncensored** fallback | ~12GB |
| Llama 3.1 8B EXL2 6.0bpw | 6.25GB | **Speed** fallback (v1) | ~6.8GB |
| snowflake-arctic-embed-xs | 22.6M params | **Embedding** model (384-dim) | CPU |

### Packages Installed (into uv venv)
| Package | Version | Purpose |
|---------|---------|---------|
| llama-cpp-python | 0.3.16 | GGUF inference engine (built from source, CUDA 12.6) |
| sentence-transformers | 5.2.2 | Embedding model runtime |
| qdrant-client | 1.16.2 | Vector DB (embedded mode) |
| outlines | 1.2.10 | Grammar-constrained decoding (not needed — llama-cpp has built-in) |
| cmake | 4.2.1 | Build dependency for llama-cpp |

### System Changes
| Change | Detail |
|--------|--------|
| Task Scheduler | `ChthonicNightly` at 03:00 UTC daily |
| Sleep disabled | `powercfg /change standby-timeout-ac 0` |
| Hibernate disabled | `powercfg /change hibernate-timeout-ac 0` |
| TDR timeout | 60s (was 2s default — admin registry change) |
| HAGS | Kept ON (HwSchMode=2) — research confirmed safe |

### Data Artifacts
| Artifact | Location |
|----------|----------|
| 8,558 ore embeddings | `dumpster-dive/intake/embeddings/ore_embeddings_*.json` |
| 8,558 vector points | `data/qdrant/` (persistent on-disk Qdrant) |
| v2 digest (86P/55F) | `claude/mailbox/ARCHAEOLOGY_DIGEST_2026_02_13.md` |

---

## Five-Tier Nightly Daemon (Final State)

```
Launcher: .\scripts\run_archaeology.ps1 [-Background] [-WithHF|-WithLLM|-Local|-LocalV2]

Tier 0  (default)     $0 cost    Bun daemon + L1 archaeology scavenge
Tier 1  -WithHF       Free HF    + hf_refiner.py (Llama 3 8B via HuggingFace API)
Tier 2  -Local        $0 cost    + local_refiner_v2.py (Qwen 14B, auto-detect)
Tier 2u -Local --unc  $0 cost    + local_refiner_v2.py (GPT-OSS 20B uncensored, Harmony parser)
Tier 3  -WithLLM      Quota      + archaeology L2 via Copilot SDK (haiku)
```

---

## Hard-Won Lessons (Field-Tested)

### 1. Building llama-cpp-python on Python 3.13 + Windows
**No pre-built wheels exist for cp313.** Must build from source:
- Requires: VS2022 Community + CUDA Toolkit + cmake pip package
- **CUDA 13.0 breaks the build** — VS2022 loads 13.0 by default with empty `CudaToolkitDir`
- **Fix:** Force CUDA 12.6 paths in all env vars (`CUDA_PATH`, `CudaToolkitDir`, `CMAKE_ARGS`, `CUDACXX`)
- Build time: ~4m 20s. Result: 67.97 tok/s prompt eval, 25.89 tok/s generation.

### 2. Structured JSON — Outlines NOT needed
- llama-cpp-python has **built-in** structured output via `response_format={"type":"json_object","schema":...}`
- Uses GBNF grammar internally — model can ONLY generate valid JSON matching the Pydantic schema
- **Outlines** is unnecessary overhead for basic JSON schema constraints

### 3. MAX_TOKENS must be generous
- At 300 tokens: 12/22 domains produced truncated JSON
- At 800 tokens: **22/22 domains, zero failures**
- Truncated JSON salvage regex as fallback: extract complete `FileVerdict` objects from partial output

### 4. GPT-OSS 20B Harmony Protocol
- Not a bug — it's a **MoE reasoning architecture** with multi-channel output
- Channels: `<|channel|>analysis` (thinking), `<|channel|>commentary` (reflection), `<|channel|>final` (answer)
- **Cannot use GBNF grammar** — breaks the channel protocol
- **Solution:** Post-process with `_parse_harmony_output()` → extract `final` channel content

### 5. Task Scheduler + GPU: Session 0 Kills CUDA
- "Run whether user is logged on or not" = Session 0 isolation = **no GPU access**
- **Must use** "Run only when user is logged on" for GPU workloads
- Screen lock is fine — GPU compute continues
- Sleep/hibernate WILL kill inference — disable them

### 6. TDR Timeout: The Silent Killer
- Default TDR (Timeout Detection and Recovery) = **2 seconds**
- Long GPU inference (e.g., 20B model, large context) easily exceeds 2s per operation
- Windows assumes driver is hung → **resets GPU mid-inference**
- Set to 60s minimum for LLM workloads

### 7. HAGS is Fine (Don't Believe the FUD)
- Hardware Accelerated GPU Scheduling costs ~1GB VRAM overhead
- On 16GB card: negligible (15GB remaining > any model we run)
- Instability reports trace to specific Windows KB updates, not HAGS architecture
- Keep it ON — disabling reduces GPU feature set for zero stability gain

### 8. Embedding Models: MiniLM is Obsolete
- `all-MiniLM-L6-v2` was the 2023 standard — 56% retrieval accuracy in 2026 benchmarks
- **Drop-in replacement:** `Snowflake/snowflake-arctic-embed-xs` — same 384-dim, same speed, better quality
- Relevance improvement measured: vulkan.rs 0.614 → **0.823** on identical query
- **Future upgrade:** `Qwen3-Embedding-0.6B` (32k context, instruction-aware, 1.2GB)

### 9. ExLlamaV2 vs llama-cpp: Both Now Have Structured Output
- **ExLlamaV3** exists (2026) with EXL3 format + XGrammar structured output
- **TabbyAPI** serves ExLlamaV3 with OpenAI-compatible API
- llama-cpp improved: multi-GPU support, JIT schema compilation
- Choice is now hardware alignment, not feature gap

### 10. LocalAI: Not for Windows (Yet)
- No native Windows binary — Docker/WSL only
- For single-consumer overnight pipeline, llama-cpp-python is simpler
- LocalAI value proposition = multi-model hot-swap + OpenAI API compatibility
- Revisit if we need to serve models to multiple consumers

---

## Research Documents Processed

8 Gemini 3 Pro Deep Research documents → unified verdicts in `08-phase-learning-verdicts.md`:

| # | File | Topic | Key Verdict |
|---|------|-------|-------------|
| 1 | `researchhags.md` | HAGS viability | Keep ON, KB bugs are the problem |
| 2 | `research_GPTOSS_HF.md` | GPT-OSS structured output | Harmony parser needed, GBNF on final channel |
| 3 | `hotswapresearch.md` | Chat template hot-swap | Jinja2 templates per model, llama-cpp handles natively |
| 4 | `Embedding_model_landscape_DRESRCH_DUMP.md` | Embedding models 2026 | MiniLM obsolete → arctic-embed-xs → Qwen3-Embed |
| 5 | `task_scheduler_researchDUMP.md` | Task Scheduler + GPU | Session 0 breaks GPU, TDR=60s, disable sleep |
| 6 | `vsTRAJECTORYDUMP.md` | ExLlamaV2 vs llama-cpp | Both viable, ExV3+TabbyAPI emerging |
| 7 | `general_researchDUMP003.md` | GPT-OSS deployment synthesis | MoE architecture, Harmony protocol |
| 8 | `research_dump003.md` | General + voice assistant | Broad landscape survey |

---

## What's Next (Unstarted)

### Immediate Upgrade Paths
1. **Qwen3-Embedding-0.6B** — 32k context embeddings when released as stable
2. **ExLlamaV3 + TabbyAPI** — Speed upgrade path for structured output
3. **Hermes 4.3 36B** — Next uncensored model candidate (if VRAM fits via IQ2 quant)

### Bonus Mission: HF Model Scraper
- Automated scraper for `huggingface.co/models?other=uncensored`
- SQLite registry with diff-on-pull (what's new since last scrape)
- Filters to 16GB VRAM fits (Q4_K_M ≤ 14.5GB)
- Weekly digest → `claude/mailbox/`

### Pipeline Enhancements
- Debt score trending via Qdrant (embed nightly digests, track drift over time)
- Semantic deduplication (cluster similar ore entries, merge findings)
- Auto-test new models against golden set of 22 domains

---

## Command Quick Reference

```powershell
# Run nightly (production Qwen 14B)
.\scripts\run_archaeology.ps1 -Local

# Run nightly (uncensored GPT-OSS 20B)
uv run scripts/local_refiner_v2.py --uncensored

# Semantic search over 8,558 ore entries
uv run scripts/embed_ore.py search "authentication middleware"

# Vector DB search
uv run scripts/vector_db.py search "CUDA shader pipeline"

# Check nightly task
schtasks /Query /TN "ChthonicNightly"

# Verify TDR
Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'TdrDelay'

# Verify HAGS
Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name 'HwSchMode'
```
