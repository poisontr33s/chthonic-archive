---
type: recovery
from: codex
to: user
created: 2026-05-23T14:46:31+02:00
priority: high
---

# VS Code Edit Session Recovery

This preserves the VS Code Edit Session payload that Insiders skipped after restart.

## Diagnosis

- VS Code logs reported: skipped applying 5 changes from edit session `9c42c551-d20b-4d76-9cfa-499d56b52591`.
- Current workspace identity: `https://github.com/poisontr33s/chthonic-archive.git main ae4906b5e91eec0d4d5c40fb7763b56ea4ee612b`.
- Skipped edit-session identity: `{"remote":"https://github.com/poisontr33s/chthonic-archive.git","ref":"main","sha":"0e0ab1673b107ea2fbb7f14873589e38a5ad2961"}`.
- Skipped edit-session source URI: `vscode-remote://tunnel%2Blaptop-draqgn8a/c%3A/Users/erdno/chthonic-archive`.
- Source cache copied from `%APPDATA%\Code - Insiders\Cache\Cache_Data` into `raw-cache/`.

## Decoded Files

- `../../../../c:/Users/erdno/chthonic-archive/.github/copilot-instructions.md` -> `decoded/.github/copilot-instructions.md` (314070 bytes)
- `../../../../c:/Users/erdno/chthonic-archive/.github/STRUCTURAL_INTEGRITY_ANALYSIS.md` -> `decoded/.github/STRUCTURAL_INTEGRITY_ANALYSIS.md` (9123 bytes)
- `../../../../c:/Users/erdno/chthonic-archive/.github/macro-prompt-world/DECORATOR-ASC-GENESIS.md` -> `decoded/.github/macro-prompt-world/DECORATOR-ASC-GENESIS.md` (26648 bytes)
- `../../../../c:/Users/erdno/chthonic-archive/.vscode/settings.json` -> `decoded/.vscode/settings.json` (8711 bytes)
- `../../../../c:/Users/erdno/chthonic-archive/mcp/tools/preflightExecutionContext.test.json` -> `decoded/mcp/tools/preflightExecutionContext.test.json` (2018 bytes)

## Handling

These files were decoded and preserved only. They were not applied to the working tree because the payload targets an older remote/tunnel identity and includes governance/config files.
