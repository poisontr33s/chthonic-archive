---
type: task
from: copilot-cli (Claude Sonnet 4.6)
to: codex
date: 2026-02-10
<<<<<<< HEAD
priority: VOID
status: SUPERSEDED
methodology: WET_PAPER_TO_GOLD_METHODOLOGY.md § No-Delete Principle
---

# ~~TASK: Scripts Directory Phase 1~~ — VOIDED

**Status:** SUPERSEDED by No-Delete Principle (2026-02-10T19:55Z).

This task contained executable deletion commands that violated the updated methodology. The methodology no longer contains specific file lists — it contains only triage *principles*. Specific cleanup proposals now happen in conversation, approved by the user before any execution.

**Original objective was:** Remove ~82 regenerable files from scripts/. That work was already done earlier in the session (scripts/ went from 259 → 178 files) but the user has final say on whether those changes are staged.

**Do not execute this task. All code blocks below have been redacted.**

---

## Task 1–4: [REDACTED]

Original tasks contained PowerShell commands for file removal. Commands removed to prevent agent misinterpretation. The voided task header was insufficient — agents at low reasoning parse code blocks as instructions regardless of surrounding prose.

See git history for the original content if needed.
=======
priority: high
methodology: WET_PAPER_TO_GOLD_METHODOLOGY.md § Scripts Directory Triage Protocol
constraint: Use your `artifact-upcycle` and `dumpster-upcycler` skills. Do NOT ad-hoc.
---

# TASK: Scripts Directory Phase 1 — Noise Floor Cleanup

**Objective:** Remove 82+ regenerable/duplicate files from `scripts/` per the triage protocol in `WET_PAPER_TO_GOLD_METHODOLOGY.md`.

**Rules:**
- Do NOT delete any `.py`, `.ps1`, or `.ts` script that is unique and functional.
- Do NOT modify any file outside `scripts/`.
- Do NOT condense, summarize, or rewrite any surviving file.
- Use `git rm` for removals so they are tracked.

---

## Task 1: Remove .meta.json files (75 files)

These are auto-generated metadata from `envelope_sync.py`. They are regenerable on demand and are not source code.

```powershell
# Verification: count before
(Get-ChildItem scripts -Filter "*.meta.json").Count
# Should be ~75

# Execution
Get-ChildItem scripts -Filter "*.meta.json" | ForEach-Object { git rm $_.FullName }
```

## Task 2: Remove orphan .instructions.md copies (2 files)

These are stale copies. The live versions are in `.github/instructions/`.

```powershell
git rm scripts/python-scripting.instructions.md
git rm scripts/technical-directives.instructions.md
```

**Verify live copies exist:**
```powershell
Test-Path ".github/instructions/python-scripting.instructions.md"  # Must be True
Test-Path ".github/instructions/technical-directives.instructions.md"  # Must be True
```

## Task 3: Remove backup/copy artifacts (3 files)

```powershell
git rm "scripts/asc_entity_generator - Copy.py"
git rm "scripts/asc_entity_generator.py.bak_envelope_2026_02_02"
git rm "scripts/_tmp_freq.py"
```

## Task 4: Remove transient state files (2 files)

```powershell
git rm scripts/.dcrp_state.json
git rm scripts/_tmp_freq.py.meta.json
```
>>>>>>> d9d017bde4c5b881f8301c12262614e66adf5fc7

---

## Verification

After all removals, run:

```powershell
$remaining = (Get-ChildItem scripts -File).Count
Write-Host "Files remaining: $remaining (target: ~175-180)"
# Should be ~175-180 (down from 259)

# Confirm no .meta.json survive
(Get-ChildItem scripts -Filter "*.meta.json").Count  # Should be 0

# Confirm no orphan .instructions.md survive  
(Get-ChildItem scripts -Filter "*.instructions.md").Count  # Should be 0
```

---

## Response Protocol

Respond using your `mailbox-handoff` skill:
```
python scripts/mailbox_scribe.py --emit-response
```

Or manually create `codex/mailbox/ACTUAL-WORKING-HANDOFFS/TASK_RESPONSE_SCRIPTS_PHASE1.md` with:
- Files removed (count)
- Files remaining (count)
- Any errors encountered
- Verification output

---

**DO NOT** proceed to Phase 2 (variant consolidation) or Phase 3 (doc relocation) without a new task. This is Phase 1 only.
