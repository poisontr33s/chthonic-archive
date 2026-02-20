import * as vscode from 'vscode';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';
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

    // --- Core Runtime ---
    const outputChannel = vscode.window.createOutputChannel('Chthonic Archive');
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
    const chthonicConfig = vscode.workspace.getConfiguration('chthonic');

    context.subscriptions.push(
        outputChannel,
        vscode.window.registerWebviewViewProvider('chthonic.chatView', new ParkedChatProvider()),
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
    const entropyLedgerMode = entropyConfig.get<LedgerMode>('entropy.ledgerMode', 'bankrun');
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
    loomProvider.updateWorkspaceHealth(entropyClient.getSnapshot());

    context.subscriptions.push(
        entropyClient,
        entropyDecorations,
        abyssalProvider,
        polyglotOrchestrator,
        entropyClient.onDidUpdateSnapshot((snapshot) => {
            loomProvider.updateWorkspaceHealth(snapshot);
        }),
        vscode.window.registerFileDecorationProvider(entropyDecorations),
        vscode.window.registerWebviewViewProvider(AbyssalPaneProvider.viewType, abyssalProvider),
    );

    const refreshToolchainCompleteness = async (reason: string): Promise<void> => {
        if (!workspaceRoot) {
            return;
        }
        const report = await computeRustificationReport(workspaceRoot);
        loomProvider.update(report);
        await activityBarMorph.update(report);
        outputChannel.appendLine(`[monolith] toolchain completeness ${report.score}% (${report.tier}) via ${reason}`);
    };

    if (workspaceRoot) {
        void refreshToolchainCompleteness('startup');

        const markerWatcher = vscode.workspace.createFileSystemWatcher(
            new vscode.RelativePattern(
                workspaceRoot,
                '{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}',
            ),
        );
        context.subscriptions.push(
            markerWatcher,
            markerWatcher.onDidCreate(() => { void refreshToolchainCompleteness('marker-create'); }),
            markerWatcher.onDidChange(() => { void refreshToolchainCompleteness('marker-change'); }),
            markerWatcher.onDidDelete(() => { void refreshToolchainCompleteness('marker-delete'); }),
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
            if (!workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to refresh workspace health.');
                return;
            }
            if (!entropyEnabled) {
                void vscode.window.showWarningMessage('Workspace health lane is disabled (chthonic.entropy.enabled=false).');
                return;
            }
            entropyClient.rescanNow();
            entropyClient.requestGraph(260);
            polyglotOrchestrator.requestManualScan();
            vscode.window.showInformationMessage('Chthonic workspace health scan requested');
        }),
    );

    // --- ANNO / Workspace Health Reactor ---
    const reactorEnabled = entropyConfig.get<boolean>('reactor.enabled', true);
    const reactorHeadlessVulkan = entropyConfig.get<boolean>('reactor.headlessVulkan', true);
    const reactorCockpitAutoLayout = entropyConfig.get<boolean>('reactor.cockpitAutoLayout', false);
    const reactorTransport = entropyConfig.get<string>('reactor.transport', 'auto');
    const reactorDaemonBinaryPath = asOptionalPath(entropyConfig.get<string>('reactor.daemonBinaryPath', ''));
    const reactorReadiness = assessReactorReadiness(workspaceRoot, reactorEnabled, reactorDaemonBinaryPath);
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

    if (!reactorReadiness.ready) {
        outputChannel.appendLine(`[reactor] lane parked: ${reactorReadiness.reason}`);
    }

    context.subscriptions.push(annoClient, cockpitLayout, synapseBridge);

    const handleEntropyState = (state: EntropyState): void => {
        void activityBarMorph.updateEntropy(state);
        outputChannel.appendLine(
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
                void selfHealingLoop.runNow('manual');
            }
        });
    };

    context.subscriptions.push(
        annoClient.onDidReceiveEnv((envReport) => {
            cockpitLayout.applyTerminalEnv(envReport);
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

    if (reactorReadiness.ready && workspaceRoot && reactorEnabled) {
        annoClient.start(workspaceRoot);
        void annoClient.requestEntropyState()
            .then((state) => {
                handleEntropyState(state);
            })
            .catch((error) => {
                outputChannel.appendLine(`[workspace-health] initial snapshot unavailable: ${error}`);
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
            void refreshToolchainCompleteness('manual-command');
        }),
        vscode.commands.registerCommand('chthonic.annoDetect', () => {
            if (!reactorReadiness.ready) {
                void vscode.window.showWarningMessage(
                    `ANNO lane unavailable: ${reactorReadiness.reason}. Using workspace-health fallback.`,
                );
                void vscode.commands.executeCommand('chthonic.entropyRefresh');
                return;
            }
            if (workspaceRoot) {
                annoClient.start(workspaceRoot);
            }
            vscode.window.showInformationMessage('ANNO project detection triggered');
        }),
        vscode.commands.registerCommand('chthonic.reactorSediment', async () => {
            if (!reactorReadiness.ready) {
                entropyClient.rescanNow();
                entropyClient.requestGraph(260);
                vscode.window.showInformationMessage(
                    `Reactor sediment lane unavailable (${reactorReadiness.reason}); refreshed workspace-health graph instead.`,
                );
                return;
            }
            try {
                const result = await annoClient.requestSediment(10, 500);
                vscode.window.showInformationMessage(
                    `Sediment computed: ${result.file_count} files, ${result.layer_count} layers (${result.backend}, ${result.compute_time_ms}ms)`,
                );
            } catch (err) {
                vscode.window.showErrorMessage(`Sediment computation failed: ${err}`);
            }
        }),
        vscode.commands.registerCommand('chthonic.openWebCockpit', async () => {
            const cockpitUrl = resolveWebCockpitUrl(chthonicConfig);
            const reachable = await isWebCockpitReachable(cockpitUrl, 1_200);

            if (!reachable) {
                const choice = await vscode.window.showWarningMessage(
                    `Web cockpit is not responding at ${cockpitUrl}.`,
                    'Start and Open',
                    'Open Anyway',
                    'Cancel',
                );
                if (!choice || choice === 'Cancel') {
                    return;
                }
                if (choice === 'Start and Open') {
                    await vscode.commands.executeCommand('chthonic.startWebCockpit');
                    await delay(1_800);
                }
            }

            openWebCockpitPanel(context, outputChannel, cockpitUrl);
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
        vscode.commands.registerCommand('chthonic.postRestartVerify', () => {
            if (!workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to run post-restart verification.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Post-Restart Verify',
                cwd: workspaceRoot,
            });
            terminal.show();
            terminal.sendText('bun run --cwd extensions/chthonic-archive insiders:post-restart:verify');
            outputChannel.appendLine('[insiders] post-restart verification lane started');
        }),
        vscode.commands.registerCommand('chthonic.restartGate', () => {
            if (!workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to run restart gate checks.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Restart Gate',
                cwd: workspaceRoot,
            });
            terminal.show();
            terminal.sendText('bun run --cwd extensions/chthonic-archive insiders:restart:gate');
            outputChannel.appendLine('[insiders] restart gate check lane started');
        }),
        vscode.commands.registerCommand('chthonic.runtimeStatus', async () => {
            const cockpitUrl = resolveWebCockpitUrl(chthonicConfig);
            const webCockpitReachable = await isWebCockpitReachable(cockpitUrl, 900);
            const commandCatalog = new Set(await vscode.commands.getCommands(true));
            const rows = collectRuntimeStatusRows({
                workspaceRoot,
                entropyEnabled,
                entropyPolyglotEnabled,
                entropyLedgerMode,
                reactorReadiness,
                slabSelfHealingEnabled,
                extensionPath: context.extensionPath,
                webCockpitUrl: cockpitUrl,
                webCockpitReachable,
                commandCatalog,
            });

            outputChannel.show(true);
            outputChannel.appendLine('[runtime] component status');
            for (const row of rows) {
                outputChannel.appendLine(`[runtime] ${row}`);
            }

            const degraded = rows.some((row) =>
                row.includes('DISABLED')
                || row.includes('PARKED')
                || row.includes('UNAVAILABLE')
                || row.includes('MISSING')
                || row.includes('UNREACHABLE'));
            void vscode.window.showInformationMessage(
                degraded
                    ? 'Some runtime lanes are parked. See Chthonic Archive output for details.'
                    : 'All runtime lanes are operational.',
            );
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
                { label: '$(symbol-color) Geological Core', description: 'Mineral strata palette · deep earth lane', id: 'Chthonic Geological Core' },
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
        lineageItem.command = 'workbench.view.scm';
        const refreshLineage = () => {
            const lineage = readGitLineage(workspaceRoot);
            lineageItem.text = `$(git-branch) ${lineage.label}`;
            lineageItem.tooltip = lineage.tooltip;
            lineageItem.show();
        };

        refreshLineage();
        const intervalHandle = setInterval(refreshLineage, 6_000);
        context.subscriptions.push({
            dispose: () => clearInterval(intervalHandle),
        });

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
            void refreshToolchainCompleteness('refresh-status');
        })
    );
}

export function deactivate() {}

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

function openWebCockpitPanel(
    context: vscode.ExtensionContext,
    outputChannel: vscode.OutputChannel,
    cockpitUrl: string,
): void {
    const panel = vscode.window.createWebviewPanel(
        'chthonicWebCockpit',
        'Chthonic Web Cockpit',
        vscode.ViewColumn.Active,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
        },
    );

    panel.webview.html = buildWebCockpitHtml(cockpitUrl);

    panel.webview.onDidReceiveMessage(
        async (message: unknown) => {
            if (!message || typeof message !== 'object') {
                return;
            }
            const payload = message as { type?: string; url?: string };
            if (payload.type === 'start') {
                await vscode.commands.executeCommand('chthonic.startWebCockpit');
                return;
            }
            if (payload.type === 'openExternal' && payload.url) {
                await vscode.env.openExternal(vscode.Uri.parse(payload.url));
                return;
            }
            outputChannel.appendLine(`[webview] Received message: ${JSON.stringify(message)}`);
        },
        undefined,
        context.subscriptions,
    );

    panel.onDidDispose(
        () => {
            outputChannel.appendLine('[webview] Chthonic Web Cockpit panel disposed');
        },
        undefined,
        context.subscriptions,
    );
}

function buildWebCockpitHtml(cockpitUrl: string): string {
    const nonce = createNonce();
    const safeUrl = escapeHtml(cockpitUrl);
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src http: https:; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>Chthonic Web Cockpit</title>
    <style>
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            font-family: var(--vscode-font-family, Segoe UI, sans-serif);
        }
        .shell {
            display: grid;
            grid-template-rows: auto 1fr;
            height: 100%;
        }
        .bar {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
            background: var(--vscode-sideBar-background);
            font-size: 12px;
        }
        .status {
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--vscode-descriptionForeground);
        }
        .btn {
            border: 1px solid var(--vscode-button-border, var(--vscode-panel-border));
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 11px;
            cursor: pointer;
        }
        .btn:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }
        iframe {
            border: 0;
            width: 100%;
            height: 100%;
            background: #0b0b0b;
        }
    </style>
</head>
<body>
    <section class="shell">
        <header class="bar">
            <div id="status" class="status">Connecting to ${safeUrl}</div>
            <button id="start" class="btn" type="button">Start Server</button>
            <button id="external" class="btn" type="button">Open Browser</button>
        </header>
        <iframe id="cockpit" src="${safeUrl}" title="Chthonic Web Cockpit"></iframe>
    </section>
    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const targetUrl = ${JSON.stringify(cockpitUrl)};
        const statusNode = document.getElementById('status');
        const iframe = document.getElementById('cockpit');
        let loaded = false;

        iframe.addEventListener('load', () => {
            loaded = true;
            statusNode.textContent = 'Connected: ' + targetUrl;
        });

        setTimeout(() => {
            if (!loaded) {
                statusNode.textContent = 'No response from ' + targetUrl + ' (try Start Server).';
            }
        }, 5000);

        document.getElementById('start').addEventListener('click', () => {
            vscode.postMessage({ type: 'start' });
        });
        document.getElementById('external').addEventListener('click', () => {
            vscode.postMessage({ type: 'openExternal', url: targetUrl });
        });
    </script>
</body>
</html>`;
}

async function isWebCockpitReachable(url: string, timeoutMs = 1_200): Promise<boolean> {
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), Math.max(300, timeoutMs));
    try {
        const response = await fetch(url, {
            method: 'GET',
            redirect: 'follow',
            signal: abort.signal,
        });
        return response.ok;
    } catch {
        return false;
    } finally {
        clearTimeout(timer);
    }
}

function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function createNonce(): string {
    const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 24; i += 1) {
        nonce += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return nonce;
}

interface ReactorReadiness {
    ready: boolean;
    reason: string;
    daemonPath?: string;
}

function assessReactorReadiness(
    workspaceRoot: string | null,
    enabled: boolean,
    daemonBinaryOverride?: string,
): ReactorReadiness {
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

interface RuntimeStatusInput {
    workspaceRoot: string | null;
    entropyEnabled: boolean;
    entropyPolyglotEnabled: boolean;
    entropyLedgerMode: LedgerMode;
    reactorReadiness: ReactorReadiness;
    slabSelfHealingEnabled: boolean;
    extensionPath: string;
    webCockpitUrl: string;
    webCockpitReachable: boolean;
    commandCatalog: Set<string>;
}

function collectRuntimeStatusRows(input: RuntimeStatusInput): string[] {
    const rows: string[] = [];
    const entropyWorkerPath = path.join(input.extensionPath, 'dist', 'entropy-worker.js');
    const entropyWorkerReady = fs.existsSync(entropyWorkerPath);
    const mandalaBridgeReady = input.commandCatalog.has('chthonic.mandalaBridge.switchTheme');
    const statusBridgeReady = input.commandCatalog.has('chthonic.bridge.verifySSOT');

    rows.push(`workspace=${input.workspaceRoot ? 'READY' : 'UNAVAILABLE'}`);
    rows.push(`workspace-health=${input.entropyEnabled ? 'ENABLED' : 'DISABLED'}`);
    rows.push(
        `polyglot-sidecars=${
            input.entropyEnabled
                ? (input.entropyPolyglotEnabled ? 'ENABLED' : 'DISABLED')
                : 'PARKED (workspace-health disabled)'
        }`,
    );
    rows.push(
        `ledger-mode=${
            input.entropyEnabled && input.entropyPolyglotEnabled
                ? input.entropyLedgerMode
                : `PARKED (${input.entropyLedgerMode}, polyglot disabled)`
        }`,
    );
    rows.push(`self-healing=${input.slabSelfHealingEnabled ? 'ENABLED' : 'DISABLED'}`);
    rows.push(`reactor=${input.reactorReadiness.ready ? 'READY' : `PARKED (${input.reactorReadiness.reason})`}`);
    rows.push(`entropy-worker=${entropyWorkerReady ? 'READY' : 'MISSING'}`);
    rows.push(
        `abyssal-view=${
            input.entropyEnabled
                ? (entropyWorkerReady ? 'READY' : `PARKED (worker missing at ${entropyWorkerPath})`)
                : 'PARKED (workspace-health disabled)'
        }`,
    );
    rows.push(`loom-view=${input.workspaceRoot ? 'READY' : 'PARKED (workspace unavailable)'}`);
    rows.push(`web-cockpit-url=${input.webCockpitUrl}`);
    rows.push(`web-cockpit=${input.webCockpitReachable ? 'REACHABLE' : 'UNREACHABLE'}`);
    rows.push(`bridge-mandala=${mandalaBridgeReady ? 'READY' : 'UNAVAILABLE'}`);
    rows.push(`bridge-statusbar=${statusBridgeReady ? 'READY' : 'UNAVAILABLE'}`);
    if (input.reactorReadiness.daemonPath) {
        rows.push(`reactor-daemon=${input.reactorReadiness.daemonPath}`);
    }
    return rows;
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

class ParkedChatProvider implements vscode.WebviewViewProvider {
    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        webviewView.webview.options = { enableScripts: false };
        webviewView.webview.html = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <style>
                    body {
                        margin: 0;
                        padding: 16px;
                        font-family: var(--vscode-font-family);
                        color: var(--vscode-foreground);
                        background: var(--vscode-editor-background);
                    }
                    h3 {
                        margin: 0 0 8px 0;
                        font-size: 14px;
                    }
                    p {
                        margin: 0;
                        line-height: 1.4;
                        color: var(--vscode-descriptionForeground);
                    }
                </style>
            </head>
            <body>
                <h3>Agent Chat Parked</h3>
                <p>
                    SDK/ACP chat integration is intentionally parked during runtime hardening.
                    Existing SDK files remain in source for later reactivation.
                </p>
            </body>
            </html>
        `;
    }
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
            { name: 'Chthonic Geological Core', short: 'Geological Core', icon: '🪨', desc: 'Mineral strata · Deep earth' },
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
