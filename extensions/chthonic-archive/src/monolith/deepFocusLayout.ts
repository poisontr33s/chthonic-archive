import * as vscode from 'vscode';

type MoveViewFn = (viewId: string, location: unknown) => Promise<void> | void;

export class DeepFocusLayout {
    constructor(private readonly output: vscode.OutputChannel) {}

    async activate(): Promise<void> {
        const usedProposal = await this.tryProposedLayout();
        if (!usedProposal) {
            await this.applyCommandFallback();
        }

        await vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        await vscode.commands.executeCommand('chthonic.loomView.focus');
        this.output.appendLine(`[deep-focus] activated via ${usedProposal ? 'proposed-api' : 'command-fallback'} lane`);
    }

    private async tryProposedLayout(): Promise<boolean> {
        const windowAny = vscode.window as unknown as Record<string, unknown>;
        const moveViewTo = windowAny['moveViewTo'];
        if (typeof moveViewTo !== 'function') {
            return false;
        }

        const locations = [
            windowAny['ViewContainerLocation'] && (windowAny['ViewContainerLocation'] as Record<string, unknown>)['AuxiliaryBar'],
            'auxiliaryBar',
            'secondarySidebar',
        ];

        for (const location of locations) {
            if (!location) {
                continue;
            }
            try {
                await (moveViewTo as MoveViewFn)('terminal', location);
                return true;
            } catch (error) {
                this.output.appendLine(`[deep-focus] proposed moveViewTo failed: ${stringifyError(error)}`);
            }
        }

        return false;
    }

    private async applyCommandFallback(): Promise<void> {
        try {
            await vscode.commands.executeCommand('workbench.action.terminal.moveToSidePanel');
            await vscode.commands.executeCommand('workbench.action.toggleAuxiliaryBar');
            await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');
        } catch (error) {
            this.output.appendLine(`[deep-focus] fallback layout failed: ${stringifyError(error)}`);
        }
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
