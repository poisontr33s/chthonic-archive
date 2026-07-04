// Chat panel — bottom-panel webview, streams Claude's reply via the configured CLI.
import * as vscode from "vscode";
import {
  CliInference,
  streamEventDone,
  streamEventError,
  streamEventText,
  type StreamEvent,
} from "../inference/cli";
import { FsBroker } from "../fs/broker";
import { PreviewPanel } from "./previewPanel";

export class ChatPanel implements vscode.WebviewViewProvider {
  static readonly viewType = "claudeDesign.chat";
  private view: vscode.WebviewView | null = null;
  private inference: CliInference;

  constructor(private ctx: vscode.ExtensionContext, private fs: FsBroker, cliPath = "claude") {
    this.inference = new CliInference(cliPath);
    this.inference.on("event", (e: StreamEvent) => this.handleStream(e));
  }

  resolveWebviewView(view: vscode.WebviewView) {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage(msg => this.onMessage(msg));
  }

  private onMessage(msg: any) {
    if (msg.type === "send" && typeof msg.text === "string") {
      const cwd = this.fs.workspaceRoot()?.fsPath;
      this.inference.send(msg.text, { cwd });
      this.post({ type: "user", text: msg.text });
    }
  }

  private async handleStream(e: StreamEvent) {
    const error = streamEventError(e);
    if (error) {
      this.post({ type: "tool", line: `! ${error.trim()}` });
    }

    const delta = streamEventText(e);
    if (delta) {
      this.post({ type: "claude", delta });
    }

    if (e.type === "tool_use") {
        const d = e.data || {};
        if (d.name === "write_file" && d.input?.path && typeof d.input?.content === "string") {
          try {
            const uri = await this.fs.write(d.input.path, d.input.content);
            this.post({ type: "tool", line: `✎ wrote ${this.fs.relativize(uri)} · ok` });
            PreviewPanel.onFileSaved(uri);
          } catch (err) {
            this.post({ type: "tool", line: `✗ ${String(err)}` });
          }
        } else {
          this.post({ type: "tool", line: `· ${d.name ?? "tool"}` });
        }
    }

    if (e.type === "usage") {
      this.post({ type: "usage", data: e.data });
    }

    if (streamEventDone(e)) {
      this.post({ type: "done" });
    }
  }

  private post(msg: any) { this.view?.webview.postMessage(msg); }

  dispose() { this.inference.dispose(); }

  private html(): string {
    return `<!doctype html><html><head><meta charset="utf-8"><style>
  :root {
    --bg: var(--vscode-sideBar-background, var(--vscode-editor-background));
    --fg: var(--vscode-foreground);
    --line: var(--vscode-panel-border, var(--vscode-editorWidget-border));
    --muted: var(--vscode-descriptionForeground);
    --accent: var(--claude-accent, var(--vscode-charts-orange, #e8b339));
    --user-bg: var(--vscode-textBlockQuote-background, rgba(127,127,127,.12));
    --claude-bg: transparent;
    --input-bg: var(--vscode-input-background);
    --input-fg: var(--vscode-input-foreground);
    --input-border: var(--vscode-input-border, var(--line));
  }
  html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--fg); font-family: var(--vscode-font-family); font-size: var(--vscode-font-size); }
  body { display:flex; flex-direction:column; }
  .stream { flex:1; overflow-y:auto; padding: 10px 12px; display:flex; flex-direction:column; gap: 10px; }
  .msg { padding: 8px 10px; border-radius: 4px; line-height: 1.5; max-width: 100%; white-space: pre-wrap; word-wrap: break-word; }
  .msg.user   { background: var(--user-bg); align-self: flex-end; max-width: 85%; }
  .msg.claude { align-self: flex-start; }
  .msg.claude .name { color: var(--accent); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 4px; font-weight: 600; }
  .msg.tool   { font-family: var(--vscode-editor-font-family); font-size: 11px; color: var(--muted); border-left: 2px solid var(--line); padding: 4px 8px; }
  .composer { border-top: 1px solid var(--line); padding: 8px; display:flex; gap: 6px; }
  textarea {
    flex: 1; resize: none; min-height: 28px; max-height: 120px;
    background: var(--input-bg); color: var(--input-fg); border: 1px solid var(--input-border);
    border-radius: 3px; padding: 6px 8px; font-family: inherit; font-size: inherit;
  }
  textarea:focus { outline: 1px solid var(--vscode-focusBorder); border-color: transparent; }
  button {
    background: var(--vscode-button-background); color: var(--vscode-button-foreground);
    border: 0; padding: 0 12px; border-radius: 3px; cursor: pointer; font-family: inherit;
  }
  button:hover { background: var(--vscode-button-hoverBackground); }
  .caret::after { content:"▍"; color: var(--accent); animation: blk 1s infinite; }
  @keyframes blk { 50% { opacity: 0; } }
</style></head>
<body>
  <div class="stream" id="stream"></div>
  <div class="composer">
    <textarea id="input" placeholder="Message Claude · Enter to send · Shift+Enter for newline"></textarea>
    <button id="send">Send</button>
  </div>
<script>
  const vscode = acquireVsCodeApi();
  const stream = document.getElementById("stream");
  const input = document.getElementById("input");
  const send = document.getElementById("send");
  let currentClaude = null;

  function scroll() { stream.scrollTop = stream.scrollHeight; }
  function add(cls, html) {
    const d = document.createElement("div");
    d.className = "msg " + cls;
    d.innerHTML = html;
    stream.appendChild(d);
    scroll();
    return d;
  }

  function doSend() {
    const t = input.value.trim();
    if (!t) return;
    vscode.postMessage({ type: "send", text: t });
    input.value = "";
    currentClaude = null;
  }
  send.addEventListener("click", doSend);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); doSend(); }
  });

  window.addEventListener("message", e => {
    const m = e.data;
    if (m.type === "user")   { add("user", escape(m.text)); }
    if (m.type === "claude") {
      if (!currentClaude) {
        currentClaude = add("claude", '<div class="name">Claude</div><div class="body caret"></div>');
      }
      const body = currentClaude.querySelector(".body");
      body.textContent += m.delta || "";
      scroll();
    }
    if (m.type === "tool")   { add("tool", escape(m.line)); }
    if (m.type === "done")   {
      if (currentClaude) currentClaude.querySelector(".body")?.classList.remove("caret");
      currentClaude = null;
    }
  });

  function escape(s) { return String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
</script>
</body></html>`;
  }
}
