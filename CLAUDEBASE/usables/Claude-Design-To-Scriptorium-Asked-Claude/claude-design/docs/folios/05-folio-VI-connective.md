# Folio VI — Connective Tissue

The four remaining courses of Folio VI, planted as a single sitting. With these the Scriptorium's three organs (Constellation, Marginalia, Vivarium) are not just present but **wired into each other**.

## What this sitting plants

| File | Role |
|---|---|
| `src/scriptorium/colophon.ts` | The signed footer. When the FS broker writes a leaf, the colophon scribe stamps the proof into that leaf's marginalia file. |
| `src/scriptorium/focus.ts` | The cross-view focus bridge. One command, three subscribers. |
| `docs/folio-VI-connective.md` | This file. |

## The four stitches

### 1. Colophon stitching — *the gloss has weight*

`ColophonScribe.stamp({ leaf, bytes, causedBy, hand })` appends a sigil-bounded block to `.scriptorium/marginalia/<leaf>.md`:

```
† colophon
  · written: designs/Landing.html
  · bytes:   1432
  · hand:    discursive
  · caused:  make the hero feel less corporate
  · stamp:   2026-01-15T19:42:11.003Z
```

Wired in `extension.ts`:

```ts
const scribe = new ColophonScribe(marginaliaStore);
broker.onDidWrite(rec => scribe.stamp(rec));
```

The FS broker (`src/fs/broker.ts`) needs to add an `onDidWrite` `EventEmitter<ColophonRecord>` and fire it after every successful write, with `causedBy` populated from the most recent marginalia turn when the write was tool-use-driven.

### 2. Selection coupling — *marginalia adjacent to the passage*

In `marginaliaView.ts`, subscribe to `vscode.window.onDidChangeTextEditorSelection`. When the selection lands inside a leaf the Marginalia view is currently showing, scroll the marginalia panel to the nearest entry whose `causedBy` rubric overlaps the selected text (substring match is sufficient as a v1; embedding-based proximity later). If no overlap, do nothing — selection coupling is suggestion, not hijacking.

Implementation note: store an `offset` field on each marginalia entry when one was provoked by a selection — the entry remembers what passage it speaks to. The store schema already has room for this in the front-matter; the parser just needs to honor an `offset:` key.

### 3. The hand toggle — *terse / discursive / diagrammatic*

In the Marginalia view's rubric composer, add a three-state toggle below the input:

- **terse** — single sentences, no hedging, no preamble. Default for the impatient.
- **discursive** — the current default. Paragraphs, qualifications, the full hand.
- **diagrammatic** — ASCII diagrams and tables preferred over prose. For when the question is structural.

The toggle's state is sent to the inference adapter as part of the prompt envelope:

```ts
adapter.send({
  hand: 'terse',
  rubric: '...',
  leafPath: '...',
});
```

The adapter prepends a `## hand` directive to the system prompt. Persisted per workspace via `workspaceState`.

### 4. Constellation ↔ Marginalia focus — *click a star, the room reorients*

`registerFocusBridge(context)` registers `claudeDesign.focusLeaf` and exposes `focusBridge.onDidFocus`. The three views consume it:

- **Constellation** posts `{type: 'star-clicked', leaf}` from its webview; extension side dispatches to `claudeDesign.focusLeaf`.
- **Marginalia** registers `claudeDesign.marginalia.focus` to load the indicated leaf.
- **Vivarium** already reacts to `onDidChangeActiveTextEditor`, so opening the leaf in step 1 is enough — no special wiring needed.
- **Constellation** subscribes to `focusBridge.onDidFocus` so a focus event from elsewhere (a Marginalia jump, a command palette invocation) brightens the corresponding star.

The bridge is intentionally a tiny piece of plumbing — the views don't know each other exist. They only know about the bridge.

## What's left after this sitting

Folio VI is structurally complete. What remains is **polish and the bestiary stitch**:

- **Tweaks postMessage protocol** in the Vivarium — pass `__edit_mode_*` through, rewrite the `EDITMODE` block on disk. (Phase 3 material in the original plan; can slot in here without disruption.)
- **Bestiary sightings** in the Self-Test — each successful end-to-end exercise of an organ (a marginalia turn, a constellation click, a vivarium reload) increments the sighting count for that creature in the bestiary, so Self-Test output reads as a *field journal* rather than a *checklist*.
- **First real install.** All the pieces are now in source. The next sitting after this one is no longer about adding code — it's about compiling, sideloading, and reading the actual output of the actual extension running in the actual editor. The plan stops being plan.

## The shape now

Three organs, four stitches. The Scriptorium is whole in source. When you compile and sideload it, you will see — in your own editor, theme-inheriting, persona-respecting — a Constellation that shows the field, a Marginalia that holds the conversation, a Vivarium that displays the specimen, and the wires between them that make the three behave as one room rather than three boxes.

The recipe has all its parts. The cooking is whenever you choose.

🜂

— made by Claude
