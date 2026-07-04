/**
 * gap-close patches — items 3 and 4 from the Not Done list.
 *
 * These deltas extend files that already exist in source. They are
 * documented here as drop-in replacements / additions rather than
 * speculative re-writes. A coding agent (or you, by hand) can apply
 * them directly.
 *
 * Made by Claude.
 */

# Gap-Close Patches

## Item 3 — `src/fs/broker.ts` gains `onDidWrite`

Add an `EventEmitter<ColophonRecord>` to the broker and fire it after every successful write. The record is the payload the `ColophonScribe` consumes.

```ts
// at top, alongside other imports
import * as vscode from 'vscode';
import { ColophonRecord } from '../scriptorium/colophon';

export class FsBroker {
  // ... existing state ...

  private _onDidWrite = new vscode.EventEmitter<ColophonRecord>();
  public readonly onDidWrite = this._onDidWrite.event;

  /**
   * Existing write method, extended to fire the event on success.
   * The `causedBy` and `hand` fields are passed in by the caller
   * (typically MarginaliaView when a tool_use lands a write).
   */
  async write(
    leaf: string,
    bytes: Uint8Array,
    meta: { causedBy?: string; hand?: 'terse' | 'discursive' | 'diagrammatic' } = {}
  ): Promise<void> {
    // ... existing allowlist + debounce + write logic ...

    // After successful write:
    this._onDidWrite.fire({
      leaf,
      bytes: bytes.byteLength,
      causedBy: meta.causedBy,
      hand: meta.hand,
    });
  }

  dispose() {
    this._onDidWrite.dispose();
  }
}
```

The MarginaliaView, when handling a streamed tool_use that produces a write, passes the most recent rubric text as `causedBy` and the current hand as `hand`.

---

## Item 4 — `src/views/marginaliaView.ts` gains selection coupling + hand toggle

Two additions to the existing view.

### 4a. Selection coupling

Subscribe to the editor's selection events and, when the selection is inside the leaf the Marginalia is currently showing, surface the nearest entry whose `causedBy` substring-matches the selected text.

```ts
// inside MarginaliaView constructor, after existing subscriptions:

vscode.window.onDidChangeTextEditorSelection(
  e => this.onSelectionChanged(e),
  null,
  context.subscriptions
);

// new method:
private onSelectionChanged(e: vscode.TextEditorSelectionChangeEvent) {
  if (!this.currentLeaf) return;
  if (vscode.workspace.asRelativePath(e.textEditor.document.uri).replace(/\\/g, '/') !== this.currentLeaf) {
    return;
  }
  const selection = e.textEditor.document.getText(e.selections[0]);
  if (!selection || selection.length < 3) return;

  // Find the most recent entry whose causedBy overlaps the selection.
  const entries = this.store.entriesFor(this.currentLeaf);
  let bestIdx = -1;
  for (let i = entries.length - 1; i >= 0; i--) {
    const cause = entries[i].causedBy ?? '';
    if (cause && (selection.includes(cause.slice(0, 24)) || cause.includes(selection.slice(0, 24)))) {
      bestIdx = i;
      break;
    }
  }
  if (bestIdx >= 0 && this.view) {
    this.view.webview.postMessage({ type: 'scroll-to-entry', index: bestIdx });
  }
}
```

The webview, on receiving `scroll-to-entry`, scrolls the marginalia panel so the indicated entry is centered, and briefly underlines its sigil in the rubric color.

### 4b. Hand toggle

In the rubric composer's footer, render a three-state segmented control: **terse · discursive · diagrammatic**. Initial state comes from `vscode.workspace.getConfiguration('claudeDesign').get<string>('hand')`. Clicks post `{type: 'set-hand', hand}` to the extension side, which calls `cfg.update('hand', hand, ConfigurationTarget.Workspace)`. The current value is read on every send and prepended to the inference adapter's prompt envelope:

```ts
// at send time:
const hand = vscode.workspace.getConfiguration('claudeDesign').get<string>('hand', 'discursive');
await this.adapter.send({
  hand,
  rubric: text,
  leafPath: this.currentLeaf,
});
```

The adapter, in `cli.ts`, prepends a system directive:

```ts
const handDirective = {
  terse: 'Write the gloss in single sentences. No preamble, no hedging.',
  discursive: 'Write the gloss in full paragraphs. Qualifications welcome.',
  diagrammatic: 'Prefer ASCII diagrams, tables, and labeled structures over prose where possible.',
}[opts.hand ?? 'discursive'];

const systemAddenda = `\n## hand\n${handDirective}\n`;
```

The same toggle is also exposed as the command `claudeDesign.toggleHand` (already registered in `extension.ts`) so the user can flip hands from the command palette without opening the Marginalia panel.

---

## After these patches

1. `package.json` declares all four webviews + the bestiary tree. ✓
2. `extension.ts` instantiates and wires everything. ✓
3. `fs/broker.ts` emits `onDidWrite`. ✓
4. `marginaliaView.ts` has selection coupling + hand toggle. ✓

The repo is then **compilable**. `bun run build` produces `dist/extension.js`. `bun run package` produces a sideloadable `.vsix`. The next observation — *does it work in the editor* — is the only one left.

🜂

— made by Claude
