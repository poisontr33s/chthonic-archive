# Overnight Daemon Report (20260221_030002)

- Repo root: C:/Users/erdno/chthonic-archive
- Files scanned: 1612
- TODO/FIXME/HACK hits (captured): 127

## Top Candidates
| Rank | File | Score | TODO hits | Reasons | 
|---:|---|---:|---:|---| 
| 1 | scripts/api_pool_persist_user_env.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 2 | scripts/api_pool.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 3 | scripts/aws/env.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 4 | scripts/bridge-diagnostic.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 5 | scripts/check-profiles.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 6 | scripts/check-solana-version.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 7 | scripts/chthonic.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 8 | scripts/claude_crossover.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 9 | scripts/claude_healthcheck.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 10 | scripts/claude_insiders_selfheal.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 11 | scripts/claude_profile.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 12 | scripts/claude-ide-e2e-check.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 13 | scripts/claudine.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 14 | scripts/compare_probe_variants.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 15 | scripts/copilot_clean.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 16 | scripts/Discover-SSOT-Treasure.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 17 | scripts/fix_vscode_cli.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 18 | scripts/fix-md-links.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 19 | scripts/fortify_terminal.ps1 | 58 | 0 | repo tooling, powershell tooling |
| 20 | scripts/gemini-cli-wrapper.ps1 | 58 | 0 | repo tooling, powershell tooling |

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
| scripts/run_archaeology.ps1 | 28 | TODO | hits for daemon |
| scripts/scanner_approval.md | 210 | TODO | \|FIXME\|HACK\|NOTE\|WARNING\|DEPRECATED)\b', re.I), |
| extensions/tabbyAPI/main.py | 60 | TODO | remove model_dump() |
| extensions/tabbyAPI/main.py | 70 | TODO | remove model_dump() |
| extensions/tabbyAPI/main.py | 83 | TODO | remove model_dump() |
| extensions/tabbyAPI/sampler_overrides/sample_preset.yml | 8 | TODO | Improve documentation for each field |
| extensions/tabbyAPI/endpoints/server.py | 78 | TODO | Move OAI API to a separate folder |
| extensions/tabbyAPI/common/config_models.py | 31 | TODO | convert this to a pathlib.path? |
| extensions/tabbyAPI/common/config_models.py | 89 | TODO | Migrate config.yml to have the log_ prefix |
| extensions/tabbyAPI/common/config_models.py | 118 | TODO | convert this to a pathlib.path? |
| extensions/tabbyAPI/common/config_models.py | 314 | TODO | convert this to a pathlib.path? |
| extensions/tabbyAPI/common/config_models.py | 386 | TODO | convert this to a pathlib.path? |
| extensions/tabbyAPI/common/config_models.py | 409 | TODO | convert this to a pathlib.path? |
| extensions/tabbyAPI/common/model.py | 156 | TODO | Figure out a way to do this with Pydantic validation |
| extensions/tabbyAPI/common/sampling.py | 331 | FIXME | find a better way to register this |
| extensions/tabbyAPI/common/sampling.py | 396 | TODO | Maybe move these into the class |
| extensions/tabbyAPI/common/tabby_config.py | 21 | TODO | make this pydantic? |
| extensions/tabbyAPI/common/tabby_config.py | 33 | TODO | Change logic if file loading requires actions in the future |
| extensions/tabbyAPI/common/tabby_config.py | 49 | TODO | clean this up a bit |
| extensions/tabbyAPI/common/templating.py | 241 | TODO | Possibly link to the TokenizerConfig class |
| extensions/tabbyAPI/backends/exllamav3/model.py | 193 | TODO | Remove when fixed in exllama upstream |
| extensions/tabbyAPI/backends/exllamav3/model.py | 932 | TODO | This currently does not work in exl3 |
| extensions/tabbyAPI/backends/exllamav3/model.py | 1020 | TODO |  |
| extensions/tabbyAPI/backends/exllamav3/model.py | 1074 | TODO |  |
| extensions/tabbyAPI/backends/exllamav2/model.py | 666 | TODO | Maybe make a wrapper class with an ID instead of a utility function |
| extensions/chthonic-archive/src/entropy/entropyWorker.ts | 200 | TODO | \|FIXME\|HACK\|XXX\|BUG)\b/gi); |
| extensions/chthonic-archive/media/wasm/pkg/entropy_renderer_wasm.js | 437 | TODO | we could test for more things here, like `Set`s and `Map`s. |
| error-classifier/ingest.ts | 76 | TODO | , FIXME, HACK) in src directory |
| error-classifier/ingest.ts | 82 | TODO | \|FIXME\|HACK):?\s*(.*)/gi; |
| docs/STAGE_1_MIGRATION_PLAN.md | 210 | TODO | Create ankhrc_validator.py |
| docs/STAGE_1_MIGRATION_PLAN.md | 215 | TODO | #6) |
