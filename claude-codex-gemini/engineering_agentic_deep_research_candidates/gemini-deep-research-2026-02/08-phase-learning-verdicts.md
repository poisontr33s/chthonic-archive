# Deep Research Verdicts — Phase Learning Digest
## Unified from 8 Gemini 3 Pro Deep Research documents (2026-02-13)

---

## Q1: HAGS Verdict → KEEP ON (conditional)

**Source:** `researchhags.md`

**Finding:** HAGS is architecturally safe on RTX 4090 (16GB+ VRAM = 1GB overhead is negligible). The instability people report is NOT from HAGS itself — it's from broken Win11 updates KB5074109 (Jan 2026) and KB5077181 (Feb 2026) conflicting with dxgmms2.sys.

**Action:**
- ✅ **Keep HAGS ON** — no need to disable for our RTX 4090 Laptop
- ⚠️ Check if KB5077181 is installed: if yes, roll it back or install NVIDIA hotfix driver 581.94/591.86
- ❌ Cancel the `hags-disable` todo — the research says disabling HAGS actually reduces GPU feature set for no stability gain on 16GB cards

**VRAM impact:** ~1GB overhead, leaving 15GB — comfortable for Qwen 14B (8.38GB) and even GPT-OSS 20B (11.8GB).

---

## Q2: GPT-OSS 20B "Chatty" Output → Harmony Protocol Parser

**Source:** `research_GPTOSS_HF.md`, `general_researchDUMP003.md`

**Root cause:** GPT-OSS 20B uses the **Harmony Response Format** — a multi-channel protocol with `<|channel|>analysis`, `<|channel|>commentary`, and `<|channel|>final` tokens. This is a deliberate MoE reasoning architecture, not a bug.

**Solutions (ranked):**
1. **Golden Path:** GBNF grammar-constrained decoding via llama-cpp — force the `final` channel to emit valid JSON while letting analysis channel "think" freely
2. **Silver Path:** "Dummy Tool Hack" — disguise JSON extraction as a function call, which triggers the model's disciplined tool-use mode
3. **Harmony-aware wrapper:** Parse the multi-channel output, extract only the `<|channel|>final` content

**Key insight:** Suppressing reasoning ("Don't think, just output JSON") actually DEGRADES quality because it bypasses the MoE experts needed to formulate correct answers. Let it think, then parse the final channel.

**Specific flags for 16GB:** `--n-cpu-moe` (offload MoE routing to CPU) + `--flash-attn` to fit in VRAM with usable context.

**Role verdict:** Keep **Qwen 2.5 14B as production** (native JSON, fast, reliable). Use **GPT-OSS 20B as uncensored fallback** with Harmony parser for security/exploit file classification that Qwen refuses.

---

## Q3: Chat Template Hot-Swap → Server-Side Jinja2

**Source:** `hotswapresearch.md`

**Finding:** The industry has solved this. llama-cpp reads chat templates from GGUF metadata (embedded Jinja2 from `tokenizer_config.json`). The key discovery:
- llama-cpp now uses **Minja** (its C++ Jinja2 implementation) to auto-apply templates from GGUF
- If a GGUF lacks the template, you can override via `--chat-template` flag or `chat_template` parameter in llama-cpp-python
- **No universal format exists** — but ChatML is the closest to universal for instruction models

**Action:** Our current code (`create_chat_completion`) already does auto-detection correctly for Qwen (ChatML). For GPT-OSS, we'd need to either:
1. Specify the Harmony template explicitly
2. Use raw `__call__` completion mode instead of chat mode

---

## Q4: Embedding Model → Upgrade from MiniLM to Arctic-XS or Qwen3-0.6B

**Source:** `Embedding_model_landscape_DRESRCH_DUMP.md`

**Verdict:** MiniLM-L6-v2 is **obsolete** in 2026. Retrieval accuracy at 56% is "dangerously low."

**Recommended upgrades (our constraints: <500MB, CPU-friendly):**
| Model | Dims | Size | Advantage |
|-------|------|------|-----------|
| **snowflake-arctic-embed-xs** | 384 | ~80MB | Drop-in MiniLM replacement, same speed, better quality |
| **nomic-embed-text-v1.5** | 768→any | ~270MB | Matryoshka dims (compress to 128d for storage) |
| **Qwen3-Embedding-0.6B** | 1024 | ~1.2GB | 32k context, instruction-aware, best quality for size |

**Immediate action:** Swap MiniLM for `snowflake-arctic-embed-xs` — zero latency change, strictly better.
**Future:** When re-indexing, move to Qwen3-Embedding-0.6B for code-aware embeddings.

---

## Q5: Task Scheduler + GPU → Session 0 is Hostile

**Source:** `task_scheduler_researchDUMP.md`

**Critical findings:**
- **Session 0 isolation** (when "Run whether user is logged on or not") runs in a headless session with NO GPU access via WDDM — the GPU driver needs a display surface to initialize
- **Our current config** ("Run only when user is logged on") is actually CORRECT for GPU workloads — it runs in the user's interactive session where GPU is available
- **Screen lock is fine** — GPU compute works while locked, the session stays active
- **Sleep/hibernate kills GPU jobs** — Must disable sleep timers

**Action items:**
1. ✅ Keep task as "Run only when user is logged on" (our default, which is correct)
2. 🔧 Set power plan to disable sleep: `powercfg /change standby-timeout-ac 0`
3. 🔧 Extend TDR timeout: `HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers\TdrDelay` = 60 (default is 2s, kills long GPU ops)
4. ❌ Do NOT enable "Run whether user is logged on or not" — this breaks GPU access

---

## Q6: ExLlamaV2 vs llama-cpp Trajectory → ExLlamaV3 is the future

**Source:** `vsTRAJECTORYDUMP.md`

**Key findings:**
- **ExLlamaV3** now exists (2026) with EXL3 format — 4.0bpw quants, faster than v2
- **ExLlamaV3 has XGrammar support** — structured output is now available (closing the gap that drove us to llama-cpp)
- **TabbyAPI** serves ExLlamaV3 with OpenAI-compatible API + XGrammar JSON output
- **llama-cpp** improved CUDA significantly in 2026, multi-GPU breakthrough, JIT schema conversion

**Verdict for us:**
- **Keep llama-cpp for now** — stable, working, GBNF grammar proven
- **Watch ExLlamaV3 + TabbyAPI** for potential speed upgrade (EXL3 quants are faster)
- **Both engines now have structured output** — the gap is closed

---

## Q7: Bonus — Dola.ai & Local Voice Assistant

**Source:** `research_dump003.md`

**Finding:** Dola.ai is a Singaporean commercial product (proprietary). Not useful for local stack.

**"Local Gold" voice stack alternative:**
- **Pipecat** (orchestration) + **Whisper.cpp** (STT) + **Llama 3/Qwen** (brain) + **Kokoro** (TTS, 82M params, high quality)
- Full local voice assistant, zero API cost, comparable quality

---

## Actionable Summary (Priority Order)

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | Cancel hags-disable — keep HAGS ON | None | Avoids unnecessary reboot |
| 2 | Set `standby-timeout-ac 0` for overnight GPU jobs | 1 cmd | Prevents sleep killing nightly |
| 3 | Set TDR timeout to 60s | 1 reg key | Prevents GPU timeout on long inference |
| 4 | Swap MiniLM → snowflake-arctic-embed-xs | 5 min | Better retrieval, same speed |
| 5 | Build Harmony channel parser for GPT-OSS 20B | 30 min | Unlocks uncensored fallback |
| 6 | Watch ExLlamaV3 + TabbyAPI for future upgrade | Track | Potential 2x speed boost |

---

## Files Processed

| File | Topic | Lines |
|------|-------|-------|
| `researchhags.md` | HAGS viability on Win11 24H2 | 200 |
| `research_GPTOSS_HF.md` | GPT-OSS 20B structured output | 427 |
| `hotswapresearch.md` | Chat template hot-swap | 330 |
| `Embedding_model_landscape_DRESRCH_DUMP.md` | Embedding models 2026 | 292 |
| `task_scheduler_researchDUMP.md` | Task Scheduler + GPU | 328 |
| `vsTRAJECTORYDUMP.md` | ExLlamaV2 vs llama-cpp trajectory | 235 |
| `general_researchDUMP003.md` | GPT-OSS deployment synthesis | 242 |
| `research_dump003.md` | General + voice assistant | 561 |
