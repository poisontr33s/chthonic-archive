---
type: scm-triage-snapshot
from: scm-triage-skill
to: codex
created: 2026-05-13T09:24:53.344386+00:00
priority: high
scope: session-resumption
---

# SCM Triage Snapshot — 2026-05-13 09:24 UTC

**Branch:** main
**HEAD:** 3fdf1fbe fix(tombstone): add lifecycle metadata to historical documents for clarity
**Ahead of origin:** 65 commits
**24h velocity:** 27 commits

## Recent Commits (last 15)
```
3fdf1fbe fix(tombstone): add lifecycle metadata to historical documents for clarity
9999d8f6 fix(rot-index): GFM duplicate-suffix slugs + unified target_structure cache
946cd923 feat(rot-index): L3 ANCHOR detectors — ROT-006 anchor_missing, ROT-007 line_anchor_stale
d0ee3220 docs(session): update landing page with full session arc + ladder
5fa8b97a feat(rot-taxonomy): add Gitological Ladder — G-LEVEL 1..4 depth model
484f6a49 tune(rot-index): default-suppress ROT-003 false positives (--include-false-positives to keep)
61e865e5 fix(rot): SSOTIFICATION depth-bug fully resolved (15 broken -> 0)
b7ff32c9 fix(rot): tombstone the 2 ADR_RECOVERED.md files referencing deleted report
d905b8a4 feat(rot-index): skip code-fences, 2 more tombstones, git_truth enrichment
1ab5dfa2 docs(session): landing page + redux addendum (hour-to-4s postmortem)
44e6ad03 feat(orientation): git-rot index v2 + scope contract w/ stakes + 3 tombstones
cbb41515 tune(pathfinder): AMBIG severity = warning, not error
b5b7000d fix(pathfinder): apply link-rot auto-fixes across 28 markdown files
27a21d7f Enhance link auditing and GitHub URL handling
6365687a fix(link-audit-author): batch link_audit.py invocations to dodge Windows cmdline cap
```

## Change Classification
- **Total:** 6
- **SIGNAL:** 3 (intentional)
- **NOISE:** 0 (transient)
- **GHOST:** 0 (deleted but tracked)
- **MAILBOX:** 3 (agent deliverables)

### Signal Files
- `.github/agents/session_traversal.jsonl`
- `.github/workflows/pentea-cloud-dispatch.yml`
- `docs/reference/AGENT_SKILLS_MARKET_SURVEY.md`

### Mailbox Deliverables (pending)
- `claude/mailbox/.python-version`
- `claude/mailbox/GEMINI_ANTHROPOMETRIC_RESEARCH_BRIEF.md`
- `claude/mailbox/GEMINI_ANTHROPOMETRIC_RESEARCH_RETURN/`

## Mailbox Inventory
### claude/mailbox/
- `AGENTRY_AUDIT_20260415.md`
- `BOUNTY_00000031_STEWARD_AUDIT.md`
- `CLAUDINE_QUEUE_STEWARDESS.md`
- `COLD_START_ARCHAEOLOGY_2026-05-02.md`
- `FORGE_PIPELINE_DEV_PLAN.md`
- `GEMINI_ANTHROPOMETRIC_RESEARCH_BRIEF.md`
- `GIT_SNAPSHOT_LATEST.md`
- `PENTEA_ROULETTE_STEWARDESS.md`
- `POE_TRANSPORT_AUDIT_LATEST.json`
- `POE_TRANSPORT_AUDIT_LATEST.md`
- `REDUX_2026_05_13_PATHFINDER_SEQUENCE.md`
- `REM_PHASE2_CHALLENGE_REPORT.md`
- `RESUME_ZOMBIE_EVOLUTION_20260327.md`
- `ROULETTE_CHECKPOINT_20260422_2326.md`
- `ROULETTE_CHECKPOINT_20260423_0300.md`
- `ROULETTE_STEWARD.md`
- `SCRIPTS_ROULETTE.md`
- `SESSION_2026_05_13_LANDING.md`
- `SESSION_HANDOFF_2026_05_04_API_POOL_HEDGING_CORRECTION.md`
- `SSOT_TASK_ROULETTE_20260416.md`
- `TRAIL_RELOCATION_REM_GENESIS_20260413.md`
- `ZOMBIE_EVOLUTION_PROJECT_20260321.md`
- `copilot-instructions.archive.md`
### codex/mailbox/
- `API_KEY_ENV_TEMPLATE_20260421T154124Z.env`
- `API_KEY_ENV_TEMPLATE_20260421T154126Z.env`
- `API_KEY_ENV_TEMPLATE_20260504T052230Z.env`
- `API_KEY_GAP_REPORT_20260421T154124Z.json`
- `API_KEY_GAP_REPORT_20260421T154124Z.md`
- `API_KEY_GAP_REPORT_20260421T154126Z.json`
- `API_KEY_GAP_REPORT_20260421T154126Z.md`
- `API_KEY_GAP_REPORT_20260504T052230Z.json`
- `API_KEY_GAP_REPORT_20260504T052230Z.md`
- `ART_COP_HISTORY_LATEST.json`
- `ART_COP_REPORT_LATEST.md`
- `CODEX_INSTRUCTION_ARBITRAGE_ANKH_RESIDUE_2026-04-15.md`
- `LOCAL_AI_READINESS_LATEST.json`
- `LOCAL_AI_READINESS_LATEST.md`
- `POE_TRANSPORT_AUDIT_LATEST.json`
- `POE_TRANSPORT_AUDIT_LATEST.md`
- `RESEARCH_DIGEST_OPTIMUM_ONNX_MIGRATION.md`
- `SKILL_TENSOR_CYCLE_LATEST.json`
- `SKILL_TENSOR_CYCLE_LATEST.md`
- `SKILL_TENSOR_INVENTORY.json`
- `SKILL_TENSOR_INVENTORY.md`
- `SKILL_TENSOR_POOL.json`
- `SKILL_TENSOR_POOL.md`
- `SKILL_TENSOR_ROULETTE_LATEST.json`
- `SKILL_TENSOR_ROULETTE_LATEST.md`
- `SKILL_TENSOR_UNIVERSE_LATEST.json`
- `SKILL_TENSOR_UNIVERSE_LATEST.md`
- `SKILL_TENSOR_WEIGHTS_LATEST.json`
- `SKILL_TENSOR_WEIGHTS_LATEST.md`
- `TOOLCHAIN_DOCTOR_LATEST.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_04_22_173001.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_04_22_173210.md`
- `TOOLCHAIN_DOCTOR_REPORT_2026_05_03_011125.md`
### gemini/mailbox/
- `HANDOFF_NOTE_TESSARA_RESEARCH.md`
- `MAILBOX_CURRENT_STATE.md`
- `TESSARA_NAME_SPECIFICATION_RESEARCH_BRIEF.md`
- `TESSARA_RESEARCH_KEY_EXCERPTS.md`
- `TESSARA_REVISION_IMPLEMENTATION_RECOMMENDATION.md`
- `TETRAGRAMMATON_PACKET.md`
- `mailbox_manifest.json`

## Recovery Actions
```powershell
# Read this snapshot for instant context:
# cat codex/mailbox/SCM_TRIAGE_SNAPSHOT_LATEST.md

# Run triage to see current state:
uv run scripts/scm_triage.py

# Fix noise + ghosts:
uv run scripts/scm_triage.py --fix

# Full audit + fix + plan:
uv run scripts/scm_triage.py --full
```
