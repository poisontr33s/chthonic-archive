"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.CorpusTreeProvider = void 0;
// @SID: VAMPIRE_CORPUS_CORPUS_PROVIDER_V1
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("node:fs"));
const path = __importStar(require("node:path"));
// ---------------------------------------------------------------------------
// Tree item
// ---------------------------------------------------------------------------
class CorpusItem extends vscode.TreeItem {
    constructor(label, collapsible, kind, opts = {}) {
        super(label, collapsible);
        this.contextValue = kind;
        if (opts.description !== undefined)
            this.description = opts.description;
        if (opts.tooltip !== undefined)
            this.tooltip = opts.tooltip;
        if (opts.icon)
            this.iconPath = new vscode.ThemeIcon(opts.icon);
        if (opts.command)
            this.command = opts.command;
    }
}
class SectionItem extends vscode.TreeItem {
    sectionId;
    constructor(label, sectionId, description) {
        super(label, vscode.TreeItemCollapsibleState.Expanded);
        this.sectionId = sectionId;
        this.contextValue = 'section';
        if (description)
            this.description = description;
        switch (sectionId) {
            case 'corpus':
                this.iconPath = new vscode.ThemeIcon('database');
                break;
            case 'gates':
                this.iconPath = new vscode.ThemeIcon('symbol-boolean');
                break;
            case 'satellites':
                this.iconPath = new vscode.ThemeIcon('remote-explorer');
                break;
        }
    }
}
// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
class CorpusTreeProvider {
    workspaceRoot;
    _onDidChange = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChange.event;
    statePath;
    state = null;
    loadError = null;
    constructor(workspaceRoot) {
        this.workspaceRoot = workspaceRoot;
        this.statePath = path.join(workspaceRoot, 'manifest', 'corpus-state.json');
        this.load();
    }
    refresh() {
        this.load();
        this._onDidChange.fire(undefined);
    }
    load() {
        try {
            if (!fs.existsSync(this.statePath)) {
                this.state = null;
                this.loadError = `corpus-state.json not found at ${this.statePath}`;
                return;
            }
            this.state = JSON.parse(fs.readFileSync(this.statePath, 'utf8'));
            this.loadError = null;
        }
        catch (e) {
            this.state = null;
            this.loadError = String(e);
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return this.getRoots();
        }
        if (element instanceof SectionItem) {
            return this.getSectionChildren(element.sectionId);
        }
        return [];
    }
    getRoots() {
        if (this.loadError || !this.state) {
            const err = new CorpusItem('corpus-state.json not found', vscode.TreeItemCollapsibleState.None, 'error', { icon: 'warning', description: 'Run vampire:drain to initialize' });
            return [err];
        }
        const state = this.state;
        const gateTotal = Object.keys(state.gate_ladder ?? {}).length;
        const gatesPassed = Object.values(state.gate_ladder ?? {}).filter(Boolean).length;
        return [
            new SectionItem('Corpus', 'corpus', `v${state.schema_version} · ${state.sessions ?? 0} sessions`),
            new SectionItem('Gate Ladder', 'gates', `${gatesPassed}/${gateTotal} admitted`),
            new SectionItem('Satellites', 'satellites', `${state.satellites?.length ?? 0} registered`),
        ];
    }
    getSectionChildren(section) {
        if (!this.state)
            return [];
        switch (section) {
            case 'corpus': return this.getCorpusStats();
            case 'gates': return this.getGates();
            case 'satellites': return this.getSatellites();
        }
    }
    getCorpusStats() {
        const s = this.state;
        const items = [];
        const addStat = (label, value, icon) => {
            const item = new CorpusItem(label, vscode.TreeItemCollapsibleState.None, 'corpus.stat', { description: String(value ?? '—'), icon });
            items.push(item);
        };
        addStat('Sessions', s.sessions, 'history');
        addStat('Entities', s.entities, 'symbol-class');
        addStat('Occurrences', s.entity_occurrences, 'references');
        addStat('Vectors', s.vec_count, 'symbol-number');
        addStat('Vec model', s.vec_model, 'hubot');
        addStat('Vec dims', s.vec_dims, 'symbol-numeric');
        addStat('Schema', s.schema_version, 'versions');
        if (s.ingest_ts) {
            const dt = new Date(s.ingest_ts);
            const ago = formatRelative(dt);
            addStat('Last ingest', ago, 'clock');
        }
        // Corpus file size
        const corpusPath = path.join(this.workspaceRoot, 'manifest', 'corpus.sqlite');
        try {
            const stat = fs.statSync(corpusPath);
            addStat('corpus.sqlite', formatBytes(stat.size), 'database');
        }
        catch {
            addStat('corpus.sqlite', 'not found', 'database');
        }
        return items;
    }
    getGates() {
        const gates = this.state?.gate_ladder ?? {};
        if (Object.keys(gates).length === 0) {
            return [new CorpusItem('No gates recorded', vscode.TreeItemCollapsibleState.None, 'gate.unknown', { icon: 'circle-outline' })];
        }
        const gateOrder = ['G0', 'G1a', 'G1b', 'G2', 'G5', 'G6', 'G7', 'G8a', 'G8b', 'G8c', 'G9'];
        const knownGates = new Set(gateOrder);
        const allGates = [...gateOrder.filter(g => g in gates), ...Object.keys(gates).filter(g => !knownGates.has(g))];
        return allGates.map(key => {
            const admitted = gates[key];
            const kind = admitted ? 'gate.admitted' : 'gate.failed';
            const icon = admitted ? 'pass-filled' : 'circle-outline';
            const desc = admitted ? 'admitted' : 'pending';
            return new CorpusItem(key, vscode.TreeItemCollapsibleState.None, kind, {
                icon,
                description: desc,
                tooltip: `Gate ${key}: ${desc}`,
            });
        });
    }
    getSatellites() {
        const satellitePaths = this.state?.satellites ?? [];
        if (satellitePaths.length === 0) {
            return [new CorpusItem('No satellites registered', vscode.TreeItemCollapsibleState.None, 'satellite.missing', { icon: 'remote' })];
        }
        return satellitePaths.map(relPath => {
            const fullPath = path.join(this.workspaceRoot, relPath);
            try {
                const sat = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
                const drainPath = sat.drain_format?.path
                    ? path.join(this.workspaceRoot, sat.drain_format.path)
                    : null;
                const drainExists = drainPath ? fs.existsSync(drainPath) : false;
                const id = sat.satellite_id ?? path.basename(path.dirname(relPath));
                const tables = (sat.tables ?? []).length;
                const desc = drainExists ? `${tables} tables · drain ✓` : `${tables} tables · drain missing`;
                return new CorpusItem(id, vscode.TreeItemCollapsibleState.None, 'satellite.active', {
                    icon: drainExists ? 'pass-filled' : 'warning',
                    description: desc,
                    tooltip: `${id} v${sat.version ?? '?'}\n${sat.description ?? ''}\nDrain: ${drainPath ?? 'none'}`,
                });
            }
            catch {
                const id = path.basename(path.dirname(relPath));
                return new CorpusItem(id, vscode.TreeItemCollapsibleState.None, 'satellite.missing', {
                    icon: 'error',
                    description: 'satellite.json unreadable',
                });
            }
        });
    }
}
exports.CorpusTreeProvider = CorpusTreeProvider;
// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function formatBytes(bytes) {
    if (bytes < 1024)
        return `${bytes} B`;
    if (bytes < 1024 * 1024)
        return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
function formatRelative(date) {
    const diffMs = Date.now() - date.getTime();
    const mins = Math.floor(diffMs / 60_000);
    if (mins < 1)
        return 'just now';
    if (mins < 60)
        return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24)
        return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}
//# sourceMappingURL=CorpusTreeProvider.js.map