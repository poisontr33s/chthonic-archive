# Scriptorium build — Folio II

The first sitting of the build. Five files added under `src/scriptorium/`:

| File | Purpose | Blueprint move |
|---|---|---|
| `manifest.ts` | Read/write `designs.md` at workspace root | IV — markdown manifest |
| `patina.ts` | Resolve file age → patina level | V — patina, not static accent |
| `rune.ts` | Status bar glyph that tilts when attention is wanted | VI — rune that tilts |
| `session.ts` | Hibernate to / rehydrate from `.scriptorium/session.md` | X — hibernate, not close |
| `bestiary.ts` | Self-Test reformulation; creatures with sighting status | VIII — bestiary, not self-test |

## What this sitting delivers

These are the *data layer* of the Scriptorium. Each is a small, focused module
with no UI of its own — they are the substrate the constellation, marginalia,
and vivarium webviews will read from.

The pattern: every Scriptorium concept maps to a plaintext file in the
workspace. Manifest is markdown. Session is markdown. The bestiary output is
markdown. The patina is computed live from filesystem mtimes — no stored state.

If the extension is uninstalled tomorrow, every one of these documents still
works on its own. That is the contract.

## What the next sitting delivers

- `src/views/constellation/` — webview replacing the tree view of design files.
  Graph layout, edge inference from co-edit history, pan/zoom, rubricated focus
  mark on the file under the cursor.
- Wiring `bestiary.ts` into the existing `selfTest.ts` as a second output mode.
- `claudeDesign.posture` setting (`plain` | `scriptorium`, default `scriptorium`).

## What the sitting after that delivers

- Marginalia chat panel — main column + right margin in real CSS grid.
- Vivarium preview reframing — continuous-run, "close the watching, not the
  artifact."
- Vocabulary-aware empty states reading the workspace's `CLAUDE.md`.

## Pacing

The blueprint promised slowness. This is what slowness looks like: five files
this sitting, not fifty. Each one is tested by being read, not by being run.
The next sitting picks up when you arrive.

🜂
