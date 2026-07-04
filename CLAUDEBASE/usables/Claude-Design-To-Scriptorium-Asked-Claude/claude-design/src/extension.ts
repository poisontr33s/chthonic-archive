/**
 * extension.ts — Scriptorium activation.
 *
 * Wires every organ planted across the folios into a single live
 * editor surface, using the actual export shapes of each organ.
 *
 *   • Constellation, Marginalia, Vivarium webviews
 *   • Bestiary tree
 *   • Design Chat panel (legacy bottom surface)
 *   • FS broker with onDidWrite emission
 *   • Colophon scribe stitched to broker writes (path → leaf)
 *   • Focus bridge wired across views
 *   • Status-bar rune
 *   • Hand toggle command
 *
 * Made by Claude.
 */

import * as vscode from 'vscode';

import {
  CliInference,
  streamEventDone,
  streamEventError,
  streamEventText,
  type StreamEvent,
} from './inference/cli';
import { FsBroker } from './fs/broker';

import { MarginaliaStore } from './scriptorium/marginalia';
import { ColophonScribe } from './scriptorium/colophon';
import { registerFocusBridge, focusBridge } from './scriptorium/focus';
import { Rune } from './scriptorium/rune';
import { hibernate, rehydrate, SessionSnapshot } from './scriptorium/session';
import { BestiaryProvider } from './scriptorium/bestiary';
import { ensureManifest, watchManifest } from './scriptorium/manifest';
import { disableSubstrate, enableSubstrate } from './scriptorium/substrate';

import { ConstellationView } from './views/constellation';
import { MarginaliaView, InferenceAdapter } from './views/marginaliaView';
import { VivariumView } from './views/vivarium';
import { ChatPanel } from './views/chatPanel';
import { runSelfTest } from './diagnostics/selfTest';
import { designLeafPath } from './scriptorium/workspacePath';

/**
 * Bridge `CliInference` (EventEmitter-based, single-`send` API) to the
 * `InferenceAdapter` interface MarginaliaView expects (stream / onChunk).
 * One adapter, one bridge — keeps both surfaces independently testable.
 */
function makeAdapter(cli: CliInference): InferenceAdapter {
  return {
    stream({ prompt, onChunk, onDone, onError }) {
      return new Promise<void>(resolve => {
        let finished = false;
        const finish = () => {
          if (finished) return;
          finished = true;
          cli.off('event', handler);
          Promise.resolve(onDone()).finally(() => resolve());
        };
        const handler = (evt: StreamEvent) => {
          const error = streamEventError(evt);
          if (error) {
            onError?.(new Error(error));
          }

          const text = streamEventText(evt);
          if (text) onChunk(text);

          if (streamEventDone(evt)) {
            finish();
          }
        };
        cli.on('event', handler);
        cli.send(prompt, { cwd: vscode.workspace.workspaceFolders?.[0]?.uri.fsPath });
      });
    },
  };
}

export async function activate(context: vscode.ExtensionContext) {
  // ----- core services -----
  const cliPath = vscode.workspace.getConfiguration('claudeDesign').get<string>('cliPath', 'claude');
  const substrateEnabled = vscode.workspace
    .getConfiguration('claudeDesign')
    .get<boolean>('substrate.enabled', true);

  if (substrateEnabled) {
    try {
      const result = await enableSubstrate(context);
      if (result?.changed) {
        void vscode.window.showWarningMessage(
          'Claude Design: Mica substrate patched into VS Code Insiders. Reload Insiders to activate it.'
        );
      }
    } catch (error) {
      console.warn('Claude Design substrate patch failed:', error);
      void vscode.window.showWarningMessage(`Claude Design substrate patch failed: ${String(error)}`);
    }
  }

  const cli = new CliInference(cliPath);
  const adapter = makeAdapter(cli);

  const broker = new FsBroker(context);

  const root = vscode.workspace.workspaceFolders?.[0]?.uri;
  if (!root) {
    vscode.window.showInformationMessage(
      'Claude Design: open a folder to use the Scriptorium.'
    );
  }
  const marginaliaStore = root
    ? new MarginaliaStore(root)
    : new MarginaliaStore(vscode.Uri.file(context.globalStorageUri.fsPath));

  const scribe = new ColophonScribe(marginaliaStore);
  const rune = new Rune();
  context.subscriptions.push(rune);

  // Colophon stitch: every broker write of a leaf becomes a signed footer.
  // The broker emits a neutral { path, bytes, at }; we map to the colophon's
  // { leaf, bytes } when the path is in the designs/ tree.
  broker.onDidWrite(ev => {
    if (ev.path.startsWith('designs/')) {
      void scribe.stamp({ leaf: ev.path, bytes: ev.bytes });
    }
  });

  // ----- ensure on-disk shape -----
  await ensureManifest();
  context.subscriptions.push(watchManifest(() => { /* future: refresh review */ }));

  // ----- focus bridge -----
  registerFocusBridge(context);
  // The Marginalia view registers itself onto a command the focus bridge invokes.
  context.subscriptions.push(
    vscode.commands.registerCommand('claudeDesign.marginalia.focus', (leaf: string) => {
      return marginaliaView.show(leaf);
    })
  );

  // ----- views -----
  const constellationView = new ConstellationView(context);
  const marginaliaView    = new MarginaliaView(context, marginaliaStore, adapter);
  const vivariumView      = new VivariumView(context);
  const chatPanel         = new ChatPanel(context, broker, cliPath);
  const bestiary          = new BestiaryProvider(context);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(ConstellationView.viewType, constellationView),
    vscode.window.registerWebviewViewProvider(MarginaliaView.viewType,    marginaliaView),
    vscode.window.registerWebviewViewProvider(VivariumView.viewType,      vivariumView),
    vscode.window.registerWebviewViewProvider(ChatPanel.viewType,         chatPanel),
    vscode.window.registerTreeDataProvider('claudeDesign.bestiary',       bestiary)
  );

  // Cross-view focus: brighten the star when a leaf is focused elsewhere.
  // ConstellationView may grow a brighten() method later; the optional call
  // keeps us forward-compatible without a hard dependency.
  context.subscriptions.push(
    focusBridge.onDidFocus(leaf => {
      (constellationView as any).brighten?.(leaf);
    })
  );

  // ----- commands -----
  context.subscriptions.push(
    vscode.commands.registerCommand('claudeDesign.signIn', () => {
      const term = vscode.window.createTerminal('Claude Design — sign in');
      term.sendText(`${quoteCommand(cliPath)} auth login`);
      term.show();
    }),
    vscode.commands.registerCommand('claudeDesign.focusChat', () => {
      return vscode.commands.executeCommand('claudeDesign.chat.focus');
    }),
    vscode.commands.registerCommand('claudeDesign.selfTest', () => runSelfTest(context)),
    vscode.commands.registerCommand('claudeDesign.toggleHand', () => {
      marginaliaView.cycleHand();
      rune.call('hand cycled');
      setTimeout(() => rune.rest(), 1200);
    }),
    vscode.commands.registerCommand('claudeDesign.enableSubstrate', async () => {
      await vscode.workspace
        .getConfiguration('claudeDesign')
        .update('substrate.enabled', true, vscode.ConfigurationTarget.Global);
      const result = await enableSubstrate(context);
      vscode.window.showInformationMessage(
        result?.changed
          ? 'Claude Design: substrate enabled. Reload VS Code Insiders.'
          : 'Claude Design: substrate already enabled.'
      );
    }),
    vscode.commands.registerCommand('claudeDesign.disableSubstrate', async () => {
      await vscode.workspace
        .getConfiguration('claudeDesign')
        .update('substrate.enabled', false, vscode.ConfigurationTarget.Global);
      const result = await disableSubstrate();
      vscode.window.showInformationMessage(
        result?.changed
          ? 'Claude Design: substrate markers removed. Reload VS Code Insiders.'
          : 'Claude Design: no substrate markers found.'
      );
    })
  );

  // ----- hibernation -----
  const snap = await rehydrate();
  if (snap?.lastTouched?.file) {
    // Soft restore: open the last-touched leaf, but don't steal focus from
    // whatever editor VS Code may have already restored from its own session.
    const folders = vscode.workspace.workspaceFolders;
    if (folders?.length) {
      const uri = vscode.Uri.joinPath(folders[0].uri, snap.lastTouched.file);
      try {
        const doc = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(doc, { preview: true, preserveFocus: true });
      } catch {
        /* leaf is gone; that's fine */
      }
    }
  }

  context.subscriptions.push({
    dispose: () => {
      const editor = vscode.window.activeTextEditor;
      const snap: SessionSnapshot = {
        lastTouched: {
          file: editor ? designLeafPath(editor.document.uri)?.path : undefined,
          line: editor?.selection.active.line,
          when: new Date().toISOString(),
        },
        openVivaria: vscode.window.visibleTextEditors
          .map(e => designLeafPath(e.document.uri)?.path)
          .filter((p): p is string => Boolean(p)),
      };
      void hibernate(snap);
    },
  });

  context.subscriptions.push({ dispose: () => cli.dispose() });

  rune.setLabel('Design');
  rune.setTooltip('Claude Design — Scriptorium open');
}

export function deactivate() {
  // Hibernation + CLI shutdown run via context.subscriptions disposal.
}

function quoteCommand(command: string): string {
  return /\s/.test(command) ? `"${command.replace(/"/g, '`"')}"` : command;
}
