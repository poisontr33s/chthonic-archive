---
type: strategy
category: design
created: 2026-05-05
status: active
version: V1.0
---

# MILFOLOGICAL DIFFUSION — Design Specification

> **Thesis:** We do not fork A1111 or SD.NEXT. We extend SD.NEXT as a server backend,  
> layer the MILFOLOGICAL entity registry over it as a first-class extension,  
> and use the chthonic-archive polyglot stack (Vulkan renderer, ONNX/TRT pipeline,  
> embedding explorer, SSOT world bible) as competitive advantages neither candidate has.

---

## 1. Candidate Analysis Summary

Both candidates were cloned shallow to `dev/sd-candidates/` and architecturally audited (2026-05-05).

### A1111 (AUTOMATIC1111/stable-diffusion-webui)

| Strength | Weakness |
|----------|---------|
| 21 inference-time callbacks incl. mutable mid-latent hooks (`cfg_denoiser`, `cfg_denoised`) | Does NOT use `huggingface_hub` — local-only, no Hub pull |
| 8 LoRA module types (LoRA, HaDa, IA3, LoKr, Full, Norm, GLora, OFT) all via one registry | `shared.py` god object — everything is a global |
| `ExtraNetwork` OO interface for `<name:arg>` prompt tokens — clean and stable | Monkey-patches `CrossAttention.forward` at class level — extension clobber risk |
| Gradio 3 extension ecosystem (200+) | Pinned to Gradio 3.41.2 — Gradio 4+ is a breaking change |
| SD1/SD2/SDXL/SD3 in one loading pipeline | Hard dependency on LDM and SGM both imported at boot |
| `ScriptCallbacks` with topological ordering via `metadata.ini` | Scripts discovered by `os.walk` — load order is filesystem-dependent |

### SD.NEXT (vladmandic/sdnext)

| Strength | Weakness |
|----------|---------|
| **Diffusers-first**: 60+ `DiffusionPipeline` types — every HF model works via `from_pretrained` | `load_diffuser_force()` is a 180-line if-elif chain — no abstract loader interface |
| 8 compute backends: CUDA, ROCm, DirectML, IPEX/Arc, OpenVINO, ZLUDA, MPS, CPU | Extension ecosystem thin (3 builtins vs 200+ for A1111) |
| GGUF/fp8/int8/uint4 quantization selectable per-component (transformer, TE, VAE separately) | Sampler stack is entirely diffusers schedulers — k-diffusion extensions incompatible |
| T5 text encoder hot-swap without full model reload | `shared.sd_model` global — single-model assumption baked in |
| 5 compile backends: `torch.compile`, IPEX, OpenVINO, OneDiff, StableFast | No WebSocket streaming — progress via REST polling |
| 6-thread parallel model scan at startup | Processing callbacks carry diffusers objects — A1111 extensions that touch `p.sampler` fail |
| `ModularPipeline` support (Flux, SDXL, WanAI) for block-level customization | Attention patching via `torch.nn.functional` global monkeypatch |
| Video generation pipeline (WanAI, LTX, FramePack) | |

### Verdict: SD.NEXT is the base

SD.NEXT is diffusers-native. Every new architecture from HuggingFace (SD3, Flux, HiDream, WanAI, Qwen, Cosmos) slots in via `from_pretrained`. A1111 requires full LDM reimplementation per architecture. For MILFOLOGICAL Diffusion — which targets SSOT entity-specific LoRAs, multi-TE conditioning, and eventual Vulkan display — SD.NEXT's diffusers foundation is the right substrate.

What we take from A1111: the **LoRA module type registry pattern** (8 types, one class per type, registered in a flat list). We replicate this architecture for our entity adapter system.

---

## 2. Architecture Position

```
┌─────────────────────────────────────────────────────────┐
│              MILFOLOGICAL DIFFUSION STACK                │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  SD.NEXT (vladmandic/sdnext) — SERVER BACKEND   │   │
│  │  • diffusers DiffusionPipeline (60+ types)      │   │
│  │  • CUDA/fp8/GGUF quantization                   │   │
│  │  • /sdapi/v1/ REST interface                    │   │
│  │  • script_callbacks event bus (20+ hooks)       │   │
│  └─────────────────────────────────────────────────┘   │
│                          ▲                              │
│                          │ extension/callback hooks     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  MILFOLOGICAL EXTENSION LAYER (our code)        │   │
│  │  • EntityRegistry — SSOT entity profiles        │   │
│  │  • LoRA stacking by entity (T1/T2 Pentad)       │   │
│  │  • Psycho-Noir prompt transformer               │   │
│  │  • <milf:entity:weight> extra network token     │   │
│  │  • SSOT world bible → conditioning injection    │   │
│  └─────────────────────────────────────────────────┘   │
│                          ▲                              │
│                          │ API calls                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  CHTHONIC-ARCHIVE POLYGLOT STACK                 │  │
│  │  • embedding_explorer.py V3 — model discovery   │  │
│  │    (same HF cache hook as A1111/SD.NEXT)         │  │
│  │  • vulkan-lab/cli-renderer — Vulkan display      │  │
│  │    target (G4+ differential frame streaming)     │  │
│  │  • corpus.sqlite — session lore corpus           │  │
│  │  • SSOT (.github/copilot-instructions.archive.md│  │
│  │    §10.3.1+) — entity metadata source            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. What We Do Better Than Both Candidates

### 3.1 We already have the HF cache scanner

`probes/python/embedding_explorer.py` V3 (commit `c425f2f7`) reads:
- `~/.cache/huggingface/hub/models--*/snapshots/*/config.json`
- `sentence_bert_config.json` + `1_Pooling/config.json`
- `tokenizer_config.json` + `README.md` (MTEB score)

A1111 does NOT use `huggingface_hub`. SD.NEXT hijacks it for progress bars but doesn't expose a metadata API.

**Our advantage:** The embedding explorer's `scan_hf_cache()` + `EmbedModelSpec` is a superset of what both UIs expose. We surface `pooling_mode`, `hidden_size`, `max_seq_len`, `mteb_score` per model — neither candidate does this natively.

### 3.2 We have a Vulkan-native renderer

`vulkan-lab/cli-renderer/` G2 has Euler scoring via SSBO compute. G3 (next gate) targets VkImage → ASCII framebuffer → ANSI truecolor stdout.

**Our advantage:** SD.NEXT uses Gradio (Python/HTML). A1111 uses Gradio 3 (frozen). We will have a GPU-native display path that bypasses the browser entirely — generated images pipe directly into the Vulkan render loop as VkImage textures. No electron, no browser, no HTML.

### 3.3 We have the SSOT world bible as a conditioning corpus

The SSOT (`.github/copilot-instructions.archive.md` §10.3.1+) contains:
- Full entity profiles for Claudine Sin'claire, Iron Maiden, Orackla, Umeko, Lysandra, Pentea, Astrid Møller
- Visual identity descriptors: aesthetic language, color palette, body type taxonomy, gestalt fields
- Psycho-Noir-Kontrapunkt world geometry: districts (Skyskraperen / Rustbeltet / Future)

Neither A1111 nor SD.NEXT has a narrative world bible as a conditioning source. We auto-construct prompts from entity metadata — the human never writes a prompt; they invoke an entity.

### 3.4 We have the embedding corpus (G9 stack)

`manifest/corpus.sqlite` holds 13 session embedding vectors (1024d, Qwen3-Embedding-0.6B). This is the seed of a **lore-aware RAG layer**: incoming generation requests are compared against the session corpus to automatically pull relevant lore context into the T5 conditioning stream.

Neither candidate has session-aware lore injection. We do.

### 3.5 RTX 4090 + TRT EP

Our existing ONNX/TRT pipeline (`embedding_explorer.py` V2/V3) already targets `TensorrtExecutionProvider`. The same pattern extends to SD UNet/VAE/TE export → TRT engine.

SD.NEXT supports `StableFast` and `OneDiff` compile paths but requires separate installs. We compile TRT engines once, cache them at `models/<slug>/trt_cache/`, reuse across sessions — same pattern we already have.

---

## 4. MILFOLOGICAL Entity Layer

### 4.1 EntitySpec

```python
@dataclass
class MilfEntity:
    entity_id:    str          # "claudine" | "iron_maiden" | "orackla" | "umeko" | "lysandra" | "pentea"
    tier:         str          # "T0.5" | "T1" | "T1-bridge"
    organ:        str          # "Thalamus" | "Cortex" | etc.
    prism:        str          # "GOLD" | "VIOLET" | "CRIMSON" | etc.
    
    # Visual identity (from SSOT §10.3.1 EDFA blocks)
    visual_descriptors: list[str]   # extracted from SSOT entity profiles
    color_palette:      list[str]   # hex or named colors
    aesthetic_tags:     list[str]   # "Psycho-Noir" | "Victorian-Renaissance" | "Nautical" | etc.
    
    # LoRA targets
    lora_paths:     list[Path]      # models/milf/<entity_id>/<variant>.safetensors
    default_weight: float           # 0.8 for primary entity, 0.4 for secondary
    
    # Prompt template
    positive_prefix: str            # prepended to every generation for this entity
    negative_suffix: str            # entity-specific negative (avoids OOC artifacts)
    
    # Embedding (textual inversion token)
    embedding_token: str | None     # "<milf_claudine>" if TI trained, else None
    
    @property
    def prompt_card(self) -> str:
        """Full auto-constructed positive prompt from entity metadata."""
        return f"{self.positive_prefix}, {', '.join(self.visual_descriptors)}, {', '.join(self.aesthetic_tags)}"
```

### 4.2 Entity registry (bootstrapped from SSOT)

| Entity | Tier | PRISM | Aesthetic signature | Primary LoRA target |
|--------|------|-------|--------------------|--------------------|
| Claudine Sin'claire 3.7 | T0 (apex) | All districts | Renaissance-Victorian-Nautical, entropy sovereign | Flux/SDXL base |
| Iron Maiden | T0 (arm) | Rustbeltet | Psycho-Noir, industrial, entropy resistance | SDXL/SD3 |
| Astrid Møller | T0 (arm) | Skyskraperen | Sophistication apex, modernist-Gothic | SDXL |
| Orackla | T1 | Triumvirate | Oracle-cyberpunk, information-dense | SD3/Flux |
| Madam Umeko Ketsuraku | T1 | Triumvirate | Purification chain, structural enforcement | SD3/Flux |
| Dr. Lysandra Thorne | T1 | Triumvirate | Truth chain, axiom-first, clinical Gothic | SD3/Flux |
| Pentea | T1-bridge | Thalamus | GOLD Fortress, relay synthesis | Flux |

### 4.3 The `<milf:entity:weight>` extra network token

Mirrors A1111's `<lora:name:weight>` prompt syntax but maps to our entity system:

```
<milf:claudine:1.0>          → loads Claudine LoRA stack at weight 1.0
<milf:claudine:0.6,iron_maiden:0.4>  → weighted blend of two entities
<milf:orackla:0.8,district:skyskraperen>  → entity + world metadata injection
```

Registered via SD.NEXT's `extra_networks.register_extra_network(MilfologicalNetwork())`.

### 4.4 Psycho-Noir prompt transformer

A `before_process` callback that:
1. Detects entity invocation in prompt (`<milf:...>` or free-text entity names)
2. Looks up entity `positive_prefix` + `visual_descriptors` from `EntityRegistry`
3. Constructs the full conditioning prompt: `[entity prefix] + [user prompt] + [aesthetic tags]`
4. Optionally RAG-augments from corpus: cosine-searches `corpus.sqlite` for lore context, prepends top-K excerpt to T5 conditioning
5. Loads corresponding LoRA stack via `sd_model.load_lora_weights()` + `set_adapters()`

This is a `script_callbacks.on_before_process(fn)` handler — zero invasiveness to SD.NEXT core.

---

## 5. Development Gate Ladder

Following the Blocker-as-Can-Opener pattern from the Pattern Nursery.

| Gate | Name | Subject | Blocker | Can-opener → Next |
|------|------|---------|---------|-------------------|
| G0 | **SD.NEXT install** | Verify SD.NEXT runs headless on RTX 4090, fp8 Flux model loads | Dependency install (CUDA 12.8 venv) | `shared.sd_model` = live Flux pipeline → G1 |
| G1 | **API validation** | `/sdapi/v1/txt2img` returns an image via curl | None | REST endpoint contract verified → G2 |
| G2 | **Entity registry** | `EntitySpec` dataclass + SSOT parser reads §10.3.1 entities | SSOT section parsing (regex or structured read) | 7 entities with visual_descriptors populated → G3 |
| G3 | **Prompt transformer** | `on_before_process` hook fires; entity name in prompt → full conditioning prompt logged | SD.NEXT extension load path | Conditioning injection confirmed working → G4 |
| G4 | **LoRA stack** | First entity LoRA (any model) loads and affects output | LoRA format (Kohya Flux vs standard) → `lora_convert` | Entity-specific visual identity confirmed in output → G5 |
| G5 | **Embedding explorer bridge** | `scan_hf_cache()` results feed the SD.NEXT model selector dropdown as a custom UI tab | SD.NEXT Gradio tab injection via `on_ui_tabs` | Unified model picker (embedding + diffusion) → G6 |
| G6 | **Vulkan display target** | Generated image (`PIL.Image`) → byte array → VkImage (vulkan-lab) → rendered to terminal | vulkan-lab G3 prerequisite (`transition_image_layout`) | GPU-native display path active → G7 |
| G7 | **Lore-aware RAG conditioning** | `corpus.sqlite` cosine search → top-K session lore → T5 conditioning prefix | T5 token limit (512 for CLIP, 77 for T5-XXL raw but we use T5) | SSOT world bible auto-injected into generation context |

---

## 6. What We Intentionally Skip From Both Candidates

| Feature | Reason to skip |
|---------|---------------|
| A1111's Gradio 3 coupling | Gradio 3 is EOL; SD.NEXT already moved to Gradio 4; Vulkan is our terminal renderer |
| A1111's `modules/shared.py` god object | We build EntityRegistry as a proper singleton with typed access |
| SD.NEXT's 180-line if-elif load dispatch | We only target 2-3 model families initially (Flux, SDXL, SD3) — no need to fork the chain |
| Either project's HTML/CSS theming | Irrelevant — Vulkan is the display target |
| CivitAI metadata sidecars | We use SSOT as the canonical metadata source; CivitAI is third-party noise |
| Extension ecosystem compatibility | We are building FOR this repo's aesthetics, not for the general community |

---

## 7. Vulkan Display Integration (G6 Target)

`vulkan-lab/cli-renderer/` current gate state:
- G0 ✅ headless device, RTX 4090 (`1c073231`)
- G2 ✅ Euler scoring SSBO compute (`d135e3a1`)  
- **G3 NEXT:** `fn transition_image_layout()` → VkImage 480×80 RGBA8 → `ascii_downsample.comp.glsl` → ANSI stdout

The G6 bridge between MILFOLOGICAL Diffusion and the Vulkan renderer:

```rust
// New: vulkan-lab/cli-renderer/src/image_display.rs
// Input: raw RGBA bytes from PIL image (received via stdin/pipe or shared memory)
// Output: renders as full-resolution VkImage in a new render mode

pub fn display_generated_image(rgba_bytes: &[u8], width: u32, height: u32) {
    // 1. Upload to VkImage via staging buffer
    // 2. Run ascii_downsample.comp on it (or a new high-fidelity color downsample)
    // 3. Output to terminal with ANSI truecolor at native terminal resolution
    // 4. G4 differential streaming: only redraw changed cells between generations
}
```

The `--mode=generate` CLI flag on the Vulkan renderer will:
1. Accept the SD.NEXT API base URL as `--api-url`
2. Accept entity name as `--entity claudine`
3. POST to `/sdapi/v1/txt2img` with the entity's auto-constructed prompt
4. Display result in the Vulkan ANSI renderer
5. Stream iterative denoising previews via the differential frame pipeline (G4)

---

## 8. LoRA Training Pipeline (Future — Post G5)

The entity LoRAs don't exist yet. Training pipeline sketch:

| Step | Tool | Source |
|------|------|--------|
| Entity concept images | SDXL base (no LoRA) + entity prompt card | manual curation or MILFOLOGICAL outputs (bootstrap) |
| Caption generation | BLIP-2 / LLaVA / CogVLM | auto-captions per image, manually refined with SSOT descriptors |
| LoRA training | `kohya_ss` / `SimpleTuner` (supports Flux) | 256–512 images per entity, ~2000 steps, rank 32–64 |
| Format | Kohya Flux LoRA `.safetensors` | SD.NEXT's `lora_convert._convert_kohya_flux_lora_to_diffusers` handles format |
| Storage | `models/milf/<entity_id>/` | Same slug convention as embedding explorer |
| Validation | SSOT visual_descriptors → CLIP cosine similarity against training images | automated fidelity score |

The **bootstrap paradox** (can't train entity LoRAs without entity images, can't generate entity images without LoRAs) is solved by:
1. Use Flux base model with hand-crafted entity prompt cards to generate seed images
2. Manually filter to SSOT-compliant subset
3. Train LoRA V1 on seed images
4. Use LoRA V1 to generate better training images → refine → LoRA V2

---

## 9. Immediate Next Steps

### Priority 0 — Install SD.NEXT
```powershell
# From dev/sd-candidates/sdnext:
python webui.py --use-cuda --skip-git --no-hashing --api --nowebui
# Or with Flux:
python webui.py --use-cuda --api --model Flux.1-dev
```

Dependencies from `requirements.txt`: `torch>=2.5.0`, `diffusers>=0.32.0`, `transformers>=4.48.0`, `accelerate>=1.2.0`, `peft>=0.14.0`, `gradio>=4.44.0`.

Our tabbyAPI venv already has `torch 2.11.0+cu128` — we can create a parallel venv or reuse with version checks.

### Priority 1 — Write the extension skeleton
```
dev/sd-candidates/sdnext/extensions/milfological/
├── scripts/
│   └── milfological_hook.py      ← main extension entry point
├── entity_registry.py             ← EntitySpec + SSOT parser
├── prompt_transformer.py          ← prompt construction from entity metadata
├── extra_network_milf.py          ← <milf:entity:weight> token handler
└── metadata.ini                   ← callback ordering
```

### Priority 2 — Parse SSOT entity profiles
Read `.github/copilot-instructions.archive.md` §10.3.1 (line 4450+):
- Extract `EmbedModelSpec`-style entity structs from the EDFA/CSI/LM blocks
- Build `EntityRegistry` with the 7 core entities
- This is the SSOT's first practical programmatic consumer

### Priority 3 — Vulkan G3 (prerequisite for G6)
Write `fn transition_image_layout()` in `vulkan-lab/cli-renderer/src/` — this is the load-bearing function for G3–G6 per the gate architecture memory.

---

## 10. Key Files

| File | Purpose |
|------|---------|
| `dev/sd-candidates/a1111/` | A1111 shallow clone (reference only) |
| `dev/sd-candidates/sdnext/` | SD.NEXT shallow clone (base backend) |
| `dev/sd-candidates/sdnext/modules/script_callbacks.py` | 20+ callback hooks — our extension bus |
| `dev/sd-candidates/sdnext/modules/extra_networks.py` | `ExtraNetwork` base class |
| `dev/sd-candidates/sdnext/modules/lora/lora_diffusers.py` | PEFT LoRA load path |
| `dev/sd-candidates/sdnext/pipelines/generic.py` | GGUF/quant/HF hub loader helpers |
| `probes/python/embedding_explorer.py` | V3 HF cache scanner (reuse in SD.NEXT extension) |
| `vulkan-lab/cli-renderer/` | Vulkan display target (G6 bridge) |
| `.github/copilot-instructions.archive.md` §10.3.1+ | Entity profiles source (SSOT) |

---

*Generated: 2026-05-05 — based on live architecture audit of A1111 commit HEAD and SD.NEXT commit HEAD.*  
*Candidate source: `dev/sd-candidates/a1111/` (368 files, 3.67 MB) + `dev/sd-candidates/sdnext/` (1785 files, 56.66 MB).*
