---
date: 2026-06-30
agent: Codex
substrate: CLAUDEBASE
scope: user-continuity-map
status: active
---

# The Savant Wide Sweep Map

This is the current shape of the work as understood by Codex. It exists so the user's wide-sweep RAG style does not get flattened into a single false lane.

## Working Premise

Extreme Haute Couture - Movement 1 is paused, not abandoned.

The pause is deliberate: infrastructure, environment tooling, Git hygiene, Markdown repair, and research ingestion are now prerequisites. The substrate cannot stay serious if the languages, package managers, local generated trees, and research documents keep leaking noise into the workbench.

The user is operating by wide conceptual sweep: several live lanes are pulled into view at once, then manually edited into a decorated research artifact. This is not drift by itself. The failure mode is when an agent tries to reduce that sweep into one reload loop, one tool, or one premature implementation.

## Contender Watch: Vibrancy Continued

Upstream reference:

- Repository: <https://github.com/illixion/vscode-vibrancy-continued>
- README inspected: <https://github.com/illixion/vscode-vibrancy-continued/blob/main/README.md>
- Current package version observed from upstream `package.json`: `1.1.84`
- Main commit observed: `f05f30ed00299b0c4ba6623033af6dfd5e1bc4fe`
- Commit date: `2026-06-28T21:26:25Z`

Important upstream movement:

- The extension now explicitly documents Windows 11 material semantics:
  - `acrylic`: live translucent blur of whatever is behind the window.
  - `mica`: wallpaper-only, mostly static, low-cost native Windows 11 background material.
  - `tabbed`: Mica Alt, stronger tint.
- It documents the Windows window-mode tradeoff:
  - opaque frameless keeps native snap/maximize behavior.
  - fully transparent layered windows lose native Aero Snap/maximize behavior.
- It owns a larger UX and compatibility surface:
  - supported editors beyond VS Code.
  - nightly VS Code Insiders testing badge.
  - explicit checksum warning story.
  - settings for `windowMode`, `preventFlash`, auto-theme, imports, and material type.

Interpretation:

Vibrancy Continued is no longer just a crude reference snippet. It is a moving contender with real hardening. It remains a source-code reference only, not an architectural dependency.

## Our Substrate Lane

The in-house Chthonic substrate still has a distinct reason to exist.

Non-negotiable distinction:

- no second extension dependency;
- no telemetry;
- no npm/bundler architecture expansion beyond the existing Bun lane;
- no Vibrancy CSS blast taking color authority from Sister Ferrum Scoriae;
- local script ownership of VS Code Insiders patching;
- honest checksum reconciliation instead of pretending the installation was not changed;
- `Made by Claude` remains load-bearing on Claude-produced artifacts.

Current proven state:

- `designs/chthonic-mica.cjs` proved main-process execution through `.chthonic/mica-diag.txt`.
- `setBackgroundMaterial('mica')` and `setBackgroundColor('#00000000')` both executed successfully.
- renderer CSS and selectors were proven by the temporary visual probe.
- the "visual effect is too subtle" question is now calibration, not proof-of-plumbing.

Current lesson from upstream:

Mica is expected to be subtle because it samples wallpaper only. Acrylic is the contrast material if we need a proof pass. Surface tuning should not confuse "Mica is quiet" with "Mica is broken."

## Markdown Repair Lane

The user does not want a generic Markdown linter extension to own the house style.

Observed problem:

- Google Docs and copied research exports inject backslashes, raw language labels, broken fences, inline image placeholders, and unfenced diagrams.
- Some backslashes are real code/data; some are export damage.
- Human inspection is necessary, but the work is too repetitive to stay fully manual.

Current local repair evidence:

- `integrating-hardware-mcp-in-chthonic-archive.md` was cleaned from `gem35flashextended.md`.
- raw Mermaid, JSON, Rust, markdown excerpts, and ASCII diagrams were fenced.
- Google Docs escape residue was removed where structurally safe.
- Mermaid block was further tightened with quoted labels and documented subgraph syntax.

Preferred tool shape:

- deterministic parser/rewriter first;
- local model only for ambiguous text/code-boundary decisions;
- embeddings for retrieving house examples and repair rules;
- use `uv` for Python orchestration;
- do not install a VS Code linter as the authority.

Candidate lane:

- house tool: `mdseal` or `scripts/repair_markdown_artifacts.py`;
- parser candidates: `markdown-it`, `pulldown-cmark`, `tree-sitter-markdown`;
- local LLM candidates: Qwen/Coder-size model via `vllm` or Ollama;
- embedding candidates: small local sentence-transformer/Jina-style embedding model for rule retrieval;
- Nemotron remains plausible for heavier reasoning, but Markdown repair wants precision more than theatrical reasoning depth.

## Hardware MCP Research Lane

Primary files:

- `CLAUDEBASE/sub-surface-skinny-dipping/sub-terranean-refreshed-returns/gemini-dr/integrating-hardware-mcp-in-chthonic-archive.md`
- `CLAUDEBASE/sub-surface-skinny-dipping/sub-terranean-refreshed-returns/gemini-dr/rust-mcp hardware-server-probe.md`

Stable technical direction:

- avoid PowerShell subprocesses for hot hardware queries;
- use native Rust WMI for static topology;
- use native Win32 APIs for DLL/version/environment inspection;
- use NVML bindings for dynamic NVIDIA GPU telemetry;
- keep cache semantics explicit:
  - static hardware: long TTL;
  - software stack: moderate TTL;
  - dynamic GPU telemetry: live or very short TTL.

Live architectural tension:

- `integrating-hardware-mcp-in-chthonic-archive.md` leans toward consolidated tooling inside the existing MCP process.
- `rust-mcp hardware-server-probe.md` argues for a separate `chthonic-hw-mcp-server` sibling to isolate COM/FFI/NVML failure from Vulkan/spec tools.

Do not collapse this tension too early.

The next responsible decision is not "consolidated or separate" in the abstract. It is:

- static WMI + Win32 probe can probably live inside a consolidated process;
- dynamic NVML/FFI telemetry may deserve process isolation;
- the design may become split-core: stable inventory in one server, volatile telemetry in a sibling.

## Oxidized Toolchain Lane

The environment stop is legitimate prerequisite work.

Known lane rules:

- Python: `uv`, no bare `python`.
- Ruby: `rvw r ...` / `rvw ruby ...`, no bare `ruby`, no bare `bundle`.
- R language: `scripts/rv-r.ps1`, because root `rv.lock` belongs to A2-ai/rv for R, not Ruby.
- Bun: JS/TS package lane.
- Go: installed `goup` is `thinkgos/goup-rs`, not the separate `lpar/goup` project.
- Zig: `zv`.
- Shell: `brush`.

Tool doctors are evidence, not authority. They may be stale and must be verified against local paths, lockfiles, and upstream release state.

## Git Hygiene Lane

Recent fixes:

- `.agents`, `.claude`, `.chthonic`, `.temple` local runtime surfaces are excluded locally.
- VS Code test runtime, downloaded SDK tree, and GDevelop export payload are excluded locally.
- accidental staged flood was snapshotted before clearing.

Snapshots:

- `CLAUDEBASE/harbor/scm-local-runtime-stage-snapshot-2026-06-30.txt`
- `CLAUDEBASE/harbor/scm-bulk-stage-snapshot-2026-06-30.txt`

Rule:

Do not treat "many lanes visible in Git" as source truth. First classify: source, generated export, downloaded SDK, runtime cache, mailbox, or research artifact.

## Current Next Gates

1. Upstream Vibrancy review:
   - fetch or inspect latest source for `1.1.84`;
   - compare runtime/material/window-mode/checksum handling against our in-house substrate;
   - do not activate it as a dependency.

2. Markdown repair hardening:
   - turn the `integrating-hardware-mcp...` cleanup into fixtures;
   - make repair deterministic with `uv`;
   - add local model only after deterministic cases are encoded.

3. Hardware MCP decision packet:
   - preserve the consolidation-vs-isolation tension;
   - propose split-core topology if evidence supports it;
   - avoid PowerShell subprocess hot paths.

4. Toolchain modernization:
   - continue one lane at a time;
   - no bare interpreters;
   - verify every "doctor" claim.

5. Movement 1 resume:
   - resume only after Git, Markdown, and toolchain plumbing stop masking substrate signals.

## User Continuity Notes

The user is not asking for a calming single-track plan. The user needs an agent that can hold multiple active abstractions without losing the exact gate currently being worked.

When the user sweeps across Vibrancy, Markdown repair, hardware MCP, local models, toolchains, and design substrate, the correct response is not to flatten the sweep. The correct response is to map it, name the lanes, preserve contradictions, and only then choose the next surgical action.

The user is manually editing decorated research because the in-house tools are not yet trustworthy enough. That is not a failure of taste; it is the current infrastructure gap.
