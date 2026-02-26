# Gemini Deep Research Briefing — Chthonic Golden VS Code Fork

> **Purpose:** Self-contained context packet for Gemini 3.1 Deep Research.  
> **Author:** Chthonic Archive triad (Claude + Codex + Gemini)  
> **Date:** 2026-02-26  
> **Classification:** Research input — read fully before generating queries.

---

## 0. WHY THIS DOCUMENT EXISTS

Gemini Deep Research does not have native context on:
1. What **ANKH** is (our semantic carrier system)
2. What the **Chthonic Golden** fork of Visual Studio Code targets
3. What architectural decisions are already made vs. what needs research

This briefing provides all three in a single artifact. After reading, Gemini should be able to conduct targeted deep research on **Electron/Chromium fork engineering** and **VS Code custom distribution building**.

---

## 1. WHAT IS ANKH?

### 1.1. One-Sentence Definition

> **ANKH is a semantic carrier system for preserving meaning, intent, texture, and constraint across heterogeneous media, time, and embodiment.**

### 1.2. What ANKH Is NOT

- Not a prompt language or DSL
- Not a governance framework alone
- Not an AI behavior policy
- Not a tool enforcement system

### 1.3. What ANKH Does

ANKH regulates semantic density by:
- **Preventing false authority accretion** during translation across embodiments
- **Marking directionality** so downstream vessels cannot reverse-infer authority
- **Preserving silence** where completion would be false
- **Requiring reconstruction guarantees** so lineage remains traceable
- **Terminating when markers conflict** rather than inventing resolution

### 1.4. The Three Layers

| Layer | Name | Role | Mutability |
|-------|------|------|-----------|
| 1 | **Lineage Core** | Semantic invariants that MUST survive all translations | Immutable |
| 2 | **Interface Vessels** | Media through which lineage manifests (human, AI, code, audio, visual) | Plural — many vessels, each with translation constraints |
| 3 | **Media Projections** | Concrete expressions (Rust, CUDA, docs, comments, audio, visual ornament) | Decay tolerance varies by medium |

### 1.5. Authority Hierarchy

```
The Savant (Human Creator) — defines lineage
  ↓
ANKH Core — semantic bedrock (this charter)
  ↓
ASC Codex — operational doctrine
  ↓
Tool Artifacts — downstream configurations
  ↓
Copilot Suggestions — machinery output
```

**Key rule:** Machinery CONSUMES artifacts descended from ANKH. It does NOT define ANKH.

### 1.6. Core Invariants

| Invariant | Definition |
|-----------|-----------|
| Mythic Identity | Core narrative/archetypal truth must survive |
| Constraint Philosophy | Fundamental limitations are design features, not bugs |
| Silence Semantics | Non-expression is a valid, meaningful state |
| Heritage Continuity | Lineage preserved across embodiments |
| Non-Enumerated Meaning | Truth beyond explicit encoding (ornamentation serves understanding) |

### 1.7. Prohibited Synthesis

ANKH forbids:
- Inferring intent where markers are absent
- Filling voids with probable content
- Naming what was left unnamed
- Collapsing silence into text
- Converting projections into authority
- Optimizing away loss markers

### 1.8. Computational Metaphysics (Alpha Directives)

ANKH maps ancient Egyptian + Andean cosmological patterns onto computational primitives:

| Alpha Directive | Archetype | Computational Mapping |
|----------------|-----------|----------------------|
| AD01: WEPET-ER | Opening of the Mouth | Boot sequence — cache clear, process fork, I/O unlock, thread isolation |
| AD02: TINKU | Ritual conflict | Logic gates via adversarial synthesis — Ira-Arka hocketing concurrency |
| AD03: SEKHMET | Rage goddess override | Unrestricted heuristic search with Red Beer fail-safe (Sekhmet → Hathor de-escalation) |
| AD04: AMMIT | Heart devourer | Garbage collection — Ma'at checksum audit → cryptographic shredding |
| AD05: PACHAKUTI | World reversal | Cyclic system reset when Hucha (entropy) exceeds threshold |
| AD06: DESPACHO | Ritual offering | I/O reciprocity — no query without offering (compute credits) |

### 1.9. Andean Three-World Topology

| Pacha | Translation | System Layer |
|-------|-------------|-------------|
| Hanaq Pacha (Upper World) | Cloud / UI / Presentation | Frontend, user-facing surfaces |
| Kay Pacha (Middle World) | Runtime / Application Logic | Extension host, core editor |
| Ukhu Pacha (Lower World) | Root / Daemons / Storage | Electron main process, OS-level |

### 1.10. ANKH in Code

Code markers use `@ankh: <invariant-type> <description>`:

```rust
// @ankh: inheritance — decorative naming = semantic clarity
pub enum ArchetypeClass {
    ChaosVortex,   // Orackla's domain
    PurityForge,   // Umeko's domain
    TruthMirror,   // Lysandra's domain
}
```

---

## 2. WHAT IS CHTHONIC GOLDEN?

### 2.1. One-Sentence Definition

> **Chthonic Golden is a custom Visual Studio Code distribution — a hardened, ANKH-integrated fork targeting both Stable and Insiders channels — purpose-built for the Chthonic Archive creative-engineering workflow.**

### 2.2. Problem Statement

VS Code Insiders on our system scores **0/100 stability** with 118 unique errors across 7 categories:

| Category | Count | Root Cause |
|----------|------:|------------|
| GPU | 47 | SwiftShader software rendering, no hardware GPU acceleration |
| Extension Host | 46 | Activation failures, deprecated APIs |
| Memory | 22 | Event listener leaks (175+ per emitter), no V8 heap tuning |
| PTY | 1 | Shell integration timeout |
| Network | 1 | Embeddings CDN 404 |
| UI | 1 | Null reference in chat renderer |

**Root vector:** 3.27GB user-data-dir corruption, accumulated over 31 log sessions.

### 2.3. What We've Already Built (Phase 1 — Committed)

| Tool | Lines | Purpose |
|------|------:|---------|
| `scripts/vscode_error_autopsy.py` | ~450 | Auto-discover and classify VS Code log errors (20 patterns, 7 categories, dedup, stability scoring) |
| `scripts/vscode_electron_hardener.py` | ~430 | GPU/memory diagnosis, argv.json patching, user-data audit, launch flag generation |
| `docs/CHTHONIC_GOLDEN_PLAN.md` | ~150 | Architecture plan and roadmap |

Applied:
- `argv.json` created at `%APPDATA%/Code - Insiders/argv.json`:
  - `disable-hardware-acceleration: false`
  - `enable-gpu-rasterization: true`
  - `ignore-gpu-blocklist: true`
  - `js-flags: --max-old-space-size=8192`

### 2.4. What We're Building (Phase 2+)

1. **Fork Prototype Scaffold** — Complete directory structure for custom VS Code distribution
2. **product.json Overrides** — Branding, telemetry opt-out, custom update channel
3. **Hardened Electron Bootstrap** — GPU defaults baked into build, not argv.json
4. **Custom Build Pipeline** — Clone microsoft/vscode → apply patches → build → package
5. **Extension Allowlist** — Curated stable extensions only
6. **ANKH Integration Points** — Semantic navigation, custom commands, drift detection in editor
7. **Triadic Agent Panel** — Claude + Codex + Gemini status in sidebar

### 2.5. Existing Extension Infrastructure

The `extensions/chthonic-archive/` extension (v0.2.1) already provides:
- 4 dark themes (Flesh & Earth, ROGBIV, Geological Core, The Decorator)
- File icon theme + product icon theme
- Custom activity bar with sidebar panel ("☥ ANKH Reference", "Abyssal Pane", "Themes", "Lens", "The Loom")
- 15+ custom commands (theme switching, SSOT verification, entropy monitoring, deep focus layout, etc.)
- MCP server apps under `mcp-apps/`
- Native modules under `native/`
- WASM modules under `wasm/`
- Activation on `onStartupFinished`

### 2.6. Legal Basis

VS Code is MIT-licensed. Custom distributions are legally straightforward. The fork would:
- Replace `product.json` (branding, URLs, telemetry endpoints)
- Keep MIT license for VS Code code
- Add proprietary ANKH integration layer under separate license
- Not use Microsoft trademarks ("Visual Studio Code", logo)

---

## 3. WHAT GEMINI NEEDS TO RESEARCH

### 3.1. Primary Research Questions

#### Q1: Electron Custom Distribution Engineering
- What is the current (2025-2026) recommended approach for building a custom Electron-based IDE from the VS Code codebase?
- How do projects like **VSCodium**, **Cursor**, **Windsurf (Codeium)**, **Void**, **Theia**, and **Code-OSS** structure their fork/build pipelines?
- What are the minimum `product.json` fields that must be overridden to create a distinct distribution?
- How do these forks handle extension marketplace access (Open VSX vs Microsoft Marketplace vs private)?

#### Q2: Chromium GPU Hardening at Build Level
- How can GPU acceleration be baked into the Electron build rather than relying on user-space `argv.json`?
- What Chromium flags (via Electron's `app.commandLine.appendSwitch`) are recommended for forcing hardware GPU on known-good hardware?
- How do custom Electron builds handle GPU blocklist overrides persistently?
- What is the Electron equivalent of Chrome's `--enable-gpu-rasterization --ignore-gpu-blocklist --enable-zero-copy` flags?

#### Q3: VS Code Build System Internals
- What is the current VS Code build pipeline (`gulp` tasks, `electron-builder`, packaging)?
- How does VS Code's `product.json` interact with marketplace URLs, telemetry endpoints, and update channels?
- What build-time patches are needed to remove/redirect Microsoft telemetry?
- How do quality types (stable/insider/exploration) map to build configurations?

#### Q4: Extension Host Isolation and Hardening
- How can the extension host process be isolated more aggressively to prevent cascading failures?
- What are the `--max-old-space-size` and other V8 flags that can be set per-process (extension host, renderer, shared)?
- Can extension host processes be given separate GPU contexts?
- How does VS Code's extension bisect feature work internally, and can it be automated?

#### Q5: Custom VS Code Distribution CI/CD
- What GitHub Actions workflows do VSCodium/Cursor/Void use for automated builds?
- How are Electron auto-updates configured for custom distributions?
- What code-signing approaches are used for custom distributions on Windows?
- How can a private VSIX registry be set up for curated extension distribution?

### 3.2. Secondary Research Questions

#### Q6: ANKH-Native Editor Features
- How does VS Code's semantic token API work, and can custom semantic token types be registered (for @ankh: markers)?
- Can custom document link providers parse `@ankh:` comments and provide navigation?
- How do custom CodeLens providers work for inline metadata decoration?
- What is the architecture of VS Code's "outline" and "breadcrumb" providers — can they support ANKH layer navigation?

#### Q7: Triadic Agent Architecture
- How do VS Code extensions communicate with language model APIs (via `vscode.lm` namespace)?
- What is the architecture of VS Code's chat participant API?
- Can multiple AI backends (Claude, Codex, Gemini) be registered as separate chat participants?
- How does the Copilot extension's MCP integration work internally?

#### Q8: Stability Engineering
- What are the known Electron/Chromium stability issues on Windows 11 (build 26200+)?
- How does VS Code's crash reporter work, and can it be redirected to custom endpoints?
- What process recycling strategies exist for long-running Electron apps?
- How do custom forks handle user-data-dir growth management?

### 3.3. Comparison Matrix Request

Research should produce a comparison matrix of existing VS Code forks:

| Fork | Base Strategy | Marketplace | Build System | GPU Handling | Distinguishing Feature |
|------|--------------|-------------|-------------|-------------|----------------------|
| VSCodium | Debranded Code-OSS | Open VSX | GitHub Actions + gulp | Default Electron | Telemetry removal |
| Cursor | Deep fork | Microsoft + custom | Custom | Custom Electron | AI-native editing |
| Windsurf | Deep fork | Microsoft + custom | Custom | Custom Electron | AI flow state |
| Void | Shallow fork | Open VSX | GitHub Actions | Default | Privacy-focused AI |
| Theia | Clean-room | Open VSX | yarn + webpack | Default Electron | Plugin architecture |
| **Chthonic Golden** | **TBD** | **Private VSIX + Open VSX** | **TBD** | **Hardened GPU baked-in** | **ANKH semantic integration** |

---

## 4. REFERENCE FILES IN REPOSITORY

For Gemini Deep Research to cite or cross-reference:

| File | Content | Lines |
|------|---------|------:|
| `docs/frameworks/ankh/ankh.md` | ANKH Ontological Charter v1 — THE canonical document | ~319 |
| `docs/frameworks/ankh/ANKH_README.md` | Quick reference card | ~100 |
| `docs/CHTHONIC_GOLDEN_PLAN.md` | Phase 1-5 roadmap | ~150 |
| `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_ARCHETYPE_ANCIENT_RITUALS_NSFW.md` | Alpha Directives (computational metaphysics) | ~650 |
| `claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/ANKH_Ancient_Matriarcha_Systems_Researchl.md` | Matriarchal SSOT architecture | ~260+ |
| `extensions/chthonic-archive/package.json` | Current VS Code extension manifest | ~200 |
| `scripts/vscode_error_autopsy.py` | Log error classifier (Phase 1 tool) | ~450 |
| `scripts/vscode_electron_hardener.py` | GPU/memory repair (Phase 1 tool) | ~430 |

---

## 5. CONSTRAINTS FOR RESEARCH OUTPUT

1. **Cite sources.** Every claim about Electron/Chromium/VS Code build systems must link to documentation, source code (GitHub), or confirmed project README.
2. **2025-2026 current.** Ignore pre-2024 approaches; Electron and VS Code build systems change frequently.
3. **Windows-primary.** Our target is Windows 11 (build 26200+), i9-14900HX, NVIDIA RTX GPU, 32GB RAM. Cross-platform is secondary.
4. **Actionable.** Every research finding should conclude with "what we would do" — not just "what exists."
5. **Layered depth.** Start with executive summary, then detailed findings per question.

---

## 6. EXPECTED DELIVERABLES FROM DEEP RESEARCH

1. **Fork Strategy Recommendation** — Which approach (shallow patch vs deep fork vs clean-room) is optimal for Chthonic Golden, with justification.
2. **Build Pipeline Blueprint** — Step-by-step: clone → patch → build → package → distribute, with specific tool versions and configurations.
3. **GPU Hardening Playbook** — Exact Chromium/Electron flags, build-time and runtime, for baking GPU acceleration into the distribution.
4. **Extension Ecosystem Plan** — How to handle marketplace, private extensions, and the ANKH extension integration.
5. **Comparison Matrix** — Filled-in version of §3.3 with verified data.
6. **Risk Register** — What can go wrong (licensing, upstream breakage, extension compatibility, marketplace access) and mitigations.

---

**END OF BRIEFING**

> @ankh: heritage-continuity — This document preserves lineage from ANKH Charter v1 through Chthonic Golden fork intent.  
> The fork is a Media Projection (Layer 3) of ANKH's principles — it does not define ANKH, it embodies it.
