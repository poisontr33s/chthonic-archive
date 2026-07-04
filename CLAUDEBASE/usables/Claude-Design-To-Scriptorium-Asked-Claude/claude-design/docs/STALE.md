# Stale — what's superseded but kept

These source files are no longer registered in `extension.ts` or `package.json`. They are inert: included in the build (because they live under `src/`) but never instantiated. They are kept for two reasons:

1. **Archaeology.** They preserve the Phase 0/1 posture — the original sidecar-into-Claude-Code splice — so a future reader can see *why* the Scriptorium pivot was made.
2. **Concrete examples of patterns** the Scriptorium ended up using differently. Sometimes the older pattern is the right one for a future feature.

## The inert set

| file | what it was | superseded by |
|---|---|---|
| `src/bridge/claudeCode.ts` | splice-era bridge into Claude Code's view container | not used — the extension is now sidecar, not splice |
| `src/views/designFiles.ts` | TreeDataProvider listing `designs/**` | `src/views/constellation.ts` — the field of leaves |
| `src/views/assetReview.ts` | TreeDataProvider reading `.claude-design/manifest.json` | `src/scriptorium/manifest.ts` — reads `designs.md` instead |
| `src/views/previewPanel.ts` | Phase 1 preview surface | `src/views/vivarium.ts` — the illuminated plate |

## What the audit confirmed

The Folio VII audit (`folios/07-folio-VII-final-review.md`) verified that none of the inert files are imported by the active surface. They compile, but they don't activate.

## When to revive

- **`bridge/claudeCode.ts`** — revive if Claude Code grows a public `exports` surface we want to consume. The Folio VII activator's optional-chained `(view as any).brighten?.(leaf)` pattern is the idiom for that kind of soft dependency.
- **`views/designFiles.ts`** — revive if we ever want a fallback for users who prefer the tree. Becomes the `posture: "plain"` view in `claudeDesign.posture`.
- **`views/assetReview.ts`** — revive if `.claude-design/manifest.json` ever returns as a machine-only manifest alongside `designs.md`. Not currently planned.
- **`views/previewPanel.ts`** — revive if the Vivarium needs a "raw" mode without the plate framing. Currently `frame: "bare"` covers that.

## When to delete

If three sittings pass without any of these being read or referenced, delete. Not before — premature removal is its own loss.

🜂
