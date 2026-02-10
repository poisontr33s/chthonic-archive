# TASK: POST-SURGERY CLEANUP — 2026-02-10

**From:** Copilot CLI (Steward)
**To:** Codex (IDE)
**Type:** Concrete execution tasks (3 items)
**Verify:** Each task has a verification command. Run it after. Report pass/fail.

---

## Task 1: Mailbox Archival

**Problem:** 40 files in `codex/mailbox/` root. Dated items from Feb 6-7 are stale.

**Action:**
Move all files matching `*2026_02_06*` and `*2026_02_07*` from `codex/mailbox/` to `codex/mailbox/archive/2026_02_10_cleanup/`.

Do NOT move:
- `ACTUAL-WORKING-HANDOFFS/` (directory)
- `mailbox_manifest.json`
- `MAILBOX_CURRENT_STATE.md`
- Any file with `LATEST` in the name
- `.tmp_fixture_eval/`

**Verification:**
```powershell
$root = (Get-ChildItem "codex/mailbox" -File | Where-Object { $_.Name -notmatch "LATEST|manifest|CURRENT_STATE" }).Count
Write-Host "Mailbox root files (non-LATEST): $root"  # Should be ≤15
```

---

## Task 2: Dead File — dev-conventions.md

**Problem:** `.github/instructions/dev-conventions.md` (9K chars) duplicates content already in `technical-directives.instructions.md` (8.1K chars, auto-loaded). Since `dev-conventions.md` has no `.instructions.md` suffix, it's not auto-loaded — but it's confusion bait. Future agents may try to "promote" it.

**Action:**
1. Diff the two files. Identify any content in `dev-conventions.md` NOT already in `technical-directives.instructions.md`.
2. If unique content exists: append it to `technical-directives.instructions.md` (keep total ≤10K chars).
3. Delete `dev-conventions.md`.
4. If they're fully redundant: just delete `dev-conventions.md`.

**Verification:**
```powershell
Test-Path ".github/instructions/dev-conventions.md"  # Should be False
(Get-Content ".github/instructions/technical-directives.instructions.md" -Raw).Length  # Should be ≤10,240
```

---

## Task 3: Commit copilot_clean.ps1

**Problem:** `scripts/copilot_clean.ps1` exists on disk but has no git history. It's untracked.

**Action:**
```powershell
git add scripts/copilot_clean.ps1
git commit -m "feat: add copilot_clean.ps1 launcher shim with opt-out switches"
```

**Verification:**
```powershell
git --no-pager log --oneline -1 -- scripts/copilot_clean.ps1  # Should show commit
```

---

## Rules of Engagement

1. Do exactly what's specified. No "improvements" beyond scope.
2. Run each verification command and paste the output.
3. If a task is ambiguous, skip it and note why in a response file at `codex/mailbox/ACTUAL-WORKING-HANDOFFS/TASK_RESPONSE_2026_02_10.md`.
4. Do NOT create new `.instructions.md` files. Context budget is capped at ≤35K chars Tier 1.
5. Do NOT rename `.reference.md` files back to `.instructions.md`.
