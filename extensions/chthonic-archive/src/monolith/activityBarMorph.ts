import * as vscode from 'vscode';
import type { RustificationReport, RustificationTier } from './rustificationScore';
import { iconFileForTier } from './rustificationScore';
import type { EntropyState } from '../reactor/types';

type ProposedApiFn = (containerId: string, iconPath: vscode.Uri) => Promise<void> | void;

export class ActivityBarMorph implements vscode.Disposable {
    private readonly fallbackItem: vscode.StatusBarItem;
    private proposalAvailable: boolean | null = null;
    private latestRustification: RustificationReport | null = null;
    private latestEntropy: EntropyState | null = null;

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
        this.latestRustification = report;
        await vscode.commands.executeCommand('setContext', 'chthonic.rustificationTier', report.tier);
        await vscode.commands.executeCommand('setContext', 'chthonic.rustificationScore', report.score);
        await this.apply();
    }

    async updateEntropy(state: EntropyState): Promise<void> {
        this.latestEntropy = state;
        await vscode.commands.executeCommand('setContext', 'chthonic.decayStatus', state.status);
        await vscode.commands.executeCommand('setContext', 'chthonic.decayScore', Math.round(state.decay_score * 100));
        await this.apply();
    }

    dispose(): void {
        this.fallbackItem.dispose();
    }

    private async apply(): Promise<void> {
        const iconFile = this.resolveIconFile();
        const iconPath = vscode.Uri.joinPath(this.extensionUri, 'resources', iconFile);
        const applied = await this.tryApplyProposedIcon(iconPath);
        if (!applied) {
            this.updateFallbackStatus();
        } else {
            this.fallbackItem.text = this.fallbackSummary();
            this.fallbackItem.backgroundColor = undefined;
        }
    }

    private resolveIconFile(): string {
        const entropy = this.latestEntropy;
        if (entropy) {
            if (entropy.decay_score > 0.5 || entropy.status === 'critical') {
                return 'hazard.svg';
            }
            if (entropy.decay_score < 0.2 && entropy.status === 'pristine') {
                return 'gate.svg';
            }
            return 'lens.svg';
        }

        const tier = this.latestRustification?.tier ?? 'gate';
        return iconFileForTier(tier);
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

    private updateFallbackStatus(): void {
        const rust = this.latestRustification;
        const entropy = this.latestEntropy;

        if (!rust) {
            this.fallbackItem.text = '$(pulse) Slab boot';
            this.fallbackItem.tooltip = 'Rustification score pending';
            return;
        }

        const label = tierLabel(rust.tier);
        const decayPercent = entropy ? Math.round(entropy.decay_score * 100) : null;
        const decayLabel = entropy ? `${entropy.status} ${decayPercent}%` : 'unknown';

        this.fallbackItem.text = `$(pulse) ${label} ${rust.score}% · Decay ${decayPercent ?? '?'}%`;
        this.fallbackItem.tooltip = [
            `Rustification ${rust.score}% (${rust.tier})`,
            `Decay ${decayLabel}`,
            `Present: ${rust.present.join(', ') || 'none'}`,
            `Missing: ${rust.missing.join(', ') || 'none'}`,
            entropy && entropy.critical_tools.length > 0
                ? `Critical tools: ${entropy.critical_tools.join(', ')}`
                : undefined,
        ].filter(Boolean).join('\n');
    }

    private fallbackSummary(): string {
        const rust = this.latestRustification;
        const entropy = this.latestEntropy;
        const rustScore = rust ? `${rust.score}%` : '?';
        const decayScore = entropy ? `${Math.round(entropy.decay_score * 100)}%` : '?';
        return `$(pulse) Slab ${rustScore} · Decay ${decayScore}`;
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
