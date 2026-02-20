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

const ROUTES: RouteSpec[] = [
    {
        from: 'chthonic.verifySSO_T',
        to: 'chthonic.verifySSOT',
        title: 'Chthonic: Verify SSOT (Bridge)',
    },
    {
        from: 'chthonic.runMetabolicCycle',
        to: 'chthonic.slabHeal',
        title: 'Chthonic: Run Self-Heal Loop (Bridge)',
    },
    {
        from: 'chthonic.showGPUStats',
        to: 'chthonic.reactorSediment',
        title: 'Chthonic: Run Reactor Sediment (Bridge)',
    },
    {
        from: 'chthonic.openWebCockpitBridge',
        to: 'chthonic.openWebCockpit',
        title: 'Chthonic: Open Web Cockpit (Bridge)',
    },
    {
        from: 'chthonic.openBunTrainingDocsBridge',
        to: 'chthonic.openBunTrainingDocs',
        title: 'Chthonic: Open Bun Training Docs (Bridge)',
    },
];

export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Chthonic Status Bridge');
    context.subscriptions.push(output);
    output.appendLine('[status-bridge] activated');

    bridgeItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 120);
    bridgeItem.name = 'Chthonic Status Bridge';
    bridgeItem.command = 'chthonic.runHostVerify';
    context.subscriptions.push(bridgeItem);

    laneItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 119);
    laneItem.name = 'Chthonic Toolchain Lane';
    laneItem.command = 'chthonic.runHostVerify';
    context.subscriptions.push(laneItem);

    for (const route of ROUTES) {
        context.subscriptions.push(
            vscode.commands.registerCommand(route.from, async () => {
                await forwardCommand(route.to, route.title, output);
                refreshItems(output);
            }),
        );
    }

    context.subscriptions.push(
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
            ? 'Legacy statusbar commands are routed to chthonic-archive.'
            : 'chthonic-archive workspace not found. Open repository root.';
        bridgeItem.color = archiveReady ? undefined : new vscode.ThemeColor('statusBarItem.warningForeground');
        bridgeItem.show();
    }

    if (laneItem) {
        laneItem.text = archiveReady ? '$(shield) Verify Host' : '$(circle-slash) Verify Host';
        laneItem.tooltip = archiveReady
            ? 'Run heavyweight host verification lane for chthonic-archive.'
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
