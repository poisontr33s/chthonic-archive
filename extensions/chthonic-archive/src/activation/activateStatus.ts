// @SID: EXT_ACTIVATION_STATUS_V1
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import type { LaneRegistry } from '../runtime/laneState';
import { SSOT_POINTER } from '../ssot-paths';

export interface ActivateStatusDeps {
    readonly workspaceRoot: string | null;
    readonly chthonicConfig: vscode.WorkspaceConfiguration;
    readonly laneRegistry: LaneRegistry;
}

export function activateStatus(context: vscode.ExtensionContext, deps: ActivateStatusDeps): void {
    let fpItem: vscode.StatusBarItem | undefined;
    let lineageItem: vscode.StatusBarItem | undefined;
    let lineageInterval: NodeJS.Timeout | undefined;

    const stopFingerprint = (): void => {
        fpItem?.dispose();
        fpItem = undefined;
    };

    const refreshFingerprint = (publish = true): void => {
        if (!fpItem) return;
        updatePolicyFingerprint(fpItem, deps, publish);
    };

    const startFingerprint = (): void => {
        if (fpItem) {
            refreshFingerprint();
            return;
        }
        fpItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
        fpItem.command = 'chthonic.verifySSOT';
        fpItem.tooltip = 'Policy fingerprint — click to verify integrity';
        context.subscriptions.push(fpItem);
        refreshFingerprint();
    };

    const stopLineage = (): void => {
        if (lineageInterval) {
            clearInterval(lineageInterval);
            lineageInterval = undefined;
        }
        lineageItem?.dispose();
        lineageItem = undefined;
    };

    const refreshLineage = (publish = true): void => {
        if (!lineageItem) return;
        const lineage = readGitLineage(deps.workspaceRoot);
        lineageItem.text = `$(git-branch) ${lineage.label}`;
        lineageItem.tooltip = lineage.tooltip;
        lineageItem.show();
        if (publish) {
            deps.laneRegistry.set({
                name: 'git-lineage',
                state: lineage.label === 'lineage-error' ? 'DEGRADED' : 'READY',
                reason: lineage.label,
            });
        }
    };

    const startLineage = (): void => {
        if (!lineageItem) {
            lineageItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 49);
            lineageItem.command = 'workbench.view.scm';
            context.subscriptions.push(lineageItem);
        }
        refreshLineage();
        if (!lineageInterval) {
            lineageInterval = setInterval(refreshLineage, 6_000);
        }
    };

    const sync = (): void => {
        deps.chthonicConfig.get<boolean>('showSSOTHash', false) ? startFingerprint() : stopFingerprint();
        deps.chthonicConfig.get<boolean>('showLineage', false) ? startLineage() : stopLineage();
    };

    sync();
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc) => {
            if (fpItem && doc.fileName.includes(path.basename(SSOT_POINTER, '.md'))) {
                refreshFingerprint();
            }
        }),
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (
                event.affectsConfiguration('chthonic.showSSOTHash')
                || event.affectsConfiguration('chthonic.showLineage')
            ) {
                sync();
            }
        }),
        deps.laneRegistry.onDidChange((lane) => {
            if (lane.name === 'policyOracle') {
                refreshFingerprint(false);
            }
            if (lane.name === 'git-lineage') {
                refreshLineage(false);
            }
        }),
        { dispose: stopFingerprint },
        { dispose: stopLineage },
    );
}

export function computePolicyFingerprint(deps: Pick<ActivateStatusDeps, 'workspaceRoot' | 'chthonicConfig'>): string | null {
    if (!deps.workspaceRoot) return null;
    const policyRel = deps.chthonicConfig.get<string>('ssotPath', SSOT_POINTER);
    const policyPath = path.join(deps.workspaceRoot, policyRel);
    if (!fs.existsSync(policyPath)) return null;
    const content = fs.readFileSync(policyPath, 'utf-8');
    const canonical = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
        .split('\n').map((line) => line.trimEnd()).join('\n').trim();
    return crypto.createHash('sha256').update(canonical, 'utf-8').digest('hex');
}

function updatePolicyFingerprint(item: vscode.StatusBarItem, deps: ActivateStatusDeps, publish: boolean): void {
    const hash = computePolicyFingerprint(deps);
    if (hash) {
        item.text = `$(shield) ${hash.substring(0, 8)}`;
        item.show();
        if (publish) {
            deps.laneRegistry.set({ name: 'policyOracle', state: 'READY', reason: hash.substring(0, 16) });
        }
    } else {
        item.text = '$(shield) Policy ??';
        item.show();
        if (publish) {
            deps.laneRegistry.set({ name: 'policyOracle', state: 'MISSING', reason: 'policy file not found' });
        }
    }
}

interface GitLineage {
    label: string;
    tooltip: string;
}

function readGitLineage(workspaceRoot: string | null): GitLineage {
    if (!workspaceRoot) {
        return {
            label: 'no-workspace',
            tooltip: 'Chthonic lineage unavailable: no workspace root.',
        };
    }

    const gitDir = path.join(workspaceRoot, '.git');
    const headPath = path.join(gitDir, 'HEAD');
    if (!fs.existsSync(headPath)) {
        return {
            label: 'no-git',
            tooltip: 'Chthonic lineage unavailable: .git/HEAD not found.',
        };
    }

    try {
        const head = fs.readFileSync(headPath, 'utf8').trim();
        if (!head) {
            return {
                label: 'detached',
                tooltip: 'Chthonic lineage unavailable: empty git HEAD.',
            };
        }

        if (!head.startsWith('ref:')) {
            const detached = head.slice(0, 8);
            return {
                label: `detached@${detached}`,
                tooltip: `Detached HEAD ${head}`,
            };
        }

        const ref = head.slice(4).trim();
        const branch = ref.split('/').pop() || ref;
        const refPath = path.join(gitDir, ...ref.split('/'));
        const hash = fs.existsSync(refPath)
            ? fs.readFileSync(refPath, 'utf8').trim().slice(0, 8)
            : 'unknown';

        return {
            label: `${branch}@${hash}`,
            tooltip: `Chthonic lineage\n${ref}\n${hash}`,
        };
    } catch (error) {
        return {
            label: 'lineage-error',
            tooltip: `Chthonic lineage read failed: ${String(error)}`,
        };
    }
}
