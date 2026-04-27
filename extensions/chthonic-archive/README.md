# Chthonic Archive

VS Code workspace extension for the Chthonic Archive: themes, icon surfaces,
sidebar lenses, local runtime status, and rendered AI Markdown paste fidelity.

## Included

- 4 color themes
- 1 file icon theme
- 1 product icon theme
- 5 extension views
- 18 extension commands
- GLSL and TOML language registration

## Theme Surfaces

- `Chthonic — Geological Core (Sister Ferrum Scoriae)`
- `Chthonic — Flesh & Earth (The Decorator)`
- `Chthonic — ROGBIV (Spectra Chroma)`
- `Chthonic — The Decorator`
- `Chthonic Archive File Icons`
- `Chthonic Archive Product Icons`

## Views

- `☥ ANKH Reference`
- `Abyssal Pane`
- `Themes`
- `Lens`
- `The Loom`

## Commands

- `Chthonic: Switch Theme`
- `Chthonic: Refresh Status Bar`
- `Chthonic: Verify Policy Fingerprint`
- `Chthonic: Refresh Workspace Health Overlay`
- `Chthonic: Activate Cockpit Layout`
- `Chthonic: Detect Project Tooling (ANNO)`
- `Chthonic: Compute Sediment Layers`
- `Chthonic: Deep Focus Layout`
- `Chthonic: Restore Order Layout`
- `Chthonic: Self-Heal Slab`
- `Chthonic: Refresh Toolchain Completeness Score`
- `Chthonic: Open Next Cockpit`
- `Chthonic: Start Next Cockpit`
- `Chthonic: Open Bun Training Docs`
- `Chthonic: Post-Restart Verify`
- `Chthonic: Restart Gate Check`
- `Chthonic: Runtime Status`
- `Chthonic: Paste Rendered AI HTML as Markdown`

## Rendered AI Markdown Paste

KISS behavior: copy rendered AI output, open a Markdown file, paste. If the
clipboard includes `text/html`, the extension inserts GFM Markdown instead of
lossy plain text.

Preserved structures:

- ATX headings
- Bullet and numbered lists
- Fenced code blocks, including language tags and nested fences
- Tables
- Blockquotes
- Links and inline code
- Markdown-legal HTML islands such as `kbd`, `sub`, `sup`, `details`, and `summary`

Command palette fallback:

- `Chthonic: Paste Rendered AI HTML as Markdown`

If a source only puts plain text on the clipboard, VS Code keeps its normal paste
behavior and the extension shows a non-blocking note that `text/html` was absent.

Fixture check:

```powershell
bun run test:markdown-paste
bun run test:markdown-paste:stress
```

The stress benchmark renders
`.claude/skills/markdown-bridge/fixtures/outbound/stress_corpus_v1.md` to HTML,
feeds that rendered output through the paste converter, and asserts the corpus
keeps its high-value Markdown structures.

## Local Update

Build and reinstall the local VSIX:

```powershell
bun run --cwd extensions/chthonic-archive insiders:package
code-insiders --install-extension extensions/chthonic-archive/chthonic-archive-insiders.vsix --force
```

Then run `Developer: Reload Window` in VS Code Insiders. A full Insiders restart
is only needed if theme or icon surfaces still show stale metadata after reload.

## Notes

This extension is packaged as a local VSIX in this workspace. If themes or icon
surfaces appear stale after reinstall, reload VS Code Insiders so the installed
extension copy is reactivated.
