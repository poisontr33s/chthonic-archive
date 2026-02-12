# Level 2 Digest — 2026-02-11T02-27-22

## mas_mcp
**DOMAIN ASSESSMENT: mas_mcp/**

[FLAG] `.venv-py314-parked/` — Virtual environment sprawl; entire site-packages checked in. Should gitignore or delete.

[FLAG] `.pytest_cache/README.md` — Auto-generated cache artifact; belongs in `.gitignore`, not repo.

---

**Analysis:**
- All files in `.venv-py314-parked/Lib/site-packages/` are third-party dependencies (adodbapi, anyio, annotated_types, etc.)
- Virtual environments are regenerable; this is dead weight in version control.
- The `.pytest_cache` is a pytest auto-generated directory.
- **No PROMOTE cases**: These are dependencies, not source logic worth surfacing.

**Recommendation:** Remove `.venv-py314-parked/` entirely and ensure both `.venv*` and `.pytest_cache/` are in `.gitignore`. If archival intent exists, document it separately (e.g., `docs/archived-env-notes.md`), not in the repo tree.

---

## dumpster-dive
[PROMOTE] dumpster-dive\archive\deep-research\conversation_about_win11_pwsh_standard_uv_shebang.md — Contains drift analysis (score 4.84) and vocabulary coherence signals worth surface audit

[PROMOTE] dumpster-dive\archive\deep-research\Gemini_CLI_Preview_Win11_Bun_vscode_insiders_deep_research_IMPLEMENTATION.md — Compressed actionable implementation extract; reference for MCP/CLI patterns

[FLAG] dumpster-dive\archive\health_reports_2026-01\ — 24 timestamped health snapshots (Jan 1-9) with no consolidation; stale monitoring artifacts

[FLAG] dumpster-dive\archive\instructions-backup-20251230\ — Instruction backups from Dec 30 (46d old); unclear if superseded or active reference; needs consolidation audit

[FLAG] dumpster-dive\archive\sessions_2026-01\AUTONOMOUS_SESSION_3_*.md — Five variants ("COMPLETE", "DEEP_DIVE_SYNTHESIS", "EXECUTION_COMPLETE") of same session; fragmentation/versioning smell detected

---

## scripts
**OVERNIGHT ARCHAEOLOGY REPORT: scripts/**

[FLAG] scripts\.deprecated\ide-detection.ps1 — Deprecated but retains active-sounding name (ide-detection diagnostic)

[FLAG] scripts\.deprecated\launch-claude-ide.ps1 — References Bun 1.3.6 segfault workaround; version stale vs. current 1.3.5

[FLAG] scripts\.deprecated\mcp_legacy\INTEGRATION_GUIDE.md — Status claims "READY FOR INTEGRATION" but housed in deprecated directory (orphaned)

[FLAG] scripts\.deprecated\mcp_legacy\OPTION_A_STATUS.md — Status claims "AWAITING USER VALIDATION" but housed in deprecated (orphaned validation state)

[FLAG] scripts\.deprecated\run_mcp_artisan_server.ps1 — Wrapper launching deprecated MCP server; dead entry point

---

**ASSESSMENT**: 5 orphaned status files + wrappers in deprecated domain. Recommend archival sweep of README markers claiming active integration status.

---

## codex
# CODEX DOMAIN OVERNIGHT ARCHAEOLOGY

**PROMOTES:**

[PROMOTE] codex\mailbox\ACTUAL-WORKING-HANDOFFS\* — Active agent coordination memos (5 files, 0d). Clear handoff pattern signals.
[PROMOTE] codex\codex-session-logs\archive\SESSION_TRAIL_00001.md — Session consolidation metadata, tier-3 docs, fresh (0d).

**FLAGS:**

[FLAG] codex\codex-session-logs\archive\* (_pretty.md, _resume.md, _structured.json/txt variants) — Over-derived pipeline (18+ files, 0d). Unclear retention intent; potential duplication smell.
[FLAG] codex\artifacts\* — Creative/lore tier-3 assets aging 8d without active signals. Consider archival or refresh.
[FLAG] codex\codex-session-logs\archive\The-Iron-Maiden*.md — Dual markdown files (original + voicepack pair). Unclear separation; potential naming drift.

---

**SUMMARY:**  
Handoff coordination is live and clean. Session-log archive shows **procedural overgrowth**: many derived formats suggest a processing pipeline without clear cleanup. Artifacts are stale but harmless (low priority).

---

## artifacts
[PROMOTE] artifacts\hf_mcp_service_registry.generated.py — Source generator for HF MCP registry JSONs; shows automation intent

[FLAG] artifacts\hf_discovery_spaces_2026-02-09T18-13-*.json|md — Duplicated pairs (18:13:17Z, 18:13:53Z); iteration waste, same query

[FLAG] artifacts\hf_mcp_service_registry.generated.2026-02-09T*.registry.json — Six sequential versions (18:29–19:24); no consolidation, drift signal

[FLAG] artifacts\hf_mcp_tools_2026-02-09T19-3[467]*.json — Schema version instability (1→2); 6 variants in 8 minutes, unresolved iteration

[FLAG] artifacts\mcp_run_audit_2026-01-29T18-3[156]*.json — Mix of null outputs (failures) & real outputs; debugging residue, incomplete triage

**Recommendation:** Consolidate HF discovery artifacts to single canonical JSONs. Archive iteration variants to `dumpster-dive/`. Keep `generated.py` as source of truth reference.

---

## docs
**PROMOTE**

- `docs\design\genre-extraction.md` — Novel MILF-Core extraction lens worth agents' attention
- `docs\design\TECHNIQUE_HYBRIDIZATION.md` — Disco Elysium hybrid technique discovery (active, 7d fresh)
- `docs\ops\API_POOL.md` — New ops guidance for stable local API management (3d fresh)

**FLAG**

- `docs\COMPLETION_SUMMARY_TOOL_CONSOLIDATION.md` — Stale session summary (tool consolidation completed weeks prior)
- `docs\frameworks\SESSION_3_ORCHESTRATION_QUICKREF.md` — Orphaned session-specific reference (40d old, no current context)
- `docs\frameworks\SESSION_3_TYPESCRIPT_QUICKREF.md` — Orphaned session-specific reference (40d old, no current context)
- `docs\handoffs\GEMINI_HANDOFF_PHASE_11_5.md` — Ancient handoff (63d old, pre-reorg lifecycle)

---

## bun-playwright-poc
[PROMOTE] BUN_PLAYWRIGHT_2026.md — Governance document; surfaces 2026 automation paradigm decisions (age 12d).

[PROMOTE] example-buncdp.ts — CDP pattern example; demonstrates blessed implementation pattern (age 12d).

[PROMOTE] git-crawl-demo.ts — Live crawler integration demo; shows actual usage beyond tests (age 12d).

[PROMOTE] github-crawl-output/knowledge-graph.json — Real crawler output; demonstrates successful data structure (3 nodes, 15 edges, age 11d).

[FLAG] crawl-output/CRAWL_SUMMARY.md — Orphaned dry-run output; pages/edges both 0, stale (age 18d).

[FLAG] crawl-output/knowledge-graph.json — Orphaned empty graph; dry-run artifact, no live data (age 18d).

[FLAG] FINAL_RESULT.txt — Incomplete truncation; contains only "[STEP 4] Starting..." with no completion (age 18d).

---

## .
# OVERNIGHT DOMAIN TRIAGE (./)

[FLAG] BRIDGE_COMPLETE_SUMMARY.md — completion artifact (13d old), may need refresh validation  
[FLAG] CHTHONIC_V3_META_CLI_COMPLETE.md — stale completion summary, verify active status  
[FLAG] CLAUDE_CODE_BRIDGE_ARCHITECTURE.md — aged bridge doc (13d), verify still canonical  
[FLAG] CLAUDE_CODE_BRIDGE_INTEGRATION.md — aged integration guide (13d), drift risk  
[FLAG] captured_viii_ix.txt — extracted snapshot, probable duplicate of SSOT content  
[FLAG] check_jump.txt — extracted snapshot, probable duplicate of governance content  
[FLAG] claudine_check.txt — extracted snapshot, probable duplicate of protocol content  
[FLAG] edits_context_proto.txt — working artifact, should be in session cache, not repo  
[FLAG] edits_context_ssot.txt — working artifact, should be in session cache, not repo  
[FLAG] pre_xiv_check.txt — extracted snapshot, probable duplicate of protocol content  
[FLAG] broken-refs.json — stale (6d), verify still accurate & actionable  
[FLAG] cargo_test.json — stale test output (11d), cleanup candidate  
[FLAG] meta_cli_test.json — stale test output (11d), cleanup candidate  
[FLAG] server_debug.json — stale debug output (11d), cleanup candidate  
[FLAG] status_test.json — stale test output (11d), cleanup candidate  

[PROMOTE] pathstofiles.md — canonical file index (0d fresh), navigation critical  
[PROMOTE] get_hash.py — SSOT verification foundational utility (5d active)  
[PROMOTE] purify_ssot.py — SSOT governance tooling (5d active)  
[PROMOTE] strip_ssot.py — SSOT maintenance utility (5d active)  

**OBSERVATION**: Root domain contains **high-entropy archive debris**. Extracted snapshots (captured_*, check_*, claudine_*, pre_*_check.txt, edits_context_*) suggest mid-operation state. Stale test artifacts (_test.json, _debug.json) should be moved to `dumpster-dive/logs/` or cleaned. Recommend separating operational docs (AGENTS.md, CLAUDE.md, GEMINI.md, PWSH_RULES.md) into `.github/instructions/` and archiving stale completion summaries.

---

## meta-ide
**DOMAIN ANALYSIS: meta-ide/**

---

**PROMOTE** meta-ide/copilot-sdk/overnight-archaeology.ts — Gold extraction refinery; loop 1 (scavenge) mapped. Architectural pattern.

**PROMOTE** meta-ide/copilot-sdk/overnight-intelligence.ts — Daemon-driven intelligence layer; complements archaeology. Decision: detached execution.

**PROMOTE** meta-ide/copilot-sdk/shims/node-sqlite.ts — Bun/Node compatibility bridge. Critical for SDK runtime parity.

**PROMOTE** meta-ide/copilot-sdk/bunfig.toml — Preload strategy (shim registration) encoded. Bun-specific governance.

**FLAG** meta-ide/copilot-sdk/self-dialogue-response.md — Single-run artifact (2026-02-11T01:22:53Z). Staleness risk if not periodically refreshed.

**FLAG** meta-ide/copilot-sdk/definitions/oracle.agent.yaml — New oracle agent; no corresponding entry in copilot-cli-0.0.406. Cross-version drift signal.

**FLAG** meta-ide/copilot-sdk/test-*.ts — Six test files with no coordinated harness. Scattered test strategy; needs consolidation.

**FLAG** meta-ide/copilot-cli-0.0.406/definitions/*.agent.yaml vs. copilot-sdk/definitions/*.agent.yaml — Duplication (code-review, explore, task). Version drift risk.

---

**SUMMARY**: Copilot-cli is frozen reference (skip). Copilot-sdk is active: new archaeology/intelligence logic is gold; shims + bunfig are critical infrastructure. Tests are scattered; oracle definition is orphaned from CLI reference.

---

## claude
[PROMOTE] claude\README.md — Domain anchor with semantic identity structure; foundational orientation.

[PROMOTE] claude\VESPER_PROTOCOL.md — Canonical protocol definition (MILFOLOGICAL tier 2); active status.

[PROMOTE] claude\WET_PAPER_TO_GOLD_METHODOLOGY.md — Freshly updated (1d) canonical methodology; foundational overlay.

[FLAG] claude\mailbox\KISS_PARITY_BRIEF_2026_02_06.md — Claims "from: codex, to: codex" but lives in claude/mailbox; routing ambiguity.

---

## extensions
**DOMAIN ANALYSIS: extensions/**

---

**FLAGS:**

[FLAG] extensions\chthonic-statusbar\ — entire extension stale (16–33d), others 0d; orphaned status
[FLAG] extensions\chthonic-archive\src\acp\ & extensions\chthonic-archive\src\sdk\ — parallel code paths (ACP→SDK transition), likely duplication
[FLAG] extensions\chthonic-archive\icons\mandala.svg + resources\mandala.svg — duplicate SVG, both 32d stale
[FLAG] extensions\chthonic-mandala\icons\mandala.svg + resources\mandala.svg — duplicate SVG, both 32d stale

---

**PROMOTES:**

[PROMOTE] extensions\chthonic-archive\src\sdk\connection.ts — comment signals ACP deprecation; clarify bifurcation
[PROMOTE] extensions\chthonic-statusbar\src\hedonisticValidation.ts — unusual naming + SSOT validation tie; understand intent

---

**SUMMARY:**

Three structural smells:
1. **Staleness**: chthonic-statusbar is orphaned (16–33d while peers are 0d)
2. **Bifurcation**: ACP/SDK parallel paths in chthonic-archive need consolidation or explicit ownership
3. **Duplication**: 4 redundant icon SVGs (favors deletion or canonical choice)

Recommend triage order: (1) Clarify ACP→SDK transition + remove dead branch, (2) unify SVG icon choice, (3) resurrect or archive chthonic-statusbar.

---

## claude-codex-gemini
[PROMOTE] codex52_medium_reasoning_candidate_persona.md — CRC archetype design actively feeding persona/LM work
[PROMOTE] OpenAI_Codex_Win11_Keyring_Auth_Resolution.md — Portable auth troubleshooting pattern; reference-grade
[PROMOTE] Session_20260131_Codex_Onboarding_Summary.md — Triad establishment continuity; valuable decision record
[PROMOTE] TRIAD_DOC_CONSOLIDATION_STRATEGY.md — Active documentation governance guide; feeds SSOT work

[FLAG] Accurate_PEP_Standards_Win11_Uv_Python.md — Redundant with PMS-v3 in SSOT; consolidate or retire
[FLAG] BUN_SEGFAULT_2026_02_01.md — Incident report needs resolution closure or escalation marker
[FLAG] claude-session-help.md — Stale session notes (12d); archive or delete
[FLAG] gemini-cli-session-fix-too-large.md — Orphaned fragment; incomplete; remove or complete
[FLAG] Python_Metabolic_Standard_v3_Transition.md — Superseded by SSOT consolidation; archive
[FLAG] SSOT_STRUCTURAL_INDEX.json — 12 days old; likely desynchronized; run regeneration script
[FLAG] STRATEGIC_PLAN.md — 12 days old; may drift from SSOT edits; validate currency

---

## src
**DOMAIN ANALYSIS: src/**

[FLAG] src\README.md — Documentation age (24d) drifts from code refactoring (12d); likely stale vs Decorator governance

---

**Rationale:**

- ✅ All `.rs` files: Consistent "Decorator's Blessing" headers, clean modular structure (50-121L each), fresh (12-16d), organized deliberately (data/ + render/ domains). No actionable decay.
- ✅ Module boundaries: `mod.rs` files appropriately lean (27-33L), no bloat or orphaning.
- ⚠️ **README.md lags code by 12 days**, suggesting it wasn't updated during the recent governance pass that touched all .rs files. Check if it documents current architecture or is stale ceremony.

---

## chthonic-vscode-extension
[PROMOTE] chthonic-vscode-extension\package.json — FRESH (0d), recently updated, extension metadata current
[PROMOTE] chthonic-vscode-extension\REVERSE_ENGINEERING.md — Documents Copilot Chat API reverse-eng patterns worth preserving
[PROMOTE] chthonic-vscode-extension\src\extension.ts — Active code, 13d old, main extension entry point

[FLAG] chthonic-vscode-extension\bun.lock — 41d old, package.json 0d old; dependency staleness signal
[FLAG] chthonic-vscode-extension\DEBUG_GUIDE.md — Status 2025-12-31, 41d old; risk of diagnostic advice drift
[FLAG] chthonic-vscode-extension\INSTALL.md — 41d old; installation docs prone to rapid obsolescence

---

## ankh_atlas
FLAG ankh_atlas\pyproject.toml — Placeholder description "Add your description here" signals incomplete configuration (42d stale, should reflect actual purpose).

DOMAIN NOTES:
- All `.py` files (detectors, index, models, scan, __main__) are recent (5d), tier-1 operational code with standard headers. Without reading internals, metadata suggests these are active and maintained.
- `README.md` is documented and stable (42d old is normal for reference docs).
- `uv.lock` is as expected (minimal, tier-2 data).

**ACTION NEEDED:** Update `pyproject.toml` description to reflect ANKH Atlas' actual purpose (semantic instrumentation for Chthonic Archive). This is a governance completeness issue, not a code smell.

---

## data
**OVERNIGHT TRIAGE: data/ DOMAIN**

[PROMOTE] data\indices\sid_index.json — Active SID mapping artifact (7d), supports Archive addressability per mandate.

[PROMOTE] data\indices\ankh_index.json — Canonical ANKH index (8d), essential for cross-referencing governance.

[PROMOTE] data\graphs\dependency_graph_enhanced.json — Active variant (8d, GOLD spectral), signals recent development focus.

[FLAG] data\graphs\dependency_graph_production.json — Orphaned production variant (40d), stale vs. enhanced (8d); clarify versioning strategy.

[FLAG] data\curriculum_core_v1.json — Core artifact aging (37d); verify if superseded by newer extraction or requires refresh.

[FLAG] data\state\.dcrp_evolution.json — Historical snapshot (40d, Jan 1); verify if still canonical or archived.

**SUMMARY**: Multiple graph variants + stale "core" curriculum suggest versioning drift. ANKH & SID indices healthy. Recommend: audit production vs. enhanced graph strategy, refresh curriculum if canonical.

---

## pr2_review
**pr2_review Domain: Overnight Triage Report**

[PROMOTE] pr2_review\ankh.md — Foundational ANKH system articulation; semantic carrier patterns worth centralizing

[FLAG] pr2_review\ANKH_README.md — Duplicate ANKH documentation; consolidation candidate with UPPERCASE naming drift

[FLAG] pr2_review\CHERRY_PICK_PLAN.md — PR #2 plan stale 44 days; pending approval status indicates orphaned decision record

[FLAG] pr2_review\COMPARISON_ANALYSIS.md — PR #2 quality gate analysis 44 days old; decision record staleness, archive relevance unclear

[FLAG] pr2_review\SNOW_POWDERED_WHITE_MYTHOLOGY_DRAFT.md — Draft mythological system (Alabaster Voyde) incomplete; integration status unknown

[FLAG] pr2_review\validation_alabaster_voyde.txt — Validation artifact for draft system; confirm if validation passed before archiving

**Summary:** This domain contains **stale PR #2 materials** (cherry-pick plan, comparison analysis) and **duplicate ANKH documentation** alongside **active recent work** (SSOT hash script, draft mythology validation). Recommend: retire PR #2 artifacts, consolidate ANKH docs, surface Alabaster Voyde mythology if validation passed.

---

## error-classifier
**DOMAIN CLEAN**

The error-classifier/ domain is a coherent, focused module (Phase 13 error database with SQLite storage, Bun doc enrichment, and research reporting). All files are ~12 days old, appropriately sized (38–102L), tier 1–2, and showing no drift, orphaning, or naming smells. This is intentional infrastructure, not accumulation.

---

## assets
DOMAIN CLEAN — No critical issues detected.

**Rationale:**
- **Concept art PNGs** (tier:3): Properly archived, frozen by design. "TIER_UNKNOWN" naming is acceptable for experimental reference material.
- **data.json & save_state.json** (tier:2, 12d old): Fresh, versioned, correctly structured.
- **abbreviations.json** (tier:2, 63d old): Tier system reference data. Age aligns with stable reference material; no drift signal from snippet.

All files exhibit correct tier placement and naming discipline. No orphaning, staleness, or structural smell detected.

---

## logs
[FLAG] logs\session_20251207_043539.jsonl — Orphaned 65d-old telemetry; 2 lines only. Consolidate or remove.
[FLAG] logs\session_20251207_043745.jsonl — Orphaned 65d-old watcher logs; minimal data. Consolidate or remove.
[FLAG] logs\session_20251207_043803.jsonl — Orphaned 65d-old service event; 2 lines. Consolidate or remove.

---

## dev
**DOMAIN ANALYSIS: dev/**

[FLAG] dev\overnight_refactor_mode.md — Age 46d, references nonexistent GPT-5.2 model; stale/drift signal

**Status**: Mostly SKIP (copilot-cli docs are fresh, properly tiered, current). One file requires attention for versioning alignment.

---

## plugins
[PROMOTE] plugins\chthonic-tools\.claude-plugin\plugin.json — Declares plugin interface scope: IDE self-heal + mailbox continuity. Agents need to know this contract.

[PROMOTE] plugins\chthonic-tools\commands\postman.md — Formalizes "Response: <topic>" mailbox continuation skeleton. Documents operational pattern for handoff replies.

[PROMOTE] plugins\chthonic-tools\commands\selfheal.md — Declares IDE self-heal + MCP refresh operation. Operational pattern agents should know.