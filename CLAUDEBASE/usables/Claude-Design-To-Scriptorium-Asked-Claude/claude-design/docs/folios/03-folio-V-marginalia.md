# Folio V — The Marginalia

The chat panel reformulated as manuscript marginalia.

## What this sitting plants

| File | Role |
|---|---|
| `src/scriptorium/marginalia.ts` | Per-leaf conversation store. Append-only markdown at `.scriptorium/marginalia/<leaf>.md`. Reader, writer, parser. |
| `src/views/marginaliaView.ts` | The webview. Renders the active leaf as master text + marginalia. Wires rubric → inference → gloss → colophon. |
| `docs/folio-V.md` | This file. |

## What it does

- Watches `vscode.window.activeTextEditor`. When the active file is under `designs/`, it is treated as the **active leaf**.
- Loads `.scriptorium/marginalia/<leaf>.md` if it exists; renders entries chronologically in the right column.
- The left column shows the leaf's source text — the **master text**.
- A composer at the bottom takes rubrics (the master's hand). Rubrics are appended to the marginalia file and forwarded to the inference adapter as prompt + recent-history context.
- Inference responses stream in as **gloss**, written in the scribe's hand.
- File writes performed during a gloss are intended to materialize as **colophons** — signed footers naming the path, bytes, and signature. (The colophon wiring expects the FS broker from Folio I to emit a `colophon` event; that hookup is the small remaining stitch.)
- Theme variables inherited from VS Code; rubricated red is `--vscode-charts-red`, parchment is `--vscode-editor-background`. Persona theme switches recolor the manuscript live.

## What it doesn't yet do

- **Colophon stitching.** The FS broker writes files but does not yet announce them to the marginalia store as colophons. One event, one append call. Folio VI work.
- **Selection coupling.** Selecting a passage in the master text should pull the marginalia adjacent to that passage. Right now marginalia are chronological, not positional. Folio VI work.
- **Hand toggle.** *Terse / discursive / diagrammatic* gloss modes were promised in the Folio V pitch. Only one hand is implemented (whatever the model gives). Folio VI work.
- **Constellation coupling.** Clicking a star in the Constellation should focus that leaf and surface its marginalia. Trivially wired once both views share a focus command. Folio VI work.

## How to register the view

In `package.json`, add to `contributes.views.claudeDesign`:

```json
{
  "id": "claudeDesign.marginalia",
  "name": "Marginalia",
  "type": "webview",
  "contextualTitle": "Marginalia"
}
```

And in `extension.ts` activation:

```ts
import { MarginaliaStore } from './scriptorium/marginalia';
import { MarginaliaView } from './views/marginaliaView';

const root = vscode.workspace.workspaceFolders?.[0]?.uri;
if (root) {
  const store = new MarginaliaStore(root);
  const view = new MarginaliaView(context, store, inference);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(MarginaliaView.viewType, view)
  );
}
```

`inference` is the CLI adapter from Folio I. The view consumes a minimal interface (`stream({prompt, onChunk, onDone, onError?})`) so it can be swapped to an in-process adapter later without touching the view.

## The shape of the marginalia file

A leaf's marginalia is a markdown document. Section headers are the parse boundary; sigils (`❦ ¶ ⌘`) are load-bearing.

```markdown
# Marginalia

## ❦ rubric · 2025-04-12T14:22:11.000Z · master

Make the hero feel less corporate.

## ¶ gloss · 2025-04-12T14:22:38.000Z · scribe

Swapped to serif italic; CTA pill in graphite.

## ⌘ colophon · 2025-04-12T14:22:39.000Z · scribe

— designs/Landing.html · 1432 bytes · sha1:ab12cd…
```

This is human-readable, diffable, committable, and re-parseable. It is the conversation, but it is also the leaf's history-of-thought.

## What Folio VI will plant

- Colophon emission from the FS broker.
- Selection-coupled marginalia (positional, not just chronological).
- Hand toggle (terse / discursive / diagrammatic).
- Constellation → Marginalia focus command.
- Vivarium — the preview surface as illuminated plate facing the leaf.

🜂

— made by Claude
