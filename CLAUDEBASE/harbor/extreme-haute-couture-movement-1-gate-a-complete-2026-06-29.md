# Extreme Haute Couture — Movement 1: Gate A Complete

Snapshot: 2026-06-29

## Gate ladder state

Gate A: closed
Gate B: CSS written (verdigris pass live), visual calibration pending
Gate C: chthonic-themes admission decision pending
Gate D: marketplace identity pending

## couture:gate — all checks green (last run 2026-06-29)

```
official-stable-floor: ok — engines.vscode=^1.126.0, stable=1.126.0
local-insiders-current: ok — 1.127.0-insider, commit=0d2dfb2eb8
vscode-types-compatible: ok — @types/vscode=^1.125.0
root-sdk-catalog-check: ok — 12 managed packages
extension-dependencies-latest: ok — @openai/codex-sdk bumped to ^0.142.4
insiders-substrate-verify: ok — 1.127.0-insider, commit=0d2dfb2eb8
substrate-targets-current-insiders: ok
insiders-integrity-reconcile-verify: ok — workbench.html checksum owned (Gate A)
color/file/product icon contributions: ok — 4 themes / 99 file icons / 115 product icons
extension-kits-check: ok
extension-package-insiders: ok — 457422 bytes
extension-host-e2e: ok — archive/statusbar/mandala
```

## Substrate runtime proof

`.chthonic/mica-diag.txt` after last clean restart:

```
chthonic-mica.cjs loaded
material=mica
whenReady: 0 existing window(s)
setBackgroundMaterial('mica') ok
dom-ready url=vscode-file://vscode-app/.../workbench.html
setBackgroundColor(#00000000) ok
```

## What is live in workbench.html

- Inline `<style data-claude-design-substrate="vibrancy-obsidian">` block (not file:// link)
- Root reset: `body, .monaco-workbench { background: transparent !important }`
- Depth tier map: abyss 96% / bedrock 92% / hull 87% / deck 83% / glass 68%
- Verdigris cast on glass tier: `color-mix(in oklch, var(--token) 88%, oklch(53% 0.088 164))`
- Integrity reconcile: checksum current, no VS Code corrupt warning

## Why paused

Toolchain hardening required before continuing. Lane does not drift — it waits.
