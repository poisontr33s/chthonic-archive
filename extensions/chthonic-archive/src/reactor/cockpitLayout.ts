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

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly envCollection: vscode.EnvironmentVariableCollection,
    ) {}

    /**
     * Force the IDE into Cockpit layout.
     */
    async activate(): Promise<void> {
        if (this.disposed) {
            return;
        }

        try {
            // Step 1: Close the primary sidebar (Explorer, Source Control, etc.)
            // to maximize editor real estate in Cockpit mode.
            await vscode.commands.executeCommand('workbench.action.closeSidebar');

            // Step 2: Move terminal to AuxiliaryBar (right side panel).
            // Available since VS Code 1.64.
            await vscode.commands.executeCommand('workbench.action.terminal.moveToSidePanel');

            // Step 3: Ensure the AuxiliaryBar (secondary sidebar) is visible
            await vscode.commands.executeCommand('workbench.action.toggleAuxiliaryBar');

            // Step 4: Maximize the bottom panel (Entropy Reactor view)
            await vscode.commands.executeCommand('workbench.action.toggleMaximizedPanel');

            // Step 5: Focus the editor group
            await vscode.commands.executeCommand('workbench.action.focusActiveEditorGroup');

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

        for (const segment of pathSegments) {
            this.envCollection.prepend('PATH', `${segment}${delimiter}`);
        }

        // -----------------------------------------------------------------
        // Live: inject into already-running terminals via sendText
        // -----------------------------------------------------------------

        for (const terminal of vscode.window.terminals) {
            if (process.platform === 'win32') {
                for (const segment of pathSegments) {
                    terminal.sendText(`$env:PATH = "${segment};$env:PATH"`, true);
                }
            } else {
                for (const segment of pathSegments) {
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
