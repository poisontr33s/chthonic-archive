// TreeView for designs/** — the user-facing output folder.
import * as vscode from "vscode";
import * as path from "node:path";

export class DesignFilesProvider implements vscode.TreeDataProvider<vscode.Uri> {
  private _onDidChangeTreeData = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private ctx: vscode.ExtensionContext) {
    const watcher = vscode.workspace.createFileSystemWatcher("**/designs/**");
    watcher.onDidCreate(() => this.refresh());
    watcher.onDidDelete(() => this.refresh());
    ctx.subscriptions.push(watcher);
  }

  refresh() { this._onDidChangeTreeData.fire(); }

  getTreeItem(uri: vscode.Uri): vscode.TreeItem {
    const item = new vscode.TreeItem(uri, vscode.TreeItemCollapsibleState.None);
    item.command = { command: "vscode.open", title: "Open", arguments: [uri] };
    item.label = path.basename(uri.fsPath);
    return item;
  }

  async getChildren(): Promise<vscode.Uri[]> {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) return [];
    const dir = vscode.Uri.joinPath(root.uri, "designs");
    try {
      const entries = await vscode.workspace.fs.readDirectory(dir);
      return entries
        .filter(([, type]) => type === vscode.FileType.File)
        .map(([name]) => vscode.Uri.joinPath(dir, name));
    } catch { return []; }
  }
}
