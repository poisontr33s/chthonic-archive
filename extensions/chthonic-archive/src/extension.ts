// @SID: EXT_EXTENSION_V1
import * as vscode from 'vscode';
import { ActivityBarMorph } from './monolith/activityBarMorph';
import { DesignFrameProvider } from './design/designFrameView';
import { DeepFocusLayout } from './monolith/deepFocusLayout';
import { RestoreOrderLayout } from './monolith/restoreOrderLayout';
import { LoomViewProvider } from './monolith/loomView';
import { computeRustificationReport } from './monolith/rustificationScore';
import { StylusInputProvider } from './monolith/stylusInputView';
import { registerRenderedMarkdownPasteLane } from './markdownPaste/register';
import { registerStatusBridgeLane } from './statusbar/register';
import { LaneRegistry } from './runtime/laneState';
import { registerDevAutoReload } from './runtime/devAutoReload';
import { registerWebviewHmrWatcher } from './runtime/webviewHmrWatcher';
import { activateCommands } from './activation/activateCommands';
import { FluxService } from './flux/fluxService';
import { activateStatus, computePolicyFingerprint } from './activation/activateStatus';
import { activateViews, StatusTreeProvider, ThemeTreeProvider } from './activation/activateViews';
import { activateSidecars } from './activation/activateSidecars';
import type { ActivationDeps } from './activation/types';

export function activate(context: vscode.ExtensionContext) {
    console.log('☥ Chthonic Archive extension activated');

    const outputChannel = vscode.window.createOutputChannel('Chthonic Archive');
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
    const chthonicConfig = vscode.workspace.getConfiguration('chthonic');

    const laneRegistry = new LaneRegistry();
    laneRegistry.bindSnapshotFile(context.globalStorageUri);
    runActivationLane(laneRegistry, outputChannel, 'dev-reload', () => registerDevAutoReload(context, outputChannel));
    runActivationLane(laneRegistry, outputChannel, 'webview-hmr', () => registerWebviewHmrWatcher(context, outputChannel, laneRegistry));

    context.subscriptions.push(outputChannel, laneRegistry);
    runActivationLane(laneRegistry, outputChannel, 'markdown-paste', () => registerRenderedMarkdownPasteLane(context, outputChannel));
    runActivationLane(laneRegistry, outputChannel, 'statusbar', () => registerStatusBridgeLane(context, outputChannel, workspaceRoot));

    const activityBarMorph = new ActivityBarMorph(context.extensionUri, outputChannel);
    context.subscriptions.push(
        laneRegistry.onDidChange(() => activityBarMorph.updateLanes(laneRegistry.snapshot())),
    );
    const designFrameProvider = new DesignFrameProvider(context.extensionUri, workspaceRoot, outputChannel);
    const deepFocusLayout = new DeepFocusLayout(outputChannel);
    const restoreOrderLayout = new RestoreOrderLayout(outputChannel);
    const loomProvider = new LoomViewProvider(context.extensionUri);
    const activationDeps: ActivationDeps = { context, outputChannel, workspaceRoot, chthonicConfig, laneRegistry, activityBarMorph, restoreOrderLayout, loomProvider };

    context.subscriptions.push(activityBarMorph, designFrameProvider, loomProvider);
    const stylusProvider = new StylusInputProvider(context.extensionUri);
    const refreshToolchainCompleteness = registerToolchainCompleteness(context, activationDeps);
    const sidecars = runActivationLane(laneRegistry, outputChannel, 'sidecars', () => activateSidecars(context, activationDeps));
    if (!sidecars) return;

    const themeProvider = new ThemeTreeProvider();
    const statusProvider = new StatusTreeProvider(
        () => computePolicyFingerprint({ workspaceRoot, chthonicConfig }),
        () => laneRegistry.snapshot(),
    );
    statusProvider.configure({ entropyEnabled: sidecars.entropyEnabled, allowSidecars: sidecars.allowNativeSidecars, reactorReady: sidecars.reactorReadiness.ready, selfHealing: sidecars.slabSelfHealingEnabled });
    runActivationLane(laneRegistry, outputChannel, 'views', () => activateViews(context, { ...activationDeps, designFrameProvider, stylusProvider, entropyDecorations: sidecars.entropyDecorations, abyssalProvider: sidecars.abyssalProvider, themeProvider, statusProvider }));
    runActivationLane(laneRegistry, outputChannel, 'commands', () => activateCommands(context, { ...sidecars, workspaceRoot, outputChannel, chthonicConfig, laneRegistry, designFrameProvider, stylusProvider, deepFocusLayout, restoreOrderLayout, themeProvider, statusProvider, refreshToolchainCompleteness }));
    runActivationLane(laneRegistry, outputChannel, 'flux', () => new FluxService(context, outputChannel, workspaceRoot).register());

    if (workspaceRoot && chthonicConfig.get<boolean>('webCockpit.autoStart', false)) {
        void vscode.commands.executeCommand('chthonic.startWebCockpit');
    }
    runActivationLane(laneRegistry, outputChannel, 'status', () => activateStatus(context, { workspaceRoot, chthonicConfig, laneRegistry }));
    void ensureDefaultChthonicPlacement(context, restoreOrderLayout, outputChannel);
}

export function deactivate() {}

function registerToolchainCompleteness(
    context: vscode.ExtensionContext,
    deps: Pick<ActivationDeps, 'workspaceRoot' | 'outputChannel' | 'activityBarMorph' | 'loomProvider'>,
): (reason: string) => Promise<void> {
    const refresh = async (reason: string): Promise<void> => {
        if (!deps.workspaceRoot) return;
        const report = await computeRustificationReport(deps.workspaceRoot);
        deps.loomProvider.update(report);
        await deps.activityBarMorph.update(report);
        deps.outputChannel.appendLine(`[monolith] toolchain completeness ${report.score}% (${report.tier}) via ${reason}`);
    };

    if (deps.workspaceRoot) {
        void refresh('startup');
        const markerWatcher = vscode.workspace.createFileSystemWatcher(new vscode.RelativePattern(
            deps.workspaceRoot,
            '{uv.lock,Cargo.toml,native/Cargo.toml,mise.toml,.mise.toml,anno-manifest.toml,go.mod,.ruby-version,Gemfile,.node-version,.nvmrc,package.json,bun.lock,.python-version}',
        ));
        context.subscriptions.push(
            markerWatcher,
            markerWatcher.onDidCreate(() => { void refresh('marker-create'); }),
            markerWatcher.onDidChange(() => { void refresh('marker-change'); }),
            markerWatcher.onDidDelete(() => { void refresh('marker-delete'); }),
        );
    }
    return refresh;
}

function runActivationLane<T>(
    laneRegistry: LaneRegistry,
    output: vscode.OutputChannel,
    laneName: string,
    action: () => T,
): T | undefined {
    try {
        return action();
    } catch (error) {
        const reason = stringifyError(error);
        output.appendLine(`[activation] ${laneName} failed: ${reason}`);
        laneRegistry.set({ name: laneName, state: 'DEGRADED', reason });
        return undefined;
    }
}

async function ensureDefaultChthonicPlacement(
    context: vscode.ExtensionContext,
    restoreOrderLayout: RestoreOrderLayout,
    output: vscode.OutputChannel,
): Promise<void> {
    const placementKey = 'chthonic.layoutPlacementAppliedVersion';
    const currentVersion = String(context.extension.packageJSON.version ?? 'unknown');
    const appliedVersion = context.workspaceState.get<string>(placementKey);

    if (appliedVersion === currentVersion) {
        return;
    }

    try {
        await restoreOrderLayout.activate();
        await context.workspaceState.update(placementKey, currentVersion);
        output.appendLine(`[layout] default Chthonic placement applied for ${currentVersion}`);
    } catch (error) {
        output.appendLine(`[layout] placement bootstrap failed: ${stringifyError(error)}`);
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
