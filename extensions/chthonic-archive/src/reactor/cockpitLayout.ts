// @SID: EXT_COCKPITLAYOUT_V1
import * as vscode from 'vscode';
import type { EnvReport } from './types';

/**
 * Programmatic layout manager for the "Cockpit" configuration:
 *   - Terminal -> AuxiliaryBar (right)
 *   - Entropy Reactor -> Panel (bottom)
 *   - Editor -> Center
 *
 * Also handles hot-swapping PATH/env in running terminals and setting
 * persistent environment variables via VS Code's EnvironmentVariableCollection.
 */
export class CockpitLayout implements vscode.Disposable {
    private disposed = false;
    private cockpitActive = false;

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly envCollection: vscode.EnvironmentVariableCollection,
    ) {}

    /**
     * Force the IDE into Cockpit layout. Idempotent - repeated calls are no-ops.
     */
    async activate(): Promise<void> {
        if (this.disposed || this.cockpitActive) {
            return;
        }

        try {
            await vscode.commands.executeCommand('workbench.action.closeSidebar');
            await vscode.commands.executeCommand('workbench.action.terminal.moveToSidePanel');
            await vscode.commands.executeCommand('workbench.action.focusAuxiliaryBar');
            await vscode.commands.executeCommand('workbench.action.maximizePanel');
            await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');

            this.cockpitActive = true;
            this.output.appendLine('[cockpit] layout activated: sidebar=closed, terminal=AuxBar, panel=maximized, editor=Center');
        } catch (error) {
            this.output.appendLine(`[cockpit] layout activation failed: ${stringifyError(error)}`);
        }
    }

    /**
     * Apply ANNO environment report to all terminals.
     *
     * For running terminals: sends shell commands to mutate env.
     * For future terminals: uses VS Code's EnvironmentVariableCollection
     * which persists across terminal sessions.
     */
    applyTerminalEnv(envReport: EnvReport): void {
        if (this.disposed) {
            return;
        }

        if (!envReport.path_mutations.length) {
            return;
        }

        // Build PATH segments sorted by priority (lowest first = prepended first)
        const pathSegments = envReport.path_mutations
            .sort((a, b) => a.priority - b.priority)
            .map((seg) => seg.path);

        // -----------------------------------------------------------------
        // Persistent: EnvironmentVariableCollection (affects new terminals)
        // -----------------------------------------------------------------

        const delimiter = process.platform === 'win32' ? ';' : ':';

        // Prepend in reverse order so highest-priority segment ends up first
        for (let i = pathSegments.length - 1; i >= 0; i--) {
            this.envCollection.prepend('PATH', `${pathSegments[i]}${delimiter}`);
        }

        // -----------------------------------------------------------------
        // Live: inject into already-running terminals via sendText
        // -----------------------------------------------------------------

        const safePathPattern = /^[A-Za-z0-9_./\\: -]+$/;
        const safeSegments = pathSegments.filter((seg) => {
            if (!safePathPattern.test(seg)) {
                this.output.appendLine(`[cockpit] WARNING: skipping unsafe PATH segment: ${seg}`);
                return false;
            }
            return true;
        });

        for (const terminal of vscode.window.terminals) {
            if (process.platform === 'win32') {
                for (const segment of safeSegments) {
                    terminal.sendText(`$env:PATH = "${segment};$env:PATH"`, true);
                }
            } else {
                for (const segment of safeSegments) {
                    terminal.sendText(`export PATH="${segment}:$PATH"`, true);
                }
            }
        }

        this.output.appendLine(`[cockpit] terminal env updated: ${pathSegments.length} PATH mutations applied`);

        if (envReport.warnings.length > 0) {
            for (const warning of envReport.warnings) {
                this.output.appendLine(`[cockpit] warning: ${warning}`);
            }
        }
    }

    dispose(): void {
        this.disposed = true;
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
