import * as vscode from 'vscode';

export class DeepFocusLayout {
    constructor(private readonly output: vscode.OutputChannel) {}

    async activate(): Promise<void> {
        await this.applyCommandLayout();
        await vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        await vscode.commands.executeCommand('chthonic.loomView.focus');
        this.output.appendLine('[deep-focus] activated via stable command lane');
    }

    private async applyCommandLayout(): Promise<void> {
        try {
            await vscode.commands.executeCommand('workbench.action.terminal.moveToSidePanel');
            await vscode.commands.executeCommand('workbench.action.toggleAuxiliaryBar');
            await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');
        } catch (error) {
            this.output.appendLine(`[deep-focus] command layout failed: ${stringifyError(error)}`);
        }
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
