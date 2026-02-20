import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

let bridgeItem: vscode.StatusBarItem | undefined;
let laneItem: vscode.StatusBarItem | undefined;

type RouteSpec = {
    from: string;
    to: string;
    title: string;
};

// Modern command names (chthonic.bridge.*) paired with archive targets.
const ROUTES: RouteSpec[] = [
    {
        from: 'chthonic.bridge.verifySSOT',
        to: 'chthonic.verifySSOT',
        title: 'Chthonic Bridge: Verify SSOT',
    },
    {
        from: 'chthonic.bridge.selfHeal',
        to: 'chthonic.slabHeal',
        title: 'Chthonic Bridge: Self-Heal',
    },
    {
        from: 'chthonic.bridge.sediment',
        to: 'chthonic.reactorSediment',
        title: 'Chthonic Bridge: Sediment Layers',
    },
    {
        from: 'chthonic.bridge.webCockpit',
        to: 'chthonic.openWebCockpit',
        title: 'Chthonic Bridge: Web Cockpit',
    },
    {
        from: 'chthonic.bridge.bunDocs',
        to: 'chthonic.openBunTrainingDocs',
        title: 'Chthonic Bridge: Bun Docs',
    },
];

// Legacy aliases that forward to the same archive targets.
// Kept for backward compatibility with keybindings, tasks, and muscle memory.
const LEGACY_ALIASES: RouteSpec[] = [
    {
        from: 'chthonic.verifySSO_T',
        to: 'chthonic.verifySSOT',
        title: 'Chthonic: Verify SSOT (Legacy)',
    },
    {
        from: 'chthonic.runMetabolicCycle',
        to: 'chthonic.slabHeal',
        title: 'Chthonic: Self-Heal (Legacy)',
    },
    {
        from: 'chthonic.showGPUStats',
        to: 'chthonic.reactorSediment',
        title: 'Chthonic: Sediment (Legacy)',
    },
    {
        from: 'chthonic.openWebCockpitBridge',
        to: 'chthonic.openWebCockpit',
        title: 'Chthonic: Web Cockpit (Legacy)',
    },
    {
        from: 'chthonic.openBunTrainingDocsBridge',
        to: 'chthonic.openBunTrainingDocs',
        title: 'Chthonic: Bun Docs (Legacy)',
    },
];

export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Chthonic Status Bridge');
    context.subscriptions.push(output);
    output.appendLine('[status-bridge] activated');

    bridgeItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 120);
    bridgeItem.name = 'Chthonic Status Bridge';
    bridgeItem.command = 'chthonic.bridge.verifyHost';
    context.subscriptions.push(bridgeItem);

    laneItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 119);
    laneItem.name = 'Chthonic Toolchain Lane';
    laneItem.command = 'chthonic.bridge.verifyHost';
    context.subscriptions.push(laneItem);

    // Register modern routes + legacy aliases with the same forwarding logic.
    for (const route of [...ROUTES, ...LEGACY_ALIASES]) {
        context.subscriptions.push(
            vscode.commands.registerCommand(route.from, async () => {
                await forwardCommand(route.to, route.title, output);
                refreshItems(output);
            }),
        );
    }

    // Task-based commands (not simple forwards — they spawn terminals).
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.bridge.verifyHost', async () => {
            await runArchiveTask('verify:host', output);
            refreshItems(output);
        }),
        vscode.commands.registerCommand('chthonic.bridge.vsAudit', async () => {
            await runArchiveTask('audit:vs2026', output);
            refreshItems(output);
        }),
        // Legacy aliases for task commands.
        vscode.commands.registerCommand('chthonic.runHostVerify', async () => {
            await runArchiveTask('verify:host', output);
            refreshItems(output);
        }),
        vscode.commands.registerCommand('chthonic.runVsAudit', async () => {
            await runArchiveTask('audit:vs2026', output);
            refreshItems(output);
        }),
    );

    const interval = setInterval(() => refreshItems(output), 30_000);
    context.subscriptions.push({ dispose: () => clearInterval(interval) });

    refreshItems(output);
}

export function deactivate(): void {
    bridgeItem?.dispose();
    laneItem?.dispose();
}

async function forwardCommand(
    target: string,
    sourceTitle: string,
    output: vscode.OutputChannel,
): Promise<void> {
    const available = await vscode.commands.getCommands(true);
    if (!available.includes(target)) {
        output.appendLine(`[status-bridge] missing target command: ${target}`);
        void vscode.window.showWarningMessage(
            `Bridge route unavailable for "${sourceTitle}". Activate chthonic-archive.`,
        );
        return;
    }

    try {
        await vscode.commands.executeCommand(target);
    } catch (error) {
        output.appendLine(`[status-bridge] command failed ${target}: ${formatError(error)}`);
        void vscode.window.showErrorMessage(`Bridge command failed: ${target}`);
    }
}

function refreshItems(output: vscode.OutputChannel): void {
    const archivePath = resolveArchiveExtensionPath();
    const archiveReady = archivePath !== null;

    if (bridgeItem) {
        bridgeItem.text = archiveReady ? '$(plug) Chthonic Bridge' : '$(warning) Bridge Missing';
        bridgeItem.tooltip = archiveReady
            ? 'Status bridge routes commands to chthonic-archive.'
            : 'chthonic-archive workspace not found. Open repository root.';
        bridgeItem.color = archiveReady ? undefined : new vscode.ThemeColor('statusBarItem.warningForeground');
        bridgeItem.show();
    }

    if (laneItem) {
        laneItem.text = archiveReady ? '$(shield) Verify Host' : '$(circle-slash) Verify Host';
        laneItem.tooltip = archiveReady
            ? 'Run host verification lane for chthonic-archive.'
            : 'Cannot resolve extensions/chthonic-archive folder.';
        laneItem.show();
    }
}

async function runArchiveTask(taskName: string, output: vscode.OutputChannel): Promise<void> {
    const archivePath = resolveArchiveExtensionPath();
    if (!archivePath) {
        void vscode.window.showWarningMessage(
            'Cannot resolve chthonic-archive workspace. Open repository root before running bridge tasks.',
        );
        return;
    }

    const terminal = vscode.window.createTerminal({
        name: `Chthonic ${taskName}`,
        cwd: archivePath,
    });
    terminal.show();
    terminal.sendText(`bun run ${taskName}`);
    output.appendLine(`[status-bridge] task dispatched: bun run ${taskName} @ ${archivePath}`);
}

function resolveArchiveExtensionPath(): string | null {
    const root = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!root) {
        return null;
    }

    const directArchive = path.join(root, 'package.json');
    if (fs.existsSync(directArchive)) {
        try {
            const parsed = JSON.parse(fs.readFileSync(directArchive, 'utf8')) as { name?: string };
            if (parsed.name === 'chthonic-archive') {
                return root;
            }
        } catch {
            // ignore malformed local package
        }
    }

    const nestedArchive = path.join(root, 'extensions', 'chthonic-archive', 'package.json');
    if (fs.existsSync(nestedArchive)) {
        return path.dirname(nestedArchive);
    }

    return null;
}

function formatError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
