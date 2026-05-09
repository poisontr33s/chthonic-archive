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

### DSL / Schema / Corpus Candidates (character card, data pipeline, ANSI art — see §8)

| ID | Candidate | Source | Mine Class | Clone | Priority |
|----|-----------|--------|------------|-------|----------|
| C18 | SillyTavern CharCard V2 | SillyTavern/SillyTavern | SCHEMA (entity metadata DSL) | ❌ Spec only | HIGH |
| C19 | Seed-and-Evolve pipeline | arxiv 2603.14505 | PORTABLE (generative seeding) | ❌ Paper mine | MEDIUM |
| C20 | ASCII Cat LoRA | vossenwout/ascii-cat-llm-finetuning | PORTABLE (spatial LoRA recipe) | ❌ Ref read | MEDIUM |
| C21 | ZX-Art ANSI corpus | zxart.ee | SCHEMA/REFERENCE (block-char atlas) | ❌ Corpus only | MEDIUM |
| C22 | Awesome-Local-LLM + Firecrawl | rafska/awesome-local-llm | SCHEMA (Markdown pipeline ref) | ❌ Ref read | LOW |

### Interactive Fiction Frontends (narrative loop, CharBook, multi-AI — see §9)

| ID | Candidate | Repo | Mine Class | Clone | Priority |
|----|-----------|------|------------|-------|----------|
| C23 | agnaistic/agnai | agnaistic/agnai | PROTOCOL+SCHEMA (CharBook stacking, multi-AI, multi-tenant) | ❌ Web-research | HIGH |
| C24 | agn-ai early fork | malfoyslastname/agn-ai | LINEAGE (design-philosophy baseline, pre-MongoDB optionality) | ❌ Diff ref only | LOW |
| C25 | AIDungeon2 | latitudegames/AIDungeon | SCHEMA (narrative tree data pipeline, story-loop format) | ❌ Archived corpus | MEDIUM |

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

DSL / SCHEMA / CORPUS CANDIDATES (§8) — no clone; spec/paper/corpus archaeology:
  [O8]  C18 SillyTavern CharCard V2 — read SillyTavern src/character-card-validator.js + spec
        → extract: entity metadata schema ({{user}}/{{char}}/{{description}}/{{personality}}/{{scenario}})
        → target: MILFOLOGICAL entity card format (entity_card.py stub + JSON schema)
        Trigger: entity metadata layer is prioritized
  [O9]  C19 Seed-and-Evolve — read arxiv.org/html/2603.14505v1
        → extract: seed-fragment → iterative completion pipeline for sprite/content generation
        → target: entity sprite seeding approach in entity_pixelart.py pipeline
        Trigger: iterative entity sprite generation is prioritized
  [O10] C20 ASCII Cat LoRA — read vossenwout/ascii-cat-llm-finetuning training scripts
        → extract: LoRA dataset format, fine-tune recipe for ASCII spatial reasoning
        → target: entity LoRA training lane design doc
        Trigger: entity-specific LoRA fine-tuning lane is prioritized
  [O11] C21 ZX-Art ANSI corpus — archaeology pass on zxart.ee block-char atlas
        → extract: block-char + ANSI truecolor escape palette reference
        → target: vulkan-lab G3 ascii_downsample.comp.glsl block-char selection
        Trigger: vulkan-lab G3 ASCII framebuffer is next
  [O12] C22 Awesome-Local-LLM + Firecrawl — read repo markdown pipeline
        → extract: visual web → LLM-ready Markdown conversion pipeline
        → target: roleplay context generation in entity card DSL
        Trigger: entity card DSL generation pipeline is prioritized

INTERACTIVE FICTION CANDIDATES (§9) — multi-AI narrative frontends, CharBook schema:
  [O13] C23 agnai — sweep agnaistic/agnai common/ + srv/ + web/
        → extract: CharacterBook stacking (key-trigger semantics, priority weighting)
        → extract: multi-AI service adapter contract (KoboldCpp, OpenAI, Claude, OpenRouter)
        → extract: multi-tenant isolation (MongoDB-optional JSON storage fallback)
        → target: entity_card.py CharacterBook + LoreEntry design refinement; adapter ref
        Trigger: UNBLOCKED — entity card format stabilized (1b086bb1 committed)
  [O14] C24 agn-ai early fork — read Design Goals section + early srv/ pre-MongoDB-optional state
        → extract: "low-friction self-hosting, no native deps, no Docker" principle
        → extract: diff vs agnai:dev to understand evolution trajectory (what was added in 953 commits)
        → target: MILFOLOGICAL pipeline portability design philosophy
        Trigger: self-host deployment design decision for MILFOLOGICAL inference stack
  [O15] C25 AIDungeon2 — read story/story_manager.py + data/ JSON schema
        → extract: story-tree format (tree_id / story_start / action_results nesting)
        → extract: GPT-2 fine-tune text format (<|startoftext|> / action-result interleaving)
        → target: narrative loop data format reference for entity roleplay pipeline
        Trigger: narrative loop (interactive fiction engine) is prioritized above SD integration

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

---

## §8 — DSL / Schema / Corpus Candidates (Entity Card, Data Pipeline, ANSI Art)

> **Mine axiom for §8:** The MILFOLOGICAL pipeline requires three things beyond image generation: (1) a structured entity metadata format (character card DSL), (2) a generative seeding strategy for iterative content completion, and (3) a reference corpus for the ASCII/ANSI renderer (vulkan-lab G3). These candidates supply all three. No source clones required — spec archaeology + paper reads + corpus reference.

> **New mine axis — DSL sophistication:** SillyTavern's CharCard V2 system constitutes a domain-specific language for entity metadata. `{{user}}`, `{{char}}`, `{{description}}`, `{{personality}}`, `{{scenario}}` are not mere template variables — they are semantic interpolation anchors that govern scene-conditional behavior, art injection, and symbolic interaction. This DSL surface is architecturally richer than standard Python/JSON schemas and maps directly to MILFOLOGICAL entity representation needs.

---

### C18 — SillyTavern Character Card V2 (Entity Metadata DSL)

| Field | Value |
|-------|-------|
| Source | github.com/SillyTavern/SillyTavern + [CharCard V2 spec](https://github.com/malfoyslastname/character-card-spec-v2) |
| Status | **ACTIVE** — production frontend for local LLM character roleplay |
| License | AGPL-3.0 |
| Stack | Node.js + TypeScript + Handlebars-style template DSL |
| Mine class | **SCHEMA** — entity metadata DSL with interpolation semantics |
| Key source patterns | (1) **Variable interpolation DSL**: `{{user}}`, `{{char}}`, `{{description}}`, `{{personality}}`, `{{scenario}}`, `{{system_prompt}}`, `{{wiBefore}}`, `{{wiAfter}}` — scene-conditional text injection. (2) **Character card JSON schema**: `name`, `description`, `personality`, `scenario`, `first_mes`, `mes_example`, `system_prompt`, `post_history_instructions`, `tags[]`, `creator_notes`. (3) **World Info (lorebook)** entries: key-triggered context injection — effectively a semantic memory system for entity attributes. (4) **Asset attachment** in PNG metadata (Exif UserComment base64-encoded JSON) — entity card is portable as a single PNG. |
| Mine priority | **HIGH** — directly maps to MILFOLOGICAL entity card format. The CharCard V2 JSON schema is the canonical external reference for designing `entity_card.py` + `schemas/entity_card.json`. |
| Immediate action | [O8]: Read `SillyTavern/src/character-card-validator.js` (validation logic) + CharCard V2 spec markdown. Extract field inventory → draft `extensions/milfological/src/milfological/entity_card.py` stub with matching schema. |
| Axis note | DSL semantics go beyond Python/JSON — interpolation anchors enable symbolic scene interaction. The PNG metadata embedding is a portability pattern worth adopting for MILFOLOGICAL entity assets. |

---

### C19 — Seed-and-Evolve Data Pipeline (arxiv 2603.14505)

| Field | Value |
|-------|-------|
| Source | [arxiv.org/html/2603.14505v1](https://arxiv.org/html/2603.14505v1) |
| Status | **2025 paper** — data generation technique, no repo clone needed |
| License | Academic (open access) |
| Stack | LLM prompting strategy + iterative completion |
| Mine class | **PORTABLE** — generative seeding pipeline technique |
| Key source patterns | (1) **Seed fragment seeding**: provide a partial ASCII/visual fragment and instruct the model to complete the visual sequence. Bypasses the model's reflexive refusal by framing completion as a continuation task rather than a generation task. (2) **Iterative evolution**: each completion becomes the seed for the next pass — produces progressive refinement without a single high-complexity prompt. (3) **Spatial reasoning probe**: the technique reveals fine-tuned vs. base model differences in spatial ASCII generation quality — relevant to LoRA evaluation. |
| Mine priority | **MEDIUM** — technique maps directly to `entity_pixelart.py` iterative sprite generation. The seed-fragment approach is the basis for the `pixelart_entity()` pipeline extension beyond single-pass generation. |
| Immediate action | [O9]: Read paper §3-§4 (methodology). Extract seeding schema → add `seed_and_evolve()` stub in `entity_pixelart.py` with docstring describing the iterative completion contract. |
| Axis note | The key insight: completion framing outperforms generation framing for spatially structured outputs. Directly actionable in the pixelart pipeline without any model fine-tuning. |

---

### C20 — ASCII Cat LoRA (vossenwout/ascii-cat-llm-finetuning)

| Field | Value |
|-------|-------|
| Source | github.com/vossenwout/ascii-cat-llm-finetuning |
| Status | **ACTIVE** — Llama 3.2 3B LoRA for ASCII spatial generation |
| License | MIT |
| Stack | Python + HuggingFace PEFT + LoRA |
| Mine class | **PORTABLE** — fine-tuning recipe for ASCII spatial reasoning |
| Key source patterns | (1) **Dataset format**: ASCII art examples as text completions — input is a partial cat ASCII, output is the completed art. (2) **LoRA config**: target modules (`q_proj`, `v_proj`), rank (r=16), alpha=32 — reference config for entity-specific LoRA. (3) **Tokenization quirk**: ASCII art requires `add_special_tokens=False` and careful padding to preserve spatial structure. (4) **Evaluation metric**: character-level spatial accuracy, not semantic similarity — defines how to benchmark ASCII generation quality. |
| Mine priority | **MEDIUM** — provides the training recipe template for MILFOLOGICAL entity LoRA fine-tuning lane. The dataset format + LoRA config are directly adaptable. |
| Immediate action | [O10]: Read `train.py` + dataset loader. Extract LoRA config defaults + dataset schema → draft `extensions/milfological/src/milfological/entity_lora_train.py` stub with config dataclass. |
| Axis note | Models with spatial LoRA handle block-char ASCII generation qualitatively differently — spatial tokens are treated as positional rather than semantic. This is the foundation of the entity ASCII rendering lane. |

---

### C21 — ZX-Art ANSI Corpus (zxart.ee)

| Field | Value |
|-------|-------|
| Source | [zxart.ee/spa/software/tags/](https://zxart.ee/spa/software/tags/) + [Amiga-Stuff PD archives](https://www.amiga-stuff.com/pd/17bit.html) |
| Status | **ACTIVE** — community-curated ZX Spectrum and Amiga ANSI/ASCII art archive |
| License | Community archive — individual works vary; reference use |
| Stack | ANSI escape sequences + ZX block graphics (`█▀▄░▒▓` charset) + Amiga ANSi color palette |
| Mine class | **SCHEMA / REFERENCE** — block-char atlas + ANSI truecolor escape palette |
| Key source patterns | (1) **ZX block graphics charset**: `U+2580–U+259F` half-block characters + `U+2588` full block — the canonical set for the vulkan-lab G3 `ascii_downsample.comp.glsl` block-char selection. (2) **ANSI color palette**: 4-bit (16 color CGA/EGA), 8-bit (256 xterm), 24-bit truecolor escape sequences — reference for the ANSI truecolor stdout in G3. (3) **Composition patterns**: how professional ANSI artists pack spatial density — border patterns, shading gradients, orbital border motifs — direct reference for the CLI renderer's visual output style. |
| Mine priority | **MEDIUM** — directly feeds vulkan-lab G3 design. Block-char selection for `ascii_downsample.comp.glsl` should be driven by this corpus. |
| Immediate action | [O11]: Browse zxart.ee `tags/ascii` + Amiga-Stuff 17bit archive. Catalogue block-char palette + ANSI escape sequences used. Write `vulkan-lab/cli-renderer/docs/ANSI_BLOCKCHAR_REFERENCE.md` with the canonical char set + escape sequence table. |
| Axis note | The ZX/Amiga ANSI corpus is the "Orbiter" source — dense geometric border patterns that the ANSI renderer can produce. These are not safety-bypass techniques; they are compositional reference patterns for the block-char renderer. |

---

### C22 — Awesome-Local-LLM + Firecrawl (Markdown Pipeline Reference)

| Field | Value |
|-------|-------|
| Source | github.com/rafska/awesome-local-llm + github.com/mendableai/firecrawl |
| Status | **ACTIVE** — curated tool list + visual web → Markdown conversion service |
| License | MIT (both) |
| Stack | Markdown curation + Node.js/Python web scrape → Markdown pipeline |
| Mine class | **SCHEMA** — Markdown conversion pipeline for roleplay context generation |
| Key source patterns | (1) **Firecrawl API**: `POST /v1/scrape` with `formats: ["markdown"]` — converts any URL to LLM-ready Markdown. Output schema: `{ markdown: string, metadata: { title, description, sourceURL } }`. (2) **Awesome-Local-LLM taxonomy**: categorizes local LLM tools into frontends / backends / fine-tuning / evaluation — directly applicable to SD_CANDIDATE_REGISTRY classification axis refinement. (3) **Roleplay context generation pattern**: visual web content → Firecrawl → Markdown → CharCard V2 `{{description}}` field — the pipeline for generating entity card content from visual references. |
| Mine priority | **LOW** — useful for entity card content generation automation; not critical path. |
| Immediate action | [O12]: Skim rafska/awesome-local-llm README. Extract any tools not yet in registry. Note Firecrawl API schema for potential `entity_card_generator.py` content pipeline. |
| Axis note | Firecrawl's Markdown output is structurally compatible with CharCard V2 `{{description}}` and `{{scenario}}` fields — enabling a web-reference → entity card pipeline with no manual formatting. |

---

## §9 — Interactive Fiction Frontend Candidates (Narrative Loop, CharBook, Multi-AI)

> **Mine axiom for §9:** The MILFOLOGICAL entity pipeline requires a narrative interaction surface — not just static metadata. Interactive fiction frontends (agnai, AI Dungeon lineage) supply three things the SD backend sweep did not: (1) CharacterBook stacking semantics (key-triggered context injection as a live memory system), (2) multi-AI service adapter contracts (how a frontend abstracts KoboldCpp vs. Claude vs. OpenAI into a unified inference call), and (3) narrative tree data schemas (how story state is represented, persisted, and forked). These are architectural inputs to the MILFOLOGICAL entity roleplay pipeline, not competitor systems.

> **Lineage note — malfoyslastname:** `malfoyslastname/agn-ai` is the original fork that later merged back as contributor activity into `agnaistic/agnai`. The fork is 953 commits behind `agnaistic/agnai:dev` as of 2026-05. It is NOT a separate product — it is a **design-origin snapshot**. The CharCard V2 spec (`malfoyslastname/character-card-spec-v2`) is an independent, high-signal artifact from the same author. The fork's "Design Goals" section reveals the self-hosting philosophy that shaped agnai: low-friction, no Docker mandate, no native deps, JSON storage fallback. Mine value = design archaeology, not source integration.

---

### C23 — agnaistic/agnai (Interactive Fiction Frontend — Canonical)

| Field | Value |
|-------|-------|
| Source | github.com/agnaistic/agnai |
| Status | **ACTIVE** — last commit ~5 days ago (2026-05). 730 stars, 41 contributors, 136 forks. npm package `agnai`. |
| License | AGPL-3.0 |
| Stack | TypeScript 96.4% + SolidJS (frontend) + pnpm v8 (internally) + MongoDB (optional) + Redis (optional). No native addons — **bun-translatable**. |
| Mine class | **PROTOCOL + SCHEMA** — CharBook stacking semantics, multi-AI adapter contract, multi-tenant isolation, sprite system, group conversation architecture |
| Key source patterns | **(1) CharacterBook stacking**: `common/presets/` + lorebook handling — key-trigger semantics (regex/substring matching against dialogue → inject world-info entry into context window at configured priority). Multiple books stack additively. Priority weighting controls insertion order. Maps directly to `CharacterBook` / `LoreEntry` in `entity_card.py`. **(2) Multi-AI service adapter contract**: `srv/adapter/` — each AI service (KoboldCpp, Novel, AI Horde, OpenAI, Claude, Replicate, OpenRouter, Mancer, Goose) implements a common interface: `generate(opts: AdapterOpts): AsyncIterable<string>`. This is the canonical multi-AI abstraction surface. **(3) Multi-tenant isolation**: user-scoped character cards + chat histories, MongoDB-optional (JSON storage fallback for single-user self-hosting). Demonstrates how to scope entity metadata to a user session. **(4) Sprite system**: character image attachment (portrait + emote variants) tied to character card, displayed reactively via SolidJS signals on dialogue triggers. Architecture reference for MILFOLOGICAL avatar/sprite pipeline. **(5) Memory + summarization**: rolling context summarization to stay within token budget — reference for entity session memory management. |
| Mine priority | **HIGH** — CharBook stacking semantics directly refine `entity_card.py` `CharacterBook`/`LoreEntry` design. Multi-AI adapter is the reference contract for a future `backends/agnai_adapter.py`. UNBLOCKED: entity_card.py committed (1b086bb1). |
| Immediate action | [O13]: Web-sweep `agnaistic/agnai` `common/` (CharacterBook schema fields + stacking logic), `srv/adapter/` (adapter interface contract). Extract: (a) lorebook key-trigger regex semantics, (b) priority weighting scheme, (c) per-adapter generate() signature. Refine `entity_card.py` `LoreEntry` fields if gaps found. |
| Axis note | agnai's bun-translatability is strategic: its frontend+backend can be rebuilt on bun without native module issues. The SolidJS reactive model maps cleanly to a Tauri+SolidJS desktop shell if a native MILFOLOGICAL client is ever needed. |

---

### C24 — malfoyslastname/agn-ai (Design-Origin Snapshot — LINEAGE REFERENCE)

| Field | Value |
|-------|-------|
| Source | github.com/malfoyslastname/agn-ai |
| Status | **FROZEN** — 953 commits behind `agnaistic/agnai:dev`. Last meaningful commit ~3 years ago. 0 stars, 1 fork. malfoyslastname is an active contributor to the upstream (agnaistic/agnai). |
| License | AGPL-3.0 (inherited) |
| Stack | Same as C23 at a much earlier stage — no MongoDB optionality, simpler adapter surface |
| Mine class | **LINEAGE** — design philosophy origin, evolution diff baseline |
| Key source patterns | **(1) Design Goals section** (README): "high quality codebase, low friction self-hosting, avoid native deps, avoid Docker mandate, JSON storage fallback as default" — the philosophical north star that shaped agnai's architecture. **(2) Pre-MongoDB-optional state**: early `srv/` shows what the system looked like before storage was abstracted — useful for understanding which abstractions were later-added vs. original. **(3) Diff signal**: 953-commit delta between agn-ai:main and agnai:dev shows the complete evolution of features (memory, group chat, multi-tenancy, image gen, sprite system, OpenRouter) — useful for understanding what the system gained over 3 years. |
| Mine priority | **LOW** — no standalone clone needed. Reference only via diff archaeology (GitHub Compare UI). The CharCard V2 spec (`malfoyslastname/character-card-spec-v2`) is a higher-value artifact from the same author and is already captured in C18. |
| Immediate action | [O14]: Read malfoyslastname/agn-ai README Design Goals section. Extract self-host philosophy principles → add to MILFOLOGICAL pipeline design docs as portability axioms. |
| Axis note | The author's most durable contribution is the CharCard V2 spec (C18), not the fork. The fork is historical context. Mine accordingly — archaeology pass only, no clone. |

---

### C25 — latitudegames/AIDungeon (AIDungeon2 — Narrative Tree Archaeology)

| Field | Value |
|-------|-------|
| Source | github.com/latitudegames/AIDungeon (archived Oct 2023, read-only) |
| Status | **ARCHIVED** — 3.2k stars, 36 contributors, 546 forks. Python 87.7% + Jupyter 8.7%. MIT license. Last meaningful commit 7 years ago. Latitude's current product (aidungeon.io) is proprietary SaaS — this repo is the historical open-source artifact. |
| License | MIT |
| Stack | Python 3 + TensorFlow 1.15.2 + GPT-2 (gpt-2-simple wrapper) + requirements.txt |
| Mine class | **SCHEMA** — narrative tree data format, interactive story loop architecture, GPT-2 fine-tune pipeline |
| Key source patterns | **(1) Story-tree JSON schema**: `{ tree_id, story_start, action_results: [{ action, result, action_results: [...] }] }` — recursive action→result tree. This is the canonical data structure for branching interactive fiction. Maps to a `NarrativeNode` model in a MILFOLOGICAL entity interaction pipeline. **(2) Fine-tune text format**: `<\|startoftext\|>` / `> [action]\n[result]\n` interleaving pattern — the token format that teaches a model the action-response loop. Any MILFOLOGICAL entity fine-tune should adopt this interleaving convention. **(3) Story manager**: `story/story_manager.py` — manages context window budget (truncate from start, preserve recent context), action injection, result streaming. Reference for session memory management in entity roleplay. **(4) Data pipeline**: `data/build_training_data.py` — scrape → tree → flat-text pipeline. The flat-text format is LLM-agnostic and directly portable to modern fine-tuning scripts. **(5) Architecture**: `generator/`, `story/`, `data/`, `other/` separation — the boundary between generative core and narrative management layer is the key abstraction. |
| Mine priority | **MEDIUM** — the story-tree schema + fine-tune text format are directly applicable to a MILFOLOGICAL entity interaction log format. The story manager's context truncation logic is a reference for entity session memory. |
| Immediate action | [O15]: Read `story/story_manager.py` (context window management) + `data/build_training_data.py` (tree → flat-text). Extract: (a) story-tree JSON schema field definitions, (b) `<\|startoftext\|>` text format spec, (c) context truncation algorithm. Write `docs/reference/NARRATIVE_TREE_FORMAT.md` as a portable data format reference. |
| Axis note | The AIDungeon2 architecture is the historical proof-of-concept that GPT-2-scale models can sustain coherent branching narratives via prompt engineering alone (no RLHF). The repo is MIT-licensed — schemas and format patterns are free to adopt directly. The Python/TF1.15 code is not portable, but the *data schemas and narrative loop logic* are implementation-agnostic. |

---

## §10 — Strategic Altitude Map (Sequencing + Stewardship Overview)

> **Purpose:** This section answers: *given all active candidates, work-in-progress modules, and frontier projects — what order does the work happen in, and why?* It operates at three altitudes: **Vector** (6-month horizon, strategic direction), **Phase** (2-4 week sprints), and **Task** (day-scale, unblocked now). Update this section when a phase completes or a new blocker resolves.

---

### Altitude 1 — Strategic Vectors (6-month horizon)

```
VECTOR A — MILFOLOGICAL Entity Pipeline (Core Identity)
  Purpose: Build the full entity lifecycle from CharCard V2 schema → image generation → entity card PNG export
  North star: WHR:MAX prototype — entity with full MILFOLOGICAL metadata rendered via SD backend + entity card
  Dependencies: SD backends (C1–C5), entity_card.py [DONE], entity_pixelart.py, entity_cutout.py, entity_unet_hook.py
  Key external inputs: C23 agnai (CharBook stacking), C18 CharCard V2 spec (schema), C10 sd.cpp (GGUF inference)
  Status: PIPELINE ACTIVE — entity_card.py committed (1b086bb1); backends/sdnext.py created; 3 Tier 1 stubs wired

VECTOR B — Vulkan-Lab CLI Renderer (GPU-Native Output Surface)
  Purpose: Produce ANSI/block-char terminal output via Vulkan compute — the visual output layer for MILFOLOGICAL entities
  North star: G6 — unified --mode=polar (roulette arc) | --mode=dungeon (isometric cRPG) via same GPU pipeline
  Dependencies: G2 ✅ (Euler scoring SSBO), G3 (fn transition_image_layout + ascii_downsample), G4 (GPU diff), G5 (SpinState), G6 (render modes)
  Key external inputs: C21 ZX-Art ANSI corpus (block-char atlas for G3), C17 diffusion-rs (Rust-native SD for future G7+)
  Status: G0–G2 ADMITTED — G3 pending (fn transition_image_layout() write is the unblocking action)

VECTOR C — Narrative Interaction Layer (Interactive Fiction Engine)
  Purpose: Enable entity roleplay sessions — entity card as character, user as player, LLM as narrator
  North star: Entity interaction loop with lorebook injection + session memory + branching story tree
  Dependencies: entity_card.py [DONE], C23 agnai [O13 pending], C25 AIDungeon2 [O15 pending], LLM backend (tabbyAPI / exllamav2)
  Status: DEFERRED — no unblocked tasks yet; dependent on [O13] + [O15] archaeology completing first
  Note: tabbyAPI gate ladder (G1–G6) provides the LLM inference host; exllamav2 EXL2 backend confirmed working (49e6e33f)
```

---

### Altitude 2 — Phase Sequencing (2-4 week sprint bands)

```
PHASE 1 — FOUNDATION (COMPLETE ✅)
  Git silence (5abcccb6) · protocols.py (46742297) · Tier 1 stubs (71359961) · entity_card.py (1b086bb1)
  All SD backends web-researched. B1/B2/B3 Forge sweep deferred.

PHASE 2 — ENTITY PIPELINE STABILIZATION (ACTIVE 🔄)
  Unblocked:
    [O13] agnai CharBook stacking sweep → refine entity_card.py LoreEntry design
    [B1]  Forge unet_patcher.py filesystem sweep → [B2] backends/forge.py → [B3] entity_unet_hook.py
    [O11] ZX-Art ANSI corpus → ANSI_BLOCKCHAR_REFERENCE.md (feeds Vulkan G3)
  Sequencing:
    [O13] first (no setup required, web sweep) → may revise entity_card.py fields
    [B1] second (requires dev/sd-candidates/forge/ already cloned ✅) → unblocks entity_unet_hook.py
    [O11] in parallel with [B1] — independent, feeds vulkan-lab not entity pipeline

PHASE 3 — GPU RENDERING + HOOK INTEGRATION (NEXT)
  Unblocked after Phase 2:
    Vulkan G3: write fn transition_image_layout() + ascii_downsample.comp.glsl → ANSI stdout [BLOCKED on G3 start]
    entity_unet_hook.py: UnetPatcher integration [BLOCKED on B3]
  Sequencing:
    G3 start is independent of [B3] — parallel execution possible
    [O6] IREE-Turbine sweep in parallel if Vulkan compute inference is prioritized

PHASE 4 — NARRATIVE LOOP + WHR:MAX (DEFERRED → future phase)
  Gated on:
    [O13] + [O15] archaeology complete → narrative data format spec
    entity_card.py stable (no pending field revisions)
    LLM inference host operational (tabbyAPI G1–G6 ladder)
  Deliverable:
    WHR:MAX prototype: full MILFOLOGICAL entity rendered as CharCard + SD-generated portrait + ANSI terminal display + lorebook injection
    This is the convergence point of all three vectors (A + B + C)
```

---

### Altitude 3 — Unblocked Task Queue (day-scale, execute now)

```
PRIORITY 1 — [O13] agnai CharBook sweep
  Why now: entity_card.py just committed; this refines LoreEntry before downstream modules depend on it
  Cost: 1 web-research pass, no setup
  Output: potential entity_card.py LoreEntry field patch + doc note in CharacterBook docstring

PRIORITY 2 — Vulkan G3 start: fn transition_image_layout()
  Why now: G3 is the load-bearing blocker for G4-G6; fn is self-contained, ~80 lines
  Cost: write one Rust function in vulkan-lab/cli-renderer/src/
  Output: transition_image_layout() available → immediately enables ascii_downsample.comp.glsl pass

PRIORITY 3 — [B1] Forge modules_forge/unet_patcher.py sweep
  Why now: entity_unet_hook.py is the highest-capability module in the pipeline (per-step block modification)
  Cost: filesystem read of already-cloned dev/sd-candidates/forge/
  Output: full UnetPatcher map → [B2] backends/forge.py → [B3] entity_unet_hook.py

PRIORITY 4 — [O11] ZX-Art ANSI corpus
  Why: directly feeds G3 block-char selection; cheap archaeology pass
  Cost: web browse zxart.ee/tags/ascii → write ANSI_BLOCKCHAR_REFERENCE.md
  Output: canonical block-char set + escape table ready for shader use

DEFERRED (not yet unblocked):
  [O9]  Seed-and-Evolve paper read (after entity_pixelart.py work is next)
  [O14] agn-ai Design Goals read (after portability decision is prioritized)
  [O15] AIDungeon2 narrative tree read (after narrative loop enters Phase 4)
  [B6]  sd.cpp clone (after GGUF lane or Vulkan inference prioritized)
  [B7]  forge-ll clone (after LayerDiffuse or canonical UnetPatcher prioritized)
```

---

### Candidate Classification Summary (all 25 entries)

| Class | Candidates | Strategic Role |
|-------|-----------|----------------|
| **SD INFERENCE BACKEND** | C1–C5 | Image generation API surface — `backends/*.py` |
| **LLM FRONTEND** | C6–C7 | SD API consumers — reference for API compatibility |
| **EXTENDED SD** | C8–C12 | Specialty backends (GGUF, LayerDiffuse, Vulkan) |
| **NICHE SOURCE** | C13–C17 | Translate / portable techniques (Metal→Vulkan, Rust, IREE) |
| **DSL / SCHEMA / CORPUS** | C18–C22 | Entity metadata, seeding, block-char, markdown pipeline |
| **INTERACTIVE FICTION** | C23–C25 | CharBook stacking, multi-AI adapter, narrative tree |

**Total active mine operations:** [O1]–[O15] + [S1]–[S6] + [B1]–[B7]
**Total rejected:** 3 (C8 Fooocus, C9 SwarmUI, C12 Easy Diffusion)
**Convergence target:** WHR:MAX prototype — entity pipeline × Vulkan renderer × narrative loop
