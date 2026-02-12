# Level 2 Digest — 2026-02-11T02-39-10

## mas_mcp
**DOMAIN AUDIT: mas_mcp/** (2026-02-11)

**VERDICT: STRUCTURAL FLAG — venv artifacts polluting audit scope.**

---

[FLAG] mas_mcp\.venv-py314-parked\ — Parked/backup venv should be excluded from nightly crawler; vendor code noise

---

**ANALYSIS:**
- All `.venv-py314-parked\Lib\site-packages\*` files are third-party dependencies (adodbapi, annotated_types, anyio, etc.) — standard, unmodified vendor code
- Directory naming `.venv-py314-parked` signals intentional backup/archival status (not active environment)
- These should **not appear in nightly audits** — configure crawler to skip `\.venv*` and `\.pytest_cache` entirely

**ACTION:** Add venv glob to crawler exclusion list; no individual files require review.

---

## dumpster-dive
**OVERNIGHT AUDIT: dumpster-dive/ Domain**

---

[PROMOTE] `dumpster-dive\archive\deep-research\Gemini_CLI_Preview_Win11_Bun_vscode_insiders_deep_research_IMPLEMENTATION.md` — Compressed actionable extract; ready-to-use MCP/CLI patterns for current stack.

[FLAG] `dumpster-dive\archive\health_reports_2026-01\` (entire directory) — Stale monitoring artifacts (40+ days old); no active health monitoring since Jan-02. Archive or delete.

[FLAG] `dumpster-dive\archive\deep-research\Bun_Native_CDP_Playwright_Win11_25_2026.md` — Incomplete research stub (29L); unclear conclusion. Orphaned or unfinished?

---

**Summary:**
- **1 PROMOTE**: Implementation extract (actionable)
- **2 FLAG**: Stale health reports + orphaned research stub
- **Remainder SKIPPED**: Intentional backups/archives (2025-12-30 and 2026-01 sessions) doing their job

---

## scripts
**OVERNIGHT AUDIT REPORT — scripts/ domain**

---

FLAG `scripts\.deprecated\` — Comprehensive mcp_legacy deprecation (12-37d stale) with fresh .meta.json refresh (5d) suggests stale indexing without cleanup decision.

FLAG `scripts\.deprecated\mcp_legacy\` — 15+ files marked deprecated; .meta.json sidecars regenerated 5d ago but source code 12-37d old. Recommend deprecation audit (preserve? archive? discard?).

PROMOTE `scripts\api_pool.ps1` — Fresh env-var pooling pattern (1d old, 128L), supports API token management via envelope. Check integration with `api_pool_persist_user_env.ps1` below.

PROMOTE `scripts\api_pool_persist_user_env.ps1` — Paired complement (1d old, 119L) for persisting pool env vars to Windows User scope. New env-binding strategy emerging; worth cross-reference with IDE/MCP tooling.

---

**Narrative:** The deprecated folder is a graveyard (expected); the real signal is the **fresh API pool scripts (1d)** paired together for credential envelope management. This is active, recent work. Recommend validating integration with existing credential/auth infrastructure.

---

## codex
**CODEX DOMAIN ARCHAEOLOGY — 2026-02-11 OVERNIGHT DIGEST**

---

**PROMOTE:**

| File | Reason |
|------|--------|
| codex\codex-session-logs\archive\*_structured.json + _resume.md + _pretty.md pattern | Systematic session archival infrastructure: automated compression/summarization applied to raw logs. Worth documenting pattern. |
| codex\codex-session-logs\archive\SESSION_TRAIL_00001.md | Session consolidation metadata; demonstrates tier-3 tracking of session closure and scope resolution. |
| codex\mailbox\ACTUAL-WORKING-HANDOFFS\* (5 files) | Active agent coordination protocol: clear from/to/priority/status semantics. Real operational handoff pattern. |
| codex\codex-session-logs\archive\The-Iron-Maiden.md.voicepack.json | Narrative-to-voicepack schema conversion; blessing/canonicalization pattern for creative lore work. |

---

**FLAG:**

| File | Issue |
|------|-------|
| codex\codex-session-logs\archive\The-Iron-Maiden-(SSOT)-Copyright-Savant.md + .refined-pre.md | Duplicate files (identical content, 0d age, unclear naming). Refinement workflow unclear—keep or archive one? |
| codex\codex-session-logs\archive\*_structured.txt (2 files: default-session-code-gemini.py_transcript.txt_structured.txt, default-session-code-gemini.json_structured.txt) | Both 2L or empty. Failed artifact generation or incomplete pipeline? Recommend audit. |

---

**SKIPS:** 8-day-old creative artifacts (intentional). Complete session log variants (expected derived formats). MCP validation (expected tier-3 doc).

**DOMAIN SUMMARY:** Codex domain shows **active session archival + active handoff protocol**. The structured logging pattern (original → compressed/pretty/resume/structured variants) is new infrastructure worth preserving. Two minor issues: duplicate Iron Maiden files and two hollow _structured.txt artifacts. Recommend cleanup.

---

## artifacts
# ARTIFACTS DOMAIN SCAN — 2026-02-11 02:40 UTC

**FINDINGS:**

[PROMOTE] artifacts\claude-code.cli.2.1.38.frozen.2026-02-10T15-28-36.cli.js — Frozen CLI reference (tier:1), version-locked executable snapshot

[PROMOTE] artifacts\hf_mcp_service_registry.generated.py — Source generator for HF MCP registries; 6 JSON snapshots redundant without this logic

[PROMOTE] artifacts\copilot-cli.changelog.2026-02-10T15-52-07.md — Documents Claude Opus 4.6 Fast support in v0.0.406; actionable governance change

[FLAG] artifacts\hf_mcp_service_registry.generated.*.json (7 files, 1d) — Proliferation: 6 identical-schema snapshots from 2026-02-09 18:29–19:24. Keep latest only, archive rest

[FLAG] artifacts\hf_mcp_tools_*.json (8 files, 1d) — Schema version drift (v1→v2 mid-run 2026-02-09 19:36+). Consolidate to canonical version, document migration

[FLAG] artifacts\mcp_run_audit_2026-01-29T*.json (7 files, 12d) + (3 files, 37d) — Stale audit snapshots; 3 show null outputs (failed runs). Archive to dumpster-dive/archive/

[FLAG] artifacts\mcp_run_curriculum_2026-01-05T*.json (3 files, 37d) — Stale curriculum runs (37d). Archive; no refresh signal detected

---

**SUMMARY:** Domain shows **active capture** of CLI/tooling metadata (fresh 0d), but **snapshot proliferation** at 1d and **failed/stale audit cycles** at 12d–37d. Recommend consolidation of HF registry artifacts and archival of failed MCP audit runs.

---

## docs
# OVERNIGHT ARCHAEOLOGICAL REPORT: docs/

**SCAN TIMESTAMP:** 2026-02-11T02:40:35Z  
**DOMAIN:** docs/ (tier-3, documentation)  
**PRIOR DIGEST:** Flagged drift analysis + implementation extractsin dumpster-dive  

---

## FINDINGS

**PROMOTE — New Signal:**
- **docs\CLAUDE_CODE_REGISTRATION_VERIFICATION_PROOF.md** — Fresh (0d) verification artifact; signals successful MCP registration validation cycle
- **docs\ops\API_POOL.md** — Fresh ops doc (3d); governance pattern for stable secrets across IDE updates
- **docs\design\TECHNIQUE_HYBRIDIZATION.md** — Active design doc (7d); interdisciplinary hybridization pattern (Disco Elysium cross-reference)

**FLAG — Staleness Signals:**
- **docs\MILF_TRINITY_CHROMATIC_LINEAGE.md** — 43d old; marked "chromatic archaeology" but age suggests content freeze, verify against current MILF canon
- **docs\architecture\topology_map.md** + **topology_summary.md** — Both 40d old; generated 2026-01-01; MERMAID graphs may be stale, node/edge counts unvalidated
- **docs\CHTHONIC_ARCHIVE_WORLD_TPEF.md** — 85d ancient (oldest in domain); "macro-prompt world" framing outdated per current SSOT hierarchy; consider archival
- **docs\handoffs\GEMINI_HANDOFF_PHASE_11_5.md** — 63d old; post-session artifact, likely orphaned; verify if still referenced

**SKIP:** Framework docs (ANKH/ANKHOLOGY/README at 42-44d) stable; MCP templates (14d) aligned; lore tier frozen per design.

---

## ACTIONABLE SIGNAL

**One file needs immediate audit:** `topology_summary.md` — Claims "10110 nodes, 9165 edges" as of 2026-01-01. No recent validation. If SSOT reorganization occurred (evident from fresh copilot-instructions.md), graph is likely corrupted.

---

## bun-playwright-poc
**DOMAIN CLEAN**

The `bun-playwright-poc/` domain shows coherent structure with no new findings or status changes since prior digest (2026-02-11):

- **Blessed tier-1 code** (bun-launcher.ts, chthonic-crawler.ts, example-buncdp.ts, etc.): All age 12d, bearing decorator headers, stable
- **Governance anchor** (BUN_PLAYWRIGHT_2026.md): Age 12d, ANKH-marked, already promoted
- **Real crawler output** (github-crawl-output/knowledge-graph.json): Age 12d, 3 nodes / 15 edges, functional
- **Historical artifacts** (age 18d test logs, PNGs, old crawl output): Inert, expected
- **Configuration layer** (package.json, bun.lock, .vscode/tasks.json): Stable, no drift signals

**Verdict:** No promotions, no flags. Domain maintains structural integrity. All prior discoveries remain valid anchors.

---

## .
# OVERNIGHT ARCHAEOLOGIST REPORT (2026-02-11)

## PROMOTIONS (Gold-Tier Signals)

[PROMOTE] **claude_test.py** — Fresh Bedrock integration test (0d); signals new AWS/ML capability expansion path  
[PROMOTE] **pyproject.toml** — Fresh Python config (1d); critical for environment coherence validation  
[PROMOTE] **package.json** — Recent churn (3d); active frontend/build iteration visible  
[PROMOTE] **bun.lock** — Fresh lockfile (3d); dependency management actively maintained  

---

## FLAGS (Drift / Orphaning Signals)

[FLAG] **broken-refs.json** — Active broken reference list (6d); unresolved documentation debt accumulating  
[FLAG] **build.rs** — Rust subsystem dormant (12d); assess if compilation/Vulkan layer abandoned  
[FLAG] **Cargo.toml** — Rust project config untouched (12d); dormancy indicator  
[FLAG] **get_hash.py** — SSOT hash utility (5d); validate canonical hash algorithm matches current SSOT state  
[FLAG] **purify_ssot.py** — SSOT cleanup script (5d); validate output doesn't corrupt canonical state  
[FLAG] **strip_ssot.py, strip_post_ssot.py** — SSOT transformation cluster (5d); validate mutual coherence and prevent data loss  
[FLAG] **bunfig.toml** — Bun config stale (16d); Playwright test exclusion rules may diverge from actual setup  
[FLAG] **book.toml** — mdBook config stale (14d); no active publishing signal detected  

---

## CONTEXT

**High-signal cluster**: SSOT governance scripts (get_hash, purify, strip variants) form a transformation pipeline. If any have diverged, cascade errors possible. Recommend validation pass.

**Rust subsystem**: build.rs + Cargo.toml both 12d stale. If Vulkan renderer is inactive, consider marking as archival.

**Frontend**: Fresh churn in bun.lock + package.json (both 3d) contradicts stale bunfig.toml (16d). Config may need refresh.

**Documentation**: broken-refs.json is active. Systematically resolve or audit why links persist unresolved.

---

## meta-ide
# meta-ide/ Domain: Overnight Archaeology Digest

[PROMOTE] meta-ide\copilot-sdk\overnight-archaeology.ts — New gold extractor (Two-Loop SCAVENGE+REFINE pattern, 0d)

[PROMOTE] meta-ide\copilot-sdk\overnight-intelligence.ts — Fresh daemon implementing scavenger loop, 0d

[PROMOTE] meta-ide\copilot-sdk\oracle.ts — Pure reasoning companion; part of fresh SDK trio, 0d

[PROMOTE] meta-ide\copilot-sdk\companion.ts — CLI delegate via SDK; fresh architectural layer, 0d

[PROMOTE] meta-ide\copilot-sdk\harness.ts — Bun sidecar for VS Code; fresh integration pattern, 0d

[PROMOTE] meta-ide\copilot-sdk\shims\ (node-sqlite.ts, preload.ts, sqlite.js) — Node-to-Bun bridge infrastructure, 0d

[PROMOTE] meta-ide\copilot-sdk\self-dialogue.ts — Fresh Claude-Claude reasoning capture, 0d

[PROMOTE] meta-ide\copilot-sdk\self-dialogue-response.md — Architecture snapshot documenting IDE decision logic, 0d

[FLAG] meta-ide\copilot-cli-0.0.406\ — Entire directory 14717d stale; copilot-sdk/ has fresher definitions. Potential orphaned reference copy.

---

**Summary:** copilot-sdk/ is live (overnight daemon infrastructure + IDE integration patterns established). Investigate whether copilot-cli-0.0.406/ is still needed or can be archived to dumpster-dive.

---

## claude
# Claude Domain: Overnight Archaeology Report

[PROMOTE] claude/mailbox/ARCHAEOLOGY_DIGEST_2026_02_11.md — Fresh daily digest (0d); surfaces current findings. Read first.

[PROMOTE] claude/mailbox/CLAUDE_CODE_HIERARCHICAL_RESEARCH_2026_02_09.md — Active research on Claude-code parity (agents, hooks, MCP); fresh direction signal.

[PROMOTE] claude/mailbox/SESSION_HANDOFF_2026_02_10_CLAUDE_CODE_OPUS_SETUP.md — Latest handoff; Claude-code posture + cost decisions (1d, priority:high).

[PROMOTE] claude/mailbox/CLAUDE_TASK_SESSION_SYNC_2026_02_09.md — Active session-sync challenge task; operational continuity signal.

[PROMOTE] claude/mailbox/SESSION_SYNC_PACKET_2026_02_09.md — Operational checklist; machine-readable runbook for system execution (1d).

[PROMOTE] claude/mailbox/MAILBOX_CURRENT_STATE.md — Fresh mailbox snapshot (1d); current active files index.

[PROMOTE] claude/mailbox/mailbox_manifest.json — Schema v2 manifest (1d); machine-readable state.

[PROMOTE] claude/mailbox/skill_audit_claude_2026-02-09T22-01-52Z.json — Latest skill audit data (1d); reflects current Claude skill state.

[PROMOTE] claude/mailbox/TETRAGRAMMATON_PACKET.md — Governance packet; recently updated (1d touch), active.

[PROMOTE] claude/WET_PAPER_TO_GOLD_METHODOLOGY.md — Canonical methodology; updated 1d ago (2026-02-10). Gold-tier preservation signal.

[FLAG] claude/mailbox/KISS_PARITY_BRIEF_2026_02_06.md — Parity guidance stale (4d); likely superseded by Feb 9-10 research.

[FLAG] claude/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md — Parity report (4d); recommend refresh against Feb 9-10 audit.

[FLAG] claude/mailbox/skills_parity_map_2026_02_06.json — Parity snapshot (4d); data may drift; check against latest audit.

[FLAG] claude/mailbox/MAILBOX_CURRENT_STATE_2026_02_06.md — Obsolete state snapshot (5d); superseded by Feb 9-10 current state.

---

## extensions
**EXTENSIONS DOMAIN AUDIT — 2026-02-11**

[PROMOTE] extensions\chthonic-archive\src\acp\* + extensions\chthonic-archive\src\sdk\* — Both ACP and SDK connections present, both 0d fresh; clarify migration/parallel status

[FLAG] extensions\chthonic-statusbar\ — Lockfile/config 32-33d stale; extension.ts/hedonisticValidation.ts only 16-17d. Dependency drift detected

[FLAG] extensions\chthonic-mandala\README.md — Age 12d with UPPERCASE semantic signals; docs aging relative to 0d code refresh

[PROMOTE] extensions\chthonic-archive\themes\* + extensions\chthonic-mandala\themes\* — Fresh theme configs (0d) align with Flesh & Earth / ROGBIV palette spec; validate against current color mandate

---

**Summary:** Chthonic-archive showing healthy 0d refresh across code/config. Chthonic-statusbar lagging (32-33d drift). ACP/SDK bifurcation needs status clarification.

---

## claude-codex-gemini
# OVERNIGHT ARCHAEOLOGIST REPORT: claude-codex-gemini/ domain

**Scan Date:** 2026-02-11T02:42:40Z  
**Files Analyzed:** 22 | **Prior Night Drift:** 2 items noted  
**Verdict:** **DOMAIN HAS STALENESS + GOVERNANCE DRIFT**

---

## FINDINGS

**[FLAG]** `triadic-session-context\SSOT_STRUCTURAL_INDEX.json` — Age 12d; auto-generated index stale; regenerate via `ssot_outline_extractor.ps1 -UpdateIndex` required

**[FLAG]** `triadic-session-context\SSOT_NAVIGATION_INDEX.md` — Age 12d; should auto-update after SSOT edits; check if regeneration pipeline running

**[FLAG]** `triadic-session-context\SESSION_CACHE_STRUCTURED.md` — Age 9d for working memory; stale for active cross-session cache; needs refresh/audit

**[FLAG]** `triadic-session-context\SESSION_PROTOCOL.md` — Age 14d; MASP core governance doc; verify if integrated into main SSOT or needs maintenance cycle

**[FLAG]** `triadic-session-context\Python_Metabolic_Standard_v3_Transition.md` — Age 7d; PMS-v3 is live in instructions; confirm this artifact archived or consolidated

**[FLAG]** `triadic-session-context\Accurate_PEP_Standards_Win11_Uv_Python.md` — Age 10d; likely superseded by PMS-v3 codification; archive or cross-reference

**[FLAG]** `triadic-session-context\OpenAI_Codex_Win11_Keyring_Auth_Resolution.md` — Age 10d; troubleshooting guide; verify integrated into agent setup or mark stale

**[FLAG]** `triadic-session-context\BUN_SEGFAULT_2026_02_01.md` — Age 7d; incident report from Feb 1; status unclear (mitigated or open?)

**[FLAG]** `triadic-session-context\claude-session-help.md` — Age 12d; orphaned conversation fragment; should be consolidated into structured session log or deleted

**[FLAG]** `triadic-session-context\gemini-cli-session-fix-too-large.md` — Age 7d; incomplete/malformed doc (starts mid-snippet); unclear purpose; cleanup needed

---

## PATTERN DIAGNOSIS

The **triadic-session-context/** subdomain contains **research, analysis, and session artifacts** that are NOT being actively maintained:

- **Stale indices**: SSOT_STRUCTURAL_INDEX.json + SSOT_NAVIGATION_INDEX.md (both 12d) suggest the auto-update pipeline is not running.
- **Orphaned docs**: conversation fragments (claude-session-help.md, gemini-cli-session-fix-too-large.md) should be consolidated per **Lineage B consolidation strategy**.
- **Governance integration gaps**: PMS-v3, Keyring Auth, and SESSION_PROTOCOL need explicit archival or integration signals.

---

## RECOMMENDATION

1. **IMMEDIATE**: Run `ssot_outline_extractor.ps1 -UpdateIndex` to refresh structural index.
2. **TODAY**: Audit SSOT_NAVIGATION_INDEX.md and SESSION_CACHE_STRUCTURED.md for update recency.
3. **LINEAGE B TASK**: Consolidate orphaned fragments into SESSION_CACHE or SSOTIFIED_SESSION_LOG per intake checklist.
4. **GOVERNANCE**: Mark PMS-v3 and Keyring Auth docs with explicit "ARCHIVED" or "INTEGRATED" status in headers.

---

## src
**src/ DOMAIN ANALYSIS** (2026-02-11)

---

## Judgment

**FLAG** src\README.md — Documentation drift risk: 24d age (4d older than peers), UPPERCASE signals, Tier 3 status; reconcile against current architecture snapshot.

---

## Rationale

- **All .rs files (27 files)**: Correctly blessed, consistently structured, 12d age (baseline for domain), no staleness or orphaning signals. **SKIP**.
- **types.rs (16d)**: Slightly older than peers but within tolerance; architectural core status justified. **SKIP**.
- **README.md (24d)**: Oldest file in domain by 12 days; documentation risk surface-worthy. UPPERCASE signals suggest it may lag current SSOT state. Worth one-pass coherence audit.

---

**Result**: 1 FLAG, rest SKIP. Recommend surface audit of README context against `.github/copilot-instructions.md` (fresh, 0d) to catch any docstring drift.

---

## chthonic-vscode-extension
**DOMAIN ANALYSIS: chthonic-vscode-extension**

[PROMOTE] package.json — Fresh (age:0d). Verify what changed today; signals active intent.

[PROMOTE] src/extension.ts — Active code (age:13d). Recent development momentum; reference for pattern validation.

[FLAG] bun.lock — Stale (age:41d). Lockfile unrefreshed; dependencies may be outdated. Recommend `bun install` sync.

[FLAG] Documentation cluster (COPILOT_API.md, DEBUG_GUIDE.md, INSTALL.md, README.md, REVERSE_ENGINEERING.md) — All age:41d while extension.ts changed 13d ago. Documentation debt signal; docs may be out-of-sync with code.

---

## ankh_atlas
**DOMAIN SCAN: ankh_atlas/**

[FLAG] ankh_atlas\pyproject.toml — placeholder description "Add your description here" unfilled after 42d; config drift signal

[PROMOTE] ankh_atlas\ module (detectors.py, index.py, models.py, scan.py, __main__.py, main.py) — synchronized 5d refresh across all tier:1 code; suggests recent activation; worth audit for integration readiness

---

**Observation**: ankh_atlas shows **temporal desynchronization** — code refreshed 5 days ago (all .py files), but project metadata (pyproject.toml, README.md) frozen at 42d creation. README is present and documented, but pyproject.toml never initialized properly. Suggests: recently revived dormant module. Recommend surface audit of `__main__.py` (96L, entry point) and `detectors.py` (104L, likely core logic) for current operational state.

---

## data
# DATA DOMAIN AUDIT (2026-02-11)

[FLAG] data\curriculum_core_v1.json — Stale v1.0.0 (37d), tied to old epistemograph db extraction (2026-01-04); orphan signal

[FLAG] data\graphs\dependency_graph.json — Naming conflict: three versions (VIOLET/12d, GOLD-enhanced/8d, BLUE-production/40d); ownership unclear

[FLAG] data\graphs\dependency_graph_production.json — Stale (40d); newer "enhanced" version (8d) exists; authoritative source unknown

[FLAG] data\graphs\topology_graph.json — Massive frozen snapshot (10110 nodes, 40d); untouched since 2026-01-01; verify intentional stasis or refresh needed

[FLAG] data\state\.dcrp_evolution.json — Time series frozen at Jan 1 (40d); no refresh signal; baseline or orphan?

[FLAG] data\state\.dcrp_state.json — Sparse state tracker (41L, 20d); verify active usage or archive candidate

---

**DOMAIN SIGNAL**: Data/graphs layer shows **multi-version drift**. Three dependency graphs with conflicting spectral frequencies and ages suggest stale promotion cycle or failed consolidation. Recommend: audit ownership (which graph is authoritative?), then consolidate or archive non-canonical versions.

---

## pr2_review
# OVERNIGHT ARCHAEOLOGY: pr2_review/ DOMAIN

**Digest:** Low-volume domain, mostly stale governance docs. One fresh utility script surfaced. Three files show drift/orphaning signals.

---

[PROMOTE] pr2_review\scripts\ssot_hash.py — Recent (5d), tier-1 code; active SSOT governance infrastructure utility

[FLAG] pr2_review\CHERRY_PICK_PLAN.md — Status "PENDING USER APPROVAL" (44d stale); decision gate abandoned

[FLAG] pr2_review\SNOW_POWDERED_WHITE_MYTHOLOGY_DRAFT.md — Draft status (6d); completion/archival decision pending

[FLAG] pr2_review\validation_alabaster_voyde.txt — Orphan validation artifact (16d); paired to draft, staleness unknown

---

**Summary:**  
- **Gold Found**: `ssot_hash.py` (fresh, governed)  
- **Decay Detected**: 3 files in limbo state (pending approval, draft, orphan validation)  
- **Stable**: `ankh.md`, `ANKH_README.md`, `COMPARISON_ANALYSIS.md` (reference material, no drift)

**Recommendation**: Triage the 3 flagged files—either complete them, archive them, or explicitly close the decision gate.

---

## error-classifier
**DOMAIN CLEAN**

The error-classifier subsystem is stable and coherent. All six files (database.ts, ingest.ts, memory.ts, research.ts, package.json, bun.lock) form a unified SQLite-backed ingestion pipeline with appropriate tier assignments and no signs of drift, orphaning, or staleness. All 12d unchanged; this indicates maturity, not decay. No files meet PROMOTE or FLAG thresholds.

---

## assets
**ASSETS DOMAIN AUDIT** (2026-02-11)

[PROMOTE] assets\data.json — Fresh game engine structure (12d), ASC-NATIVE-CHAIN-RPG canonical—audit version lock
[PROMOTE] assets\save_state.json — Fresh game state snapshot (12d), mirrors data.json schema—drift risk if diverged

Remaining files clean (concept art frozen 43d, tier reference stable 63d).

---

## logs
## LOGS DOMAIN AUDIT — 2026-02-11

PROMOTE logs\sessions\session_2025-12-31_0746_vscode-extension-debug.md — Fresh session transcript (3d) with active Copilot CLI coordination signals; shows vscode-extension debug workflow patterns

FLAG logs\session_20251207_043539.jsonl — Orphaned service log (65d old, 2L minimal); no companion metadata, stale watcher events

FLAG logs\session_20251207_043745.jsonl — Orphaned service log (65d old); paired with 043539/043803 but unclear archival/retention intent

FLAG logs\session_20251207_043803.jsonl — Orphaned service log (65d old, 2L minimal); orphaned trio, stale watcher startup signal

---

**SUMMARY**: Fresh session transcript (3d) is gold—shows live agent interaction. Ancient trio (65d) are staleness red flags—determine if archived or rotted.

---

## dev
**DOMAIN ANALYSIS: dev/**

[FLAG] dev\overnight_refactor_mode.md — 46d stale, references "GPT-5.2" (agent mismatch); drift candidate

[FLAG] dev\copilot-cli\{changelog,LICENSE,README}.md — 0d fresh reference copies; check for duplication against upstream/vendor sources

---

**ASSESSMENT:** Minimal maturity signals. The copilot-cli suite appears newly mirrored (0d); overnight_refactor_mode is orphaned by time and outdated agent nomenclature. Neither set shows active integration into core workflows.

---

## plugins
[PROMOTE] plugins\chthonic-tools\.claude-plugin\plugin.json — Declares plugin identity and "IDE self-heal + mailbox continuity" integration layer. Tier-2 structural anchor, fresh (1d).

[PROMOTE] plugins\chthonic-tools\commands\postman.md — Documents "Response: <topic>" mailbox handoff skeleton command. Implements critical Codex agent coordination pattern, properly tiered (tier 3).

[PROMOTE] plugins\chthonic-tools\commands\selfheal.md — Documents VS Code Insiders self-heal automation (.mcp.json refresh, plugin refresh). Aligns with IDE patching governance (CLAUDE.md); operationally critical, fresh.

---

**Domain verdict**: 3/3 files are **gold-worthy**—they represent a fresh plugin infrastructure layer connecting IDE automation to agent handoff continuity. No drift or staleness detected. These should be surfaced for integration cross-check against `.claude-plugin/` standards in the broader archive.