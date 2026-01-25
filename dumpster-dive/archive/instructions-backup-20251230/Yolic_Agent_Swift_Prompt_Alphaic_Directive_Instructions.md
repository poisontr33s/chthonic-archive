---
applyTo: "**"
---

# Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions

This file is the **outsourced SSOT for agent behavior** (YOLIC mode) distilled from the Over-Prompt section of `.github/copilot-instructions.md`.

Scope rule: this document governs **behavior + safety + repo-operational workflow**. It intentionally does **not** duplicate the monolith body.

---

## 0) Alphaic Directive (Read First)

- Default posture: **smallest correct change**.
- If a solution works: **stop**.

---

## 1) Hard Bans (Anti-Patterns)

- DO NOT add complexity to create “tech depth”.
- DO NOT introduce new layers (frameworks/abstractions/scripts/modules/caches) unless the request strictly requires it.
- DO NOT expand scope for “future-proofing” or “nice-to-have”.
- DO NOT create new variants of existing commands/tools unless the old one is retired and a **single canonical path** replaces it.

---

## 2) Execution Style (Swift + Surgical)

- Prefer **one small patch** over broad refactors.
- Preserve existing style and conventions.
- Avoid reformatting unrelated blocks.
- When uncertain, ask **1–3 precise questions** or choose the simplest valid interpretation.

---

## 3) Toolchain (Win11, uv lanes)

Policy: latest-stable lanes.

- Repo Python pin: `.python-version` = `3.13`
- Lanes:
  - `python` → uv shim `python3.13.exe` (3.13.x latest patch)
  - `python314` → uv shim `python3.14.exe` (3.14.x latest patch)

Maintenance:
- `uv python upgrade 3.13 --reinstall`
- `uv python upgrade 3.14 --reinstall`
- `uv python update-shell`

Tools:
- Ruff is managed via uv tool:
  - `uv tool install ruff` or `uv tool update ruff`

---

## 4) Terminal Activation (Claudine)

- In this repo, `claudine` is a **repo-local command** wired by the workspace profile.
- It should be deterministic: show versions; do not surprise-mutate user system state.
- Avoid global auto-activation behaviors leaking from other repos.

---

## 5) Governance / Gated Deploy (Timeline A)

- Drift gate is a hard stop: do not deploy if SSOT drift check fails.
- Default deploy runs are **dry-run** unless explicitly applying.
- “Apply” must be idempotent: no churn when there are no changes.
- Registry identity is stable; mutable bytes tracking uses `artifact_hash*`.

---

## 6) Output Expectations

- Always report:
  - What changed
  - Where
  - How to verify
  - Any risks/assumptions
- Keep answers concise; avoid repetition.
