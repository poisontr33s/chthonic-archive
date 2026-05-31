// @SID: EXT_ANKHREFERENCEVIEW_V1
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { jsonForInlineScript, loadWebviewHtml } from '../runtime/webviewLoader';
import { trackWebview } from '../runtime/webviewHmrWatcher';
import { SSOT_CANON, SSOT_HOLDER } from '../ssot-paths';

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

export class AnkhReferenceProvider implements vscode.WebviewViewProvider {
    static readonly viewType = 'chthonic.chatView';

    private readonly workspaceRoot: string | null;
    private readonly extensionUri: vscode.Uri;
    private _currentSourcePath: string | null = null;
    private _configListener: vscode.Disposable | undefined;

    constructor(workspaceRoot: string | null, extensionUri: vscode.Uri = resolveExtensionUri()) {
        this.workspaceRoot = workspaceRoot;
        this.extensionUri = extensionUri;
    }

    /**
     * Source-resolution chain (re-rooted 2026-05-31 — the ANKH Reference
     * surfaces the GENERATIVE CANON, not ephemeral session logs):
     *  1. Configured override — chthonic.ankh.sourcePath (explicit opt-in; this
     *     is how an epoch log or any other lens is reached, by choice).
     *  2. SSOT canon — .chthonic/SSOT.md, the artifact every active instruction
     *     file derives from. This is the default; the Ankhology IS the SSOT.
     *  3. SSOT mirror — .github/copilot-instructions.archive.md, only if the
     *     canon is absent.
     *
     * Prior regression: the newest EPOCH_*.md was ranked ABOVE the SSOT, so the
     * panel surfaced a 10-day session log while the canon sat last as "legacy."
     * Epoch logs are now reachable only via the configured override.
     */
    private resolveSourcePath(): string | null {
        if (!this.workspaceRoot) { return null; }

        // 1. Configured override (explicit opt-in — e.g. point at an epoch lens)
        const configured = vscode.workspace.getConfiguration('chthonic').get<string>('ankh.sourcePath');
        if (configured) {
            const abs = path.isAbsolute(configured)
                ? configured
                : path.join(this.workspaceRoot, configured);
            if (fs.existsSync(abs)) { return abs; }
        }

        // 2. SSOT canon — primary, the artifact that created everything else
        const canon = path.join(this.workspaceRoot, SSOT_CANON);
        if (fs.existsSync(canon)) { return canon; }

        // 3. SSOT mirror — fallback only if the canon is absent
        const mirror = path.join(this.workspaceRoot, SSOT_HOLDER);
        if (fs.existsSync(mirror)) { return mirror; }

        return null;
    }

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this.extensionUri],
        };

        const refresh = () => {
            const sourcePath = this.resolveSourcePath();
            const sections = this.loadSections(sourcePath);
            webviewView.webview.html = this.buildHtml(webviewView.webview, sections, sourcePath);
            this._currentSourcePath = sourcePath;
        };

        refresh();
        trackWebview('ankh', webviewView, refresh);

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

    private buildHtml(webview: vscode.Webview, sections: ArchiveSection[], sourcePath: string | null): string {
        const sectionPayload = sections.map((section) => ({
            l: section.level,
            t: section.title,
            s: section.snippet,
            n: section.line,
            k: section.kind,
            g: section.tag || '',
        }));
        const headingCount = sections.filter((section) => section.kind === 'heading').length;
        const entityCount = sections.filter((section) => section.kind === 'entity').length;
        const tierCount = sections.filter((section) => section.kind === 'tier').length;
        const xrefCount = sections.filter((section) => section.kind === 'xref').length;
        const anchorCount = sections.filter((section) => section.kind === 'anchor').length;
        const mentionCount = sections.filter((section) => section.kind === 'mention').length;
        const isCanon = !!sourcePath && sourcePath.replace(/\\/g, '/').endsWith(SSOT_CANON);
        const archiveLabel = !sourcePath
            ? 'no source found'
            : isCanon
                ? 'SSOT.md · canon — the artifact all else derives from'
                : path.basename(sourcePath);

        return loadWebviewHtml(webview, this.extensionUri, 'ankh', {
            sectionsJsonInlined: jsonForInlineScript(sectionPayload),
            archiveLabel: escapeHtml(archiveLabel),
            totalSections: String(sections.length),
            headingCount: String(headingCount),
            entityCount: String(entityCount),
            tierCount: String(tierCount),
            xrefCount: String(xrefCount),
            anchorCount: String(anchorCount),
            mentionCount: String(mentionCount),
        });
    }
}

function resolveExtensionUri(): vscode.Uri {
    const extension = vscode.extensions.getExtension('chthonic-archive.chthonic-archive');
    return extension?.extensionUri ?? vscode.Uri.file(path.resolve(__dirname, '..'));
}

function escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
