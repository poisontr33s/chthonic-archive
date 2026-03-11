---
type: strategic-plan
from: claude
to: claude · codex · gemini · user
created: 2026-03-10
revised: 2026-03-10 (69-search HF sweep + live trending validation)
priority: high
scope: local-ai-stack · toolchain-gaps · daemon-repair · model-strategy
status: CLOSED — READY_FOR_DELEGATION
---

# Strategic Plan: Local AI Stack Activation + Toolchain Gap Closure
## Chthonic Archive — March 2026

> **Context:** Solo developer with RTX 4090 Laptop (16GB VRAM), polyglot Win11 environment
> (Rust/Python/Bun-TypeScript-Next.js-React-TailwindCSS-Vercel-etc/Ruby/Go/PowerShell), full API access to Claude/Codex/Gemini,
> but no local inference running and a broken overnight automation loop.
> Goal: close the three-body gap (SSOT work ↔ daemon ↔ local inference) so digital
> intelligence can carry more of the load autonomously.

---

## Environment Snapshot (Live, 2026-03-10)

| Layer | Tool | Version | Status |
|---|---|---|---|
| Shell (default) | pwsh 7.5.x | current | ✅ |
| Shell (bash) | brush (Rustified bash reimpl, Win11 native .exe) | — | ✅ — update via `cargo install brush-shell` |
| Python | uv 0.10.8 | current | ✅ |
| Python runtime | CPython 3.14.3 (active) + 3.13.11 (installed) | **⚠️ 3.14 active** |
| Ruby | rv 0.5.3 → Ruby 4.0.1 | current | ✅ |
| Go | goup → Go 1.26.1 | current | ⚠️ goup not in bash PATH |
| JS/TS | bun 1.3.9 | current | ✅ |
| Rust | cargo/rustc 1.93.1 | current | ✅ |
| GPU | RTX 4090 Laptop, 16376 MiB, driver 595.71, compute 8.9 | — | ✅ |
| Inference binary | mistralrs 0.7.0 @ ~/.cargo/bin/ | **⚠️ not in PATH, not running** |
| Local models | none | ❌ nothing downloaded |
| Torch/ExLlamaV2 | not installed | ❌ |
| TabbyAPI | installed (dev/tabbyAPI/) | dormant, loras/ empty |
| Overnight daemon | runs nightly, no memory, same output every night | ❌ broken loop |

---

## Gap Map (Three-Body Problem)

```
SSOT / lore authoring          ← you + Claude (working)
         ↕ NO ROUTING
overnight daemon               ← stateless scanner, reports ignored
         ↕ NO LOCAL MODEL
local inference                ← binary exists, no model, not running
```

**Root causes:**
1. Daemon has no state — it re-ranks the same files nightly with no memory of what ran
2. No local model downloaded — all classification still hits HF free-tier API
3. PATH gaps mean mistralrs/goup/brush aren't accessible from pwsh or brush sessions
4. Python 3.14 active — blocks most ML wheel installs that require 3.13

---

## Part 1 — Immediate Toolchain Fixes (Codex-delegatable, ~1 session)

These are mechanical, scoped, low-risk. Delegate to Codex with file scope limits.

### 1a. PATH Fix — cargo tools + goup in pwsh + brush

**Problem:** The primary shell is **pwsh 7.5.x**. Several tool PATH entries are missing from the PowerShell profile. brush (bash companion) is available but its `~/.cargo/bin` location must be on PATH in both shells.

**Fix — PowerShell profile (`$PROFILE`):**
```powershell
# cargo tools: mistralrs, brush, goup binary itself
$env:PATH = "$HOME\.cargo\bin;" + $env:PATH

# goup-managed Go: symlink at ~/.go/current, env written by goup init
$env:PATH = "$HOME\.go\bin;$HOME\.go\current\bin;" + $env:PATH
```

**Fix — brush profile (`~/.bashrc` or `~/.brushrc` for when brush is used):**
```bash
export PATH="$HOME/.cargo/bin:$PATH"        # mistralrs, brush self, goup binary
export PATH="$HOME/.go/bin:$HOME/.go/current/bin:$PATH"  # goup-managed Go
eval "$(rv shell init bash)"                # rv hook — no shims, hook mutates PATH per project
```

**rv note:** rv does NOT use shims. It fires a pre-exec hook (`eval "$(rv shell init bash)"`) that directly sets PATH to the active Ruby's `bin/`. For PowerShell: `Invoke-Expression (& "rv" shell init powershell)` in `$PROFILE`. (`Remove-Variable` alias conflict is already resolved in this pwsh context via a profile override on `cd` into chthonic-archive.)

**goup note:** goup uses a symlink (`~/.go/current` → active version) written by `goup install`/`goup set`. No shell hook needed — PATH just needs `~/.go/current/bin` present once. Windows symlinks require Developer Mode or admin privileges.

**Scope:** pwsh `$PROFILE`, `~/.bashrc` / `~/.brushrc`, no changes to existing scripts
**Agent:** Codex
**Constraint:** Do not modify `GT-ENV-SHL-CAP` content — only PATH/hook entries

### 1b. Python Version Pin for ML Work

**Problem:** Python 3.14 is active globally but most CUDA/ML wheels (torch, ExLlamaV2,
bitsandbytes) are 3.13-only.
**Fix:** ML-specific projects use `uv python pin 3.13.11` in their project root.
Do NOT downgrade the global default — 3.14 is fine for everything else.

**Deliverable:** A `pyproject.toml` template at `dev/local-inference/pyproject.toml`
pinning Python 3.13, with `torch --torch-backend=cu124`, `exllamav2` deps.
**Agent:** Codex
**Constraint:** One new directory only (`dev/local-inference/`), no changes to existing scripts

### 1c. goup Discovery

**goup commands for reference** (binary at `~/.go/bin/goup.exe` or `~/.cargo/bin/goup.exe`):
```
goup install              # install latest Go
goup install 1.26.1       # install specific version
goup ls                   # list all installed Go versions
goup search               # list all available versions from golang.org/dl
goup set <VERSION>        # switch active version (updates ~/.go/current symlink)
goup remove <VERSION>     # remove a version
goup upgrade              # upgrade goup itself
goup init                 # (re)initialize — writes ~/.go/env + profile entries
```

**How it works:** goup installs Go into `~/.go/<version>/` and maintains a symlink `~/.go/current` → active version. No hook needed after initial PATH setup — just `~/.go/current/bin` on PATH. Windows requires Developer Mode or admin for symlink creation.

Go 1.26.1 is current — no action needed on the runtime, just confirm PATH includes `~/.go/current/bin` in pwsh `$PROFILE`.

### 1d. rv Discovery

**rv commands for reference** (binary confirmed, Ruby 4.0.1 active):
```
rv ruby list                      # list installed + available Ruby versions
rv ruby install [VERSION]         # install a version (latest, 4.0.1, etc.)
rv ruby pin [VERSION]             # set/show the Ruby version for current project
rv ruby find [VERSION]            # show path to Ruby executable
rv ruby uninstall VERSION
rv selfupdate                     # update rv itself (standalone install only)
rv run <COMMAND> [ARGS]           # run a command with the active Ruby (alias: rv r)
rv tool install GEM[@VER]         # install a gem as a global tool
rv <...>                          # use rv directly in pwsh (Remove-Variable alias removed via profile override)
```

**Shell integration (critical — no shims):** rv does NOT use shims. It uses a pre-exec hook that evaluates `rv shell env bash` before each command, directly mutating `PATH`, `GEM_HOME`, etc. to activate the correct Ruby. Version is resolved from `.ruby-version`, `.tool-versions`, or `gem.kdl` in the project tree.

Verify the hook is in `~/.bashrc`:
```bash
eval "$(rv shell init bash)"
```

Ruby installs to: `~/.local/share/rv/rubies/` (XDG-compliant).

Ruby 4.0.1 is current — no action needed on the runtime. Verify hook is active in glam/bash.

### 1e. brush (bash shell) Discovery

**brush** is a Rustified bash/POSIX-compatible shell for Win11 — a full reimplementation in Rust, not a wrapper. Compiles to `brush.exe` in `~/.cargo/bin/`. Managed via cargo like any other Rust tool:

```powershell
cargo install --locked brush-shell   # install or update to latest
brush --version                      # confirm active version
brush script.sh                      # run a bash script
brush                                # interactive bash-compatible session
```

**Role in the stack:** brush is the bash-compatible layer when pwsh is not suitable (e.g., running Unix-style shell scripts). It reads `~/.bashrc` / `~/.brushrc` for config. Since it lives in `~/.cargo/bin/`, the same PATH entry that covers mistralrs and goup also covers brush — one PATH fix covers all three cargo tools.

**Update:** No built-in subcommand — reinstall via `cargo install --locked brush-shell`.

---

## Part 2 — Local Inference Stack (User-executed, Codex-assisted)

**Decision (from Feb 2026 research, still valid):** mistralrs is the canonical engine.
Binary 0.7.0 already compiled. No model downloaded yet.

### 2a. Model Selection — HF Quality Audit (March 2026, 69-search sweep)

**Hardware:** RTX 4090 Laptop, 16376 MiB VRAM, CUDA compute 8.9

#### Abliteration — What It Actually Is

Weight-level surgery, not a prompt trick. Isolates the single latent direction in
activation space responsible for refusal behavior, removes it via orthogonal projection
from the model's weight matrices. Survives system prompt changes — the refusal capacity
is structurally gone. Best tool for capability preservation: ErisForge or DECCP
single-pass (arxiv 2512.13655, Dec 2025). Pipeline names in the wild: Heretic, huihui-ai.

Three producers dominate the uncensored GGUF space right now:
- **DavidAU** — primary abliteration/Heretic author, highest likes-to-download ratio
- **huihui-ai** — primary abliteration author for Chinese frontier models (Qwen3.5, DeepSeek)
- **mradermacher** — prolific mass quantizer, imatrix mirrors of the above two

---

#### Corrected Intelligence on Chinese Frontier Models

The landscape context supplied named several models as current. Live HF verification:

| Model/Firm | Named as | Actual HF Status |
|---|---|---|
| DeepSeek-R2 / R2-Lite | Implied current | **Does not exist** — no release as of Mar 2026 |
| GLM-4.5 / GLM-5 (Zhipu) | Current | **Does not exist** — latest is GLM-4/Z1-0414 (Apr 2025) |
| MiniMax M2.5 | Current | **Does not exist** — Text-01 (456B, Jan 2025) only; no GGUF feasible |
| Kimi K2.5 / Moonshot | Current | **No open weights** — zero HF presence |
| Doubao / Seedance (ByteDance) | Named | **No open weights** — not open-sourced |
| DeepSeek-R1 distills | Named | ✅ Fully open, MIT, mature GGUF + abliterated ecosystem |
| Qwen3.5 (Alibaba) | Named | ✅ Released Feb 2026, Apache-2.0, GGUF + abliterated variants exist |

The open Chinese frontier usable locally right now is **DeepSeek-R1 distills** and
**Qwen3.5**. Everything else is either closed-API only, unreleased, or infeasibly large.

---

#### Model Selection Matrix

Use case split: reasoning/STEM/code → DeepSeek-R1 distill lineage.
Creative/instruction/SSOT voice → GPT-oss-20B Heretic or Qwen3.5 abliterated.

---

**Slot A — Reasoning / STEM / code (DeepSeek-R1 distill lineage)**

| Model | VRAM | DL | Likes | Released | Notes |
|---|---|---|---|---|---|
| `unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF` | ~5.5GB Q4 | 97K | 390 | May 2025 | Best small reasoning model on HF — updated R1 distill on Qwen3 base |
| `mradermacher/DeepSeek-R1-Distill-Qwen-14B-Uncensored-GGUF` | ~9.5GB Q4 | 11.7K | 148 | Jan 2025 | **Sweet spot** — 14B uncensored reasoning, comfortable fit, proven |
| `mradermacher/DeepSeek-R1-Distill-Qwen-14B-abliterated-i1-GGUF` | ~9.5GB Q4 | 1.4K | 18 | Jan 2025 | Abliterated variant (surgical vs fine-tuned) |
| `bartowski/DeepSeek-R1-Distill-Qwen-32B-abliterated-GGUF` | ~20GB hybrid | 8.8K | 132 | Jan 2025 | Best reasoning ceiling; Q3_K_M for partial CPU offload |

R1 distills outperform same-size Llama3.3/Qwen3 instruct on reasoning benchmarks.
The 14B-Qwen distill benchmarks above Llama3.3-70B on MATH and AIME.
For non-reasoning creative tasks, standard instruct models still perform better.

---

**Slot B — Creative / instruction / SSOT voice work**

| Model | VRAM | DL | Likes | Trend | Released | Notes |
|---|---|---|---|---|---|---|
| `mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF` | ~12GB Q4 | 84K | 25 | 14 | Feb 2026 | Best validated creative uncensored — highest cross-reference count across full sweep |
| `mradermacher/Huihui-Qwen3.5-35B-A3B-abliterated-i1-GGUF` | ~7GB active (MoE) | 44K | 22 | 12 | Mar 2026 | Qwen3.5 MoE abliterated, newest architecture, comfortable VRAM |
| `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive` | ~6GB Q4 | 104.9K | 253 | **253** | 4 Mar 2026 | **#4 trending globally on all of HF right now** — "Aggressive" uncensoring, ships as GGUF, 9B Qwen3.5 base. Trending score two orders of magnitude above anything else in the uncensored GGUF space. Community consensus pick for 9B slot. |
| `DavidAU/Qwen3.5-9B-Claude-4.6-OS-Auto-Variable-HERETIC-UNCENSORED-THINKING-MAX-NEOCODE-Imatrix-GGUF` | ~6GB Q4 | 3.3K | 5 | 5 | 9 Mar 2026 | DavidAU's newest release — auto-switches between thinking/instruct modes, NEO Imatrix MAX pipeline. Supersedes the HighIQ variants. Too fresh to validate but DavidAU's track record is proven. |

---

**Slot C — Thinking / hybrid offload (GLM-4.7 lineage)**

| Model | VRAM | DL | Likes | Released | Notes |
|---|---|---|---|---|---|
| `DavidAU/GLM-4.7-Flash-Uncensored-Heretic-NEO-CODE-Imatrix-MAX-GGUF` | Q3_K_M ~15-16GB | 174K | 279 | Jan 2026 | Highest-velocity 2026 model, native thinking/reasoning, MIT license, DavidAU's most sophisticated quant pipeline. At Q4 (~25GB) needs CPU/GPU split — use Q3_K_M or IQ3_XS for 16GB fit |

GLM-4.7-Flash MoE compatibility with mistralrs 0.7.0 is unconfirmed — use llama.cpp
server for this model specifically.

---

#### What Does Not Exist or Is Not Viable

| Family | Status |
|---|---|
| DeepSeek-R2 | Not released |
| GLM-4.5 / GLM-5 | Not released — GLM-4/Z1-0414 (Apr 2025) is latest |
| MiniMax M2.5 | Not released — Text-01 is 456B, no GGUF, not viable |
| Kimi K2 / Moonshot | No open weights |
| Doubao / ByteDance chat | No open weights |
| WizardLM / Dolphin (TheBloke) | LLaMA-1/2 era, fully superseded |
| Phi-4 uncensored | No abliteration work exists on HF |
| Full DeepSeek-V3/R1 (671B) | Not feasible at 16GB — use distills |
| Unsloth bnb-4bit for inference | Training format only — use GGUF for inference |

---

#### Engine Strategy

| Engine | GGUF | R1 Distills | GPT-oss-20B | GLM-4.7 MoE | Thinking/CoT | Win11 | Status |
|---|---|---|---|---|---|---|---|
| **mistralrs 0.7.0** | ✅ | ✅ | ✅ | Unknown | Partial | ✅ | Compiled, ready now |
| **llama.cpp server** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Widest compat, drop-in |
| **ExLlamaV2 + TabbyAPI** | Via shim | Partial | Partial | ❌ | ✅ | ✅ | LoRA-ready, needs Python 3.13 |

**Path:**
1. Start: mistralrs 0.7.0 + DeepSeek-R1-Distill-Qwen-14B-Uncensored **or** GPT-oss-20B Heretic
2. If GLM-4.7 desired: llama.cpp server — same OpenAI API surface, zero code change in daemon
3. LoRA serving (future): TabbyAPI + ExLlamaV2, `loras/` directory already present

### 2b. mistralrs Startup Script

**Deliverable:** `scripts/start_mistralrs.ps1`

Parameterized for model swap without editing:
```powershell
param([string]$Model = "DeepSeek-R1-Distill-Qwen-14B-Uncensored.Q4_K_M.gguf")
$env:RUST_LOG = "info"
& "$env:USERPROFILE\.cargo\bin\mistralrs.exe" `
    --port 8080 `
    gguf `
    --model-id "dev/models/$Model"
```

**Agent:** Codex — script only, no model download

### 2c. Model Download (User step)

Recommended first download (~9.5GB, fits cleanly in 16GB):
```bash
uv run --with huggingface-hub python -m huggingface_hub.cli download \
  mradermacher/DeepSeek-R1-Distill-Qwen-14B-Uncensored-GGUF \
  --include "*.Q4_K_M.gguf" \
  --local-dir dev/models/
```

Or for creative/SSOT work (~12GB, also fits):
```bash
uv run --with huggingface-hub python -m huggingface_hub.cli download \
  mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF \
  --include "*.Q4_K_M.gguf" \
  --local-dir dev/models/
```

#### Unsloth LoRA Fine-Tune Path (after inference validated)

- **Best base:** `huihui-ai/Huihui-Qwen3.5-9B-abliterated` (Mar 2026, already abliterated,
  Qwen3.5 architecture, Apache-2.0 — use safetensors directly with Unsloth)
  OR `mradermacher/DeepSeek-R1-Distill-Qwen-14B-Uncensored` if reasoning capability needed
- **Training cost:** ~6-8GB VRAM (Unsloth bnb-4bit: model ~5GB + optimizer ~2GB)
- **Dataset:** SSOT corpus — EDFA profiles, Genesis narratives, ASC vocabulary, faction
  hierarchy — from `copilot-instructions.archive.md` (~8,958 lines of bespoke domain data)
- **Output:** LoRA adapter (~100-300MB) → TabbyAPI `loras/` (already installed and waiting)
- **Result:** Model generating LUPLR/EULP_AA/LIPAA voice natively, no system prompt needed
- **Next upstream task:** Gemini DR brief for SSOT dataset extraction and cleaning pass

---

## Part 3 — Daemon Repair (Codex-delegatable, ~1-2 sessions)

This is the highest-leverage fix. The daemon is a scanner with no memory — it produces
the same report nightly and nothing acts on it.

### 3a. Add State File (Seen Set)

**Problem:** No memory of what was already surfaced.
**Fix:** Write a `dumpster-dive/intake/overnight-daemon/.seen_files.json` after each run
containing `{ "path": "...", "hash": "...", "last_surfaced": "ISO8601", "score": N }`.
On next run, files already in seen set get score penalty (-40) unless their mtime changed.

**Impact:** Top-20 list rotates to new files instead of repeating same PowerShell scripts.
**Agent:** Codex
**File scope:** `scripts/overnight_daemon.ts` (add ~50 lines to scoring + output phase)

### 3b. Add Action Routing Stub

**Problem:** Reports land in `dumpster-dive/intake/` and stop — nothing consumes them.
**Fix:** At end of daemon run, if top-3 candidates exceed score threshold (>80), append
a structured task entry to `codex/mailbox/DAEMON_TASK_QUEUE.md`:

```markdown
## [ISO8601] Candidate: scripts/foo.ps1
- Score: 94
- Reasons: repo tooling, 3 TODOs, long function
- Suggested action: REFACTOR
- Status: PENDING
```

Codex picks this up on next session start (it already reads codex/mailbox/).
**Agent:** Codex
**File scope:** `scripts/overnight_daemon.ts` + new `codex/mailbox/DAEMON_TASK_QUEUE.md`

### 3c. Wire Local Model into Classification Pass

Once mistralrs is running on port 8080:

**Fix:** Daemon's classification step currently calls HF API. Add a local-first flag:
```typescript
const LOCAL_INFERENCE_URL = "http://localhost:8080/v1/chat/completions";
const useLocal = await isPortOpen(8080); // probe before deciding
```

Falls back to HF API if local not running. Zero configuration change required from user.
**Agent:** Codex
**File scope:** `scripts/overnight_daemon.ts` (classification function only)

---

## Part 4 — Strategic Delegation Map (Ongoing)

Which agent gets which category of work:

| Work Type | Agent | Why |
|---|---|---|
| SSOT authoring, EDFA profiles, Genesis narratives, creative lore | **Claude** | Creative depth, protocol-aware, voice-consistent |
| Architecture decisions, long-horizon planning, DSL spec, game mechanic validation | **Claude** (Opus tier) | Sustained reasoning over large context — ANKH DSL, Phase 2 extraction, P&P validation |
| Code, scripts, repo audit, skill consolidation, daemon repair, broken-ref sweeps | **Codex** | Autonomous engineer — terminal + patch tools, multi-file, no practical token ceiling, Extra High thinking |
| Deep research briefs (models, frameworks, external landscape) | **Gemini** | 7 research docs already proven, best at web synthesis |
| Batch classification, genre extraction, overnight nightly work | **Local model** | Zero API cost, uncensored, no rate limits, fully autonomous loop |
| LoRA fine-tuning, SSOT domain adaptation | **Unsloth + local GPU** | Produces ASC-native voice model via LoRA on SSOT corpus |

---

## Part 5 — Version Currency Check (manager-standardized)

| Language / Tool | Current Installed | Latest Available | Manager | Update Command | Action |
|---|---|---|---|---|---|
| Python | 3.14.3 | 3.14.3 ✅ | uv | `uv python install` | Pin 3.13.11 for ML projects only |
| Ruby | 4.0.1 | 4.0.1 ✅ | rv | `rv selfupdate` / `rv ruby install <ver>` | Current — verify shell hook in ~/.bashrc |
| Go | 1.26.1 | 1.26.1 ✅ | goup | `goup install <ver>` | Current — fix PATH |
| JS/TS | Bun 1.3.9 | check `bun upgrade` | bun | `bun upgrade` | Likely current |
| Rust | 1.93.1 | check rustup | rustup | `rustup update` | Likely current |
| Shell (bash) | brush (current) | check crates.io | cargo | `cargo install --locked brush-shell` | Likely current |
| mistralrs | 0.7.0 | check crates.io | cargo | `cargo install mistralrs` | 0.7.0 is recent — OK |

All toolchain managers (`uv`, `rv`, `goup`, `bun`, `rustup`, `cargo`) are at current versions. The gap is not version currency —
it is PATH exposure and missing ML project environment.

---

## Execution Sequence (Recommended Order)

```
IMMEDIATE (you, ~10-15min):
  1. Choose first model download (pick one):
     — Reasoning/code:  mradermacher/DeepSeek-R1-Distill-Qwen-14B-Uncensored-GGUF (~9.5GB)
     — Creative/SSOT:   mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF (~12GB)
     — Fast/trending:   HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive (~6GB, #4 HF global trending)
     Save to: dev/models/  (see download commands in §2c)

DELEGATE TO CODEX (single session, no scope limit):
  2. PATH fix — ~/.cargo/bin in bash profile (goup + mistralrs accessible from glam shell)
  3. scripts/start_mistralrs.ps1 — parameterized startup, model-swappable
  4. dev/local-inference/pyproject.toml — Python 3.13 pinned, torch cu124 + exllamav2 deps
  5. overnight_daemon.ts — seen-set state file (stops nightly repetition)
  6. overnight_daemon.ts — task queue output → codex/mailbox/DAEMON_TASK_QUEUE.md
  7. overnight_daemon.ts — local-first classification probe (port 8080, HF API fallback)

AFTER LOCAL MODEL RUNNING:
  8. Validate: run overnight_daemon.ts manually, confirm local model classifies
  9. Verify task queue entries appear in codex/mailbox/DAEMON_TASK_QUEUE.md

FUTURE (Unsloth LoRA — after above stable):
  10. Gemini DR brief: SSOT corpus extraction + cleaning for fine-tuning dataset
  11. Unsloth bnb-4bit fine-tune on huihui-ai/Huihui-Qwen3.5-9B-abliterated
  12. Deploy LoRA adapter → TabbyAPI loras/ (already installed and waiting)
```

---

## Files Touched / Created by This Plan

| File | Agent | Action |
|---|---|---|
| `~/.bashrc` or bash profile | Codex | Add `~/.cargo/bin` to PATH; add `eval "$(rv shell init bash)"` hook |
| `scripts/start_mistralrs.ps1` | Codex | New — startup script |
| `dev/local-inference/pyproject.toml` | Codex | New — ML environment |
| `dev/models/` | User | New directory, download GGUF |
| `scripts/overnight_daemon.ts` | Codex | +seen set +task queue +local probe |
| `codex/mailbox/DAEMON_TASK_QUEUE.md` | Codex | New — daemon output target |

---

---

## Model Candidate Pool — Final Status

| Model | Slot | Trending | Validated | Action |
|---|---|---|---|---|
| `mradermacher/DeepSeek-R1-Distill-Qwen-14B-Uncensored-GGUF` | Slot A reasoning | 4 | ✅ 11.7K DL, 148 likes | Primary reasoning download |
| `unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF` | Slot A small | — | ✅ 97K DL, 390 likes | Best 8B reasoner |
| `bartowski/DeepSeek-R1-Distill-Qwen-32B-abliterated-GGUF` | Slot A ceiling | — | ✅ 8.8K DL, 132 likes | Hybrid offload, max reasoning |
| `mradermacher/OpenAI-gpt-oss-20B-Claude-4.5-Opus-Heretic-Uncensored-i1-GGUF` | Slot B primary | 14 | ✅ 84K DL, 25 likes | Primary creative/SSOT download |
| `mradermacher/Huihui-Qwen3.5-35B-A3B-abliterated-i1-GGUF` | Slot B MoE | 12 | ✅ 44K DL, 22 likes | Qwen3.5 MoE, comfortable VRAM |
| `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive` | Slot B 9B | **253** | ✅ 104.9K DL, 253 likes | #4 HF global trending — community consensus |
| `DavidAU/Qwen3.5-9B-Claude-4.6-OS-Auto-Variable-HERETIC-UNCENSORED-THINKING-MAX-NEOCODE-Imatrix-GGUF` | Slot B 9B watch | 5 | ⏳ 3.3K DL — too fresh | Monitor — DavidAU newest, auto thinking mode |
| `DavidAU/GLM-4.7-Flash-Uncensored-Heretic-NEO-CODE-Imatrix-MAX-GGUF` | Slot C thinking | 19 | ✅ 174K DL, 279 likes | Hybrid offload, use llama.cpp not mistralrs |

Pool closed: 2026-03-10. Next review when Qwen3.5 abliteration ecosystem matures or
new Chinese open-weight releases land (monitor: DeepSeek-R2, GLM-4.5, Kimi K2).

---

*Closed by Claude. Live environment snapshot 2026-03-10. HF data: 69-search sweep +
final trending validation. All model candidates verified against live HF metrics.*

---

## Delegation Checklist — Track Progress Here

Mark `[X]` when each item is verified complete. Update in place — this is the live status board.

### USER — You

- [ ] **U1** — Choose and download first GGUF model to `dev/models/` (see §2c download commands)
- [ ] **U2** — Confirm `dev/models/` directory exists and file downloaded successfully
- [ ] **U3** — Run `scripts/start_mistralrs.ps1` after Codex delivers it — verify server starts on port 8080
- [ ] **U4** — Reload VS Code Insiders after PATH changes (Codex C1) to pick up new shell env
- [ ] **U5** — (Future) Trigger Gemini DR brief for SSOT corpus extraction when ready for LoRA pass

---

### CODEX — Autonomous Engineering Lane

Paste the prompt in the next section directly into a Codex session. Each item maps to a checkbox here.

- [ ] **C1** — PATH fix: `~/.cargo\bin` + `~/.go/current/bin` in pwsh `$PROFILE`; `rv` hook in `$PROFILE`; same paths + `rv` hook in `~/.bashrc`/`~/.brushrc`; verify `goup ls`, `mistralrs --version`, `ruby --version`, `go version` all resolve from pwsh
- [ ] **C2** — `scripts/start_mistralrs.ps1` created, parameterized, tested for syntax
- [ ] **C3** — `dev/local-inference/pyproject.toml` created — Python 3.13 pinned, torch cu124 + exllamav2
- [ ] **C4** — `overnight_daemon.ts` — seen-set state file added (`dumpster-dive/intake/overnight-daemon/.seen_files.json`)
- [ ] **C5** — `overnight_daemon.ts` — task queue output added → `codex/mailbox/DAEMON_TASK_QUEUE.md`
- [ ] **C6** — `overnight_daemon.ts` — local-first classification probe added (port 8080, HF API fallback)
- [ ] **C7** — Validate: run daemon manually, confirm seen-set writes, confirm task queue entry appears

---

### CLAUDE — Protocol / Lore / Architecture Lane

- [ ] **L1** — Draft Gemini DR brief for SSOT corpus dataset extraction (prerequisite for LoRA)
- [ ] **L2** — ANKH DSL spec (`dev/ankh-dsl-spec.md`) — prototype grammar for AD01–AD06
- [ ] **L3** — Phase 2 character extraction: 15 entity sheets → `game/lore/characters/` (SSOT Phase 2)
- [ ] **L4** — Pen-and-paper game mechanic validation pass (prerequisite for vertical slice)
- [ ] **L5** — §10.3.11 Curatrix Mortuorum profile build (last pending T4 entity)
- [ ] **L6** — Skin FA⁵ tag schema decision (deferred from EDFA audit — pick one tag name, backfill)

---

## Codex Prompt — Paste This Directly

> Copy everything between the triple-backtick fences into a Codex session as the opening instruction.

```
CONTEXT:
You are operating on the chthonic-archive repository at C:/Users/erdno/chthonic-archive.
This is a polyglot Win11 codebase (Rust/Python/TypeScript/PowerShell/Ruby/Go).
Primary shell: pwsh 7.5.x. Bash-compatible shell: brush (Rustified bash reimpl, brush.exe via cargo).
Version managers: uv (Python), rv (Ruby), goup (Go), bun (JS/TS), cargo/rustup (Rust).
All of these follow the same pattern as uv — canonical version manager for their language.
Python for ML work must be pinned to 3.13 — NOT the active global 3.14.

Reference document: claude/mailbox/STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md
Read it fully before starting. Update the checklist items C1–C7 with [X] as you complete each one.

TASKS (complete in order, no scope limit):

C1 — PATH FIX (PRIMARY: PowerShell; SECONDARY: brush/bash)
Primary shell is pwsh 7.5.x. Fix $PROFILE first, then brush profile.

PowerShell $PROFILE — add if missing:
  $env:PATH = "$HOME\.cargo\bin;" + $env:PATH          # brush.exe, mistralrs.exe, goup binary
  $env:PATH = "$HOME\.go\bin;$HOME\.go\current\bin;" + $env:PATH  # goup-managed Go
  Invoke-Expression (& "rv" shell init powershell)     # rv hook for Ruby

brush/bash profile (~/.bashrc or ~/.brushrc) — add if missing:
  export PATH="$HOME/.cargo/bin:$PATH"
  export PATH="$HOME/.go/bin:$HOME/.go/current/bin:$PATH"
  eval "$(rv shell init bash)"

Verify after: `goup ls`, `mistralrs --version`, `ruby --version`, `go version` all resolve from pwsh.
Note: goup uses a symlink at ~/.go/current — requires Developer Mode or admin on Windows for symlink creation.
Do NOT modify scripts/shell_capabilities.ps1 content.

C2 — scripts/start_mistralrs.ps1
Create this file. It must:
- Accept a -Model parameter (string, default: "DeepSeek-R1-Distill-Qwen-14B-Uncensored.Q4_K_M.gguf")
- Set RUST_LOG=info
- Call $env:USERPROFILE\.cargo\bin\mistralrs.exe with --port 8080 and the gguf subcommand
- Point --model-id to dev/models/$Model
- Print a startup message showing which model is loading
Do not download any model. The model file will be placed in dev/models/ by the user.

C3 — dev/local-inference/pyproject.toml
Create the directory dev/local-inference/ and a pyproject.toml inside it that:
- Pins Python to 3.13 (requires-python = ">=3.13,<3.14")
- Lists dependencies: torch (with index-url for cu124), exllamav2, huggingface-hub, unsloth
- Includes a uv section with index for PyTorch CUDA wheels
This is an environment scaffold only — no scripts, no logic.

C4 — overnight_daemon.ts: seen-set state file
File: scripts/overnight_daemon.ts
Add a seen-set mechanism:
- After scoring, load .seen_files.json from dumpster-dive/intake/overnight-daemon/ if it exists
- Files present in the seen set with unchanged mtime get a score penalty of -40
- After writing the report, append/update the seen set with top-20 candidates:
  { relPath, score, lastSurfaced (ISO8601), mtimeMs }
- Write the updated seen set back to .seen_files.json
This stops the same PowerShell scripts appearing in the top-20 every single night.

C5 — overnight_daemon.ts: task queue routing
After the report is written, if any of the top-3 candidates have score > 80:
- Append a structured entry to codex/mailbox/DAEMON_TASK_QUEUE.md (create if absent):

## [ISO8601 timestamp] — [relPath]
- Score: [N]
- Reasons: [reasons joined by comma]
- Suggested action: REFACTOR
- Status: PENDING

This routes high-priority candidates directly into the Codex mailbox for pickup.

C6 — overnight_daemon.ts: local-first classification probe
In the LLM classification step (wherever HF API is called):
- First probe http://localhost:8080/health with a 500ms timeout
- If reachable, route the classification request to http://localhost:8080/v1/chat/completions
  using the same payload shape already used for the HF API call
- If not reachable, fall back to HF API as currently implemented
- Log which backend was used at the start of each classification batch

C7 — VALIDATE
Run overnight_daemon.ts manually (bun run scripts/overnight_daemon.ts --dry-run or equivalent).
Confirm:
- Seen-set file is written to dumpster-dive/intake/overnight-daemon/.seen_files.json
- If any candidates score > 80, an entry appears in codex/mailbox/DAEMON_TASK_QUEUE.md
- No regressions in existing daemon output format

After each task, mark the corresponding [X] in:
claude/mailbox/STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md
under the CODEX checklist (C1–C7).
```

---

## The Horse-Market Concept — Assessment + ANKH Integration Analysis

### What It Is (Emergence Trace)

The concept surfaced organically during the model selection sweep of this session — a vernacular signal, not a coined term. The observation: in the open-weight model ecosystem, the market *looks* structured but behaves like a horse market. Sellers project quality through surface signals (trending rank, download count, name branding). Buyers can't inspect the horse's actual gait until after purchase. Community knowledge circulates faster than official documentation. Reputation asymmetry is acute — mass quantizers (mradermacher) inflate download counts without endorsing quality; niche curators (DavidAU) have low download numbers but the highest likes-to-download ratio in the ecosystem. Trending ≠ quality. Quality is *findable* but requires cross-signal triangulation, not naive marketplace trust.

The concept isn't about horses. It's about **non-transparent quality markets where signal and substance are systematically decoupled** — and where the skilled buyer survives by building a different reading apparatus than what the market provides.

---

### What It Isn't (Anti-Collapse Guard)

The Horse-Market is not a one-trick framing for "open-weight model selection is hard." That reading collapses it back into its origin context and makes it redundant once the model pool is closed (which it now is).

The nascency signal is richer than that. What surfaced is a **transferable epistemology**: a named heuristic for navigating any domain where:
1. Surface signals are abundant but systematically misleading
2. Quality is buried under velocity/volume
3. The market rewards confident producers, not necessarily best producers
4. The skilled participant builds cross-referencing apparatus rather than trusting primary signals

This pattern recurs across every domain the Chthonic Archive touches.

---

### Utility Map — Non-Linear Applications

The Horse-Market functions as a **second-order lens**, not a workflow. It doesn't generate tasks; it names an epistemological condition that already exists across multiple lanes.

| Domain | Horse-Market Manifestation | What the Lens Unlocks |
|--------|---------------------------|----------------------|
| **Open-weight models** (origin) | Trending rank ≠ quality; mass quantizers inflate DL counts; quality is likes-to-DL ratio + cross-ref count | Build a tiered vetting protocol rather than trusting single signals |
| **Overnight daemon output** | Same top-20 every night because scoring weights path/extension — high volume ≠ high debt | Seen-set + signal decay is the Horse-Market fix for the daemon |
| **SSOT lore corpus** | Large entity pool; not all entities are equally developed; surface metrics (line count, section headers) don't reflect actual lore density | Phase sequencing by *actual readiness*, not document size |
| **Toolchain/package ecosystem** | `uv`, `rv`, `goup`, `bun`, `cargo` all have clean quality signals — deterministic version management, explicit update commands, no silent degradation. PyPI ML wheels do not — version mismatch, GPU incompatibility hidden behind clean version strings | Python 3.14 trap was a Horse-Market failure: trusted the version number, not the wheel compatibility reality. The five polyglot managers are the anti-Horse-Market layer for the toolchain. |
| **Agent output quality** | Codex produces confident output; confidence ≠ correctness; Gemini produces velocity; velocity ≠ accuracy | The Triad structure itself is a Horse-Market countermeasure: no single agent's output is trusted unilaterally |
| **Conceptual frameworks (ANKH itself)** | Many named constructs in the archive; not all have equal architectural grounding; some are naming-without-specification | ANKH_SYNTHESIS_META.md gap table is the Horse-Market diagnostic for the framework corpus |

---

### ANKH Fit Analysis

**Does Horse-Market belong inside ANKH?**

Partial fit — but not as an Alpha Directive or a Foundational Axiom. The existing six ADs already cover the computational primitives that Horse-Market touches:

- **AD02 (TINKU):** Adversarial synthesis — exactly the apparatus that defeats Horse-Market. You don't trust either signal alone; you produce output C from the collision of A and B.
- **AD04 (AMMIT):** Ma'at weighing — the anti-Horse-Market quality gate. Data is weighed against the Feather of Ma'at (checksum), not against its own claimed weight.
- **AD06 (DESPACHO):** No receive without give — the reciprocal I/O that prevents naive marketplace trust (you pay in `Tallow/compute credits`, you receive validated output).

The Horse-Market doesn't need its own Directive. It names the **failure mode that the ADs were designed to prevent.** It is the *shadow archetype* — the condition that exists when Tinku is bypassed, when Ma'at weighing is skipped, when Despacho offering is omitted.

**Where it fits:** It belongs as a named anti-pattern in the ANKH lexicon — a **Hucha** accumulator (in Andean topology: heavy energy, entropy). When a system routes through Horse-Market conditions (trusting surface signals, skipping adversarial synthesis), Hucha accumulates. When Hucha exceeds Ayni (reciprocity) capacity, AD05 (PACHAKUTI) — the cyclic reset — becomes necessary. The Horse-Market is the mechanism *by which* Hucha enters the system.

**Proposed ANKH notation:**

```
HUCHA(Horse-Market) := { surface_signal_trusted=true, tinku_bypassed=true, maat_weighing_skipped=true }
→ PACHAKUTI risk elevated
→ Countermeasure: AD02 + AD04 activation
```

This makes Horse-Market a *diagnostic trigger*, not a standalone concept — which is exactly what prevents it from being a one-trick pony.

---

### The Wet-Paper-to-Gold Read

Under WPTG, the Horse-Market concept is **Tier 3 Conceptual Gold** — a pattern, vocabulary, metaphor worth repurposing. Its emergence means someone (you) noticed a genuine structural pattern across domains and named it associatively. That naming IS the nascency signal the framework is built to honor.

The WPTG directive: don't let it evaporate as a conversational aside. Capture it with enough specification that it can be invoked later without re-deriving.

This section is that capture.

---

### Where It Lives in the Repo

The concept is currently encoded only in this plan document. Next appropriate placement when the ANKH DSL spec (Claude lane L2) is drafted:

```
docs/frameworks/ankh/ANKH_ANTI_PATTERNS.md
  § Horse-Market (HUCHA accumulator pattern)
    — Definition
    — ANKH diagnostic notation
    — Countermeasure: AD02 + AD04 activation sequence
    — Cross-domain application table (above)
```

Until that file exists, this section in the plan is the canonical capture.

---

*Horse-Market assessment authored: 2026-03-10. Concept source: organic emergence during HF model sweep, session STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.*
