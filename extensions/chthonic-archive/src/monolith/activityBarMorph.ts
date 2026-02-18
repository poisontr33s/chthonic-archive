import * as vscode from 'vscode';
import type { RustificationReport, RustificationTier } from './rustificationScore';
import { iconFileForTier } from './rustificationScore';

type ProposedApiFn = (containerId: string, iconPath: vscode.Uri) => Promise<void> | void;

export class ActivityBarMorph implements vscode.Disposable {
    private readonly fallbackItem: vscode.StatusBarItem;
    private proposalAvailable: boolean | null = null;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly output: vscode.OutputChannel,
        private readonly containerId = 'chthonic-archive',
    ) {
        this.fallbackItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 47);
        this.fallbackItem.command = 'chthonic.refreshRustification';
        this.fallbackItem.tooltip = 'Rustification score and activity bar icon fallback';
        this.fallbackItem.show();
    }

    async update(report: RustificationReport): Promise<void> {
        await vscode.commands.executeCommand('setContext', 'chthonic.rustificationTier', report.tier);
        await vscode.commands.executeCommand('setContext', 'chthonic.rustificationScore', report.score);

        const iconPath = vscode.Uri.joinPath(this.extensionUri, 'resources', iconFileForTier(report.tier));
        const applied = await this.tryApplyProposedIcon(iconPath);
        if (!applied) {
            this.updateFallbackStatus(report);
        } else {
            this.fallbackItem.text = `$(pulse) Slab ${report.score}%`;
            this.fallbackItem.backgroundColor = undefined;
        }
    }

    dispose(): void {
        this.fallbackItem.dispose();
    }

    private async tryApplyProposedIcon(iconPath: vscode.Uri): Promise<boolean> {
        if (this.proposalAvailable === false) {
            return false;
        }

        const windowAny = vscode.window as unknown as Record<string, unknown>;
        const candidates: string[] = [
            'setActivityBarIcon',
            'updateActivityBarIcon',
            'setViewContainerIcon',
            'updateViewContainerIcon',
        ];

        for (const candidate of candidates) {
            const maybeFn = windowAny[candidate];
            if (typeof maybeFn !== 'function') {
                continue;
            }
            try {
                const fn = maybeFn as ProposedApiFn;
                await fn(this.containerId, iconPath);
                this.proposalAvailable = true;
                return true;
            } catch (error) {
                this.output.appendLine(`[morph] ${candidate} failed: ${stringifyError(error)}`);
            }
        }

        this.proposalAvailable = false;
        return false;
    }

    private updateFallbackStatus(report: RustificationReport): void {
        const label = tierLabel(report.tier);
        this.fallbackItem.text = `$(pulse) ${label} ${report.score}%`;
        this.fallbackItem.tooltip = `Rustification ${report.score}%\nPresent: ${report.present.join(', ') || 'none'}\nMissing: ${report.missing.join(', ') || 'none'}`;
    }
}

function tierLabel(tier: RustificationTier): string {
    switch (tier) {
        case 'loom':
            return 'Loom';
        case 'lens':
            return 'Lens';
        default:
            return 'Gate';
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
