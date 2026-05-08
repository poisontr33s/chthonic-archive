---
type: strategy
category: architecture
created: 2026-05-09
mine-pass: 1 (MILFOLOGICAL_OPPORTUNITY_REPORT.md §I–§XVII)
lock: soft — provisional groupings; expands with each subsequent sweep
description: Architecture-layer mine-state across 5 SD backends. NOT a capability matrix (§XIII covers that). This file maps the current mine state — where convergence has been found, where unique gold lives, and where the ground is uncharted. No backend is out of scope.
---

# MILF Architecture Convergence Matrix

> **Purpose:** Track the current mine state across 5 SD inference backends. Group rows by convergence (SHARED), divergence (VARIANT), and unique gold (UNIQUE). All groupings are provisional — they reflect what mine pass 1 found, not what will remain fixed. Each subsequent sweep against any backend can promote a 🔍 MINE cell, split a SHARED row, or elevate a UNIQUE into a new protocol dimension.
>
> **Mine pass 1 source:** `MILFOLOGICAL_OPPORTUNITY_REPORT.md §I–§XVII`. 🔍 MINE marks cells that need a direct filesystem sweep.
>
> **Clone state + task sequencing:** `docs/design/SD_CANDIDATE_REGISTRY.md` — ground truth for what is cloned, what has been swept, what is pending, and what each stub depends on. Read before editing this matrix or creating new stubs.
>
> **Feeds:** `extensions/milfological/src/milfological/protocols.py` — a provisional interface surface derived from SHARED rows. It is not the architecture — it is the current best read of the convergence. It grows.

## Soft-Lock Dynamic Frame

This matrix operates on a **soft-lock**: provisional groupings derived from mine pass 1, open to revision as any backend is swept more deeply. No backend is out of scope. No interface is frozen.

The `/sdapi/v1/` lineage (SD.NEXT + A1111 + Forge) shares a surface because they share **history** — not because that surface is the canonical standard. InvokeAI and ComfyUI are not deviants from a standard. They are distinct architectural families with their own gold veins — some of which (Grounding DINO+SAM2, SAM3 video track, Flux Kontext, GLSL shader nodes, fp4 in-graph LoRA trainer, 20+ API nodes) are **richer than anything in the `/sdapi/v1/` lineage**.

The UNIQUE rows table is the primary value output of this matrix — those are the openers, not afterthoughts. SHARED rows define the provisional convergence surface; UNIQUE rows define the next modules. Both matter equally.

**Mine-pass upgrade path:** When a 🔍 MINE cell is filled via filesystem sweep, update this file in place. If the fill reveals a new UNIQUE capability: add it to the UNIQUE table and create the target module stub. If it reveals convergence across backends: promote the row to SHARED and add it to the provisional interface. The interface grows forward — it does not lock.

---

## Layer 1 — REST API Surface

| Layer | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|-------|---------|-------|-------|----------|---------|----------------|
| URL prefix | `/sdapi/v1/` | `/sdapi/v1/` | `/sdapi/v1/` | `/api/v1/` | `/api/` | **VARIANT** — 3 share prefix |
| Text-to-image | `POST /sdapi/v1/txt2img` | `POST /sdapi/v1/txt2img` | `POST /sdapi/v1/txt2img` | Named workflow POST | `POST /api/prompt` → WS progress | **VARIANT** |
| Image-to-image | `POST /sdapi/v1/img2img` | `POST /sdapi/v1/img2img` | `POST /sdapi/v1/img2img` | Named workflow + denoise | `KSampler` node with latent input | **VARIANT** (3 shared) |
| Interrogate/caption | `POST /sdapi/v1/interrogate` | `POST /sdapi/v1/interrogate` | `POST /sdapi/v1/interrogate` | 🔍 MINE | 🔍 MINE | **SHARED** for 3 (A1111 lineage) |
| Model list | `GET /sdapi/v1/sd-models` | Same | Same | `GET /api/v1/models/` | `GET /object_info` node schema | **VARIANT** |
| Sampler list | `GET /sdapi/v1/samplers` | Same | Same | Per workflow | `GET /object_info` | **VARIANT** |
| Progress/status | `GET /sdapi/v1/progress` | Same | Same | `GET /api/v1/queue/` | WebSocket stream | **VARIANT** |

**Mine-pass 1 finding:** SD.NEXT + A1111 + Forge share the full `/sdapi/v1/` surface due to shared lineage. KoboldCpp exposes `A1111ForgeApi` — covers all three without modification (§XVI). InvokeAI uses `/api/v1/` + named workflows; ComfyUI uses `/api/` + WebSocket + JSON node graph. These are not deviations — they are different architectural philosophies that require different adapters. **One thin adapter covers the `/sdapi/v1/`-lineage family; InvokeAI and ComfyUI adapters unlock distinct gold that the lineage family does not have.**

---

## Layer 2 — UNet Hook Contract

| Layer | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|-------|---------|-------|-------|----------|---------|----------------|
| Pre-attention hook | `sd_hijack_unet.py` | `sd_hijack_unet.py` | `transformer_options["patches"]["attn1"]` | No hook primitive | `PatcherExtension` | **VARIANT** |
| Post-attention hook | `sd_hijack.py` | `sd_hijack.py` | `patches["attn1_output_patch"]` | No hook primitive | `PatcherExtension` | **VARIANT** |
| Cross-attn (text→image) | `sd_hijack_unet.py` | `sd_hijack_unet.py` | `patches["attn2_patch"]` / `patches["attn2_output_patch"]` | No hook primitive | 🔍 MINE | **VARIANT** |
| Full attn replacement | CLIP hijack | `sd_hijack.py` CFGDenoiser subclass | `patches_replace[(block, layer, idx)]` (§XIV.4) | Via graph node swap | Via node wiring | **UNIQUE per candidate** |
| Per-step denoiser hook | `script_callbacks` | `on_cfg_denoiser_step` (per-step, §III) | `block_modifiers` (phase before/after) | No step hook | 🔍 MINE | **VARIANT** |
| Block-level modifier | 🔍 MINE | 🔍 MINE | `block_modifiers(h, phase, opts)→h` | No primitive | 🔍 MINE | **UNIQUE to Forge** |
| GroupNorm override | 🔍 MINE | 🔍 MINE | `transformer_options["group_norm_wrapper"]` | No primitive | 🔍 MINE | **UNIQUE to Forge** |
| Middle block hook | 🔍 MINE | 🔍 MINE | `patches["middle_patch"]` | No primitive | 🔍 MINE | **UNIQUE to Forge** |

**Mine-pass 1 finding:** Forge's `UnetPatcher` is architecturally the deepest hook system found (§XIV.4 — 8 distinct patch keys + `patches_replace` + 3 modifier types). InvokeAI has no UNet hook primitive — customisation is graph-level instead, which is a different architecture not a limitation. `protocols.py` does not need to provide a uniform hook interface across all 5 — hooks are UNIQUE to the backend that has them. Forge gets a dedicated hook surface; InvokeAI's graph architecture is its own opener (Grounding DINO, Flux Kontext, Z-Image). 🔍 MINE: SD.NEXT and A1111 block-level hooks remain uncharted — medium priority sweep.

---

## Layer 3 — Model Loader + Folder Convention

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| Checkpoint root | `models/Stable-diffusion/` | `models/Stable-diffusion/` | `models/Stable-diffusion/` | `~/.invokeai/models/` or configurable | `models/checkpoints/` | **VARIANT** — A1111 lineage shares path |
| VAE folder | `models/VAE/` | `models/VAE/` | `models/VAE/` | ModelManager abstraction | `models/vae/` (lowercase) | **VARIANT** — case difference |
| LoRA folder | `models/Lora/` | `models/Lora/` | `models/Lora/` | ModelManager abstraction | `models/loras/` (lowercase) | **VARIANT** — case difference |
| ControlNet folder | `models/ControlNet/` | `models/ControlNet/` | `models/ControlNet/` | Via ModelManager | `models/controlnet/` (lowercase) | **VARIANT** — case difference |
| Embeddings | `embeddings/` | `embeddings/` | `embeddings/` | 🔍 MINE | `models/embeddings/` | **SHARED** for A1111 lineage |
| GGUF models | `models/Diffusers/` | 🔍 MINE | `models/GGUF/` or inline | 🔍 MINE | via custom nodes | **UNIQUE per candidate** |
| Model type detection | Auto (extension-based) | Auto | Auto | ModelManager typed | ComfyNode typed input | **VARIANT** |
| CivitAI integration | ✓ native `modules/civitai/` (§VI) | Via extension | Via extension | No native | No native | **UNIQUE to SD.NEXT** |
| SDNQ 4-bit quantization | ✓ native in model loader (§V) | No | No | No | No | **UNIQUE to SD.NEXT** |

**Key insight:** The A1111-lineage path convention (`models/Stable-diffusion/`, `models/VAE/`, `models/Lora/`, `models/ControlNet/`) is SHARED across SD.NEXT + A1111 + Forge. ComfyUI uses lowercase variants. InvokeAI abstracts paths entirely via ModelManager. **`protocols.py` can expose a `model_path(type, name)` method that resolves per backend; the A1111 lineage implementation is trivial.**

---

## Layer 4 — Extension / Plugin Registration

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| Registration mechanism | Script API (class inheriting `Script`) | Script API (same) | Script API (inherited, §XVII.1) | `@invocation` decorator (graph node) | `ComfyNode` subclass | **VARIANT** (3 share Script API) |
| UI panel | `Script.ui(is_img2img)` | Same | Same (§XVII.1) | Node input panel | Node input panel | **SHARED** for A1111 lineage |
| Pre-generation hook | `Script.process()` | Same | Same | Graph node | 🔍 MINE | **SHARED** for A1111 lineage |
| Post-generation hook | `Script.postprocess_image()` | Same | Same (§XVII.1) | Graph node output | Graph node output | **SHARED** for A1111 lineage |
| Batch-level hook | `Script.process_batch()` | Same | `UnetPatcher.clone()` + patch dict (§XVII.1) | 🔍 MINE | 🔍 MINE | **VARIANT** |
| Extension discovery | `extensions/` dir + `scripts/` subdir | Same | Same | Python package install | Custom nodes dir | **VARIANT** |

**Key insight:** A1111 Script API (`ui`, `process`, `postprocess_image`) is forward-compatible with SD.NEXT and Forge **without modification** (§XVII.1). Extensions built against A1111 run on all three. InvokeAI and ComfyUI use distinct paradigms.

---

## Layer 5 — LoRA Injection Point

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| LoRA application | Weight merge into model copy | Weight merge | `ModelPatcher.add_patches()` | `LoRALinearLayer` adapter | `ModelPatcher.add_patches()` | **VARIANT** — result equivalent |
| Formats supported | HaDa/GLoRA/LoKr/IA³/OFT/Norm/Nunchaku (§2.7) | Standard + LyCORIS | Standard + Forge-specific | Standard | Standard + custom | **VARIANT** |
| Activation syntax | `<lora:name:weight>` in prompt | Same | Same | Via graph node | Via `LoraLoader` node | **VARIANT** (3 share syntax) |
| LoRA extraction | ✓ native `modules/lora/lora_extract.py` (§2.7) | No | No | No | ✓ In-graph trainer (fp4) (§X) | **UNIQUE per candidate** |
| FLUX LoRA | Nunchaku quantized (§2.7) | 🔍 MINE | 🔍 MINE | 🔍 MINE | 🔍 MINE | **UNIQUE to SD.NEXT (confirmed)** |
| Recommended format | HaDa rank-32 (§2.7) | Standard | Standard | 🔍 MINE | 🔍 MINE | MILFOLOGICAL recommendation |

**Key insight:** ComfyUI and Forge share the `ModelPatcher.add_patches()` pattern — they share diffusers ancestry at the patching layer. This is non-obvious from the surface API. **`entity_lora_trainer.py` should target ComfyUI's in-graph fp4 trainer; extraction should target SD.NEXT's native extractor.**

---

## Layer 6 — ControlNet Injection

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| ControlNet unit | `ControlNetUnit(model, weight, ...)` | Same dataclass | Same dataclass (§XVII.2) | Via workflow node | Via `ControlNetApply` node | **SHARED** for A1111 lineage |
| Multi-ControlNet | `list[ControlNetUnit]` | Same | Same (§XVII.2) | Multi-node | Multi-node chain | **SHARED** for A1111 lineage |
| IP-Adapter | `modules/ipadapter.py` (§2.3) | Extension | Forge built-in `ip_adapter` module | `Flux Kontext` / IP-Adapter | IP-Adapter + Kontext nodes | **VARIANT** |
| Preprocessor call | `Processor(name)(image)` | Same | Same (§XVII.2) | Via graph node | Via preprocessor node | **SHARED** for A1111 lineage |
| Flux ControlNet | 🔍 MINE | 🔍 MINE | NOT implemented in py3.12 (§XIV.3) | ✓ Flux Kontext (§XI) | ✓ via Kontext nodes | **UNIQUE** — InvokeAI/ComfyUI only |

---

## Layer 7 — Image Interrogation / Captioning

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| REST endpoint | `POST /sdapi/v1/interrogate` | Same | Same | 🔍 MINE | 🔍 MINE | **SHARED** for A1111 lineage |
| JoyCaption | ✓ `modules/caption/` (§2.5) | No | 🔍 MINE | No | 🔍 MINE | **UNIQUE to SD.NEXT (confirmed)** |
| DeepBooru | ✓ built-in (§2.5) | ✓ built-in | 🔍 MINE | No | Via custom node | **SHARED** for A1111 lineage |
| WD Tagger | ✓ `modules/caption/` (§2.5) | Via extension | 🔍 MINE | No | Via custom node | **VARIANT** |
| VQA | ✓ `modules/caption/` (§2.5) | No | No | No | 🔍 MINE | **UNIQUE to SD.NEXT (confirmed)** |

**Key insight:** `auto_caption.py` should target SD.NEXT as primary backend for JoyCaption/VQA (unique capabilities). The `/sdapi/v1/interrogate` endpoint also works against A1111 and Forge for DeepBooru fallback. **This is already the right stub choice — but the `Backend` protocol should express `interrogate()` as optional capability, not assumed.**

---

## Layer 8 — Segmentation / Entity Cutout

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| SAM variant | SAM 2.1 (§2.4) | No | LayerDiffuse alpha (different mechanism) | Grounding DINO + SAM2 (§XI) | SAM3 + video track (§X) | **VARIANT** — 3 have SAM, different versions |
| Text-prompt cutout | Via Grounding DINO → SAM | No | No | ✓ Primary capability (§XI) | ✓ SAM3 (§X) | **SHARED** InvokeAI + ComfyUI |
| Video entity tracking | No | No | No | 🔍 MINE | ✓ SAM3 video track (§X) | **UNIQUE to ComfyUI** |
| Transparent alpha gen | SAM mask → composite | No | ✓ LayerDiffuse (★ §XIII) | Via SAM output | Via node output | **VARIANT** — Forge = generative, others = post-process |

**Key insight:** `entity_cutout.py` should target InvokeAI for text-prompt → entity extraction (zero annotation, best pipeline per §XIII.2 P1). ComfyUI's SAM3 is the video tracking extension. These are distinct use cases. **The stub already correctly separates these by backend assignment.**

---

## Layer 9 — Post-Processing Hook

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| On-save hook | `on_image_saved` callback | Same | Same (after decode) | Via graph node | Via node output | **SHARED** for A1111 lineage |
| Pixel art processor | ✓ `modules/postprocess/pixelart.py` DCT algorithm (§2.6) | No | No | No | No | **UNIQUE to SD.NEXT** |
| Edge detection | ✓ `edge_detect_for_pixelart()` (§2.6) | No | No | No | Via custom node | **UNIQUE to SD.NEXT (confirmed)** |
| Face restoration | CodeFormer + GFPGAN (§III) | Same (§XVII.3) | Inherited (§XVII.3) | No | No | **SHARED** A1111 lineage |
| DAT / HAT upscaler | 🔍 MINE | ✓ `dat_model.py`, `hat_model.py` (§III) | Inherited | No | Via custom node | **UNIQUE to A1111 (confirmed)** |
| ESRGAN | ✓ via chainner (§IV) | ✓ built-in | ✓ inherited | 🔍 MINE | Via custom node | **SHARED** A1111 lineage |

**Key insight:** `entity_pixelart.py` must target SD.NEXT — the DCT pixel art processor is unique to SD.NEXT (`modules/postprocess/pixelart.py` §2.6). No other backend has an equivalent. **This is one of the highest-value UNIQUE rows in the entire matrix.**

---

## Layer 10 — Quantization Pathway

| Concern | SD.NEXT | A1111 | Forge | InvokeAI | ComfyUI | Classification |
|---------|---------|-------|-------|----------|---------|----------------|
| SDNQ 4-bit | ✓ native (§V) — baked into model loader | No | No | No | No | **UNIQUE to SD.NEXT** |
| GGUF Q4–Q8 | Via Diffusers backend | 🔍 MINE | ✓ native (★ §XIII) | No | Via custom nodes | **UNIQUE to Forge (confirmed)** |
| BitsAndBytes | Via diffusers integration | Via extension | ✓ PR #2712 for CUDA 12.8 (§XIV.2) | ✓ Via config | Via custom nodes | **SHARED** diffusers lineage |
| fp4 in-graph training | No | No | No | No | ✓ LoRA trainer (§X) | **UNIQUE to ComfyUI** |
| Nunchaku (FLUX LoRA) | ✓ `lora_nunchaku.py` (§2.7) | No | 🔍 MINE | No | No | **UNIQUE to SD.NEXT (confirmed)** |

---

## Mine-State Summary (Soft-Lock Provisional)

### Provisional convergence surface (→ first-pass `protocols.py`)

Rows where mine pass 1 found alignment across ≥3 backends. A thin shared surface exists here. This list grows with each sweep — it is not closed:

| Protocol method | Coverage | Adapter complexity |
|----------------|----------|--------------------|
| `txt2img(params) → Image` | SD.NEXT + A1111 + Forge + KoboldCpp | Low — same JSON schema |
| `img2img(params) → Image` | SD.NEXT + A1111 + Forge + KoboldCpp | Low — same JSON schema |
| `interrogate(image, model) → str` | SD.NEXT + A1111 + Forge | Low — same endpoint |
| `model_path(type, name) → str` | SD.NEXT + A1111 + Forge | Trivial — same folder convention |
| `on_image_saved(hook_fn)` | SD.NEXT + A1111 + Forge | Low — same callback system |
| `controlnet_unit(model, weight) → Unit` | SD.NEXT + A1111 + Forge | Trivial — same dataclass |
| `lora_activate(name, weight)` | SD.NEXT + A1111 + Forge (prompt syntax shared) | Low |

### Divergent surface (→ per-backend adapters — equal-weight mining targets)

| Concern | Adapter strategy |
|---------|-----------------|
| InvokeAI REST (`/api/v1/`) | `InvokeAIAdapter` — workflow POST + named denoise |
| ComfyUI REST (`/api/` + WebSocket) | `ComfyUIAdapter` — `KSampler` graph POST |
| LoRA application mechanism | All produce equivalent output — adapter abstracts activation syntax |
| Model folder casing (ComfyUI lowercase) | `model_path()` implementation per backend |
| Sampler selection | Same JSON key, different valid values — adapter holds sampler map |

### Gold veins — primary mine targets (exploit directly, do not collapse)

These are the richest finds from mine pass 1. Each is a first-class capability with no equivalent elsewhere. These are not edge cases — they are the reason the sweep was worth running.

| Capability | Backend | MILFOLOGICAL target module |
|-----------|---------|---------------------------|
| DCT pixel art processor | SD.NEXT only | `entity_pixelart.py` |
| UnetPatcher (8 patch keys + replace + modifiers) | Forge only | Future `entity_unet_hook.py` |
| SDNQ 4-bit native quantization | SD.NEXT only | `entity_video.py` (video pipeline) |
| GGUF Q4→Q8 Flux | Forge only | `entity_quantized_batch.py` |
| In-graph LoRA trainer (fp4) | ComfyUI only | `entity_lora_trainer.py` |
| Text-prompt → entity SAM3 video track | ComfyUI only | `entity_video_track.py` |
| GLSL shader nodes | ComfyUI only | `entity_glsl_vfx.py` |
| JoyCaption + VQA | SD.NEXT only | `auto_caption.py` |
| Grounding DINO + SAM2 (text-prompt cutout) | InvokeAI only | `entity_cutout.py` |
| Z-Image regional prompting | InvokeAI only | Future `entity_regional.py` |
| Flux Kontext reference conditioning | InvokeAI + ComfyUI | `entity_ipadapter.py` |
| LayerDiffuse transparent alpha generation | Forge only | Future `entity_transparent_gen.py` |
| CivitAI native integration | SD.NEXT only | `entity_model_fetch.py` |
| In-graph 20+ API nodes (ElevenLabs, Kling, Veo2) | ComfyUI only | `entity_video.py` (API route) |

---

## `protocols.py` — Provisional Interface (Mine Pass 1)

Derived from the provisional convergence surface above. This interface reflects what mine pass 1 found — it is not a fixed contract. It grows as sweeps deepen. New SHARED rows become new protocol methods; new UNIQUE rows become new Protocol classes or dedicated module surfaces.

```python
# extensions/milfological/src/milfological/protocols.py
from typing import Protocol, Optional
from PIL import Image

class SDBackend(Protocol):
    """
    Provisional convergence surface for the /sdapi/v1/-lineage family
    (SD.NEXT, A1111, Forge, KoboldCpp). Methods reflect mine pass 1 findings.
    This interface grows — each sweep may add methods as new SHARED rows are confirmed.
    InvokeAI and ComfyUI have their own adapters with their own gold (see backends/).
    """

    def txt2img(self, prompt: str, **params) -> Image.Image: ...
    def img2img(self, image: Image.Image, prompt: str, **params) -> Image.Image: ...
    def interrogate(self, image: Image.Image, model: str = "clip") -> str: ...
    def model_path(self, model_type: str, name: str) -> str: ...
    def sampler_names(self) -> list[str]: ...
    def health(self) -> bool: ...


class SegmentationBackend(Protocol):
    """
    Text-prompt → entity segmentation mask.
    Mine pass 1: InvokeAI (Grounding DINO + SAM2), ComfyUI (SAM3) both implement this surface.
    SD.NEXT has SAM 2.1 — its integration contract is 🔍 MINE for a future sweep.
    This Protocol may split or grow when SD.NEXT SAM is fully mapped.
    """

    def segment(self, image: Image.Image, prompt: str) -> Image.Image: ...  # returns mask
    def cutout(self, image: Image.Image, prompt: str) -> Image.Image: ...   # returns RGBA PNG


class PixelArtBackend(Protocol):
    """
    GPU-accelerated DCT pixel art postprocessor.
    Mine pass 1: SD.NEXT only (modules/postprocess/pixelart.py).
    Remains unique until another backend implements an equivalent DCT path.
    """

    def pixelart(
        self,
        image: Image.Image,
        block_size: int = 8,
        sharpen: float = 0.0,
    ) -> Image.Image: ...
```

---

## Adapter Hierarchy

```
extensions/milfological/src/milfological/
  protocols.py                   ← Interface definitions (above)
  backends/
    sdnext.py                    ← Implements SDBackend + PixelArtBackend (/sdapi/v1/)
    a1111.py                     ← Implements SDBackend (nearly identical to sdnext.py)
    forge.py                     ← Implements SDBackend — NOTE: also has UnetPatcher access
    invokeai.py                  ← Implements SegmentationBackend (/api/v1/)
    comfyui.py                   ← Implements SegmentationBackend + video track (/api/ + WS)
    koboldcpp.py                 ← Thin wrapper: re-uses sdnext.py (exposes A1111ForgeApi)
  auto_caption.py                ← requires: SDBackend (interrogate) + sdnext specific JoyCaption
  entity_cutout.py               ← requires: SegmentationBackend
  entity_pixelart.py             ← requires: PixelArtBackend
```

---

## Uncharted Territory (🔍 MINE — next sweep targets)

These cells were not resolved in mine pass 1. They are not low-value — they are simply uncharted. Any of them could reveal a new UNIQUE gold vein or extend the convergence surface. Priority reflects how likely the fill changes current module decisions.

| Gap | Backend | Layer | Priority |
|-----|---------|-------|----------|
| InvokeAI interrogate endpoint | InvokeAI | Layer 7 | Low |
| ComfyUI captioning node API | ComfyUI | Layer 7 | Low |
| Forge JoyCaption availability | Forge | Layer 7 | Low |
| SD.NEXT block-level modifier availability | SD.NEXT | Layer 2 | Medium |
| A1111 block-level modifier availability | A1111 | Layer 2 | Medium |
| A1111 GGUF pathway | A1111 | Layer 10 | Low |
| InvokeAI LoRA injection detail | InvokeAI | Layer 5 | Medium |
| ComfyUI per-step denoiser hook | ComfyUI | Layer 2 | Medium |
| InvokeAI cross-attn hook | InvokeAI | Layer 2 | Low (no hook primitive confirmed) |
| Forge FLUX LoRA (Nunchaku) availability | Forge | Layer 5 | Medium |
| InvokeAI ESRGAN availability | InvokeAI | Layer 9 | Low |

---

## Work Queue (current ceiling-raise pass — soft-lock order)

This order reflects mine pass 1 findings. It is not fixed — if a 🔍 MINE sweep on ComfyUI or InvokeAI reveals a higher-value opener, that step moves up. Steps 5–6 are deliberately unordered (equal weight).

| Step | Artifact | What it unlocks |
|------|----------|-----------------|
| 1 | `protocols.py` (from the sketch above) | Backend abstraction exists; stubs can import it |
| 2 | `backends/sdnext.py` | Unblocks `auto_caption.py` + `entity_pixelart.py` implementation |
| 3 | `backends/invokeai.py` | Unblocks `entity_cutout.py` implementation |
| 4 | Refactor 3 Tier 1 stubs to call protocol | Stubs are no longer hardcoded; ceiling is raised |
| 5 | `backends/comfyui.py` | Unlocks SAM3 video track + GLSL VFX |
| 6 | `backends/forge.py` | Unlocks UnetPatcher hooks + GGUF throughput |
| 7 | Fill 🔍 MINE gaps (opportunistic) | Completes matrix; no blocking work |

> Gradio 4 frontend begins **after step 4**. `gr.Blocks` wraps `protocols.py` calls — no architecture decisions live in the Gradio layer.

---

*Mine pass 1 filed by Claudine Sin'claire — sourced from `MILFOLOGICAL_OPPORTUNITY_REPORT.md §I–§XVII`. No direct filesystem sweep on candidates performed yet. 🔍 MINE markers are invitations, not blockers — each is a potential gold vein waiting for the next pass.*
