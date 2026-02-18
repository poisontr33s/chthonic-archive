import * as vscode from 'vscode';

type MoveViewFn = (viewId: string, location: unknown) => Promise<void> | void;

const LENS_VIEW_ID = 'chthonic.statusView';
const LOOM_VIEW_ID = 'chthonic.loomView';

export class RestoreOrderLayout {
    constructor(private readonly output: vscode.OutputChannel) {}

    async activate(): Promise<void> {
        const usedProposal = await this.tryProposedLayout();
        if (!usedProposal) {
            await this.applyCommandFallback();
        }

        await vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        this.output.appendLine(`[restore-order] completed via ${usedProposal ? 'proposed-api' : 'command-fallback'} lane`);
    }

    private async tryProposedLayout(): Promise<boolean> {
        const windowAny = vscode.window as unknown as Record<string, unknown>;
        const moveViewTo = windowAny['moveViewTo'];
        if (typeof moveViewTo !== 'function') {
            return false;
        }

        const locations = windowAny['ViewContainerLocation'] as Record<string, unknown> | undefined;
        const lensCandidates = compact([
            locations?.AuxiliaryBar,
            locations?.SecondarySideBar,
            'auxiliaryBar',
            'secondarySidebar',
        ]);
        const loomCandidates = compact([
            locations?.Panel,
            'panel',
        ]);

        for (const lensLocation of lensCandidates) {
            for (const loomLocation of loomCandidates) {
                try {
                    await (moveViewTo as MoveViewFn)(LENS_VIEW_ID, lensLocation);
                    await (moveViewTo as MoveViewFn)(LOOM_VIEW_ID, loomLocation);
                    return true;
                } catch (error) {
                    this.output.appendLine(`[restore-order] proposed moveViewTo failed: ${stringifyError(error)}`);
                }
            }
        }

        return false;
    }

    private async applyCommandFallback(): Promise<void> {
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

function compact(values: Array<unknown>): Array<unknown> {
    return values.filter((value) => value !== undefined && value !== null);
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
