// FS broker — every write Claude triggers funnels through here.
// Enforces a workspace-relative allowlist; anything outside prompts for confirmation.
import * as vscode from "vscode";
import * as path from "node:path";

const ALLOWED_PREFIXES = ["designs/", "assets/", ".claude-design/"];

export interface ColophonEvent {
  /** workspace-relative, forward-slash path */
  path: string;
  /** byte length of the write */
  bytes: number;
  /** ms timestamp the write completed */
  at: number;
}

export class FsBroker {
  private locks = new Map<string, number>();
  private _onDidWrite = new vscode.EventEmitter<ColophonEvent>();

  /** Fires after every successful write Claude has performed through the broker.
   *  The colophon scribe subscribes here to sign each leaf's marginalia. */
  readonly onDidWrite = this._onDidWrite.event;

  constructor(private ctx: vscode.ExtensionContext) {
    ctx.subscriptions.push(this._onDidWrite);
  }

  async write(relPath: string, content: string | Uint8Array): Promise<vscode.Uri> {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) throw new Error("No workspace open");

    const normalized = relPath.replace(/\\/g, "/").replace(/^\.\//, "");
    const allowed = ALLOWED_PREFIXES.some(p => normalized.startsWith(p));

    if (!allowed) {
      const ok = await vscode.window.showWarningMessage(
        `Claude wants to write outside the design sandbox: ${normalized}`,
        { modal: true },
        "Allow once", "Block"
      );
      if (ok !== "Allow once") throw new Error("Write blocked by user");
    }

    const uri = vscode.Uri.joinPath(root.uri, normalized);

    // Per-path debounce — 200ms — to avoid races with other writers.
    const now = Date.now();
    const last = this.locks.get(uri.fsPath) ?? 0;
    if (now - last < 200) await new Promise(r => setTimeout(r, 200 - (now - last)));
    this.locks.set(uri.fsPath, Date.now());

    const dir = vscode.Uri.joinPath(uri, "..");
    try { await vscode.workspace.fs.createDirectory(dir); } catch { /* exists */ }

    const bytes = typeof content === "string" ? new TextEncoder().encode(content) : content;
    await vscode.workspace.fs.writeFile(uri, bytes);

    this._onDidWrite.fire({
      path: normalized,
      bytes: bytes.byteLength,
      at: Date.now(),
    });

    return uri;
  }

  async readManifest(): Promise<any> {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) return { items: [] };
    const uri = vscode.Uri.joinPath(root.uri, ".claude-design", "manifest.json");
    try {
      const raw = await vscode.workspace.fs.readFile(uri);
      return JSON.parse(new TextDecoder().decode(raw));
    } catch { return { items: [] }; }
  }

  workspaceRoot(): vscode.Uri | null {
    return vscode.workspace.workspaceFolders?.[0]?.uri ?? null;
  }

  relativize(uri: vscode.Uri): string {
    const root = this.workspaceRoot();
    if (!root) return uri.fsPath;
    return path.relative(root.fsPath, uri.fsPath).replace(/\\/g, "/");
  }
}
