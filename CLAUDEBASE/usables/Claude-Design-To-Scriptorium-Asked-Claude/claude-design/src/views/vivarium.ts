/**
 * Vivarium — the preview surface as illuminated plate.
 *
 * Folio VI of the Scriptorium build. The third organ. When a leaf is
 * active, the Vivarium renders it as a living specimen in an iframe,
 * reloads on save, and offers three plate frames: bare, parchment,
 * device. Theme variables inherited from VS Code; the plate's mat
 * uses --vscode-editor-background tinted toward parchment.
 *
 * The iframe is sandboxed (allow-scripts only). The artifact loads via
 * a webview-safe URI through asWebviewUri; the localResourceRoots is
 * scoped to designs/ and assets/ so a malformed leaf cannot reach
 * outside its enclosure.
 *
 * Made by Claude.
 */

import * as vscode from 'vscode';
import { designLeafPath, designResourceRoots } from '../scriptorium/workspacePath';

export class VivariumView implements vscode.WebviewViewProvider {
  public static readonly viewType = 'claudeDesign.vivarium';
  private view: vscode.WebviewView | undefined;
  private activeLeaf: vscode.Uri | undefined;
  private saveListener: vscode.Disposable | undefined;

  constructor(private context: vscode.ExtensionContext) {
    vscode.window.onDidChangeActiveTextEditor(
      e => this.onEditorChanged(e),
      null,
      context.subscriptions
    );
    this.saveListener = vscode.workspace.onDidSaveTextDocument(
      doc => this.onDocumentSaved(doc),
      null,
      context.subscriptions
    );
  }

  resolveWebviewView(view: vscode.WebviewView) {
    this.view = view;
    const roots = designResourceRoots();
    view.webview.options = { enableScripts: true, localResourceRoots: roots };
    view.webview.html = renderShell();
    view.webview.onDidReceiveMessage(
      msg => this.onMessage(msg),
      null,
      this.context.subscriptions
    );
    this.onEditorChanged(vscode.window.activeTextEditor);
    // If the view resolved after activeLeaf was set (star clicked before
    // the panel scrolled into view), load the specimen now.
    if (this.activeLeaf) void this.loadSpecimen();
  }

  private onEditorChanged(editor: vscode.TextEditor | undefined) {
    if (!editor) return;
    const rel = designLeafPath(editor.document.uri, /\.(html?|svg)$/i);
    if (!rel) return;
    this.activeLeaf = editor.document.uri;
    void this.loadSpecimen();
  }

  private onDocumentSaved(doc: vscode.TextDocument) {
    if (!this.activeLeaf) return;
    if (doc.uri.toString() === this.activeLeaf.toString()) {
      void this.loadSpecimen();
    }
  }

  private onMessage(msg: any) {
    if (msg.type === 'set-frame' && this.view) {
      this.context.workspaceState.update('claudeDesign.vivarium.frame', msg.frame);
    }
  }

  private async loadSpecimen() {
    if (!this.view || !this.activeLeaf) return;
    const rel = designLeafPath(this.activeLeaf, /\.(html?|svg)$/i)?.path ?? this.activeLeaf.fsPath.replace(/\\/g, '/');
    const webviewUri = this.view.webview.asWebviewUri(this.activeLeaf);
    // Cache-bust with mtime so the iframe actually reloads.
    let stamp = Date.now();
    try {
      const stat = await vscode.workspace.fs.stat(this.activeLeaf);
      stamp = stat.mtime;
    } catch {
      /* fall through */
    }
    this.view.webview.postMessage({
      type: 'specimen',
      path: rel,
      src: `${webviewUri.toString()}?v=${stamp}`,
      frame: this.context.workspaceState.get('claudeDesign.vivarium.frame', 'parchment'),
    });
  }
}

/* ---------- shell ---------- */

function renderShell(): string {
  return /* html */ `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<style>
  :root {
    color-scheme: light dark;
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --fg-dim: color-mix(in oklab, var(--fg) 55%, transparent);
    --fg-faint: color-mix(in oklab, var(--fg) 28%, transparent);
    --rule: color-mix(in oklab, var(--fg) 14%, transparent);
    --rubric: var(--vscode-charts-red, var(--vscode-errorForeground, #b85450));
    --colophon: var(--vscode-charts-orange, var(--vscode-textLink-foreground));
    --mat: color-mix(in oklab, var(--bg) 88%, #e6dcc0 12%);
    --serif: ui-serif, 'Iowan Old Style', 'Georgia', serif;
    --mono: var(--vscode-editor-font-family, 'Cascadia Code', ui-monospace, monospace);
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100vh; overflow: hidden;
    background: var(--bg); color: var(--fg);
    font-family: var(--serif); font-size: 12px;
  }

  .stage { display: grid; grid-template-rows: auto 1fr auto; height: 100vh; }

  .head {
    padding: 8px 12px;
    border-bottom: 1px solid var(--rule);
    display: flex; align-items: baseline; gap: 10px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .12em; text-transform: uppercase;
    color: var(--fg-dim);
  }
  .head .sigil { color: var(--rubric); font-family: var(--serif); font-size: 14px; }
  .head .path { color: var(--fg); letter-spacing: .04em; text-transform: none; }

  .plate {
    overflow: auto;
    display: grid; place-items: center;
    padding: 24px;
    background:
      radial-gradient(ellipse at center top,
        color-mix(in oklab, var(--bg) 92%, var(--colophon) 8%) 0%,
        var(--bg) 60%);
  }

  .frame {
    position: relative;
    background: var(--mat);
    border: 1px solid var(--rule);
    box-shadow: 0 30px 60px -25px rgba(0,0,0,.5),
                0 0 0 1px color-mix(in oklab, var(--colophon) 18%, transparent);
    border-radius: 4px;
  }
  .frame.bare { background: transparent; box-shadow: none; border-color: transparent; padding: 0; }
  .frame.parchment { padding: 24px; }
  .frame.device {
    padding: 14px;
    border-radius: 18px;
    background:
      linear-gradient(180deg,
        color-mix(in oklab, var(--bg) 80%, #000 20%),
        color-mix(in oklab, var(--bg) 70%, #000 30%));
  }
  .frame.device::before {
    content: '';
    position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
    width: 40%; height: 4px; border-radius: 2px;
    background: color-mix(in oklab, var(--fg) 30%, transparent);
  }

  .specimen-shell {
    background: #fff;
    border-radius: 2px;
    overflow: hidden;
    box-shadow: inset 0 0 0 1px var(--rule);
    width: min(900px, 78vw);
    aspect-ratio: 16 / 10;
    display: block;
  }
  .frame.device .specimen-shell {
    width: min(360px, 86vw);
    aspect-ratio: 9 / 16;
    border-radius: 10px;
  }
  iframe.specimen {
    width: 100%; height: 100%;
    border: 0; display: block; background: #fff;
  }

  .empty {
    color: var(--fg-faint); font-style: italic; font-size: 13px;
    font-family: var(--serif);
    text-align: center; max-width: 24em; line-height: 1.6;
  }

  .foot {
    border-top: 1px solid var(--rule);
    padding: 6px 12px;
    display: flex; align-items: center; gap: 10px;
    background: var(--bg);
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .1em; text-transform: uppercase;
    color: var(--fg-dim);
  }
  .foot .frames { display: flex; gap: 6px; margin-left: auto; }
  .foot button {
    background: transparent; border: 1px solid var(--rule);
    color: var(--fg-dim); cursor: pointer;
    padding: 3px 9px; border-radius: 3px;
    font-family: var(--mono); font-size: 10px;
    letter-spacing: .1em; text-transform: uppercase;
  }
  .foot button:hover { color: var(--fg); border-color: var(--colophon); }
  .foot button.active {
    color: var(--colophon); border-color: var(--colophon);
    background: color-mix(in oklab, var(--colophon) 10%, transparent);
  }
  .foot .stamp { color: var(--colophon); }

  .credit {
    position: fixed; right: 10px; bottom: 28px;
    font-family: var(--mono); font-size: 9px;
    color: var(--fg-faint); letter-spacing: .14em; text-transform: uppercase;
    pointer-events: none;
  }
</style>
</head>
<body>
  <div class="stage">
    <header class="head">
      <span class="sigil">◑</span>
      <span>vivarium ·</span>
      <span class="path" id="path">—</span>
    </header>
    <main class="plate" id="plate">
      <div class="empty">no specimen — open an .html or .svg leaf under designs/</div>
    </main>
    <footer class="foot">
      <span class="stamp" id="stamp">awaiting specimen</span>
      <div class="frames">
        <button data-frame="bare">bare</button>
        <button data-frame="parchment" class="active">parchment</button>
        <button data-frame="device">device</button>
      </div>
    </footer>
  </div>
  <div class="credit">vivarium · made by claude</div>

<script>
  const vscode = acquireVsCodeApi();
  const plate = document.getElementById('plate');
  const pathEl = document.getElementById('path');
  const stampEl = document.getElementById('stamp');
  let currentFrame = 'parchment';
  let currentSrc = null;
  let currentPath = null;

  function render() {
    if (!currentSrc) {
      plate.innerHTML = '<div class="empty">no specimen — open an .html or .svg leaf under designs/</div>';
      return;
    }
    plate.innerHTML =
      '<div class="frame ' + currentFrame + '">' +
        '<div class="specimen-shell">' +
          '<iframe class="specimen" sandbox="allow-scripts" src="' + currentSrc + '"></iframe>' +
        '</div>' +
      '</div>';
  }

  function setFrame(name) {
    currentFrame = name;
    document.querySelectorAll('.foot button').forEach(b => {
      b.classList.toggle('active', b.dataset.frame === name);
    });
    vscode.postMessage({ type: 'set-frame', frame: name });
    render();
  }

  document.querySelectorAll('.foot button').forEach(b => {
    b.addEventListener('click', () => setFrame(b.dataset.frame));
  });

  window.addEventListener('message', ev => {
    const m = ev.data;
    if (m.type === 'specimen') {
      currentSrc = m.src;
      currentPath = m.path;
      pathEl.textContent = m.path;
      stampEl.textContent = 'rendered · ' + new Date().toLocaleTimeString();
      if (m.frame && m.frame !== currentFrame) {
        setFrame(m.frame);
      } else {
        render();
      }
    }
  });
</script>
</body>
</html>`;
}
