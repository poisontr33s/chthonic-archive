---
type: waypoint
category: codex, claude, github copilot
updated: 2026-03-14
---

# Codex: Next Steps

## Current State (2026-03-14)

- **Reasoning:** `extra high` (workspace + global)
- **Self-modification:** Denied (config, instructions, AGENTS.md all locked)
- **Git:** Read-only (no commit/add/push)
- **Skills:** 27 non-system in `.codex/skills/` (cap is 15 — consolidation needed, 12 over)
- **Mailbox:** `codex/mailbox/ACTUAL-WORKING-HANDOFFS/` is the task queue
- **MILF-Core Pipeline:** Steps 1–4 complete, 7 prototypes analyzed (P1–P7 incl. Planescape: Tides of Numenera), MILF-Core spec at 24/24 dimensional coverage

## Active Chore

**`CHORE_CODEBASE_HYGIENE_2026_03_09.md`** — Seven-zone structural hygiene across skills (27→≤15), mailbox (294 files), scripts (255 files), tracked .pyc (6), root files (16+), forge dedup, and migration plan completions.

## Pending Work

1. **Skill consolidation** — Reduce from 27 to ≤15 per AGENTS.md anti-proliferation rules (5 redirects, 2 stashed, 1 protocol identified)
2. **Mailbox rotation** — 294 files need census, rotation policy, and archive engine
3. **Scripts variant triage** — 6+ variant families (decorator_cross_ref 3×172KB, hf_6×, claude_8×)
4. **Scripts Phase 3** — Relocate .md docs from scripts/ to docs/
5. **Tracked .pyc cleanup** — 6 compiled bytecode files tracked in git
6. **Root file archaeology** — 16+ stale artifacts at repo root
7. **Forge dedup audit** — furnace↔tempered 1:1 mirror after perfect 18/18 graduation

## WIP Lanework: MILF-Core

Organ-to-Surface-to-Prototype pipeline — comparative prototype research for entity-level genre spec.
- **Step 3** (Sets + 7 Prototypes): [MILF-Core-Step3-Deep-Exploration-Prototypes.md](codex-session-logs/archive/MILF-Core-Step3-Deep-Exploration-Prototypes.md)
- **Step 4** (Gap Analysis + MILF-Core Spec): [MILF-Core-Prototype-Analysis.md](codex-session-logs/archive/MILF-Core-Prototype-Analysis.md)

## Rules

- Check `codex/mailbox/MAILBOX_CURRENT_STATE.md` for task priority
- Execute tasks from `ACTUAL-WORKING-HANDOFFS/` as written
- Do not self-document, self-audit, or generate meta-reports unprompted
- **Claude** is the steward/engineer. **Codex** is the shepherd of the workspace/codebase. **Gemini** is the velocity engine (when active).
