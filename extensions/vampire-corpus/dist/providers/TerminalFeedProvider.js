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
exports.TerminalFeedProvider = void 0;
// @SID: VAMPIRE_CORPUS_TERMINAL_FEED_V1
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("node:fs"));
const path = __importStar(require("node:path"));
// ---------------------------------------------------------------------------
// Tree item
// ---------------------------------------------------------------------------
class FeedItem extends vscode.TreeItem {
    constructor(label, opts = {}) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.contextValue = opts.kind ?? 'feed.entry';
        if (opts.description !== undefined)
            this.description = opts.description;
        if (opts.tooltip)
            this.tooltip = opts.tooltip;
        if (opts.icon)
            this.iconPath = new vscode.ThemeIcon(opts.icon);
    }
}
// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
class TerminalFeedProvider {
    workspaceRoot;
    _onDidChange = new vscode.EventEmitter();
    onDidChangeTreeData = this._onDidChange.event;
    jsonlPath;
    entries = [];
    loadError = null;
    constructor(workspaceRoot) {
        this.workspaceRoot = workspaceRoot;
        this.jsonlPath = path.join(workspaceRoot, 'manifest', 'terminal_session.jsonl');
        this.load();
    }
    refresh() {
        this.load();
        this._onDidChange.fire(undefined);
    }
    load() {
        const feedLines = vscode.workspace.getConfiguration('vampireCorpus').get('feedLines') ?? 8;
        try {
            if (!fs.existsSync(this.jsonlPath)) {
                this.entries = [];
                this.loadError = null;
                return;
            }
            const raw = fs.readFileSync(this.jsonlPath, 'utf8');
            const lines = raw.split('\n').filter(l => l.trim().length > 0);
            // Take last N lines
            const tail = lines.slice(-Math.max(feedLines * 3, 30));
            const parsed = [];
            for (const line of tail) {
                try {
                    parsed.push(JSON.parse(line));
                }
                catch {
                    // skip malformed
                }
            }
            // Only command events in the last feedLines commands
            const cmds = parsed.filter((e) => e.type === 'command');
            this.entries = cmds.slice(-feedLines);
            this.loadError = null;
        }
        catch (e) {
            this.entries = [];
            this.loadError = String(e);
        }
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element)
            return [];
        if (this.loadError) {
            return [new FeedItem('Error reading terminal feed', { icon: 'warning', description: this.loadError, kind: 'feed.error' })];
        }
        if (!fs.existsSync(this.jsonlPath)) {
            return [
                new FeedItem('terminal_session.jsonl not found', {
                    icon: 'circle-outline',
                    description: 'Source shell hook with: . scripts/chthonic-shell-hook.ps1',
                    kind: 'feed.empty',
                }),
            ];
        }
        if (this.entries.length === 0) {
            return [new FeedItem('No commands recorded yet', { icon: 'circle-outline', kind: 'feed.empty' })];
        }
        return this.entries.map(cmd => this.makeFeedItem(cmd));
    }
    makeFeedItem(cmd) {
        const exitOk = cmd.exit_code === undefined || cmd.exit_code === 0;
        const icon = exitOk ? 'terminal' : 'error-small';
        const exitDesc = cmd.exit_code !== undefined ? ` [${cmd.exit_code}]` : '';
        const durationDesc = cmd.duration_ms !== undefined ? ` ${formatDurationMs(cmd.duration_ms)}` : '';
        const ts = cmd.ts ? ` · ${formatRelative(new Date(cmd.ts))}` : '';
        // Trim long commands
        const label = cmd.command.length > 60 ? cmd.command.slice(0, 57) + '…' : cmd.command;
        const description = `${exitDesc}${durationDesc}${ts}`.trim();
        const cwd = cmd.cwd ?? '';
        const tooltip = new vscode.MarkdownString(`**Command:** \`${cmd.command}\`\n\n` +
            `**Exit:** ${cmd.exit_code ?? 'unknown'}\n\n` +
            `**Duration:** ${cmd.duration_ms !== undefined ? formatDurationMs(cmd.duration_ms) : 'unknown'}\n\n` +
            `**CWD:** ${cwd}\n\n` +
            `**Time:** ${cmd.ts ?? 'unknown'}`);
        return new FeedItem(label, {
            icon,
            description,
            tooltip: tooltip,
            kind: exitOk ? 'feed.cmd.ok' : 'feed.cmd.fail',
        });
    }
}
exports.TerminalFeedProvider = TerminalFeedProvider;
// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
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
    return `${Math.floor(hours / 24)}d ago`;
}
function formatDurationMs(ms) {
    if (ms < 1000)
        return `${ms}ms`;
    if (ms < 60_000)
        return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.floor(ms / 60_000)}m${Math.floor((ms % 60_000) / 1000)}s`;
}
//# sourceMappingURL=TerminalFeedProvider.js.map