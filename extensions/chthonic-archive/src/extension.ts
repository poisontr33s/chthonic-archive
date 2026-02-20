import * as vscode from 'vscode';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
import { ChthonicChatProvider } from './sdk/webview';
import { EntropyWorkerClient } from './entropy/entropyWorkerClient';
import { EntropyDecorationProvider } from './entropy/entropyDecorations';
import { AbyssalPaneProvider } from './entropy/archiveAbyssalView';
import { PolyglotEntropyOrchestrator } from './polyglot/polyglotEntropyOrchestrator';
import type { LedgerMode } from './polyglot/ledgerBroker';
import { AnnoClient } from './reactor/annoClient';
import { CockpitLayout } from './reactor/cockpitLayout';
import { SynapseBridge } from './reactor/synapseBridge';
import { ActivityBarMorph } from './monolith/activityBarMorph';
import { DeepFocusLayout } from './monolith/deepFocusLayout';
import { RestoreOrderLayout } from './monolith/restoreOrderLayout';
import { LoomViewProvider } from './monolith/loomView';
import { SelfHealingLoop } from './monolith/selfHealingLoop';
import { computeRustificationReport } from './monolith/rustificationScore';
import type { EntropyState, FiredancerSurgeState } from './reactor/types';

export function activate(context: vscode.ExtensionContext) {
    console.log('☥ Chthonic Archive extension activated');

    // --- SDK Chat Panel ---
    const outputChannel = vscode.window.createOutputChannel('Chthonic SDK');
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
    const chthonicConfig = vscode.workspace.getConfiguration('chthonic');
    const harnessPath = path.join(
        workspaceRoot || '',
        'meta-ide', 'copilot-sdk', 'harness.ts',
    );
    const chatProvider = new ChthonicChatProvider(
        context.extensionUri,
        harnessPath,
        (msg: string) => outputChannel.appendLine(`[${new Date().toISOString()}] ${msg}`),
    );
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(ChthonicChatProvider.viewType, chatProvider),
    );

    const activityBarMorph = new ActivityBarMorph(context.extensionUri, outputChannel);
    const deepFocusLayout = new DeepFocusLayout(outputChannel);
    const restoreOrderLayout = new RestoreOrderLayout(outputChannel);
    const loomProvider = new LoomViewProvider();
    const selfHealingLoop = new SelfHealingLoop(
        outputChannel,
        context.environmentVariableCollection,
        workspaceRoot,
    );

    context.subscriptions.push(
        activityBarMorph,
        loomProvider,
        selfHealingLoop,
        vscode.window.registerWebviewViewProvider(LoomViewProvider.viewType, loomProvider),
    );

    // --- Entropy Engine (worker + decorations + webview) ---
    const entropyConfig = chthonicConfig;
    const entropyEnabled = entropyConfig.get<boolean>('entropy.enabled', true);
    const entropyMaxFiles = entropyConfig.get<number>('entropy.maxFiles', 10000);
    const entropyScanIntervalMs = entropyConfig.get<number>('entropy.scanIntervalMs', 20000);
    const entropyDecorationDebounceMs = entropyConfig.get<number>('entropy.decorationDebounceMs', 120);
    const entropyDecorationBatch = entropyConfig.get<number>('entropy.decorationBatchSize', 240);
    const entropyPolyglotEnabled = entropyConfig.get<boolean>('entropy.polyglotEnabled', true);
    const entropyPythonScanIntervalMs = entropyConfig.get<number>('entropy.pythonScanIntervalMs', 30000);
    const entropyLedgerSettleDebounceMs = entropyConfig.get<number>('entropy.ledgerSettleDebounceMs', 1400);
    const entropyLedgerMode = entropyConfig.get<LedgerMode>('entropy.ledgerMode', 'validator');
    const entropySolanaRpcUrl = entropyConfig.get<string>('entropy.solanaRpcUrl', 'http://127.0.0.1:8899');
    const entropySolanaAutostartValidator = entropyConfig.get<boolean>('entropy.solanaAutostartValidator', false);
    const entropySolanaLedgerHostBinaryPath = asOptionalPath(entropyConfig.get<string>('entropy.solanaLedgerHostBinaryPath', ''));
    const entropySolanaWalletPath = asOptionalPath(entropyConfig.get<string>('entropy.solanaWalletPath', ''));
    const entropySolanaIdlPath = asOptionalPath(entropyConfig.get<string>('entropy.solanaIdlPath', ''));

    const entropyClient = new EntropyWorkerClient(context, outputChannel);
    let entropyDecorations: EntropyDecorationProvider | undefined;
    const polyglotOrchestrator = new PolyglotEntropyOrchestrator(
        outputChannel,
        entropyClient,
        {
            enabled: entropyPolyglotEnabled,
            pythonScanIntervalMs: entropyPythonScanIntervalMs,
            settleDebounceMs: entropyLedgerSettleDebounceMs,
            ledgerMode: entropyLedgerMode,
            solanaRpcUrl: entropySolanaRpcUrl,
            solanaAutostartValidator: entropySolanaAutostartValidator,
            solanaLedgerHostBinaryPath: entropySolanaLedgerHostBinaryPath,
            solanaWalletPath: entropySolanaWalletPath,
            solanaIdlPath: entropySolanaIdlPath,
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
    abyssalProvider.setRootPath(workspaceRoot);

    context.subscriptions.push(
        entropyClient,
        entropyDecorations,
        abyssalProvider,
        polyglotOrchestrator,
        vscode.window.registerFileDecorationProvider(entropyDecorations),
        vscode.window.registerWebviewViewProvider(AbyssalPaneProvider.viewType, abyssalProvider),
    );

    const refreshRustification = async (reason: string): Promise<void> => {
        if (!workspaceRoot) {
            return;
        }
        const report = await computeRustificationReport(workspaceRoot);
        loomProvider.update(report);
        await activityBarMorph.update(report);
        outputChannel.appendLine(`[monolith] rustification ${report.score}% (${report.tier}) via ${reason}`);
    };

    if (workspaceRoot) {
        void refreshRustification('startup');

        const markerWatcher = vscode.workspace.createFileSystemWatcher(
            new vscode.RelativePattern(
                workspaceRoot,
                '{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}',
            ),
        );
        context.subscriptions.push(
            markerWatcher,
            markerWatcher.onDidCreate(() => { void refreshRustification('marker-create'); }),
            markerWatcher.onDidChange(() => { void refreshRustification('marker-change'); }),
            markerWatcher.onDidDelete(() => { void refreshRustification('marker-delete'); }),
        );
    }

    if (workspaceRoot && entropyEnabled) {
        entropyClient.start(workspaceRoot, entropyMaxFiles, entropyScanIntervalMs);
        void polyglotOrchestrator.start(workspaceRoot);
    }

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            entropyClient.refreshFile(document.uri);
            polyglotOrchestrator.onDidSaveDocument(document);
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.entropyRefresh', () => {
            entropyClient.rescanNow();
            entropyClient.requestGraph(260);
            polyglotOrchestrator.requestManualScan();
            vscode.window.showInformationMessage('Chthonic entropy scan requested');
        }),
    );

    // --- ANNO / Entropy Reactor ---
    const reactorEnabled = entropyConfig.get<boolean>('reactor.enabled', true);
    const reactorHeadlessVulkan = entropyConfig.get<boolean>('reactor.headlessVulkan', true);
    const reactorCockpitAutoLayout = entropyConfig.get<boolean>('reactor.cockpitAutoLayout', false);
    const reactorTransport = entropyConfig.get<string>('reactor.transport', 'auto');
    const reactorDaemonBinaryPath = asOptionalPath(entropyConfig.get<string>('reactor.daemonBinaryPath', ''));
    const slabSelfHealingEnabled = entropyConfig.get<boolean>('slab.selfHealingEnabled', true);
    const slabSelfHealingIntervalMs = entropyConfig.get<number>('slab.selfHealingIntervalMs', 21600000);
    const slabEolApiBase = entropyConfig.get<string>('slab.eolApiBase', 'https://endoflife.date/api');
    const daemonEolApiBase = normalizeEolApiBase(slabEolApiBase);
    const daemonEntropyIntervalMs = Math.max(60_000, Math.floor(slabSelfHealingIntervalMs / 2));

    const annoClient = new AnnoClient(
        outputChannel,
        reactorHeadlessVulkan,
        reactorDaemonBinaryPath,
        daemonEolApiBase,
        daemonEntropyIntervalMs,
    );
    const cockpitLayout = new CockpitLayout(outputChannel, context.environmentVariableCollection);
    const synapseBridge = new SynapseBridge(outputChannel, context.extensionPath, reactorTransport);
    let lastEntropyPromptFingerprint: string | null = null;
    let lastValidatorLayoutFingerprint: string | null = null;
    let lastSurgeLayoutFingerprint: string | null = null;

    const moveLoomToPanel = (reason: string, tps?: number): void => {
        const lane = tps ? `${reason} (${tps.toLocaleString()} tps)` : reason;
        outputChannel.appendLine(`[loom-reflex] panel lane ${lane}`);
        void restoreOrderLayout.activate();
    };

    const focusLoomPrimary = (reason: string): void => {
        outputChannel.appendLine(`[loom-reflex] primary lane ${reason}`);
        void vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        void vscode.commands.executeCommand('chthonic.loomView.focus');
    };

    context.subscriptions.push(annoClient, cockpitLayout, synapseBridge);

    const handleEntropyState = (state: EntropyState): void => {
        void activityBarMorph.updateEntropy(state);
        outputChannel.appendLine(
            `[lens] decay ${Math.round(state.decay_score * 100)}% (${state.status}) from ${state.source_mise ?? 'no-mise'}`,
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
                moveLoomToPanel('entropy-surge', state.simulated_tps);
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
            `Chthonic decay is critical (${Math.round(state.decay_score * 100)}%). ${criticalTools} needs healing.`,
            'Run mise upgrade',
            'Later',
        ).then((choice) => {
            if (choice === 'Run mise upgrade') {
                void selfHealingLoop.runNow('manual');
            }
        });
    };

    context.subscriptions.push(
        annoClient.onDidReceiveEnv((envReport) => {
            cockpitLayout.applyTerminalEnv(envReport);
        }),
        annoClient.onDidReceiveSediment((sediment) => {
            abyssalProvider.postSedimentData(sediment);
        }),
        annoClient.onDidReceiveSedimentChunk((chunk) => {
            abyssalProvider.postSedimentChunk(chunk);
        }),
        annoClient.onDidReceiveSynapse((descriptor) => {
            synapseBridge.updateDescriptor(descriptor);
        }),
        annoClient.onDidReceiveEntropyState((state) => {
            handleEntropyState(state);
        }),
        annoClient.onDidReceiveFiredancerSurge((state: FiredancerSurgeState) => {
            if (state.surge) {
                const surgeFingerprint = `${state.slot}:${state.simulated_tps}`;
                if (surgeFingerprint !== lastSurgeLayoutFingerprint) {
                    lastSurgeLayoutFingerprint = surgeFingerprint;
                    moveLoomToPanel('daemon-surge', state.simulated_tps);
                }
            }
        }),
    );

    // Allow the Abyssal Pane webview to trigger sediment computation
    abyssalProvider.onRequestSediment(() => {
        void requestSedimentForWebview(annoClient, abyssalProvider, synapseBridge, outputChannel);
    });

    if (workspaceRoot && reactorEnabled) {
        annoClient.start(workspaceRoot);
        void annoClient.requestEntropyState()
            .then((state) => {
                handleEntropyState(state);
            })
            .catch((error) => {
                outputChannel.appendLine(`[lens] initial entropy snapshot unavailable: ${error}`);
            });
        if (reactorCockpitAutoLayout) {
            void cockpitLayout.activate();
        }

        // Live loop: watch .git/HEAD for branch switches and new commits
        const gitHeadPath = path.join(workspaceRoot, '.git', 'HEAD');
        if (fs.existsSync(gitHeadPath)) {
            let liveLoopTimer: ReturnType<typeof setTimeout> | null = null;
            const gitWatcher = fs.watch(
                path.join(workspaceRoot, '.git'),
                { persistent: false },
                (_event, filename) => {
                    // HEAD changes on checkout; refs change on commit
                    if (filename === 'HEAD' || filename?.startsWith('refs')) {
                        // Debounce: wait 800ms for git to settle
                        if (liveLoopTimer) clearTimeout(liveLoopTimer);
                        liveLoopTimer = setTimeout(() => {
                            outputChannel.appendLine('[reactor] git change detected, recomputing sediment');
                            annoClient.requestSediment(10, 500).catch((err) => {
                                outputChannel.appendLine(`[reactor] live-loop sediment failed: ${err}`);
                            });
                        }, 800);
                    }
                },
            );
            context.subscriptions.push({ dispose: () => gitWatcher.close() });
        }
    }

    if (workspaceRoot && slabSelfHealingEnabled) {
        selfHealingLoop.start({
            intervalMs: slabSelfHealingIntervalMs,
            eolApiBase: slabEolApiBase,
        });
        void selfHealingLoop.runNow('interval');
    }

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.activateCockpit', () => {
            void cockpitLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.deepFocus', () => {
            void deepFocusLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.restoreOrder', () => {
            void restoreOrderLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.slabHeal', () => {
            void selfHealingLoop.runNow('manual');
        }),
        vscode.commands.registerCommand('chthonic.refreshRustification', () => {
            void refreshRustification('manual-command');
        }),
        vscode.commands.registerCommand('chthonic.annoDetect', () => {
            if (workspaceRoot) {
                annoClient.start(workspaceRoot);
            }
            vscode.window.showInformationMessage('ANNO project detection triggered');
        }),
        vscode.commands.registerCommand('chthonic.reactorSediment', async () => {
            try {
                const result = await annoClient.requestSediment(10, 500);
                vscode.window.showInformationMessage(
                    `Sediment computed: ${result.file_count} files, ${result.layer_count} layers (${result.backend}, ${result.compute_time_ms}ms)`,
                );
            } catch (err) {
                vscode.window.showErrorMessage(`Sediment computation failed: ${err}`);
            }
        }),
        vscode.commands.registerCommand('chthonic.openWebCockpit', () => {
            const cockpitUrl = resolveWebCockpitUrl(chthonicConfig);
            void vscode.env.openExternal(vscode.Uri.parse(cockpitUrl));
        }),
        vscode.commands.registerCommand('chthonic.startWebCockpit', () => {
            if (!workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to start the Bun/Next cockpit.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Web Cockpit',
                cwd: workspaceRoot,
            });
            terminal.show();
            terminal.sendText('bun run web:dev');
            outputChannel.appendLine('[web-cockpit] started via bun run web:dev');
        }),
        vscode.commands.registerCommand('chthonic.openBunTrainingDocs', async () => {
            const docs = [
                {
                    label: 'Bun React Guide',
                    description: 'Build a React app with Bun',
                    url: 'https://bun.com/docs/guides/ecosystem/react#build-a-react-app-with-bun',
                },
                {
                    label: 'Bun Next.js Guide',
                    description: 'Build an app with Next.js and Bun',
                    url: 'https://bun.com/docs/guides/ecosystem/nextjs#build-an-app-with-next-js-and-bun',
                },
                {
                    label: 'Bun Tailwind (Fullstack Bundler)',
                    description: 'Tailwind plugin lane for Bun fullstack',
                    url: 'https://bun.com/docs/bundler/fullstack#tailwindcss-plugin',
                },
                {
                    label: 'Bun SQLite API',
                    description: 'Typed SQL training lane (bun:sqlite)',
                    url: 'https://bun.com/docs/api/sqlite',
                },
            ];
            const pick = await vscode.window.showQuickPick(docs, {
                placeHolder: 'Open Bun training docs',
            });
            if (!pick) {
                return;
            }
            void vscode.env.openExternal(vscode.Uri.parse(pick.url));
        }),
    );

    if (workspaceRoot && chthonicConfig.get<boolean>('webCockpit.autoStart', false)) {
        void vscode.commands.executeCommand('chthonic.startWebCockpit');
    }

    // --- Theme Switcher ---
    const themeProvider = new ThemeTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.themeView', themeProvider);

    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.switchTheme', async () => {
            const themes = [
                { label: '$(paintcan) Flesh & Earth', description: 'Warm earth · WCAG AA · Distribution palette', id: 'Chthonic Mandala - Flesh & Earth' },
                { label: '$(zap) ROGBIV', description: 'SSOT spectral · FA¹⁻⁵ canonical hexes', id: 'Chthonic Mandala - ROGBIV' },
            ];
            const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme');
            const pick = await vscode.window.showQuickPick(themes.map(t => ({
                ...t,
                picked: current === t.id
            })), { placeHolder: `Current: ${current}` });
            if (pick) {
                await vscode.workspace.getConfiguration('workbench').update('colorTheme', pick.id, vscode.ConfigurationTarget.Workspace);
                vscode.window.showInformationMessage(`Theme: ${pick.id}`);
                themeProvider.refresh();
            }
        })
    );

    // --- Status Bar: SSOT Hash ---
    const displayConfig = chthonicConfig;
    if (displayConfig.get<boolean>('showSSOTHash', true)) {
        const ssotItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
        ssotItem.command = 'chthonic.verifySSOT';
        ssotItem.tooltip = 'SSOT integrity hash — click to verify';
        context.subscriptions.push(ssotItem);
        updateSSOTHash(ssotItem);

        // Re-check on save
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(doc => {
                if (doc.fileName.includes('copilot-instructions')) {
                    updateSSOTHash(ssotItem);
                }
            })
        );
    }

    // --- Status Bar: Lineage ---
    if (displayConfig.get<boolean>('showLineage', true)) {
        const lineageItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 49);
        lineageItem.text = '$(git-branch) ☥ main';
        lineageItem.tooltip = 'Chthonic lineage';
        lineageItem.show();
        context.subscriptions.push(lineageItem);
    }

    // --- Status View ---
    const statusProvider = new StatusTreeProvider();
    vscode.window.registerTreeDataProvider('chthonic.statusView', statusProvider);

    // --- SSOT Verify Command ---
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.verifySSOT', async () => {
            const hash = computeSSOTHash();
            if (hash) {
                vscode.window.showInformationMessage(`SSOT SHA-256: ${hash.substring(0, 16)}…`);
            } else {
                vscode.window.showWarningMessage('SSOT file not found');
            }
        })
    );

    // --- Refresh Command ---
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.refreshStatus', () => {
            statusProvider.refresh();
            themeProvider.refresh();
            entropyClient.rescanNow();
            entropyClient.requestGraph(260);
            polyglotOrchestrator.requestManualScan();
            void refreshRustification('refresh-status');
        })
    );
}

export function deactivate() {}

async function requestSedimentForWebview(
    annoClient: AnnoClient,
    abyssalProvider: AbyssalPaneProvider,
    synapseBridge: SynapseBridge,
    outputChannel: vscode.OutputChannel,
): Promise<void> {
    try {
        if (synapseBridge.isReady()) {
            const result = await annoClient.requestSedimentSynapse(10, 500, 220);
            if (result.transport === 'shared_memory') {
                const drained = await synapseBridge.drain(result, (chunk) => {
                    abyssalProvider.postSedimentBinary(chunk);
                });
                outputChannel.appendLine(`[reactor] synapse drain ${drained}/${result.chunks_written} chunks`);
                return;
            }
        }

        await annoClient.requestSedimentStream(10, 500);
    } catch (error) {
        outputChannel.appendLine(`[reactor] sediment request failed: ${error}`);
    }
}

// --- SSOT Hash ---
function computeSSOTHash(): string | null {
    const ws = vscode.workspace.workspaceFolders?.[0];
    if (!ws) return null;
    const ssotRel = vscode.workspace.getConfiguration('chthonic').get<string>('ssotPath', '.github/copilot-instructions.md');
    const ssotPath = path.join(ws.uri.fsPath, ssotRel);
    if (!fs.existsSync(ssotPath)) return null;
    const content = fs.readFileSync(ssotPath, 'utf-8');
    const canonical = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
        .split('\n').map(l => l.trimEnd()).join('\n').trim();
    return crypto.createHash('sha256').update(canonical, 'utf-8').digest('hex');
}

function updateSSOTHash(item: vscode.StatusBarItem) {
    const hash = computeSSOTHash();
    if (hash) {
        item.text = `$(shield) ${hash.substring(0, 8)}`;
        item.show();
    } else {
        item.text = '$(shield) SSOT ??';
        item.show();
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

function resolveWebCockpitUrl(config: vscode.WorkspaceConfiguration): string {
    const raw = config.get<string>('webCockpit.url', 'http://127.0.0.1:3000').trim();
    if (/^https?:\/\//i.test(raw)) {
        return raw;
    }
    return `http://${raw}`;
}

// --- Theme Tree ---
class ThemeTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;
    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || '';
        const themes = [
            { name: 'Chthonic Mandala - Flesh & Earth', short: 'Flesh & Earth', icon: '🌍', desc: 'Warm earth · Distribution' },
            { name: 'Chthonic Mandala - ROGBIV', short: 'ROGBIV', icon: '🌈', desc: 'SSOT spectral · Research' },
        ];
        return themes.map(t => {
            const active = current === t.name;
            const item = new vscode.TreeItem(
                `${active ? '◉' : '○'} ${t.icon} ${t.short}`,
                vscode.TreeItemCollapsibleState.None
            );
            item.tooltip = `${t.name}\n${t.desc}${active ? '\n\n✅ ACTIVE' : ''}`;
            item.description = active ? 'active' : '';
            item.command = { command: 'chthonic.switchTheme', title: 'Switch' };
            return item;
        });
    }
}

// --- Status Tree ---
class StatusTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;
    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const hash = computeSSOTHash();
        const items: vscode.TreeItem[] = [];

        const ssotItem = new vscode.TreeItem(
            `$(shield) SSOT: ${hash ? hash.substring(0, 12) + '…' : 'not found'}`,
            vscode.TreeItemCollapsibleState.None
        );
        ssotItem.command = { command: 'chthonic.verifySSOT', title: 'Verify' };
        items.push(ssotItem);

        const themeItem = new vscode.TreeItem(
            `$(paintcan) Theme: ${(vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || 'default').replace('Chthonic Mandala - ', '')}`,
            vscode.TreeItemCollapsibleState.None
        );
        themeItem.command = { command: 'chthonic.switchTheme', title: 'Switch' };
        items.push(themeItem);

        return items;
    }
}
