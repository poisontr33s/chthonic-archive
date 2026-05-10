// @SID: EXT_ACTIVATION_VIEWS_V1
import * as vscode from 'vscode';
import { DesignFrameProvider } from '../design/designFrameView';
import { AbyssalPaneProvider } from '../entropy/archiveAbyssalView';
import { EntropyDecorationProvider } from '../entropy/entropyDecorations';
import { AnkhReferenceProvider } from '../monolith/ankhReferenceView';
import { LoomViewProvider } from '../monolith/loomView';
import { StylusInputProvider } from '../monolith/stylusInputView';
import type {
    LaneRegistry,
    LaneSnapshot,
    RuntimeLaneState,
    RuntimeLaneStateKind,
} from '../runtime/laneState';

export interface ActivateViewsDeps {
    readonly workspaceRoot: string | null;
    readonly outputChannel: vscode.OutputChannel;
    readonly laneRegistry: LaneRegistry;
    readonly designFrameProvider: DesignFrameProvider;
    readonly loomProvider: LoomViewProvider;
    readonly stylusProvider: StylusInputProvider;
    readonly entropyDecorations: EntropyDecorationProvider;
    readonly abyssalProvider: AbyssalPaneProvider;
    readonly themeProvider: ThemeTreeProvider;
    readonly statusProvider: StatusTreeProvider;
}

export function activateViews(context: vscode.ExtensionContext, deps: ActivateViewsDeps): void {
    registerView(context, deps, 'chat-view', () =>
        vscode.window.registerWebviewViewProvider('chthonic.chatView', new AnkhReferenceProvider(deps.workspaceRoot)),
    );
    registerView(context, deps, 'loom-view', () =>
        vscode.window.registerWebviewViewProvider(LoomViewProvider.viewType, deps.loomProvider),
    );
    registerView(context, deps, 'design-frame-view', () =>
        vscode.window.registerWebviewViewProvider(DesignFrameProvider.viewType, deps.designFrameProvider),
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
    context.subscriptions.push(
        deps.laneRegistry.onDidChange(() => deps.statusProvider.refresh()),
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

class StatusTreeNode extends vscode.TreeItem {
    readonly children: StatusTreeNode[];

    constructor(
        label: string,
        opts: {
            description?: string;
            tooltip?: string;
            icon?: string;
            command?: vscode.Command;
            children?: StatusTreeNode[];
            collapsible?: vscode.TreeItemCollapsibleState;
        } = {},
    ) {
        const children = opts.children ?? [];
        super(
            label,
            opts.collapsible ?? (children.length > 0
                ? vscode.TreeItemCollapsibleState.Collapsed
                : vscode.TreeItemCollapsibleState.None),
        );
        this.children = children;
        this.description = opts.description;
        this.tooltip = opts.tooltip;
        this.command = opts.command;
        if (opts.icon) {
            this.iconPath = new vscode.ThemeIcon(opts.icon);
        }
    }
}

export class StatusTreeProvider implements vscode.TreeDataProvider<StatusTreeNode> {
    private _onDidChange = new vscode.EventEmitter<void>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    private _entropyEnabled = false;
    private _allowSidecars = false;
    private _reactorReady = false;
    private _selfHealing = false;

    constructor(
        private readonly getPolicyFingerprint: () => string | null,
        private readonly getLaneSnapshot: () => LaneSnapshot,
    ) {}

    configure(opts: { entropyEnabled: boolean; allowSidecars: boolean; reactorReady: boolean; selfHealing: boolean }) {
        this._entropyEnabled = opts.entropyEnabled;
        this._allowSidecars = opts.allowSidecars;
        this._reactorReady = opts.reactorReady;
        this._selfHealing = opts.selfHealing;
    }

    refresh() { this._onDidChange.fire(); }

    getTreeItem(el: StatusTreeNode) { return el; }

    getChildren(el?: StatusTreeNode): StatusTreeNode[] {
        if (el) {
            return el.children;
        }
        const items: StatusTreeNode[] = [];
        const snapshot = this.getLaneSnapshot();
        const lanes = snapshot.lanes;

        const hash = this.getPolicyFingerprint();
        const fpItem = new StatusTreeNode(
            `Policy: ${hash ? hash.substring(0, 12) + '…' : 'not found'}`,
            {
                icon: 'shield',
                command: { command: 'chthonic.verifySSOT', title: 'Verify' },
            },
        );
        items.push(fpItem);

        const currentTheme = (vscode.workspace.getConfiguration('workbench').get<string>('colorTheme') || 'default').replace('Chthonic Mandala - ', '');
        const themeItem = new StatusTreeNode(
            `Theme: ${currentTheme}`,
            {
                icon: 'paintcan',
                command: { command: 'chthonic.switchTheme', title: 'Switch' },
            },
        );
        items.push(themeItem);

        items.push(this.buildConfigNode());
        items.push(this.buildOversightSummaryNode(lanes));
        items.push(this.buildHierarchyNode(lanes));
        items.push(this.buildChronologyNode(lanes));
        items.push(new StatusTreeNode('Full Runtime Status…', {
            icon: 'output',
            command: { command: 'chthonic.runtimeStatus', title: 'Runtime Status' },
        }));

        return items;
    }

    private buildConfigNode(): StatusTreeNode {
        const children = [
            new StatusTreeNode(`Sidecars: ${this._allowSidecars ? 'unlocked' : 'locked'}`, {
                icon: this._allowSidecars ? 'unlock' : 'lock',
                tooltip: this._allowSidecars
                    ? 'Native sidecars are enabled; polyglot, reactor, and self-healing lanes are permitted.'
                    : 'Native sidecars disabled. Set chthonic.security.allowNativeSidecars to enable.',
            }),
            new StatusTreeNode(`Entropy: ${this._entropyEnabled ? 'active' : 'off'}`, {
                icon: this._entropyEnabled ? 'pulse' : 'circle-slash',
            }),
            new StatusTreeNode(`Reactor: ${this._reactorReady ? 'ready' : 'off'}`, {
                icon: this._reactorReady ? 'flame' : 'circle-slash',
            }),
            new StatusTreeNode(`Self-Heal: ${this._selfHealing ? 'active' : 'off'}`, {
                icon: this._selfHealing ? 'tools' : 'circle-slash',
            }),
        ];
        return new StatusTreeNode('Configuration Gates', {
            icon: 'settings-gear',
            children,
            collapsible: vscode.TreeItemCollapsibleState.Expanded,
        });
    }

    private buildOversightSummaryNode(lanes: readonly RuntimeLaneState[]): StatusTreeNode {
        const counts = countStates(lanes);
        return new StatusTreeNode(`Oversight: ${counts.active}/${counts.total} active`, {
            icon: counts.attention > 0 ? 'warning' : 'pass',
            description: counts.attention > 0 ? `${counts.attention} need attention` : 'clear',
            tooltip: [
                `Active lanes: ${counts.active}`,
                `Parked/off lanes: ${counts.parked}`,
                `Attention lanes: ${counts.attention}`,
                `Total lanes: ${counts.total}`,
            ].join('\n'),
            command: { command: 'chthonic.runtimeStatus', title: 'Runtime Status' },
        });
    }

    private buildHierarchyNode(lanes: readonly RuntimeLaneState[]): StatusTreeNode {
        const remaining = new Map(lanes.map((lane) => [lane.name, lane]));
        const groups = OVERSIGHT_GROUPS
            .map((group) => {
                const groupLanes = group.names
                    .map((name) => remaining.get(name))
                    .filter((lane): lane is RuntimeLaneState => Boolean(lane));
                for (const lane of groupLanes) {
                    remaining.delete(lane.name);
                }
                return new StatusTreeNode(group.label, {
                    icon: group.icon,
                    description: describeLaneGroup(groupLanes),
                    children: groupLanes.map((lane) => laneNode(lane)),
                });
            })
            .filter((group) => group.children.length > 0);

        const leftovers = [...remaining.values()].sort(compareLaneNames);
        if (leftovers.length > 0) {
            groups.push(new StatusTreeNode('Other Emitted Lanes', {
                icon: 'list-tree',
                description: describeLaneGroup(leftovers),
                children: leftovers.map((lane) => laneNode(lane)),
            }));
        }

        if (groups.length === 0) {
            groups.push(new StatusTreeNode('No lane state emitted yet', {
                icon: 'circle-slash',
                tooltip: 'Run Chthonic: Runtime Status or wait for activation lanes to publish state.',
            }));
        }

        return new StatusTreeNode('Oversight Hierarchy', {
            icon: 'list-tree',
            children: groups,
            collapsible: vscode.TreeItemCollapsibleState.Expanded,
        });
    }

    private buildChronologyNode(lanes: readonly RuntimeLaneState[]): StatusTreeNode {
        const recent = [...lanes]
            .filter((lane) => typeof lane.updatedAt === 'number')
            .sort((a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0))
            .slice(0, 10);

        const children = recent.length > 0
            ? recent.map((lane) => laneNode(lane, true))
            : [new StatusTreeNode('No chronology emitted yet', {
                icon: 'clock',
                tooltip: 'LaneRegistry has not emitted timestamped lane state in this session.',
            })];

        return new StatusTreeNode('Chronology', {
            icon: 'history',
            description: recent.length > 0 ? `${recent.length} recent` : 'pending',
            children,
        });
    }
}

const OVERSIGHT_GROUPS: Array<{ label: string; icon: string; names: string[] }> = [
    {
        label: '1. Contract And Workspace',
        icon: 'shield',
        names: ['workspace', 'policyOracle', 'git-lineage'],
    },
    {
        label: '2. Visible Surfaces',
        icon: 'layout',
        names: ['loom-view', 'abyssal-view', 'markdown-paste', 'webviewHmr', 'web-cockpit'],
    },
    {
        label: '3. Local Runtime',
        icon: 'server-process',
        names: ['entropyWorker', 'workspace-health', 'native-sidecars', 'polyglot-sidecars', 'ledger-mode', 'entropyLedgerHost'],
    },
    {
        label: '4. Reactor And Synapse',
        icon: 'flame',
        names: ['reactor', 'chthonicDaemon', 'synapseShm'],
    },
    {
        label: '5. Bridge Extensions',
        icon: 'plug',
        names: ['bridge-mandala', 'bridge-statusbar'],
    },
];

function laneNode(lane: RuntimeLaneState, chronological = false): StatusTreeNode {
    const label = chronological
        ? `${stateIcon(lane.state)} ${lane.name}`
        : `${stateIcon(lane.state)} ${formatLaneName(lane.name)}`;
    const description = chronological
        ? `${formatTime(lane.updatedAt)} · ${lane.state}`
        : lane.state;
    return new StatusTreeNode(label, {
        icon: iconForState(lane.state),
        description,
        tooltip: [
            `${lane.name}=${lane.state}`,
            lane.reason ? `Reason: ${lane.reason}` : undefined,
            lane.localAction ? `Action: ${lane.localAction}` : undefined,
            lane.updatedAt ? `Updated: ${new Date(lane.updatedAt).toLocaleString()}` : undefined,
        ].filter(Boolean).join('\n'),
    });
}

function countStates(lanes: readonly RuntimeLaneState[]): {
    total: number;
    active: number;
    parked: number;
    attention: number;
} {
    let active = 0;
    let parked = 0;
    let attention = 0;
    for (const lane of lanes) {
        if (lane.state === 'READY' || lane.state === 'LIVE') {
            active += 1;
        } else if (lane.state === 'PARKED' || lane.state === 'DISABLED') {
            parked += 1;
        } else {
            attention += 1;
        }
    }
    return { total: lanes.length, active, parked, attention };
}

function describeLaneGroup(lanes: readonly RuntimeLaneState[]): string {
    if (lanes.length === 0) {
        return 'none';
    }
    const counts = countStates(lanes);
    return counts.attention > 0
        ? `${counts.active}/${counts.total} active, ${counts.attention} attention`
        : `${counts.active}/${counts.total} active`;
}

function stateIcon(state: RuntimeLaneStateKind): string {
    switch (state) {
        case 'READY':
        case 'LIVE':
            return '[on]';
        case 'PARKED':
        case 'DISABLED':
            return '[off]';
        case 'DEGRADED':
        case 'UNAVAILABLE':
        case 'MISSING':
            return '[!]';
        default:
            return '[?]';
    }
}

function iconForState(state: RuntimeLaneStateKind): string {
    switch (state) {
        case 'READY':
        case 'LIVE':
            return 'pass';
        case 'PARKED':
        case 'DISABLED':
            return 'circle-slash';
        case 'DEGRADED':
        case 'UNAVAILABLE':
        case 'MISSING':
            return 'warning';
        default:
            return 'question';
    }
}

function formatLaneName(name: string): string {
    return name
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .replace(/[-_]/g, ' ')
        .replace(/\b\w/g, (match) => match.toUpperCase());
}

function formatTime(updatedAt: number | undefined): string {
    if (!updatedAt) {
        return 'pending';
    }
    return new Date(updatedAt).toLocaleTimeString();
}

function compareLaneNames(a: RuntimeLaneState, b: RuntimeLaneState): number {
    return a.name.localeCompare(b.name);
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
