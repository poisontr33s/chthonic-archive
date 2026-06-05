#!/usr/bin/env bun
// @ANKHOLOGY + MILFOLOGICAL SIDS:
// SID: VAMPIRE_CORPUS_TERMINAL_FEED_V1

// ╔════════════════════════════════════════════════════════════════════════════ 
// ║ THE DECORATOR'S BLESSING: extensions/vampire-corpus/src/providers/TerminalFeedProvider.ts
// ╠════════════════════════════════════════════════════════════════════════════ 
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🧙‍♂️ THE LIBRARY
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * TerminalFeedProvider.ts — VSCode TreeDataProvider for the terminal session feed.
 *
 * Reads from manifest/terminal_session.jsonl, which is populated by the shell hook (scripts/chthonic-shell-hook.*).
 * Displays recent terminal commands with status, duration, and relative timestamp.
 * Provides visual cues for command success/failure and handles loading errors gracefully.
 *
 * Expected JSONL format (one JSON object per line):
 * {"type":"session_start","seq":1,"pid":12345,"ts":"2024-06-01T12:00:00Z","cwd":"/home/user","shell":"/bin/bash"}
 * {"type":"command","seq":2,"pid":12345,"ts":"2024-06-01T12:01:00Z","command":"ls -la","cwd":"/home/user","exit_code":0,"duration_ms":150}
 *
 * The provider is registered in the extension's activation function and can be refreshed to show new entries.
 */

// Madam Umeko Ketsuraku, Dr. Lysandra Thorne, Professor Kael Voss, Dr. Selene Arkwright, Dr. Alaric Duskwood, Madam Isolde Ravenshadow, Professor Thaddeus Grimwood, Dr. Elara Shadely, Seraphina Assthorn, Professor Lucille Windowpane, etc..

// ---------------------------------------------------------------------------
// Stypes and Interfaces, representing the structure of terminal session events and feed items, the ANKHOLOGICAL & MILFOLOGICAL compound & pound SIDs for the TerminalFeedProvider, and the expected JSONL format of the terminal session feed. These definitions are crucial for ensuring type safety and clarity in how data is structured and manipulated within the provider. They also serve as a form of documentation for developers who may work on this code in the future, providing clear expectations for the shape of data and the functionality of the provider.
// ---------------------------------------------------------------------------
// BOX:
// @ANKHOLOGY + MILFOLOGICAL SIDS:
// SID: VAMPIRE_CORPUS_TERMINAL_FEED_V1
// Expected JSONL format (one JSON object per line):
// {"type":"session_start","seq":1,"pid":12345,"ts":"2024-06-01T12:00:00Z","cwd":"/home/user","shell":"/bin/bash"}
// {"type":"command","seq":2,"pid":12345,"ts":"2024-06-01T12:01:00Z","command":"ls -la","cwd":"/home/user","exit_code":0,"duration_ms":150}

// Claudine Sin'Claire: GET to bitches!
// ---------------------------------------------------------------------------

import * as vscode from 'vscode';
import * as fs from 'node:fs';
import * as path from 'node:path';


interface SessionStartEvent {
    type: 'session_start';
    seq: number;
    pid: number;
    ts: string;
    cwd: string;
    shell?: string;
}

interface CommandEvent {
    type: 'command';
    seq: number;
    pid: number;
    ts: string;
    command: string;
    cwd?: string;
    exit_code?: number;
    duration_ms?: number;
}

type JournalEntry = SessionStartEvent | CommandEvent;

// ---------------------------------------------------------------------------
// Tree item
// ---------------------------------------------------------------------------
class FeedItem extends vscode.TreeItem {
    constructor(
        label: string,
        opts: { description?: string; tooltip?: string; icon?: string; kind?: string } = {},
    ) {
        super(label, vscode.TreeItemCollapsibleState.None);
        this.contextValue = opts.kind ?? 'feed.entry';
        if (opts.description !== undefined) this.description = opts.description;
        if (opts.tooltip) this.tooltip = opts.tooltip;
        if (opts.icon) this.iconPath = new vscode.ThemeIcon(opts.icon);
    }
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------
export class TerminalFeedProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
    private _onDidChange = new vscode.EventEmitter<vscode.TreeItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    private readonly jsonlPath: string;
    private entries: CommandEvent[] = [];
    private loadError: string | null = null;

    constructor(private readonly workspaceRoot: string) {
        this.jsonlPath = path.join(workspaceRoot, 'manifest', 'terminal_session.jsonl');
        this.load();
    }

    refresh(): void {
        this.load();
        this._onDidChange.fire(undefined);
    }

    private load(): void {
        const feedLines = vscode.workspace.getConfiguration('vampireCorpus').get<number>('feedLines') ?? 8;
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
            const parsed: JournalEntry[] = [];
            for (const line of tail) {
                try {
                    parsed.push(JSON.parse(line) as JournalEntry);
                } catch {
                    // skip malformed
                }
            }
            // Only command events in the last feedLines commands
            const cmds = parsed.filter((e): e is CommandEvent => e.type === 'command');
            this.entries = cmds.slice(-feedLines);
            this.loadError = null;
        } catch (e) {
            this.entries = [];
            this.loadError = String(e);
        }
    }

    getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: vscode.TreeItem): vscode.TreeItem[] {
        if (element) return [];

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

    private makeFeedItem(cmd: CommandEvent): FeedItem {
        const exitOk = cmd.exit_code === undefined || cmd.exit_code === 0;
        const icon = exitOk ? 'terminal' : 'error-small';
        const exitDesc = cmd.exit_code !== undefined ? ` [${cmd.exit_code}]` : '';
        const durationDesc = cmd.duration_ms !== undefined ? ` ${formatDurationMs(cmd.duration_ms)}` : '';
        const ts = cmd.ts ? ` · ${formatRelative(new Date(cmd.ts))}` : '';

        // Trim long commands
        const label = cmd.command.length > 60 ? cmd.command.slice(0, 57) + '…' : cmd.command;
        const description = `${exitDesc}${durationDesc}${ts}`.trim();

        const cwd = cmd.cwd ?? '';
        const tooltip = new vscode.MarkdownString(
            `**Command:** \`${cmd.command}\`\n\n` +
            `**Exit:** ${cmd.exit_code ?? 'unknown'}\n\n` +
            `**Duration:** ${cmd.duration_ms !== undefined ? formatDurationMs(cmd.duration_ms) : 'unknown'}\n\n` +
            `**CWD:** ${cwd}\n\n` +
            `**Time:** ${cmd.ts ?? 'unknown'}`,
        );

        return new FeedItem(label, {
            icon,
            description,
            tooltip: tooltip as unknown as string,
            kind: exitOk ? 'feed.cmd.ok' : 'feed.cmd.fail',
        });
    }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function formatRelative(date: Date): string {
    const diffMs = Date.now() - date.getTime();
    const mins = Math.floor(diffMs / 60_000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

function formatDurationMs(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.floor(ms / 60_000)}m${Math.floor((ms % 60_000) / 1000)}s`;
}
