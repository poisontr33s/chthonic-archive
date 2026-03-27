// @SID: EXT_ACTIVITYBARMORPH_V1
import * as vscode from 'vscode';
import type { RustificationReport, RustificationTier } from './rustificationScore';
import { iconFileForTier } from './rustificationScore';
import type { EntropyState } from '../reactor/types';

export class ActivityBarMorph implements vscode.Disposable {
    private readonly fallbackItem: vscode.StatusBarItem;
    private fallbackNoticeEmitted = false;
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
        if (!this.fallbackNoticeEmitted) {
            this.output.appendLine('[morph] dynamic Activity Bar icon updates are unavailable on stable API; using status lane fallback');
            this.fallbackNoticeEmitted = true;
        }
        this.updateFallbackStatus();
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

        const decayText = decayPercent !== null ? ` · Decay ${decayPercent}%` : '';
        this.fallbackItem.text = `$(pulse) ${label} ${rust.score}%${decayText}`;
        this.fallbackItem.tooltip = [
            `Toolchain completeness: ${rust.score}% (${rust.tier})`,
            `Present: ${rust.present.join(', ') || 'none'}`,
            `Missing: ${rust.missing.join(', ') || 'none'}`,
            entropy ? `Workspace health: ${decayLabel}` : 'Workspace health: entropy disabled',
            entropy && entropy.critical_tools.length > 0
                ? `Critical tools: ${entropy.critical_tools.join(', ')}`
                : undefined,
        ].filter(Boolean).join('\n');
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
