---
type: savant level laborious
from: Claudine (stewardess) -> on behalf of the Savant -> to Pentea (router) -> on behalf of the chthonic-archive
to: codex
created: 2026-03-09T00:00:00Z
priority: extremely necessarily high
scope: codebase hygiene — skill consolidation, mailbox rotation, script variant triage, tracked artifact cleanup, root file archaeology, forge deduplication audit, migration plan completions
subject: "Codebase Temper" — Full-Spectrum Hygiene Across Seven Structural Deficiency Zones
difficulty: |
  beyond extreme — requires ingesting 27 skill definitions, 294 mailbox files, 255 scripts,
  cross-referencing variant families, understanding WPTG governance constraints, working within
  git-read-only sandbox, and producing architectural proposals that respect the no-destroy principle
  across every zone. Multi-phase with dependency chains. Designed for GPT-5.4 xhigh reasoning
  with 1M context.
boon_system: |
  Each completed phase removes codekiller penalty points and adds boon:
  - Phase 1 (Skill Consolidation Audit): removes 2 penalties, adds 4 boon
  - Phase 2 (Mailbox Rotation Engine): removes 2 penalties, adds 5 boon
  - Phase 3 (Script Variant Triage): removes 2 penalties, adds 5 boon
  - Phase 4 (Tracked Artifact Cleanup): removes 1 penalty, adds 2 boon
  - Phase 5 (Root Archaeology): removes 1 penalty, adds 3 boon
  - Phase 6 (Forge Dedup Audit): removes 1 penalty, adds 3 boon
  - Phase 7 (Migration Plan Completions): removes 1 penalty, adds 3 boon
  - Bonus: each novel cross-reference discovery adds 0.5 boon
  - Bonus: each script that gets a correct @SID assignment adds 0.25 boon
  - Bonus: rotation script that passes uv run dry-run adds 2.0 boon
lane_exclusions: |
  DO NOT TOUCH (active frozen work):
  - extensions/chthonic-archive/** (entire extension — active lane)
  - .temple/** (agent infrastructure — sacred)
  - .github/copilot-instructions.md (SSOT pointer — frozen)
  - .github/copilot-instructions.archive.md (SSOT archive — frozen)
  - gemini/to_gemini_DR/** (active deep research)
  - WET_PAPER_TO_GOLD_METHODOLOGY.md (protected artifact)
  - AGENTS.md, AGENT_COMMON.md, CLAUDE.md, GEMINI.md (governance docs — read-only for reference)
  - Any file with ☥ ARCHIVE GOVERNANCE header
  - Any *.reference.md in .github/instructions/
  - STRATEGIC_PLAN.md, HARVEST_REGISTRY.md, PWSH_RULES.md (protected)
  - dumpster-dive/forge/extension-archaeology/** (active archaeology lane)
governance: |
  - WPTG (Wet Paper To Gold) is absolute. No file destruction. Propose, upcycle, archive, prep to makeshift.
  - codekiller.md anti-pattern applies. Deletion proposals without salvage = penalty.
  - Git is READ-ONLY for you. No git commit, git add, git push, git stash. Ever.
  - User stages + commits via VS Code Insiders.
  - One clarification max per phase, then execute.
  - Read SKILL.md before invoking any skill.
  - Check anti-proliferation rules in AGENTS.md (≤15 skill cap) before proposing skill changes.
---

# CHORE: Codebase Temper — Seven-Zone Structural Hygiene

## Problem Statement

This repository has grown through 5+ months of multi-agent creative work. The living artifacts are sound. The governance is intact. But the **structural tissue** — the skills, mailbox, scripts, tracked build artifacts, root-level files, and forge pipeline — has accumulated drift that no single agent session has addressed holistically.

The numbers tell the story:

| Zone | Metric | Target | Delta |
|------|--------|--------|-------|
| `.codex/skills/` | 27 non-system skills | (AGENTS.md cap) | **+12 over cap** |
| `codex/mailbox/` | 294 files | <50 active + archived series | **~244 need rotation** |
| `scripts/` | 255 tracked files in 6+ variant families | Consolidated unique scripts | **Unknown dedup ratio** |
| Tracked `.pyc` | 6 compiled bytecode files in git | 0 (should never be tracked) | **+6** |
| Root stale files | 16+ stale `.py`, `_test.json`, `_audit.json` | 0 at root (archived or relocated) | **+16** |
| Forge furnace↔tempered | 1:1 duplicate (18/18 graduated, 0 rejected) | Clarified relationship | **Audit needed** |
| `docs/STAGE_1_MIGRATION_PLAN.md` | Outstanding TODOs | Completed or tracked | **≥2 unresolved** |

This chore requires you to **ingest all 27 skill definitions, scan 294 mailbox files, cross-reference 255 scripts**, and produce architectural proposals for each zone — all while respecting WPTG governance (no destruction, only upcycling and proposals).

This is not cleanup. This is **structural diagnostics with remediation plans.**

---

## Phase 1 — Skill Consolidation Audit (CRITICAL)

### Context

`.codex/skills/` contains 27 non-system skill directories. `AGENTS.md` mandates a cap of ≤15. `codex/NEXT.md` lists this as the #1 pending work item. Previous audit identified 5 REDIRECT skills, 2 STASHED skills, and 1 PROTOCOL-not-skill — but no consolidation has been executed.

### TODO 1.1: Read All 27 SKILL.md Files

For every directory in `.codex/skills/` (excluding `.system/`), read the `SKILL.md` and classify into:

| Category | Criteria | Action Proposal |
|----------|----------|-----------------|
| **REDIRECT** | Description starts with "REDIRECT —" and names a target skill | Propose archive (move content to target's SKILL.md as "Absorbed from:" note) |
| **STASHED** | Description starts with "STASHED -" with rationale | Propose archive (content already absorbed elsewhere) |
| **PROTOCOL** | Describes behavior embedded in all agents, not a standalone execution lane | Propose merge into AGENT_COMMON.md or relevant protocol doc |
| **ACTIVE** | Has a CLI, script, or distinct execution pathway | Keep |
| **DUPLICATE** | Active but functionally overlaps with another active skill | Propose merge with rationale |

**Known classifications (verify these, don't trust blindly):**

| Skill | Expected Category | Redirect Target |
|-------|-------------------|-----------------|
| `claude-skill-bridge` | REDIRECT | → skill-polisher |
| `codex-skill-bridge` | REDIRECT | → skill-polisher |
| `gh-address-comments` | REDIRECT | → gh-fix-ci |
| `postman` | REDIRECT | → mailbox-handoff |
| `meta-polisher-validator` | REDIRECT | → skill-polisher |
| `artifact-upcycle` | STASHED | → dumpster-upcycler |
| `script-envelope` | STASHED | → AGENT_COMMON.md |
| `decision-razor` | PROTOCOL | → AGENT_COMMON.md |
| `sora` | ACTIVE | (verify — does it have a working CLI?) |

### TODO 1.2: Produce Consolidation Proposal

Write `codex/mailbox/SKILL_CONSOLIDATION_PROPOSAL.md` containing:

1. **Full inventory table** — all 27 skills with: name, category, has CLI (Y/N), has scripts/ subdir (Y/N), line count of SKILL.md, proposed action
2. **Merge map** — for each REDIRECT/STASHED/PROTOCOL skill, the exact target and what content (if any) should be absorbed
3. **Post-consolidation count** — projected skill count after all proposed actions (must be ≤15)
4. **Risk assessment** — any skills where the redirect target doesn't exist or the absorption would lose unique capabilities
5. **Tracked `.pyc` files inside skills** — list them (known: 5 files across artifact-upcycle, codekiller-remediation-gate, mailbox-handoff, script-envelope, skill-polisher) and propose `.gitignore` additions

### TODO 1.3: Verify Cross-References

For each REDIRECT skill, verify the target skill actually exists in `.codex/skills/` AND in `.claude/skills/` (Claude has a parallel skill set). If a redirect target is missing from either side, flag it.

**Output:** `codex/mailbox/SKILL_CONSOLIDATION_PROPOSAL.md`

---

## Phase 2 — Mailbox Rotation Engine (CRITICAL)

### Context

`codex/mailbox/` contains 294 files. Many are timestamped series from burst operations:
- 15× `TOOLCHAIN_DOCTOR_REPORT_2026_02_23_*` (12 generated within 10 minutes on Feb 23)
- 14× `VSCODE_TERMINAL_TRIAGE_*` directories (Feb 26 burst)
- 16× `API_KEY_GAP_REPORT_*` files (8 timestamp pairs, Feb 26)
- 12× `POE_CALLABILITY_*` files (3 registry + 3 sample variants, each json+md)
- 8× `SESSION_HANDOFF_*` files
- 11× `RELATIONSHIP_AUDIT_*` files
- 6× `VSCODE_INSIDERS_MATRIX_*` directories

The `MAILBOX_CURRENT_STATE.md` lists 52 "active" files but was last updated 2026-02-23 — 14 days stale.

### TODO 2.1: Census the Mailbox

Scan every file and directory in `codex/mailbox/` and produce a structured census:

```
{
  "total_files": N,
  "total_directories": N,
  "series": [
    {
      "prefix": "TOOLCHAIN_DOCTOR_REPORT",
      "count": 15,
      "date_range": "2026-02-17 to 2026-02-23",
      "latest": "TOOLCHAIN_DOCTOR_REPORT_2026_02_23_165711.md",
      "proposed_action": "Archive 13, keep LATEST + most recent timestamped"
    },
    ...
  ],
  "singletons": [...],
  "subdirectories": [
    {
      "name": "archive/",
      "file_count": 77,
      "purpose": "Previous archive rotation"
    },
    {
      "name": "ACTUAL-WORKING-HANDOFFS/",
      "file_count": 5,
      "last_modified": "2026-02-10",
      "status": "STALE — no tasks newer than 27 days"
    },
    ...
  ]
}
```

### TODO 2.2: Design Rotation Policy

Write a rotation policy document that defines:

1. **Series consolidation rule**: For any prefix with >3 timestamped files, keep: (a) the `*_LATEST.*` file, (b) the most recent timestamped file, (c) archive the rest to `codex/mailbox/archive/` in a subdirectory named after the series prefix
2. **Staleness threshold**: Files older than 30 days with no cross-reference from active documents → candidate for archive rotation
3. **Protected files**: `MAILBOX_CURRENT_STATE.md`, `mailbox_manifest.json`, anything in `ACTUAL-WORKING-HANDOFFS/`
4. **Directory series handling**: For the 14× `VSCODE_TERMINAL_TRIAGE_*` dirs and 6× `VSCODE_INSIDERS_MATRIX_*` dirs, propose consolidation into single summary documents + archive of raw data

### TODO 2.3: Build the Rotation Script

Create `scripts/mailbox_rotation.py` following Metabolic Standard v3:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Mailbox rotation engine — consolidates timestamped series, archives stale files,
and regenerates MAILBOX_CURRENT_STATE.md.

@SID:           UTIL_MAILBOX_ROTATION_V1
@Type:          Utility
"""
```

Requirements:
- `--dry-run` mode (DEFAULT — never destructive without explicit flag)
- `--target codex` or `--target claude` (operate on either mailbox)
- Reads `codex/mailbox/` (or `claude/mailbox/`)
- Identifies series by prefix pattern matching
- Applies rotation policy from TODO 2.2
- Outputs a rotation plan as JSON before executing
- In execute mode (`--execute`), moves files to `archive/` subdirectories (NOT deletion)
- Regenerates `MAILBOX_CURRENT_STATE.md` after rotation
- Uses `pathlib` only (no `os.path`)
- Uses `uv run` compatibility (no PEP 723 inline metadata — project-integrated per v3)

### TODO 2.4: Update MAILBOX_CURRENT_STATE.md

Regenerate the state file to reflect the actual current contents (not the 14-day-stale version).

**Output:** `codex/mailbox/MAILBOX_ROTATION_POLICY.md`, `scripts/mailbox_rotation.py`, updated `codex/mailbox/MAILBOX_CURRENT_STATE.md`

---

## Phase 3 — Script Variant Triage (CRITICAL)

### Context

`scripts/` contains 255 tracked files. Multiple variant families exist where a single concept was iterated into N separate files without consolidating back:

| Family | Count | Files |
|--------|-------|-------|
| `decorator_cross_ref_*.py` | 3 | `_enhanced.py`, `_maximum.py`, `_production.py` (172KB combined) |
| `hf_*.py` | 6 | `discovery`, `gemma_probe`, `model_scout`, `prep`, `probe`, `refiner` |
| `theme_*.py` | 8 | `artcop`, `color_diversity`, `contrast_audit`, `parity`, `promote_master`, `scaffold`, `sfs_transmute`, `token_coverage` |
| `poe_*.py/ps1` | 5 | `account.ps1`, `api_setup_pull.py`, `lane.py`, `sdk_lane.py`, `transport_audit.py` |
| `claude_*.ps1` | 8 | `crossover`, `healthcheck`, `ide`, `ide_settings_generate`, `insiders_selfheal`, `plugin_ensure`, `profile`, `claudine` |
| `ssot_*.ps1` | 4 | `crc_selector`, `outline_extractor`, `registry_query`, `tier_query` |

`codex/NEXT.md` lists this as pending work items #2 (variant consolidation) and #3 (relocate 13 .md docs from scripts/ to docs/).

### TODO 3.1: Full Script Census

For every file in `scripts/` (including subdirectories `bin/`, `lib/`, `data/`, `aws/`, `hooks/`, `.deprecated/`):

1. Record: filename, extension, line count, has @SID (Y/N), has shebang (Y/N), has Metabolic Standard header (Y/N), last-modified date
2. Group into families by prefix pattern
3. Flag files that are markdown docs (`.md`) living in `scripts/` — these should be in `docs/`
4. Flag files in `.deprecated/` — verify they have equivalent replacements in the main scripts/ dir

### TODO 3.2: Variant Family Analysis

For each variant family with 3+ members:

1. Read all members and produce a **diff summary** — what makes each variant unique
2. For `decorator_cross_ref_*.py` (172KB, 3 files) specifically:
   - What is the functional difference between `_enhanced`, `_maximum`, and `_production`?
   - Can they be consolidated into one script with a `--mode enhanced|maximum|production` flag?
   - What signal from each variant is unique and must be preserved?
3. For `hf_*.py` (6 files): Are these genuinely distinct tools (discovery vs probe vs refiner are different tasks) or do some overlap?
4. For `theme_*.py` (8 files): These are lane-excluded per the chore frontmatter — **document their existence but DO NOT propose changes**

### TODO 3.3: Script Header Compliance Audit

Audit all `.py` files in `scripts/` against Metabolic Standard v3:
- Must have `#!/usr/bin/env python3` shebang
- Must have `#-*- coding: utf-8 -*-`
- Must NOT have PEP 723 `/// script` blocks (v3 prohibits these — dependencies in `pyproject.toml`)
- Must have `@SID` in docstring
- Must have `@Type` in docstring

For `.ps1` files, check against `PWSH_RULES.md` conventions.

Produce a compliance table sorted by non-compliance severity.

### TODO 3.4: Produce Consolidation Proposal

Write `codex/mailbox/SCRIPTS_VARIANT_TRIAGE.md` containing:
1. Full census table
2. Family analysis with diff summaries
3. Header compliance table
4. Consolidation proposals (with preserved signal, not deletion)
5. List of .md files that should relocate to `docs/`

**Output:** `codex/mailbox/SCRIPTS_VARIANT_TRIAGE.md`

---

## Phase 4 — Tracked Build Artifact Cleanup (HIGH)

### Context

6 compiled Python bytecode files (`.pyc`) are tracked in git. These are generated artifacts that change on every Python version bump and should never be in source control.

### TODO 4.1: List and Verify All Tracked .pyc Files

Known tracked `.pyc` files:
1. `.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc`
2. `.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc`
3. `.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc`
4. `.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc`
5. `.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc`
6. `dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc`

Run `git ls-files '*.pyc' '*__pycache__*'` to verify this list is complete.

### TODO 4.2: Verify .gitignore Coverage

Check the root `.gitignore` for `__pycache__/` and `*.pyc` patterns. If missing, propose additions.

Also check for `.codex/skills/**/__pycache__/` coverage specifically.

### TODO 4.3: Generate Cleanup Commands

Since you CANNOT run `git rm --cached`, produce a cleanup script that the user can execute:

Write `codex/mailbox/TRACKED_ARTIFACT_CLEANUP.md` containing:
1. The exact `git rm --cached` commands for each file
2. The `.gitignore` additions needed
3. A verification command to confirm no `.pyc` remains tracked after cleanup

```powershell
# User executes this — Codex cannot:
git rm --cached .codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc
git rm --cached .codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc
git rm --cached .codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc
git rm --cached .codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc
git rm --cached .codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc
git rm --cached dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc

# Verify clean:
git ls-files '*.pyc' '*__pycache__*'
# Should return empty
```

**Output:** `codex/mailbox/TRACKED_ARTIFACT_CLEANUP.md`

---

## Phase 5 — Root File Archaeology (HIGH)

### Context

The repository root contains 16+ files that are stale artifacts from previous sessions — test outputs, one-off scripts, intermediate processing results. Per WPTG, these cannot be deleted. They must be archaeologically assessed: what signal do they contain, where should they live, and what is their gold grade?

### TODO 5.1: Inventory and Assess Root Stale Files

| File | Type | Assess |
|------|------|--------|
| `strip_ssot.py` | Python script | SSOT stripping tool v1 |
| `strip_ssot_v2.py` | Python script | SSOT stripping tool v2 (supersedes v1?) |
| `strip_post_ssot.py` | Python script | Post-SSOT stripping tool |
| `strip_broken_headers.py` | Python script | Header repair tool |
| `get_hash.py` | Python script | Hash computation utility |
| `claude_test.py` | Python script | Claude integration test |
| `purify_ssot.py` | Python script | SSOT purification tool |
| `cargo_test.json` | JSON | Cargo test output |
| `meta_cli_test.json` | JSON | Meta CLI test output |
| `status_test.json` | JSON | Status test output |
| `validate_test.json` | JSON | Validation test output |
| `kcp_batch1_verify.json` | JSON | KCP batch verification |
| `stage2_1_audit.json` | JSON | Stage 2.1 audit output |
| `stage2_1_final_audit.json` | JSON | Stage 2.1 final audit output |
| `stage2_1_recolor_audit.json` | JSON | Stage 2.1 recolor audit |
| `stage2_1_round3_audit.json` | JSON | Stage 2.1 round 3 audit |
| `challenge_task_session_context_truncted.md_pretty.md` | Markdown | Session truncation artifact |
| `challenge_task_session_context_truncted.md_resume.md` | Markdown | Session resume artifact |
| `challenge_task_session_context_truncted.md_structured.txt` | Text | Structured session artifact |
| `broken-refs.json` | JSON | Broken reference scan output |
| `server_debug.json` | JSON | Server debug output |

For each file:
1. Read the first 20 lines to assess purpose
2. Check if it has a `@SID` or identifiable origin
3. Determine gold grade: **EXTRACT** (has reusable signal), **ARCHIVE** (historical value only), **DUPLICATE** (superseded by another file)
4. Propose destination: `dumpster-dive/forge/anvil/` (for structured data), `docs/sessions/` (for session artifacts), `scripts/.deprecated/` (for superseded scripts), or `audit-reports/` (for test/audit outputs)

### TODO 5.2: Produce Archaeology Report

Write `codex/mailbox/ROOT_ARCHAEOLOGY_REPORT.md` containing:
1. Full inventory table with gold grade and proposed destination
2. Signal extraction notes (what useful data is buried in each)
3. A relocation proposal (remember: PROPOSE only, user approves and executes)
4. Cross-references — do any of these root files get referenced from `docs/STAGE_1_MIGRATION_PLAN.md` or other governance docs?

**Output:** `codex/mailbox/ROOT_ARCHAEOLOGY_REPORT.md`

---

## Phase 6 — Forge Deduplication Audit (HIGH)

### Context

`dumpster-dive/forge/` is the WPTG transmutation pipeline:
- `anvil/` — raw ore assessment (3 files: CODEBASE_ANOMALY_HARVEST.json, CORPSE_VAULT_DEEP_AUDIT.json, README.md)
- `furnace/` — heating/smelting stage with language subdirectories (csharp, c_cpp, docs, go, powershell, python, ruby, schemas, typescript)
- `tempered/` — graduated artifacts with language subdirectories + manifests + summaries
- `quench/` — empty (only README.md)
- `slag/` — empty (only README.md)
- `tea-vault/` — empty (only README.md)
- `intake/` — empty (only README.md)
- `extension-archaeology/` — EXCLUDED (active archaeology lane)

The previous chore (EXTENSION_CONTRIBUTION_GRAPH_VALIDATOR_CHORE) produced a **perfect 18/18 graduation** from furnace to tempered with 0 rejections. This means furnace and tempered are currently 1:1 mirrors (every furnace artifact has an identical copy in tempered).

### TODO 6.1: Verify Furnace ↔ Tempered Duplication

For each language subdirectory that exists in both `furnace/` and `tempered/`:
1. List files in both
2. Compare file sizes (byte-for-byte identical?)
3. Check `FURNACE_MANIFEST.json` and `GRADUATION_MANIFEST.json` for provenance

### TODO 6.2: Assess Empty Pipeline Stages

For `quench/`, `slag/`, `tea-vault/`, and `intake/`:
1. Read each README.md to understand the intended purpose
2. Determine if these stages were designed but never used, or if they were bypassed by the 18/18 perfect graduation
3. Document whether the pipeline design assumes all stages will eventually have content

### TODO 6.3: Produce Forge Status Report

Write `codex/mailbox/FORGE_DEDUP_AUDIT.md` containing:
1. Furnace ↔ tempered comparison matrix (file-by-file)
2. Whether furnace should be cleared after confirmed graduation (PROPOSE only)
3. Empty stage assessment
4. Pipeline health summary — is the forge pipeline structurally sound for future transmutations?

**Output:** `codex/mailbox/FORGE_DEDUP_AUDIT.md`

---

## Phase 7 — Migration Plan Completions (MODERATE)

### Context

`docs/STAGE_1_MIGRATION_PLAN.md` contains at least 2 outstanding TODOs that have not been resolved:

1. **Line ~206**: `# TODO: Create ankhrc_validator.py` — a post-migration verification tool to ensure `.ankhrc` resolves all paths
2. **Section 7 (lines ~212+)**: Session capture mechanism — `scripts/session_extractor.py` that parses Copilot chat logs into structured summaries

### TODO 7.1: Build ankhrc_validator.py

Create `scripts/ankhrc_validator.py` following Metabolic Standard v3:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Validates .ankhrc path resolution — ensures every path declared in .ankhrc
points to an existing file or directory in the repository.

@SID:           UTIL_ANKHRC_VALIDATOR_V1
@Type:          Guardian
"""
```

Requirements:
- Parse `.ankhrc` (determine format first — TOML? JSON? INI? Custom?)
- For each declared path, verify it exists relative to repo root
- Output: list of valid paths, broken paths, and suggested fixes
- Exit code 0 if all paths valid, 1 if any broken
- Handle the case where `.ankhrc` doesn't exist (exit with informative message)

### TODO 7.2: Assess Session Extractor Feasibility

For the session_extractor.py TODO:
1. Check if `github-copilot-chat-log` exists at repo root (the migration plan references it as a dependency)
2. Determine what format Copilot chat logs are in
3. Write a feasibility assessment in the output document — is this buildable or did the dependency never materialize?

### TODO 7.3: Update Migration Plan

Write `codex/mailbox/MIGRATION_PLAN_STATUS.md` containing:
1. TODO completion status for each item in STAGE_1_MIGRATION_PLAN.md
2. The ankhrc_validator.py (or report that .ankhrc doesn't exist yet)
3. Session extractor feasibility assessment
4. Any other unresolved items discovered while reading the full migration plan

**Output:** `scripts/ankhrc_validator.py` (if .ankhrc exists), `codex/mailbox/MIGRATION_PLAN_STATUS.md`

---

## Execution Protocol

### Phase Dependencies

```
Phase 1 (Skills) ──────────────────────────────────────── → standalone
Phase 2 (Mailbox) ─────────────────────────────────────── → standalone (but Phase 1 feeds skill awareness)
Phase 3 (Scripts) ─────────────────────────────────────── → standalone
Phase 4 (Tracked .pyc) ── depends on Phase 1 skill list → sequential after Phase 1
Phase 5 (Root Files) ──────────────────────────────────── → standalone
Phase 6 (Forge) ───────────────────────────────────────── → standalone
Phase 7 (Migration) ── depends on Phases 3, 5 for cross-refs → sequential after Phase 3
```

Recommended execution order: **1 → 4 → 2 → 3 → 5 → 6 → 7**

### Output Summary

Upon completion, the following files should exist:

| File | Phase |
|------|-------|
| `codex/mailbox/SKILL_CONSOLIDATION_PROPOSAL.md` | 1 |
| `codex/mailbox/TRACKED_ARTIFACT_CLEANUP.md` | 4 |
| `codex/mailbox/MAILBOX_ROTATION_POLICY.md` | 2 |
| `scripts/mailbox_rotation.py` | 2 |
| `codex/mailbox/MAILBOX_CURRENT_STATE.md` (updated) | 2 |
| `codex/mailbox/SCRIPTS_VARIANT_TRIAGE.md` | 3 |
| `codex/mailbox/ROOT_ARCHAEOLOGY_REPORT.md` | 5 |
| `codex/mailbox/FORGE_DEDUP_AUDIT.md` | 6 |
| `scripts/ankhrc_validator.py` (if .ankhrc exists) | 7 |
| `codex/mailbox/MIGRATION_PLAN_STATUS.md` | 7 |

### Quality Gate

After all phases, write a summary to `codex/mailbox/CODEBASE_TEMPER_SUMMARY.md`:
- Phase-by-phase completion status (DONE / PARTIAL / BLOCKED)
- Total boon earned
- Total proposals generated (count of actionable items for the user)
- Any blocked items requiring user input
- Cross-references discovered between zones (e.g., a root stale file that's referenced from a script, a skill that depends on a mailbox file)

### Reasoning Expectations

This chore is designed for GPT-5.4 with xhigh reasoning and 1M context. You are expected to:

1. **Ingest broadly** — read ALL 27 SKILL.md files, not just the 9 known classifications
2. **Cross-reference deeply** — when you find a redirect in skills, check if the target exists in both `.codex/skills/` AND `.claude/skills/`
3. **Produce structured output** — JSON where structured, Markdown where narrative, tables where comparative
4. **Respect governance absolutely** — every proposal is a proposal. You do NOT execute filesystem-destructive operations.
5. **Show your work** — visible reasoning in each output document. If a classification is uncertain, say so with evidence.
6. **One clarification max** — if a phase is ambiguous, write ONE clarification request, then proceed with your best interpretation

---

*This chore was generated by Claude (steward) based on live codebase analysis on 2026-03-09. All file counts, paths, and classifications verified against `git ls-files` and directory scans.*
