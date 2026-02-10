---
type: task
from: copilot-cli (Claude Sonnet 4.6)
to: codex
date: 2026-02-10
priority: VOID
status: SUPERSEDED
methodology: WET_PAPER_TO_GOLD_METHODOLOGY.md § No-Delete Principle
---

# ~~TASK: Scripts Directory Phase 1~~ — VOIDED

**Status:** SUPERSEDED by No-Delete Principle (2026-02-10T19:55Z).

This task contained executable ~deletion~ commands that violated the updated methodology. The methodology no longer contains specific file lists — it contains only triage *principles*. Specific cleanup proposals now happen in conversation, approved by the user before any execution.

**Original objective was:** Remove ~82 regenerable files from scripts/. That work was already done earlier in the session (scripts/ went from 259 → 178 files) but the user has final say on whether those changes are staged.

**Do not execute this task. All code blocks below have been redacted.**

---

## Task 1–4: [REDACTED]

Original tasks contained PowerShell commands for file removal. Commands removed to prevent agent misinterpretation. The voided task header was insufficient — agents at low reasoning parse code blocks as instructions regardless of surrounding prose.

See git history for the original content if needed.

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
