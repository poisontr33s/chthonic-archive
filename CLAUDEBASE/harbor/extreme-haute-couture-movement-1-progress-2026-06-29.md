# The Extreme Haute Couture — Movement 1 Progress, 2026-06-29

This progress note covers only the VS Code couture substrate and marketplace extension lane.

## Current Gate

Gate N is complete enough to proceed.

Completed:

- official SDK catalog exists and refreshes through Bun
- unofficial substrate boundary is documented
- `scripts/mica-substrate.ps1` now has lifecycle commands
- current VS Code Insiders substrate verifies cleanly
- tracked marketplace extension package can build a VSIX

Committed base before the Claude Design quarantine batch:

```text
9ffc1077 Harden Movement 1 substrate ownership
```

## Substrate State

Command run:

```powershell
pwsh -NoProfile -Command "& './scripts/mica-substrate.ps1' -Verify | ConvertTo-Json -Depth 8"
```

Result:

```text
Ok: true
Version: 1.127.0-insider
Commit: 628f6de50e89b20c7688c66ac2923cce2862c1b0
Electron: 42.2.0
Chthonic main block: present
Chthonic main block count: 1
Vibrancy block: absent
Workbench substrate CSS link: present
Workbench substrate CSS link count: 1
Runtime URI: current
CSS URI: current
```

## Extension Package Baseline

Tracked package:

```text
extensions/chthonic-archive
```

Checks run:

```bash
bun run --cwd extensions/chthonic-archive insiders:kits:check
bun run --cwd extensions/chthonic-archive insiders:package
```

Result:

```text
VSCE resolved: 3.9.1
@vscode/test-web resolved: 0.0.80
Package output: chthonic-archive-insiders.vsix
VSIX contents: 275 files
VSIX size: 446.7 KB
Package command: passed
```

Preflight warnings observed during package:

```text
Codex Native Sandbox (Windows): warning
Solana Tool Suite Lane: warning
```

These warnings did not block packaging. They are outside the immediate marketplace package gate.

Derived candidate package:

```text
extensions/chthonic-themes
```

Checks run:

```bash
bun run --cwd extensions/chthonic-themes insiders:kits:check
bun run --cwd extensions/chthonic-themes insiders:package
```

Result:

```text
VSCE resolved: 3.9.2
Package output: chthonic-themes-insiders.vsix
VSIX contents: 241 files
VSIX size: 209.74 KB
Package command: passed
```

Important boundary:

`extensions/chthonic-themes` is currently untracked source. It should not be silently admitted wholesale. Treat it as a derived package candidate until there is a deliberate commit deciding whether it becomes part of Movement 1.

## SDK Alignment Result

The tracked full extension package tooling has been aligned with the root SDK catalog:

```text
@openai/agents: 0.12.0
@openai/codex-sdk: 0.142.3
@vscode/test-cli: 0.0.15
@vscode/test-electron: 3.0.0
@vscode/test-web: 0.0.81
@vscode/vsce: 3.9.2
openai: 6.45.0
```

Checks rerun after alignment:

```bash
bun run --cwd extensions/chthonic-archive insiders:kits:check
bun run --cwd extensions/chthonic-archive insiders:package
```

Result:

```text
VSCE resolved: 3.9.2
@vscode/test-web resolved: 0.0.81
Package output: chthonic-archive-insiders.vsix
VSIX contents: 275 files
VSIX size: 446.7 KB
Package command: passed
```

Bun blocked two official lifecycle scripts during install:

```text
@playwright/browser-chromium: install
@vscode/vsce-sign: postinstall
```

The package gate passed without trusting or running those scripts. Leave them untrusted unless a browser test or VSIX signing gate actually requires them.

## Latest-Stable Sync Result

Official Microsoft release endpoints checked on 2026-06-29:

```text
VS Code Stable: 1.126.0
VS Code Insiders: 1.127.0-insider
Local code-insiders: 1.127.0-insider
Local code-insiders commit: 628f6de50e89b20c7688c66ac2923cce2862c1b0
```

The tracked extension manifest is now synced to the current Stable floor while packaging against Insiders:

```text
engines.vscode: ^1.126.0
@types/vscode: ^1.125.0
```

The remaining tracked extension dev dependencies were moved to npm latest and verified with `bun outdated`:

```text
@types/node: ^26.0.1
markdown-it: ^14.2.0
typescript: ^6.0.3
```

Checks rerun after this stricter sync:

```bash
bun outdated
bun run --cwd extensions/chthonic-archive insiders:kits:check
bun run --cwd extensions/chthonic-archive insiders:package
```

Result:

```text
Tracked extension outdated packages: none
VSCE resolved: 3.9.2
@vscode/test-web resolved: 0.0.81
Package output: chthonic-archive-insiders.vsix
VSIX contents: 275 files
VSIX size: 446.7 KB
Package command: passed
```

## Couture Gate Result

Single lane command added:

```bash
bun run couture:gate
```

Gate report:

```text
manifest/extreme-haute-couture-movement-1-gate.json
```

Scope covered:

```text
Official Stable release: 1.126.0
Official Insiders release: 1.127.0-insider
Local code-insiders: 1.127.0-insider
Local code-insiders commit: 628f6de50e89b20c7688c66ac2923cce2862c1b0
Tracked extension engines.vscode: ^1.126.0
Tracked extension @types/vscode: ^1.125.0
Root SDK catalog: present
Tracked extension outdated packages: none
Substrate verification: passed
Color theme contributions: 4
File icon theme definitions: 99
Product icon definitions: 115
Product icon fonts: 1
VSCE resolved: 3.9.2
@vscode/test-web resolved: 0.0.81
Package output: chthonic-archive-insiders.vsix
Package bytes: 457425
Extension-host E2E: archive/statusbar/mandala passed
```

This is now the Movement 1 deterministic runtime/visual gate. Use it before promoting material-surface changes.

## Claude Design Quarantine

Notification observed after Insiders reload:

```text
command 'claudeDesign.runeAction' not found
```

Cause:

```text
Installed stale extension: claude-design.claude-design@0.1.0
Rune status item command: claudeDesign.runeAction
Registered command: absent
Existing safe target: claudeDesign.openBestiary
```

Resolution added:

```text
scripts/claude-design-quarantine.ps1
manifest/claude-design-quarantine.json
```

The quarantine script patches the installed bundle idempotently by registering `claudeDesign.runeAction` as a bridge to `claudeDesign.openBestiary`, with a backup under:

```text
CLAUDEBASE/hold/claude-design-quarantine/backups/
```

The couture gate now checks both:

```text
claudeDesign.substrate.enabled=false in .vscode/settings.json
claudeDesign.runeAction is registered if the stale Claude Design extension is installed
```

The VS Code Insiders "installation appears to be corrupt" notification is expected for this lane because substrate injection modifies the local Insiders app files. Treat it as known collateral for the patched-substrate architecture, not as a Movement 1 blocker, while `scripts/mica-substrate.ps1 -Verify` and `bun run couture:gate` pass.

Reload diagnosis result:

```text
Claude Design stale main/CSS blocks were present after reload.
scripts/mica-substrate.ps1 -Apply stripped them and restored one Chthonic main block plus one workbench CSS link.
scripts/mica-substrate.ps1 -Verify passed.
bun run couture:gate passed with Claude Design quarantine checks included.
```

## Material Surface Pass 1

Files changed:

```text
designs/chthonic-mica.cjs
designs/vibrancy-obsidian.css
manifest/extreme-haute-couture-movement-1-gate.json
```

Runtime pass:

```text
Mica material selection now normalizes aliases such as mica-alt and mica-tabbed.
Window application is idempotent per BrowserWindow.
Runtime no-ops outside Windows and against destroyed or unsupported windows.
ready-to-show receives a second guarded application hook for newly created windows.
```

Surface pass:

```text
Workbench depth variables added under .monaco-workbench.
Activity bar, sidebars, panel, editor field, tabs, list rows, quick input, notifications, menus, find/suggest widgets, breadcrumbs, status bar, and title bar now share one depth map.
Color remains sourced from VS Code theme tokens; this pass only controls opacity and depth.
```

Gate rerun:

```bash
bun run couture:gate
```

Result:

```text
Status: passed
Generated: 2026-06-29T01:30:20.999Z
Stable: 1.126.0
Insiders: 1.127.0-insider
Substrate verification: passed
Package output: chthonic-archive-insiders.vsix
Package bytes: 457425
Extension-host E2E: archive/statusbar/mandala passed
```

## Notification Diagnosis

Observed after restart:

```text
Claude Design: Mica substrate patched into VS Code Insiders. Reload Insiders to activate it.
Your Code - Insiders installation appears to be corrupt. Please reinstall.
```

Diagnosis:

```text
claude-design.claude-design@0.1.0 is installed in VS Code Insiders.
It activates onStartupFinished.
Its package default is claudeDesign.substrate.enabled = true.
Its substrate patcher is stale for this lane: engines.vscode ^1.97.0-insider, @types/vscode ^1.97.0, @vscode/vsce ^3.0.0.
It patches the same Insiders install files as Movement 1 and reintroduced a duplicate substrate CSS link.
```

Resolution:

```text
.vscode/settings.json now sets claudeDesign.substrate.enabled = false.
scripts/mica-substrate.ps1 now strips old Claude Design main/CSS substrate markers.
Substrate verification now fails if old Claude Design main/CSS markers are present.
```

Gate rerun:

```text
Status: passed
Generated: 2026-06-29T01:52:32.570Z
single-workbench-css-link: passed
no-claude-design-main-block: passed
no-claude-design-css-block: passed
Package output: chthonic-archive-insiders.vsix
Extension-host E2E: archive/statusbar/mandala passed
```

## Current Holdup

No package gate holdup remains. The remaining warnings are environmental rather than marketplace-package blockers:

```text
Codex Native Sandbox (Windows): warning
Solana Tool Suite Lane: warning
```

## Next Exact Step

Next: run a focused visual inspection of the live Insiders workbench after restart/reload, then decide whether Surface Pass 2 should adjust opacity ratios or theme-token color balance:

- reload/restart VS Code Insiders so the runtime/CSS file changes are live
- inspect activity bar, sidebars, editor, terminal panel, quick input, notifications, and menus
- only then adjust `designs/vibrancy-obsidian.css` opacity ratios or the theme tokens
- keep screenshots/generated artifacts out of commits unless deliberately promoted

Do not admit `extensions/chthonic-themes` until the lane decides whether the themes-only VSIX is a first-class Movement 1 artifact or a generated derivative.
