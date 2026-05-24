# Codex IDE Slash Command Parity — Blueprint

> How CLI-only slash commands were reverse-engineered into the Codex IDE extension.

## Problem

Codex CLI exposes ~25 slash commands (`/plan`, `/model`, `/agent`, `/diff`, etc.).
The IDE extension only surfaces ~18 via its webview bundle. The missing commands flash blank
when attempted because the webview has no handler — the menu selects, fires into nothing, and
the input field resets.

## Architecture (Reverse-Engineered)

```
┌──────────────────────────────────────────────────────────────┐
│ Webview (index-B5Tvu0Eq.js)                                 │
│                                                              │
│  OJ(e)  — useProvideSlashCommand hook (React)                │
│           Registers a command: {id, title, Content, onSelect}│
│           Stored in a shared Map keyed by id                 │
│                                                              │
│  MJ(e,t) — buildSlashCommandList()                           │
│           Reads OJ registry, applies aliases via a() helper, │
│           deduplicates by id + title, returns sorted array   │
│                                                              │
│  a(src, newId, title, desc) — alias helper inside MJ         │
│           Clones from OJ registry: spreads onSelect/Content  │
│           Source MUST exist or alias is silently skipped      │
│                                                              │
│  I.dispatchMessage(type, data) — webview→extension bridge    │
│           Singleton from logger-DeWf6XmT.js                  │
│           Uses acquireVsCodeApi().postMessage({...data,type}) │
│           113 call sites in the main bundle                  │
└──────────────┬───────────────────────────────────────────────┘
               │ postMessage
               ▼
┌──────────────────────────────────────────────────────────────┐
│ Extension Host (extension.js)                                │
│                                                              │
│  handleMessage(e, r) — switch on r.type:                     │
│                                                              │
│    "open-vscode-command"                                     │
│      → vscode.commands.executeCommand(r.command, ...r.args)  │
│      (universal bridge to any registered VS Code command)    │
│                                                              │
│    "show-settings"                                           │
│      → this.showSettings({section: r.section})               │
│      Known sections: "agent", "mcp-settings", "skills-settings", "model" │
│                                                              │
│    "show-diff"         → diff panel                          │
│    "show-plan-summary" → plan summary panel                  │
│    "codex-app-server-restart" → reloadWindow                 │
│    + 50 more message types                                   │
│                                                              │
│  19 codex.command.* registrations:                           │
│    newThread, settings, toggleDiffPanel, findInThread,       │
│    toggleTerminal, toggleSidebar, openSkills, manageTasks,   │
│    mcpSettings, personalitySettings, feedback, logOut,       │
│    navigateBack, navigateForward, nextThread, previousThread,│
│    openFolder, openThreadOverlay, forceReloadSkills          │
└──────────────────────────────────────────────────────────────┘
```

## Patch Strategy (v2)

Two injection vectors, both inside `MJ()`:

### 1. Aliases via `a()` helper
Clone existing OJ-registered commands under new names. These inherit the full
`onSelect`/`Content` behavior of the source — zero custom dispatch needed.

| Alias       | Source OJ ID         |
|-------------|----------------------|
| `/plan`     | `plan-mode`          |
| `/review`   | `review-mode`        |
| `/fast`     | `speed`              |
| `/new`      | `hotkey-window-new`  |
| `/resume`   | `hotkey-window-resume`|
| `/statusline`| `status`            |
| `/collab`   | `personality`        |
| `/bug-report`| `feedback`          |

### 2. Direct entries via `I.dispatchMessage()`
For commands without an OJ registration, inject objects directly into the
command list, with `onSelect` calling the real webview→extension bridge.

| Command     | Dispatch                                       |
|-------------|------------------------------------------------|
| `/model`    | `show-settings` → `{section: "model"}`         |
| `/clear`    | `open-vscode-command` → `codex.command.newThread` |
| `/diff`     | `open-vscode-command` → `codex.command.toggleDiffPanel` |
| `/agent`    | `show-settings` → `{section: "agent"}`         |
| `/find`     | `open-vscode-command` → `codex.command.findInThread` |
| `/terminal` | `open-vscode-command` → `codex.command.toggleTerminal` |
| `/skills`   | `open-vscode-command` → `codex.command.openSkills` |
| `/tasks`    | `open-vscode-command` → `codex.command.manageTasks` |

### Why v1 Failed

v1 used `CustomEvent("codex:slash")` dispatched on the DOM. Nothing in the
extension listens for that event — the handler only exists in CLI mode. The
`/agent` alias also targeted `subagents`, which was never OJ-registered, so
the `a()` helper silently dropped it.

## File Inventory

| File                       | Purpose                              |
|----------------------------|--------------------------------------|
| `codex-toolkit.ps1`       | **Entry point** — routes to patch/restore/audit/parity/status |
| `audit-bundle.ps1`        | **Unified audit** — quick, `-Deep`, or `-Parity` modes |
| `patch-slash-parity.ps1`  | **Apply/restore/dry-run the v2 patch** — the main tool |
| `restructure-codex.ps1`   | Housekeeping: move codex/ folder files into canonical subdirs |
| `run-codex-polisher.ps1`  | Run skill-polisher against `.codex/skills/` and emit mailbox artifacts |
| `slash-audit.ps1`         | *(deprecated — use audit-bundle.ps1)* |
| `slash-deep-audit.ps1`    | *(deprecated — use audit-bundle.ps1)* |

## Usage

```powershell
# Quick status check
.\scripts\codex\codex-toolkit.ps1 status

# Dry run — see what would change
.\scripts\codex\codex-toolkit.ps1 patch -DryRun

# Apply the patch (creates .bak backup on first run)
.\scripts\codex\codex-toolkit.ps1 patch

# Restore original bundle
.\scripts\codex\codex-toolkit.ps1 restore

# Quick audit of current bundle
.\scripts\codex\codex-toolkit.ps1 audit

# Deep audit — full OJ/MJ extraction, all commands, dispatch types
.\scripts\codex\codex-toolkit.ps1 audit -Deep

# Parity check — coverage matrix + gaps
.\scripts\codex\codex-toolkit.ps1 parity
```

After patching: `Ctrl+Shift+P` → `Developer: Reload Window`.

## Extending

To add a new slash command:

1. **If an OJ source exists**: Add an `a()` alias call in the `$replacement` here-string.
   Format: `a(\`sourceId\`,\`newId\`,\`Title\`,\`Description\`);`

2. **If no OJ source**: Add a direct entry to the `_pi` object.
   - For VS Code commands: `I.dispatchMessage(\`open-vscode-command\`,{command:\`codex.command.XXX\`})`
   - For settings panels: `I.dispatchMessage(\`show-settings\`,{section:\`XXX\`})`
   - For protocol messages: `I.dispatchMessage(\`message-type\`,{...data})`

3. Run `codex-toolkit.ps1 audit -Deep` to find available OJ IDs and `codex.command.*` names.
   Run `codex-toolkit.ps1 parity` to check what's still unexploited.

## Version Pinning

The patch targets bundle hash `B5Tvu0Eq` in extension version `26.5313.41514`.
When Codex updates, the bundle filename changes. The audit scripts will fail to
find the file — that's the signal to re-locate the new bundle and update the
`$bundlePath` in each script (or parameterize it).

## Parity Matrix

Full inventory of every slash command surface, current coverage, and status.

### OJ-Registered Commands (18 native)

These are registered via `useProvideSlashCommand` hooks in the webview bundle.
They have full `onSelect`/`Content` handlers and work natively.

| OJ ID                         | Title (resolved)    | Has Content? | Notes |
|-------------------------------|---------------------|-------------|-------|
| `local`                       | Local               | Yes         | Environment selector |
| `worktree`                    | Worktree            | Yes         | Environment selector |
| `cloud`                       | Cloud               | Yes         | Environment selector |
| `cloud-environment`           | Cloud Environment   | Yes         | Environment selector |
| `hotkey-window-new`           | New Window          | Yes         | Hotkey window launcher |
| `hotkey-window-resume`        | Resume Window       | Yes         | Hotkey window picker |
| `hotkey-window-select-project`| Select Project      | Yes         | Hotkey window project |
| `composer.slashCommands.skillsGroup` | Skills Group | Yes         | Skills group header |
| `composer.forkSlashCommand.*` | Fork (worktree)     | Yes         | Fork thread as worktree |
| `composer.ideContextSlashCommand.*` | IDE Context   | Yes         | IDE context injection |
| `ide-context`                 | IDE Context         | Yes         | Variable-based registration |
| `composer.mcpStatus.*`        | MCP Status          | Yes         | MCP status display |
| `personality`                 | Personality         | Yes         | Collaboration mode |
| `plan-mode`                   | Plan Mode           | Yes         | Toggle plan/act |
| `review-mode`                 | Review Mode         | Yes         | Code review mode |
| `speed`                       | Speed               | Yes         | Fast/quality toggle |
| `status`                      | Status              | Yes         | Session status |
| `feedback`                    | Feedback            | Yes         | Bug report / feedback |

### v2 Patch Aliases (8 added)

Cloned from OJ via `a()` helper. Inherit full `onSelect`/`Content`.

| Slash Command | Source OJ ID         | Status |
|---------------|----------------------|--------|
| `/plan`       | `plan-mode`          | **LIVE** |
| `/review`     | `review-mode`        | **LIVE** |
| `/fast`       | `speed`              | **LIVE** |
| `/new`        | `hotkey-window-new`  | **LIVE** |
| `/resume`     | `hotkey-window-resume`| **LIVE** |
| `/statusline` | `status`             | **LIVE** |
| `/collab`     | `personality`        | **LIVE** |
| `/bug-report` | `feedback`           | **LIVE** |

### v2 Patch Direct Entries (8 added)

Injected with `I.dispatchMessage()` bridge calls. No OJ source needed.

| Slash Command | Dispatch Type         | Target                          | Status |
|---------------|-----------------------|---------------------------------|--------|
| `/model`      | `show-settings`       | `{section: "model"}`            | **LIVE** |
| `/clear`      | `open-vscode-command` | `codex.command.newThread`       | **LIVE** |
| `/diff`       | `open-vscode-command` | `codex.command.toggleDiffPanel` | **LIVE** |
| `/agent`      | `show-settings`       | `{section: "agent"}`            | **LIVE** |
| `/find`       | `open-vscode-command` | `codex.command.findInThread`    | **LIVE** |
| `/terminal`   | `open-vscode-command` | `codex.command.toggleTerminal`  | **LIVE** |
| `/skills`     | `open-vscode-command` | `codex.command.openSkills`      | **LIVE** |
| `/tasks`      | `open-vscode-command` | `codex.command.manageTasks`     | **LIVE** |

### Unexploited codex.command.* (Not Yet Exposed as Slash Commands)

These VS Code commands exist and are callable via `open-vscode-command` but
have no slash command surface yet.

| Command                           | Potential Slash   | Notes |
|-----------------------------------|-------------------|-------|
| `codex.command.settings`          | `/settings`       | Opens full settings panel |
| `codex.command.mcpSettings`       | `/mcp`            | MCP server configuration |
| `codex.command.personalitySettings`| `/personality`   | Personality settings (deeper than `/collab`) |
| `codex.command.toggleSidebar`     | `/sidebar`        | Toggle sidebar panel |
| `codex.command.openThreadOverlay` | `/threads`        | Thread overlay / picker |
| `codex.command.navigateBack`      | `/back`           | Navigate history back |
| `codex.command.navigateForward`   | `/forward`        | Navigate history forward |
| `codex.command.nextThread`        | `/next`           | Jump to next thread |
| `codex.command.previousThread`    | `/prev`           | Jump to previous thread |
| `codex.command.openFolder`        | `/folder`         | Open workspace folder |
| `codex.command.forceReloadSkills` | `/reload-skills`  | Force refresh skills |
| `codex.command.logOut`            | `/logout`         | Log out of Codex |

### Unexploited show-settings Sections

| Section           | Potential Slash | Notes |
|-------------------|-----------------|-------|
| `mcp-settings`    | `/mcp`          | MCP server panel |
| `skills-settings` | `/skills-config`| Skills settings (vs `/skills` which opens browser) |

### Unexploited dispatchMessage Types (High-Value)

These extension host message types could power new slash commands:

| Message Type             | Potential Slash    | Notes |
|--------------------------|--------------------|-----------------------------|
| `show-diff`              | —                  | Already covered by `/diff` via command |
| `show-plan-summary`      | `/plan-summary`    | Show plan summary panel |
| `codex-app-server-restart` | `/restart`       | Reload VS Code window |
| `open-config-toml`       | `/config`          | Open config.toml in editor |
| `open-extension-settings`| `/ext-settings`    | VS Code extension settings |
| `open-keyboard-shortcuts`| `/keys`            | Keyboard shortcuts panel |
| `export-logs`            | `/export-logs`     | Export debug logs |
| `open-debug-window`      | `/debug`           | Open debug window |
| `toggle-trace-recording` | `/trace`           | Toggle trace recording |
| `subagent-thread-opened` | —                  | Subagent navigation (read-only) |

### Thread-Follower Protocol Actions (Advanced)

These are bidirectional protocol messages between webview and app-server.
Could theoretically be triggered as slash commands but require proper state.

| Action                            | Potential Use |
|-----------------------------------|---------------|
| `interrupt-turn-request`          | `/stop` — interrupt current turn |
| `edit-last-user-turn-request`     | `/edit` — edit last message |
| `set-model-and-reasoning-request` | `/model` — already covered via settings |
| `set-collaboration-mode-request`  | `/collab` — already covered via alias |
| `set-queued-follow-ups-state-request` | `/queue` — manage follow-up queue |
| `steer-turn-request`              | `/steer` — redirect current turn |

### CLI-Only Commands (No IDE Equivalent Found)

These exist in Codex CLI REPL but have no webview/extension equivalent:

| CLI Command    | Status    | Notes |
|----------------|-----------|-------|
| `/compact`     | **GAP**   | Context compaction — server-initiated only (`context-compaction` protocol), no client trigger found |
| `/undo`        | **GAP**   | Undo last change — `codex/event/undo_started` exists in telemetry but no command surface |
| `/history`     | **GAP**   | No equivalent — thread overlay is closest proxy |
| `/rename`      | **GAP**   | Rename thread — `thread/name/updated` protocol exists but no trigger |

## Summary Stats

| Category | Count |
|----------|-------|
| OJ-registered (native) | 18 |
| v2 aliases (patched) | 8 |
| v2 direct entries (patched) | 8 |
| **Total slash commands available** | **34** |
| Unexploited codex.command.* | 12 |
| Unexploited dispatch types | ~8 |
| CLI-only with no IDE path | 4 |

## Key Files in the Extension

```
webview/assets/
  index-B5Tvu0Eq.js          — Main webview bundle (3.8MB, patched)
  index-B5Tvu0Eq.js.bak      — Original backup
  logger-DeWf6XmT.js         — VS Code API bridge (acquireVsCodeApi singleton)
  app-scope-DIqwQRLP.js      — Command registry (19 codex.command.* definitions)
  app-server-manager-hooks-CqIYwVRX.js — Protocol handler (197 case labels)
extension.js                  — Extension host (handleMessage: 90+ case labels, 57 dispatchMessage types)
```

---

## Baseline Snapshot — 2026-03-17

Complete halted-state inventory across **every Codex surface** — extension
install, workspace config, workspace session data, and Win11 user-level state.
Everything below captures the exact working configuration so this lanework can
resume from any point without re-discovery.

---

### 1. Extension Install (`openai.chatgpt-26.5313.41514-win32-x64`)

Only version installed. No VS Code global storage for this extension — all
persistent state lives in `~/.codex/`.

| Property | Value |
|----------|-------|
| Extension ID | `openai.chatgpt-26.5313.41514-win32-x64` |
| CLI binary | `bin\codex.exe` (155 MB) + `bin\codex` Linux (133 MB) |
| CLI version | Codex CLI 0.115.0-alpha.27 |
| Bundle (patched) | `index-B5Tvu0Eq.js` — 3,863,389 bytes |
| Bundle (original backup) | `index-B5Tvu0Eq.js.bak` — 3,861,492 bytes |
| Patch delta | +1,897 bytes (v2 aliases + direct dispatch entries) |
| Extension host | `out\extension.js` — 1,285,642 bytes |
| VS Code Insiders | 1.112.0-insider |
| Patch status | **v2 active** |

**Extension directory structure:**

| Subdir | Files | Size | Contents |
|--------|-------|------|----------|
| `bin/` | 6 | 286.3 MB | codex.exe (155 MB), codex Linux (133 MB), rg.exe (4.3 MB), rg Linux (5.4 MB), codex-command-runner.exe (670 KB), codex-windows-sandbox-setup.exe (709 KB) |
| `webview/` | 1,245 | 92.9 MB | Bundled Vite app (index-*.js, assets, fonts, source maps) |
| `out/` | 1 | 1.2 MB | extension.js (extension host) |
| `resources/` | 7 | — | Icons, manifests |
| `syntaxes/` | 3 | — | TextMate grammars |
| Root | 4 | — | .vsixmanifest, LICENSE.md, package.json (6,928 B), readme.md |

### 2. Bundle Hash Registry

All filenames are content-hashed. When the extension updates, these change:

| File | Hash | Size |
|------|------|------|
| `index-B5Tvu0Eq.js` | `B5Tvu0Eq` | 3.8 MB |
| `logger-DeWf6XmT.js` | `DeWf6XmT` | 2,295 B |
| `app-scope-DIqwQRLP.js` | `DIqwQRLP` | 127,856 B |
| `app-server-manager-hooks-CqIYwVRX.js` | `CqIYwVRX` | 270,374 B |
| `index-DHcKUmEn.css` | `DHcKUmEn` | 330,536 B |

### 3. VS Code Settings (Codex-specific)

**Global** (`settings.json`):
```json
"chatgpt.cliExecutable": "...\\openai.chatgpt-26.5313.41514-win32-x64\\bin\\windows-x86_64\\codex.exe",
"chatgpt.openOnStartup": true,
"chatgpt.localeOverride": ""
```

**Workspace** (`.vscode/settings.json`):
```json
"chatgpt.commentCodeLensEnabled": true,
"chatgpt.openOnStartup": true,
"chatgpt.composerEnterBehavior": "cmdIfMultiline"
// "chatgpt.thinkingMode": "xhigh"  (commented out)
```

Codex CLI binary is also on `PATH` via workspace terminal env.

---

### 4. `.codex/` — Workspace Config (222 files)

**Root files:**

| File | Size | Purpose |
|------|------|---------|
| `config.toml` | 1,501 B | Model=gpt-5.4, approval=never, sandbox=workspace-write, context_window=1,050,000, auto_compact=900,000, reasoning=**xhigh** |
| `instructions.md` | 4,347 B | Codex agent behavioral rules |
| `sfs_reference_index.py` | 24,278 B | SFS reference index |
| `.gitignore` | 6,057 B | Ignore patterns |

MCP servers in workspace config: `github`, `openaiDeveloperDocs`, `hf-mcp-server`.

**Subdirectories:**

| Directory | Files | Contents |
|-----------|-------|----------|
| `skills/` | 211 | 28 skill directories (see breakdown below) |
| `mailbox/` | 1 | `.gitkeep` only (workspace-level agent handoff lane) |
| `codekiller_DUMP_code/` | 2 | `codekiller_remediation_gate.py` (21 KB), `SESSION_HANDOFF_CODEKILLER_STRUCTURAL_AUDIT.md` (8.6 KB) |
| `lane_WPTG_wet_paper_to_gold_abstraction_task/` | 2 | Implementation blueprint (14.6 KB), poe-preview.html (65.6 KB) |
| `visualStudioInstaller2006/` | 3 | SSMS22.vsconfig, VS2026-Buildtools.vsconfig, VS2026-Pro-Insiders.vsconfig |

**Filetype breakdown (222 files total):**
60 `.md`, 59 `.svg`, 30 `.yaml`, 28 `.py`, 13 `.json`, 9 `.txt`, 8 `.pyc`,
7 `.png`, 3 `.vsconfig`, 2 `.toml`, 1 `.gitignore`, 1 `.gitkeep`, 1 `.html`.

**`.codex/skills/` — 28 workspace skill directories:**

| Skill | Files | | Skill | Files |
|-------|-------|-|-------|-------|
| skill-polisher | 28 | | .system | 18 |
| sora | 15 | | imagegen | 12 |
| artifact-upcycle | 12 | | trainstop-orchestrator | 10 |
| codekiller | 9 | | script-envelope | 8 |
| conceptualize | 8 | | ironmaiden-merge | 8 |
| decision-razor | 7 | | gh-mcp-autonomy | 7 |
| chatgpt-apps | 7 | | openai-docs | 7 |
| gh-address-comments | 6 | | gh-fix-ci | 6 |
| komplett-reklamasjon | 6 | | lane-wptg | 6 |
| mailbox-distill | 6 | | artcop | 5 |
| hf-explore | 5 | | memos | 5 |
| screenshot | 4 | | vscode-scalpel | 4 |
| insiders-matrix-eval | 4 | | harvest-skill | 4 |
| corpse-reviver | 3 | | forge-session-notes | 3 |

---

### 5. `codex/` — Workspace Session Data (738 files)

Working directory for Codex session logs, mailbox handoffs, and artifacts.

**Filetype breakdown (738 files total):**
332 `.log`, 223 `.md`, 134 `.json`, 18 `.txt`, 10 `.svg`, 5 `.dmp`, 5 `.vsconfig`,
4 `.yaml`, 3 `.csv`, 1 `.db`, 1 `.env`, 1 `.py`, 1 `.zip`.

**Top-level subdirectories:**

| Directory | Files | Contents |
|-----------|-------|----------|
| `artifacts/` | 6 | Creative session artifacts (haikus, bestiary, feature sketch, sigil, poem, desktop clone steps) |
| `codex-session-logs/` | 38 | 6 root files + `archive/` with 30 (MILF-Core docs, Iron Maiden SSOT, Gemini transcripts, session logs) |
| `mailbox/` | 690 | 177 root files + 25 subdirectories (see breakdown below) |
| `reports/` | 4 | Audit/status reports |

**`codex/NEXT.md`** (2,312 B) — current state waypoint:
- Documents 27 active skills (cap target: 15)
- Active chore: `CHORE_CODEBASE_HYGIENE_2026_03_09`
- 7 pending items: skill consolidation 27→≤15, mailbox rotation (294 files), scripts variant triage, scripts Phase 3, .pyc cleanup, root archaeology, forge dedup

**`codex/mailbox/` detail (690 files):**

*Root (177 files):* 97 `.md`, 58 `.json`, 13 `.log`, 5 `.vsconfig`, 2 `.txt`, 1 `.env`, 1 `.zip`.

*25 subdirectories:*

| Subdirectory | Files | | Subdirectory | Files |
|-------------|-------|-|-------------|-------|
| archive/ | 113 | | .tmp_fixture_eval/ | 19 |
| komplett_reklamasjon/ | 17 | | ACTUAL-WORKING-HANDOFFS/ | 7 |
| cache/ | 2 | | VSCODE_INSIDERS_MATRIX_* (×6) | ~10 each |
| VSCODE_TERMINAL_TRIAGE_* (×14) | 6–28 each | | | |

**Root-level files:**
- `codexfailsessionDUMP.md` (69,410 B) at repo root — session dump from a failed Codex run

---

### 6. `~/.codex/` — Win11 User-Level State (1,006 files, 1,328.7 MB)

Path: `C:\Users\eldno\.codex\`. All Codex persistent state lives here (no VS Code
global storage used by this extension).

**Root files:**

| File | Size | Purpose |
|------|------|---------|
| `state_5.sqlite` | 438 MB | Primary state database |
| `logs_1.sqlite` | 69 MB | Log database |
| `logs_1.sqlite-shm` | 32 KB | SQLite shared memory |
| `logs_1.sqlite-wal` | 4.2 MB | SQLite write-ahead log |
| `config.toml` | 1,427 B | Global config (see key differences below) |
| `instructions.md` | 2,302 B | User-level agent instructions |
| `AGENTS.md` | 1,745 B | Agent definitions |
| `auth.json` | 4,337 B | Authentication tokens |
| `models_cache.json` | 204 KB | Cached model list |
| `session_index.jsonl` | 4,363 B | Session index |
| `history.jsonl` | 86 B | Command history |
| `version.json` | 105 B | Version metadata |
| `cap_sid` | 275 B | Capability session ID |
| `sandbox.log` | 380 B | Sandbox log |
| `.personality_migration` | 3 B | Migration flag |

**Subdirectories:**

| Directory | Files | Size | Contents |
|-----------|-------|------|----------|
| `sessions/` | 38 | 653.2 MB | Active session data (largest by far) |
| `.sandbox-bin/` | 1 | 148.6 MB | Sandbox binary |
| `vendor_imports/` | 751 | 4.8 MB | Vendor library imports |
| `archived_sessions/` | 4 | 32 MB | Old session archives |
| `skills/` | 107 | — | 13 user-level skill directories |
| `tmp/` | 86 | — | Temporary files |
| `log/` | 1 | 1.7 MB | Runtime log |
| `.sandbox/` | 2 | — | Sandbox config |
| `.sandbox-secrets/` | 1 | — | Sandbox secrets |
| `memories/` | 0 | — | Empty (unused) |

**`~/.codex/skills/` — 13 user-level skill directories:**
`.system`, `artifact-upcycle`, `chatgpt-apps`, `conceptualize`, `decision-razor`,
`gh-address-comments`, `gh-fix-ci`, `gh-mcp-autonomy`, `imagegen`, `openai-docs`,
`script-envelope`, `skill-polisher`, `sora`.

**Key config difference — global vs workspace:**

| Setting | Global (`~/.codex/`) | Workspace (`.codex/`) |
|---------|---------------------|-----------------------|
| `model` | gpt-5.4 | gpt-5.4 |
| `model_reasoning_effort` | **low** | **xhigh** |
| `approval_mode` | never | never |
| `sandbox_permissions` | elevated | workspace-write |
| `context_window` | (default) | 1,050,000 |
| `auto_compact` | (default) | 900,000 |
| `multi_agent` | true | (not set) |
| `forced_login` | chatgpt | (not set) |
| MCP servers | github, openaiDeveloperDocs, hf-mcp-server | github, openaiDeveloperDocs, hf-mcp-server |

Reasoning `low` globally is intentional cost control — `xhigh` only inside this workspace.

---

### 7. `scripts/codex/` Inventory (Final)

| File | Lines | Purpose |
|------|-------|---------|
| `BLUEPRINT.md` | 500+ | This document — full architecture + parity matrix + baseline |
| `codex-toolkit.ps1` | ~75 | Entry point: `status`, `patch`, `restore`, `audit`, `parity` |
| `audit-bundle.ps1` | ~140 | Unified bundle audit (quick / `-Deep` / `-Parity`) |
| `patch-slash-parity.ps1` | ~140 | v2 patch apply/restore/dry-run with backup |
| `restructure-codex.ps1` | ~40 | Codex folder housekeeping |
| `run-codex-polisher.ps1` | ~60 | Skill polisher runner |

---

### 8. What Works Right Now

1. **34 slash commands** in the Codex IDE composer — 18 native + 16 patched
2. `codex-toolkit.ps1 status` — instant health check
3. `codex-toolkit.ps1 parity` — live parity matrix vs unexploited surfaces
4. `codex-toolkit.ps1 audit -Deep` — full extraction of OJ/MJ/commands/dispatch
5. `codex-toolkit.ps1 patch` — re-apply after extension updates (needs hash update)
6. `codex-toolkit.ps1 restore` — revert to original bundle

### 9. What's Halted / Available to Pick Up

| Lane | State | Effort | Notes |
|------|-------|--------|-------|
| **More slash commands** | Mapped, not implemented | Low | 11 `codex.command.*` + 2 settings sections ready to wire |
| **CLI-only gaps** | Analyzed, no path found | High | `/compact`, `/undo`, `/history`, `/rename` — need protocol-level injection |
| **Thread-follower actions** | 24 actions cataloged | Medium | Could expose `/stop`, `/edit`, `/steer` via protocol |
| **Auto hash detection** | Not started | Low | Replace hardcoded `B5Tvu0Eq` with glob for `index-*.js` |
| **Extension update resilience** | Manual only | Medium | Detect new bundle hash, re-apply patch automatically |
| **Source map exploitation** | Maps present, unused | Medium | `.js.map` files could deobfuscate for cleaner patches |
| **Skill consolidation** | Pending (codex/NEXT.md) | Medium | 28 workspace skills → target ≤15; 13 user-level skills shared |
| **Mailbox rotation** | Pending (codex/NEXT.md) | Low | 294+ files flagged for archive/cleanup |

### 10. Resume Checklist

When returning to this lanework:

1. Run `codex-toolkit.ps1 status` — confirms patch state
2. If extension updated: find new `index-*.js` hash, update `$bundlePath` in `audit-bundle.ps1` + `patch-slash-parity.ps1`, re-run patch
3. Run `codex-toolkit.ps1 parity` — see what's still unexploited
4. Pick a lane from "Halted" table above
5. `codex-toolkit.ps1 audit -Deep` for raw data if needed
6. Check `codex/NEXT.md` for pending hygiene chores
7. Review `~/.codex/state_5.sqlite` size (438 MB at snapshot) — may need pruning
