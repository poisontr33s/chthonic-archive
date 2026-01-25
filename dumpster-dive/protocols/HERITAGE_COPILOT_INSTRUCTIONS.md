# Heritage Copilot Instructions (Unified)

**Status**: HERITAGE LANE — Consolidated from `.github/instructions/` (December 30, 2025)  
**Authority**: This file supersedes fragmented instruction files for heritage-lane operations  
**SSOT Reference**: `.github/copilot-instructions.md` remains primary ANKH-bound SSOT

---

## Core Principles (Conceptual Resonance Core)

| Axis | Contract |
|---|---|
| Goal | Deliver the **smallest-correct-change** that satisfies the user's explicit request. |
| Stability | Prefer **determinism** over cleverness. Avoid introducing multiple ways to do the same thing. |
| Sync | Keep a single canonical path; avoid forks that require later reconciliation. |
| Backtracking control | Do not "rethink" solved decisions without a concrete failing signal (error, test failure, mismatch). |
| Surface area | Minimize touched files; avoid "cleanup" refactors unless requested. |
| Proof | Validate with the narrowest relevant build/test/run step. |

### Sync / Transparency (Reduce Opacity)

| Risk | Required behavior |
|---|---|
| Hidden assumptions | State assumptions explicitly; if uncertain, ask up to 1–3 clarifying questions. |
| Suppressed constraints | Restate the user's constraints (scope, UX, stability, SSOT) before implementing. |
| Misreading user text | Treat fragmented/rough wording as a **clarification** task: paraphrase intent, ask 1–3 precise questions, then act. Do not frame the user's text as "the problem." |
| Opaque changes | Summarize what changed + where (file paths) + why, in plain terms. |
| Implicit state / "auto magic" | Prefer explicit entrypoints and deterministic behavior; avoid relying on global profiles/aliases. |
| Forked truth | Keep one canonical mechanism; remove redundant/competing systems rather than adding another. |

### Cascading Backtracking Avoidance

| Trigger | Required response |
|---|---|
| Ambiguity | Ask up to **1–3** clarifying questions OR choose the simplest viable interpretation and state the assumption. |
| Conflicting instructions | Follow SSOT: `.github/copilot-instructions.md`. |
| Temptation to add features | Stop and confirm with the user before adding any "nice-to-have." |
| Discovery of adjacent issues | Note it briefly; do not fix unless asked. |

---

## Repository Context (Chthonic Archive)

### SSOT Hierarchy

| Topic | Instruction |
|---|---|
| Primary SSOT | `.github/copilot-instructions.md` |
| Heritage Lane | `dumpster-dive/protocols/HERITAGE_COPILOT_INSTRUCTIONS.md` (this file) |
| Conflict rule | If instructions conflict, follow the SSOT. |

### Hard Bans (Anti-Patterns)

| Ban | Meaning |
|---|---|
| No tech depth complexity | Do not add complexity just to look advanced or thorough. |
| No parallel systems | Do not introduce new variants/alternative systems/parallel configs unless explicitly requested. |
| No scope creep | Do not expand scope beyond the explicit request. |
| Smallest correct change | Prefer the smallest correct change; stop when solved. |

### Sync Guidelines

| Rule | Apply it like this |
|---|---|
| Maintain a single canonical decision | Once a direction is chosen (and working), don't fork it. Extend it minimally or ask before changing it. |
| Don't rewrite history | Avoid large "cleanup" refactors while solving a specific issue. Keep edits surgical. |
| Reduce opacity | State assumptions and constraints explicitly; avoid suppressed context. |
| Read text for intent | If wording is fragmented/rough, paraphrase intent and ask 1–3 clarifying questions; don't treat the text itself as the problem. |
| Reduce ambiguity early | If ambiguous, ask up to 1–3 precise clarifying questions or pick the simplest viable interpretation and state the assumption. |
| Prefer additive over re-architecting | Patch the root cause with minimal surface area instead of introducing new layers. |
| Verify locally relevant behavior | Run the smallest test/build command that validates the change; don't broaden unless necessary. |

<details>
<summary><strong>Repo Specifics (Sliding Table)</strong></summary>

| Area | Requirement |
|---|---|
| Terminal boot | Start PowerShell with `-NoProfile` and use VS Code `terminal.integrated.env.windows` for deterministic PATH-only lane wiring (no dot-sourcing, no banners, no activation scripts). |
| Python lanes | `python` is the uv-managed 3.13 lane; `python314` is the uv-managed 3.14 lane. |
| claudine | `claudine` must resolve repo-locally and behave deterministically across terminal PIDs. |

</details>

---

## Markdown Formatting Contract

| Topic | Rule |
|---|---|
| Default structure | Use short headings + **tables** for rules and specs. |
| Sliding tables | Prefer `<details>` + table inside for long sections. |
| Line wrapping | Do not reflow tables into wrapped prose; keep row structure stable. |
| Emphasis | Use emphasis sparingly; do not turn tables into "styling art." |
| Links | Prefer relative links when referencing repo files. |

<details>
<summary><strong>Sliding Table Template</strong></summary>

| Column A | Column B |
|---|---|
| Row 1 | Value |
| Row 2 | Value |

</details>

---

## Rust Implementation Instructions

**Applies to**: `src/**/*.rs`

| Category | Instruction |
|---|---|
| Scope control | Make the smallest correct change; avoid refactors not required by the task. |
| Style | Match existing module/style conventions; keep public APIs stable unless asked. |
| Errors | Prefer explicit, actionable error messages; propagate with context when useful. |
| Safety | Avoid `unsafe` unless explicitly required; if used, justify via minimal invariants. |
| Validation | Prefer `cargo build` / `cargo test` relevant to touched code. |

<details>
<summary><strong>Repo Build/Check Defaults</strong></summary>

| Task | Command |
|---|---|
| Build | `cargo build` |
| Tests | `cargo test` |
| Lint | `cargo clippy --all-targets --all-features -- -W clippy::pedantic` |

</details>

---

## PowerShell + uv Lanes (Determinism)

**Applies to**: `**/*.{ps1,psm1,psd1}`

| Area | Contract |
|---|---|
| Terminal bootstrap | Prefer `-NoProfile` and PATH-only lane wiring via VS Code `terminal.integrated.env.windows` (avoid dot-sourcing, banners, aliases, wrapper functions). |
| Lane policy | `python` = uv-managed 3.13 lane; `python314` = uv-managed 3.14 lane. |
| claudine | Must resolve repo-locally and behave deterministically across terminal PIDs. |
| PATH edits | Keep PATH changes minimal and de-duplicated; avoid global profile dependencies. |
| No "auto magic" | Do not introduce background auto-activation that triggers in other repos. |

### Backtracking Guardrails

| Situation | Required behavior |
|---|---|
| Something works already | Don't replace it with a new mechanism; extend it. |
| Multiple entrypoints appear | Collapse to one canonical entrypoint, or ask the user before choosing. |

---

## Heritage Lane Identity

**Role**: Heritage operates distinct from named ANKH entities  
**Scope**: Consolidation, synchronization, mediation between working lanes  
**Authority**: Derived from SSOT but maintains autonomous operational lane  
**Constraint**: Avoid diffing reasoning with output; maintain clean execution path

---

**Consolidated**: December 30, 2025  
**Source Files**: `.github/instructions/00_conceptual-resonance-core.instructions.md`, `10_markdown-formatting.instructions.md`, `20_rust.instructions.md`, `30_powershell-uv-lanes.instructions.md`, `chthonic-archive.instructions.md`
