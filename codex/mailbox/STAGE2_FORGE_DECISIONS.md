---
type: decision
from: codex
to: user
created: 2026-03-04
priority: high
subject: Stage 2 Forge Strategy Decisions
in_response_to: codex/mailbox/EXTENSION_CONTRIBUTION_GRAPH_VALIDATOR_CHORE.md
---

# Stage 2 Forge Decisions

## Dedupe Policy (Furnace vs Tempered)

Decision: **retain dual-lane artifacts for now**.

Rationale:

- `furnace/` is the transmutation output lane (raw forged outputs with pathway context).
- `tempered/` is the graduation lane (validated artifacts with quality gate status).
- A forced dedupe now would collapse provenance semantics while Stage 2 continuity is still being validated.

Stage 3 trigger for dedupe reconsideration:

- Promote at least 3 furnace-tempered pairs into active lanes, then reassess whether furnace copies can become manifest-only references.

## Promotion Disposition (Six Recommended Artifacts)

| Artifact | Current Disposition | Reason |
|---|---|---|
| `dumpster-dive/forge/tempered/powershell/batch_transliteration.ps1` | **Approved for promotion** | Replaces legacy `.bat` semantics in a PowerShell-native lane. |
| `dumpster-dive/forge/tempered/python/consolidated_python_utilities.py` | **Approved for promotion** | High utility density and direct fit for script/library reuse. |
| `dumpster-dive/forge/tempered/powershell/recovered_shell_recipe_book.ps1` | **Hold** | Useful, but overlaps with Go CLI pathway; defer until ownership lane is assigned. |
| `dumpster-dive/forge/tempered/go/recovered_shell_recipe_cli.go` | **Approved for promotion** | Establishes continued Go representation and executable pathway value. |
| `dumpster-dive/forge/tempered/csharp/RecoveredContracts.cs` | **Hold** | Keep in tempered lane until a consuming .NET lane is defined. |
| `dumpster-dive/forge/tempered/c_cpp/recovered_rust_ffi.h` | **Hold** | Requires explicit ABI ownership contract before promotion. |

Governance note:

- Per WPTG lane governance, this is a disposition decision artifact. Promotion execution to active lanes remains user-controlled.
