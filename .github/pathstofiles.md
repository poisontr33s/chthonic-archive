# pathsToFiles.md (Bridge Index)

This index exists to keep instruction-loading surgical. Use it to select the smallest relevant reference(s) instead of ingesting large SSOT artifacts.

## Entry Rule

1. Start here.
2. Open only the file(s) relevant to the current task.
3. Prefer the smallest scope file that answers the question.

## Primary Pointers

- **Copilot pointer/router (small):** [`.github/copilot-instructions.md`](copilot-instructions.md)
- **SSOT archive (large, never auto-load):** [`.github/copilot-instructions.archive.md`](copilot-instructions.archive.md)
- **GitHub Actions + VS Code mapping:** [`.github/INTEGRATION_MAP.md`](INTEGRATION_MAP.md)

## Tier 1 — Auto-Loaded Instruction Satellites

These `.instructions.md` files are auto-loaded by Copilot in every session (~33K chars):

- **Project workflow + lineage discipline:** [`.github/instructions/project-workflow.instructions.md`](instructions/project-workflow.instructions.md)
- **Python scripting (uv lanes, headers, policy):** [`.github/instructions/python-scripting.instructions.md`](instructions/python-scripting.instructions.md)
- **Technical directives (platform/toolchain rules):** [`.github/instructions/technical-directives.instructions.md`](instructions/technical-directives.instructions.md)
- **SSOT toolbox (navigation, hashing, drift checks):** [`.github/instructions/ssot-toolbox.instructions.md`](instructions/ssot-toolbox.instructions.md)
- **ANKH workflow (procedural basics):** [`.github/instructions/ankh-workflow.instructions.md`](instructions/ankh-workflow.instructions.md)
- **Autopsy protocol (debt decomposition):** [`.github/instructions/autopsy-protocol.instructions.md`](instructions/autopsy-protocol.instructions.md)

## Tier 2 — On-Demand Reference Files

These `.reference.md` files are NOT auto-loaded. Open only when the task requires them:

- **Mathematical engines (T³-MΨ, §VIII-IX):** [`.github/instructions/mathematical-engines.reference.md`](instructions/mathematical-engines.reference.md)
- **Magistra logic (validation ceremonies, §X):** [`.github/instructions/magistra-logic.reference.md`](instructions/magistra-logic.reference.md)
- **Entity generation (9-step protocol):** [`.github/instructions/asc-entity-generation.reference.md`](instructions/asc-entity-generation.reference.md)
- **Behavioral scenarios (SBS, §XVII):** [`.github/instructions/behavioral-scenarios.reference.md`](instructions/behavioral-scenarios.reference.md)
- **Reference appendix (glossary, appendices A-E):** [`.github/instructions/reference-appendix.reference.md`](instructions/reference-appendix.reference.md)

## IDE / Agent Configuration

- **VS Code workspace settings:** [`.vscode/settings.json`](../.vscode/settings.json)
- **Workspace MCP servers (VS Code):** [`.vscode/mcp.json`](../.vscode/mcp.json)
- **Project MCP servers (Claude/Codex):** [`.mcp.json`](../.mcp.json)

- **Claude project config:** [`.claude/`](../.claude/)
- **Claude project agents (also discovered by Copilot CLI):** [`.claude/agents/`](../.claude/agents/)
- **Codex project config:** [`.codex/config.toml`](../.codex/config.toml)

User-scoped (do not commit secrets; treat as local state):

- **Claude user settings:** `C:\\Users\\erdno\\.claude\\settings.json`
- **Codex user settings:** `C:\\Users\\erdno\\.codex\\config.toml`

## META-IDE Research Staging

Curated, sorted payloads for inspection/assembly:

- **Structured vendor tree:** `meta-ide/structured/`
- **Structured manifest:** `meta-ide/structured/manifests/structured.manifest.json`
- **Vendor snapshots:** `meta-ide/snapshots/`

Terminal Copilot lanes (vendored under the structured tree when present):

- **Copilot CLI (WinGet prerelease install snapshot):** `meta-ide/structured/engines/copilot-cli/install-root/`
- **GitHub CLI Copilot extension:** `meta-ide/structured/engines/gh-copilot/`

## Operational Tooling (Common Touchpoints)

- **Claude VS Code wrapper:** [`scripts/claude_process_wrapper.ps1`](../dumpster-dive/intake/claude-ide-harden-2026-02-10/tier-1-direct/claude_process_wrapper.ps1)
- **Claude IDE overlay generator:** [`scripts/claude_ide_settings_generate.ps1`](../scripts/claude_ide_settings_generate.ps1)
- **Copilot CLI launcher profile (opt-out switches for agents/MCP/instructions):** [`scripts/copilot_clean.ps1`](../scripts/copilot_clean.ps1)
- **GitHub MCP server binary:** [`scripts/bin/github-mcp-server.exe`](../scripts/bin/github-mcp-server.exe)
- **Repo scripts index:** [`SCRIPTS_README.md`](../SCRIPTS_README.md)
