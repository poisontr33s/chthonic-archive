# VS Code Settings Modernization Research

- Generated: 2026-06-17
- Workspace: `C:\Users\eldno\chthonic-archive`
- VS Code Insiders: `1.126.0-insider`
- Commit: `226cd5d573076e1d3b260d21409538fbc67cb059`
- Research mode: no settings mutation

## Purpose

This is the prerequisite research pass before sequencing modernization. The intent is direct and practical: make the current VS Code Insiders workspace/user settings match current VS Code, Copilot, Codex, and Claude Code behavior without preserving stale beta workarounds or introducing unnecessary abstraction.

Modernization here means:

- Use the current setting key when VS Code Insiders recognizes it.
- Keep valid current settings even if they look unusual.
- Remove misspelled or unsupported settings.
- De-duplicate user/workspace settings when duplication creates confusion.
- Probe behavior-affecting changes with a restart and Output-log comparison.

## Sources Consulted

Official VS Code documentation:

- User/workspace settings: `https://code.visualstudio.com/docs/configure/settings`
- Default settings reference: `https://code.visualstudio.com/docs/reference/default-settings`
- AI settings reference: `https://code.visualstudio.com/docs/agents/reference/ai-settings`
- Chat tools: `https://code.visualstudio.com/docs/chat/chat-tools`
- MCP servers: `https://code.visualstudio.com/docs/agent-customization/mcp-servers`
- AI trust and safety: `https://code.visualstudio.com/docs/agents/concepts/trust-and-safety`
- AI features cheat sheet: `https://code.visualstudio.com/docs/agents/reference/ai-features-cheat-sheet`
- Terminal profiles: `https://code.visualstudio.com/docs/terminal/profiles`
- Profiles: `https://code.visualstudio.com/docs/configure/profiles`
- VS Code 1.99 release notes for `chat.tools.autoApprove`: `https://code.visualstudio.com/updates/v1_99`
- VS Code 1.103 release notes for `chat.tools.terminal.autoApprove`: `https://code.visualstudio.com/updates/v1_103`

Additional context used cautiously:

- GitHub issue evidence for Copilot fetcher diagnostics: `https://github.com/microsoft/vscode/issues/270050`
- Copilot network/fetcher community evidence, used only as troubleshooting context, not as policy.

Local evidence:

- `C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\226cd5d573\resources\app`
- `C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\226cd5d573\resources\app\extensions\copilot\package.json`
- `C:\Users\eldno\.vscode-insiders\extensions\openai.chatgpt-26.5609.30741-win32-x64\package.json`
- `C:\Users\eldno\.vscode-insiders\extensions\anthropic.claude-code-2.1.179-win32-x64\package.json`
- `C:\Users\eldno\.vscode-insiders\extensions\github.vscode-pull-request-github-0.151.2026061704\package.json`

## Confirmed Current Baseline

Installed VS Code:

- `1.126.0-insider`
- Commit: `226cd5d573076e1d3b260d21409538fbc67cb059`

Installed AI-relevant extensions:

- Built-in Copilot Chat: `0.54.2026061702`
- OpenAI Codex extension: `26.5609.30741`
- Claude Code extension: `2.1.179`
- GitHub Pull Requests: `0.151.2026061704`

Copilot Chat local manifest:

- Requires VS Code `^1.126.0`
- Requires Node `>=22.14.0`
- Uses modern dependency set including:
  - `@github/copilot`: `^1.0.63`
  - `@vscode/copilot-api`: `^0.4.3`
  - `@modelcontextprotocol/sdk`: `^1.25.2`
  - `undici`: `^7.24.1`
  - `@anthropic-ai/claude-agent-sdk`: `0.2.112`

Interpretation:

- The local Copilot stack is current and no longer resembles the older beta-era custom SDK assumptions.
- Settings that force old transport/fetch behavior deserve verification before being kept.

## Documentation Findings

### Settings Scope

VS Code stores settings in `settings.json`, and the Settings UI/JSON IntelliSense highlights invalid setting names and formatting issues. Extension settings are contributed by installed extensions and can be reviewed through the Settings editor or an extension's Feature Contributions.

Important security rule: settings that specify executables can be restricted to user settings rather than workspace settings. That matters for terminal profiles and tool executable paths.

Modernization implication:

- Appearance and general editor ergonomics should normally live in user settings.
- Workspace settings should only pin repo-specific behavior, trust boundaries, tools, MCP startup behavior, and workspace language defaults.
- Executable/path settings need extra care because VS Code restricts some executable settings at workspace scope for security.

### Default Settings Are the Ground Truth

The official default settings reference says to use `Preferences: Open Default Settings (JSON)` for the actual running build's complete defaults.

Modernization implication:

- Before renaming or removing ambiguous keys, verify the key in the current default settings JSON or Settings UI.
- Manifest scans are useful but incomplete because core settings are not all exposed through extension `package.json`.

### AI and Agent Settings Are Moving

The AI settings reference explicitly says VS Code AI features are actively evolving, and some are experimental.

Confirmed current documented concepts:

- Agent skills:
  - `chat.useAgentSkills`
  - `chat.agentSkillsLocations`
- Claude agent bypass:
  - `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`
  - Default is documented/local-manifest `false`
  - Documentation says this should only be enabled in isolated sandbox environments.
- Agent plugins:
  - `chat.plugins.enabled`
  - `chat.plugins.marketplaces`
  - `chat.plugins.enabledPlugins`
  - `chat.pluginLocations`
- Copilot virtual tools:
  - `github.copilot.chat.virtualTools.threshold`
  - Relevant when tool count exceeds 128.

Modernization implication:

- Keep skill/plugin/agent locations explicit only where needed.
- Do not treat all old `chat.*` settings as invalid just because they are missing from a package manifest.

### Tool Approval Names Changed From Older Local Assumptions

Current docs name:

- `chat.tools.autoApprove`
- `chat.tools.terminal.autoApprove`

Current user/workspace settings contain:

- `chat.tools.global.autoApprove`

Modernization implication:

- `chat.tools.global.autoApprove` must be checked in the current Default Settings JSON before changing.
- If absent there, migrate to the documented `chat.tools.autoApprove` only after one controlled restart comparison.
- The chronology should not rebuke global auto-approve as an intent. It should only verify whether the key name is current and whether user-scope inheritance is desired.

### MCP Auto Start Has a Doc/Local Mismatch

Official MCP docs name:

- `chat.mcp.autoStart`

This exact VS Code Insiders build contains local localization metadata for:

- `chat.mcp.autostart`
- `chat.mcp.autostart.never`
- `chat.mcp.autostart.newAndOutdated`
- `chat.mcp.autostart.onlyNew`

Current workspace setting:

- `chat.mcp.autostart`: `never`

Modernization implication:

- Do not blindly rename this yet.
- First check `Preferences: Open Default Settings (JSON)` or Settings IntelliSense inside the current running Insiders build.
- If both keys exist, prefer the key the Settings UI marks as current.
- If only `chat.mcp.autostart` exists locally, keep it despite docs using `autoStart`.
- The current workspace value `never` matches the performance intent; the only question is key spelling.

### Chat Terminal Tool Behavior

Current chat tools docs say:

- Agent terminal commands run through the integrated terminal.
- Terminal output location can be configured with `chat.tools.terminal.outputLocation`.
- Agents use the configured default terminal except `cmd`/`sh`, because those shells do not provide enough shell integration.
- There is a maximum of 128 tools per chat request unless tool selection/virtual tools reduce the active set.

Modernization implication:

- PowerShell as default terminal remains a reasonable Windows default for agent visibility.
- Bun/uv/rv/rvx/Rust tooling should be exposed through PATH/profiles/tasks, not by forcing shell replacements where VS Code agents lose shell integration.

## Local Extension Findings

### OpenAI Codex Extension

Local settings contributed:

- `chatgpt.commentCodeLensEnabled`
- `chatgpt.cliExecutable`
- `chatgpt.openOnStartup`
- `chatgpt.followUpQueueMode`
- `chatgpt.composerEnterBehavior`
- `chatgpt.reviewDelivery`
- `chatgpt.localeOverride`
- `chatgpt.runCodexInWindowsSubsystemForLinux`

Current relevant values:

- `chatgpt.openOnStartup`: `false`
- `chatgpt.composerEnterBehavior`: `cmdIfMultiline`
- `chatgpt.reviewDelivery`: `detached` in user settings

Interpretation:

- `chatgpt.openOnStartup=false` is modern and should stay; it directly reduces startup cascade.
- `chatgpt.composerEnterBehavior` and `chatgpt.reviewDelivery` are valid current extension settings.

### Copilot Fetcher Overrides

Local Copilot manifest contributes:

- `github.copilot.chat.nesFetcher`
  - enum: `electron-fetch`, `node-fetch`
  - no default shown in manifest extraction
- `github.copilot.chat.completionsFetcher`
  - enum: `electron-fetch`, `node-fetch`
  - no default shown in manifest extraction

Current values:

- Workspace: both forced to `node-fetch`
- User: both forced to `node-fetch`

Interpretation:

- These keys are valid, not typo noise.
- They are still probably beta-era overrides because modern Copilot includes current network dependencies such as `undici`.
- Modernization should probe removal in workspace first, then user, with Output-log comparison.

### Copilot Context Editing

Local Copilot manifest contributes:

- `github.copilot.chat.anthropic.contextEditing.mode`
  - enum: `off`, `clear-thinking`, `clear-tooluse`, `clear-both`
  - default: `off`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`
  - default: `false`
- `github.copilot.chat.responsesApiContextManagement.enabled`
  - default: `false`

Current values:

- `github.copilot.chat.anthropic.contextEditing.mode`: `clear-both`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`: `true`
- `github.copilot.chat.responsesApiContextManagement.enabled`: `true`

Interpretation:

- These are valid current keys.
- They are intentional frontier/permissive behavior, not stale syntax.
- They should be scoped deliberately rather than removed blindly.

### Claude Code Extension

Local Claude Code manifest contributes:

- `claudeCode.allowDangerouslySkipPermissions`

Description says bypass permissions mode is recommended only for sandboxes with no internet access.

Current values:

- Workspace: `true`
- User: `true`

Interpretation:

- Valid but high-trust.
- Decide whether this belongs globally. Safer modernization is workspace-only if this repo is the intended permissive environment.

## Research-Based Chronology

This is the corrected order. It is based on current documentation plus local installed build evidence, not on a conceptual reframe.

### Phase 0: Capture Running Defaults

Prerequisite before edits:

1. Open `Preferences: Open Default Settings (JSON)` in VS Code Insiders.
2. Search for these exact keys:
   - `chat.mcp.autostart`
   - `chat.mcp.autoStart`
   - `chat.tools.global.autoApprove`
   - `chat.tools.autoApprove`
   - `chat.tools.terminal.autoApprove`
   - `chat.agent.maxRequests`
   - `chat.useAgentSkills`
   - `chat.agentSkillsLocations`
3. Record which keys IntelliSense marks as valid in current workspace settings.

Expected outcome:

- Resolve the docs/local mismatch before renaming MCP or tool approval settings.

### Phase 1: Remove Proven Typo/Dead Setting

Candidate:

- `workbenchexperimental.cloudChanges.partialMatches.enabled`

Why first:

- It has no official evidence and no local evidence.
- It is syntactically suspicious.
- It should have no behavioral dependency.

Verification:

- Restart VS Code Insiders.
- Compare Output logs for unknown setting/config warnings.

### Phase 2: Preserve Startup-Cascade Wins

Keep:

- `chatgpt.openOnStartup=false`
- MCP auto-start disabled using whichever key Phase 0 proves current
- `chat.agent.maxRequests=100` unless Default Settings proves a better modern cap
- `diffEditor.maxComputationTime=5000`
- `editor.largeFileOptimizations=true`
- `editor.maxTokenizationLineLength=20000`

Why second:

- These are known improvements from the Output-log cleanup.

### Phase 3: Probe Copilot Fetcher Overrides

Candidate:

- `github.copilot.chat.nesFetcher`
- `github.copilot.chat.completionsFetcher`

Order:

1. Remove only from workspace settings.
2. Restart.
3. Compare Copilot Chat, Copilot Log, Renderer Output.
4. If clean, remove from user settings.

Why not first:

- Keys are valid and may have been added for a real network workaround.
- They should be tested as behavior, not deleted as invalid.

### Phase 4: Scope Split User vs Workspace

Move/prefer user settings for:

- Theme
- Icon theme
- Product icon theme
- Font/cursor/minimap/editor ergonomics
- Rich token/color customizations

Keep/prefer workspace settings for:

- Repo Git behavior
- MCP/tool startup behavior
- Chthonic extension behavior
- Rust analyzer/repo language behavior
- Workspace trust/autonomy choices

Why fourth:

- This reduces duplicated settings without changing behavior first.

### Phase 5: Trust Boundary Pass

Review:

- `chat.tools.global.autoApprove` or its current documented replacement
- `claudeCode.allowDangerouslySkipPermissions`
- `github.copilot.chat.claudeAgent.allowDangerouslySkipPermissions`

Order:

1. Decide if global permissive mode is intended.
2. If not, remove from user settings and keep only workspace-local.
3. Restart and verify no agent/tool workflow breaks.

Why fifth:

- These are valid but high-impact. They should be scoped after current key names are proven.

### Phase 6: Formatter Modernization

Review:

- Global `editor.defaultFormatter=GitHub.copilot-chat`
- `notebook.defaultFormatter=GitHub.copilot-chat`
- `[json] editor.defaultFormatter=GitHub.copilot-chat`
- `[html] editor.defaultFormatter=GitHub.copilot-chat`

Likely target:

- JSON/JSONC: `vscode.json-language-features`
- HTML/JS/TS: choose only after confirming desired formatter extension
- Notebook: remove Copilot default unless proven useful

Why last:

- Formatter changes affect day-to-day editing more than startup logs.

## Not Yet Done

No settings were changed in this research pass.

```json
{
  "tasks": {
    "research_prerequisite_complete": true,
    "settings_modernization_started": false,
    "still_not_finished": [
      "Open current Default Settings JSON and resolve chat.mcp/chat.tools key-name mismatch",
      "Remove or prove workbenchexperimental.cloudChanges.partialMatches.enabled",
      "Probe workspace-only removal of Copilot fetcher overrides",
      "Split duplicated user/workspace UI settings",
      "Scope high-trust automation settings deliberately",
      "Modernize formatter settings last"
    ],
    "active": false,
    "not_finished_all": true
  }
}
```
