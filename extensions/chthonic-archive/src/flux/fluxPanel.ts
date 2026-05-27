// @SID: EXT_FLUX_PANEL_V1
import * as vscode from 'vscode';

export interface FluxPanelHandlers {
    onGenerate(req: {
        prompt: string; steps: number; guidance: number;
        width: number; height: number; seed: number;
    }): Promise<{ buffer: Buffer; genMs: number; width: number; height: number; channels: number }>;
    onStart(): Promise<void>;
    onStop(): Promise<void>;
}

interface WebviewMessageIn {
    kind: 'generate' | 'start' | 'stop';
    req?: { prompt: string; steps: number; guidance: number; width: number; height: number; seed: number };
}

interface WebviewMessageOut {
    kind: 'image' | 'error' | 'status';
    payload?: unknown;
}

export class FluxPanel implements vscode.Disposable {
    private static readonly viewType = 'chthonic.fluxPanel';
    private panel: vscode.WebviewPanel | null = null;

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly output: vscode.OutputChannel,
        private readonly handlers: FluxPanelHandlers,
    ) {}

    dispose(): void {
        this.panel?.dispose();
        this.panel = null;
    }

    reveal(): void {
        if (this.panel) {
            this.panel.reveal();
            return;
        }
        this.panel = vscode.window.createWebviewPanel(
            FluxPanel.viewType,
            'Chthonic FLUX',
            vscode.ViewColumn.Beside,
            { enableScripts: true, retainContextWhenHidden: true },
        );
        this.panel.webview.html = this.html();
        this.panel.webview.onDidReceiveMessage((m: WebviewMessageIn) => void this.onMessage(m));
        this.panel.onDidDispose(() => { this.panel = null; });
    }

    private async onMessage(m: WebviewMessageIn): Promise<void> {
        try {
            if (m.kind === 'start') {
                await this.handlers.onStart();
                this.post({ kind: 'status', payload: 'started' });
                return;
            }
            if (m.kind === 'stop') {
                await this.handlers.onStop();
                this.post({ kind: 'status', payload: 'stopped' });
                return;
            }
            if (m.kind === 'generate' && m.req) {
                const t0 = Date.now();
                const result = await this.handlers.onGenerate(m.req);
                const wall = Date.now() - t0;
                this.post({
                    kind: 'image',
                    payload: {
                        bytes: new Uint8Array(result.buffer.buffer, result.buffer.byteOffset, result.buffer.byteLength),
                        width: result.width,
                        height: result.height,
                        genMs: result.genMs,
                        wallMs: wall,
                        seed: m.req.seed,
                        prompt: m.req.prompt,
                    },
                });
            }
        } catch (e) {
            const err = e as Error & { code?: string };
            this.output.appendLine(`[flux-panel] ${err.code ?? ''} ${err.message}`);
            this.post({ kind: 'error', payload: { code: err.code ?? '', message: err.message } });
        }
    }

    private post(m: WebviewMessageOut): void {
        this.panel?.webview.postMessage(m);
    }

    private html(): string {
        const nonce = Math.random().toString(36).slice(2);
        return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: blob:; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';" />
<style>
  body { font-family: var(--vscode-font-family); padding: 12px; color: var(--vscode-foreground); }
  fieldset { border: 1px solid var(--vscode-panel-border); padding: 8px 12px; margin-bottom: 12px; }
  legend { padding: 0 4px; opacity: 0.7; }
  label { display: inline-block; margin-right: 12px; }
  input[type=number], input[type=text], textarea { background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); padding: 4px; }
  textarea { width: 100%; min-height: 60px; box-sizing: border-box; }
  button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 6px 14px; cursor: pointer; margin-right: 8px; }
  button:disabled { opacity: 0.5; cursor: default; }
  #gallery { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
  .item { border: 1px solid var(--vscode-panel-border); padding: 8px; }
  .item header { font-size: 11px; opacity: 0.7; margin-bottom: 4px; }
  .item canvas { display: block; max-width: 100%; image-rendering: pixelated; }
  #status { font-family: var(--vscode-editor-font-family); font-size: 11px; opacity: 0.7; margin-top: 8px; }
  #status .ok { color: var(--vscode-charts-green); }
  #status .err { color: var(--vscode-errorForeground); }
</style>
</head>
<body>
  <fieldset>
    <legend>prompt</legend>
    <textarea id="prompt" placeholder="a photograph of an astronaut riding a horse"></textarea>
  </fieldset>
  <fieldset>
    <legend>parameters</legend>
    <label>steps <input id="steps" type="number" value="22" min="1" max="100" /></label>
    <label>guidance <input id="guidance" type="number" value="3.5" step="0.1" /></label>
    <label>width <input id="width" type="number" value="1024" step="16" /></label>
    <label>height <input id="height" type="number" value="1024" step="16" /></label>
    <label>seed <input id="seed" type="number" value="0" /></label>
  </fieldset>
  <button id="generate">generate</button>
  <button id="start">start backend</button>
  <button id="stop">stop backend</button>
  <div id="status">endpoint: bridge://chthonic-flux &mdash; <span id="state">idle</span></div>
  <div id="gallery"></div>
<script nonce="${nonce}">
const vscode = acquireVsCodeApi();
const $ = (id) => document.getElementById(id);
const stateEl = $('state');

function setState(s, cls) { stateEl.textContent = s; stateEl.className = cls || ''; }

$('start').addEventListener('click', () => { setState('starting...'); vscode.postMessage({ kind: 'start' }); });
$('stop').addEventListener('click', () => { setState('stopping...'); vscode.postMessage({ kind: 'stop' }); });

$('generate').addEventListener('click', () => {
  setState('generating...');
  vscode.postMessage({
    kind: 'generate',
    req: {
      prompt: $('prompt').value || 'a photograph of an astronaut riding a horse',
      steps: parseInt($('steps').value, 10),
      guidance: parseFloat($('guidance').value),
      width: parseInt($('width').value, 10),
      height: parseInt($('height').value, 10),
      seed: parseInt($('seed').value, 10) || Math.floor(Math.random() * 2147483647),
    },
  });
});

window.addEventListener('message', (e) => {
  const m = e.data;
  if (m.kind === 'status') { setState(m.payload, 'ok'); return; }
  if (m.kind === 'error') { setState((m.payload && m.payload.code) + ' ' + (m.payload && m.payload.message), 'err'); return; }
  if (m.kind === 'image') {
    const p = m.payload;
    const canvas = document.createElement('canvas');
    canvas.width = p.width; canvas.height = p.height;
    const ctx = canvas.getContext('2d');
    const img = ctx.createImageData(p.width, p.height);
    img.data.set(p.bytes);
    ctx.putImageData(img, 0, 0);
    const item = document.createElement('div');
    item.className = 'item';
    item.innerHTML = '<header></header>';
    item.querySelector('header').textContent = 'gen ' + p.genMs + 'ms / wall ' + p.wallMs + 'ms / seed ' + p.seed + ' / ' + p.width + 'x' + p.height + ' :: ' + (p.prompt || '');
    item.appendChild(canvas);
    $('gallery').prepend(item);
    setState('ok (' + p.genMs + 'ms)', 'ok');
  }
});
</script>
</body>
</html>`;
    }
}
