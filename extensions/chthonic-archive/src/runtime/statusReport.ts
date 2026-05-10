// @SID: EXT_RUNTIME_STATUS_REPORT_V1
import * as fs from 'node:fs';
import * as path from 'node:path';
import type { LedgerMode } from '../polyglot/ledgerBroker';
import { formatRuntimeLaneState, type RuntimeLaneState } from './laneState';

export interface ReactorReadiness {
    ready: boolean;
    reason: string;
    daemonPath?: string;
}

export interface BridgeLaneStatus {
    installed: boolean;
    active: boolean;
    commandAvailable: boolean;
}

export interface RuntimeStatusInput {
    workspaceRoot: string | null;
    entropyEnabled: boolean;
    entropyPolyglotEnabled: boolean;
    entropyLedgerMode: LedgerMode;
    reactorReadiness: ReactorReadiness;
    slabSelfHealingEnabled: boolean;
    allowNativeSidecars: boolean;
    extensionPath: string;
    webCockpitUrl: string;
    webCockpitReachable: boolean;
    commandCatalog: Set<string>;
    bridgeMandala: BridgeLaneStatus;
    bridgeStatusbar: BridgeLaneStatus;
}

export function collectRuntimeLaneStates(input: RuntimeStatusInput): RuntimeLaneState[] {
    const entropyWorkerPath = path.join(input.extensionPath, 'dist', 'entropy-worker.js');
    const entropyWorkerReady = fs.existsSync(entropyWorkerPath);
    const polyglotActive = input.entropyEnabled && input.entropyPolyglotEnabled;
    const lanes: RuntimeLaneState[] = [];

    lanes.push({ name: 'workspace', state: input.workspaceRoot ? 'READY' : 'UNAVAILABLE' });
    lanes.push({ name: 'workspace-health', state: input.entropyEnabled ? 'LIVE' : 'DISABLED' });
    lanes.push({
        name: 'native-sidecars',
        state: input.allowNativeSidecars ? 'LIVE' : 'DISABLED',
        reason: input.allowNativeSidecars ? undefined : 'chthonic.security.allowNativeSidecars=false',
    });
    lanes.push({
        name: 'polyglot-sidecars',
        state: input.entropyEnabled ? (input.entropyPolyglotEnabled ? 'LIVE' : 'DISABLED') : 'PARKED',
        reason: input.entropyEnabled ? undefined : 'workspace-health disabled',
    });
    lanes.push({
        name: 'ledger-mode',
        state: polyglotActive ? 'LIVE' : 'PARKED',
        reason: polyglotActive
            ? input.entropyLedgerMode
            : `${input.entropyLedgerMode}, polyglot disabled`,
    });
    lanes.push({
        name: 'entropy-settlement',
        state: polyglotActive ? 'READY' : (input.entropyEnabled ? 'DISABLED' : 'PARKED'),
        reason: polyglotActive ? 'awaiting entropy leaves' : 'polyglot sidecars disabled',
    });
    lanes.push({
        name: 'solana-ledger',
        state: polyglotActive ? 'READY' : (input.entropyEnabled ? 'DISABLED' : 'PARKED'),
        reason: polyglotActive
            ? (input.entropyLedgerMode === 'validator' ? 'validator backend configured' : 'bankrun simulation backend')
            : 'polyglot sidecars disabled',
    });
    lanes.push({ name: 'self-healing', state: input.slabSelfHealingEnabled ? 'LIVE' : 'DISABLED' });
    lanes.push({
        name: 'reactor',
        state: input.reactorReadiness.ready ? 'READY' : 'PARKED',
        reason: input.reactorReadiness.ready ? undefined : input.reactorReadiness.reason,
    });
    lanes.push({ name: 'entropy-worker', state: entropyWorkerReady ? 'READY' : 'MISSING' });
    lanes.push({
        name: 'abyssal-view',
        state: input.entropyEnabled ? (entropyWorkerReady ? 'READY' : 'PARKED') : 'PARKED',
        reason: input.entropyEnabled
            ? (entropyWorkerReady ? undefined : `worker missing at ${entropyWorkerPath}`)
            : 'workspace-health disabled',
    });
    lanes.push({
        name: 'loom-view',
        state: input.workspaceRoot ? 'READY' : 'PARKED',
        reason: input.workspaceRoot ? undefined : 'workspace unavailable',
    });
    lanes.push({
        name: 'markdown-paste',
        state: 'READY',
        reason: 'text/html -> GFM Markdown, sidecar-free',
    });
    lanes.push({
        name: 'web-cockpit',
        state: input.webCockpitReachable ? 'LIVE' : 'UNAVAILABLE',
        reason: input.webCockpitReachable ? undefined : 'run "Chthonic: Start Next Cockpit"',
    });
    return lanes;
}

export function collectRuntimeStatusRows(input: RuntimeStatusInput): string[] {
    const rows: string[] = collectRuntimeLaneStates(input).map(formatRuntimeLaneState);
    rows.push(`web-cockpit-url=${input.webCockpitUrl}`);
    rows.push(`bridge-mandala=${formatBridgeStatus(input.bridgeMandala)}`);
    rows.push(`bridge-statusbar=${formatBridgeStatus(input.bridgeStatusbar)}`);
    if (input.reactorReadiness.daemonPath) {
        rows.push(`reactor-daemon=${input.reactorReadiness.daemonPath}`);
    }
    return rows;
}

function formatBridgeStatus(status: BridgeLaneStatus): string {
    if (!status.installed) {
        return 'UNAVAILABLE (extension not installed)';
    }
    if (status.commandAvailable) {
        return 'READY';
    }
    if (status.active) {
        return 'DEGRADED (active but command missing)';
    }
    return 'INSTALLED (awaiting activation)';
}
