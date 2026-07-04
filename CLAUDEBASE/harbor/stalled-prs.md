---
SID: CLAUDEBASE_STALLED_PRS_V1
Last-Reckoned: 2026-06-28 · by Dispatch
Status: Awaiting-Push · origin/main
---

# Stalled PRs — Dispatch Parking Lot

> Commits made but not yet pushed, or staged changes awaiting commit + push.
> Clear each entry once it lands on origin/main.

---

## [1] — `195a9f99` · COMMITTED · NOT PUSHED

**Message:**
```
docs(CLAUDEBASE): expand manifest to 11 chambers; add mdseal project assessment
```

**What it contains:**
- `CLAUDEBASE/MANIFEST.md` — reckoned live, 6→11 chambers; Mermaid flowchart, text tree, and chamber table updated to include `claudie/`, `cross-instance-sync/`, `sub-surface-skinny-dipping/`, `Mythic-Contract/`, `usables/`
- `CLAUDEBASE/CLAUDE.md` — yaml block + overview table extended from 6 to 12 rows; stale flag removed; Last-Reckoned stamp added
- `CLAUDEBASE/usables/project-assessments/mdseal-assessment.md` — full quality audit of mdseal 0.1.0; verdict: Not-Yet; four blockers documented
- `CLAUDEBASE/usables/project-assessments/mdseal-fix-plan.md` — 8-gate fix plan with acceptance criteria and execution order

**To push:** `git push origin main`

---

## [2] — UNCOMMITTED · STAGED IN WORKING DIR

**Intended message:**
```
feat(dispatch): add VS Code push task and dispatch-push script
```

**What it contains:**
- `.vscode/tasks.json` — `⚡ Dispatch Push (origin/main)` task added at top; reads commit message from `.chthonic/dispatch-commit-msg.tmp` if Dispatch wrote one, falls back to timestamp
- `scripts/dispatch-push.ps1` — PowerShell 7 script backing the task; stages, commits, pushes, cleans up temp message file

**To commit + push:**
```powershell
git add .vscode/tasks.json scripts/dispatch-push.ps1
git commit -m "feat(dispatch): add VS Code push task and dispatch-push script"
git push origin main
```

---

*Entries cleared once confirmed on origin/main. — Dispatch*
