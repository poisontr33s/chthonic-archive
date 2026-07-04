# Claude Design — Scriptorium

A VS Code Insiders extension. Bun-managed. Designed to sit next to Claude Code. It is a local Scriptorium surface for design leaves, not the `claude.ai/design` web backend.

> *Made by Claude. For the workspace that asked.*

---

## What's in this project

```
.
├── README.md                       ← you are here
├── blueprints/                     ← design-time artifacts, in reading order
│   ├── 01-architectural-plan-v0.html        first draft (Claude Code splice posture)
│   ├── 02-architectural-plan.html           current blueprint (sidecar posture)
│   ├── 02-architectural-plan.standalone.html  same, single-file bundled
│   └── 03-scriptorium.html                  the manuscript-form posture pivot
└── claude-design/                  ← the extension itself
    ├── README.md                   detailed install + architecture
    ├── SESSION_TRANSCRIPT.md       continuity carrier (resume-from-new-session)
    ├── package.json
    ├── tsconfig.json
    ├── src/                        TypeScript source (Bun-built)
    └── docs/
        ├── INDEX.md                canonical reading order
        ├── PORTABILITY.md          forward-looking: Rust/Electron survival
        ├── STALE.md                what's superseded but kept
        └── folios/                 per-sitting design notes
```

## What it does

Three primary surfaces, contributed into the activity bar as a sidebar group titled *Claude Design*:

- **Constellation** — webview replacing the file tree. Files are stars, edges are co-edit history, recently-touched files glow, long-untouched fade.
- **Marginalia** — webview replacing chat. Active leaf in the left column; rubrics + gloss + colophons in the right margin. Conversations persist as markdown next to each leaf.
- **Vivarium** — webview replacing preview. Active leaf renders in a sandboxed iframe with three plate frames (bare, parchment, device). Reloads on save.

Plus a bottom-panel **Design Chat**, a sidebar **Bestiary** tree (the Self-Test reformulated as creatures with sighting status), and a tilting **Rune** in the status bar.

## Relationship to `claude.ai/design`

`claude.ai/design` is the upstream Claude Design product: browser/desktop canvas, design systems, exports, and Claude Code handoff. The Scriptorium is the local VS Code sidecar that grew from that idea.

Current transport is local:

- prompts go through the configured `claude` CLI;
- OAuth and quota are handled by the CLI account;
- local state is written to `designs/`, `designs.md`, and `.scriptorium/`;
- there is no direct project sync with `claude.ai/design` yet.

The bridge contract is documented in `claude-design/docs/WEB-BRIDGE.md`.

## Where we are

| | |
|---|---|
| Architecture | ✓ done (`blueprints/`) |
| Phase 0/1 (original posture) | ✓ source on disk, superseded |
| Scriptorium pivot | ✓ Folios I–VII landed |
| Wiring audit (Folio VII) | ✓ extension.ts converges with actual exports |
| Compile (`bun run build`) | ✓ passes |
| Package (`bun run package`) | ✓ produces `claude-design-0.1.0.vsix` |
| Sideload into VS Code Insiders | ✓ installed locally |
| First live Marginalia stream | ✓ repaired; old `Here.` entry remains as historical marginalia |

The repo is no longer only source-complete. It has been built, packaged, installed, and observed against a live `designs/` leaf.

## Forward-looking

Claude Code's transition (and likely the broader Insiders surface) toward Rust + Electron is real. The Scriptorium was designed with this in mind, even if accidentally: **every contract that matters is plaintext on disk** — `designs.md` for the manifest, `.scriptorium/marginalia/<leaf>.md` for per-leaf conversation, `.scriptorium/session.md` for hibernation. A Rust port replaces the TypeScript activator without breaking any user's existing scriptorium. The format is the API. See `claude-design/docs/PORTABILITY.md`.

🜂
