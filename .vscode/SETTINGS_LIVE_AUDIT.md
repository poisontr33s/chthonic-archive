# VS Code Settings Live Audit

- Generated: 2026-06-17
- Workspace: `C:\Users\eldno\chthonic-archive`
- VS Code Insiders: `1.126.0-insider`
- Commit: `226cd5d573076e1d3b260d21409538fbc67cb059`
- Install root: `C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\226cd5d573`
- Workspace settings: `.vscode/settings.json`
- User settings: `C:\Users\eldno\AppData\Roaming\Code - Insiders\User\settings.json`

## Intent

This audit is not an argument for extra abstraction. The goal is practical modernization of VS Code Insiders settings:

1. Keep settings that are current, recognized, and useful.
2. Remove or replace settings that are stale, misspelled, duplicated across scopes, or only kept from old beta-era workarounds.
3. Keep the editor ergonomic and familiar while reducing startup work and Output noise.
4. Make changes in small, reversible steps with a restart/log comparison after behavior-affecting edits.

Both workspace and user settings parse as valid JSONC.

## Local Evidence

Installed extension set:

- `anthropic.claude-code@2.1.179`
- `chthonic-archive.chthonic-archive@0.2.9`
- `chthonic-archive.chthonic-mandala@0.1.0`
- `chthonic-archive.chthonic-themes@0.2.9`
- `chthonic-archive.chtonic-rendered-ai-markdown-paste-flavoured@0.1.0`
- `chthonic-archive.vampire-corpus@0.1.0`
- `donjayamanne.githistory@0.6.20`
- `github.codespaces@1.18.13`
- `github.remotehub@0.65.2026060101`
- `github.vscode-github-actions@0.32.0`
- `github.vscode-pull-request-github@0.151.2026061704`
- `google.gemini-cli-vscode-ide-companion@0.20.0`
- `ms-vscode-remote.remote-containers@0.461.0`
- `ms-vscode.remote-explorer@0.5.0`
- `ms-vscode.remote-repositories@0.43.2026060101`
- `ms-vscode.remote-server@1.5.3`
- `openai.chatgpt@26.5609.30741`

Manifest crawl:

- Package manifests inspected: `224`
- Contributed settings keys found: `1022`
- Workspace parse errors: `0`
- User parse errors: `0`

Note: core VS Code settings such as `editor.*`, `workbench.*`, `terminal.integrated.*`, and `files.*` are not fully represented by extension `package.json` manifests, so this audit treats local manifest absence as a hint, not proof of invalidity.

## Scope Collision

The same key appears in both workspace and user settings for 35 entries:

- `[json]`
- `[jsonc]`
- `[markdown]`
- `chat.agent.maxRequests`
- `chat.checkpoints.showFileChanges`
- `chat.tools.global.autoApprove`
- `chat.unifiedAgentsBar.enabled`
- `chat.useCustomizationsInParentRepositories`
- `chatgpt.openOnStartup`
- `claudeCode.allowDangerouslySkipPermissions`
- `claudeCode.preferredLocation`
- `claudeCode.selectedModel`
- `claudeCode.useTerminal`
- `diffEditor.maxComputationTime`
- `editor.bracketPairColorization.enabled`
- `editor.formatOnSave`
- `editor.guides.bracketPairs`
- `editor.tokenColorCustomizations`
- `git.autofetch`
- `git.openRepositoryInParentFolders`
- `git.suggestSmartCommit`
- `github.copilot.chat.anthropic.contextEditing.mode`
- `github.copilot.chat.askAgent.model`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`
- `github.copilot.chat.completionsFetcher`
- `github.copilot.chat.exploreAgent.model`
- `github.copilot.chat.nesFetcher`
- `github.copilot.chat.responsesApiContextManagement.enabled`
- `github.copilot.enable`
- `github.copilot.nextEditSuggestions.enabled`
- `terminal.integrated.defaultProfile.windows`
- `terminal.integrated.profiles.windows`
- `workbench.colorTheme`
- `workbench.iconTheme`
- `workbench.productIconTheme`

Interpretation:

- User settings are the right place for personal UI/editor defaults such as theme, font, cursor, color customizations, and broad editor behavior.
- Workspace settings are the right place for repo-specific behavior such as Git scan limits, MCP startup policy, tasks, Chthonic extension toggles, and language/tool defaults.
- Copilot/Claude/OpenAI settings should be split by actual intent: personal preference in user settings, repo-specific safety/startup/tool limits in workspace settings.

## High-Signal Findings

### 1. Probable Typo / Retired Key

Workspace:

- `workbenchexperimental.cloudChanges.partialMatches.enabled`

Finding:

- No local manifest evidence.
- The shape is suspicious: it lacks the normal `workbench.experimental...` namespace dot.

Recommendation:

- Remove it unless a current log explicitly references it.

### 2. Legacy Copilot Fetcher Overrides

Workspace and user:

- `github.copilot.chat.nesFetcher`: `node-fetch`
- `github.copilot.chat.completionsFetcher`: `node-fetch`

Finding:

- Current Copilot is no longer the same beta-era path these overrides were likely created for.
- They are contributed settings, so they are not invalid, but they force a specific fetch implementation.

Recommendation:

- Test one restart with both removed from workspace first.
- If no Copilot Output regression appears, remove them from user settings too.

### 3. Global Copilot Formatter

User:

- `editor.defaultFormatter`: `GitHub.copilot-chat`
- `notebook.defaultFormatter`: `GitHub.copilot-chat`
- `[json] editor.defaultFormatter`: `GitHub.copilot-chat`
- `[html] editor.defaultFormatter`: `GitHub.copilot-chat`

Finding:

- This is broad and likely not what you want for a Bun/uv/Rust workspace.
- Workspace already pins `[jsonc]` to `vscode.json-language-features`.

Recommendation:

- Move to language-specific formatters:
  - JSON/JSONC: `vscode.json-language-features`
  - TypeScript/JavaScript/HTML: only set when the intended formatter is installed and active
  - Markdown: keep Copilot only if you intentionally want generated formatting behavior

### 4. High-Trust Automation Settings

Workspace and user:

- `chat.tools.global.autoApprove`: `true`
- `claudeCode.allowDangerouslySkipPermissions`: `true`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`: `true`

Finding:

- These are not startup-noise problems.
- They are high-trust operating mode settings duplicated across scopes.

Recommendation:

- Keep them workspace-local if this repo is intentionally permissive.
- Remove from user settings if other workspaces should not inherit the same trust model.

### 5. Startup-Cascade Controls Are Correct

Workspace/user:

- `chatgpt.openOnStartup`: `false`
- `chat.mcp.autostart`: `never` in workspace
- `chat.agent.maxRequests`: `100`
- `diffEditor.maxComputationTime`: `5000`
- `editor.largeFileOptimizations`: `true` in user settings
- `editor.maxTokenizationLineLength`: `20000` in workspace

Finding:

- These match the Output-log cleanup direction.
- They should stay.

### 6. Theme Scope Is Now Correct

Workspace:

- `workbench.colorTheme`: `Chthonic — Geological Core (Sister Ferrum Scoriae)`
- `editor.tokenColorCustomizations` now targets `[Chthonic — Geological Core (Sister Ferrum Scoriae)]`

User:

- Same theme plus richer theme-specific token/color customizations.

Recommendation:

- Keep the rich visual customization in user settings.
- Keep only repo-critical theme assertion in workspace, or remove workspace theme entirely if user settings should control all appearance.

## Modernization Sequence

Use the research file first: `.vscode/SETTINGS_MODERNIZATION_RESEARCH.md`. Do not rename settings whose current key is unresolved between official docs and local Insiders metadata.

### Pass 1: No-Risk Cleanup

Remove from workspace:

- `workbenchexperimental.cloudChanges.partialMatches.enabled`

Then restart and compare Output logs.

### Pass 2: De-Duplicate UI Defaults

Prefer user settings for:

- `workbench.colorTheme`
- `workbench.iconTheme`
- `workbench.productIconTheme`
- `editor.tokenColorCustomizations`
- `editor.bracketPairColorization.enabled`
- `editor.guides.bracketPairs`
- `terminal.integrated.defaultProfile.windows`
- `terminal.integrated.profiles.windows`

Workspace keeps only repo-specific terminal env or profile additions if needed.

### Pass 3: Copilot Fetcher Probe

Temporarily remove from workspace first:

- `github.copilot.chat.nesFetcher`
- `github.copilot.chat.completionsFetcher`

Restart and compare:

- Copilot Chat Output
- Copilot Log
- Renderer warnings

If clean, remove the same keys from user settings.

### Pass 4: Formatter Sanity

Replace global `GitHub.copilot-chat` formatter usage in user settings with language-scoped formatters.

Immediate candidates:

- `[json]`: `vscode.json-language-features`
- `[jsonc]`: `vscode.json-language-features`

Leave TypeScript/JavaScript/HTML unset until the active formatter choice is explicit.

### Pass 5: Trust Boundary Split

Keep these only where intended:

- `chat.tools.global.autoApprove`
- `claudeCode.allowDangerouslySkipPermissions`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`

Recommended split:

- Workspace: allowed for `chthonic-archive` if intentional.
- User: remove unless every workspace should inherit permissive automation.

## Current Task State

```json
{
  "tasks": {
    "finished_first_live_settings_audit": true,
    "settings_files_parse": true,
    "safe_startup_controls_kept": true,
    "still_not_finished": [
      "Remove or prove workbenchexperimental.cloudChanges.partialMatches.enabled",
      "Decide which duplicated UI/theme settings belong only in user settings",
      "Probe removal of Copilot node-fetch overrides",
      "Normalize global formatter settings away from GitHub.copilot-chat",
      "Split high-trust automation settings between workspace and user scope"
    ],
    "active": false,
    "not_finished_all": true
  }
}
```
