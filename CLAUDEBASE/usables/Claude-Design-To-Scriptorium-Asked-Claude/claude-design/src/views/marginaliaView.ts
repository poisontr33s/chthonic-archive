/**
 * The Marginalia webview.
 *
 * Folio V of the Scriptorium build. Reformulates Folio I's chat panel as
 * manuscript marginalia: the active leaf (file under designs/**) becomes
 * the master text in the left column; the conversation about it becomes
 * gloss in the right margin. Rubrics are the master's hand; gloss is the
 * scribe's; colophons sign the file writes the scribe performs.
 *
 * Inheritance: VS Code theme variables drive the chrome. The parchment
 * tone is computed from --vscode-editor-background; the rubricated red is
 * --vscode-charts-red with a textLink fallback. Theme switches are live.
 *
 * Made by Claude.
 */

import * as vscode from 'vscode';
import { MarginaliaStore, MarginalEntry, Leaf } from '../scriptorium/marginalia';
import { designLeafPath } from '../scriptorium/workspacePath';

/** Minimal contract the marginalia view needs from the inference adapter. */
export interface InferenceAdapter {
  stream(args: {
    prompt: string;
    onChunk: (text: string) => void;
    onDone: () => void | Promise<void>;
    onError?: (err: Error) => void;
  }): Promise<void>;
}

export type ScribeHand = 'terse' | 'discursive' | 'diagrammatic';

export class MarginaliaView implements vscode.WebviewViewProvider {
  public static readonly viewType = 'claudeDesign.marginalia';
  private view: vscode.WebviewView | undefined;
  private activeLeaf: string | undefined;
  private hand: ScribeHand = 'terse';
  private selectionExcerpt: { lines: string; text: string } | undefined;

  constructor(
    private context: vscode.ExtensionContext,
    private store: MarginaliaStore,
    private inference: InferenceAdapter
  ) {
    vscode.window.onDidChangeActiveTextEditor(
      e => this.onEditorChanged(e),
      null,
      context.subscriptions
    );
    vscode.window.onDidChangeTextEditorSelection(
      e => this.onSelectionChanged(e),
      null,
      context.subscriptions
    );

    // Restore last-used hand from workspace state.
    const saved = context.workspaceState.get<ScribeHand>('claudeDesign.hand');
    if (saved === 'terse' || saved === 'discursive' || saved === 'diagrammatic') {
      this.hand = saved;
    }
  }

  /** External hook — wired from the toggleHand command. */
  public cycleHand() {
    const order: ScribeHand[] = ['terse', 'discursive', 'diagrammatic'];
    const next = order[(order.indexOf(this.hand) + 1) % order.length];
    this.setHand(next);
  }

  /** External hook — wired from the focus bridge. Opens the leaf in
   *  an editor (which seeds onEditorChanged) and refreshes immediately. */
  public async show(leaf: string) {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.length) return;
    const uri = vscode.Uri.joinPath(folders[0].uri, leaf);
    try {
      const doc = await vscode.workspace.openTextDocument(uri);
      await vscode.window.showTextDocument(doc, { preview: false });
    } catch {
      // leaf may not exist yet; still set as active so a rubric can
      // bring it into being.
      this.activeLeaf = leaf;
      void this.refresh();
    }
  }

  private setHand(hand: ScribeHand) {
    this.hand = hand;
    void this.context.workspaceState.update('claudeDesign.hand', hand);
    this.view?.webview.postMessage({ type: 'hand', hand });
  }

  resolveWebviewView(view: vscode.WebviewView) {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = renderHtml();
    view.webview.onDidReceiveMessage(msg => this.onMessage(msg), null, this.context.subscriptions);

    // Seed with whatever editor is already active, and current hand.
    this.onEditorChanged(vscode.window.activeTextEditor);
    // If the view resolved after activeLeaf was set (e.g. star clicked before
    // the panel was scrolled into view), push the leaf now so #master is populated.
    if (this.activeLeaf) void this.refresh();
    view.webview.postMessage({ type: 'hand', hand: this.hand });
  }

  private onEditorChanged(editor: vscode.TextEditor | undefined) {
    if (!editor) return;
    const rel = designLeafPath(editor.document.uri);
    if (!rel) return;
    this.activeLeaf = rel.path;
    this.selectionExcerpt = undefined;
    void this.refresh();
  }

  private onSelectionChanged(e: vscode.TextEditorSelectionChangeEvent) {
    if (!this.view || !this.activeLeaf) return;
    const rel = designLeafPath(e.textEditor.document.uri);
    if (!rel || rel.path !== this.activeLeaf) return;

    const sel = e.selections[0];
    if (!sel || sel.isEmpty) {
      this.selectionExcerpt = undefined;
      this.view.webview.postMessage({ type: 'selection', clear: true });
      return;
    }

    const startLine = sel.start.line + 1;
    const endLine = sel.end.line + 1;
    const lines = startLine === endLine ? `L${startLine}` : `L${startLine}\u2013${endLine}`;
    const raw = e.textEditor.document.getText(sel).replace(/\s+/g, ' ').trim();
    const excerpt = raw.length > 140 ? raw.slice(0, 140) + '\u2026' : raw;
    this.selectionExcerpt = { lines, text: excerpt };
    this.view.webview.postMessage({ type: 'selection', lines, excerpt });
  }

  private async refresh() {
    if (!this.view || !this.activeLeaf) return;
    const leaf = await this.store.load(this.activeLeaf);
    const masterText = await readLeafText(this.activeLeaf);
    this.view.webview.postMessage({
      type: 'leaf',
      path: leaf.path,
      masterText,
      entries: leaf.entries.map(serializeForView),
    });
  }

  private async onMessage(msg: any) {
    if (msg.type === 'set-hand' && (msg.hand === 'terse' || msg.hand === 'discursive' || msg.hand === 'diagrammatic')) {
      this.setHand(msg.hand);
      return;
    }

    if (!this.activeLeaf) return;

    if (msg.type === 'rubric' && typeof msg.text === 'string' && msg.text.trim()) {
      const text = msg.text.trim();
      const bound = this.selectionExcerpt;
      const annotated = bound
        ? `[${bound.lines}] \u00ab${bound.text}\u00bb \u2014 ${text}`
        : text;

      const rubric: MarginalEntry = {
        kind: 'rubric',
        hand: 'master',
        timestamp: new Date(),
        text: annotated,
      };
      await this.store.append(this.activeLeaf, rubric);
      // The selection is consumed by the rubric; clear so the next is unbound by default.
      this.selectionExcerpt = undefined;
      this.view?.webview.postMessage({ type: 'selection', clear: true });
      await this.refresh();
      await this.invokeScribe(this.activeLeaf, annotated);
    }

    if (msg.type === 'open-leaf' && typeof msg.path === 'string') {
      const uri = vscode.Uri.joinPath(vscode.workspace.workspaceFolders![0].uri, msg.path);
      const doc = await vscode.workspace.openTextDocument(uri);
      await vscode.window.showTextDocument(doc);
    }
  }

  private async invokeScribe(leafPath: string, rubricText: string) {
    if (!this.view) return;
    const leaf = await this.store.load(leafPath);
    const masterText = await readLeafText(leafPath);
    const recent = leaf.entries
      .slice(-12)
      .map(e => `[${e.hand}/${e.kind}] ${e.text}`)
      .join('\n');

    const handGuidance: Record<ScribeHand, string> = {
      terse:
        'Reply as gloss \u2014 terse, scribal, useful. One paragraph at most. ' +
        'No preamble. If you write a file, name it explicitly so a colophon can be signed.',
      discursive:
        'Reply as discursive gloss \u2014 unfold reasoning, name tradeoffs, ' +
        'cite the master\u2019s rubric when relevant. Multiple paragraphs welcome. ' +
        'If you write a file, name it explicitly so a colophon can be signed.',
      diagrammatic:
        'Reply as diagrammatic gloss \u2014 prefer lists, tables, small ASCII layouts, ' +
        'or structured outlines over prose. Be visual on the page. ' +
        'If you write a file, name it explicitly so a colophon can be signed.',
    };

    const prompt =
      `You are the scribe of the Scriptorium. The master is annotating ` +
      `${leafPath}. Recent marginalia:\n${recent}\n\n` +
      sourceBlock(leafPath, masterText) +
      `The master writes: ${rubricText}\n\n` +
      handGuidance[this.hand];

    let glossBuffer = '';
    await this.inference.stream({
      prompt,
      onChunk: (text: string) => {
        glossBuffer += text;
        this.view?.webview.postMessage({ type: 'gloss-stream', text: glossBuffer });
      },
      onDone: async () => {
        if (!glossBuffer.trim()) return;
        await this.store.append(leafPath, {
          kind: 'gloss',
          hand: 'scribe',
          timestamp: new Date(),
          text: glossBuffer,
        });
        await this.refresh();
      },
      onError: err => {
        this.view?.webview.postMessage({
          type: 'gloss-stream',
          text: `(scribal hand falters — ${err.message})`,
        });
      },
    });
  }
}

async function readLeafText(leafPath: string): Promise<string> {
  try {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.length) return '';
    const uri = vscode.Uri.joinPath(folders[0].uri, leafPath);
    const bytes = await vscode.workspace.fs.readFile(uri);
    return new TextDecoder().decode(bytes);
  } catch {
    return '';
  }
}

function sourceBlock(leafPath: string, text: string): string {
  if (!text.trim()) {
    return `Active leaf source for ${leafPath}: unavailable.\n\n`;
  }
  const maxChars = 24000;
  const truncated = text.length > maxChars;
  const excerpt = truncated ? text.slice(0, maxChars) : text;
  return (
    `Active leaf source for ${leafPath}` +
    `${truncated ? ` (first ${maxChars} of ${text.length} chars)` : ` (${text.length} chars)`}:\n` +
    '```html\n' +
    excerpt +
    '\n```\n\n'
  );
}

function serializeForView(e: MarginalEntry) {
  return {
    kind: e.kind,
    hand: e.hand,
    timestamp: e.timestamp.toISOString(),
    text: e.text,
    colophon: e.colophon,
  };
}

/* ---------- the webview ---------- */

function renderHtml(): string {
  return /* html */ `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  :root {
    color-scheme: light dark;
    --parchment: var(--vscode-editor-background);
    --ink: var(--vscode-editor-foreground);
    --ink-dim: color-mix(in oklab, var(--ink) 60%, transparent);
    --ink-faint: color-mix(in oklab, var(--ink) 35%, transparent);
    --rubric: var(--vscode-charts-red, var(--vscode-errorForeground, #b85450));
    --gloss-rule: color-mix(in oklab, var(--ink) 15%, transparent);
    --colophon: var(--vscode-charts-orange, var(--vscode-textLink-foreground));
    --serif: ui-serif, 'Iowan Old Style', 'Georgia', 'Garamond', serif;
    --mono: var(--vscode-editor-font-family, 'Cascadia Code', ui-monospace, monospace);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    background: var(--parchment); color: var(--ink);
    font-family: var(--serif);
    font-size: 13px; line-height: 1.55;
    height: 100vh; overflow: hidden;
  }

  .stage {
    display: grid; grid-template-rows: auto 1fr auto auto auto;
    height: 100vh; overflow: hidden;
  }

  .leaf-head {
    padding: 10px 14px;
    border-bottom: 1px solid var(--gloss-rule);
    display: flex; align-items: baseline; gap: 10px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .12em; text-transform: uppercase;
    color: var(--ink-dim);
  }
  .leaf-head .sigil { color: var(--rubric); font-family: var(--serif); font-size: 14px; }
  .leaf-head .path { color: var(--ink); letter-spacing: .04em; text-transform: none; font-family: var(--mono); }

  .leaf {
    display: grid;
    grid-template-columns: 1fr minmax(280px, 1.1fr);
    min-height: 0;
  }
  .master {
    overflow: auto;
    padding: 18px 18px 18px 22px;
    border-right: 1px solid var(--gloss-rule);
    font-family: var(--mono);
    font-size: 11.5px;
    line-height: 1.6;
    white-space: pre-wrap;
    color: var(--ink-dim);
  }
  .master:empty::before {
    content: 'no leaf chosen — open a file under designs/';
    color: var(--ink-faint);
    font-style: italic;
    font-family: var(--serif);
    font-size: 12px;
  }

  .marginalia {
    overflow: auto;
    padding: 14px 16px 18px 18px;
    display: flex; flex-direction: column; gap: 18px;
  }
  .marginalia:empty::before {
    content: 'no marginalia yet — write a rubric below';
    color: var(--ink-faint);
    font-style: italic;
  }

  .entry { position: relative; padding-left: 18px; }
  .entry .meta {
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; color: var(--ink-faint);
    margin-bottom: 4px;
  }
  .entry .sigil {
    position: absolute; left: 0; top: 0;
    font-size: 14px; line-height: 1.2;
  }
  .entry.rubric .sigil { color: var(--rubric); }
  .entry.gloss .sigil { color: var(--ink-dim); }
  .entry.colophon .sigil { color: var(--colophon); }

  .entry.rubric .text {
    color: var(--rubric); font-style: italic;
  }
  .entry.gloss .text {
    color: var(--ink);
  }
  .entry.colophon .text {
    color: var(--colophon);
    font-family: var(--mono); font-size: 11px;
  }
  .text { white-space: pre-wrap; }

  .gloss-stream {
    border-left: 2px solid var(--colophon);
    padding-left: 10px; margin-left: 18px;
    color: var(--ink); font-style: italic;
  }
  .gloss-stream::after {
    content: '▍'; animation: blink 1s steps(2) infinite;
    color: var(--colophon); margin-left: 2px;
  }
  @keyframes blink { 50% { opacity: 0; } }

  .selection-bar {
    border-top: 1px solid var(--gloss-rule);
    padding: 6px 14px;
    display: none;
    align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .04em; color: var(--ink-dim);
    background: color-mix(in oklab, var(--rubric) 6%, var(--parchment));
  }
  .selection-bar.on { display: flex; }
  .selection-bar .lines { color: var(--rubric); }
  .selection-bar .excerpt {
    color: var(--ink); font-family: var(--serif); font-style: italic;
    font-size: 11.5px; letter-spacing: 0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    flex: 1; min-width: 0;
  }
  .selection-bar .clear {
    background: transparent; border: 0; color: var(--ink-faint);
    font-family: var(--mono); font-size: 10px; cursor: pointer; padding: 0 4px;
  }
  .selection-bar .clear:hover { color: var(--rubric); }

  .hand-bar {
    border-top: 1px solid var(--gloss-rule);
    padding: 6px 14px;
    display: flex; align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; color: var(--ink-faint); text-transform: uppercase;
  }
  .hand-bar .label { padding-right: 4px; }
  .hand-bar .seg {
    display: inline-flex; border: 1px solid var(--gloss-rule); border-radius: 2px;
    overflow: hidden;
  }
  .hand-bar .seg button {
    background: transparent; border: 0;
    padding: 2px 8px; font-family: var(--mono); font-size: 10px;
    letter-spacing: .08em; text-transform: uppercase;
    color: var(--ink-dim); cursor: pointer;
  }
  .hand-bar .seg button + button { border-left: 1px solid var(--gloss-rule); }
  .hand-bar .seg button.on {
    background: color-mix(in oklab, var(--rubric) 14%, transparent);
    color: var(--rubric);
  }
  .hand-bar .seg button:hover:not(.on) { color: var(--ink); }

  .composer {
    border-top: 1px solid var(--gloss-rule);
    padding: 10px 14px;
    display: flex; align-items: flex-start; gap: 8px;
    background: var(--parchment);
  }
  .composer .sigil {
    color: var(--rubric); font-size: 16px; padding-top: 3px;
  }
  .composer textarea {
    flex: 1;
    background: transparent;
    border: 0; outline: 0; resize: none;
    color: var(--rubric); font-family: var(--serif); font-style: italic;
    font-size: 13.5px; line-height: 1.5;
    padding: 4px 0; min-height: 22px; max-height: 160px;
  }
  .composer textarea::placeholder { color: var(--ink-faint); font-style: italic; }
  .composer .hint {
    font-family: var(--mono); font-size: 9.5px;
    color: var(--ink-faint); letter-spacing: .08em;
    padding-top: 7px; white-space: nowrap;
  }

  .credit {
    position: fixed; right: 10px; bottom: 6px;
    font-family: var(--mono); font-size: 9px;
    color: var(--ink-faint); letter-spacing: .14em; text-transform: uppercase;
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="stage">
    <header class="leaf-head">
      <span class="sigil">❦</span>
      <span>marginalia ·</span>
      <span class="path" id="leaf-path">—</span>
    </header>
    <div class="leaf">
      <pre class="master" id="master"></pre>
      <div class="marginalia" id="marginalia"></div>
    </div>
    <div class="selection-bar" id="selbar">
      <span class="lines" id="sel-lines">—</span>
      <span class="excerpt" id="sel-excerpt"></span>
      <button class="clear" id="sel-clear" type="button" title="unbind selection">✕</button>
    </div>
    <div class="hand-bar">
      <span class="label">hand</span>
      <span class="seg" id="hand-seg">
        <button type="button" data-hand="terse">terse</button>
        <button type="button" data-hand="discursive">discursive</button>
        <button type="button" data-hand="diagrammatic">diagrammatic</button>
      </span>
    </div>
    <form class="composer" id="composer" autocomplete="off">
      <span class="sigil">❦</span>
      <textarea id="rubric" rows="1" placeholder="write a rubric…"></textarea>
      <span class="hint">⏎ to send · ⇧⏎ for line</span>
    </form>
  </div>
  <div class="credit">marginalia · made by claude</div>

<script>
  const vscode = acquireVsCodeApi();
  const masterEl = document.getElementById('master');
  const margEl = document.getElementById('marginalia');
  const pathEl = document.getElementById('leaf-path');
  const rubricEl = document.getElementById('rubric');
  const composerEl = document.getElementById('composer');

  let streamEl = null;

  function renderEntries(entries) {
    margEl.innerHTML = '';
    streamEl = null;
    for (const e of entries) {
      const node = document.createElement('div');
      node.className = 'entry ' + e.kind;
      const sigil = { rubric: '❦', gloss: '¶', colophon: '⌘' }[e.kind] || '·';
      const when = new Date(e.timestamp);
      const stamp = when.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      const meta = e.kind + ' · ' + stamp + ' · ' + e.hand;
      let body = e.text;
      if (e.kind === 'colophon' && e.colophon) {
        body = '— ' + e.colophon.path + ' · ' + e.colophon.bytes + ' bytes · ' + e.colophon.sig;
      }
      node.innerHTML =
        '<span class="sigil">' + sigil + '</span>' +
        '<div class="meta">' + meta + '</div>' +
        '<div class="text"></div>';
      node.querySelector('.text').textContent = body;
      margEl.appendChild(node);
    }
    margEl.scrollTop = margEl.scrollHeight;
  }

  const selBar = document.getElementById('selbar');
  const selLines = document.getElementById('sel-lines');
  const selExcerpt = document.getElementById('sel-excerpt');
  const selClear = document.getElementById('sel-clear');
  const handSeg = document.getElementById('hand-seg');

  function paintHand(hand) {
    handSeg.querySelectorAll('button').forEach(b => {
      b.classList.toggle('on', b.dataset.hand === hand);
    });
  }

  handSeg.addEventListener('click', ev => {
    const btn = ev.target.closest('button[data-hand]');
    if (!btn) return;
    paintHand(btn.dataset.hand);
    vscode.postMessage({ type: 'set-hand', hand: btn.dataset.hand });
  });

  selClear.addEventListener('click', () => {
    selBar.classList.remove('on');
    vscode.postMessage({ type: 'selection-cleared' });
  });

  window.addEventListener('message', ev => {
    const m = ev.data;
    if (m.type === 'leaf') {
      pathEl.textContent = m.path;
      masterEl.textContent = m.masterText || '';
      renderEntries(m.entries);
    } else if (m.type === 'gloss-stream') {
      if (!streamEl) {
        streamEl = document.createElement('div');
        streamEl.className = 'gloss-stream';
        margEl.appendChild(streamEl);
      }
      streamEl.textContent = m.text;
      margEl.scrollTop = margEl.scrollHeight;
    } else if (m.type === 'hand') {
      paintHand(m.hand);
    } else if (m.type === 'selection') {
      if (m.clear) {
        selBar.classList.remove('on');
      } else {
        selLines.textContent = m.lines;
        selExcerpt.textContent = '«' + m.excerpt + '»';
        selBar.classList.add('on');
      }
    }
  });

  function autosize() {
    rubricEl.style.height = 'auto';
    rubricEl.style.height = Math.min(rubricEl.scrollHeight, 160) + 'px';
  }
  rubricEl.addEventListener('input', autosize);

  composerEl.addEventListener('submit', ev => {
    ev.preventDefault();
    const text = rubricEl.value.trim();
    if (!text) return;
    vscode.postMessage({ type: 'rubric', text });
    rubricEl.value = '';
    autosize();
  });

  rubricEl.addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault();
      composerEl.requestSubmit();
    }
  });
</script>
</body>
</html>`;
}
