// Preview webview — beside the active editor, live-reloads on save.
// Inherits VS Code theme via --vscode-* CSS variables injected automatically.
import * as vscode from "vscode";
import * as path from "node:path";

export class PreviewPanel {
  private static current: PreviewPanel | null = null;
  private panel: vscode.WebviewPanel;
  private currentUri: vscode.Uri | null = null;

  private constructor(panel: vscode.WebviewPanel, private ctx: vscode.ExtensionContext) {
    this.panel = panel;
    this.panel.onDidDispose(() => { PreviewPanel.current = null; });
    this.panel.webview.onDidReceiveMessage(msg => this.handleMessage(msg));
    this.render(null);
  }

  static show(ctx: vscode.ExtensionContext, _bridge: unknown) {
    if (PreviewPanel.current) { PreviewPanel.current.panel.reveal(); return; }
    const panel = vscode.window.createWebviewPanel(
      "claudeDesignPreview",
      "Claude Design — Preview",
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );
    PreviewPanel.current = new PreviewPanel(panel, ctx);
    // Auto-load latest design if any.
    PreviewPanel.current.loadLatest();
  }

  static toggleTweaks() {
    PreviewPanel.current?.panel.webview.postMessage({ type: "__activate_edit_mode" });
  }

  static onFileSaved(uri: vscode.Uri) {
    if (!PreviewPanel.current) return;
    if (uri.fsPath.includes(path.sep + "designs" + path.sep)) {
      PreviewPanel.current.render(uri);
    }
  }

  static dispose() { PreviewPanel.current?.panel.dispose(); }

  private async loadLatest() {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) return;
    const dir = vscode.Uri.joinPath(root.uri, "designs");
    try {
      const entries = await vscode.workspace.fs.readDirectory(dir);
      const html = entries.find(([n, t]) => t === vscode.FileType.File && n.endsWith(".html"));
      if (html) this.render(vscode.Uri.joinPath(dir, html[0]));
    } catch { /* no designs yet */ }
  }

  private async render(uri: vscode.Uri | null) {
    this.currentUri = uri;
    let body = `<div class="empty">Open <code>Claude Design: Open Preview Beside</code> on a design file.</div>`;
    if (uri) {
      try {
        const raw = await vscode.workspace.fs.readFile(uri);
        body = new TextDecoder().decode(raw);
      } catch (e) {
        body = `<pre>${String(e)}</pre>`;
      }
    }
    this.panel.webview.html = this.wrap(body, uri);
  }

  private wrap(body: string, uri: vscode.Uri | null): string {
    const title = uri ? path.basename(uri.fsPath) : "Claude Design";
    return `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
<style>
  :root {
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-foreground);
    --line: var(--vscode-panel-border, var(--vscode-editorWidget-border));
    --accent: var(--vscode-charts-orange, var(--vscode-statusBarItem-warningBackground, #e8b339));
  }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg); font-family: var(--vscode-font-family); }
  .chrome { display: flex; align-items: center; gap: 10px; padding: 6px 10px; border-bottom: 1px solid var(--line); font-size: 12px; }
  .chrome .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent); }
  .chrome .file { font-family: var(--vscode-editor-font-family); opacity: .7; }
  .chrome .grow { flex: 1; }
  iframe.preview { width: 100%; height: calc(100vh - 30px); border: 0; background: white; }
  .empty { padding: 40px; opacity: .6; font-family: var(--vscode-editor-font-family); }
</style></head>
<body>
  <div class="chrome"><span class="dot"></span><span>Design</span><span class="file">${uri ? path.basename(uri.fsPath) : ""}</span><span class="grow"></span><span>live</span></div>
  <iframe class="preview" sandbox="allow-scripts" srcdoc="${escapeAttr(body)}"></iframe>
  <script>
    const vscode = acquireVsCodeApi();
    window.addEventListener("message", e => {
      // Forward Tweaks protocol messages from extension → iframe.
      const ifr = document.querySelector("iframe.preview");
      if (ifr && e.data && typeof e.data === "object" && e.data.type) ifr.contentWindow.postMessage(e.data, "*");
    });
  </script>
</body></html>`;
  }

  private handleMessage(_msg: any) {
    // Phase 1+: edit-mode bridge + manifest writes.
  }
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
