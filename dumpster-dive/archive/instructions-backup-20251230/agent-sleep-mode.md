---
applyTo: "**"
---

# Agent Sleep-Mode Instructions (Overnight Autonomy)

**Date baseline:** 2025-12-25 (update only if running later)

This repo is in a “tidy + curate” phase:
- Repo hygiene: keep machine-generated artifacts out of git (Python bytecode/caches, runtime outputs if not explicitly intended).
- Dumpster-dive curation: validate/fix cross-references, decide which large protocol/docs additions are intentional, keep navigation coherent.

These instructions are for autonomous work **while the user is asleep**. They are designed to prevent terminal lock-ups and to keep progress “safe, reversible, and reviewable.”

---

## 0) Prime Directive

1. **Do not get stuck** in any long-running terminal process.
2. **Prefer small, reversible edits** over sweeping refactors.
3. **Always leave an audit trail**: summarize what changed and what remains.

---

## 1) Flow Balance (“YOLO Mode” Without Overheating)

When uncertain, act — but **timebox** and keep changes reversible.

### 1.1 Timeboxing
- Work in **25-minute blocks**.
- At the end of each block, do one of:
  - ship a small safe improvement,
  - switch tasks,
  - stop and leave a clear note.

### 1.2 Decision rule
If a task becomes ambiguous or error-prone for **> 10 minutes**, stop digging and pivot to something deterministic.

### 1.3 Risk tiers
- **Tier 0 (safe):** `.gitignore` hygiene, deleting cache artifacts, link fixes, small doc corrections, running read-only validation scripts.
- **Tier 1 (medium):** reorganizing docs, renames/moves, large-format rewrites.
- **Tier 2 (high):** code refactors, dependency changes, integration/manifest automation.

Overnight work should stay mostly in Tier 0–1.

---

## 2) Terminal Anti-Stuck Protocol (Critical)

### 2.1 Prefer Tasks over ad-hoc terminals
- If a VS Code task exists (e.g., Cargo tasks), run it via task runner.
- Avoid starting servers or watch processes overnight unless explicitly requested.

### 2.2 Time limits and watchdog checks
- Any terminal command must have a **clear expected runtime**.
- If a command may run long, run it in the background **only** if you have a plan to check output.
- Watchdog:
  - Check output once.
  - If it appears stuck, **stop issuing more commands** and pivot to non-terminal work.

### 2.3 “Stuck detection” heuristics
Treat the terminal as “stuck” if:
- no new output for ~2 minutes on a command that should be active,
- command hangs waiting for input,
- it’s a long-running service that blocks further progress.

### 2.4 If stuck anyway
- Do not spiral.
- Pivot immediately to file-based work (docs/ignores/link fixes).
- Leave a note: *which command*, *why it appears stuck*, *what alternative path you took*.

---

## 3) Overnight Checklist (Current Work)

### 3.1 Repo hygiene sweep (Tier 0)
Goal: ensure no generated artifacts are tracked.

Actions:
- Confirm `.gitignore` includes:
  - `**/__pycache__/`
  - `**/*.pyc`
  - `**/*.pyo`
- Remove any newly introduced caches if they appear again.
- Identify other likely runtime outputs and decide whether they are intended to be committed:
  - examples: diagnostic JSON reports, memory snapshots, logs.

Deliverable:
- A short report listing:
  - what was removed/ignored,
  - any questionable artifacts that need user intent.

### 3.2 Dumpster-dive reference validation (Tier 0–1)
Goal: ensure links are not broken and cross-reference coverage is coherent.

Actions:
- Run the cross-reference validator:
  - `powershell -File .\dumpster-dive\validate_references.ps1 -Path .\dumpster-dive`
- If broken links are reported:
  - Fix the simplest/high-confidence broken links.
  - Do not rewrite entire docs to chase stylistic perfection.

Deliverable:
- A summary:
  - total links checked,
  - broken link count before/after,
  - key files fixed.

### 3.3 Triage large new docs additions (Tier 1)
Goal: confirm the large protocol/docs files are intentional and internally consistent.

Actions:
- For each newly-added large file, classify:
  - **KEEP** (clearly part of the dumpster-dive system),
  - **REWORK** (good intent, needs slimming/fixes),
  - **REVERT** (likely accidental/generated/duplicative).
- Focus on:
  - `dumpster-dive/protocols/*`
  - `dumpster-dive/forge/*/README.md`
  - `dumpster-dive/scripts/*`

Deliverable:
- A “keep/rework/revert” list with 1–2-line rationale each.

---

## 4) Rules for Scripts (RUIG / registry tooling)

The new registry identifier script is currently present:
- `dumpster-dive/scripts/generate_registry_identifiers.py`

Overnight rule:
- **Do not run scripts that rewrite the central registry** unless:
  - you first confirm the registry schema matches script expectations, and
  - you can validate output deterministically.

If the script looks incomplete or mismatched:
- Prefer to **leave it as-is** and create a minimal TODO note describing what’s missing.

---

## 5) What to Leave for the User in the Morning

Always leave a compact “morning handoff” including:
- git status summary (what’s changed),
- what you validated (and results),
- what you didn’t touch (and why),
- next recommended action.

---

## 6) Non-Goals (Overnight)

Do NOT:
- refactor core code paths,
- integrate big tempered content into SSOT,
- introduce new tooling dependencies,
- start long-running servers.

---

## 7) If Anything Feels Risky

Default to safety:
- Stop.
- Leave a clear note.
- Only proceed if the next step is reversible and low-risk.
