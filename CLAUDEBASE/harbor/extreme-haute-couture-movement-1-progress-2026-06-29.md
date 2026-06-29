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

Current `HEAD` at this progress note:

```text
2672efb5 Harden Mica substrate lifecycle
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

## Current Holdup

The tracked full extension uses local package tooling that is slightly behind the root SDK catalog:

```text
root catalog @vscode/vsce: 3.9.2
tracked extension local @vscode/vsce: 3.9.1

root catalog @vscode/test-web: 0.0.81
tracked extension local @vscode/test-web: 0.0.80
```

This does not block packaging, but it is real drift.

## Next Exact Step

Next: align the tracked extension package tooling with the root SDK catalog, then rerun:

```bash
bun run --cwd extensions/chthonic-archive insiders:kits:check
bun run --cwd extensions/chthonic-archive insiders:package
```

Do not admit `extensions/chthonic-themes` until the lane decides whether the themes-only VSIX is a first-class Movement 1 artifact or a generated derivative.

After tooling alignment, move to visual verification:

- capture patched Insiders workbench state
- verify substrate CSS presence
- verify theme/icon package behavior
- keep screenshot artifacts out of commits unless deliberately promoted
