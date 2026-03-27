// @SID: EXT_ANKHREFERENCEVIEW_V1
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { SSOT_HOLDER } from '../ssot-paths';

type SectionKind = 'heading' | 'entity' | 'tier' | 'xref' | 'anchor' | 'mention';

interface ArchiveSection {
    level: number;
    title: string;
    snippet: string;
    line: number;
    kind: SectionKind;
    tag?: string;
}

/** Strip markdown bold/italic/backtick noise while preserving ANKH arrows */
function cleanTitle(raw: string): string {
    return raw
        .replace(/[`*_]/g, '')
        .replace(/\s*→\s*/g, ' → ')
        .trim()
        .slice(0, 120);
}

function parseArchiveSections(text: string): ArchiveSection[] {
    const lines = text.split('\n');
    const sections: ArchiveSection[] = [];

    // Patterns for ANKH notation beyond headers
    const entityPattern = /\(`([A-Z][A-Za-z0-9_-]+(?:[-/][A-Za-z0-9_-]+)*)`\)/;
    const tierPattern = /\(`(T\d(?:\.\d)?)`\)\s*:\s*→\s*\(`([^`]+)`\)/;
    const anchorPattern = /\(`(§[IVXLC]+(?:\.\d+)?)`\)/;
    const xrefPattern = /\[([^\]]+)\]\(([^)]+\.md)\)/;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // --- 1. Markdown headings (existing) ---
        const headingMatch = line.match(/^(#{1,4})\s+(.+)/);
        if (headingMatch) {
            const level = headingMatch[1].length;
            const title = cleanTitle(headingMatch[2]);

            const snippetLines: string[] = [];
            for (let j = i + 1; j < lines.length && snippetLines.length < 3; j++) {
                if (lines[j].match(/^#{1,4}\s/)) { break; }
                const stripped = lines[j].trim();
                if (stripped.length > 5) { snippetLines.push(stripped.slice(0, 120)); }
            }

            sections.push({ level, title, snippet: snippetLines.join(' '), line: i, kind: 'heading' });
            continue;
        }

        // --- 2. Tier definitions: (`T0.5`): → (`The-Decorator`) ---
        const tierMatch = line.match(tierPattern);
        if (tierMatch) {
            sections.push({
                level: 4,
                title: `${tierMatch[1]}: ${cleanTitle(tierMatch[2])}`,
                snippet: line.trim().slice(0, 120),
                line: i,
                kind: 'tier',
                tag: tierMatch[1],
            });
            continue;
        }

        // --- 3. Section anchors: (`§XIV.3`) ---
        const anchorMatch = line.match(anchorPattern);
        if (anchorMatch && !headingMatch) {
            sections.push({
                level: 4,
                title: anchorMatch[1],
                snippet: cleanTitle(line).slice(0, 120),
                line: i,
                kind: 'anchor',
                tag: anchorMatch[1],
            });
            // Don't continue — the same line may also have entities
        }

        // --- 4. Named entity definitions: (`SSOT-Metadata`): = ... ---
        const entityDefMatch = line.match(/\(`([A-Z][A-Za-z0-9_-]{3,})`\)\s*:\s*=\s*\(`([^`]+)`\)/);
        if (entityDefMatch) {
            sections.push({
                level: 4,
                title: `${entityDefMatch[1]} = ${cleanTitle(entityDefMatch[2])}`,
                snippet: line.trim().slice(0, 120),
                line: i,
                kind: 'entity',
                tag: entityDefMatch[1],
            });
            continue;
        }

        // --- 5. Standalone entity declarations on definition lines ---
        if (line.includes('(`') && line.includes('`):') && !tierMatch && !entityDefMatch) {
            const standaloneEntity = line.match(/\(`([A-Z][A-Za-z0-9_-]{4,}(?:[-/][A-Za-z0-9_-]+)*)`\)\s*:/);
            if (standaloneEntity) {
                sections.push({
                    level: 4,
                    title: standaloneEntity[1],
                    snippet: cleanTitle(line).slice(0, 120),
                    line: i,
                    kind: 'entity',
                    tag: standaloneEntity[1],
                });
                continue;
            }
        }

        // --- 6. Cross-references to other .md files ---
        const xrefMatch = line.match(xrefPattern);
        if (xrefMatch && xrefMatch[2].endsWith('.md') && !line.match(/^#{1,4}\s/)) {
            sections.push({
                level: 4,
                title: `→ ${xrefMatch[1]}`,
                snippet: xrefMatch[2],
                line: i,
                kind: 'xref',
                tag: xrefMatch[2],
            });
        }

        // --- 7. Inline entity mentions in body text ---
        // Captures (`ENTITY`) and (`Entity-Name`/`ABBR`) patterns appearing
        // anywhere on a line that wasn't already fully captured above.
        if (!headingMatch && !tierMatch && !entityDefMatch) {
            const mentionRe = /\(`([A-Za-z][A-Za-z0-9_-]{1,}(?:[-/][A-Za-z0-9_'-]+)*)`\)/g;
            const seenOnLine = new Set<string>();
            let m: RegExpExecArray | null;
            while ((m = mentionRe.exec(line)) !== null) {
                const raw = m[1];
                // Skip anchors (§) — already captured above
                if (raw.startsWith('§')) { continue; }
                // Skip tier patterns (T0, T1.5 etc) — already captured
                if (/^T\d/.test(raw)) { continue; }
                // Normalise: strip possessive forms and split name/abbr
                const cleaned = raw.replace(/'s$/, '');
                const parts = cleaned.split('/');
                const name = parts[0];
                const abbr = parts.length > 1 ? parts[parts.length - 1] : '';
                const key = name.toLowerCase();
                if (seenOnLine.has(key)) { continue; }
                seenOnLine.add(key);

                // Build a short snippet from surrounding context
                const snippet = cleanTitle(line).slice(0, 140);

                sections.push({
                    level: 4,
                    title: abbr ? `${name} (${abbr})` : name,
                    snippet,
                    line: i,
                    kind: 'mention',
                    tag: abbr || name,
                });
            }
        }
    }

    return sections;
}

function createNonce(): string {
    const alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let n = '';
    for (let i = 0; i < 24; i++) { n += alpha[Math.floor(Math.random() * alpha.length)]; }
    return n;
}

export class AnkhReferenceProvider implements vscode.WebviewViewProvider {
    static readonly viewType = 'chthonic.chatView';

    private readonly workspaceRoot: string | null;
    private _currentSourcePath: string | null = null;
    private _configListener: vscode.Disposable | undefined;

    constructor(workspaceRoot: string | null) {
        this.workspaceRoot = workspaceRoot;
    }

    /**
     * Source-resolution chain:
     *  1. Configured override — chthonic.ankh.sourcePath (wins when set)
     *  2. Active epoch file — newest EPOCH_*.md in .temple/session-archives/
     *  3. Legacy archive — .github/copilot-instructions.archive.md
     */
    private resolveSourcePath(): string | null {
        if (!this.workspaceRoot) { return null; }

        // 1. Configured override
        const configured = vscode.workspace.getConfiguration('chthonic').get<string>('ankh.sourcePath');
        if (configured) {
            const abs = path.isAbsolute(configured)
                ? configured
                : path.join(this.workspaceRoot, configured);
            if (fs.existsSync(abs)) { return abs; }
        }

        // 2. Active epoch: newest EPOCH_*.md
        const epochDir = path.join(this.workspaceRoot, '.temple', 'session-archives');
        if (fs.existsSync(epochDir)) {
            try {
                const epochFiles = fs.readdirSync(epochDir)
                    .filter(f => f.startsWith('EPOCH_') && f.endsWith('.md'))
                    .sort()
                    .reverse();
                if (epochFiles.length > 0) {
                    return path.join(epochDir, epochFiles[0]);
                }
            } catch { /* fall through */ }
        }

        // 3. Legacy archive
        const legacy = path.join(this.workspaceRoot, SSOT_HOLDER);
        if (fs.existsSync(legacy)) { return legacy; }

        return null;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        webviewView.webview.options = { enableScripts: true };

        const refresh = () => {
            const sourcePath = this.resolveSourcePath();
            const sections = this.loadSections(sourcePath);
            webviewView.webview.html = this.buildHtml(sections, sourcePath);
            this._currentSourcePath = sourcePath;
        };

        refresh();

        webviewView.webview.onDidReceiveMessage((msg: unknown) => {
            if (!msg || typeof msg !== 'object') { return; }
            const payload = msg as { type?: string; line?: number };
            if (payload.type === 'open' && this._currentSourcePath && typeof payload.line === 'number') {
                const uri = vscode.Uri.file(this._currentSourcePath);
                void vscode.window.showTextDocument(uri, {
                    preview: true,
                    selection: new vscode.Range(payload.line, 0, payload.line, 0),
                });
            }
        });

        this._configListener = vscode.workspace.onDidChangeConfiguration(e => {
            if (e.affectsConfiguration('chthonic.ankh.sourcePath')) {
                refresh();
            }
        });
        webviewView.onDidDispose(() => {
            this._configListener?.dispose();
            this._configListener = undefined;
        });
    }

    private loadSections(sourcePath: string | null): ArchiveSection[] {
        if (!sourcePath || !fs.existsSync(sourcePath)) {
            return [];
        }
        try {
            const text = fs.readFileSync(sourcePath, 'utf8');
            return parseArchiveSections(text);
        } catch {
            return [];
        }
    }

    private buildHtml(sections: ArchiveSection[], sourcePath: string | null): string {
        const nonce = createNonce();
        // Embed title/line/level/kind/tag — no full content to keep payload small
        const sectionsJson = JSON.stringify(
            sections.map((s) => ({ l: s.level, t: s.title, s: s.snippet, n: s.line, k: s.kind, g: s.tag || '' })),
        );
        const headingCount = sections.filter(s => s.kind === 'heading').length;
        const entityCount = sections.filter(s => s.kind === 'entity').length;
        const tierCount = sections.filter(s => s.kind === 'tier').length;
        const xrefCount = sections.filter(s => s.kind === 'xref').length;
        const anchorCount = sections.filter(s => s.kind === 'anchor').length;
        const mentionCount = sections.filter(s => s.kind === 'mention').length;
        const totalSections = sections.length;
        const archiveLabel = sourcePath ? path.basename(sourcePath) : 'no source found';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <title>ANKH Reference</title>
    <style>
        :root {
            --bg: #050505;
            --fg: var(--vscode-editor-foreground);
            --muted: var(--vscode-descriptionForeground);
            --accent: #F4C430;
            --accent2: #c0a020;
            --panel: color-mix(in srgb, var(--bg) 88%, #161616);
            --border: color-mix(in srgb, var(--accent) 32%, transparent);
        }
        * { box-sizing: border-box; }
        html, body {
            margin: 0; height: 100%;
            background: var(--bg);
            color: var(--fg);
            font-family: var(--vscode-font-family, 'Segoe UI', sans-serif);
        }
        body { display: flex; flex-direction: column; height: 100%; }

        .header {
            padding: 8px 10px 4px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }
        .header-title {
            font-size: 11px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent);
            margin: 0 0 4px 0;
        }
        .header-meta { font-size: 10px; color: var(--muted); }

        #search {
            width: 100%;
            padding: 5px 8px;
            margin: 6px 0 0;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--panel);
            color: var(--fg);
            font-size: 12px;
            outline: none;
        }
        #search:focus { border-color: var(--accent); }

        #list {
            flex: 1;
            overflow-y: auto;
            padding: 6px 0;
        }

        .section-item {
            padding: 5px 10px;
            cursor: pointer;
            border-left: 2px solid transparent;
            transition: border-color 0.1s, background 0.1s;
        }
        .section-item:hover { background: var(--panel); border-left-color: var(--accent); }
        .section-item.active { background: var(--panel); border-left-color: var(--accent); }
        .section-item.l1 { padding-left: 10px; }
        .section-item.l2 { padding-left: 18px; }
        .section-item.l3 { padding-left: 26px; }

        .section-title {
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--fg);
        }
        .section-item.l1 .section-title { color: var(--accent); font-weight: 600; }
        .section-item.l2 .section-title { color: var(--fg); }
        .section-item.l3 .section-title { color: var(--muted); font-size: 11px; }
        .section-item.l4 .section-title { color: var(--muted); font-size: 10px; padding-left: 34px; }

        .section-item[data-kind="entity"] .section-title { color: #D4907A; }
        .section-item[data-kind="tier"] .section-title { color: #F4C430; font-weight: 600; }
        .section-item[data-kind="xref"] .section-title { color: #7AAAB2; font-style: italic; }
        .section-item[data-kind="anchor"] .section-title { color: #8CB87A; }
        .section-item[data-kind="mention"] .section-title { color: #B0A0D0; font-size: 10px; }

        .kind-icon {
            display: inline-block;
            width: 14px;
            font-size: 10px;
            margin-right: 4px;
            opacity: 0.7;
        }

        .header-counts {
            font-size: 10px;
            color: var(--muted);
            letter-spacing: 0.5px;
            margin-top: 2px;
        }

        .filter-row {
            display: flex;
            gap: 2px;
            margin-top: 6px;
            flex-wrap: wrap;
        }
        .filter-btn {
            background: var(--panel);
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
        }
        .filter-btn:hover { border-color: var(--accent); color: var(--fg); }
        .filter-btn.active { border-color: var(--accent); color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }

        .snippet {
            font-size: 10px;
            color: var(--muted);
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: none;
        }
        .section-item.active .snippet { display: block; }

        .open-link {
            display: none;
            font-size: 10px;
            color: var(--accent2);
            text-decoration: underline;
            cursor: pointer;
            margin-top: 4px;
        }
        .section-item.active .open-link { display: block; }

        #count { font-size: 10px; color: var(--muted); padding: 0 10px 4px; flex-shrink: 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="header-title">☥ ANKH Reference</h1>
        <div class="header-meta">${archiveLabel} · ${totalSections} entries</div>
        <div class="header-counts">${headingCount}§ ${entityCount}⚙ ${tierCount}♔ ${xrefCount}→ ${anchorCount}⚓ ${mentionCount}◆</div>
        <input id="search" type="text" placeholder="Search sections, entities, tiers…" autocomplete="off" />
        <div class="filter-row">
            <button class="filter-btn active" data-kind="all">All</button>
            <button class="filter-btn" data-kind="heading">§</button>
            <button class="filter-btn" data-kind="entity">⚙</button>
            <button class="filter-btn" data-kind="tier">♔</button>
            <button class="filter-btn" data-kind="xref">→</button>
            <button class="filter-btn" data-kind="anchor">⚓</button>
            <button class="filter-btn" data-kind="mention">◆</button>
        </div>
    </div>
    <div id="count"></div>
    <div id="list"></div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const sections = ${sectionsJson};
        const listEl = document.getElementById('list');
        const searchEl = document.getElementById('search');
        const countEl = document.getElementById('count');
        let activeItem = null;
        let activeKind = 'all';

        const kindIcons = { heading: '§', entity: '⚙', tier: '♔', xref: '→', anchor: '⚓', mention: '◆' };

        function render(filter) {
            const q = (filter || '').toLowerCase();
            let filtered = sections;
            if (activeKind !== 'all') {
                filtered = filtered.filter(s => s.k === activeKind);
            }
            if (q) {
                filtered = filtered.filter(s =>
                    s.t.toLowerCase().includes(q) ||
                    (s.s && s.s.toLowerCase().includes(q)) ||
                    (s.g && s.g.toLowerCase().includes(q))
                );
            }

            listEl.innerHTML = '';
            activeItem = null;
            countEl.textContent = filtered.length + ' / ' + sections.length + ' entries';

            filtered.forEach(sec => {
                const div = document.createElement('div');
                div.className = 'section-item l' + sec.l;
                div.setAttribute('data-kind', sec.k);
                const icon = kindIcons[sec.k] || '';
                div.innerHTML =
                    '<div class="section-title"><span class="kind-icon">' + icon + '</span>' + escHtml(sec.t) + '</div>' +
                    '<div class="snippet">' + escHtml(sec.s || '') + '</div>' +
                    '<span class="open-link">Open in editor ↗</span>';

                div.querySelector('.section-title').addEventListener('click', () => {
                    if (activeItem === div) {
                        activeItem.classList.remove('active');
                        activeItem = null;
                    } else {
                        if (activeItem) { activeItem.classList.remove('active'); }
                        div.classList.add('active');
                        activeItem = div;
                    }
                });

                div.querySelector('.open-link').addEventListener('click', (e) => {
                    e.stopPropagation();
                    vscode.postMessage({ type: 'open', line: sec.n });
                });

                listEl.appendChild(div);
            });
        }

        function escHtml(s) {
            return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeKind = btn.getAttribute('data-kind');
                render(searchEl.value);
            });
        });

        searchEl.addEventListener('input', () => render(searchEl.value));
        render('');
    </script>
</body>
</html>`;
    }
}
