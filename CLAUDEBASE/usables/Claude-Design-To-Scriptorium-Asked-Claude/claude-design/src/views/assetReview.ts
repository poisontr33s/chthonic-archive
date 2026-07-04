// TreeView for .claude-design/manifest.json — asset review state.
import * as vscode from "vscode";

type Status = "needs-review" | "approved" | "changes-requested";
interface Item { asset: string; path: string; status: Status; group?: string; subtitle?: string; }

export class AssetReviewProvider implements vscode.TreeDataProvider<Item> {
  private _onDidChangeTreeData = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private ctx: vscode.ExtensionContext) {}

  refresh() { this._onDidChangeTreeData.fire(); }

  getTreeItem(it: Item): vscode.TreeItem {
    const item = new vscode.TreeItem(it.asset, vscode.TreeItemCollapsibleState.None);
    item.description = it.status;
    item.tooltip = it.subtitle ?? "";
    item.iconPath = new vscode.ThemeIcon(
      it.status === "approved" ? "pass" : it.status === "changes-requested" ? "circle-slash" : "circle-large-outline"
    );
    item.command = { command: "claudeDesign.review", title: "Review", arguments: [vscode.Uri.file(it.path)] };
    return item;
  }

  async getChildren(): Promise<Item[]> {
    const root = vscode.workspace.workspaceFolders?.[0];
    if (!root) return [];
    const manifest = vscode.Uri.joinPath(root.uri, ".claude-design", "manifest.json");
    try {
      const raw = await vscode.workspace.fs.readFile(manifest);
      const json = JSON.parse(new TextDecoder().decode(raw));
      return (json.items ?? []) as Item[];
    } catch { return []; }
  }

  async openQuickPick(uri?: vscode.Uri) {
    const pick = await vscode.window.showQuickPick(
      ["approved", "needs-review", "changes-requested"],
      { placeHolder: "Set review status" }
    );
    if (pick) {
      vscode.window.showInformationMessage(`Status: ${pick} — manifest write pending Phase 2.`);
    }
  }
}
