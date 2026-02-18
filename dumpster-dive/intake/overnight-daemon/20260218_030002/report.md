# Overnight Daemon Report (20260218_030002)

- Repo root: C:/Users/erdno/chthonic-archive
- Files scanned: 1310
- TODO/FIXME/HACK hits (captured): 81

## Top Candidates
| Rank | File | Score | TODO hits | Reasons | 
|---:|---|---:|---:|---| 
| 1 | scripts/chthonic.ps1 | 2083 | 0 | 🚨 Critical Complexity: Giant file detected, Documentation Debt: 1525 (rel to complexity: 347, density: 0.06), repo tooling, powershell tooling |
| 2 | scripts/decorator_cross_ref_maximum.py | 1416 | 0 | 🚨 Critical Complexity: Giant file detected, Documentation Debt: 876 (rel to complexity: 230, density: 0.12), repo tooling |
| 3 | scripts/decorator_cross_ref_production.py | 1040 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 750 (rel to complexity: 197, density: 0.12), repo tooling |
| 4 | scripts/overnight_daemon.ts | 902 | 6 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 612 (rel to complexity: 138, density: 0.06), repo tooling, todos: 6 |
| 5 | scripts/ingest_research.py | 897 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 607 (rel to complexity: 122, density: 0.00), repo tooling |
| 6 | mas_mcp/milf_genesis_v2.py | 816 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 556 (rel to complexity: 132, density: 0.08) |
| 7 | scripts/decorator_cross_ref_enhanced.py | 812 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 523 (rel to complexity: 139, density: 0.12), repo tooling |
| 8 | scripts/extract_session_value.py | 771 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 482 (rel to complexity: 113, density: 0.07), repo tooling |
| 9 | mas_mcp/genesis_scheduler.py | 759 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 499 (rel to complexity: 118, density: 0.08) |
| 10 | mas_mcp/gpu_orchestrator.py | 721 | 0 | ⚠️ High Complexity: Needs decomposition, Documentation Debt: 461 (rel to complexity: 108, density: 0.07) |
| 11 | scripts/lib/extract.py | 596 | 0 | Moderate Complexity, Documentation Debt: 457 (rel to complexity: 98, density: 0.03), repo tooling |
| 12 | scripts/envelope_sync.py | 584 | 0 | Moderate Complexity, Documentation Debt: 445 (rel to complexity: 91, density: 0.01), repo tooling |
| 13 | scripts/rootdir_health_audit.py | 563 | 0 | Moderate Complexity, Documentation Debt: 424 (rel to complexity: 99, density: 0.07), repo tooling |
| 14 | scripts/structure_session_log.py | 510 | 0 | Moderate Complexity, Documentation Debt: 370 (rel to complexity: 84, density: 0.06), repo tooling |
| 15 | scripts/harvest_claudines.ps1 | 468 | 0 | Moderate Complexity, Documentation Debt: 310 (rel to complexity: 82, density: 0.12), repo tooling, powershell tooling |
| 16 | mas_mcp/test_hardware_specific.py | 458 | 0 | Moderate Complexity, Documentation Debt: 348 (rel to complexity: 78, density: 0.05) |
| 17 | scripts/hf_refiner.py | 456 | 0 | Moderate Complexity, Documentation Debt: 316 (rel to complexity: 68, density: 0.03), repo tooling |
| 18 | scripts/hf_mcp_service_registry.py | 454 | 0 | Moderate Complexity, Documentation Debt: 315 (rel to complexity: 68, density: 0.04), repo tooling |
| 19 | scripts/background_services.py | 450 | 0 | Moderate Complexity, Documentation Debt: 310 (rel to complexity: 71, density: 0.06), repo tooling |
| 20 | scripts/asc_entity_generator.py | 446 | 0 | Moderate Complexity, Documentation Debt: 307 (rel to complexity: 73, density: 0.08), repo tooling |

## TODO / FIXME / HACK (Sample)
| File | Line | Kind | Text | 
|---|---:|---|---| 
| src/data/procedural.rs | 35 | TODO | Hook into the runtime Tier 3 manifestation flow. |
| src/data/procedural.rs | 70 | TODO | Hook into dynamic faction encounter generation. |
| scripts/epistemograph_schema_design.md | 110 | TODO | , MUST, assert) are useful, but this repo has domain-specific epistemic markers: |
| scripts/overnight_daemon.ts | 35 | TODO | " \| "FIXME" \| "HACK"; |
| scripts/overnight_daemon.ts | 389 | TODO | \|FIXME\|HACK)\b\s*:?\s*(.*)$/i.exec(line); |
| scripts/overnight_daemon.ts | 392 | TODO | " \|\| rawKind === "FIXME" \|\| rawKind === "HACK") ? rawKind : "TODO"; |
| scripts/overnight_daemon.ts | 1028 | TODO | /FIXME/HACK hits (captured): ${allTodoHits.length}`); |
| scripts/overnight_daemon.ts | 1039 | TODO | hits \| Reasons \| "); |
| scripts/overnight_daemon.ts | 1047 | TODO | / FIXME / HACK (Sample)"); |
| scripts/run_archaeology.ps1 | 25 | TODO | hits for daemon |
| scripts/scanner_approval.md | 210 | TODO | \|FIXME\|HACK\|NOTE\|WARNING\|DEPRECATED)\b', re.I), |
| extensions/chthonic-archive/src/entropy/entropyWorker.ts | 200 | TODO | \|FIXME\|HACK\|XXX\|BUG)\b/gi); |
| extensions/chthonic-archive/media/wasm/pkg/entropy_renderer_wasm.js | 437 | TODO | we could test for more things here, like `Set`s and `Map`s. |
| error-classifier/ingest.ts | 76 | TODO | , FIXME, HACK) in src directory |
| error-classifier/ingest.ts | 82 | TODO | \|FIXME\|HACK):?\s*(.*)/gi; |
| docs/STAGE_1_MIGRATION_PLAN.md | 210 | TODO | Create ankhrc_validator.py |
| docs/STAGE_1_MIGRATION_PLAN.md | 215 | TODO | #6) |
| docs/reference/DAEMON_CLASSIFICATION_ENHANCEMENTS.md | 16 | TODO | detection. When enabled, the daemon generates: |
| docs/frameworks/AUTONOMOUS_ORCHESTRATION_FRAMEWORK.md | 159 | TODO | /FIXME patterns |
| docs/frameworks/AUTONOMOUS_ORCHESTRATION_FRAMEWORK.md | 160 | TODO | OR FIXME") |
| dev/overnight_refactor_mode.md | 29 | TODO | / FIXME (if none exist where they should, create them), code smells, determinism issues, hygiene issues, missing tests, unclear naming, duplicated logic, brittle patterns. \| |
| dev/overnight_refactor_mode.md | 81 | TODO | /FIXME, obvious smells, missing tests, brittle logic, unclear naming \| |
| dev/overnight_refactor_mode.md | 82 | TODO | Roulette \| `dev/overnight_todo.md` (if present) \| |
| debugging_data/codex_5.1_sabotage_trick.md | 1759 | TODO | list** - I'll break down complex work |
| debugging_data/codex_5.1_sabotage_trick.md | 4544 | HACK | . That’s a justified accommodation. |
| debugging_data/codex_5.1_sabotage_trick.md | 6682 | TODO | and begin creating the comprehensive validation document: Summarized conversation history |
| codex/mailbox/FIX_DEAD_CODE_WARNINGS.md | 34 | TODO | ` comment explaining the planned usage |
| claude-codex-gemini/hotswapresearch.md | 21 | HACK | " Era and the Instruction Tuning Divergence** |
| claude-codex-gemini/hotswapresearch.md | 23 | HACK | " era. Models were no longer just completing text; they were trained to follow instructions formatted in highly specific ways. The lack of a unified standard led to a proliferation of incompatible formats, often referred to as the "Cambrian |
| claude-codex-gemini/hotswapresearch.md | 29 | HACK | " became a standard, albeit despised, design pattern, where massive if-else blocks in the client code determined how to stringify a JSON object based on the target model name.6 |
| claude-codex-gemini/hotswapresearch.md | 39 | HACK | " obsolete.10 |
| claude-codex-gemini/research_GPTOSS_HF.md | 270 | HACK | ** |
| claude-codex-gemini/research_GPTOSS_HF.md | 391 | HACK | **. By disguising the data extraction task as a function call, we leverage the model's highly disciplined "Tool Use" mode. |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 4 | TODO | " in content or "FIXME" in content: |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 57 | TODO | " in |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 58 | FIXME | " in line] |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 63 | TODO | .md |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 133 | TODO | .md |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 284 | TODO | " in content or "FIXME" in content: |
| claude-codex-gemini/triadic-session-context/gemini-cli-session-fix-too-large.md | 298 | TODO | " in content or "FIXME" |
