# VS Code Insiders Startup Output Audit - 2026-06-17

Scope:

- Baseline log folder: `C:\Users\eldno\AppData\Roaming\Code - Insiders\logs\20260617T194836`
- Post-restart log folder: `C:\Users\eldno\AppData\Roaming\Code - Insiders\logs\20260617T205244`
- Workspace: `C:\Users\eldno\chthonic-archive`

API/MCP contract checks were run without printing or rotating secrets:

- `.\scripts\api_pool.ps1 -Mock`: pass
- `pwsh -NoProfile -File scripts\mcp_write_local.ps1 -Mock`: pass
- `pwsh -NoProfile -File scripts\mcp_write_local.ps1 -List`: pass
- `.codex\skills\api-manager\scripts\api_manager.ps1 -Doctor`: pass
- `.codex\skills\api-manager\scripts\api_manager.ps1 -VerifyGitHub`: pass as account `poisontr33s`

## ParserErrors From My Commands

1. `Missing argument in parameter list.`
   - Cause: invalid PowerShell shorthand: `Sort-Object Errors -Descending, Warns -Descending, KB -Descending`
   - Correct pattern: `Sort-Object @{Expression='Errors';Descending=$true}, ...`

2. `Missing argument in parameter list.`
   - Cause: same invalid shorthand with `Sort-Object Err -Descending, Warn -Descending, KB -Descending`
   - Correct pattern: use hashtable sort expressions.

3. `An empty pipe element is not allowed.`
   - Cause: malformed dense one-liner ending a nested script block before `| Format-List`
   - Correct pattern: avoid nested one-liners for these probes.

Related non-ParserError: `[regex]::Matches()` was called on null while scanning zero-byte log files.

## Post-Restart Comparison

Recursive signature counts in `20260617T205244`:

| Signal | Count | Status |
| --- | ---: | --- |
| `powershell_utf8` | 0 | Fixed |
| `claude-plugins-official` | 0 | Fixed |
| `Failed to load custom agents` | 0 | Fixed after cache quarantine |
| missing SSH config | 0 | Fixed |
| `MODULE_TYPELESS_PACKAGE_JSON` | 1 | Upstream/Insiders packaging noise remains |
| `potential listener LEAK` | 2 | Renderer/dependency noise remains |
| `DEP0040` | 1 | Node dependency deprecation remains |
| `DEP0169` | 1 | Node dependency deprecation remains |
| `no Copilot token source` | 1 | Reduced to startup race |
| `apps_mcp_path_override` | 3 | Codex internal feature mismatch remains |
| `AuthRequired` | 2 | Codex GitHub MCP auth drift during this restart |
| `invalid_grant` | 3 | Microsoft MSAL plus Codex GitHub MCP token refresh drift |
| `defaultPrompt` | 38 | Codex temp plugin manifest warning during this restart |
| `core.virtualfilesystem` | 1 | Logged before local fix was applied |

## Changes Applied

### VS Code Startup Cascade

Workspace `.vscode/settings.json`:

- `editor.maxTokenizationLineLength`: `99999999999` -> `20000`
- `editor.experimental.asyncTokenization`: `false` -> `true`
- `diffEditor.maxComputationTime`: `0` -> `5000`
- `chat.agent.maxRequests`: `9999999` -> `100`
- `chat.mcp.autostart`: `newAndOutdated` -> `never`
- `chatgpt.openOnStartup`: `true` -> `false`

User settings `C:\Users\eldno\AppData\Roaming\Code - Insiders\User\settings.json`:

- `diffEditor.maxComputationTime`: `0` -> `5000`
- `chat.agent.maxRequests`: `9999999` -> `100`
- `chatgpt.openOnStartup`: `true` -> `false`
- `editor.largeFileOptimizations`: `false` -> `true`

Validation:

- User settings JSON parsed successfully.
- Workspace settings JSONC parsed successfully with `jsonc-parser`.

### Codex Config Noise

Changed `C:\Users\eldno\.codex\config.toml`:

- Removed unsupported feature key `powershell_utf8`.
- Removed stale `claude-plugins-official` marketplace/plugin entries.
- Removed stale non-curated local plugin entries that were producing manifest scan noise.
- Changed GitHub MCP auth env from `GITHUB_MCP_PAT` to verified pool key `GITHUB_TOKEN`.

Evidence:

- API pool mock passed.
- MCP payload mock passed.
- GitHub token verifier passed as `poisontr33s`.
- No token values were printed, minted, refreshed, or rotated.

Remaining:

- `apps_mcp_path_override` is not in visible TOML/JSON settings. It appears to be Codex extension/server feature mismatch or internal state.
- `thread_tools` was also seen as an unknown Codex feature in earlier Codex logs. Treat as internal feature drift unless it appears in visible config after the next restart.

### Codex Temp Plugin Manifest

Finding:

- Repeated `defaultPrompt` warnings came from an unreferenced temp plugin cache:
  `C:\Users\eldno\.codex\.tmp\plugins\plugins\ngs-analysis\.codex-plugin\plugin.json`

Changed:

- Moved the cache entry out of the scan path:
  `C:\Users\eldno\.codex-quarantine\ngs-analysis.disabled-20260617T211500`

Expected after next restart:

- `ngs-analysis` / `defaultPrompt` plugin manifest warning should disappear unless Codex refreshes the remote catalog and rehydrates the plugin.

### Microsoft Authentication

Finding:

- Microsoft Authentication logged `AADSTS700082`: MSAL refresh token expired due to inactivity.
- One token issue timestamp in the log was `2025-06-27T21:13:30.1147706Z`.

Action taken:

- No account cache deletion.
- No API pool token action.

Required manual fix if it remains:

- In VS Code Insiders, sign out of the Microsoft account and sign back in.

### Window / Renderer / Custom Agents

Findings:

- `Failed to load custom agents` disappeared after restart.
- Renderer still logs listener leak and Node deprecation warnings.
- `Both old and new agent-plugins directories exist` was still logged during this restart.

Changed:

- Quarantined stale `awesome-copilot` agent-plugin cache outside the scan root:
  `C:\Users\eldno\.vscode-insiders-quarantine\awesome-copilot.disabled-20260617T201919`

Expected after next restart:

- The old/new agent-plugin migration warning should disappear.
- Listener leak and Node deprecation warnings may remain because they appear extension/runtime-side, not project package-manager-side. Bun does not directly fix those unless the noisy extension path is replaced or updated.

### Git

Changed:

- Global `safe.directory` typo fixed:
  `C:/Users/eldno/chthonic-archive` -> `C:/Users/eldno/chthonic-archive`
- Local `core.virtualfilesystem=false` added after GitHub PR startup warning.
- Local `core.fsmonitor=false` added after `git status` reported virtual repository incompatibility with fsmonitor.

Verified:

- `git config --global --get-all safe.directory` returns only `C:/Users/eldno/chthonic-archive`.
- `git config --local --get core.virtualfilesystem` returns `false`.
- `git config --local --get core.fsmonitor` returns `false`.
- Scoped `git status` no longer prints the fsmonitor warning.

### GitHub PR SSH Config

Finding:

- `C:\Users\eldno\.ssh\config` was missing.
- GitHub PR extension was probing it opportunistically.
- Git auth protocol is HTTPS, not SSH.

Changed:

- Added comment-only `C:\Users\eldno\.ssh\config`.

Result:

- Missing SSH config warning was absent in the post-restart log folder.

### GitHub Copilot Chat

Finding:

- Startup still had one `no Copilot token source` race.
- Later auth succeeded and embeddings loaded.

Conclusion:

- Reduced startup race/noise, not broken auth.

Mitigations already applied:

- Disabled ChatGPT/Codex open-on-startup.
- Disabled workspace MCP autostart.
- Quarantined stale agent/plugin cache.

## Still Needs One More Restart

Restart VS Code Insiders once more and compare the newest log folder against `20260617T205244`.

Expected gone or reduced:

- Codex GitHub MCP `AuthRequired` / `invalid_grant` from `GITHUB_MCP_PAT` drift.
- Git `core.virtualfilesystem` startup warning.
- Git fsmonitor warning.
- `defaultPrompt` warnings from `ngs-analysis`.
- Agent-plugin old/new migration warning.

Expected possibly remaining:

- Microsoft `AADSTS700082` until manual Microsoft sign-out/sign-in.
- Renderer listener leak warning.
- Node `DEP0040` / `DEP0169` deprecation warnings.
- Markdown LS `MODULE_TYPELESS_PACKAGE_JSON`.
- Codex `apps_mcp_path_override` if it is internal extension/server feature drift.

## Current Task State

```json
{
  "tasks": {
    "finished_all_that_can_be_done_without_restart": true,
    "still_not_finished": [
      "Restart VS Code Insiders and compare the newest log folder",
      "Confirm Codex GitHub MCP AuthRequired/invalid_grant warnings are gone",
      "Confirm Git core.virtualfilesystem/fsmonitor warnings are gone",
      "Confirm ngs-analysis defaultPrompt manifest warnings are gone",
      "Manual Microsoft sign-out/sign-in if AADSTS700082 remains"
    ],
    "active": false,
    "not_finished_all": true
  }
}
```

