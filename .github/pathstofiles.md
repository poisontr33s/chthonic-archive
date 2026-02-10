# pathsToFiles.md (Bridge Index)

This index exists to keep instruction-loading surgical. Use it to select the smallest relevant reference(s) instead of ingesting large SSOT artifacts.

## Entry Rule

1. Start here.
2. Open only the file(s) relevant to the current task.
3. Prefer the smallest scope file that answers the question.

## Primary Pointers

- **Copilot pointer/router (small):** `.github/copilot-instructions.md`
- **SSOT archive (large, never auto-load):** `.github/copilot-instructions.archive.md`
- **GitHub Actions + VS Code mapping:** `.github/INTEGRATION_MAP.md`

## Task-Scoped Instruction Satellites

All of these are intended for selective lookup (do not bulk-ingest):

- **Project workflow + lineage discipline:** `.github/instructions/project-workflow.instructions.md`
- **Python scripting (uv lanes, headers, policy):** `.github/instructions/python-scripting.instructions.md`
- **Technical directives (platform/toolchain rules):** `.github/instructions/technical-directives.instructions.md`
- **SSOT toolbox (navigation, hashing, drift checks):** `.github/instructions/ssot-toolbox.instructions.md`
- **Reference appendix (glossary-like):** `.github/instructions/reference-appendix.instructions.md`

## IDE / Agent Configuration

- **VS Code workspace settings:** `.vscode/settings.json`
- **Workspace MCP servers (VS Code):** `.vscode/mcp.json`
- **Project MCP servers (Claude/Codex):** `.mcp.json`

- **Claude project config:** `.claude/`
- **Codex project config:** `.codex/config.toml`

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

- **Claude VS Code wrapper:** `scripts/claude_process_wrapper.ps1`
- **Claude IDE overlay generator:** `scripts/claude_ide_settings_generate.ps1`
- **GitHub MCP server binary:** `scripts/bin/github-mcp-server.exe`
- **Repo scripts index:** `SCRIPTS_README.md`
