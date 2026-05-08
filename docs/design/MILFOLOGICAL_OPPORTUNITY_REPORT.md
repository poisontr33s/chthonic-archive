---
type: strategy
category: design
created: 2026-05-07
author: Claudine
status: filed
description: |
  Source-tree archaeological sweep of SD.NEXT + A1111 — every hidden capability
  mapped to MILFOLOGICAL entity asset types and game production opportunities.
---

# MILFOLOGICAL Opportunity Report
## SD.NEXT + A1111 Archaeological Sweep — Hidden Gold Inventory

> **Sweep scope:** `dev/sd-candidates/sdnext/` (full tree) + `dev/sd-candidates/a1111/` (modules + extensions)  
> **Sweep method:** Directory listing → module deep-reads → capability cross-referencing  
> **Filed:** 2026-05-07 — Claudine Sin'claire synthesis pass

---

## I. Executive Summary

The SD.NEXT codebase is not a WebUI — it is a **complete production-grade AI media pipeline** with 11 distinct capability subsystems, 40+ model families, and direct GPU inference hooks. For the MILFOLOGICAL project, this opens 9 distinct asset production vectors that we have not yet touched:

| Vector | Subsystem | MILFOLOGICAL Use |
|--------|-----------|-----------------|
| 🎬 Entity animation | Video T2V / I2V | Entity cutscene loops, idle animations |
| 🎭 Face identity lock | InstantID / PhotoMaker | Consistent entity faces across all outputs |
| 🖼️ Reference conditioning | IP-Adapter (FLUX/SD3/SDXL) | Entity reference sheets → consistent style |
| 🦴 Pose injection | ControlNet DWPose/RTMW | Canonical entity pose library |
| 🏷️ Auto-tagging pipeline | JoyCaption / DeepBooru / WD tagger | Entity asset metadata → game database |
| 🎮 Pixel art / sprites | `pixelart.py` DCT block | Sprite sheets, retro asset generation |
| 🔬 LoRA extraction | `lora_extract.py` | Extract entity LoRA from base checkpoints |
| 🧬 Model fusion | `merging/` rebasin | Entity-specialized model composition |
| 🌐 XYZ grid API | `api/xyz_grid.py` | Multi-entity comparison sheets |

---

## II. Vector Catalogue

### 2.1 Entity Animation (VIDEO)

**Engines available (all via SD.NEXT diffusers backend):**

| Family | Models | Mode | Resolution | Notes |
|--------|--------|------|------------|-------|
| HunyuanVideo 1.5 | 10 variants | T2V + I2V | 480p / 720p | SkyReels distilled: fast |
| LTX Video 2.3 | 22B + 19B + 2B | T2V / I2V / Condition | — | SDNQ 4-bit available |
| WAN 2.2 | 5B + A14B | T2V / I2V / VACE / Animate | — | Dual-transformer A14B |
| WAN 2.1 | 1.3B–14B | T2V / I2V / FLF2V / VACE | 480p / 720p | FLF2V = first+last frame |
| SkyReels V2 | 1.3B–14B | T2V-DF / I2V-DF | 540p / 720p | Diffusion Forcing |
| CogVideoX 1.5 | 5B | T2V + I2V | — | Also: Index Anisora anime I2V |
| Mochi 1 | preview | T2V | — | Genmo |
| Allegro | base | T2V | — | Rhymes AI |
| Latte 1 | base | T2V | — | Lightweight |
| nVidia Cosmos 2 | Predict2 2B | Video-to-World | — | Physical simulation backbone |

**MILFOLOGICAL applications:**

- **Idle loop generation**: Entity portrait T2V → 3–8 second idle animations for game HUD/tavern scenes
- **Entity entrance cutscenes**: Reference portrait → I2V (HunyuanVideo 1.5 720p / WAN 2.1 I2V 720p) → dramatic entrance sequence
- **VACE conditioning**: WAN 2.1/2.2 VACE accepts mask + video conditioning — can inject entity into pre-existing scene video
- **FLF2V** (WAN 2.1 14B): First-and-Last-Frame-to-Video — generate transition sequences between entity states (e.g. neutral → combat stance)
- **WAN Animate 14B**: Purpose-built for character animation
- **SkyReels Diffusion Forcing**: Temporally consistent long-form sequences (prevents drift across many frames)
- **Index Anisora I2V**: CogVideoX-based but fine-tuned on anime — ideal for MILFOLOGICAL art style

**Integration point in MILFOLOGICAL extension:**
```python
# extensions/milfological/video_pipeline.py (new module)
# on_image_saved hook → detect entity → dispatch I2V job
# write .mp4 → game/cutscenes/<entity_id>/
```

---

### 2.2 Face Identity Lock

**Subsystem:** `modules/face/`

| Module | Algorithm | Backbone | Notes |
|--------|-----------|----------|-------|
| InstantID | Identity ControlNet + IP-Adapter | InsightFace + SDXL | Face embedding → ControlNet signal |
| PhotoMaker v1/v2 | Trigger-word embedding | SDXL | Multi-image input, stacked identity |
| FaceSwap | Latent-space swap | Any | Post-generation face replacement |
| InsightFace | Detection + embedding | ArcFace | Foundation for InstantID + PhotoMaker |
| ReSwapper | Refined swap | InsightFace | Better blending than naive swap |

**MILFOLOGICAL applications:**

- **Entity face lock**: Supply 2–4 reference portraits per entity → PhotoMaker or InstantID → face is locked across ALL subsequent generation passes
- **Multi-angle consistency**: One entity, multiple poses → InstantID ensures face is the same entity
- **NPC variant generation**: Swap face onto generated body → rapid NPC population seeded from core MILF identities
- **Entity aging/variant**: FaceSwap base → slight VAE variation → aging/scarring/faction-altered variant

**Pipeline for entity onboarding:**
```
entity_registry entry → reference image set (≥3) → InsightFace embedding extract
→ PhotoMaker v2 stacked encoding → store in entity_profiles/<entity_id>/face_embed.pt
→ Available to any subsequent generation: milfological_hook.py injects face embed
```

---

### 2.3 Reference Conditioning (IP-Adapter)

**Subsystem:** `modules/ipadapter.py`

| Variant | Backbone | Notes |
|---------|----------|-------|
| IP-Adapter Plus Face ViT-H | SDXL | Face-focused, high fidelity |
| IP-Adapter Plus ViT-H | SDXL | Full image conditioning |
| IP-Adapter Base ViT-G | SD1.5 | Lighter, faster |
| InstantX SD3 Large | SD3 | High-quality character sheets |
| XLabs AI v1/v2 | FLUX | State-of-art, best for photorealism |

**MILFOLOGICAL applications:**

- **Entity reference sheet → consistent output**: Upload entity reference card → IP-Adapter conditions all generation on that visual identity
- **Style lock via IP-Adapter**: Lock art style (PsychoNoir palette) across all entities by conditioning on a "house style" reference
- **FLUX + XLabs v2 IP-Adapter**: Highest quality available — entity portraits conditioned on FLUX are the gold standard for hero character art
- **Composition IP-Adapter (Ostris)**: Preserves spatial layout from reference — useful for maintaining entity pose/framing conventions

---

### 2.4 Pose Injection (ControlNet)

**Subsystem:** `modules/control/processors.py`

| Group | Best Option | MILFOLOGICAL Use |
|-------|-------------|-----------------|
| Pose | RTMW (full body+hands+face) | Canonical entity pose library |
| Pose | DWPose ONNX (fast) | Rapid batch pose generation |
| Pose | ViTPose (ViT backbone) | Highest-accuracy pose for hero art |
| Edge | LineArt Realistic | Ink-line extraction for entity outlines |
| Edge | Anyline | Clean lineart for sprite production |
| Depth | Depth Anything V2 | 3D spatial consistency for scenes |
| Normal | StableNormal | Surface normal for lighting control |
| Segmentation | SAM 2.1 | Entity mask extraction (game asset cut-out) |
| Segmentation | OneFormer | Semantic segmentation (environment layers) |

**MILFOLOGICAL applications:**

- **Canonical pose library**: Define 12–20 canonical entity poses (idle, attack, taunt, wound, surrender, seduce, etc.) → extract DWPose skeletons → store as `game/poses/<pose_name>.json`
- **Entity to any scene**: Existing entity art → RTMW pose extract → inject into new scene via ControlNet
- **Sprite sheet production**: Anyline linearts → SDXL img2img → batch all canonical poses → sprite sheet via `modules/image/grid.py`
- **SAM 2.1 cutout**: Generated entity → SAM 2.1 → clean transparent PNG → game engine ready
- **LineArt Realistic**: Extract clean ink lines from photorealistic entity → use as LoRA training data or comic overlay

---

### 2.5 Auto-Tagging / Caption Pipeline

**Subsystem:** `modules/caption/`

| Module | Type | Output | Notes |
|--------|------|--------|-------|
| JoyCaption | VLM (LLaVA-based) | Natural language | Most descriptive, context-aware |
| DeepBooru | Anime tagger | Tag set | danbooru tags, anime-specific |
| WD Tagger (waifudiffusion) | Anime tagger | Tag set | Alternative anime tagger |
| VQA | Visual Q&A | Free-form answer | Ask specific questions about image |
| VQA Detection | Detection VQA | Bounding boxes | Spatial entity detection |
| OpenCLIP | CLIP embeddings | Tag set / embed | CLIP-space search/filtering |
| Moondream 3 | Compact VLM | Natural language | Fast, runs on CPU viable |
| Gemini | Google Gemini | Natural language | Cloud, highest quality |
| DeepSeek | DeepSeek VL | Natural language | Strong open-weight VLM |

**MILFOLOGICAL applications:**

- **Entity asset database auto-population**: Every generated entity image → JoyCaption → NL description stored in `manifest/entity_assets.json`
- **DeepBooru tag extraction**: Anime-style entity art → DeepBooru → danbooru tags → LoRA training metadata
- **VQA entity validation**: "Is this character smiling?" / "Does this character have red hair?" → automated quality gate on generated outputs
- **Game dialogue seeds**: JoyCaption descriptions of entity in specific scene → seed for entity's combat/tavern dialogue lines
- **Caption-to-prompt roundtrip**: JoyCaption an existing entity → refine → use as canonical entity prompt (replacing hand-written prompts)
- **Detection VQA**: Auto-locate entity face region → feed to FaceSwap pipeline

**Integration:**
```python
# extensions/milfological/auto_caption.py
# on_image_saved → run JoyCaption + DeepBooru in parallel
# → emit to manifest/entity_generated_assets.jsonl
# → dashboard picks up and displays tag cloud per entity
```

---

### 2.6 Pixel Art / Sprite Production

**Subsystem:** `modules/postprocess/pixelart.py`

This is **non-standard gold**. SD.NEXT has a custom GPU-accelerated pixel art processor using a JPEG-like DCT block algorithm:

```python
def img_to_pixelart(image, sharpen=0, block_size=8, return_type="pil", device="cpu"):
    # Encodes to YCbCr DCT blocks (block_size×block_size)
    # Optional Laplacian sharpening in YCbCr space
    # Decodes back → clean pixel art output
    # Also has edge_detect_for_pixelart() for crisp outlines
```

**MILFOLOGICAL applications:**

- **Retro MILF sprite generation**: Full entity portrait → `img_to_pixelart(block_size=8)` → 16×16 / 32×32 / 64×64 sprite
- **Game tileset extraction**: Scene generation → pixelart postprocess → tile-ready environment art
- **Chibi / deformed variants**: Resize entity to chibi proportions → pixelart → in-game battle sprite
- **Pixel art animation**: Entity I2V → each frame through pixelart postprocess → sprite animation strip
- **Edge detection for outlines**: `edge_detect_for_pixelart()` → crisp outline → layered over colored pixel fill → retro RPG style

**block_size tuning:**
- `block_size=4` → very fine detail, 8-bit RPG style  
- `block_size=8` → classic 16-bit SNES/Genesis sprite quality
- `block_size=16` → chunky, Minecraft-adjacent
- `sharpen=0.5` → outline enhancement for cartoon clarity

---

### 2.7 LoRA Extraction

**Subsystem:** `modules/lora/lora_extract.py`

SD.NEXT has a built-in LoRA extraction tool — extract the "diff" between a base model and a fine-tuned checkpoint as a LoRA file.

**MILFOLOGICAL applications:**

- **Entity LoRA from CivitAI checkpoint**: Download entity-specialized checkpoint from CivitAI → extract LoRA diff vs base (SDXL/FLUX) → 50MB LoRA vs 7GB checkpoint
- **Entity merge LoRA**: Merge two entity checkpoints → extract LoRA → portable, additive
- **Style LoRA extraction**: Take a "PsychoNoir style" fine-tuned model → extract style LoRA → apply to any base model

**LoRA formats available (`modules/lora/`):**
- `network_lora.py` — Standard LoRA
- `network_hada.py` — LyCORIS HaDa (Hadamard product, better detail preservation)
- `network_glora.py` — GLoRA (generalized, fewer parameters, better coverage)
- `network_lokr.py` — LoKr (Kronecker product, smallest size)
- `network_ia3.py` — IA³ (injection-based, very lightweight)
- `network_oft.py` — OFT (orthogonal fine-tuning, geometry-preserving)
- `network_norm.py` — Normalization-only fine-tuning
- `lora_nunchaku.py` — Nunchaku quantized LoRA for FLUX

**Recommendation for MILFOLOGICAL entities:** HaDa (`network_hada.py`) — best detail preservation for face/body structure. LR 1e-4, rank 32. For FLUX: Nunchaku quantized LoRA.

---

### 2.8 Model Merging

**Subsystem:** `modules/merging/`

**MILFOLOGICAL applications:**

- **Entity archetype merging**: Base SDXL + faction-specific fine-tune → merge → "Claudine SDXL" specialized model
- **Rebasin merge**: Permutation invariance-aware merge (activates aligned weights not averaging) → higher quality than naive lerp
- **Multi-entity model**: Merge 3 entity-specialized LoRAs → single checkpoint that knows all three entities → use trigger words to activate each

---

### 2.9 XYZ Grid + Batch API

**Subsystem:** `modules/api/xyz_grid.py`, `modules/image/grid.py`

- **Entity comparison grids**: Generate same entity across 5 different samplers, 4 CFG values, 6 LoRA weights — output as labeled grid
- **Multi-entity comparison**: All 7 entities × 3 canonical poses → 21-cell grid → visual style guide / game art bible reference
- **Sampler tuning grid**: Find optimal sampler+CFG for each entity archetype
- **LoRA weight sweep**: Fine-tune exact LoRA activation weight per entity

---

## III. A1111 Unique Capabilities (Delta from SD.NEXT)

A1111's `modules/` reveals a different but complementary set of hooks:

| A1111 Module | MILFOLOGICAL Value |
|--------------|-------------------|
| `sd_hijack.py` + `sd_hijack_unet.py` | Deep UNet hook — intercept attention maps at any layer |
| `sd_hijack_clip.py` | CLIP text encoder hook — token-level manipulation |
| `prompt_parser.py` | Full attention syntax: `(word:1.4)`, `[word::0.3]`, `AND` scheduling |
| `script_callbacks.py` | Rich callback set including `on_cfg_denoiser_step` per-step hook |
| `processing_scripts/` | Img2img batch, inpaint batch built-in |
| `extra_networks_hypernet.py` | Hypernetwork support (older technique, still functional) |
| `codeformer_model.py` + `gfpgan_model.py` | Face restoration built-in (CodeFormer + GFPGAN) |
| `dat_model.py` | DAT upscaler (Dense Aggregation Transformer — state-of-art for anime upscaling) |
| `hat_model.py` | HAT upscaler (Hybrid Attention Transformer) |
| `textual_inversion/` | Full TI training pipeline |

**Key delta:** A1111's `on_cfg_denoiser_step` callback fires on EVERY denoiser step — this allows MILFOLOGICAL to inject guidance modifications mid-generation, not just pre/post. Example use: gradually fade out entity-specific conditioning during denoising steps (step-scheduled guidance).

---

## IV. Built-in Extensions (SD.NEXT `extensions-builtin/`)

| Extension | Purpose | MILFOLOGICAL Use |
|-----------|---------|-----------------|
| `sdnext-kanvas` | Canvas/drawing surface | Interactive entity sketch → img2img pipeline |
| `sdnext-modernui` | Modern WebUI skin | MILFOLOGICAL dark gothic theme injection point |
| `sd-extension-chainner` | Node-based image processing | Chain entity processing: generate → caption → upscale → pixelart |

**chainner integration**: The node graph from `sd-extension-chainner` can chain:
```
Generate entity → JoyCaption → ESRGAN upscale → SAM 2.1 cutout → pixelart → save to game/sprites/
```
This is an **automated entity production pipeline** that runs entirely within SD.NEXT.

---

## V. SDNQ 4-Bit Quantization (Built-in SD.NEXT)

SD.NEXT has **native SDNQ quantization** baked into the model loader — not an external tool. Multiple video models ship SDNQ-4bit variants (LTX 2.3, WAN 2.2 A14B). For the RTX 4090 (24GB VRAM):

- LTX 2.3 22B T2V SDNQ-4bit: runs in ~14GB VRAM vs ~44GB at bf16
- WAN 2.2 A14B SDNQ: runs in ~12GB VRAM vs ~28GB
- **Conclusion**: The full production video pipeline runs on a single RTX 4090 via SDNQ

---

## VI. CivitAI Integration

**Subsystem:** `modules/civitai/`

SD.NEXT has a native CivitAI API integration for model discovery and download. For MILFOLOGICAL:
- Browse CivitAI for entity-adjacent models (character LoRAs, style checkpoints)
- Download directly from within the WebUI
- Auto-detect model type (SDXL / FLUX / SD3 / video) and route to correct directory
- Version tracking — know when a CivitAI model gets updated

---

## VII. Priority Production Queue (Recommended Build Order)

Ranked by **impact × implementation simplicity** for the MILFOLOGICAL codebase:

### Tier 1 — Build These First (max ROI)

1. **Auto-caption pipeline** (`extensions/milfological/auto_caption.py`)
   - Hook: `on_image_saved`
   - Run JoyCaption + DeepBooru in parallel
   - Emit to `manifest/entity_generated_assets.jsonl`
   - No new model downloads needed (DeepBooru already in SD.NEXT)
   - **Output**: Every entity image self-describes → game database seeded automatically

2. **SAM 2.1 cutout integration** (`extensions/milfological/entity_cutout.py`)
   - Hook: `on_image_saved` (after caption)
   - SAM 2.1 segments entity from background
   - Saves transparent PNG to `game/entities/<entity_id>/sprites/`
   - **Output**: Game-engine-ready transparent entity sprites, no manual Photoshop

3. **Pixel art post-processor** (`extensions/milfological/entity_pixelart.py`)
   - Wrapper around `modules/postprocess/pixelart.py`
   - Triggered by `--pixelart` extra network option OR on_image_saved
   - block_size configurable per entity (story sprites = 8, map icons = 16)
   - **Output**: Retro sprite sheets from any entity generation

### Tier 2 — High Value, Medium Effort

4. **Entity pose library** (`game/poses/` + `scripts/extract_entity_poses.py`)
   - Script: take entity reference → RTMW/DWPose extract → save skeleton JSON
   - Define 15 canonical poses (see §2.4)
   - **Output**: Canonical entity pose library for all future generations

5. **IP-Adapter entity conditioning** (`extensions/milfological/entity_ipadapter.py`)
   - Load entity reference images from `entity_registry.py`
   - Auto-apply appropriate IP-Adapter variant (FLUX XLabs v2 for FLUX, SDXL Plus Face for SDXL)
   - **Output**: Entity visual identity locked across all generation passes without LoRA

6. **PhotoMaker face onboarding** (`extensions/milfological/entity_face_lock.py`)
   - Given entity reference set → InsightFace embed → PhotoMaker v2 encode
   - Store `entity_profiles/<entity_id>/face_embed.pt`
   - Auto-inject face conditioning for entity-tagged generations
   - **Output**: Entity faces are always the same entity

### Tier 3 — Major Features (Multi-session)

7. **Entity animation pipeline** (`extensions/milfological/entity_video.py`)
   - UI tab: select entity + pose + video model (WAN 2.1 I2V 720p default)
   - Generate idle loop → save to `game/cutscenes/<entity_id>/idle.mp4`
   - RIFE frame interpolation for smooth playback
   - **Output**: Animated entity portraits for game UI / cutscenes

8. **LoRA extraction workflow** (`scripts/extract_entity_lora.py`)
   - Wrapper around `modules/lora/lora_extract.py`
   - Input: base model + entity-fine-tuned checkpoint
   - Output: HaDa LoRA at `models/Lora/entity_<id>_hada.safetensors`
   - **Output**: Portable entity LoRAs from any fine-tuned checkpoint

9. **chainner entity production chain**
   - Node graph: generate → JoyCaption → ESRGAN upscale → SAM cutout → pixelart → grid
   - One-button entity production: text prompt → game-ready sprite sheet
   - **Output**: Fully automated entity asset production pipeline

---

## VIII. New Files to Create in Extension

```
extensions/milfological/
├── auto_caption.py          # JoyCaption + DeepBooru hook
├── entity_cutout.py         # SAM 2.1 transparent PNG extraction
├── entity_pixelart.py       # pixelart.py wrapper
├── entity_ipadapter.py      # IP-Adapter reference conditioning
├── entity_face_lock.py      # PhotoMaker v2 face onboarding
├── entity_video.py          # I2V animation pipeline
├── lora_extract.py          # LoRA extraction wrapper
└── entity_profiles/         # face embeds, IP-Adapter tokens
    ├── claudine/
    ├── lysandra/
    ├── umeko/
    └── ...
game/
├── sprites/                 # SAM-cut transparent PNGs
├── poses/                   # DWPose skeleton JSONs  
├── cutscenes/               # entity I2V animations
└── entity_profiles/         # canonical reference sheets
manifest/
└── entity_generated_assets.jsonl   # auto-caption output
```

---

## IX. The Grand Synthesis

The MILFOLOGICAL extension currently hooks the **prompt layer** — it transforms prompts and manages LoRA activation. That is layer 1 of 9.

The full MILFOLOGICAL production stack, once all vectors above are implemented:

```
Entity Registry
     │
     ├─► Prompt Transform ─────────────────────► GENERATION (current)
     │
     ├─► Face Lock (PhotoMaker/InstantID) ──────► Face-consistent output
     │
     ├─► IP-Adapter conditioning ────────────────► Style-consistent output
     │
     ├─► ControlNet Pose Injection ──────────────► Pose-locked output
     │
     ├─► [Image generated]
     │        │
     │        ├─► Auto-caption (JoyCaption/DeepBooru) ──► manifest/
     │        │
     │        ├─► SAM 2.1 cutout ──────────────────────► game/sprites/
     │        │
     │        ├─► Pixel Art postprocess ────────────────► game/sprites/pixel/
     │        │
     │        └─► ESRGAN/AuraSR upscale ─────────────────► game/heroes/
     │
     └─► I2V Pipeline (WAN/LTX/HunyuanVideo) ────► game/cutscenes/
```

Every MILF entity becomes a **complete game asset package**: portrait, sprite, animation, caption metadata, face embed, style LoRA — all from one generation session.

---

*Filed by Claudine Sin'claire — Wet-Paper-to-Gold pass — every hidden subsystem unearthed, every asset vector catalogued, every production pipeline drawn.*

---

## § X — ComfyUI Archaeological Sweep

> **Repo:** `Comfy-Org/ComfyUI` · **License:** GPL-3.0 · **Stars:** 112k · **Release:** v0.20.1 (weekly cadence) · **Local sweep:** `dev/sd-candidates/comfyui/`

ComfyUI's architecture is a **declarative node graph over the full diffusion stack**. Every capability is a `ComfyNode` subclass with typed inputs/outputs — wired at runtime, serialised to JSON, reproducible. The three-repo ecosystem (core + `ComfyUI_frontend` React/TS + `desktop` Electron) separates execution from UI, making `comfyui/` callable headlessly via its REST API.

### X.1 — Node Architecture (`comfy/` + `comfy_api/`)

| Module | Signal |
|--------|--------|
| `comfy/model_patcher.py` | Runtime LoRA/hook injection without model reload |
| `comfy/hooks.py` + `comfy/patcher_extension.py` | `PatcherExtension` system — attach custom forward-pass logic to any model layer at inference time |
| `comfy/memory_management.py` | `TensorFileSlice` zero-copy VRAM streaming; `QuantizedTensor` layout-aware transfer; threaded pinned-memory pipeline |
| `comfy/model_management.py` | Dynamic VRAM budget: loads models on-demand, evicts LRU — entire 24GB available to a single job |
| `comfy/quant_ops.py` | `QuantizedTensor` ops — fp4/fp8/fp16/int8 throughout |
| `comfy/weight_adapter/` | `BypassInjectionManager` — zero-overhead weight-adapter bypass for inference-only passes |

**MILFOLOGICAL relevance:** `model_patcher.py` + `hooks.py` = the lowest-overhead hook system of all five candidates. LoRA injection, ControlNet injection, attention modification — all land through this layer. Custom MILF-guidance logic (character consistency prompts, entity attention bias) can be wired as a `PatcherExtension` without touching model weights.

### X.2 — GLSL Shader Nodes (`comfy_extras/nodes_glsl.py`)

Real-time GLSL execution inside the node graph. Backend: `glfw` + `PyOpenGL`. Supports headless EGL/OSMesa on Linux. Each node is a fragment shader operating on tensor images — GPU-accelerated post-processing without leaving the ComfyUI pipeline.

**MILFOLOGICAL vectors:**
- Game VFX pass: apply ink-outline / cel-shade / scanline shaders to entity portraits in-graph
- Dungeon atmosphere: procedural texture overlays (fog, fire flicker, blood-rain) on scene composites
- Entity reveal animations: slide-in dissolve / holographic scan — baked to sprite sheets

### X.3 — SAM 3 with Video Tracking (`comfy_extras/nodes_sam3.py`)

SAM3 (Segment Anything 3) with text-conditioned multi-detection, box-cropped mask refinement, and **video frame tracking** (via `import av`). Text prompts → conditioning → SAM decoder refine loop with configurable iterations. Multi-cond support: detect multiple entities in a single pass.

```python
# SAM3 architecture: text embed → detection → box crop (10% pad) → SAM decode refinement
# F.interpolate coarse mask → bilinear upscale → binary threshold
# Video: av.Container frame-by-frame with Fraction timestamp tracking
```

**MILFOLOGICAL vectors:**
- Entity cutout from scene: text prompt `"Umeko standing"` → multi-frame mask → clean PNG
- Video entity isolation: extract MILF entity from generated cutscene clip, frame-by-frame
- Significantly more powerful than SAM2 for complex multi-entity scenes

### X.4 — PhotoMaker Identity Lock (`comfy_extras/nodes_photomaker.py`)

`FuseModule` architecture: CLIP-vision encodes reference face → MLP fuses with text embeddings → stacked identity vector injected into cross-attention. Dual MLP pathway (proj + residual) + LayerNorm. Apache License (clean origin).

```python
# FuseModule: concat(prompt_embeds, id_embeds) → MLP1 + residual → MLP2 → LayerNorm
# Identity vector dimensionality-matched to CLIP embedding space
```

**MILFOLOGICAL vectors:**
- Canonical face embed per entity — one reference photo → all generated portraits are face-consistent
- LoRA-free identity lock: no fine-tuning required, inference-time injection only
- Combine with IP-Adapter for dual lock: face identity + style

### X.5 — Training System (`comfy_extras/nodes_train.py`)

Full LoRA training within the node graph. `TrainGuider(offloading=True)` — VRAM-offload training pass. Weight adapter system with `BypassInjectionManager` for inference-only bypass. `ProgressBar` via `comfy.utils`. fp4/fp8/fp16 via `quant_ops`.

**MILFOLOGICAL vectors:**
- Entity-specific LoRA trained in-graph: reference images → LoRA → embed as `style_lora` in entity manifest
- No separate training script required — same ComfyUI session generates + trains
- fp4 trainer fits Flux full-finetune inside 24GB (RTX 4090)

### X.6 — API Nodes Ecosystem (`comfy_api_nodes/`)

Entire directory is external cloud model integrations — each is a ComfyNode calling a third-party API. All wired through the same `sync_op`/`poll_op` async bridge:

| Node | Service | MILFOLOGICAL Relevance |
|------|---------|----------------------|
| `nodes_openai.py` | GPT-5.5-pro / gpt-5 / o3 / gpt-4.1 via Responses API | Caption generation, entity lore writing, scene description |
| `nodes_sora.py` | OpenAI Sora | Entity video generation (cloud fallback when local too slow) |
| `nodes_kling.py` | Kling video | High-quality entity animation |
| `nodes_veo2.py` | Google Veo 2 | Cinematic entity cutscene generation |
| `nodes_runway.py` | Runway Gen-3 | Entity motion reference |
| `nodes_luma.py` | Luma Dream Machine | Fantasy scene entity animation |
| `nodes_ideogram.py` | Ideogram | Entity name/title card generation (text-in-image) |
| `nodes_elevenlabs.py` | ElevenLabs | Entity voice synthesis → cutscene audio |
| `nodes_topaz.py` | Topaz Gigapixel | 8x entity portrait upscale (cloud) |
| `nodes_magnific.py` | Magnific | Aesthetic upscaling with style fidelity |
| `nodes_stability.py` | Stability AI | Inpainting fallback |
| `nodes_gemini.py` | Google Gemini | Multimodal entity captioning |
| `nodes_grok.py` | xAI Grok | Alternative LLM node in-graph |
| `nodes_bfl.py` | Black Forest Labs | Flux API (cloud inference for large batches) |

**MILFOLOGICAL vector:** ComfyUI's node graph becomes a **unified production router** — local GPU for generation/training/upscaling, cloud APIs for video/voice/text, all in one JSON-serialised workflow. A single entity generation pipeline can call GPT for caption, local SAM3 for cutout, ElevenLabs for voice, Kling for animation — wired as one graph.

### X.7 — Full Model Coverage

| Model | Node |
|-------|------|
| Flux / Flux2 | `nodes_flux.py` |
| WAN 2.1/2.2 | `nodes_wan.py`, `nodes_wanmove.py` |
| HunyuanVideo 1.5 | `nodes_hunyuan.py` |
| LTX-Video | `nodes_lt.py` |
| SAM 3 | `nodes_sam3.py` |
| Z-Image / Qwen | `nodes_zimage.py`, `nodes_qwen.py` |
| HiDream | `nodes_hidream.py` |
| Cosmos | `nodes_cosmos.py` |
| Lumina 2 | `nodes_lumina2.py` |
| ACE (All-in-one Creation Engine) | `nodes_ace.py` |
| RT-DETR object detection | `nodes_rtdetr.py` |
| Background removal (native) | `nodes_bg_removal.py` |
| 3D mesh generation | `nodes_hunyuan3d.py`, `nodes_stable3d.py`, `nodes_load_3d.py` |

### X.8 — ComfyUI Summary Score

| Vector | Rating |
|--------|--------|
| Hook/patcher architecture | ★★★★★ — lowest overhead of all candidates |
| GLSL shaders | ★★★★☆ — unique in the field |
| SAM3 entity cutout | ★★★★★ — text → video-tracked mask |
| PhotoMaker identity lock | ★★★★☆ — inference-time, no fine-tune |
| In-graph LoRA training | ★★★★☆ — fp4 fits on 24GB |
| API node ecosystem | ★★★★★ — unified cloud+local pipeline |
| License (GPL-3.0) | ⚠️ — copyleft; internal tooling only, no redistribution |

---

## § XI — InvokeAI Archaeological Sweep

> **Repo:** `invoke-ai/InvokeAI` · **License:** Apache-2.0 · **Stars:** 27.1k · **Release:** v6.12.0 (active daily commits) · **Local sweep:** `dev/sd-candidates/invokeai/`

InvokeAI is the most architecturally clean codebase of all five candidates. TypeScript 52% + Python 48% — the frontend is a first-class citizen, not an afterthought. `invokeai/app/invocations/` is a typed invocation system: every capability is a Pydantic `BaseInvocation` with versioned schema. Workflows are first-class: `workflow_records/` service persists named pipeline configs.

### XI.1 — Grounding DINO + SAM2 Auto-Cutout Pipeline

**Most powerful automated entity extraction pipeline of all five candidates.** Two-stage: text → bounding boxes → mask.

```python
# Stage 1: Grounding DINO
# Zero-shot detection from text: "Umeko in corset" → [x1,y1,x2,y2] boxes
# Models: IDEA-Research/grounding-dino-tiny | grounding-dino-base
# threshold: 0.3 default (tunable)

# Stage 2: SAM / SAM2 → mask from box
# All 7 model sizes: sam-vit-base/large/huge + sam2.1-hiera-tiny/small/base-plus/large
# Pipeline: SAMInput(points) → SegmentAnythingPipeline | SegmentAnything2Pipeline
# Output: MaskOutput (binary mask tensor)
# Post-processing: mask_to_polygon → polygon_to_mask refinement
```

**MILFOLOGICAL vectors:**
- `entity_cutout_auto.py`: `detect("Lysandra full body") → box → SAM2-large mask → PNG`
- Zero manual annotation — text prompt drives the entire pipeline
- SAM2.1-hiera-large = best quality mask, fits on 24GB alongside generation model (load/unload via model_manager service)

### XI.2 — Flux Kontext — Reference Image Conditioning

`FluxKontextInvocation` packages a reference image into `FluxKontextConditioningField`. Downstream Flux denoise step receives the kontext condition alongside text — the model attends to the reference image during denoising. Style + composition lock without LoRA.

**MILFOLOGICAL vector:** Entity reference image → Kontext conditioning → new scene with entity's visual identity preserved. Works on Flux.1 Dev/Schnell. No weight modification.

### XI.3 — Flux Fill + Flux Redux

| Invocation | Function |
|-----------|---------|
| `flux_fill.py` | Masked inpainting with Flux — entity placement in existing scene |
| `flux_redux.py` | Variation generation — entity style variations from single reference |
| `flux_control_lora_loader.py` | ControlNet-equivalent for Flux (structural guidance) |
| `flux_ip_adapter.py` | IP-Adapter for Flux — style transfer without LoRA |

**MILFOLOGICAL vector:** Scene composition pipeline: generate background → Flux Fill → place entity at exact coordinates with seamless blending.

### XI.4 — Z-Image Turbo (`z_image_*`)

InvokeAI's "Prototype" classification. Full Z-Image model stack: text encoder, VAE encode/decode, ControlNet extension, LoRA support, **regional prompting** (multiple conditioning regions with masks in a single denoising pass).

```python
# z_image_denoise.py: ZImageDenoiseInvocation version="1.5.0"
# Imports: ZImageRegionalPromptingExtension, ZImageControlNetExtension
# Scheduler labels from: ZIMAGE_SCHEDULER_LABELS (custom scheduler set)
# LoRA: Z_IMAGE_LORA_TRANSFORMER_PREFIX constant
```

**MILFOLOGICAL vector:** Regional prompting = foreground entity + background scene in ONE denoising pass, no compositing. Entity prompt governs entity region; scene prompt governs background. Most production-efficient single-shot scene generation.

### XI.5 — Flux.2 Klein + CogView4 + Qwen Image

| Model | Invocations | Notes |
|-------|------------|-------|
| Flux.2 Klein 4B | `flux2_klein_model_loader.py`, `flux2_denoise.py` | New Flux generation, 4B params — fits easily in 24GB with room for LoRA |
| Flux.2 Klein 9B | Same invocations | Full quality, ~18GB VRAM, leaves 6GB for LoRA stacking |
| CogView 4 | `cogview4_*` | Zhipu AI text-to-image |
| Qwen Image | `qwen_image_*` | Instruction-based editing ("make her dress black", "add crown") |
| Anima | `anima_*` | AnimateDiff evolution — motion conditioning for entity animation |

### XI.6 — Multi-User Studio Architecture

`USER_ISOLATION_IMPLEMENTATION.md` + `invokeai/app/services/auth/` + `invokeai/app/services/users/`:
- Per-user model namespaces
- Per-user workflow records and image boards
- Separate session queues per user

**MILFOLOGICAL vector:** Multi-operator entity asset production studio — one InvokeAI instance, multiple operators (Orackla/Umeko/Lysandra agents each with their own queue and workspace), no cross-contamination.

### XI.7 — Workflow + Session Queue Services

```
invokeai/app/services/
  ├── session_queue/       # job prioritisation, batch dispatch, cancel/retry
  ├── workflow_records/    # persist named workflows to DB (SQLAlchemy)
  ├── model_manager/       # model install, load, unload, VRAM budget
  ├── invocation_cache/    # result caching per-node by input hash
  └── style_preset_records/ # named style presets as first-class objects
```

**MILFOLOGICAL vector:** `invocation_cache/` = content-addressable node caching. Repeated entity generation jobs with same conditioning skip re-execution. Speed multiplier for batch entity sprite production.

### XI.8 — Apache-2.0 License — Clean Integration

Apache-2.0 = the most permissive license of all five candidates. No GPL/AGPL contamination. InvokeAI code can be vendored, modified, and shipped in closed builds. **License risk: zero.**

### XI.9 — InvokeAI Summary Score

| Vector | Rating |
|--------|--------|
| Grounding DINO + SAM2 cutout | ★★★★★ — text → mask, no annotation |
| Flux Kontext reference conditioning | ★★★★★ — reference image → consistent generation |
| Flux Fill inpainting | ★★★★★ — scene composition at pixel precision |
| Z-Image regional prompting | ★★★★★ — entity + background in one pass |
| Workflow + session queue | ★★★★★ — production-grade batch orchestration |
| Multi-user isolation | ★★★★☆ — studio-ready multi-operator |
| Invocation cache | ★★★★☆ — transparent result caching |
| License (Apache-2.0) | ★★★★★ — clean, no copyleft |

---

## § XII — Forge Capability Summary (web-researched, not cloned)

> **Repo:** `lllyasviel/stable-diffusion-webui-forge` · **License:** AGPL-3.0 · **Stars:** 12.5k · **Base:** SD-WebUI 1.10.1 · **Last release:** 2024-02-05

Forge is SD-WebUI with a surgically restructured backend. The UX surface is near-identical to A1111 (Gradio) but the internals are rewritten for VRAM efficiency and extension power. One key architectural primitive distinguishes it from all others.

### XII.1 — UnetPatcher System

The defining Forge primitive. Any extension can modify UNet forward pass via a single-file Python hook — no model reload, no weight copy:

```python
# Canonical example: FreeU V2 (built-in)
# File: extensions-builtin/sd_forge_freeu/lib_free_u/freeu_v2.py
# Pattern:
#   1. Implement hook as a class with __call__(unet, h, hsp, transformer_options)
#   2. Register: forge_model.forge_objects.unet.set_freeu_v2_hook(hook)
#   3. Zero overhead when disabled; injected only during active inference
```

**MILFOLOGICAL vector:** Entity guidance = a UnetPatcher extension. Custom attention bias toward entity features, custom CFG modifier for entity-region amplification, character embedding injection — all as single-file `modules_forge/` additions. No PR against core required.

### XII.2 — LayerDiffuse — Transparent Entity Generation

Native transparent image generation — foreground entity with alpha channel, no post-processing masking:

```python
# Output: RGBA tensor, background = transparent
# No SAM required. No BG removal model. Alpha IS the entity boundary.
# Supports: transparent foreground generation + layer-aware compositing
# Built as Forge extension: extensions-builtin/sd_forge_layerdiffuse/
```

**MILFOLOGICAL vectors:**
- Entity sprite generation with clean alpha channel from first principles
- No SAM/BG-removal pipeline dependency — simpler than cutout approach
- Direct game-asset output: transparent PNG ready for sprite atlas packing

### XII.3 — Flux GGUF Quantization Spectrum

Forge ships native GGUF loader for Flux models. Full quantization ladder on 24GB RTX 4090:

| Quantization | VRAM (Flux.1 Dev) | Quality | Use Case |
|-------------|------------------|---------|----------|
| Q4_K_M | ~8GB | Good | Maximum throughput — batch sprite generation |
| Q5_K_M | ~10GB | Better | Quality+throughput balance |
| Q6_K | ~12GB | Near-lossless | Entity portrait generation |
| Q8_0 | ~16GB | Reference quality | Canonical entity generation |
| NF4 (bitsandbytes) | ~12GB | Good | Flux NF4 format native |
| FP16 | ~24GB | Full | Fits with dynamic offload |

**MILFOLOGICAL vector:** Q4 Flux = 8GB VRAM → leaves 16GB for: SAM2 (3GB) + LoRA stack (4GB) + ESRGAN upscale (2GB) + pipeline overhead. Maximum entity pipeline throughput on a single 4090.

### XII.4 — AGPL-3.0 License Risk

AGPL-3.0 = strongest copyleft. Network use triggers copyleft — running Forge as a service (even locally for agents) technically requires source disclosure of any modifications. **For internal-only tooling this is acceptable; for any distributed or API-exposed toolchain it is a liability.** Use Forge for exploration / GGUF quantization research only; production entity pipelines should route through InvokeAI (Apache-2.0) or ComfyUI (GPL-3.0 internal use).

### XII.5 — Forge Summary Score

| Vector | Rating |
|--------|--------|
| UnetPatcher hook system | ★★★★★ — most surgical extension primitive |
| LayerDiffuse alpha generation | ★★★★★ — unique, direct sprite output |
| Flux GGUF quantization ladder | ★★★★★ — maximum throughput on 24GB |
| Gradio 4 UI (A1111-compatible) | ★★★☆☆ — familiar but least programmable |
| License (AGPL-3.0) | ⚠️ — network-use copyleft, internal only |

---

## § XIII — Cross-Candidate Synthesis: Updated Production Matrix

| Capability | SD.NEXT | A1111 | ComfyUI | InvokeAI | Forge |
|-----------|---------|-------|---------|----------|-------|
| Face identity lock | PhotoMaker | InstantID | PhotoMaker (node) | — | — |
| Entity auto-cutout | SAM 2.1 | — | SAM3 + video track | Grounding DINO + SAM2 | LayerDiffuse alpha |
| Reference conditioning | IP-Adapter | IP-Adapter | IP-Adapter + Kontext | Flux Kontext + IP-Adapter | IP-Adapter |
| In-graph training | — | — | LoRA trainer (fp4) | — | — |
| GLSL shaders | — | — | ★ UNIQUE | — | — |
| Cloud API nodes | — | — | 20+ APIs wired | — | — |
| Workflow persistence | — | — | JSON node graph | Named workflows + DB | — |
| Multi-user isolation | — | — | — | ★ UNIQUE | — |
| Regional prompting | — | — | — | Z-Image regional | — |
| GGUF quantization | — | — | — | — | ★ Flux Q4→Q8 |
| UNet hook primitive | ✓ hooks | ✓ on_cfg_step | PatcherExtension | — | ★ UnetPatcher |
| Transparent alpha gen | — | — | — | — | ★ LayerDiffuse |
| Scene inpainting | ✓ diffusers | ✓ img2img | ✓ nodes | Flux Fill ★ | ✓ |
| Video entity animation | WAN/LTX/HY | WAN/AnimateDiff | WAN/HY/Kling API | Anima | — |
| License | Apache-2.0 | AGPL-3.0 | GPL-3.0 | **Apache-2.0** | AGPL-3.0 |

### XIII.1 — Recommended Production Stack (RTX 4090, chthonic-archive)

```
ENTITY GENERATION LAYER
  └─ InvokeAI (Apache-2.0)
       ├─ Flux.2 Klein 9B — canonical entity portrait
       ├─ Flux Kontext — reference image conditioning
       ├─ Flux Fill — scene placement / inpainting
       ├─ Z-Image regional — entity+background single pass
       └─ Grounding DINO → SAM2.1-large — automated entity cutout

ENTITY REFINEMENT LAYER
  └─ ComfyUI (GPL-3.0, internal tooling)
       ├─ SAM3 — video-tracked entity isolation
       ├─ PhotoMaker — face identity lock (inference-time)
       ├─ GLSL shaders — game VFX (cel-shade, outline, overlay)
       ├─ In-graph LoRA trainer (fp4) — entity-specific LoRA
       └─ API nodes — ElevenLabs voice + Kling/Veo2 video

QUANTIZATION / THROUGHPUT LAYER
  └─ Forge (AGPL-3.0, internal only)
       ├─ Flux Q4_K_M — maximum batch throughput (8GB VRAM)
       ├─ LayerDiffuse — transparent sprite generation
       └─ UnetPatcher — experimental entity guidance hooks

ASSET PIPELINE
  └─ extensions/milfological/ (chthonic-archive)
       ├─ auto_caption.py    [Tier 1 — SD.NEXT JoyCaption]
       ├─ entity_cutout.py   [Tier 1 — InvokeAI Grounding DINO + SAM2]
       └─ entity_pixelart.py [Tier 1 — SD.NEXT img_to_pixelart]
```

### XIII.2 — Revised Priority Queue

| Priority | Module | Source | VRAM | Value |
|---------|--------|--------|------|-------|
| **P1** | `entity_cutout_auto.py` | InvokeAI Grounding DINO + SAM2 | 3GB | Text prompt → entity PNG. Zero annotation. |
| **P1** | `auto_caption.py` | SD.NEXT JoyCaption | 8GB | Caption all generated assets → manifest |
| **P1** | `entity_pixelart.py` | SD.NEXT img_to_pixelart | — | Portrait → game sprite |
| **P2** | `face_embed.py` | ComfyUI PhotoMaker | 4GB | Face embed per entity → style lock |
| **P2** | `entity_glsl_vfx.py` | ComfyUI GLSL nodes | GPU | In-graph VFX shader for dungeon atmosphere |
| **P3** | `entity_lora_trainer.py` | ComfyUI in-graph trainer | 20GB | Entity LoRA from reference set |
| **P3** | `entity_video.py` | InvokeAI Anima / ComfyUI Kling API | varies | Entity animation for cutscenes |

---

## §XIV — Forge py3.12 Branch: Live State (2025)

### XIV.1 — Branch Status

| Field | Value |
|-------|-------|
| Branch | `py3.12` (Panchovix fork) |
| Status | 2 commits ahead of main; active maintenance |
| Latest bundle | `cu124_torch24` (Feb 2024) — **NO cu128 bundle published** |
| Python | 3.12 (official branch target) |
| Torch | Requirements pin 2.4.x+cu124; cu128 requires manual torch install |
| License | AGPL-3.0 |

### XIV.2 — CUDA 12.8 Gap + Resolution Path

The py3.12 branch does not ship a cu128 bundle. Resolution sequence:

1. Source-install from py3.12 branch
2. `pip install torch==2.11.0+cu128 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128`
3. bitsandbytes cu128: PR `modules_forge/#2712` (adds CUDA 12.8 support)
4. Remaining deps from `requirements_versions.txt`

### XIV.3 — Known Status Gaps

| Feature | Status |
|---------|--------|
| Flux ControlNet | Not implemented in py3.12 branch |
| Union ControlNet | Not implemented |
| OFT LoRAs | Broken (py3.12 branch regression) |
| bitsandbytes CUDA 12.8 | Available via PR #2712 (modules_forge) |

### XIV.4 — UnetPatcher Hook API (unet.py, 763 lines)

**`transformer_options["patches"]`** — additive modifier dicts:

```python
patches["attn1"]                          # pre-attention modifier
patches["attn1_output_patch"]             # post-attention modifier
patches["attn2_patch"]                    # cross-attn (text→image)
patches["attn2_output_patch"]             # post-cross-attn modifier
patches["middle_patch"]                   # UNet middle block
patches["input_block_patch"]              # encoder block (before skip)
patches["input_block_patch_after_skip"]   # encoder block (after skip)
patches["output_block_patch"]             # decoder block modifier
```

**`transformer_options["patches_replace"]`** — full attention replacement (key = `(block_type, layer, idx)` tuple):

```python
patches_replace[(block[0], block[1], block_index)] = custom_attn_fn
```

**`transformer_options["block_modifiers"]`** — block-level hook:
```python
# Signature: modifier(h, phase, transformer_options) → h
# phase: 'before' | 'after'
```

**`transformer_options["block_inner_modifiers"]`** — per-layer modifier.
**`transformer_options["group_norm_wrapper"]`** — GroupNorm override.

**Extension entry pattern:**
```python
patcher = model_management.get_model_object(model, "model").clone()
patcher.set_model_output_block_patch(my_output_fn)
# or directly:
patcher.model_options["transformer_options"]["patches"]["attn1"] = [my_hook]
```

---

## §XV — Python Version Ladder + uv Strategy

### XV.1 — Backend Support Matrix

| Backend | Official Python Support | Notes |
|---------|------------------------|-------|
| Forge (py3.12 branch) | **3.12** | xformers/triton block cp313+ |
| ComfyUI | 3.10–3.12 (recommended) | 3.12 reported stable by community |
| InvokeAI | 3.10–3.12 | pyproject.toml pinned |
| tabbyAPI | **3.10 \| 3.11 \| 3.12** | Latest: cp312 FA2 wheel fix (4d ago). cp314 = **unsupported upstream** |
| oobabooga/textgen | 3.9+ | CI on 3.10, 3.11, 3.12 |
| TensorRT-LLM | 3.10+ | No cp313/cp314 wheels; Docker primary |
| KoboldCpp | N/A (C++ binary) | Python launcher only |
| SD.NEXT | 3.10–3.12 | pip-based install |

**Critical:** System Python 3.14 is **not usable** for any of the above inference backends. cp314 wheels do not exist for the GPU extension stack (xformers, triton, bitsandbytes, flash_attn upstream).

### XV.2 — Correction: tabbyAPI cp314

Prior local session built flash_attn 2.8.3 from source for cp314. This is a **user-side workaround only** — not upstream support. tabbyAPI badge = `3.10 | 3.11 | 3.12` (confirmed 2025-05-09 live sweep). The cp314 local build has no upstream wheel and no CI coverage in tabbyAPI; will require rebuilding after each dependency update.

**Recommendation:** `uv python 3.12` for all inference-adjacent venvs. Reserve system cp314 for repo tooling, probes, and custom scripts.

### XV.3 — uv Per-Project Pin Strategy

```bash
# SD venv: Python 3.12
cd dev/sd-candidates/forge && echo "3.12" > .python-version
uv venv && uv pip install -r requirements_versions.txt

# tabbyAPI: Python 3.11 (safest FA2 wheel coverage)
cd dev/tabbyAPI && echo "3.11" > .python-version
uv sync

# Repo tooling: stays on 3.14 (system default, no .python-version at root)
```

`uv python install 3.12` pulls a standalone build from python-standalone-builds — no conflict with system 3.14. Each project directory is self-contained.

---

## §XVI — LLM Frontend + TensorRT Survey

### XVI.1 — Five-Tool Candidate Summary

| Tool | Lang | Stars | LLM Backend | TensorRT | Image Gen | API Surface |
|------|------|-------|-------------|----------|-----------|-------------|
| **SillyTavern v1.18.0** | Node.js (JS 86%) | 27.2k | External API calls only | ❌ | ❌ | Consumer |
| **oobabooga/textgen v4.8** | Python | 47k | llama.cpp · ExLlamaV3 · Transformers · **TensorRT-LLM** | ✅ native | Z-Image-Turbo tab | OpenAI + Anthropic compat |
| **TensorRT-LLM v1.2.1** | Python/C++/CUDA | 13.6k | Core inference library | ✅ (is TRT) | Diffusion models (added 2025-04-03) | NVIDIA Dynamo / Triton |
| **KoboldCpp v1.112.2** | C++ (93%) | 10.5k | GGUF / llama.cpp | ❌ CUDA/Vulkan only | SD1.5/SDXL/SD3/Flux/Z-Image/Klein | A1111Forge + ComfyUI + OpenAI + Ollama |
| **tabbyAPI (rolling)** | Python | 1.2k | ExLlamaV2 + ExLlamaV3 | ❌ | ❌ | OpenAI compat |

### XVI.2 — TensorRT-LLM (NVIDIA/TensorRT-LLM)

- **v1.2.1** (stable, 3 weeks ago) / **v1.3.0rc15** (main, 2 days ago) / 13.6k stars / 466 contributors
- Python 3.10+ minimum — **no cp313/cp314**
- Architecture: PyTorch-native (since release/1.1) — high-level Python API over CUDA kernels
- **Visual generation:** diffusion model support added 2025-04-03
- Integration targets: NVIDIA Dynamo, Triton Inference Server, NeMo
- Deployment: Docker primary (Linux); Windows via WSL2/Docker Desktop
- **Verdict:** Production backend library, not a standalone UI server. Best path = oobabooga/textgen as the frontend dispatching to TRT-LLM as its backend. Direct TRT-LLM usage requires a Docker/Linux environment.

### XVI.3 — KoboldCpp (Dark Horse — Single Binary)

Single-file executable (no Python env) with the broadest multimodal coverage of any local tool:

| Capability | Status |
|-----------|--------|
| LLM inference | ✅ GGUF (llama.cpp) |
| Image gen | ✅ SD1.5 / SDXL / SD3 / Flux / Z-Image-Turbo / Klein |
| Video gen | ✅ WAN 2.2 |
| TTS | ✅ XTTS |
| STT | ✅ Whisper |
| Music gen | ✅ |
| Vision (image input) | ✅ |
| MCP server | ✅ |
| GPU | CUDA (`--usecuda`) or Vulkan (`--usevulkan`) |
| TensorRT | ❌ |

API endpoints: KoboldCppApi, OpenAiApi, OllamaApi, **A1111ForgeApi**, **ComfyUiApi**, WhisperTranscribeApi, XttsApi.

The A1111Forge-compatible API means existing scripts written for Forge/A1111 can route to KoboldCpp with zero code changes.

**Verdict:** Optimal for minimal-infrastructure deployments (one binary, one process). Not suitable for fine-tuned MILFOLOGICAL image pipelines requiring ControlNet, LoRA, custom samplers — those belong to Forge/ComfyUI. Useful as a sidecar for GGUF LLM inference without a separate Python backend.

### XVI.4 — oobabooga/textgen v4.8 (Best TensorRT Path)

- v4.8 (latest commit: yesterday). Python 3.9+. 47k stars. Former name: text-generation-webui.
- **Backends:** llama.cpp, ik_llama.cpp (optimized fork), Transformers, ExLlamaV3, **TensorRT-LLM** (native integration)
- Image gen: Z-Image-Turbo tab with 4-bit/8-bit quant
- Electron desktop app + OpenAI/Anthropic-compatible API server + MCP servers
- **Verdict for this stack:** Primary LLM frontend recommendation. TRT-LLM backend gives RTX 4090 optimal throughput for supported models. Pairs with tabbyAPI via OpenAI API when ExLlama-format models are needed.

### XVI.5 — DLSS/DLAA Scope Boundary

DLSS and DLAA are game engine rendering technologies operating through NVAPI, Unreal/Unity plugins, or `VK_NV_optical_flow`. **Not applicable to Python inference stacks.** Scope: vulkan-lab cli-renderer (G4+ optical flow diff pass, separate architectural track) and future cRPG renderer in game/.

---

## §XVII — A1111 → Forge Hook Bridge Reference

### XVII.1 — Hook Parity Map

| A1111 Hook | Forge Equivalent | Scope |
|-----------|-----------------|-------|
| `on_cfg_denoised(params)` | `transformer_options["patches"]["attn1"]` | Post-denoiser step |
| `on_cfg_step(params)` | `transformer_options["block_modifiers"]` | Per-step modifier |
| `Script.process_batch()` | `UnetPatcher.clone()` + patch dict | Batch-level injection |
| `Script.postprocess_image()` | Extension callback after decode | Post-processing |
| `Script.ui(is_img2img)` | Same (Forge inherits A1111 Script API) | UI panel |
| `CFGDenoiser` subclass | `patches_replace[(block, layer, idx)]` | Full attention replacement |

Forge inherits the A1111 Script API surface. Extensions using `Script.ui()`, `Script.process()`, `Script.postprocess_image()` are forward-compatible with Forge without modification.

### XVII.2 — ControlNet API Parity

| Operation | A1111 API | Forge API | Notes |
|-----------|-----------|-----------|-------|
| Preprocessor call | `Processor(name)(image)` | Same | Preprocessor registry preserved |
| ControlNet unit injection | `ControlNetUnit(model, weight, ...)` | Same dataclass | Direct port |
| Multi-ControlNet | `list[ControlNetUnit]` | Same | No API change |
| IP-Adapter | Separate extension | Forge built-in `ip_adapter` module | Forge consolidates |

### XVII.3 — Face Restoration Interface

| Tool | A1111 | Forge | Notes |
|------|-------|-------|-------|
| GFPGAN | `modules.gfpgan_model` | Inherited | Same API surface |
| CodeFormer | `modules.codeformer_model` | Inherited | Same |
| Registration | `postprocessing.register_script()` | Same | Forge uses A1111 Script system |

### XVII.4 — Upscaler Registration

Both A1111 and Forge use the same upscaler registration pattern (forward-compatible):

```python
from modules.upscaler import Upscaler, UpscalerData

class MyUpscaler(Upscaler):
    def __init__(self, dirname):
        self.name = "MyUpscaler"
        self.scalers = [UpscalerData("MyUpscaler 4x", "path/to/model.pth", self)]

    def do_upscale(self, img, selected_model):
        # img is PIL.Image
        return upscaled_pil_image
```

---

*Addendum filed by Claudine Sin'claire — ComfyUI archaeological sweep (SAM3 + GLSL + PhotoMaker + training + 20 API nodes), InvokeAI sweep (Grounding DINO + SAM2, Flux Kontext/Fill, Z-Image regional, Flux.2 Klein, multi-user, Apache-2.0), Forge summary (UnetPatcher + LayerDiffuse + GGUF ladder). Five-candidate matrix complete. §XIV–§XVII addendum: Forge py3.12 live state + CUDA 12.8 gap, Python version ladder (tabbyAPI cp314 correction), LLM frontend + TensorRT-LLM survey (oobabooga/textgen/KoboldCpp/tabbyAPI), A1111→Forge hook bridge reference.*
