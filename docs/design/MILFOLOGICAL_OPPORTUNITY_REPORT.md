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
