import * as vscode from 'vscode';

type BridgeView = {
    label: string;
    description: string;
    command: string;
};

const VIEW_GROUPS: Record<string, BridgeView[]> = {
    'chthonic.mandalaView': [
        {
            label: 'Open Loom View',
            description: 'Focus Chthonic Archive Loom panel',
            command: 'chthonic.openMandala',
        },
    ],
    'chthonic.dependencyView': [
        {
            label: 'Open Abyssal View',
            description: 'Focus Chthonic Archive Abyssal panel',
            command: 'chthonic.openDependencyGraph',
        },
    ],
    'chthonic.healthView': [
        {
            label: 'Open Lens View',
            description: 'Focus Chthonic Archive health/lens panel',
            command: 'chthonic.openHealthReport',
        },
    ],
    'chthonic.themeView': [
        {
            label: 'Switch Theme',
            description: 'Delegate theme switching to Chthonic Archive',
            command: 'chthonic.mandalaBridge.switchTheme',
        },
        {
            label: 'Open Web Cockpit',
            description: 'Open Bun/Next cockpit lane in browser',
            command: 'chthonic.mandalaBridge.openWebCockpit',
        },
        {
            label: 'Open Bun Docs',
            description: 'Open Bun React/Next/Tailwind/SQLite docs',
            command: 'chthonic.mandalaBridge.openBunDocs',
        },
    ],
};

export function activate(context: vscode.ExtensionContext): void {
    const output = vscode.window.createOutputChannel('Chthonic Mandala Bridge');
    context.subscriptions.push(output);
    output.appendLine('[mandala-bridge] activated');

    const commands: Array<[string, () => Thenable<void> | void]> = [
        ['chthonic.openMandala', () => focusArchiveView('chthonic.loomView.focus', output)],
        ['chthonic.openDependencyGraph', () => focusArchiveView('chthonic.abyssalView.focus', output)],
        ['chthonic.openHealthReport', () => focusArchiveView('chthonic.statusView.focus', output)],
        ['chthonic.mandalaBridge.switchTheme', () => delegate('chthonic.switchTheme', output)],
        ['chthonic.mandalaBridge.openWebCockpit', () => delegate('chthonic.openWebCockpit', output)],
        ['chthonic.mandalaBridge.openBunDocs', () => delegate('chthonic.openBunTrainingDocs', output)],
    ];

    for (const [command, handler] of commands) {
        context.subscriptions.push(vscode.commands.registerCommand(command, handler));
    }

    for (const [viewId, items] of Object.entries(VIEW_GROUPS)) {
        context.subscriptions.push(vscode.window.registerTreeDataProvider(viewId, new BridgeTreeProvider(items)));
    }
}

export function deactivate(): void {
    // no-op
}

async function focusArchiveView(focusCommand: string, output: vscode.OutputChannel): Promise<void> {
    const opened = await executeSafe('workbench.view.extension.chthonic-archive', [], output);
    if (!opened) {
        showArchiveMissing();
        return;
    }

    const focused = await executeSafe(focusCommand, [], output);
    if (!focused) {
        await executeSafe('workbench.action.focusSideBar', [], output);
    }
}

async function delegate(command: string, output: vscode.OutputChannel): Promise<void> {
    const ok = await executeSafe(command, [], output);
    if (!ok) {
        showArchiveMissing();
    }
}

async function executeSafe(
    command: string,
    args: unknown[],
    output: vscode.OutputChannel,
): Promise<boolean> {
    try {
        await vscode.commands.executeCommand(command, ...args);
        return true;
    } catch (error) {
        output.appendLine(`[mandala-bridge] command failed: ${command} -> ${formatError(error)}`);
        return false;
    }
}

function showArchiveMissing(): void {
    void vscode.window.showWarningMessage(
        'Chthonic Archive command lane is unavailable. Activate/install chthonic-archive extension.',
    );
}

function formatError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

class BridgeTreeProvider implements vscode.TreeDataProvider<BridgeItem> {
    constructor(private readonly items: BridgeView[]) {}

    getTreeItem(element: BridgeItem): vscode.TreeItem {
        return element;
    }

    getChildren(): Thenable<BridgeItem[]> {
        return Promise.resolve(
            this.items.map((item) => new BridgeItem(item.label, item.description, item.command)),
        );
    }
}

class BridgeItem extends vscode.TreeItem {
    constructor(label: string, description: string, commandId: string) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.description = description;
        this.command = { command: commandId, title: label };
    }
}
