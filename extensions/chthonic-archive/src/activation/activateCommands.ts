// @SID: EXT_ACTIVATION_COMMANDS_V1
import * as vscode from 'vscode';
import * as path from 'path';
import type { EntropyWorkerClient } from '../entropy/entropyWorkerClient';
import type { PolyglotEntropyOrchestrator } from '../polyglot/polyglotEntropyOrchestrator';
import type { LedgerMode } from '../polyglot/ledgerBroker';
import type { AnnoClient } from '../reactor/annoClient';
import type { CockpitLayout } from '../reactor/cockpitLayout';
import type { DeepFocusLayout } from '../monolith/deepFocusLayout';
import type { RestoreOrderLayout } from '../monolith/restoreOrderLayout';
import type { SelfHealingLoop } from '../monolith/selfHealingLoop';
import type { StylusInputProvider } from '../monolith/stylusInputView';
import type { LaneRegistry } from '../runtime/laneState';
import {
    collectRuntimeLaneStates,
    collectRuntimeStatusRows,
    type ReactorReadiness,
    type RuntimeStatusInput,
} from '../runtime/statusReport';
import {
    delay,
    isWebCockpitReachable,
    openWebCockpitPanel,
    resolveWebCockpitUrl,
} from './activateCockpit';
import { computePolicyFingerprint } from './activateStatus';
import type { StatusTreeProvider, ThemeTreeProvider } from './activateViews';

export interface ActivateCommandsDeps {
    readonly workspaceRoot: string | null;
    readonly outputChannel: vscode.OutputChannel;
    readonly chthonicConfig: vscode.WorkspaceConfiguration;
    readonly entropyEnabled: boolean;
    readonly entropyPolyglotEnabled: boolean;
    readonly entropyLedgerMode: LedgerMode;
    readonly reactorReadiness: ReactorReadiness;
    readonly slabSelfHealingEnabled: boolean;
    readonly allowNativeSidecars: boolean;
    readonly laneRegistry: LaneRegistry;
    readonly stylusProvider: StylusInputProvider;
    readonly cockpitLayout: CockpitLayout;
    readonly deepFocusLayout: DeepFocusLayout;
    readonly restoreOrderLayout: RestoreOrderLayout;
    readonly selfHealingLoop: SelfHealingLoop;
    readonly entropyClient: EntropyWorkerClient;
    readonly polyglotOrchestrator: PolyglotEntropyOrchestrator;
    readonly annoClient: AnnoClient;
    readonly themeProvider: ThemeTreeProvider;
    readonly statusProvider: StatusTreeProvider;
    readonly refreshToolchainCompleteness: (reason: string) => Promise<void>;
}

export function activateCommands(context: vscode.ExtensionContext, deps: ActivateCommandsDeps): void {
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.openStylusInput', () => {
            void vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
            void vscode.commands.executeCommand('chthonic.stylusView.focus');
            deps.stylusProvider.focus();
        }),
        vscode.commands.registerCommand('chthonic.entropyRefresh', () => {
            if (!deps.workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to refresh workspace health.');
                return;
            }
            if (!deps.entropyEnabled) {
                void vscode.window.showWarningMessage('Workspace health lane is disabled (chthonic.entropy.enabled=false).');
                return;
            }
            deps.entropyClient.rescanNow();
            deps.entropyClient.requestGraph(260);
            deps.polyglotOrchestrator.requestManualScan();
            vscode.window.showInformationMessage('Chthonic workspace health scan requested');
        }),
        vscode.commands.registerCommand('chthonic.activateCockpit', () => {
            void deps.cockpitLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.deepFocus', () => {
            void deps.deepFocusLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.restoreOrder', () => {
            void deps.restoreOrderLayout.activate();
        }),
        vscode.commands.registerCommand('chthonic.slabHeal', () => {
            if (!deps.allowNativeSidecars) {
                void vscode.window.showWarningMessage(
                    'Native sidecars are disabled (chthonic.security.allowNativeSidecars=false).',
                );
                return;
            }
            void deps.selfHealingLoop.runNow('manual');
        }),
        vscode.commands.registerCommand('chthonic.refreshRustification', () => {
            void deps.refreshToolchainCompleteness('manual-command');
        }),
        vscode.commands.registerCommand('chthonic.annoDetect', () => {
            if (!deps.allowNativeSidecars) {
                void vscode.window.showWarningMessage(
                    'ANNO lane is disabled by chthonic.security.allowNativeSidecars=false.',
                );
                void vscode.commands.executeCommand('chthonic.entropyRefresh');
                return;
            }
            if (!deps.reactorReadiness.ready) {
                void vscode.window.showWarningMessage(
                    `ANNO lane unavailable: ${deps.reactorReadiness.reason}. Using workspace-health fallback.`,
                );
                void vscode.commands.executeCommand('chthonic.entropyRefresh');
                return;
            }
            if (deps.workspaceRoot) {
                deps.annoClient.start(deps.workspaceRoot);
            }
            vscode.window.showInformationMessage('ANNO project detection triggered');
        }),
        vscode.commands.registerCommand('chthonic.reactorSediment', async () => {
            if (!deps.reactorReadiness.ready) {
                deps.entropyClient.rescanNow();
                deps.entropyClient.requestGraph(260);
                vscode.window.showInformationMessage(
                    `Reactor sediment lane unavailable (${deps.reactorReadiness.reason}); refreshed workspace-health graph instead.`,
                );
                return;
            }
            try {
                const result = await deps.annoClient.requestSediment(10, 500);
                vscode.window.showInformationMessage(
                    `Sediment computed: ${result.file_count} files, ${result.layer_count} layers (${result.backend}, ${result.compute_time_ms}ms)`,
                );
            } catch (err) {
                vscode.window.showErrorMessage(`Sediment computation failed: ${err}`);
            }
        }),
        vscode.commands.registerCommand('chthonic.openWebCockpit', async () => {
            const cockpitUrl = resolveWebCockpitUrl(deps.chthonicConfig);
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

            openWebCockpitPanel(context, deps.outputChannel, cockpitUrl);
        }),
        vscode.commands.registerCommand('chthonic.startWebCockpit', () => {
            if (!deps.workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to start the Bun/Next cockpit.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Web Cockpit',
                cwd: deps.workspaceRoot,
                env: {
                    CHTHONIC_LANE_STATE_PATH: path.join(context.globalStorageUri.fsPath, 'lane-state.json'),
                    CHTHONIC_COCKPIT_ORIGIN: resolveWebCockpitUrl(deps.chthonicConfig),
                },
            });
            terminal.show();
            terminal.sendText('bun run web:dev');
            deps.outputChannel.appendLine('[web-cockpit] started via bun run web:dev');
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
            if (!deps.workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to run post-restart verification.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Post-Restart Verify',
                cwd: deps.workspaceRoot,
            });
            terminal.show();
            terminal.sendText('bun run --cwd extensions/chthonic-archive insiders:post-restart:verify');
            deps.outputChannel.appendLine('[insiders] post-restart verification lane started');
        }),
        vscode.commands.registerCommand('chthonic.restartGate', () => {
            if (!deps.workspaceRoot) {
                void vscode.window.showWarningMessage('Workspace root is required to run restart gate checks.');
                return;
            }
            const terminal = vscode.window.createTerminal({
                name: 'Chthonic Restart Gate',
                cwd: deps.workspaceRoot,
            });
            terminal.show();
            terminal.sendText('bun run --cwd extensions/chthonic-archive insiders:restart:gate');
            deps.outputChannel.appendLine('[insiders] restart gate check lane started');
        }),
        vscode.commands.registerCommand('chthonic.runtimeStatus', async () => {
            const cockpitUrl = resolveWebCockpitUrl(deps.chthonicConfig);
            const webCockpitReachable = await isWebCockpitReachable(cockpitUrl, 900);
            const commandCatalog = new Set(await vscode.commands.getCommands(true));
            const mandalaExtension = vscode.extensions.getExtension('chthonic-archive.chthonic-mandala');
            const statusbarExtension = vscode.extensions.getExtension('chthonic-archive.chthonic-statusbar');
            const statusInput: RuntimeStatusInput = {
                workspaceRoot: deps.workspaceRoot,
                entropyEnabled: deps.entropyEnabled,
                entropyPolyglotEnabled: deps.entropyPolyglotEnabled,
                entropyLedgerMode: deps.entropyLedgerMode,
                reactorReadiness: deps.reactorReadiness,
                slabSelfHealingEnabled: deps.slabSelfHealingEnabled,
                allowNativeSidecars: deps.allowNativeSidecars,
                extensionPath: context.extensionPath,
                webCockpitUrl: cockpitUrl,
                webCockpitReachable,
                commandCatalog,
                bridgeMandala: {
                    installed: Boolean(mandalaExtension),
                    active: mandalaExtension?.isActive ?? false,
                    commandAvailable: commandCatalog.has('chthonic.mandalaBridge.switchTheme'),
                },
                bridgeStatusbar: {
                    installed: Boolean(statusbarExtension),
                    active: statusbarExtension?.isActive ?? false,
                    commandAvailable: commandCatalog.has('chthonic.bridge.verifySSOT'),
                },
            };
            deps.laneRegistry.setMany(collectRuntimeLaneStates(statusInput));
            const rows = collectRuntimeStatusRows(statusInput);

            deps.outputChannel.show(true);
            deps.outputChannel.appendLine('[runtime] component status');
            for (const row of rows) {
                deps.outputChannel.appendLine(`[runtime] ${row}`);
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
        vscode.commands.registerCommand('chthonic.switchTheme', async (themeId?: string) => {
            const themes = [
                { label: '$(paintcan) Flesh & Earth', description: 'The Decorator · Warm earth · WCAG AA', id: 'Chthonic — Flesh & Earth (The Decorator)' },
                { label: '$(zap) ROGBIV', description: 'Spectra Chroma · Spectral canon · FA¹⁻⁵', id: 'Chthonic — ROGBIV (Spectra Chroma)' },
                { label: '$(symbol-color) Geological Core', description: 'Sister Ferrum Scoriae · Forge strata · WCAG AA', id: 'Chthonic — Geological Core (Sister Ferrum Scoriae)' },
                { label: '$(flame) The Decorator', description: 'The Decorator · Tier 0.5 · Ornamental precision', id: 'Chthonic — The Decorator' },
            ];
            let targetId = themeId;
            if (!targetId) {
                const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme');
                const pick = await vscode.window.showQuickPick(themes.map(t => ({
                    ...t,
                    picked: current === t.id,
                })), { placeHolder: `Current: ${current}` });
                if (!pick) return;
                targetId = pick.id;
            }

            await vscode.workspace.getConfiguration('workbench').update('colorTheme', targetId, vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage(`Theme: ${targetId}`);
            deps.themeProvider.refresh();
        }),
        vscode.commands.registerCommand('chthonic.verifySSOT', async () => {
            const hash = computePolicyFingerprint({
                workspaceRoot: deps.workspaceRoot,
                chthonicConfig: deps.chthonicConfig,
            });
            if (hash) {
                vscode.window.showInformationMessage(`Policy fingerprint: ${hash.substring(0, 16)}…`);
            } else {
                vscode.window.showWarningMessage('Policy file not found');
            }
        }),
        vscode.commands.registerCommand('chthonic.refreshStatus', () => {
            deps.statusProvider.refresh();
            deps.themeProvider.refresh();
            if (deps.entropyEnabled) {
                deps.entropyClient.rescanNow();
                deps.entropyClient.requestGraph(260);
                deps.polyglotOrchestrator.requestManualScan();
            }
            void deps.refreshToolchainCompleteness('refresh-status');
        }),
    );
}
