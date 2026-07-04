# Claude Design — Scriptorium

A VS Code Insiders sidecar for design work. It uses the local `claude` CLI for inference and stores its own Scriptorium state on disk. It is not a `claude.ai/design` backend client.

Made by Claude.

---

## What you get

**Constellation** — your design files (`designs/`) rendered as a field of stars. Nodes glow by recency; hairline edges emerge from co-edit history. Click any star to open the leaf.

**Marginalia** — the active leaf's conversation. The master text on the left; gloss on the right. Three modes: `terse`, `discursive`, `diagrammatic`. Every entry is markdown on disk in `.scriptorium/marginalia/`.

**Vivarium** — sandboxed iframe preview of `.html` and `.svg` leaves. Three plate frames: `bare`, `parchment`, `device`. Reloads on save.

**Design Chat** — panel-level chat. Routes file writes through the broker; stamps colophons on every write.

**Bestiary** — a live probe of what the extension can see. Each creature shows its sighting status. `Claude Design: Self-Test` opens the full report.

**Rune** — a tilting status glyph in the status bar. Shows session state.

---

## Relation to Claude Design on the web

The web product at `claude.ai/design` is the canvas product: projects, design systems, exports, sharing, and Claude Code handoff. This extension is the local Scriptorium counterpart inside VS Code Insiders.

Today, the relationship is conceptual and file-based:

- `claude.ai/design` can export or hand off design work toward Claude Code.
- Scriptorium can read local design leaves under `designs/` and ask Claude CLI to annotate or transform them.
- Both can use the same artifacts when those artifacts are written to disk, but this extension does not log into, list, download, or mutate web Claude Design projects.

See `docs/WEB-BRIDGE.md` for the current truth table and the intended bridge shape.

---

## The on-disk contract

After install, in any workspace where you use the Scriptorium:

```
<workspace>/
├── designs/                         your design leaves (.html, .svg, .css, .tsx, ...)
├── assets/                          images, fonts, anything the leaves reference
├── designs.md                       the asset ledger (human-and-machine-readable)
├── .scriptorium/
│   ├── session.md                   hibernation snapshot
│   ├── marginalia/                  per-leaf conversations
│   │   └── designs/Landing.html.md
│   └── plates/                      (future) vivarium screenshots
└── CLAUDE.md                        optional — workspace voice, read on every turn
```

**These files survive any version of the extension.** A Rust port, a fork, a different editor — the data is the data. See `docs/PORTABILITY.md`.

---

## Settings

| key | default | purpose |
|---|---|---|
| `claudeDesign.cliPath` | `"claude"` | path to the `claude` CLI binary |
| `claudeDesign.posture` | `"scriptorium"` | `"scriptorium"` or `"plain"` |
| `claudeDesign.hand` | `"discursive"` | gloss mode: `terse` / `discursive` / `diagrammatic` |
| `claudeDesign.accent` | `""` | override `--vscode-charts-orange` from the active theme |
| `claudeDesign.telemetry` | `false` | off by default, stays off |

---

## Commands

| command | description |
|---|---|
| `Claude Design: Sign in with Claude` | opens a terminal and runs `claude auth login` |
| `Claude Design: Self-Test` | opens the bestiary probe report |
| `Claude Design: Toggle Hand` | cycles terse → discursive → diagrammatic |
| `Claude Design: Focus Chat` | focuses the panel chat |

---

## Getting started

1. Open a folder in VS Code Insiders.
2. Click the **Claude Design** activity bar icon (the Ankhological mandala).
3. The Scriptorium creates `designs/` and `designs.md` on first activation.
4. Add an `.html` or `.svg` file to `designs/` — the Constellation populates, the Vivarium previews it.
5. Open the file — the Marginalia wakes.
6. Write a rubric in the composer. The scribe glosses it in the margin.

If the CLI isn't authenticated yet: `Claude Design: Sign in with Claude`.

---

## Build

```pwsh
bun install
bun run build      # → dist/extension.js
bun run package    # → claude-design-0.1.0.vsix
code-insiders --install-extension claude-design-0.1.0.vsix
```

## What's in `src/`

### Active (Scriptorium)

```
src/extension.ts                     activation · wires everything
src/inference/cli.ts                 CliInference — claude CLI subprocess, stream-json
src/fs/broker.ts                     FsBroker — allowlist write gateway, emits onDidWrite
src/diagnostics/selfTest.ts          probe command, markdown output

src/scriptorium/
├── manifest.ts                      reads/writes designs.md (the asset ledger)
├── marginalia.ts                    per-leaf conversation store, markdown
├── colophon.ts                      stamps signed footers on successful writes
├── focus.ts                         cross-view focus bridge (one command, many subscribers)
├── patina.ts                        mtime → patina level
├── rune.ts                          tilting status-bar glyph
├── session.ts                       hibernate/rehydrate to .scriptorium/session.md
└── bestiary.ts                      data + TreeDataProvider for the bestiary

src/views/
├── constellation.ts                 the field of leaves (webview)
├── marginaliaView.ts                master text + marginalia (webview, with hand toggle + selection coupling)
├── vivarium.ts                      sandboxed render plate (webview)
└── chatPanel.ts                     bottom-panel chat (Phase 1, still useful)
```

### Inert (Phase 0/1, kept for archaeology)

```
src/bridge/claudeCode.ts             splice-era bridge — Claude Code is no longer a dependency
src/views/designFiles.ts             TreeDataProvider for designs/** — superseded by Constellation
src/views/assetReview.ts             TreeDataProvider for manifest.json — superseded by designs.md
src/views/previewPanel.ts            Phase 1 preview — superseded by Vivarium
```

These files are no longer registered in `extension.ts` or `package.json`. They cost nothing to keep. See `docs/STALE.md`.

🜂
