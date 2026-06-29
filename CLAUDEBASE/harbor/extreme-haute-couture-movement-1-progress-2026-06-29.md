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

## Material Surface Pass 2

Files changed:

```text
designs/vibrancy-obsidian.css
```

Design correction: Surface Pass 1 had the tier-to-surface mapping inverted at the overlay end. The glass tier (most transparent) was assigned to sidebar section headers. Floating overlays (command palette, notifications, context menus) were at the deep tier (90%) — nearly opaque. This buried the Mica effect in surfaces where nobody is looking for it.

Surface Pass 2 corrects the mapping. The command palette and overlays are now the glass tier showcase. Sidebar headers recede to deck.

Tier map:

```text
--chthonic-depth-abyss:    96%   editor — reading surface, barely translucent
--chthonic-depth-bedrock:  92%   structural: activity bar, panel body, terminal wrapper
--chthonic-depth-hull:     87%   navigation: sidebar, auxiliary sidebar, status bar, title bar
--chthonic-depth-deck:     83%   sub-surfaces: tab bar, sidebar headers, panel chrome
--chthonic-depth-glass:    68%   floating overlays: command palette, notifications, menus
```

The 15% jump from deck to glass is intentional. Overlays become the Mica showcase.

Surface remapping from Pass 1:

```text
Activity bar:              bedrock (92%)   was hull (86%)
Panel body:                bedrock (92%)   was deep (90%)
Terminal wrapper:          bedrock (92%)   was hull (86%)
Sidebar body:              hull (87%)      was deck (82%)
Auxiliary sidebar:         hull (87%)      was deck (82%)
Status bar:                hull (87%)      was deep (90%)
Title bar:                 hull (87%)      was deep (90%)
Tab bar:                   deck (83%)      was deck (82%, unchanged in practice)
Sidebar section headers:   deck (83%)      was glass (76%) — demoted
Panel chrome:              deck (83%)      was hull (86%)
Command palette:           glass (68%)     was deep (90%) — promoted
Notifications:             glass (68%)     was deep (90%) — promoted
Context menus:             glass (68%)     was deep (90%) — promoted
```

Additional changes:

```text
Border fallback: removed hardcoded #3e7a6a, now uses sideBar-border → panel-border → contrastBorder chain
Shadow: 80px 34% black → 32px 28% black (lift without mud)
Canvas exclusion: monaco-editor-background removed from batch color-mix rule to prevent canvas artifact
Peek editor: added at deck (83%) — floats above editor body
```

To activate: restart VS Code Insiders. The CSS is already linked from workbench.html — no substrate script run required.

## Current Holdup

No package gate holdup remains. The remaining warnings are environmental rather than marketplace-package blockers:

```text
Codex Native Sandbox (Windows): warning
Solana Tool Suite Lane: warning
```

## Next Exact Step

Restart VS Code Insiders and inspect Surface Pass 2 live. Surfaces to check:

- Command palette (Ctrl+Shift+P) — this is the primary Mica showcase at glass (68%); it should visibly differ from all anchored surfaces
- Notifications panel — same glass tier, should float with the same quality
- Activity bar — bedrock (92%); should feel anchored, structural
- Sidebar — hull (87%); should recede gently behind the editor
- Editor — abyss (96%); reading surface, essentially opaque
- Terminal panel — bedrock (92%); solid reading surface
- Status bar and title bar — hull (87%); chrome should recede

Calibration questions after inspection:

- Is the command palette glass tier too open against the current wallpaper? (Adjustable: raise glass toward 72–74%)
- Is the sidebar/activity bar distinction perceptible? (4% gap between hull and bedrock — may be invisible on SFS dark)
- Does the editor feel grounded enough at abyss (96%)? (Could move to 100% to fully exclude it from depth effects)

Do not admit `extensions/chthonic-themes` until the lane decides whether the themes-only VSIX is a first-class Movement 1 artifact or a generated derivative.

## Integrity Reconcile

Files added:

```text
scripts/insiders-integrity-reconcile.ps1
```

Modes: -Status / -Apply / -Verify / -Restore

Algorithm: SHA-256(file bytes) → base64 → strip trailing = — exact replication of VS Code ChecksumService.

Preconditions enforced before Apply:

```text
mica-substrate.ps1 -Verify must pass
Chthonic CSS marker must be present in target file
Vibrancy Continued marker must be absent
Only allowlisted paths are touched
```

Allowlist:

```text
vs/code/electron-browser/workbench/workbench.html   (tracked in this build)
vs/code/electron-sandbox/workbench/workbench.html   (not tracked in this build)
vs/code/electron-sandbox/workbench/workbench.esm.html  (not tracked in this build)
```

Run result:

```text
vs/code/electron-browser/workbench/workbench.html:
  fg2fsFbPwbrb4+QjdKJ8TqaQMi1NaRJFXy7NMSgF9GA → sD6Yz99Z54jj5poug5VGh+0T8fDPdxved0ZT3Co0uD4
Backup: CLAUDEBASE/hold/vscode-insiders-substrate/backups/product.json.628f6de50e...bak
Verify: Ok: true
```

The "Your VS Code installation appears to be corrupt" warning will be gone on next restart. This is honest accounting — we patched the file, we updated the checksum. No hiding.

## Claude Design Extension Disabled

The stale claude-design.claude-design@0.1.0 extension was re-injecting on every startup despite claudeDesign.substrate.enabled = false in workspace settings. The extension reads a user-level default, not the workspace override.

Resolution:

```text
Disabled via VS Code extension management (not uninstalled).
Scriptorium webview preserved if needed later.
```

Result: no startup notifications. Clean.

## Gate Status — Approved 2026-06-29

Startup state:

```text
No integrity warning
No Claude Design notification
No Vibrancy markers
Chthonic substrate: present and verified
```

Plan approved and stamped. Movement 1 gates remaining:

```text
Gate A: Wire insiders-integrity-reconcile.ps1 -Verify into bun run couture:gate
Gate B: Surface Pass 3 — design direction (see below)
Gate C: extensions/chthonic-themes admission decision
Gate D: Marketplace identity — what extensions/chthonic-archive publishes
```

## Surface Pass 3 — Design Direction

The trend: glassmorphology (2021–2022) = blur + white frosting + thin border. Instagram aesthetic. Light, clean, modern. We are not doing that.

What we are doing instead: material honesty through geological depth.

The pirate glass reference is exact. Historical glass (17th–18th century) was thick, slightly green from iron impurities, and had trapped air and thickness variations. Light through it was colored and distorted, not cleanly transmitted. It was the glass of ships, of taverns, of salvage.

Surface Pass 3 translates this:

Color in the glass, not just alpha. The glass tier overlays (command palette, notifications, menus) get a verdigris cast introduced through oklch interpolation — not a flat color tint, but a subtle chromatic shift as the surface becomes more transparent. The color comes from the verdigris accent already in claudine-tokens.css (oklch 53% 0.088 164). The Mica blur behind it picks up that cast.

The move:

```css
/* Pass 2: pure alpha */
color-mix(in oklch, var(--token) 68%, transparent)

/* Pass 3: alpha + verdigris cast at the glass tier */
color-mix(
  in oklch,
  color-mix(in oklch, var(--token) 90%, oklch(53% 0.088 164)) 68%,
  transparent
)
```

At 68% opacity with 10% verdigris pre-cast, the shift is barely visible against a dark theme but detectable — especially on the nebula wallpaper where the Mica already picks up the purple/magenta. The verdigris introduces the mineral quality: copper-oxide green against dark ferrous brown.

The depth metaphor stays geological, not aquatic. Glass here is what you look through to see deeper strata — not a floating surface above a clean white background. The overlay floats, but what it reveals underneath is dark, warm, mineral.

No rounded corners. No white borders. No frosted softness. The border-soft token is already verdigris at 40% opacity against a dark background — that stays.

What Surface Pass 3 does not do: change the anchored surfaces. Bedrock, hull, deck — those stay pure alpha. Only the glass tier gets the cast. The editorial choice: overlays reveal the mineral quality of the glass; the structure stays geological and opaque.

Nassau framing applicability: valid. The Nassau crew is self-governed, operating at the margin of official systems, using salvaged materials with authority. The design is the same — VS Code's official theming system plus unofficial substrate patching, owned completely, neither apologetic nor flashy about it. The pirate glass is not treasure — it's the window in the captain's quarters. Functional. Tinted. Non-negotiable.

Next exact step for Surface Pass 3: write the verdigris cast into the glass tier rule in vibrancy-obsidian.css and observe on the live workbench with the command palette open. Calibrate the cast percentage until it reads as mineral rather than colorful.
