// @SID: EXT_ACTIVATION_VIEWS_V1
import * as vscode from 'vscode';
import { AbyssalPaneProvider } from '../entropy/archiveAbyssalView';
import { EntropyDecorationProvider } from '../entropy/entropyDecorations';
import { AnkhReferenceProvider } from '../monolith/ankhReferenceView';
import { LoomViewProvider } from '../monolith/loomView';
import { StylusInputProvider } from '../monolith/stylusInputView';
import type { LaneRegistry } from '../runtime/laneState';

export interface ActivateViewsDeps {
    readonly workspaceRoot: string | null;
    readonly outputChannel: vscode.OutputChannel;
    readonly laneRegistry: LaneRegistry;
    readonly loomProvider: LoomViewProvider;
    readonly stylusProvider: StylusInputProvider;
    readonly entropyDecorations: EntropyDecorationProvider;
    readonly abyssalProvider: AbyssalPaneProvider;
    readonly themeProvider: vscode.TreeDataProvider<vscode.TreeItem>;
    readonly statusProvider: vscode.TreeDataProvider<vscode.TreeItem>;
}

export function activateViews(context: vscode.ExtensionContext, deps: ActivateViewsDeps): void {
    registerView(context, deps, 'chat-view', () =>
        vscode.window.registerWebviewViewProvider('chthonic.chatView', new AnkhReferenceProvider(deps.workspaceRoot)),
    );
    registerView(context, deps, 'loom-view', () =>
        vscode.window.registerWebviewViewProvider(LoomViewProvider.viewType, deps.loomProvider),
    );
    registerView(context, deps, 'stylus-view', () =>
        vscode.window.registerWebviewViewProvider(StylusInputProvider.viewType, deps.stylusProvider),
    );
    registerView(context, deps, 'workspace-health-decorations', () =>
        vscode.window.registerFileDecorationProvider(deps.entropyDecorations),
    );
    registerView(context, deps, 'abyssal-view', () =>
        vscode.window.registerWebviewViewProvider(AbyssalPaneProvider.viewType, deps.abyssalProvider),
    );
    registerView(context, deps, 'theme-view', () =>
        vscode.window.registerTreeDataProvider('chthonic.themeView', deps.themeProvider),
    );
    registerView(context, deps, 'status-view', () =>
        vscode.window.registerTreeDataProvider('chthonic.statusView', deps.statusProvider),
    );
}

export class ThemeTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;
    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const current = vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || '';
        const themes = [
            { name: 'Chthonic — Flesh & Earth (The Decorator)', short: 'Flesh & Earth', icon: 'paintcan', desc: 'The Decorator · Warm earth' },
            { name: 'Chthonic — ROGBIV (Spectra Chroma)', short: 'ROGBIV', icon: 'zap', desc: 'Spectra Chroma · Spectral canon' },
            { name: 'Chthonic — Geological Core (Sister Ferrum Scoriae)', short: 'Geological Core', icon: 'symbol-color', desc: 'Ferrum Scoriae · Forge strata' },
            { name: 'Chthonic — The Decorator', short: 'The Decorator', icon: 'flame', desc: 'Tier 0.5 · Ornamental precision' },
        ];
        return themes.map(t => {
            const active = current === t.name;
            const item = new vscode.TreeItem(
                `${active ? '◉' : '○'} ${t.short}`,
                vscode.TreeItemCollapsibleState.None,
            );
            item.iconPath = new vscode.ThemeIcon(t.icon);
            item.tooltip = `${t.name}\n${t.desc}${active ? '\n\n✅ ACTIVE' : ''}`;
            item.description = active ? '✅ Active' : t.desc;
            item.command = { command: 'chthonic.switchTheme', title: 'Switch Theme', arguments: [t.name] };
            return item;
        });
    }
}

export class StatusTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    private _entropyEnabled = false;
    private _allowSidecars = false;
    private _reactorReady = false;
    private _selfHealing = false;

    constructor(private readonly getPolicyFingerprint: () => string | null) {}

    configure(opts: { entropyEnabled: boolean; allowSidecars: boolean; reactorReady: boolean; selfHealing: boolean }) {
        this._entropyEnabled = opts.entropyEnabled;
        this._allowSidecars = opts.allowSidecars;
        this._reactorReady = opts.reactorReady;
        this._selfHealing = opts.selfHealing;
    }

    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: vscode.TreeItem) { return el; }

    getChildren(): vscode.TreeItem[] {
        const items: vscode.TreeItem[] = [];

        const hash = this.getPolicyFingerprint();
        const fpItem = new vscode.TreeItem(
            `Policy: ${hash ? hash.substring(0, 12) + '…' : 'not found'}`,
            vscode.TreeItemCollapsibleState.None,
        );
        fpItem.iconPath = new vscode.ThemeIcon('shield');
        fpItem.command = { command: 'chthonic.verifySSOT', title: 'Verify' };
        items.push(fpItem);

        const currentTheme = (vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || 'default').replace('Chthonic Mandala - ', '');
        const themeItem = new vscode.TreeItem(
            `Theme: ${currentTheme}`,
            vscode.TreeItemCollapsibleState.None,
        );
        themeItem.iconPath = new vscode.ThemeIcon('paintcan');
        themeItem.command = { command: 'chthonic.switchTheme', title: 'Switch' };
        items.push(themeItem);

        const secItem = new vscode.TreeItem(
            `Sidecars: ${this._allowSidecars ? 'unlocked' : 'locked'}`,
            vscode.TreeItemCollapsibleState.None,
        );
        secItem.iconPath = new vscode.ThemeIcon(this._allowSidecars ? 'unlock' : 'lock');
        secItem.tooltip = this._allowSidecars
            ? 'Native sidecars are enabled — polyglot, reactor, and self-healing lanes are permitted.'
            : 'Native sidecars disabled (safe mode). Set chthonic.security.allowNativeSidecars to enable.';
        items.push(secItem);

        const subsystems = [
            { label: 'Entropy', on: this._entropyEnabled, icon: 'pulse' },
            { label: 'Reactor', on: this._reactorReady, icon: 'flame' },
            { label: 'Self-Heal', on: this._selfHealing, icon: 'tools' },
        ];
        for (const s of subsystems) {
            const sub = new vscode.TreeItem(
                `${s.label}: ${s.on ? 'active' : 'off'}`,
                vscode.TreeItemCollapsibleState.None,
            );
            sub.iconPath = new vscode.ThemeIcon(s.on ? s.icon : 'circle-slash');
            items.push(sub);
        }

        const rtItem = new vscode.TreeItem(
            'Full Runtime Status…',
            vscode.TreeItemCollapsibleState.None,
        );
        rtItem.iconPath = new vscode.ThemeIcon('output');
        rtItem.command = { command: 'chthonic.runtimeStatus', title: 'Runtime Status' };
        items.push(rtItem);

        return items;
    }
}

function registerView(
    context: vscode.ExtensionContext,
    deps: ActivateViewsDeps,
    laneName: string,
    register: () => vscode.Disposable,
): void {
    try {
        context.subscriptions.push(register());
    } catch (error) {
        const reason = stringifyError(error);
        deps.outputChannel.appendLine(`[activation:view] ${laneName} registration failed: ${reason}`);
        deps.laneRegistry.set({
            name: laneName,
            state: 'DEGRADED',
            reason,
        });
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
