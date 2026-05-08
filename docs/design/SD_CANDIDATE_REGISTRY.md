---
type: ledger
category: mine-operations
created: 2026-05-09
mine-pass: 1
lock: living — update this file after every sweep or stub creation
description: >
  Ground truth for candidate clone state, sweep coverage, module stubs, and task
  sequencing. Read this BEFORE any sweep work, backend stub creation, or
  MILF_ARCH_MATRIX.md edit. It answers: what is cloned, what has been swept,
  what depends on what, what is the next unblocked task, and what is stale.
cross-refs:
  sweep-record: docs/design/MILFOLOGICAL_OPPORTUNITY_REPORT.md
  arch-map: docs/design/MILF_ARCH_MATRIX.md
  module-stubs: extensions/milfological/src/milfological/
---

# SD Candidate Registry — Mine Operations Ledger

---

## §1 — Candidate Index

### SD Inference Backends (5 candidates)

| ID | Candidate | Repo | Branch | Local Path | Clone | Sweep | Report §§ |
|----|-----------|------|--------|------------|-------|-------|-----------|
| C1 | SD.NEXT | vladmandic/automatic | main | `dev/sd-candidates/sdnext/` | ✅ | filesystem | §I–§IX |
| C2 | A1111 | AUTOMATIC1111/stable-diffusion-webui | master | `dev/sd-candidates/a1111/` | ✅ | filesystem | §III, §XVII |
| C3 | ComfyUI | comfyanonymous/ComfyUI | master | `dev/sd-candidates/comfyui/` | ✅ | filesystem | §X |
| C4 | InvokeAI | invoke-ai/InvokeAI | main | `dev/sd-candidates/invokeai/` | ✅ | filesystem | §XI |
| C5 | Forge | Panchovix/stable-diffusion-webui-forge | main¹ | `dev/sd-candidates/forge/` | ✅ | ⚠️ web-research + partial | §XII, §XIV |

¹ `py3.12` branch not found on Panchovix fork — cloned default/main. `modules_forge/` ✅ present.
  `extensions-builtin/sd_forge_layerdiffuse` ❌ absent — LayerDiffuse lives in `lllyasviel/stable-diffusion-webui-forge`,
  not the Panchovix fork. If LayerDiffuse is needed, clone `lllyasviel/` separately into `dev/sd-candidates/forge-ll/`.

### LLM Frontends (2 candidates — SD API consumers, not generators)

| ID | Candidate | Repo | Local Path | Clone | Sweep | Report §§ |
|----|-----------|------|------------|-------|-------|-----------|
| C6 | KoboldCpp | LostRuins/koboldcpp | `dev/sd-candidates/koboldcpp/` | ✅ | ⚠️ web-research only | §XVI.3 |
| C7 | oobabooga/textgen | oobabooga/text-generation-webui | `dev/sd-candidates/textgen/` | ✅ | ⚠️ web-research only | §XVI.4 |

### Extended Candidates (mine pass 1 web-research; see §6 for full profiles)

| ID | Candidate | Repo | Status | API | Clone | Priority |
|----|-----------|------|--------|-----|-------|---------|
| C8 | Fooocus | lllyasviel/Fooocus | STALE (Aug 2024) | None | ❌ Rejected | ❌ SKIP |
| C9 | SwarmUI | mcmonkeyprojects/SwarmUI | ACTIVE v0.9.8-Beta | ComfyUI WS | ❌ Rejected | LOW |
| C10 | sd.cpp | leejet/stable-diffusion.cpp | ACTIVE | CLI/webui (no sdapi) | Candidate | HIGH (GGUF lane) |
| C11 | forge-ll | lllyasviel/stable-diffusion-webui-forge | MAINTENANCE (11mo) | /sdapi/v1/ | DEFERRED | HIGH (LayerDiffuse) |
| C12 | Easy Diffusion | easydiffusion/easydiffusion | ACTIVE v3.0.16 | None (sdkit) | ❌ Rejected | ❌ SKIP |

### Niche Source-Code Candidates (mine-value axis — see §7 for classification frame + profiles)

| ID | Candidate | Repo | Mine Class | Clone | Priority |
|----|-----------|------|------------|-------|----------|
| C13 | Draw Things | drawthings-community/draw-things-community | TRANSLATE (Metal→Vulkan tiling) | ❌ Not needed | LOW |
| C14 | Pinokio | pinokio-computer/pinokio | SCHEMA (workflow topology) | ❌ Not needed | REFERENCE |
| C15 | Diffusion Bee | divamgupta/diffusionbee-stable-diffusion-ui | THIN-SHELL (→ C10 sd.cpp) | ❌ See [B6] | LOW |
| C16 | IREE-Turbine | iree-org/iree-turbine | PORTABLE (Vulkan SPIR-V via IREE) | `pip install` | MEDIUM |
| C17 | diffusion-rs | pykeio/diffusion-rs | PORTABLE (Rust binding → sd.cpp) | `cargo add` | MEDIUM |

---

## §2 — Sweep Coverage per Candidate

### C1 — SD.NEXT (filesystem swept ✅)
Key paths confirmed:
- `modules/caption/` — JoyCaption, WD Tagger, VQA
- `modules/postprocess/pixelart.py` — DCT pixel art processor
- `modules/ipadapter.py` — IP-Adapter
- `lora_extract.py`, `lora_nunchaku.py` — LoRA utilities
- `sdapi/v1/` REST surface — identical to A1111 surface

🔍 MINE cells remaining (from MILF_ARCH_MATRIX.md Layer 2):
- SD.NEXT block-level modifier depth vs Forge `patches_replace` — not yet compared

### C2 — A1111 (filesystem swept ✅)
Key paths confirmed:
- `modules/dat_model.py`, `modules/hat_model.py` — DAT/HAT upscalers
- `on_cfg_denoiser_step` hook — per-step callback (§XVII.1)
- `/sdapi/v1/` REST surface — reference standard

🔍 MINE cells remaining:
- GGUF pathway (Layer 10) — not present in base A1111

### C3 — ComfyUI (filesystem swept ✅)
Key paths confirmed:
- SAM3 video entity tracking nodes
- GLSL shader nodes
- In-graph fp4 LoRA trainer
- 20+ cloud API nodes (ElevenLabs, Kling, Veo2)
- `/api/` REST + JSON node graph + WebSocket surface

🔍 MINE cells remaining:
- Captioning node API contract (Layer 7) — path known, contract not mapped
- Per-step denoiser hook equivalent (Layer 2) — likely via `before_sampling` node

### C4 — InvokeAI (filesystem swept ✅)
Key paths confirmed:
- `invokeai/app/invocations/segment_anything.py` — Grounding DINO + SAM2
- Flux Kontext reference conditioning
- Z-Image regional prompting
- Multi-user isolation (DB-backed, named workflows)
- `/api/v1/` REST surface (named workflows, not raw txt2img)

🔍 MINE cells remaining:
- Interrogation/captioning endpoint (Layer 7) — not found yet
- LoRA injection detail (Layer 5)
- ESRGAN availability (Layer 9)

### C5 — Forge (WEB-RESEARCH ONLY — filesystem sweep pending ⚠️)
Mine pass 1 source: §XII (summary), §XIV (live state). No direct path verification.
Paths confirmed present (filesystem probe 2026-05-09):
- `modules_forge/` ✅ — contains: controlnet, diffusers_patcher, forge_loader, forge_sampler, forge_util
- `extensions-builtin/sd_forge_freeu/` ✅ — FreeU V2 (canonical UnetPatcher hook example)
- `extensions-builtin/sd_forge_layerdiffuse/` ❌ — NOT present (Panchovix fork)

🔍 MINE cells (high priority):
- `modules_forge/unet_patcher.py` — 8 patch keys + `patches_replace` + 3 modifier types — READ THIS
- `extensions-builtin/sd_forge_freeu/lib_free_u/freeu_v2.py` — canonical hook implementation pattern
- Forge py3.12 branch resolution (see ¹ note above)
- `/sdapi/v1/` compatibility surface (likely inherited from A1111 base)

### C6 — KoboldCpp (WEB-RESEARCH ONLY — filesystem sweep pending ⚠️)
Mine pass 1 source: §XVI.3. Root structure: `kcpp_adapters/`, `src/`, `common/`, `ggml/`.
`kcpp_adapters/` is the API surface directory (C++ adapter layer for A1111/ComfyUI/OpenAI APIs).
No `.py` API files — this is a C++ binary. Source sweep = reading C++ header/adapter files.

🔍 MINE cells:
- `kcpp_adapters/` — which endpoints implement A1111ForgeApi `/sdapi/v1/txt2img` and `/sdapi/v1/interrogate`
- Determine if koboldcpp → `backends/sdnext.py` is a thin wrapper (likely yes if /sdapi/v1/ is compatible)

### C7 — oobabooga/textgen (WEB-RESEARCH ONLY — filesystem sweep pending ⚠️)
Mine pass 1 source: §XVI.4. Root structure: `modules/`, `extensions/`, `server.py`.
`extensions/sd_api_pictures/` — confirmed present. This is the SD API consumer.

🔍 MINE cells:
- `extensions/sd_api_pictures/` — what SD backend API it calls, request contract
- TensorRT-LLM backend path (not SD-related; useful for tabbyAPI/LLM pipeline context)

---

## §3 — Module → Backend Dependency Map

| Module | Status | Backend Required | Sweep Prerequisites |
|--------|--------|-----------------|---------------------|
| `protocols.py` | NOT CREATED | Convergence surface (all SHARED rows) | Mine pass 1 ✅ (sufficient) |
| `backends/sdnext.py` | NOT CREATED | C1 API surface | C1 filesystem sweep ✅ |
| `backends/a1111.py` | NOT CREATED | C2 API surface | C2 filesystem sweep ✅ |
| `backends/invokeai.py` | NOT CREATED | C4 API surface | C4 filesystem sweep ✅ |
| `backends/comfyui.py` | NOT CREATED | C3 API + WebSocket | C3 filesystem sweep ✅ |
| `backends/forge.py` | NOT CREATED | C5 UnetPatcher API | **C5 modules_forge/ sweep ⚠️** |
| `backends/koboldcpp.py` | NOT CREATED | C6 A1111ForgeApi | **C6 kcpp_adapters/ sweep ⚠️** |
| `auto_caption.py` (refactor) | Tier 1 stub | C1 SDBackend | C1 ✅ → after protocols.py |
| `entity_cutout.py` (refactor) | Tier 1 stub | C4 SegmentationBackend | C4 ✅ → after protocols.py |
| `entity_pixelart.py` (refactor) | Tier 1 stub | C1 PixelArtBackend | C1 ✅ → after protocols.py |
| Future: `entity_unet_hook.py` | Not created | C5 UnetPatcher | **C5 modules_forge/ sweep ⚠️** |
| Future: `entity_lora_trainer.py` | Not created | C3 in-graph trainer | C3 ✅ (path confirmed) |
| Future: `entity_video_track.py` | Not created | C3 SAM3 | C3 ✅ (path confirmed) |
| Future: `entity_glsl_vfx.py` | Not created | C3 GLSL nodes | C3 ✅ (path confirmed) |
| Future: `entity_regional.py` | Not created | C4 Z-Image | C4 ✅ (path confirmed) |

---

## §4 — Task Sequence (prerequisite ordering)

```
UNBLOCKED NOW — all sweep prerequisites met:
  [S1]  Create protocols.py                 ← SHARED rows from mine pass 1 + arch matrix
  [S2]  Create backends/sdnext.py           ← C1 swept
  [S3]  Create backends/a1111.py            ← C2 swept
  [S4]  Create backends/invokeai.py         ← C4 swept
  [S5]  Create backends/comfyui.py          ← C3 swept
  [S6]  Refactor 3 Tier 1 stubs            ← DONE — wired to backend adapters (2026-05-09)

BLOCKED — pending filesystem sweeps:
  [B1]  Sweep C5 modules_forge/unet_patcher.py   → then [B2]
  [B2]  Create backends/forge.py                  → then [B3]
  [B3]  Create entity_unet_hook.py                ← after [B2]
  [B4]  Sweep C6 kcpp_adapters/                   → then [B5]
  [B5]  Create backends/koboldcpp.py              ← after [B4] (likely thin wrapper over sdnext.py)

OPTIONAL — C7 textgen sweep:
  [O1]  Sweep extensions/sd_api_pictures/         → confirm API contract
  [O2]  Document LLM↔SD API bridge pattern        ← reference for tabbyAPI lane

DEFERRED:
  - Gradio 4 frontend (gr.Blocks over protocols.py)

EXTENDED CANDIDATES — blocked on prioritization decision:
  [B6]  Clone sd.cpp → sweep Python binding (stable-diffusion-cpp-python)  → backends/sd_cpp.py
        Trigger: GGUF lane or Vulkan compute inference prioritized
  [B7]  Clone forge-ll (lllyasviel/stable-diffusion-webui-forge)
        → sweep extensions-builtin/sd_forge_layerdiffuse/
        → sweep modules_forge/unet_patcher.py canonical form
        → backends/forge_ll.py (LayerDiffuse + UnetPatcher)
        Trigger: sprite alpha pipeline or UnetPatcher hook prioritized

NICHE SOURCE-CODE CANDIDATES (§7) — source mine, no integration clone:
  [O3]  C13 Draw Things — read TiledDiffusion.swift; extract tiling algorithm for Vulkan compute
        Trigger: VRAM-constrained high-res generation is prioritized
  [O4]  C14 Pinokio — archaeology pass on app manifest corpus; reference only
  [O5]  C15 Diffusion Bee — read diffusion_bee/backend/ Python scripts; feeds [B6] design
  [O6]  C16 IREE-Turbine — install + sweep turbine_models/; Vulkan SPIR-V SD export
        Trigger: Vulkan compute inference (vulkan-lab/cli-renderer/) prioritized
  [O7]  C17 diffusion-rs — read src/lib.rs; Rust API surface reference for vulkan-lab Cargo stack
        Trigger: Rust-native SD inference in vulkan-lab/ is prioritized

REJECTED — not worth further investment:
  [R1]  Fooocus (C8) — GPL-3.0 + stale + SDXL-only + no HTTP API
  [R2]  SwarmUI (C9) — C# frontend, Python hard-capped at 3.12
  [R3]  Easy Diffusion (C12) — CreativeML RAIL-M license + no HTTP API
```

---

## §5 — Stale Detection

All clones are `--depth=1` shallow. A clone is stale when upstream has significant commits since the clone date.

```powershell
# Refresh any single candidate:
git -C dev/sd-candidates/<name> pull --depth=1

# Check upstream delta (does not write):
git -C dev/sd-candidates/<name> fetch --dry-run
```

A module stub is stale if its backend's key source path has changed since the sweep date.
After any `pull`, re-verify:
- C1 SD.NEXT: `modules/caption/`, `modules/postprocess/pixelart.py` still exist
- C4 InvokeAI: `invokeai/app/invocations/segment_anything.py` still exists
- C5 Forge: `modules_forge/unet_patcher.py` (or equivalent) still exists

Mine pass counter: increment after each systematic sweep of a new candidate.
Current mine pass: **1** (SD.NEXT, A1111, ComfyUI, InvokeAI: fully swept; Forge partial; KoboldCpp/textgen: web-research).

---

## §6 — Extended Candidate Assessment (Mine Pass 1 — Web-Research Only)

Research date: 2026-05-09. No filesystem sweeps performed. All data from GitHub metadata.

### API Pattern Taxonomy (updated after extended sweep)

| Pattern | Used By |
|---------|---------|
| A1111 `/sdapi/v1/` REST | SD.NEXT, A1111, Forge (both), KoboldCpp |
| ComfyUI WebSocket + JSON graph | ComfyUI, SwarmUI (as backend) |
| InvokeAI `/api/v1/` named workflows | InvokeAI |
| CLI subprocess / embedded webui | sd.cpp |
| sdkit direct (no HTTP API) | Fooocus, Easy Diffusion |

---

### C8 — Fooocus

| Field | Value |
|-------|-------|
| Repo | lllyasviel/Fooocus |
| Status | **STALE — LTS/bug-fix-only** |
| Last active release | v2.5.5 — August 2024 |
| License | GPL-3.0 |
| Stars | 48.4k |
| Stack | Python |
| Models | SDXL only |
| HTTP API | ❌ None — ldm_patched direct, no `/sdapi/v1/` |
| DSLs | Wildcards `__color__`, array `[[red,green]]`, inline LoRA `<lora:name:1.2>`, JSON presets |
| MINE priority | ❌ SKIP — GPL-3.0 contamination risk + stale + SDXL-only + no HTTP API |
| Clone | ❌ Not cloned — waste of depth-1 bandwidth |

---

### C9 — SwarmUI

| Field | Value |
|-------|-------|
| Repo | mcmonkeyprojects/SwarmUI |
| Status | **ACTIVELY MAINTAINED** — v0.9.8-Beta, commit 3 days ago |
| License | MIT |
| Stars | 4.1k |
| Stack | C# 54.6%, JS 32.1%, Python 4.0% |
| Runtime | DotNET 8 SDK + Python 3.10–3.12 (NOT 3.13/3.14) |
| Port | localhost:7801 |
| Primary backend | ComfyUI (auto-installed) — optionally A1111 |
| HTTP API | Wraps ComfyUI WebSocket API; own HTTP layer on top |
| DSLs | `<segment:yolo-...>` YOLO segmentation syntax |
| Python 3.14 compat | ❌ Hard cap at 3.12 |
| MINE priority | LOW — C# frontend, no direct Python library surface; reference value only for multi-backend routing pattern |
| Clone | ❌ Not cloned — C# frontend outside Python asset pipeline scope |

---

### C10 — stable-diffusion.cpp

| Field | Value |
|-------|-------|
| Repo | leejet/stable-diffusion.cpp |
| Status | **ACTIVELY MAINTAINED** — 450 releases, last commit 2 days ago |
| License | MIT |
| Stars | 6k |
| Stack | C++ 100% |
| Interface | CLI (`sd-cli` binary) + embedded webui (sdcpp-webui, added PR #1408 April 2026) |
| Compute backends | CPU, CUDA, Vulkan, Metal, OpenCL, SYCL |
| Models | SD1.x/2.x, SDXL, SD3/3.5, FLUX.1/2, Chroma, Wan, Qwen, Z-Image, Ovis, Anima, ERNIE |
| Formats | `.ckpt`, `.safetensors`, `.gguf` — converts to GGUF internally |
| HTTP API | ❌ CLI only by default; embedded webui via `--listen` (NOT `/sdapi/v1/`) |
| Python binding | `william-murray1204/stable-diffusion-cpp-python` (separate repo) |
| Rust binding | `diffusion-rs` |
| Used by | KoboldCpp (as SD backend for image generation) |
| MINE priority | **HIGH** — GGUF support + Vulkan backend aligns with repo's GPU lane; Python binding enables `backends/sd_cpp.py` |
| Clone | ✅ Candidate for `dev/sd-candidates/sd-cpp/` — clone when GGUF lane is prioritized |
| Task ID | [B6] — see §4 update |

---

### C11 — forge-ll (lllyasviel/stable-diffusion-webui-forge)

| Field | Value |
|-------|-------|
| Repo | lllyasviel/stable-diffusion-webui-forge |
| Status | **MAINTENANCE MODE** — last commit 11 months ago (Aug 2024) |
| License | AGPL-3.0 |
| Stars | 12.5k |
| Stack | Python 94.2%, JavaScript 2.0%, CUDA 1.7% |
| Base | SD-WebUI 1.10.1 (syncs every 90 days) |
| HTTP API | ✅ `/sdapi/v1/` compatible — "Normal" per Forge Status table |
| UnetPatcher | ✅ Canonical `modules_forge/unet_patcher.py` — 8 patch keys + `patches_replace` |
| LayerDiffuse | ✅ `extensions-builtin/sd_forge_layerdiffuse/` — PRESENT (unlike Panchovix fork C5) |
| GGUF support | ✅ `packages_3rdparty/` — BF16 + GGUF Q8/Q5/Q4 with NF4 BitsandBytes |
| DSLs | Inherited from A1111 base (schedules, LoRA inline `<lora:name:1.0>`) |
| MINE priority | **HIGH** — canonical LayerDiffuse source for sprite alpha pipeline; canonical UnetPatcher |
| Clone | DEFERRED → `dev/sd-candidates/forge-ll/` — clone when LayerDiffuse or UnetPatcher hook is prioritized |
| Task ID | [B7] — see §4 update (was previously DEFERRED without ID) |

---

### C12 — Easy Diffusion

| Field | Value |
|-------|-------|
| Repo | easydiffusion/easydiffusion |
| Status | **ACTIVE** — v3.0.16 Mar 2026, last commit 2 weeks ago |
| License | **CreativeML Open RAIL-M** — custom restricted license (NOT standard OSS) |
| Stars | 10.4k |
| Stack | JavaScript 68.3%, Python 16.5% |
| Backend | sdkit library (internal) — NOT A1111 API compatible |
| HTTP API | ❌ No `/sdapi/v1/` — sdkit direct only |
| Models | SDXL, SD2.1, Z-Image, FLUX 1/2 (v3.5/v4 engines), quantized |
| DSLs | `+`/`-` attention, `(word)2.4` weights, `\|` prompt matrix, `{moon,earth}` prompt set |
| Python 3.14 compat | Unknown — sdkit dependency; likely not tested on 3.14 |
| MINE priority | ❌ SKIP — non-standard license risk + non-standard API (no sdkit → protocols.py bridge path) |
| Clone | ❌ Not cloned — license incompatibility blocks integration into MILFOLOGICAL pipeline |

---

## §7 — Niche Source-Code Candidates (Mine-Value Axis: Source Code, Not Runtime OS)

> **Classification axis correction (2026-05-09):**
> Prior triage dismissed macOS-native and niche candidates based on runtime OS portability.
> That framing is wrong for mining purposes. The correct question is not *"can we run this app?"* but *"does the source code contain patterns worth extracting?"* Whether a candidate's code is relevant depends on: (1) what algorithmic or architectural patterns are embedded in the source; (2) whether those patterns translate to the MILFOLOGICAL pipeline — directly (PORTABLE) or via translation work (TRANSLATE); (3) whether the codebase expands the total mine surface. Even outlandish or OS-bound approaches contribute to the scope and quality of the batch. The runtime is a deployment detail. The source is the mine.
>
> **The rule:** *"whether it is OS relevant is dependent on how we use the underlying code and scope of it all, not the runtime."*

### Source Code Mine Classification

| Class | Meaning | Action |
|-------|---------|--------|
| **PORTABLE** | OS-independent at source — patterns directly usable or minimally ported | Clone/install; sweep for protocol patterns and inference graph topology |
| **TRANSLATE** | OS-bound bindings (Metal, Core ML, ANE) but portable algorithmic core — tiling, scheduling, quantization logic translates to Vulkan/CUDA | Read source; extract algorithm, ignore runtime bindings |
| **SCHEMA** | No inference code — value is in configuration topology, workflow definitions, or app registry patterns | Archaeology pass only; do not clone |
| **THIN-SHELL** | App wrapper over a known backend candidate — mine value routes entirely to the parent backend entry | Cross-reference parent; no independent clone needed |
| **REJECT** | No extractable patterns, or license blocks extraction | Skip |

---

### C13 — Draw Things

| Field | Value |
|-------|-------|
| Repo | drawthings-community/draw-things-community |
| Status | **ACTIVE** — Apple Seed program, continuous updates |
| License | MIT-compatible (check distribution clauses for model weights) |
| Stars | 6.5k+ |
| Stack | Swift 80%, Objective-C 12%, Metal (inline compute shaders) |
| Runtime | macOS / iOS — Core ML + Apple Neural Engine |
| Mine class | **TRANSLATE** — OS-bound at bindings layer, portable at algorithm layer |
| Key source patterns | (1) **Tiled inference** — `TiledDiffusion` splits high-res generation into overlapping tiles, denoises per-tile with seam blending; translates to VRAM-efficient Vulkan compute tiling. (2) **LoRA merge at inference time** — weight-merge approach (not A1111 patch-style); different tradeoff surface. (3) **Metal compute shaders** for attention — FlashAttention-equivalent in Metal; topology translates to Vulkan GLSL or CUDA. (4) **Core ML model pipeline** — .safetensors → .mlpackage compilation; packaging approach is reference for any model-to-native-runtime conversion. |
| Mine priority | LOW — tiling pattern is the extractable gold; Core ML bindings are noise |
| Clone | ❌ Not needed — read source via GitHub; key files: `Sources/DataModels/`, `Libraries/SwiftDiffusion/` |
| Axis note | "macOS only" is a runtime fact, not a mine fact. The tiling algorithm in `TiledDiffusion.swift` is architecture-neutral. |

---

### C14 — Pinokio

| Field | Value |
|-------|-------|
| Repo | pinokio-computer/pinokio |
| Status | **ACTIVE** — v3.x, continuously updated |
| License | CC0 (launcher code); individual app scripts vary |
| Stars | 13k+ |
| Stack | JavaScript / Node.js / Electron |
| Runtime | macOS, Windows, Linux (cross-platform Electron) |
| Mine class | **SCHEMA** — no inference code; value is in ecosystem topology |
| Key source patterns | (1) **Pinokio app manifest format** (`.pinokio` JSON) — declarative spec for AI app install/configure/run chains. 200+ apps registered. (2) **Workflow topology corpus** — each app's manifest describes how to sequence downloads, conda/venv setup, backend start, and API endpoint exposure. This is a structured corpus of AI deployment patterns. (3) **Multi-backend routing** — some app manifests chain SD + LLM + ControlNet. Reference for integration topology. |
| Mine priority | REFERENCE — no inference code to mine; topology archaeology only. The manifest corpus is a secondary reference when designing MILFOLOGICAL's workflow orchestration layer. |
| Clone | ❌ Not needed — manifests readable via GitHub. Core inference value: nil. |
| Axis note | "App runner, limited relevance" is only true for the runner code itself. The manifest ecosystem is a topology database. |

---

### C15 — Diffusion Bee

| Field | Value |
|-------|-------|
| Repo | divamgupta/diffusionbee-stable-diffusion-ui |
| Status | **ACTIVE** — v3.x updates |
| License | Custom (check before any redistribution) |
| Stars | 7.5k+ |
| Stack | Swift (UI shell) + Python backend scripts + sd.cpp (C++ binary) |
| Runtime | macOS only |
| Mine class | **THIN-SHELL** — Swift UI wraps Python scripts that wrap sd.cpp binary |
| Key source patterns | (1) **Python invocation scripts** in `diffusion_bee/backend/` — show how sd.cpp is called programmatically from Python: subprocess management, progress parsing, model path resolution. Directly informs [B6] `backends/sd_cpp.py` design. (2) **CLI argument schema** — the set of flags passed to sd.cpp via Python; cross-references C10's CLI surface. |
| Mine priority | LOW — value routes entirely to C10. Read `diffusion_bee/backend/` when implementing [B6]; do not clone repo. |
| Clone | ❌ Not needed — cross-reference C10 (sd.cpp) [B6]. Python backend scripts readable via GitHub. |
| Axis note | "macOS only" describes the UI shell. The Python backend scripts have zero macOS-specific code. |

---

### C16 — IREE-Turbine

| Field | Value |
|-------|-------|
| Repo | iree-org/iree-turbine |
| Status | **ACTIVE** — IREE project / Google Research |
| License | Apache 2.0 |
| Stars | 800+ |
| Stack | Python 78%, C++ (IREE runtime) |
| Runtime | Cross-platform — Linux, macOS, Windows; compute: CUDA, Vulkan, Metal, CPU |
| Mine class | **PORTABLE** — purely Python API; OS-independent |
| Key source patterns | (1) **IREE compiler** — lowers PyTorch `nn.Module` graphs to MLIR → compiles to Vulkan SPIR-V, CUDA PTX, or CPU. This is a model-to-Vulkan-shader compilation pipeline, directly aligned with the Vulkan GPU lane in this repo. (2) **`turbine_models/`** — pre-built IREE export pipelines for SD models (SDXL, SD3, FLUX). The export scripts show how to extract a computation graph from a diffusers model and lower it to hardware-specific kernels. (3) **Vulkan command graph patterns** — IREE's Vulkan HAL generates synchronization-correct command buffers; reference for multi-pass Vulkan compute pipelines. |
| Mine priority | MEDIUM — Vulkan SPIR-V generation for SD models aligns with `vulkan-lab/`. No HTTP API; not an inference server. Mine value is at the GPU compute / shader compilation layer, not at the backend adapter layer. |
| Clone | `pip install iree-turbine` (PyPI) or `git clone --depth=1 https://github.com/iree-org/iree-turbine` when Vulkan compute inference is prioritized. |
| Axis note | No OS dependency at source. Directly portable to any platform with a Vulkan driver. |

---

### C17 — diffusion-rs

| Field | Value |
|-------|-------|
| Repo | pykeio/diffusion-rs |
| Status | **ACTIVE** — Rust crate, crates.io published |
| License | Apache 2.0 |
| Stars | 700+ |
| Stack | Rust 95%, GLSL shaders |
| Runtime | Cross-platform — Windows, Linux, macOS; Vulkan, CUDA, Metal backends |
| Mine class | **PORTABLE** — pure Rust; OS-independent |
| Key source patterns | (1) **Rust API over sd.cpp** — wraps the sd.cpp C library with a safe Rust interface; `DiffusionModel::new()` / `generate()` / `img2img()`. This is the Rust equivalent of the Python `stable-diffusion-cpp-python` binding — directly relevant if `backends/sd_cpp.py` [B6] has a Rust counterpart in `vulkan-lab/`. (2) **GLSL compute shaders** included — custom Vulkan shader pipeline for image processing steps. (3) **Cross-backend dispatch** (Vulkan / Metal / CPU) via sd.cpp's backend enum; the dispatch architecture is reference for `vulkan-lab/` multi-backend design. |
| Mine priority | MEDIUM — directly relevant to `vulkan-lab/cli-renderer/` Cargo stack + [B6] sd.cpp lane. `cargo add diffusion-rs` is the integration path; no repo clone needed. |
| Clone | `cargo add diffusion-rs` — not a source clone. Read crate docs + `src/lib.rs` via GitHub for API surface. |
| Axis note | Pure Rust, zero OS-specific code at the library layer. Vulkan and Metal are selectable backends, not requirements. |
