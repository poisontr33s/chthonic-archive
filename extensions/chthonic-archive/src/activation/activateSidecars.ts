// @SID: EXT_ACTIVATION_SIDECARS_V1
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { AbyssalPaneProvider } from '../entropy/archiveAbyssalView';
import { EntropyDecorationProvider } from '../entropy/entropyDecorations';
import { EntropyWorkerClient } from '../entropy/entropyWorkerClient';
import type { LedgerMode } from '../polyglot/ledgerBroker';
import { PolyglotEntropyOrchestrator } from '../polyglot/polyglotEntropyOrchestrator';
import { ActivityBarMorph } from '../monolith/activityBarMorph';
import { SelfHealingLoop } from '../monolith/selfHealingLoop';
import { LoomViewProvider } from '../monolith/loomView';
import { RestoreOrderLayout } from '../monolith/restoreOrderLayout';
import { AnnoClient } from '../reactor/annoClient';
import { CockpitLayout } from '../reactor/cockpitLayout';
import { SynapseBridge } from '../reactor/synapseBridge';
import type { EntropyState, FiredancerSurgeState } from '../reactor/types';
import type { LaneRegistry, RuntimeLaneState } from '../runtime/laneState';
import type { ReactorReadiness } from '../runtime/statusReport';

export interface SidecarSupervisor extends vscode.Disposable {
    start(): void | Promise<void>;
    stop(): void;
    state(): RuntimeLaneState;
}

export interface ActivatedSidecars {
    readonly allowNativeSidecars: boolean;
    readonly entropyEnabled: boolean;
    readonly entropyPolyglotEnabled: boolean;
    readonly entropyLedgerMode: LedgerMode;
    readonly reactorReadiness: ReactorReadiness;
    readonly slabSelfHealingEnabled: boolean;
    readonly entropyClient: EntropyWorkerClient;
    readonly entropyDecorations: EntropyDecorationProvider;
    readonly abyssalProvider: AbyssalPaneProvider;
    readonly polyglotOrchestrator: PolyglotEntropyOrchestrator;
    readonly selfHealingLoop: SelfHealingLoop;
    readonly annoClient: AnnoClient;
    readonly cockpitLayout: CockpitLayout;
    readonly synapseBridge: SynapseBridge;
}

export interface ActivateSidecarsDeps {
    readonly workspaceRoot: string | null;
    readonly outputChannel: vscode.OutputChannel;
    readonly chthonicConfig: vscode.WorkspaceConfiguration;
    readonly laneRegistry: LaneRegistry;
    readonly activityBarMorph: ActivityBarMorph;
    readonly restoreOrderLayout: RestoreOrderLayout;
    readonly loomProvider: LoomViewProvider;
}

export function activateSidecars(context: vscode.ExtensionContext, deps: ActivateSidecarsDeps): ActivatedSidecars {
    const entropyConfig = deps.chthonicConfig;
    const allowNativeSidecars = entropyConfig.get<boolean>('security.allowNativeSidecars', false);
    const entropyEnabled = entropyConfig.get<boolean>('entropy.enabled', false);
    const entropyMaxFiles = entropyConfig.get<number>('entropy.maxFiles', 3000);
    const entropyScanIntervalMs = entropyConfig.get<number>('entropy.scanIntervalMs', 60000);
    const entropyDecorationDebounceMs = entropyConfig.get<number>('entropy.decorationDebounceMs', 120);
    const entropyDecorationBatch = entropyConfig.get<number>('entropy.decorationBatchSize', 240);
    const entropyPolyglotRequested = entropyConfig.get<boolean>('entropy.polyglotEnabled', false);
    const entropyPolyglotEnabled = entropyPolyglotRequested && allowNativeSidecars;
    const entropyLedgerMode = entropyConfig.get<LedgerMode>('entropy.ledgerMode', 'bankrun');

    const entropyClient = new EntropyWorkerClient(context, deps.outputChannel);
    let entropyDecorations: EntropyDecorationProvider | undefined;
    const polyglotOrchestrator = new PolyglotEntropyOrchestrator(
        deps.outputChannel,
        entropyClient,
        {
            enabled: entropyPolyglotEnabled,
            pythonScanIntervalMs: entropyConfig.get<number>('entropy.pythonScanIntervalMs', 30000),
            settleDebounceMs: entropyConfig.get<number>('entropy.ledgerSettleDebounceMs', 1400),
            ledgerMode: entropyLedgerMode,
            solanaRpcUrl: entropyConfig.get<string>('entropy.solanaRpcUrl', 'http://127.0.0.1:8899'),
            solanaAutostartValidator: entropyConfig.get<boolean>('entropy.solanaAutostartValidator', false),
            solanaLedgerHostBinaryPath: asOptionalPath(entropyConfig.get<string>('entropy.solanaLedgerHostBinaryPath', '')),
            solanaWalletPath: asOptionalPath(entropyConfig.get<string>('entropy.solanaWalletPath', '')),
            solanaIdlPath: asOptionalPath(entropyConfig.get<string>('entropy.solanaIdlPath', '')),
            laneRegistry: deps.laneRegistry,
        },
        (uris) => entropyDecorations?.enqueueExternalUpdates(uris),
    );

    entropyDecorations = new EntropyDecorationProvider(
        entropyClient,
        entropyDecorationDebounceMs,
        entropyDecorationBatch,
        (uri) => polyglotOrchestrator.getTooltipFragments(uri),
    );
    const abyssalProvider = new AbyssalPaneProvider(context.extensionUri, entropyClient);
    abyssalProvider.setRootPath(deps.workspaceRoot);
    deps.loomProvider.updateWorkspaceHealth(entropyClient.getSnapshot());

    const reactorRequested = entropyConfig.get<boolean>('reactor.enabled', false);
    const reactorEnabled = reactorRequested && allowNativeSidecars;
    const reactorHeadlessVulkan = entropyConfig.get<boolean>('reactor.headlessVulkan', true);
    const reactorCockpitAutoLayout = entropyConfig.get<boolean>('reactor.cockpitAutoLayout', false);
    const reactorTransport = entropyConfig.get<string>('reactor.transport', 'auto');
    const reactorDaemonBinaryRaw = asOptionalPath(entropyConfig.get<string>('reactor.daemonBinaryPath', ''));
    // Relative values resolve against the workspace root so the setting can stay machine-portable.
    const reactorDaemonBinaryPath = reactorDaemonBinaryRaw && !path.isAbsolute(reactorDaemonBinaryRaw)
        ? path.resolve(deps.workspaceRoot, reactorDaemonBinaryRaw)
        : reactorDaemonBinaryRaw;
    const reactorReadiness = assessReactorReadiness(
        deps.workspaceRoot,
        reactorEnabled,
        reactorDaemonBinaryPath,
        allowNativeSidecars,
        reactorRequested,
    );
    const slabSelfHealingRequested = entropyConfig.get<boolean>('slab.selfHealingEnabled', false);
    const slabSelfHealingEnabled = slabSelfHealingRequested && allowNativeSidecars;
    const slabSelfHealingIntervalMs = entropyConfig.get<number>('slab.selfHealingIntervalMs', 21600000);
    const slabEolApiBase = entropyConfig.get<string>('slab.eolApiBase', 'https://endoflife.date/api');
    const daemonEolApiBase = normalizeEolApiBase(slabEolApiBase);
    const daemonEntropyIntervalMs = Math.max(60_000, Math.floor(slabSelfHealingIntervalMs / 2));

    const selfHealingLoop = new SelfHealingLoop(
        deps.outputChannel,
        context.environmentVariableCollection,
        deps.workspaceRoot,
    );
    const annoClient = new AnnoClient(
        deps.outputChannel,
        reactorHeadlessVulkan,
        reactorDaemonBinaryPath,
        daemonEolApiBase,
        daemonEntropyIntervalMs,
        reactorTransport,
    );
    const cockpitLayout = new CockpitLayout(deps.outputChannel, context.environmentVariableCollection);
    const synapseBridge = new SynapseBridge(deps.outputChannel, context.extensionPath, reactorTransport, {
        workspaceRoot: deps.workspaceRoot,
        daemonPath: reactorReadiness.daemonPath,
        headlessVulkan: reactorHeadlessVulkan,
        laneRegistry: deps.laneRegistry,
    });

    context.subscriptions.push(
        entropyClient,
        entropyDecorations,
        abyssalProvider,
        polyglotOrchestrator,
        selfHealingLoop,
        annoClient,
        cockpitLayout,
        synapseBridge,
        entropyClient.onDidUpdateSnapshot((snapshot) => {
            deps.loomProvider.updateWorkspaceHealth(snapshot);
        }),
        vscode.workspace.onDidSaveTextDocument((document) => {
            entropyClient.refreshFile(document.uri);
            polyglotOrchestrator.onDidSaveDocument(document);
        }),
    );

    const supervisors: SidecarSupervisor[] = [
        new LaneOnlySupervisor({
            name: 'native-sidecars',
            state: allowNativeSidecars ? 'LIVE' : 'DISABLED',
            reason: allowNativeSidecars ? undefined : 'chthonic.security.allowNativeSidecars=false',
        }),
        new LaneOnlySupervisor({
            name: 'synapseShm',
            state: allowNativeSidecars && reactorReadiness.ready ? 'READY' : 'PARKED',
            reason: allowNativeSidecars ? reactorReadiness.reason : 'chthonic.security.allowNativeSidecars=false',
        }),
        new LaneOnlySupervisor({
            name: 'chthonicDaemon',
            state: reactorReadiness.ready ? 'READY' : 'PARKED',
            reason: reactorReadiness.ready ? reactorReadiness.daemonPath : reactorReadiness.reason,
        }),
        new LaneOnlySupervisor({
            name: 'entropyLedgerHost',
            state: entropyPolyglotEnabled ? 'LIVE' : 'DISABLED',
            reason: entropyPolyglotEnabled ? entropyLedgerMode : 'polyglot sidecars disabled',
        }),
        new LaneOnlySupervisor({
            name: 'polyglot-sidecars',
            state: entropyEnabled ? (entropyPolyglotEnabled ? 'LIVE' : 'DISABLED') : 'PARKED',
            reason: entropyEnabled
                ? (entropyPolyglotEnabled ? 'polyglot entropy lane armed' : 'polyglot sidecars disabled')
                : 'workspace-health disabled',
        }),
        new LaneOnlySupervisor({
            name: 'entropy-settlement',
            state: entropyPolyglotEnabled ? 'READY' : 'DISABLED',
            reason: entropyPolyglotEnabled ? 'awaiting entropy leaves' : 'polyglot sidecars disabled',
        }),
        new LaneOnlySupervisor({
            name: 'solana-ledger',
            state: entropyPolyglotEnabled ? 'READY' : 'DISABLED',
            reason: entropyPolyglotEnabled
                ? (entropyLedgerMode === 'validator' ? 'validator backend configured' : 'bankrun simulation backend')
                : 'polyglot sidecars disabled',
        }),
        new LaneOnlySupervisor({ name: 'entropyWorker', state: 'READY' }),
    ];
    context.subscriptions.push(...supervisors);
    deps.laneRegistry.setMany(supervisors.map((supervisor) => supervisor.state()));

    if (!reactorReadiness.ready) {
        deps.outputChannel.appendLine(`[reactor] lane parked: ${reactorReadiness.reason}`);
    }

    wireReactorEvents(context, {
        ...deps,
        allowNativeSidecars,
        entropyEnabled,
        entropyMaxFiles,
        entropyScanIntervalMs,
        entropyPolyglotEnabled,
        reactorEnabled,
        reactorCockpitAutoLayout,
        reactorReadiness,
        slabSelfHealingEnabled,
        slabSelfHealingIntervalMs,
        slabEolApiBase,
        entropyClient,
        polyglotOrchestrator,
        selfHealingLoop,
        annoClient,
        cockpitLayout,
        synapseBridge,
    });

    return {
        allowNativeSidecars,
        entropyEnabled,
        entropyPolyglotEnabled,
        entropyLedgerMode,
        reactorReadiness,
        slabSelfHealingEnabled,
        entropyClient,
        entropyDecorations,
        abyssalProvider,
        polyglotOrchestrator,
        selfHealingLoop,
        annoClient,
        cockpitLayout,
        synapseBridge,
    };
}

interface WireDeps extends ActivateSidecarsDeps {
    readonly allowNativeSidecars: boolean;
    readonly entropyEnabled: boolean;
    readonly entropyMaxFiles: number;
    readonly entropyScanIntervalMs: number;
    readonly entropyPolyglotEnabled: boolean;
    readonly reactorEnabled: boolean;
    readonly reactorCockpitAutoLayout: boolean;
    readonly reactorReadiness: ReactorReadiness;
    readonly slabSelfHealingEnabled: boolean;
    readonly slabSelfHealingIntervalMs: number;
    readonly slabEolApiBase: string;
    readonly entropyClient: EntropyWorkerClient;
    readonly polyglotOrchestrator: PolyglotEntropyOrchestrator;
    readonly selfHealingLoop: SelfHealingLoop;
    readonly annoClient: AnnoClient;
    readonly cockpitLayout: CockpitLayout;
    readonly synapseBridge: SynapseBridge;
}

function wireReactorEvents(context: vscode.ExtensionContext, deps: WireDeps): void {
    let lastEntropyPromptFingerprint: string | null = null;
    let lastValidatorLayoutFingerprint: string | null = null;
    let lastSurgeLayoutFingerprint: string | null = null;

    const moveLoomToPanel = (reason: string, tps?: number): void => {
        const lane = tps ? `${reason} (${tps.toLocaleString()} tps)` : reason;
        deps.outputChannel.appendLine(`[loom-reflex] panel lane ${lane}`);
        void deps.restoreOrderLayout.activate();
    };

    const focusLoomPrimary = (reason: string): void => {
        deps.outputChannel.appendLine(`[loom-reflex] primary lane ${reason}`);
        void vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        void vscode.commands.executeCommand('chthonic.loomView.focus');
    };

    const handleEntropyState = (state: EntropyState): void => {
        void deps.activityBarMorph.updateEntropy(state);
        deps.outputChannel.appendLine(
            `[workspace-health] score ${Math.round(state.decay_score * 100)}% (${state.status}) from ${state.source_mise ?? 'no-mise'}`,
        );

        if (state.validator_active) {
            const validatorFingerprint = `${state.validator_process ?? 'validator'}:${state.validator_source_mise}`;
            if (validatorFingerprint !== lastValidatorLayoutFingerprint) {
                lastValidatorLayoutFingerprint = validatorFingerprint;
                focusLoomPrimary(`validator-online:${validatorFingerprint}`);
            }
        } else {
            lastValidatorLayoutFingerprint = null;
        }

        if (state.firedancer_surge && state.validator_active) {
            const surgeFingerprint = `${state.checked_at_epoch_ms}:${state.simulated_tps}`;
            if (surgeFingerprint !== lastSurgeLayoutFingerprint) {
                lastSurgeLayoutFingerprint = surgeFingerprint;
                moveLoomToPanel('workspace-health-surge', state.simulated_tps);
            }
        } else {
            lastSurgeLayoutFingerprint = null;
        }

        if (!state.critical || !state.auto_update_enabled) {
            lastEntropyPromptFingerprint = null;
            return;
        }

        const fingerprint = `${state.status}:${state.auto_update}:${[...state.critical_tools].sort().join(',')}`;
        if (fingerprint === lastEntropyPromptFingerprint) {
            return;
        }
        lastEntropyPromptFingerprint = fingerprint;

        const criticalTools = state.critical_tools.length > 0
            ? state.critical_tools.join(', ')
            : 'runtime toolchain';
        void vscode.window.showWarningMessage(
            `Workspace health is critical (${Math.round(state.decay_score * 100)}%). ${criticalTools} needs healing.`,
            'Run mise upgrade',
            'Later',
        ).then((choice) => {
            if (choice === 'Run mise upgrade') {
                void deps.selfHealingLoop.runNow('manual');
            }
        });
    };

    if (deps.workspaceRoot && deps.entropyEnabled) {
        deps.entropyClient.start(deps.workspaceRoot, deps.entropyMaxFiles, deps.entropyScanIntervalMs);
        if (deps.entropyPolyglotEnabled) {
            void deps.polyglotOrchestrator.start(deps.workspaceRoot);
        }
    }

    context.subscriptions.push(
        deps.annoClient.onDidReceiveEnv((envReport) => {
            deps.cockpitLayout.applyTerminalEnv(envReport);
        }),
        deps.annoClient.onDidReceiveSynapse((descriptor) => {
            deps.synapseBridge.updateDescriptor(descriptor);
        }),
        deps.annoClient.onDidReceiveEntropyState((state) => {
            handleEntropyState(state);
        }),
        deps.annoClient.onDidReceiveFiredancerSurge((state: FiredancerSurgeState) => {
            if (state.surge) {
                const surgeFingerprint = `${state.slot}:${state.simulated_tps}`;
                if (surgeFingerprint !== lastSurgeLayoutFingerprint) {
                    lastSurgeLayoutFingerprint = surgeFingerprint;
                    moveLoomToPanel('daemon-surge', state.simulated_tps);
                }
            }
        }),
    );

    if (deps.reactorReadiness.ready && deps.workspaceRoot && deps.reactorEnabled) {
        deps.annoClient.start(deps.workspaceRoot);
        void deps.annoClient.requestEntropyState()
            .then((state) => {
                handleEntropyState(state);
            })
            .catch((error) => {
                deps.outputChannel.appendLine(`[workspace-health] initial snapshot unavailable: ${error}`);
            });
        if (deps.reactorCockpitAutoLayout) {
            void deps.cockpitLayout.activate();
        }

        const gitHeadPath = path.join(deps.workspaceRoot, '.git', 'HEAD');
        if (fs.existsSync(gitHeadPath)) {
            let liveLoopTimer: ReturnType<typeof setTimeout> | null = null;
            const gitWatcher = fs.watch(
                path.join(deps.workspaceRoot, '.git'),
                { persistent: false },
                (_event, filename) => {
                    if (filename === 'HEAD' || filename?.startsWith('refs')) {
                        if (liveLoopTimer) clearTimeout(liveLoopTimer);
                        liveLoopTimer = setTimeout(() => {
                            deps.outputChannel.appendLine('[reactor] git change detected, recomputing sediment');
                            deps.annoClient.requestSediment(10, 500).catch((err) => {
                                deps.outputChannel.appendLine(`[reactor] live-loop sediment failed: ${err}`);
                            });
                        }, 800);
                    }
                },
            );
            context.subscriptions.push({ dispose: () => gitWatcher.close() });
        }
    }

    if (deps.workspaceRoot && deps.slabSelfHealingEnabled) {
        deps.selfHealingLoop.start({
            intervalMs: deps.slabSelfHealingIntervalMs,
            eolApiBase: deps.slabEolApiBase,
        });
        void deps.selfHealingLoop.runNow('interval');
    }
}

class LaneOnlySupervisor implements SidecarSupervisor {
    constructor(private readonly lane: RuntimeLaneState) {}
    start(): void {}
    stop(): void {}
    state(): RuntimeLaneState {
        return this.lane;
    }
    dispose(): void {
        this.stop();
    }
}

function asOptionalPath(value: string): string | undefined {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : undefined;
}

function normalizeEolApiBase(value: string): string {
    const trimmed = value.trim().replace(/\/+$/, '');
    if (trimmed.endsWith('/api')) {
        return `${trimmed}/v1`;
    }
    return trimmed.length > 0 ? trimmed : 'https://endoflife.date/api/v1';
}

function assessReactorReadiness(
    workspaceRoot: string | null,
    enabled: boolean,
    daemonBinaryOverride?: string,
    allowNativeSidecars = false,
    requested = false,
): ReactorReadiness {
    if (!allowNativeSidecars && requested) {
        return {
            ready: false,
            reason: 'disabled by chthonic.security.allowNativeSidecars=false',
        };
    }
    if (!enabled) {
        return {
            ready: false,
            reason: 'disabled by chthonic.reactor.enabled=false',
        };
    }
    if (!workspaceRoot) {
        return {
            ready: false,
            reason: 'workspace root is unavailable',
        };
    }

    const daemonPath = resolveDaemonBinaryPath(workspaceRoot, daemonBinaryOverride);
    if (!fs.existsSync(daemonPath)) {
        return {
            ready: false,
            reason: `daemon binary missing (${daemonPath})`,
            daemonPath,
        };
    }

    return {
        ready: true,
        reason: 'ready',
        daemonPath,
    };
}

function resolveDaemonBinaryPath(workspaceRoot: string, daemonBinaryOverride?: string): string {
    if (daemonBinaryOverride) {
        return path.isAbsolute(daemonBinaryOverride)
            ? daemonBinaryOverride
            : path.join(workspaceRoot, daemonBinaryOverride);
    }
    const binary = process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon';
    return path.join(workspaceRoot, 'native', 'target', 'release', binary);
}
