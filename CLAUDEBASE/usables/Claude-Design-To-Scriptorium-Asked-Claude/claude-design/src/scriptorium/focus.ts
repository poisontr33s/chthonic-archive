/**
 * Focus bridge — the wire between Constellation and Marginalia.
 *
 * A single command, `claudeDesign.focusLeaf`, that any view can
 * invoke with a workspace-relative leaf path. The command:
 *   1. opens the leaf in the editor (which the Vivarium watches),
 *   2. reveals the Marginalia view and tells it to load that leaf,
 *   3. emits a focus event the Constellation listens for so it can
 *      brighten the corresponding star.
 *
 * The bridge does not know about the views themselves — they
 * subscribe to its event emitter. Loose coupling on purpose.
 *
 * Made by Claude.
 */

import * as vscode from 'vscode';

class FocusBridge {
  private _onDidFocus = new vscode.EventEmitter<string>();
  public readonly onDidFocus = this._onDidFocus.event;

  async focus(leaf: string): Promise<void> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders?.length) return;
    const uri = vscode.Uri.joinPath(folders[0].uri, leaf);
    try {
      const doc = await vscode.workspace.openTextDocument(uri);
      await vscode.window.showTextDocument(doc, { preview: false });
    } catch {
      // leaf may not exist on disk yet; that's allowed.
    }
    await vscode.commands.executeCommand('claudeDesign.marginalia.focus', leaf);
    this._onDidFocus.fire(leaf);
  }
}

export const focusBridge = new FocusBridge();

export function registerFocusBridge(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('claudeDesign.focusLeaf', (leaf: string) =>
      focusBridge.focus(leaf)
    )
  );
}

/**
 * Constellation, in its webview message handler:
 *   case 'star-clicked':
 *     vscode.commands.executeCommand('claudeDesign.focusLeaf', msg.leaf);
 *
 * Marginalia, on extension side:
 *   commands.registerCommand('claudeDesign.marginalia.focus', leaf => {
 *     marginaliaView.show(leaf);
 *   });
 *
 * Constellation, listening for cross-view focus:
 *   focusBridge.onDidFocus(leaf => {
 *     constellationView.brighten(leaf);
 *   });
 */
