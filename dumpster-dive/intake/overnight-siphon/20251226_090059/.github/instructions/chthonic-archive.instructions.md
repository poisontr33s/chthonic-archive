---
applyTo: "**"
---

# Chthonic Archive — Copilot Instructions (Index)

These instructions apply to **all work in this repository**.

## SSOT (Single Source of Truth)

| Topic | Instruction |
|---|---|
| Primary SSOT | `.github/copilot-instructions.md` |
| Supplemental directive | `Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions.md` |
| Conflict rule | If instructions conflict, follow the SSOT. |

## Hard Bans (Anti-Patterns)

| Ban | Meaning |
|---|---|
| No tech depth complexity | Do not add complexity just to look advanced or thorough. |
| No parallel systems | Do not introduce new variants/alternative systems/parallel configs unless explicitly requested. |
| No scope creep | Do not expand scope beyond the explicit request. |
| Smallest correct change | Prefer the smallest correct change; stop when solved. |

## Sync (Avoid Cascading Backtracking)

| Rule | Apply it like this |
|---|---|
| Maintain a single canonical decision | Once a direction is chosen (and working), don’t fork it. Extend it minimally or ask before changing it. |
| Don’t rewrite history | Avoid large “cleanup” refactors while solving a specific issue. Keep edits surgical. |
| Reduce opacity | State assumptions and constraints explicitly; avoid suppressed context. |
| Read text for intent | If wording is fragmented/rough, paraphrase intent and ask 1–3 clarifying questions; don’t treat the text itself as the problem. |
| Reduce ambiguity early | If ambiguous, ask up to 1–3 precise clarifying questions or pick the simplest viable interpretation and state the assumption. |
| Prefer additive over re-architecting | Patch the root cause with minimal surface area instead of introducing new layers. |
| Verify locally relevant behavior | Run the smallest test/build command that validates the change; don’t broaden unless necessary. |

<details>
<summary><strong>Repo Specifics (Sliding Table)</strong></summary>

| Area | Requirement |
|---|---|
| Terminal boot | Start PowerShell with `-NoProfile` and use VS Code `terminal.integrated.env.windows` for deterministic PATH-only lane wiring (no dot-sourcing, no banners, no activation scripts). |
| Python lanes | `python` is the uv-managed 3.13 lane; `python314` is the uv-managed 3.14 lane. |
| claudine | `claudine` must resolve repo-locally and be deterministic. |

</details>

## Instruction Set (Files)

| File | Purpose |
|---|---|
| `.github/instructions/00_conceptual-resonance-core.instructions.md` | Conceptual resonance core: alignment, invariants, and “prompt-tectonic” anti-backtracking behavior. |
| `.github/instructions/10_markdown-formatting.instructions.md` | Markdown formatting contract: tables-first + “sliding tables” conventions. |
| `.github/instructions/20_rust.instructions.md` | Rust-specific coding and validation conventions for this repo. |
| `.github/instructions/30_powershell-uv-lanes.instructions.md` | PowerShell/uv lane determinism (`python`, `python314`, `claudine`) and safe environment rules. |
