// @SID: EXT_RESTOREORDERLAYOUT_V1
import * as vscode from 'vscode';

export class RestoreOrderLayout {
    constructor(private readonly output: vscode.OutputChannel) {}

    async activate(): Promise<void> {
        await this.applyCommandLayout();
        await vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        this.output.appendLine('[restore-order] completed via stable command lane');
    }

    private async applyCommandLayout(): Promise<void> {
        await executeBestEffort(this.output, [
            ['workbench.view.extension.chthonic-archive'],
            ['chthonic.statusView.focus'],
            ['workbench.action.moveFocusedViewToSecondarySidebar'],
            ['chthonic.loomView.focus'],
            ['workbench.action.moveFocusedViewToPanel'],
            ['workbench.action.positionPanelBottom'],
            ['workbench.action.focusActiveEditorGroup'],
        ]);
    }
}

async function executeBestEffort(
    output: vscode.OutputChannel,
    commands: ReadonlyArray<ReadonlyArray<string>>,
): Promise<void> {
    for (const command of commands) {
        const [id, ...args] = command;
        try {
            await vscode.commands.executeCommand(id, ...args);
        } catch (error) {
            output.appendLine(`[restore-order] command failed (${id}): ${stringifyError(error)}`);
        }
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
