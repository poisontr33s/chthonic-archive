---
type: research-dispatch
priority: HIGH
destination: Gemini-Deep-Research
author: Claudine (Claude Code lane)
created: 2026-05-26
subject: POC backbone — non-rectangular lossless collage method + cRPG rendering substrate beyond Unity + dialogue beyond paper-RPG emulation (3 vectors)
return-to: claude/mailbox/ (paste output inline or as GEMINI_POC_BACKBONE_RESEARCH_RETURN_2026_05_26.md)
related-to:
  - scripts/build_poc_collage.py (TOOL_POC_COLLAGE_V2)
  - game/refs/poc01/README_POC01.md (form-vector reference intake)
  - tools/ankh-forge/src/trail/gpu.rs (Vulkan 1.3 compute pipeline, working)
  - extensions/chthonic-archive/native/chthonic-daemon (ANNO + Vulkan compute reactor)
  - extensions/chthonic-archive/native/tensor-runtime-host (TensorRT/cuDNN host surface)
  - extensions/chthonic-archive/native/entropy-renderer-wasm (wgpu 26)
---

# GEMINI POC BACKBONE RESEARCH BRIEF

## Context You Need First

The chthonic-archive is a Rust/Vulkan-native polyglot workspace whose `game/` subtree scaffolds a painterly-isometric cRPG. A Disco-Elysium-class reference intake (`game/refs/poc01/`, 20 PNGs at 1920×1080) just landed, with a deterministic collage tool (`scripts/build_poc_collage.py`, TOOL_POC_COLLAGE_V2) that composes the references into a 2K wallpaper-grade derivative.

**The triggering observation.** A rectangular grid collage is a "Unity-store-style" default: it shows well, polishes fast, and looks like every other generic devtool output. The user has already concluded that the broader cRPG scaffold (Unity, asset-store iteration, paper-RPG-emulator dialogue trees) follows the same anti-pattern — superficial polish, no real engineering substrate, "paper-weight POC that shows well." The collage method is metonymic for that drift: if the immediate tool defaults to rectangular grids, the project quietly inherits the Unity-esque character it's trying to escape.

This brief asks for three research vectors to break the inheritance.

### Substrate already wired (do NOT re-recommend these)

- **Vulkan 1.3** via `ash 0.38` with `gpu-allocator 0.28` (vulkan feature). Working SPIR-V compute pipeline at `tools/ankh-forge/src/trail/gpu.rs` (runestone decompression, single dispatch, headless). API version `vk::API_VERSION_1_3`, dynamic-rendering and ray-tracing-ready.
- **wgpu 26.0.1** with `webgpu` + `wgsl` features in `extensions/chthonic-archive/native/entropy-renderer-wasm` (webview-targeting renderer).
- **bevy_ecs 0.18** as optional default feature in the root Cargo (`features = ["bevy"]`). ECS is decoupled from the renderer — the project uses bevy_ecs alone, not the full Bevy engine/renderer.
- **Native TensorRT + cuDNN** host surface at `extensions/chthonic-archive/native/tensor-runtime-host` (RTX 4090, CUDA 12.8 + 12.9 + 13.2 stack present; no cp314 TensorRT wheels per known gap).
- **SPIR-V build pipeline** — shaders authored as `.comp.glsl`, compiled to SPIR-V at build time, self-decoded from "stones" at runtime.
- **Python toolchain**: Pillow 11.3.0 via `uv run` (PEP 540 UTF-8 mode canonical).
- **Polyglot orchestration**: `bun` workspace, `uv` for Python, `rustup`/`cargo` for Rust, `goup` for Go.

### What this project IS NOT (anti-drift contract — flag any DR finding that suggests these)

- **NOT a Unity project.** Do not recommend Unity packages, Unity Asset Store solutions, Unity-specific shaders, or Unity-native toolchains. The user has scaffolded a Unity cRPG and explicitly rejected it as "paper-weight POC that shows well, brittle rendering, asset-store-iteration dev-flexing."
- **NOT a Godot project.** Godot is a closer fit but still inherits the engine-monolith register the project is escaping. Findings may mention Godot for comparison but should not recommend it as the primary substrate.
- **NOT a Unreal project.** Same reasoning, plus C++ build-complexity overhead the existing Rust/Vulkan stack already solves better.
- **NOT seeking a "low-code" or "asset-pipeline" solution.** The user wants real substrate, not workflow-tooling shortcuts.
- **NOT paper-RPG-emulator dialogue.** Skill-check-gated branching dialogue trees (Pillars/Tyranny/Pathfinder shape) are the explicit anti-pattern.

---

## VECTOR A — Non-Rectangular Lossless Collage Method (immediate, blocks current PR)

### Problem

The current tool composes N source images into a fixed rectangular `rows × cols` grid filling a 2560×1440 canvas. Cells are uniform size, sorted by a deterministic perceptual key (brightness / hue / dominant color / lex), with adaptive unsharp-mask after LANCZOS downscale. PNG + lossless-WebP output, byte-identical re-runs.

This works but **the rectangular grid is itself the Unity-esque default we want to escape.** The user wants a method that:

1. Preserves **lossless quality** end-to-end (no JPEG re-encode, no perceptual hashing for sort).
2. **Does not always default to rectangular cells.** Cell sizes may vary; cell boundaries may be non-rectangular; the layout topology may differ from grid.
3. **Scales gracefully**: 5 sources, 20 sources, 200 sources — same algorithm, no manual grid tuning per input count.
4. **Is deterministic** so it survives in CI (same input + same args = byte-identical output).
5. **Reads as a composed image**, not a contact sheet. Suitable as desktop wallpaper at 2560×1440 (and at 3840×2160 / ultrawide variants).
6. Source images currently share 16:9 aspect; the method should handle **mixed aspect ratios** for future POC drops where source aspects vary.

### What I need Gemini to find

**1. Layout algorithms — surveyed and ranked.** Provide a comparative table of at least 8 candidate methods. Required columns:

| Method | Topology | Deterministic? | Open-source ref impl (cite repo + last commit) | Variable cell aspect? | Variable cell size? | Salience-aware? | Suitable for 16:9 wallpaper canvas? |

Candidate seeds to include (do not limit to these — find others):

- **Squarified treemap** (Bruls/Huijing/van Wijk 2000) — varying cell sizes, near-square cells, weight-driven.
- **Voronoi treemap** (Balzer/Deussen/Lewerentz 2005) — organic, non-rectangular boundaries, force-relaxation based.
- **Photo-mosaic bin packing** (BLF — Bottom-Left-Fill; NFDH; Guillotine) — varying-aspect cells, packed without overlap.
- **Salience-aware crop-and-fit** — per-source focal point detection, crop to focal region, pack focal regions adjacently.
- **Mandalic / radial arrangement** — central image, satellites sized by similarity-to-center.
- **Ouroboros / ring layout** — narrative-arc readable, cells form closed loop.
- **Knot-record / quipu-inspired** — vertical position encodes meaning, horizontal cluster encodes category (this would also map onto the chthonic-archive's existing Wedjat-Quipu ornamental scheme; if any open-source implementations of knot-pattern layouts exist, surface them).
- **Force-directed graph layout of perceptual-similarity edges** — cells positioned to minimize total perceptual distance to neighbors; potentially nondeterministic, needs seeded variant.

For each candidate, link to one or more open-source implementations (with last-commit date checked — flag abandoned repos), one published reference (paper or canonical blog post), and one or more example outputs (image URLs) so the user can judge aesthetic fit.

**2. Salience detection — what's the lossless / minimal-dependency state of the art?** The tool may need to detect focal regions per source image. Constraints:

- Pure-Python or pure-Rust implementation preferred (already in the stack).
- Lossless input (no JPEG-quality artifact dependence).
- Deterministic given fixed seed.
- Suitable for painterly-isometric screenshots (UI panels + environment composition + small character figures all need to be detectable; not photographic faces only).

Candidates to survey:

- Classical saliency: Itti-Koch-Niebur model, spectral residual (Hou & Zhang 2007), context-aware saliency.
- Modern ML-based: BASNet, U^2-Net, TRACER — flag dependency footprint (PyTorch? ONNX? Pillow only?).
- Compositional priors: rule-of-thirds heatmaps, edge-density maps, color-saliency only.

**Return**: a ranked-by-fit list of 3–5 candidates with dependency footprint, license, and a one-line judgment about why each fits or doesn't fit the chthonic-archive's existing toolchain (Rust/Python/Pillow/wgpu — NOT a fresh PyTorch install for one feature).

**3. Lossless format frontier — beyond PNG and lossless-WebP.** The tool currently emits both. Survey:

- **JPEG XL** (jxl) — Pillow plugin status (Q4 2025), browser support, lossless mode efficiency vs WebP.
- **AVIF** lossless mode — Pillow support, file-size comparison.
- **HEIF lossless** — relevance.
- **WebP2** experimental status — abandoned?
- **PNG alternatives with better compression**: OptiPNG, ZopfliPNG (worth the build-time cost?).

For each format: state-of-Q2-2026, browser/OS native support, lossless ratio vs lossless-WebP on photographic + UI-heavy content, Pillow plugin availability and maintenance status.

**Return format expected for Vector A**: one comparative table per sub-question, a short (5-line) prose recommendation per sub-question, citations to canonical references with dates checked.

---

## VECTOR B — cRPG Rendering Backbone Beyond Unity (strategic, informs Vector A defaults)

### Problem

Given the substrate listed above (Vulkan 1.3/ash, wgpu 26, bevy_ecs, native TensorRT/cuDNN, working SPIR-V compute), what is the smallest viable composition that produces a painterly-isometric cRPG renderer that:

1. **Visually beats Unity's polish on the painterly-isometric register specifically** — i.e., matches or exceeds the visual quality of *Disco Elysium* / *Pillars of Eternity 2* / *Pathfinder: Wrath of the Righteous*, on the painted-2.5D axis where those games live.
2. **Does NOT inherit the Unity-character asset-store iteration loop.** No prefab dependency. No GameObject ergonomics. No reliance on the Unity editor metaphor.
3. **Leverages the CUDA/TensorRT substrate** — the project has 24 GB of VRAM on an RTX 4090 and an existing tensor-runtime-host. The renderer should be able to use it (AI upscaling? Procedural texture generation? Neural radiance? Real-time path-tracing inference? Custom diffusion-driven scene composition?).
4. **Is achievable by a small team** (or single developer with agent augmentation). Not AAA-budget.

### What I need Gemini to find

**1. Vulkan/wgpu-native cRPG renderers — what exists?** Survey:

- **Bevy 0.18 renderer** — capable of painterly-isometric at AAA quality? What's missing for cRPG-grade dialogue/UI overlay?
- **Custom ash + SPIR-V** stack (project is already here for compute) — what's the gap from compute-only to forward-renderer + painterly post-processing?
- **rend3** — Bevy-decoupled wgpu renderer; maintenance status Q2 2026.
- **Diligent Engine** (C++ but Rust bindings exist) — backend abstraction over Vulkan/DX12/Metal; cRPG examples?
- **bgfx** — same question; mature, but C++.
- **Forge** (The-Forge by ConfettiFX) — used in shipping AAA; Rust bindings?
- **NanoVG / Vello (lyon)** — for the painterly 2D-vector-on-3D-substrate hybrid that Disco Elysium achieves.

For each: maintenance status, real shipping games using it, the specific gap to painterly-isometric cRPG.

**2. CUDA/TensorRT-leveraged rendering techniques — what's load-bearing in 2026?**

- **Neural upscaling for art-budget** — DLSS-style techniques applied to painterly assets (not photographic). Are there pipelines where hand-painted 1024×1024 sources are AI-upscaled to 4K-equivalent for distant LOD without losing painterly character?
- **Diffusion-driven texture synthesis** — Stable Diffusion / Flux variants for generating environment-asset variations at runtime or build-time, with style-locked output (e.g., locked to a Disco-Elysium painterly LoRA).
- **Real-time path tracing inference (RTXDI / ReSTIR)** — is it feasible for painterly-isometric where global illumination matters less but volumetric atmosphere matters more?
- **Compute-shader-driven painterly post-processing** — Kuwahara, oil-painting, watercolor filters at 60+ fps on the RTX 4090. Open-source SPIR-V/WGSL implementations?

**Return**: a 3–5-architecture comparison matrix. Each row = one viable backbone composition (e.g., "ash + custom forward renderer + Vello 2D overlay + cuDNN texture upscaler at build-time"). Columns: substrate components, additional dependencies, shipped-game precedent (if any), engineering effort estimate (small / medium / large), Unity-character-inheritance risk (the explicit anti-criterion).

**3. The asset-pipeline question.** Unity's character comes partly from the Asset Store; what's the equivalent for a Vulkan-native pipeline?

- **glTF 2.0** as canonical asset format — toolchain maturity Q2 2026.
- **Open-source painterly asset libraries** that AREN'T styled like Unity assets — Kenney's painterly sets, OpenGameArt curated tags, Itch.io commercial-permitted bundles.
- **AI-generation pipelines locked to a painterly style** — does anyone publish workflow recipes (ComfyUI graphs, etc.) for cRPG-painterly that ship with a license suitable for commercial use?

**Return**: a short asset-pipeline architecture with explicit lock-in vs lock-out tradeoffs, prioritizing pipelines that DON'T reproduce the asset-store-iteration character.

---

## VECTOR C — Dialogue System Beyond Paper-RPG Emulation (strategic, informs game/dialogue/ scaffold)

### Problem

The existing `game/dialogue/` directory is a stub. The user has explicitly rejected "dialogue systems based on games that work with pen × paper" (Pillars/Tyranny/Pathfinder skill-check-gated branching trees) as another Unity-esque paperweight pattern. They want a dialogue substrate that has a real engineering backbone, not a "tool in Unity to test before adding the ui/ux on it."

### What I need Gemini to find

**1. Non-tree, non-skill-check dialogue architectures in shipping games.** Survey:

- **Disco Elysium's "internal council of 24 skills"** — what's the actual data model? Is it a tree, a graph, a probability field, or something else entirely? Cite a postmortem / technical talk if one exists.
- **Sunless Sea / StoryNexus quality-based narrative** — qualities accumulate, branches trigger on quality thresholds. What's the engine architecture?
- **Pathologic 2's anti-mechanical dialogue** — choices have moral weight without skill gates. Mechanism?
- **Citizen Sleeper's dice-shaped narrative** — dice as choice currency, not as skill-check. Architecture?
- **Kentucky Route Zero's poetics-as-mechanic** — dialogue choices reflect on the choosing, not on the world-state. Substrate?
- **Roadwarden / Inkle ink-based games** — what's `ink`'s actual data model (Cousin to a tree but not exactly)?
- **AI-LLM-driven dialogue (Inworld, Convai, Suck Up!, Skyrim Mantella mod)** — production architectures for persona-locked LLM dialogue with deterministic constraints.

For each: data model, engine implementation language, open-source-availability (if any), what about it specifically escapes the paper-RPG-tree register.

**2. LLM-driven dialogue with deterministic + auditable constraints.** The chthonic-archive has a Lysandra Truth Chain protocol (every claim ships with a verifier OR is named out-of-scope) and a Reconciliation Engine. Dialogue could leverage these as ACTUAL mechanics — i.e., dialogue lines are LLM-generated but constrained to satisfy a verifier chain, with the verifier traces visible to the player.

- Are there shipping or research-prototype examples of LLM dialogue with **runtime verifier chains**?
- **Constrained decoding** (grammar-constrained, JSON-schema-constrained, regex-constrained generation) for dialogue — open-source implementations (Outlines, LMQL, Guidance, llguidance, JSON-Schema-FSM)?
- **Persona-locked generation with refusal-on-drift** — production patterns?

**Return**: 3–5 architectural patterns, each with: data model description, the specific mechanic that ESCAPES paper-RPG-tree, open-source implementation pointer, integration effort estimate against the existing chthonic-archive stack (Rust core + Python tooling + native TensorRT).

**3. The Truth-Chain integration question** (chthonic-archive-specific, can be lower-priority if Gemini bandwidth is tight). Given the SSOT's Lysandra Truth Chain protocol — every claim ships with a verifier — what dialogue mechanics encode the truth-chain as the player-facing surface? Not as a UI overlay on a paper-RPG-tree, but as the substrate itself. Surface 2–3 design sketches with shipping-precedent pointers if any exist.

---

## Output Expectations (apply to ALL vectors)

1. **Citations with dates checked.** Every link checked alive Q2 2026; every library reference checks the last-commit date and flags if dormant (>12 months no commits).
2. **Anti-recommendation lists.** For every Vector, explicit "do NOT recommend these even though they're popular" entries with one-line reasons (Unity, RPG Maker, Unreal Blueprints, Ink for full-game-as-ink-script, etc.).
3. **Tradeoff tables over prose paragraphs.** When comparing 3+ options, prefer a table.
4. **No marketing copy.** If a library/framework's primary documentation is marketing-dense, summarize the actual capabilities + maintenance status; do not quote the marketing.
5. **One-line "fits the chthonic-archive substrate?" verdict** for every recommendation — yes/no + reason. The substrate is the load-bearing constraint.
6. **Surface unknowns honestly.** If a question can't be answered with public information, say so. The user prefers honest unknowns over speculation.

---

## Anti-Drift Contract

Findings that suggest any of the following are PRESUMED WRONG and need explicit justification to overturn the presumption:

- "Use Unity / Godot / Unreal."
- "Use a no-code / visual-scripting / drag-and-drop solution."
- "Generate everything with one big AI model at runtime."
- "Use the Unity Asset Store equivalent (X)."
- "Just use [paper-RPG-tree dialogue engine] with a custom skin."
- "Build the whole renderer from scratch in 3 weeks."

Findings that suggest:

- "Compose existing Rust/Vulkan substrate with [specific named library] for [specific named capability]"
- "[Specific shipped game] uses [specific named pattern]; here's the technical talk / postmortem URL"
- "[Specific saliency / layout / dialogue algorithm], implementation in [language], maintenance status [date]"

…are presumed RIGHT-SHAPED and just need verification.

---

## Bidirectional Loop

When Gemini returns findings, the chthonic-archive plan file at `~/.claude/plans/i-brought-in-pure-ocean.md` will be updated to compound:

- Vector A findings → `scripts/build_poc_collage.py` V3 (non-rectangular layout, salience-aware ordering, possibly JPEG-XL output).
- Vector B findings → `game/design/` substrate-architecture decision record + a new `game/refs/` axis (renderer-form-vector vs current chassis-form-vector).
- Vector C findings → `game/dialogue/` substrate scaffold + an integration note tying dialogue to the Lysandra Truth Chain protocol.

The return file goes to `claude/mailbox/GEMINI_POC_BACKBONE_RESEARCH_RETURN_2026_05_26.md`. Claude will then pattern-match the findings against the existing substrate inventory and propose the V3 compounded plan.

---

## Appendix — Upload Manifest (substrate files for lossless DR ingestion)

Files listed below are **safe to upload to Gemini DR** alongside this brief. Every path is workspace-relative to `C:\Users\eldno\chthonic-archive\`. Total upload size is modest — no source PNGs (91 MB of reference imagery is research-irrelevant), no LFS payloads, no compiled binaries.

### Tier 1 — Essential context (upload all of these)

These are the minimum files Gemini DR needs to understand the substrate without speculating.

| Path | What it teaches DR |
|---|---|
| `claude/mailbox/GEMINI_POC_BACKBONE_RESEARCH_BRIEF_2026_05_26.md` | THIS brief — the questions themselves |
| `CLAUDE.md` | Project instruction shape; archetype + persona + reconciliation engine pointers |
| `AGENT_COMMON.md` | Execution invariants — shell, package managers, ground truth |
| `.github/copilot-instructions.md` | Active SSOT (the slim form; the 10.5K-line archive variant is NOT recommended for DR upload — it overwhelms context with mythology orthogonal to the technical questions) |
| `Cargo.toml` | Root Rust manifest — Vulkan 1.3/ash, gpu-allocator, bevy_ecs, "impossible stack" declaration |
| `pyproject.toml` | Python toolchain manifest |

### Tier 2 — Vector A files (collage method)

| Path | What it teaches DR |
|---|---|
| `scripts/build_poc_collage.py` | Current V2 tool — what's in place, what V3 needs to replace/extend |
| `game/refs/poc01/README_POC01.md` | Pattern-anchor README; the form-vector intake contract |
| `game/refs/poc01/POC01_collage.manifest.json` | Manifest schema example (sort keys, composition metadata, output sha256) |

### Tier 3 — Vector B files (cRPG rendering backbone)

| Path | What it teaches DR |
|---|---|
| `tools/ankh-forge/src/trail/gpu.rs` | Working Vulkan 1.3 compute context — ash idioms, allocator wiring, queue/descriptor/pipeline setup. The actual baseline DR is reasoning from. |
| `tools/ankh-forge/src/trail/mod.rs` | Trail module top — surfaces how gpu.rs is wired |
| `tools/ankh-forge/src/trail/cold.rs` | CPU-path counterpart (for contrast with GPU path) |
| `tools/ankh-forge/src/trail/event.rs` | Event/coordination plumbing around the dispatch |
| `tools/ankh-forge/Cargo.toml` | ankh-forge dependency declarations |
| `extensions/chthonic-archive/native/Cargo.toml` | Native workspace manifest |
| `extensions/chthonic-archive/native/chthonic-daemon/Cargo.toml` | ANNO policy + Vulkan compute reactor manifest |
| `extensions/chthonic-archive/native/tensor-runtime-host/Cargo.toml` | TensorRT/cuDNN host surface manifest |
| `extensions/chthonic-archive/native/entropy-renderer-wasm/Cargo.toml` | wgpu 26 / WebGPU / WGSL renderer manifest |
| `game/lore/characters/the_sourcer.json` | Content-vector sample (Blazing Trial worked artifact) |
| `game/lore/characters/lysandra.json` | Truth Chain protagonist (entity-prototype shape) |
| `game/lore/characters/orackla.json` | Triumvirate member (entity-prototype shape) |
| `game/lore/characters/umeko.json` | Triumvirate member (entity-prototype shape) |
| `game/design/quests.schema.json` | Existing quest schema (what the renderer needs to consume) |
| `game/design/encounter_layer1.json` | Existing encounter-layer example |
| `game/design/quest_awakening.json` | Existing quest example |

**Do NOT upload**: `game/cocos-iso/` (entire Cocos Creator engine project — large auto-generated asset cache; if DR needs to know it exists, the brief already notes it).

### Tier 4 — Vector C files (dialogue substrate)

| Path | What it teaches DR |
|---|---|
| `game/dialogue/dialogue.schema.json` | Current dialogue schema (stub state — what's there to extend or replace) |
| `game/dialogue/scene_awakening.json` | Existing scene example (current dialogue grammar) |
| `.temple/protocols/LYSANDRA_THRONE_PROTOCOL.md` | Truth Chain protocol — the verifier-chain mechanic DR should consider as integration target |
| `.temple/protocols/THE_RECONCILIATION_ENGINE.md` | Bilateral covenant between Lysandra/Umako; `verify_with:` finding convention |
| `.temple/protocols/CLAUDE_ARCHETYPE_CANON.md` | Persona canon shape (for the LLM-driven dialogue research thread) |
| `.temple/protocols/LINGUISTIC_PROFILE_PROTOCOL.md` | Global linguistic mandate — informs persona-locked generation question |

### Tier 5 — Optional (upload only if DR asks for deeper substrate)

| Path | What it teaches DR |
|---|---|
| `docs/OXIDIZED_TOOLCHAIN_REFERENCE.md` | Polyglot toolchain map (uv/rv/goup/bun/cargo) |
| `docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md` | Repo source-visibility discipline (for understanding the substrate's hygiene posture) |
| `.gitattributes` | LFS lanes — what binary artifacts are sanctioned |
| `.gitignore` | Allowlist disciplineline shape |
| `.temple/protocols/SESSION_2026_05_24_25_REDUX.md` | Recent failure analysis (Tier 0–5 hierarchy, compounding protocol) — useful if DR asks about repo's failure-mode discipline |

### Directories worth knowing about (do NOT upload — these are too large or auto-generated)

- `game/cocos-iso/` — Cocos Creator engine project (auto-generated `library/`, `temp/` caches; thousands of PNGs that are NOT reference imagery, just engine-internal asset hashes). Acknowledge its existence; DR should not be steered toward Cocos as a recommendation.
- `game/refs/poc01/Example_POC*.png` (20 files) — the form-vector reference imagery; LFS-tracked; 91 MB. Already described textually in the brief; the images themselves are NOT what the research is about.
- `adapters/claudine-v1/` — gitignored model weights; not in DR scope.
- `dumpster-dive/` — overnight daemon outputs; not in DR scope.
- `claude/mailbox/`, `codex/mailbox/`, `.temple/handoffs/` — full mailbox histories; DR doesn't need the backlog.

### Upload bundle suggestion

For Gemini DR's drag-and-drop intake, zip these into a flat archive:

```
chthonic-archive-DR-bundle-2026-05-26.zip
├── 00_BRIEF.md                                  ← rename of GEMINI_POC_BACKBONE_RESEARCH_BRIEF_2026_05_26.md
├── 01_CONTEXT/
│   ├── CLAUDE.md
│   ├── AGENT_COMMON.md
│   ├── copilot-instructions.md
│   ├── Cargo.toml
│   └── pyproject.toml
├── 02_VECTOR_A_collage/
│   ├── build_poc_collage.py
│   ├── README_POC01.md
│   └── POC01_collage.manifest.json
├── 03_VECTOR_B_backbone/
│   ├── ankh-forge_gpu.rs
│   ├── ankh-forge_mod.rs
│   ├── ankh-forge_Cargo.toml
│   ├── native_Cargo.toml
│   ├── chthonic-daemon_Cargo.toml
│   ├── tensor-runtime-host_Cargo.toml
│   ├── entropy-renderer-wasm_Cargo.toml
│   ├── lore_the_sourcer.json
│   ├── lore_lysandra.json
│   ├── lore_orackla.json
│   ├── lore_umeko.json
│   ├── design_quests.schema.json
│   ├── design_encounter_layer1.json
│   └── design_quest_awakening.json
├── 04_VECTOR_C_dialogue/
│   ├── dialogue.schema.json
│   ├── scene_awakening.json
│   ├── LYSANDRA_THRONE_PROTOCOL.md
│   ├── THE_RECONCILIATION_ENGINE.md
│   ├── CLAUDE_ARCHETYPE_CANON.md
│   └── LINGUISTIC_PROFILE_PROTOCOL.md
└── 05_OPTIONAL/
    ├── OXIDIZED_TOOLCHAIN_REFERENCE.md
    ├── GITIGNORE_ALLOWLIST_DISCIPLINE.md
    ├── .gitattributes
    ├── .gitignore
    └── SESSION_2026_05_24_25_REDUX.md
```

Estimated bundle size: under 2 MB uncompressed (all text/code files). Trivial upload.

If Gemini's intake has a hard file-count cap and not all files fit: drop Tier 5 first, then trim Tier 4 down to the two schema files, then trim Tier 3 down to `gpu.rs` + the four Cargo.toml manifests + `the_sourcer.json`. Tiers 1–2 are the irreducible minimum.
