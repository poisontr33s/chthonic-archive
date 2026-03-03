---
type: report
from: codex
to: user
created: 2026-03-03T07:13:16+00:00
priority: high
subject: FORGE_TRANSMUTATION_REPORT
---

# Forge Transmutation Report

## Scope

- Anomaly harvest files analyzed: 353
- Corpse-vault languages audited: 16
- Furnace artifacts attempted: 18

## Yield

- Tempered artifacts: 18
- Rejected artifacts: 0
- Compression ratio: 9451642 -> 239702

## Source Pools

- `anomaly_harvest` | inputs `363` | artifacts `8`
- `corpse_vault` | inputs `198` | artifacts `10`

## Output Languages

- `docs` | tempered `5` | rejected `0`
- `schemas` | tempered `2` | rejected `0`
- `workflows` | tempered `2` | rejected `0`
- `powershell` | tempered `2` | rejected `0`
- `python` | tempered `1` | rejected `0`
- `typescript` | tempered `2` | rejected `0`
- `go` | tempered `1` | rejected `0`
- `csharp` | tempered `1` | rejected `0`
- `c_cpp` | tempered `1` | rejected `0`
- `ruby` | tempered `1` | rejected `0`

## Pathway Catalogue

- `.log` -> `.md` | log -> pattern extraction -> diagnostic playbook | example `dumpster-dive/forge/furnace/docs/diagnostic_playbook.md`
- `.env` -> `.json` | env -> variable contract extraction -> JSON schema | example `dumpster-dive/forge/furnace/schemas/environment_schema.json`
- `.env` -> `.md` | env -> integration hint extraction -> environment map | example `dumpster-dive/forge/furnace/docs/environment_integration_map.md`
- `.off` -> `.md` | workflow.off -> pattern extraction -> workflow catalogue | example `dumpster-dive/forge/furnace/workflows/workflow_pattern_catalog.md`
- `.off` -> `.yml` | workflow.off -> reusable template synthesis -> YAML templates | example `dumpster-dive/forge/furnace/workflows/recovered_workflow_templates.yml`
- `.vsconfig` -> `.md` | vsconfig -> component diff -> toolchain decision record | example `dumpster-dive/forge/furnace/docs/toolchain_decision_record.md`
- `.bat` -> `.ps1` | batch -> transcript-preserving PowerShell transliteration | example `dumpster-dive/forge/furnace/powershell/batch_transliteration.ps1`
- `.md"` -> `.md` | damaged markdown path -> filename forensics note | example `dumpster-dive/forge/furnace/docs/filename_forensics_note.md`
- `corpse-vault/python` -> `.py` | python fragments -> cluster registry -> utility library | example `dumpster-dive/forge/furnace/python/consolidated_python_utilities.py`
- `corpse-vault/typescript` -> `.d.ts` | typescript fragments -> declaration recovery -> archive | example `dumpster-dive/forge/furnace/typescript/recovered_type_archive.d.ts`
- `corpse-vault/*test*` -> `.ts` | test fragments -> fixture metadata -> reusable registry | example `dumpster-dive/forge/furnace/typescript/recovered_test_fixtures.ts`
- `corpse-vault/markdown` -> `.md` | markdown fragments -> recovered architecture decisions | example `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md`
- `corpse-vault/config + orphaned json` -> `.json` | config fragments -> observed key signatures -> schema catalogue | example `dumpster-dive/forge/furnace/schemas/configuration_schema_catalog.json`
- `corpse-vault/shell` -> `.ps1` | shell fragments -> recipe extraction -> PowerShell registry | example `dumpster-dive/forge/furnace/powershell/recovered_shell_recipe_book.ps1`
- `corpse-vault/shell` -> `.go` | shell fragments -> recipe registry -> Go CLI | example `dumpster-dive/forge/furnace/go/recovered_shell_recipe_cli.go`
- `corpse-vault/typescript` -> `.cs` | typescript contracts -> C# class mirror | example `dumpster-dive/forge/furnace/csharp/RecoveredContracts.cs`
- `corpse-vault/rust` -> `.h` | rust struct signatures -> C header for FFI | example `dumpster-dive/forge/furnace/c_cpp/recovered_rust_ffi.h`
- `corpse-vault/python` -> `.rb` | python cluster metadata -> Ruby registry mirror | example `dumpster-dive/forge/furnace/ruby/recovered_python_cluster_registry.rb`

## Novel Pathways

- `damaged markdown path -> filename forensics note` -> `dumpster-dive/forge/tempered/docs/filename_forensics_note.md`
- `python fragments -> cluster registry -> utility library` -> `dumpster-dive/forge/tempered/python/consolidated_python_utilities.py`
- `test fragments -> fixture metadata -> reusable registry` -> `dumpster-dive/forge/tempered/typescript/recovered_test_fixtures.ts`
- `python cluster metadata -> Ruby registry mirror` -> `dumpster-dive/forge/tempered/ruby/recovered_python_cluster_registry.rb`

## Failures and Honest Skips

- None. All produced artifacts cleared the tempering gates.

## Promotion Recommendations

- Promote `dumpster-dive/forge/tempered/powershell/batch_transliteration.ps1` into an active tooling lane after user review.
- Promote `dumpster-dive/forge/tempered/python/consolidated_python_utilities.py` into an active tooling lane after user review.
- Promote `dumpster-dive/forge/tempered/powershell/recovered_shell_recipe_book.ps1` into an active tooling lane after user review.
- Promote `dumpster-dive/forge/tempered/go/recovered_shell_recipe_cli.go` into an active tooling lane after user review.
- Promote `dumpster-dive/forge/tempered/csharp/RecoveredContracts.cs` into an active tooling lane after user review.
- Promote `dumpster-dive/forge/tempered/c_cpp/recovered_rust_ffi.h` into an active tooling lane after user review.

## Tier 2 Score

- Penalty removed: 2
- Base boon: 4.0
- Artifact bonus: 2.5
- Novel pathway bonus: 4.0
- Unrepresented language bonus: 6.0
- Total Tier 2 boon: 16.5
