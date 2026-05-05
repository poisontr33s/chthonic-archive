// @SID: VAMPIRE_CORPUS_EXTENSION_V1
import * as vscode from 'vscode';
import { CorpusTreeProvider } from './providers/CorpusTreeProvider';
import { TerminalFeedProvider } from './providers/TerminalFeedProvider';
import { LocalExtProvider } from './providers/LocalExtProvider';

export function activate(context: vscode.ExtensionContext): void {
    const workspaceRoot = resolveWorkspaceRoot(context);
    if (!workspaceRoot) {
        void vscode.window.showWarningMessage('Vampire Corpus: no workspace folder found — views inactive.');
        return;
    }

    const corpusProvider = new CorpusTreeProvider(workspaceRoot);
    const terminalFeedProvider = new TerminalFeedProvider(workspaceRoot);
    const localExtProvider = new LocalExtProvider(workspaceRoot);

    // Register tree data providers
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('vampire.corpusView', corpusProvider),
        vscode.window.registerTreeDataProvider('vampire.feedView', terminalFeedProvider),
        vscode.window.registerTreeDataProvider('vampire.localExtView', localExtProvider),
    );

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('vampire.refresh', () => {
            corpusProvider.refresh();
            terminalFeedProvider.refresh();
            localExtProvider.refresh();
        }),

        vscode.commands.registerCommand('vampire.drain', () =>
            runBunTask('vampire:drain', workspaceRoot, 'Vampire Drain'),
        ),

        vscode.commands.registerCommand('vampire.terminalDrain', () =>
            runBunTask('vampire:terminal', workspaceRoot, 'Vampire Terminal Drain'),
        ),

        vscode.commands.registerCommand('vampire.terminalWatch', () =>
            runBunTask('vampire:terminal:watch', workspaceRoot, 'Vampire Terminal Watch'),
        ),

        vscode.commands.registerCommand('vampire.federationValidate', () =>
            runBunTask('vampire:validate', workspaceRoot, 'Vampire Federation Validate'),
        ),

        vscode.commands.registerCommand('vampire.corpusStats', () =>
            runBunTask('session:corpus', workspaceRoot, 'Vampire Corpus Stats'),
        ),

        vscode.commands.registerCommand('vampire.installLocalExt', (item: unknown) =>
            localExtProvider.installExt(item),
        ),

        vscode.commands.registerCommand('vampire.uninstallLocalExt', (item: unknown) =>
            localExtProvider.uninstallExt(item),
        ),

        vscode.commands.registerCommand('vampire.openExtFolder', (item: unknown) =>
            localExtProvider.openFolder(item),
        ),
    );

    // File watchers — refresh views when manifest files change
    const corpusWatcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(workspaceRoot, 'manifest/corpus-state.json'),
    );
    const feedWatcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(workspaceRoot, 'manifest/terminal_session.jsonl'),
    );

    corpusWatcher.onDidChange(() => corpusProvider.refresh());
    feedWatcher.onDidChange(() => terminalFeedProvider.refresh());

    context.subscriptions.push(corpusWatcher, feedWatcher);
}

export function deactivate(): void {
    // nothing
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveWorkspaceRoot(context: vscode.ExtensionContext): string | undefined {
    const configOverride = vscode.workspace.getConfiguration('vampireCorpus').get<string>('workspaceRoot');
    if (configOverride && configOverride.trim().length > 0) {
        return configOverride.trim();
    }
    // Prefer the workspace folder that contains a manifest/corpus-state.json
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) return undefined;
    const { existsSync } = require('node:fs') as typeof import('node:fs');
    const { join } = require('node:path') as typeof import('node:path');
    for (const folder of folders) {
        if (existsSync(join(folder.uri.fsPath, 'manifest', 'corpus-state.json'))) {
            return folder.uri.fsPath;
        }
    }
    // Fall back to first folder
    return folders[0].uri.fsPath;
}

function runBunTask(npmScript: string, cwd: string, label: string): void {
    const terminal = vscode.window.createTerminal({
        name: `⚗ ${label}`,
        cwd,
        iconPath: new vscode.ThemeIcon('terminal-bash'),
    });
    terminal.show(true);
    terminal.sendText(`bun run ${npmScript}`);
}
