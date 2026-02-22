import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

interface ArchiveSection {
    level: number;
    title: string;
    snippet: string;
    line: number;
}

function parseArchiveSections(text: string): ArchiveSection[] {
    const lines = text.split('\n');
    const sections: ArchiveSection[] = [];

    for (let i = 0; i < lines.length; i++) {
        const match = lines[i].match(/^(#{1,3})\s+(.+)/);
        if (!match) { continue; }

        const level = match[1].length;
        // Clean up the title: strip backticks, bold markers, and ANKH notation cruft
        let title = match[2]
            .replace(/[`*_]/g, '')
            .replace(/\s*→\s*/g, ' → ')
            .trim()
            .slice(0, 100);

        // Collect up to 3 non-empty content lines as snippet
        const snippetLines: string[] = [];
        for (let j = i + 1; j < lines.length && snippetLines.length < 3; j++) {
            if (lines[j].match(/^#{1,3}\s/)) { break; }
            const stripped = lines[j].trim();
            if (stripped.length > 5) { snippetLines.push(stripped.slice(0, 120)); }
        }

        sections.push({ level, title, snippet: snippetLines.join(' '), line: i });
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

    private readonly archivePath: string | null;

    constructor(workspaceRoot: string | null) {
        this.archivePath = workspaceRoot
            ? path.join(workspaceRoot, '.github', 'copilot-instructions.archive.md')
            : null;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        webviewView.webview.options = { enableScripts: true };

        const sections = this.loadSections();
        webviewView.webview.html = this.buildHtml(sections);

        webviewView.webview.onDidReceiveMessage((msg: unknown) => {
            if (!msg || typeof msg !== 'object') { return; }
            const payload = msg as { type?: string; line?: number };
            if (payload.type === 'open' && this.archivePath && typeof payload.line === 'number') {
                const uri = vscode.Uri.file(this.archivePath);
                void vscode.window.showTextDocument(uri, {
                    preview: true,
                    selection: new vscode.Range(payload.line, 0, payload.line, 0),
                });
            }
        });
    }

    private loadSections(): ArchiveSection[] {
        if (!this.archivePath || !fs.existsSync(this.archivePath)) {
            return [];
        }
        try {
            const text = fs.readFileSync(this.archivePath, 'utf8');
            return parseArchiveSections(text);
        } catch {
            return [];
        }
    }

    private buildHtml(sections: ArchiveSection[]): string {
        const nonce = createNonce();
        // Embed only title/line/level — no full content to keep payload small
        const sectionsJson = JSON.stringify(
            sections.map((s) => ({ l: s.level, t: s.title, s: s.snippet, n: s.line })),
        );
        const totalSections = sections.length;
        const archiveLabel = this.archivePath ? path.basename(this.archivePath) : 'archive not found';

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
        <div class="header-meta">${archiveLabel} · ${totalSections} sections</div>
        <input id="search" type="text" placeholder="Search sections…" autocomplete="off" />
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

        function render(filter) {
            const q = (filter || '').toLowerCase();
            const filtered = q
                ? sections.filter(s => s.t.toLowerCase().includes(q) || (s.s && s.s.toLowerCase().includes(q)))
                : sections;

            listEl.innerHTML = '';
            countEl.textContent = filtered.length + ' / ' + sections.length + ' sections';

            filtered.forEach(sec => {
                const div = document.createElement('div');
                div.className = 'section-item l' + sec.l;
                div.innerHTML =
                    '<div class="section-title">' + escHtml(sec.t) + '</div>' +
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

        searchEl.addEventListener('input', () => render(searchEl.value));
        render('');
    </script>
</body>
</html>`;
    }
}
