import * as vscode from 'vscode';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { ChthonicChatProvider } from './sdk/webview';
import { EntropyWorkerClient } from './entropy/entropyWorkerClient';
import { EntropyDecorationProvider } from './entropy/entropyDecorations';
import { AbyssalPaneProvider } from './entropy/archiveAbyssalView';

export function activate(context: vscode.ExtensionContext) {
    console.log('☥ Chthonic Archive extension activated');

    // --- SDK Chat Panel ---
    const outputChannel = vscode.window.createOutputChannel('Chthonic SDK');
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
    const harnessPath = path.join(
        workspaceRoot || '',
        'meta-ide', 'copilot-sdk', 'harness.ts',
    );
    const chatProvider = new ChthonicChatProvider(
        context.extensionUri,
        harnessPath,
        (msg: string) => outputChannel.appendLine(`[${new Date().toISOString()}] ${msg}`),
    );
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ChthonicChatProvider.viewType, chatProvider),
    );

    // --- Entropy Engine (worker + decorations + webview) ---
    const entropyConfig = vscode.workspace.getConfiguration('chthonic');
    const entropyEnabled = entropyConfig.get<boolean>('entropy.enabled', true);
    const entropyMaxFiles = entropyConfig.get<number>('entropy.maxFiles', 10000);
    const entropyScanIntervalMs = entropyConfig.get<number>('entropy.scanIntervalMs', 20000);
    const entropyDecorationDebounceMs = entropyConfig.get<number>('entropy.decorationDebounceMs', 120);
    const entropyDecorationBatch = entropyConfig.get<number>('entropy.decorationBatchSize', 240);

    const entropyClient = new EntropyWorkerClient(context, outputChannel);
    const entropyDecorations = new EntropyDecorationProvider(
        entropyClient,
        entropyDecorationDebounceMs,
        entropyDecorationBatch,
    );
    const abyssalProvider = new AbyssalPaneProvider(context.extensionUri, entropyClient);
    abyssalProvider.setRootPath(workspaceRoot);

    context.subscriptions.push(
        entropyClient,
        entropyDecorations,
        abyssalProvider,
        vscode.window.registerFileDecorationProvider(entropyDecorations),
        vscode.window.registerWebviewViewProvider(AbyssalPaneProvider.viewType, abyssalProvider),
    );

    if (workspaceRoot && entropyEnabled) {
        entropyClient.start(workspaceRoot, entropyMaxFiles, entropyScanIntervalMs);
    }

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            entropyClient.refreshFile(document.uri);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.entropyRefresh', () => {
            entropyClient.rescanNow();
            entropyClient.requestGraph(260);
            vscode.window.showInformationMessage('Chthonic entropy scan requested');
        }),
    );

    // --- Theme Switcher ---
    const themeProvider = new ThemeTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.themeView', themeProvider);

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.switchTheme', async () => {
            const themes = [
                { label: '$(paintcan) Flesh & Earth', description: 'Warm earth · WCAG AA · Distribution palette', id: 'Chthonic Mandala - Flesh & Earth' },
                { label: '$(zap) ROGBIV', description: 'SSOT spectral · FA¹⁻⁵ canonical hexes', id: 'Chthonic Mandala - ROGBIV' },
            ];
            const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme');
            const pick = await vscode.window.showQuickPick(themes.map(t => ({
                ...t,
                picked: current === t.id
            })), { placeHolder: `Current: ${current}` });
            if (pick) {
                await vscode.workspace.getConfiguration('workbench').update('colorTheme', pick.id, vscode.ConfigurationTarget.Workspace);
                vscode.window.showInformationMessage(`Theme: ${pick.id}`);
                themeProvider.refresh();
            }
        })
    );

    // --- Status Bar: SSOT Hash ---
    const config = vscode.workspace.getConfiguration('chthonic');
    if (config.get<boolean>('showSSOTHash', true)) {
        const ssotItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
        ssotItem.command = 'chthonic.verifySSOT';
        ssotItem.tooltip = 'SSOT integrity hash — click to verify';
        context.subscriptions.push(ssotItem);
        updateSSOTHash(ssotItem);

        // Re-check on save
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(doc => {
                if (doc.fileName.includes('copilot-instructions')) {
                    updateSSOTHash(ssotItem);
                }
            })
        );
    }

    // --- Status Bar: Lineage ---
    if (config.get<boolean>('showLineage', true)) {
        const lineageItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 49);
        lineageItem.text = '$(git-branch) ☥ main';
        lineageItem.tooltip = 'Chthonic lineage';
        lineageItem.show();
        context.subscriptions.push(lineageItem);
    }

    // --- Status View ---
    const statusProvider = new StatusTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.statusView', statusProvider);

    // --- SSOT Verify Command ---
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.verifySSOT', async () => {
            const hash = computeSSOTHash();
            if (hash) {
                vscode.window.showInformationMessage(`SSOT SHA-256: ${hash.substring(0, 16)}…`);
            } else {
                vscode.window.showWarningMessage('SSOT file not found');
            }
        })
    );

    // --- Refresh Command ---
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.refreshStatus', () => {
            statusProvider.refresh();
            themeProvider.refresh();
            entropyClient.rescanNow();
            entropyClient.requestGraph(260);
        })
    );
}

export function deactivate() {}

// --- SSOT Hash ---
function computeSSOTHash(): string | null {
    const ws = vscode.workspace.workspaceFolders?.[0];
    if (!ws) return null;
    const ssotRel = vscode.workspace.getConfiguration('chthonic').get<string>('ssotPath', '.github/copilot-instructions.md');
    const ssotPath = path.join(ws.uri.fsPath, ssotRel);
    if (!fs.existsSync(ssotPath)) return null;
    const content = fs.readFileSync(ssotPath, 'utf-8');
    const canonical = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
        .split('\n').map(l => l.trimEnd()).join('\n').trim();
    return crypto.createHash('sha256').update(canonical, 'utf-8').digest('hex');
}

function updateSSOTHash(item: vscode.StatusBarItem) {
    const hash = computeSSOTHash();
    if (hash) {
        item.text = `$(shield) ${hash.substring(0, 8)}`;
        item.show();
    } else {
        item.text = '$(shield) SSOT ??';
        item.show();
    }
}

// --- Theme Tree ---
class ThemeTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;
    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || '';
        const themes = [
            { name: 'Chthonic Mandala - Flesh & Earth', short: 'Flesh & Earth', icon: '🌍', desc: 'Warm earth · Distribution' },
            { name: 'Chthonic Mandala - ROGBIV', short: 'ROGBIV', icon: '🌈', desc: 'SSOT spectral · Research' },
        ];
        return themes.map(t => {
            const active = current === t.name;
            const item = new vscode.TreeItem(
                `${active ? '◉' : '○'} ${t.icon} ${t.short}`,
                vscode.TreeItemCollapsibleState.None
            );
            item.tooltip = `${t.name}\n${t.desc}${active ? '\n\n✅ ACTIVE' : ''}`;
            item.description = active ? 'active' : '';
            item.command = { command: 'chthonic.switchTheme', title: 'Switch' };
            return item;
        });
    }
}

// --- Status Tree ---
class StatusTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;
    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const hash = computeSSOTHash();
        const items: vscode.TreeItem[] = [];

        const ssotItem = new vscode.TreeItem(
            `$(shield) SSOT: ${hash ? hash.substring(0, 12) + '…' : 'not found'}`,
            vscode.TreeItemCollapsibleState.None
        );
        ssotItem.command = { command: 'chthonic.verifySSOT', title: 'Verify' };
        items.push(ssotItem);

        const themeItem = new vscode.TreeItem(
            `$(paintcan) Theme: ${(vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || 'default').replace('Chthonic Mandala - ', '')}`,
            vscode.TreeItemCollapsibleState.None
        );
        themeItem.command = { command: 'chthonic.switchTheme', title: 'Switch' };
        items.push(themeItem);

        return items;
    }
}
