---
type: handoff
from: codex
to: claude
created: 2026-05-15
updated: 2026-05-15
priority: high
scope: vscode-extension, git-visibility, local-ci
subject: FLUX VS Code extension visibility and Git source-visibility correction
---

# FLUX Visibility And Git Source-Visibility Correction

## Current Sync State For Claude

This is the active combined handoff. Do not create a parallel FLUX visibility note unless the installed extension version or lane architecture changes again.

There are two separate visibility lanes:

1. **VS Code extension UI visibility:** FLUX is installed globally in VS Code Insiders as `chthonic-archive.chthonic-archive@0.2.9`. The user-facing entry points are now the `FLUX Gate` Activity Bar view, `Chthonic FLUX: Verify Extension Presence`, startup notification, Command Palette commands, output channel, and status bar item.
2. **Git source visibility:** the repository uses an allowlist `.gitignore` beginning with `*`. New source lanes can exist on disk but remain invisible to Git and VS Code Source Control unless `.gitignore` re-opens their parent directories and file patterns. Codex added a CI guard and local pre-commit hook automation so this does not keep becoming a manual user burden.

Do not collapse these into "workspace vs global extension install." That diagnosis is wrong for the FLUX extension and incomplete for source-file visibility.

## Latest Update: Git Visibility Gate Sealed

Codex added the missing automation around the recurring `.gitignore` allowlist problem.

New commands:

```powershell
bun run ignore:audit
bun run ignore:audit:report
bun run ci/run.ts --check ignored-source
bun run hooks:precommit
bun run hooks:verify
```

Local commit path:

- `bun run ci:staged` now includes the `ignored-source` check.
- `.git/hooks/pre-commit` is installed and runs `ci/run.ts --staged`.
- VS Code / VS Code Insiders normal Commit button commits go through Git, so they run the pre-commit hook.
- `bun install` now runs `scripts/postinstall.ps1`, which refreshes the local pre-commit hook through `scripts/ensure-precommit-hook.ps1`.
- `bun run hooks:verify` confirms the active hook points at `ci/run.ts --staged`.

Important limit:

- Git still allows an explicit `git commit --no-verify` bypass. That is Git's intended escape hatch, not the normal IDE commit path.

Current verification:

```text
bun run hooks:precommit  PASS
bun run hooks:verify     PASS
bun run postinstall      PASS
bun run ci:staged        PASS
bun run ignore:audit     PASS
git diff --check         PASS
deletion preflight       no deletions
```

Source-visibility convention:

- Canonical doc: [docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md](../../docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md)
- CI check: [ci/checks/ignored-source.ts](../../ci/checks/ignored-source.ts)
- CI registry: [ci/run.ts](../../ci/run.ts)
- Hook verifier: [scripts/ensure-precommit-hook.ps1](../../scripts/ensure-precommit-hook.ps1)
- Postinstall refresher: [scripts/postinstall.ps1](../../scripts/postinstall.ps1)
- Hook source: [scripts/pre-commit-hook.sh](../../scripts/pre-commit-hook.sh)

Expected side effect:

- Many formerly hidden source files now appear as `??` in `git status --short --untracked-files=all`. That is desired. They were not created by the guard; they were made visible by repairing the allowlist.

## Superseding Update: Visibility Hardened

Codex implemented a stronger FLUX visibility surface after the user reported that the status bar entry was still not visible enough.

Current installed extension:

```text
chthonic-archive.chthonic-archive@0.2.9
```

New visibility contract:

- A visible `FLUX Gate` webview now appears under the Chthonic Archive Activity Bar container.
- `Chthonic FLUX: Verify Extension Presence` focuses the gate and pops a visible presence notification.
- Startup now shows `Chthonic FLUX is active (v0.2.9).` with actions: `Open Panel`, `Show FLUX Gate`, and `Show Output`.
- The status bar item remains, but it is no longer the only verification surface.

Primary user instruction now:

```text
Reload VS Code Insiders. A notification should say `Chthonic FLUX is active (v0.2.9).` Click `Show FLUX Gate` or run `Chthonic FLUX: Verify Extension Presence` from the Command Palette. The Chthonic Activity Bar will contain a `FLUX Gate` view with Open Panel, Verify, Start Backend, Stop Backend, and Output buttons.
```

## Correction

The FLUX extension visibility issue is not a workspace-vs-global install problem.

`code-insiders --install-extension` installs the VSIX into the user extension root:

`C:\Users\eldno\.vscode-insiders\extensions\chthonic-archive.chthonic-archive-0.2.9`

Local verification:

```powershell
code-insiders --list-extensions --show-versions | rg "chthonic-archive|vampire"
```

Observed:

```text
chthonic-archive.chthonic-archive@0.2.9
chthonic-archive.vampire-corpus@0.1.0
```

The VS Code extension detail panel showing `Source: VSIX`, a fresh update time, and activation timing means the extension is loaded. If the user sees `$(circle-outline) FLUX: idle` / `○ FLUX: idle` in the bottom-left status bar, that is still a valid entry point, but as of `0.2.9` the stronger entry point is the `FLUX Gate` view and verify command.

## Implementation Facts

Do not debug FLUX through the older `chthonic-vscode-extension/` scaffold. The current FLUX VSIX lives under `extensions/chthonic-archive/`.

## Actions Taken

### Extension Visibility

- Verified the installed VS Code Insiders extension identity with `code-insiders --list-extensions --show-versions`.
- Verified the installed extension root at `C:\Users\eldno\.vscode-insiders\extensions\chthonic-archive.chthonic-archive-0.2.9`.
- Traced FLUX visibility through package activation, command contribution, runtime status bar creation, and panel reveal code.
- Added a first-class `FLUX Gate` launcher view, verify command, output command, and startup presence notification.
- Packaged and installed the updated VSIX into VS Code Insiders.

### Git Source Visibility

- Added `ignored-source`, a CI check that scans managed roots for source-shaped files hidden by `.gitignore`.
- Registered `ignored-source` in `ci/run.ts`, including alias names `autoignore` and `gitignore`.
- Added `ignore:audit` and `ignore:audit:report` scripts in the root `package.json`.
- Expanded `.gitignore` allowlist rules for active source lanes: FLUX extension source, extension syntaxes/themes/icons, app lanes, MAS MCP libraries/tests, scripts subtrees, and root Rust source docs.
- Added `docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md` as the canonical convention.
- Added `scripts/ensure-precommit-hook.ps1` and `scripts/postinstall.ps1`.
- Updated `scripts/pre-commit-hook.sh` to document that it runs staged CI including `ignored-source`.
- Installed and verified the local `.git/hooks/pre-commit` hook.

## Files Changed

- Updated this combined handoff in place: `claude/mailbox/CODEX_HANDOFF_FLUX_VISIBILITY_STATUSBAR_2026_05_15.md`.
- Modified [extensions/chthonic-archive/package.json](../../extensions/chthonic-archive/package.json).
- Modified [extensions/chthonic-archive/src/flux/fluxService.ts](../../extensions/chthonic-archive/src/flux/fluxService.ts).
- Added [extensions/chthonic-archive/src/flux/fluxLauncherView.ts](../../extensions/chthonic-archive/src/flux/fluxLauncherView.ts).
- Rebuilt [extensions/chthonic-archive/dist/extension.js](../../extensions/chthonic-archive/dist/extension.js).
- Updated [.gitignore](../../.gitignore) to expose source lanes and keep generated outputs ignored.
- Added [ci/checks/ignored-source.ts](../../ci/checks/ignored-source.ts).
- Modified [ci/run.ts](../../ci/run.ts).
- Modified root [package.json](../../package.json).
- Modified [AGENT_COMMON.md](../../AGENT_COMMON.md).
- Added [docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md](../../docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md).
- Added [scripts/ensure-precommit-hook.ps1](../../scripts/ensure-precommit-hook.ps1).
- Added [scripts/postinstall.ps1](../../scripts/postinstall.ps1).
- Modified [scripts/pre-commit-hook.sh](../../scripts/pre-commit-hook.sh).

Relevant source files:

- [extensions/chthonic-archive/package.json](../../extensions/chthonic-archive/package.json)
- [extensions/chthonic-archive/src/extension.ts](../../extensions/chthonic-archive/src/extension.ts)
- [extensions/chthonic-archive/src/flux/fluxLauncherView.ts](../../extensions/chthonic-archive/src/flux/fluxLauncherView.ts)
- [extensions/chthonic-archive/src/flux/fluxService.ts](../../extensions/chthonic-archive/src/flux/fluxService.ts)
- [extensions/chthonic-archive/src/flux/fluxPanel.ts](../../extensions/chthonic-archive/src/flux/fluxPanel.ts)

Exact wiring:

- `package.json` activates on startup: `activationEvents: ["onStartupFinished"]`.
- `package.json` contributes command `chthonic.flux.openPanel` titled `Chthonic FLUX: Open Panel`.
- `src/extension.ts` imports `FluxService` and registers it in the activation lane: `new FluxService(context, outputChannel, workspaceRoot).register()`.
- `src/flux/fluxService.ts` creates the visible status bar item with `vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50)`.
- `src/flux/fluxService.ts` registers `chthonic.flux.verifyPresence`, `chthonic.flux.focusLauncher`, and `chthonic.flux.showOutput`.
- `src/flux/fluxLauncherView.ts` provides `chthonic.fluxLauncherView`, the Activity Bar `FLUX Gate` surface.
- The status item command is `chthonic.flux.openPanel`.
- The status item is explicitly shown with `this.statusBarItem.show()`.
- Idle text is `$(circle-outline) FLUX: idle`; running text is `$(zap) FLUX: running`.
- `src/flux/fluxPanel.ts` opens the panel with `vscode.window.createWebviewPanel(...)`.

## What To Tell The User

Use this wording:

```text
The extension is already installed globally in VS Code Insiders as `chthonic-archive.chthonic-archive@0.2.9`; this is not a workspace-extension visibility problem. Reload the VS Code Insiders window. You should get a visible `Chthonic FLUX is active (v0.2.9).` notification; click `Show FLUX Gate`, or run `Chthonic FLUX: Verify Extension Presence` from the Command Palette. The gate view also has Open Panel, Start Backend, Stop Backend, and Output buttons.

The separate Git visibility problem is also now guarded. `bun run ignore:audit` detects source files swallowed by the allowlist `.gitignore`, and normal VS Code Commit button commits run the pre-commit hook through `ci/run.ts --staged`, which includes `ignored-source`. Verify that hook with `bun run hooks:verify`.
```

## If Patching Visibility Elsewhere

Replicate this pattern:

1. Add a command contribution in `package.json`.
2. Ensure activation happens without requiring a hidden view interaction, usually `onStartupFinished`.
3. During `activate()`, instantiate the service and register commands.
4. Create a status bar item.
5. Set `statusBarItem.command` to the open-panel command.
6. Call `statusBarItem.show()`.
7. In the open command, create or reveal a `WebviewPanel`.

Do not tell the user to move the extension into the workspace. The installed-user-extension location is correct for `code-insiders --install-extension`.

## How To Verify

```powershell
code-insiders --list-extensions --show-versions | rg "chthonic-archive"
rg -n "chthonic.fluxLauncherView|chthonic.flux.verifyPresence|showPresenceOnStartup|FLUX Gate|Chthonic FLUX is active" extensions/chthonic-archive/package.json extensions/chthonic-archive/src/flux/fluxService.ts extensions/chthonic-archive/src/flux/fluxLauncherView.ts
bun run ignore:audit
bun run ci/run.ts --check ignored-source
bun run hooks:verify
```

## Tests

- `bun run compile` passed in `extensions/chthonic-archive`.
- `bunx @vscode/vsce package --pre-release --no-dependencies --out chthonic-archive-flux.vsix --skip-license` passed.
- `code-insiders --install-extension extensions/chthonic-archive/chthonic-archive-flux.vsix --force` installed successfully.
- `code-insiders --list-extensions --show-versions | rg "chthonic-archive"` returned `chthonic-archive.chthonic-archive@0.2.9`.
- `bun run ignore:audit` passed.
- `bun run ci/run.ts --check ignored-source` passed.
- `bun run hooks:precommit` passed.
- `bun run hooks:verify` passed.
- `bun run postinstall` passed.
- `bun run ci:staged` passed.
- `uv run scripts/link_audit.py check docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md --dry-run` passed.
- `uv run scripts/link_audit.py check AGENT_COMMON.md --dry-run` passed.

## Next Actions

- Tell the user to reload the VS Code Insiders window so the active extension host picks up `0.2.9`.
- When responding to the user, point them first to `Chthonic FLUX: Verify Extension Presence` and the `FLUX Gate` view, not only the bottom-left status bar entry.
- When responding about files not appearing in Source Control, run `bun run ignore:audit` and `git check-ignore -v <path>` before proposing manual Git fixes.
- Do not ask the user to remember recurring `.gitignore` latch rules. The repo now carries the convention, CI check, and pre-commit hook automation.
- If patching another extension, replicate the command-plus-status-bar-plus-webview-panel pattern listed above.
- Do not recommend moving the installed VSIX into the workspace.
