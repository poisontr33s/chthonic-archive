---
type: handoff
from: Codex
to: Claude Code
created: 2026-06-29
priority: high
subject: "Stop reload-flipping; trace the active Insiders root and chthonic-themes provider first"
---

# Claude Code Handoff — Chthonic Themes / Mica Substrate Root Correction

This is the missing diagnostic layer before any more reload/restart advice.

The problem was not "VS Code needs another reload." The problem was that the investigation was looking at the wrong ownership plane.

## Current Stable Anchor

- Live VS Code Insiders root after restart:
  `C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\0d2dfb2eb8\resources\app`
- Version:
  `1.127.0-insider`
- Commit:
  `0d2dfb2eb897808a27356ab6e5d33000acec4590`
- Active visible theme/icon provider:
  `chthonic-archive.chthonic-themes`
- Disabled larger runtime extension:
  `chthonic-archive.chthonic-archive`
- Active color theme:
  `Chthonic — Geological Core (Sister Ferrum Scoriae)`
- Active file icon theme:
  `chthonic-file-icons`
- Active product icon theme:
  `chthonic-product-icons`

## What Claude Code Was Missing

VS Code Insiders can hold two local app roots during an update:

- old running root:
  `...\628f6de50e\resources\app`
- new staged/update root:
  `...\0d2dfb2eb8\resources\app`

The old `scripts/mica-substrate.ps1` discovery selected by `main.js` `LastWriteTimeUtc`. That rewarded the previously patched old root, because patching `main.js` made it newer than the clean staged update. Meanwhile `scripts/insiders-integrity-reconcile.ps1` selected by commit-directory freshness. Result: substrate verification and checksum verification could silently talk about different app roots.

That was the reload trap.

Codex fixed `scripts/mica-substrate.ps1` so app-root discovery selects by Insiders commit-directory timestamp, not patched `main.js` timestamp.

## Do Not Continue Until These Pass

Run these from `C:\Users\eldno\chthonic-archive`:

```powershell
pwsh -NoProfile -File scripts\mica-substrate.ps1 -Verify
pwsh -NoProfile -File scripts\insiders-integrity-reconcile.ps1 -Verify
```

Expected:

```text
mica-substrate.ps1 -Verify: Ok true
insiders-integrity-reconcile.ps1 -Verify: Ok true
```

If either fails, do not ask the user to reload. Fix the root/marker/checksum state first.

## First Proof: Running App Root

Before changing CSS, theme JSON, or asking for another restart, prove which app root the renderer is using:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -eq 'Code - Insiders.exe' -and $_.CommandLine -like '*--app-path=*' } |
  Select-Object ProcessId,CommandLine
```

Expected app path after the user's June 29 restart:

```text
--app-path="C:\Users\eldno\AppData\Local\Programs\Microsoft VS Code Insiders\0d2dfb2eb8\resources\app"
```

If the renderer still points at `628f6de50e`, the visible window is old. Do not infer anything from renderer behavior until the app path matches the intended root.

## Second Proof: Active Provider Is chthonic-themes

Use `uv` for SQLite access. Do not invoke bare `python`; this workspace expects `uv` as the Python handler.

```powershell
$py = @'
import sqlite3, pathlib, json
p = pathlib.Path(r'C:\Users\eldno\AppData\Roaming\Code - Insiders\User\globalStorage\state.vscdb')
con = sqlite3.connect(f'file:{p.as_posix()}?mode=ro&immutable=1', uri=True)
cur = con.cursor()
for key in ('colorThemeData','iconThemeData','productIconThemeData','extensionsIdentifiers/disabled'):
    row = cur.execute('select value from ItemTable where key=?', (key,)).fetchone()
    print('---', key)
    print(row[0][:2000] if row else 'missing')
con.close()
'@
$py | uv run python -
```

Expected ownership:

- `colorThemeData.id` contains:
  `chthonic-archive-chthonic-themes-themes-chthonic-geology-color-theme-json`
- `iconThemeData.id`:
  `chthonic-archive.chthonic-themes-chthonic-file-icons`
- `productIconThemeData.id`:
  `chthonic-archive.chthonic-themes-chthonic-product-icons`
- `extensionsIdentifiers/disabled` includes:
  `chthonic-archive.chthonic-archive`

This means the visible GUI is owned by `chthonic-themes`, not the larger runtime extension.

## Product Icon Delta

The newer in-house `chthonic-themes` family did not introduce a large hidden theme rewrite. The meaningful product-icon delta is one glyph:

- active/local `chthonic-themes` product font map: 44 glyphs
- stale disabled installed `chthonic-archive` product font map: 43 glyphs
- new glyph:
  `folder U+E02D`

Active/local `chthonic-themes` maps these aliases to `U+E02D`:

- `folder`
- `folder-active`
- `folder-library`
- `folder-opened`
- `root-folder`
- `root-folder-opened`
- `workspace-trusted`
- `workspace-unspecified`
- `workspace-untrusted`

The disabled installed full archive maps those aliases to the older `extensions U+E00A` glyph. That is stale lineage and not the active GUI source.

## Wrong Places

Do not spend the next pass primarily in these places:

- repeated reload/restart cycles
- only `extensions/chthonic-archive/package.json`
- only `extensions/chthonic-archive/themes/chthonic-product-icon-theme.json`
- the disabled installed full archive extension as if it were active
- the old Insiders root `628f6de50e` after update
- assuming the command palette flatness is proof the Mica patch failed

Those are subordinate or stale surfaces.

## Right Places

Look here first:

- running renderer `--app-path` command line
- `scripts/mica-substrate.ps1` root selection
- `scripts/insiders-integrity-reconcile.ps1` checksum target
- VS Code state DB keys:
  `colorThemeData`, `iconThemeData`, `productIconThemeData`, `extensionsIdentifiers/disabled`
- active installed extension:
  `C:\Users\eldno\.vscode-insiders\extensions\chthonic-archive.chthonic-themes-0.2.9`
- canonical local visible provider:
  `C:\Users\eldno\chthonic-archive\extensions\chthonic-themes`
- local source mirrored into the active family:
  `C:\Users\eldno\chthonic-archive\extensions\chthonic-archive\themes`
- renderer substrate CSS:
  `C:\Users\eldno\chthonic-archive\designs\vibrancy-obsidian.css`
- main-process Mica runtime:
  `C:\Users\eldno\chthonic-archive\designs\chthonic-mica.cjs`

## Correct Next Plan

1. Prove active Insiders root.
   The renderer must be on `0d2dfb2eb8`.

2. Prove substrate gates.
   `mica-substrate.ps1 -Verify` and `insiders-integrity-reconcile.ps1 -Verify` must both pass.

3. Prove active GUI provider.
   State DB must resolve theme/icon/product icon through `chthonic-themes`.

4. Treat `chthonic-themes` as visible authority.
   The larger `chthonic-archive` extension is runtime-capable but disabled; do not reason from it as the active theme provider.

5. Only then inspect command palette visibility.
   If command palette still looks flat, it is not automatically a failed Mica patch. It is likely the depth-chain/compositing problem already described in:
   `CLAUDEBASE\sub-surface-skinny-dipping\gemini-dr\chthonic-mica-command-palette-visibility-dr-brief.md`

6. Avoid CSS guessing until DOM/compositor evidence exists.
   Use DevTools or a deep-research answer to determine whether `.quick-input-widget` children or Chromium backdrop-filter behavior are swallowing the intended Mica visibility.

## Current Uncommitted/Untracked Artifacts To Preserve

- modified:
  `scripts/mica-substrate.ps1`
- untracked:
  `scripts/insiders-integrity-reconcile.ps1`
- untracked:
  `CLAUDEBASE\sub-surface-skinny-dipping\gemini-dr\chthonic-mica-command-palette-visibility-dr-brief.md`
- untracked:
  `extensions\chthonic-themes\themes\chthonic-geology-color-theme.json`

Do not delete these while trying to "clean up." They are part of the current evidence trail.

## Decision Rule

If the user reports "nothing changed," do not answer with another reload instruction.

Answer by proving:

1. which app root is running,
2. which extension owns the active theme cache,
3. whether substrate/integrity gates pass,
4. whether the visible surface is a renderer CSS/compositor problem rather than a patch deployment problem.

Only after those four proofs should visual calibration continue.

Made by Codex for Claude Code. Preserves the Chthonic/SFS substrate boundary and the user's in-house GUI authority.
