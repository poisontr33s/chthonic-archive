// @SID: EXT_DESIGN_FRAME_VIEW_V1
import { spawn } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';
import { jsonForInlineScript, loadWebviewHtml } from '../runtime/webviewLoader';
import { trackWebview } from '../runtime/webviewHmrWatcher';

type GateStatus = 'admitted' | 'open' | 'blocked_not_closed' | 'degraded' | string;

interface DesignFrameState {
    readonly selectedRoot: string | null;
    readonly exportRoot: string | null;
    readonly frameRoot: string | null;
    readonly sourceRoot: string | null;
    readonly manifest: unknown;
    readonly tokens: unknown;
    readonly designContract: string;
    readonly handoffPrompt: string;
    readonly preview: PreviewState;
    readonly gates: Array<{ level: string; status: GateStatus }>;
    readonly errors: string[];
    readonly statusMessage: string | null;
    readonly intakeRunning: boolean;
}

interface PreviewState {
    readonly mode: 'html' | 'image' | 'none';
    readonly uri: string | null;
    readonly label: string;
}

interface FrameRoots {
    readonly selectedRoot: string;
    readonly exportRoot: string;
    readonly frameRoot: string;
    readonly sourceRoot: string | null;
}

export class DesignFrameProvider implements vscode.WebviewViewProvider, vscode.Disposable {
    static readonly viewType = 'chthonic.designFrameView';

    private view: vscode.WebviewView | null = null;
    private selectedRoot: string | null = null;
    private intakeRunning = false;
    private statusMessage: string | null = null;

    constructor(
        private readonly extensionUri: vscode.Uri,
        private readonly workspaceRoot: string | null,
        private readonly outputChannel: vscode.OutputChannel,
    ) {}

    resolveWebviewView(
        webviewView: vscode.WebviewView,
        _context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ): void {
        this.view = webviewView;
        this.selectedRoot = this.selectedRoot ?? this.findLatestExportRoot();
        this.configureWebview(webviewView.webview);
        webviewView.webview.html = this.buildHtml(webviewView.webview);
        trackWebview('design-frame', webviewView, () => {
            this.configureWebview(webviewView.webview);
            webviewView.webview.html = this.buildHtml(webviewView.webview);
        });

        webviewView.webview.onDidReceiveMessage((message: unknown) => {
            void this.handleMessage(message);
        });
    }

    dispose(): void {
        this.view = null;
    }

    async selectExportRoot(): Promise<void> {
        const defaultUri = this.workspaceRoot
            ? vscode.Uri.file(path.join(this.workspaceRoot, 'artifacts', 'claude-design'))
            : undefined;
        const picked = await vscode.window.showOpenDialog({
            title: 'Select Claude Design export or frame folder',
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            defaultUri,
        });
        const folder = picked?.[0]?.fsPath;
        if (!folder) {
            return;
        }
        this.setExportRoot(folder);
        void vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        void vscode.commands.executeCommand(`${DesignFrameProvider.viewType}.focus`);
    }

    setExportRoot(absPath: string): void {
        this.selectedRoot = absPath;
        this.refresh();
    }

    refresh(): void {
        if (!this.view) {
            return;
        }
        this.configureWebview(this.view.webview);
        this.view.webview.html = this.buildHtml(this.view.webview);
    }

    private configureWebview(webview: vscode.Webview): void {
        const localRoots = [this.extensionUri];
        if (this.workspaceRoot) {
            localRoots.push(vscode.Uri.file(this.workspaceRoot));
        }
        if (this.selectedRoot) {
            localRoots.push(vscode.Uri.file(this.selectedRoot));
        }
        const roots = this.resolveRoots();
        if (roots) {
            localRoots.push(vscode.Uri.file(roots.exportRoot), vscode.Uri.file(roots.frameRoot));
            if (roots.sourceRoot) {
                localRoots.push(vscode.Uri.file(roots.sourceRoot));
            }
        }
        webview.options = {
            enableScripts: true,
            localResourceRoots: localRoots,
        };
    }

    private buildHtml(webview: vscode.Webview): string {
        const state = this.readState(webview);
        return loadWebviewHtml(webview, this.extensionUri, 'design-frame', {
            stateJson: jsonForInlineScript(state),
        });
    }

    private async handleMessage(message: unknown): Promise<void> {
        if (!message || typeof message !== 'object') {
            return;
        }
        const payload = message as { type?: string };
        if (payload.type === 'selectExport') {
            await this.selectExportRoot();
            return;
        }
        if (payload.type === 'openClaudeDesign') {
            await this.openClaudeDesign();
            return;
        }
        if (payload.type === 'importCapture') {
            await this.importCapture();
            return;
        }
        if (payload.type === 'refresh') {
            this.refresh();
            return;
        }
        if (payload.type === 'runIntake') {
            await this.runIntake();
            return;
        }
        if (payload.type === 'copyHandoff') {
            const state = this.readState(this.view?.webview);
            if (state.handoffPrompt.trim().length > 0) {
                await vscode.env.clipboard.writeText(state.handoffPrompt);
                void vscode.window.showInformationMessage('Claude Design handoff prompt copied.');
            } else {
                void vscode.window.showWarningMessage('No handoff_prompt.md found for the selected Design Frame.');
            }
            return;
        }
        if (payload.type === 'openContract') {
            const state = this.readState(this.view?.webview);
            if (state.frameRoot) {
                const contractPath = path.join(state.frameRoot, 'design_contract.md');
                if (fs.existsSync(contractPath)) {
                    await vscode.window.showTextDocument(vscode.Uri.file(contractPath), { preview: false });
                }
            }
        }
    }

    async openClaudeDesign(): Promise<void> {
        await vscode.env.openExternal(vscode.Uri.parse('https://claude.ai/design'));
    }

    async importCapture(): Promise<void> {
        if (!this.workspaceRoot) {
            void vscode.window.showWarningMessage('Workspace root is required to import Claude Design captures.');
            return;
        }
        const picked = await vscode.window.showOpenDialog({
            title: 'Import Claude Design screenshots, exports, or capture folder',
            canSelectFiles: true,
            canSelectFolders: true,
            canSelectMany: true,
            filters: {
                'Claude Design capture files': ['png', 'jpg', 'jpeg', 'webp', 'avif', 'svg', 'html', 'htm', 'css', 'js', 'md', 'pdf', 'pptx'],
            },
        });
        if (!picked || picked.length === 0) {
            return;
        }

        const artifactRoot = path.join(
            this.workspaceRoot,
            'artifacts',
            'claude-design',
            `browser-capture-${timestampSlug()}`,
        );
        const sourceRoot = path.join(artifactRoot, 'source');
        fs.mkdirSync(sourceRoot, { recursive: true });

        let copied = 0;
        for (const uri of picked) {
            copied += copyCaptureItem(uri.fsPath, sourceRoot);
        }

        if (copied === 0) {
            this.statusMessage = 'No supported capture files were imported.';
            this.refresh();
            void vscode.window.showWarningMessage('No supported Claude Design capture files were imported.');
            return;
        }

        this.setExportRoot(artifactRoot);
        this.statusMessage = `Imported ${copied} capture file(s). Running local intake...`;
        this.refresh();
        await this.runIntake(artifactRoot);
    }

    private async runIntake(targetOverride?: string): Promise<void> {
        if (!this.workspaceRoot) {
            void vscode.window.showWarningMessage('Workspace root is required to run Claude Design intake.');
            return;
        }
        if (this.intakeRunning) {
            void vscode.window.showInformationMessage('Claude Design intake is already running.');
            return;
        }
        const target = targetOverride ?? this.resolveRoots()?.exportRoot ?? this.selectedRoot;
        if (!target) {
            void vscode.window.showWarningMessage('Select a Claude Design export folder first.');
            return;
        }
        this.intakeRunning = true;
        this.statusMessage = `Running intake for ${displayPath(target, this.workspaceRoot)}...`;
        this.refresh();
        this.outputChannel.appendLine(`[design-frame] running intake for ${target}`);

        await new Promise<void>((resolve) => {
            const child = spawn('bun', ['run', 'design:intake', target], {
                cwd: this.workspaceRoot ?? undefined,
                shell: false,
                windowsHide: true,
            });
            child.stdout.on('data', (chunk: Buffer) => {
                this.outputChannel.append(chunk.toString());
            });
            child.stderr.on('data', (chunk: Buffer) => {
                this.outputChannel.append(chunk.toString());
            });
            child.on('error', (error) => {
                this.intakeRunning = false;
                this.statusMessage = `Intake failed to start: ${stringifyError(error)}`;
                this.outputChannel.appendLine(`[design-frame] intake failed to start: ${stringifyError(error)}`);
                this.refresh();
                resolve();
            });
            child.on('close', (code) => {
                this.intakeRunning = false;
                if (code === 0) {
                    this.statusMessage = `Intake complete: ${displayPath(target, this.workspaceRoot)}`;
                    this.selectedRoot = target;
                } else {
                    this.statusMessage = `Intake failed with exit code ${code}. See Chthonic Archive output.`;
                }
                this.refresh();
                resolve();
            });
        });
    }

    private readState(webview?: vscode.Webview): DesignFrameState {
        const errors: string[] = [];
        const roots = this.resolveRoots();
        if (!roots) {
            return {
                selectedRoot: this.selectedRoot,
                exportRoot: null,
                frameRoot: null,
                sourceRoot: null,
                manifest: null,
                tokens: null,
                designContract: '',
                handoffPrompt: '',
                preview: { mode: 'none', uri: null, label: 'No Design Frame selected' },
                gates: [],
                errors: this.selectedRoot
                    ? [`No frame artifacts found under ${displayPath(this.selectedRoot, this.workspaceRoot)}.`]
                    : ['No Claude Design export selected.'],
                statusMessage: this.statusMessage,
                intakeRunning: this.intakeRunning,
            };
        }

        const manifest = readJson(path.join(roots.frameRoot, 'manifest.json'), errors);
        const tokens = readJson(path.join(roots.frameRoot, 'tokens.json'), errors);
        const designContract = readText(path.join(roots.frameRoot, 'design_contract.md'), errors);
        const handoffPrompt = readText(path.join(roots.frameRoot, 'handoff_prompt.md'), errors);
        return {
            selectedRoot: displayPath(roots.selectedRoot, this.workspaceRoot),
            exportRoot: displayPath(roots.exportRoot, this.workspaceRoot),
            frameRoot: displayPath(roots.frameRoot, this.workspaceRoot),
            sourceRoot: roots.sourceRoot ? displayPath(roots.sourceRoot, this.workspaceRoot) : null,
            manifest,
            tokens,
            designContract,
            handoffPrompt,
            preview: this.resolvePreview(webview, roots, manifest),
            gates: extractGates(manifest),
            errors,
            statusMessage: this.statusMessage,
            intakeRunning: this.intakeRunning,
        };
    }

    private resolveRoots(): FrameRoots | null {
        if (!this.selectedRoot) {
            return null;
        }
        const selected = path.resolve(this.selectedRoot);
        const selectedManifest = path.join(selected, 'manifest.json');
        if (fs.existsSync(selectedManifest)) {
            return {
                selectedRoot: selected,
                exportRoot: path.dirname(selected),
                frameRoot: selected,
                sourceRoot: inferSourceRoot(path.dirname(selected)),
            };
        }
        const frameRoot = path.join(selected, 'frame');
        if (fs.existsSync(path.join(frameRoot, 'manifest.json'))) {
            return {
                selectedRoot: selected,
                exportRoot: selected,
                frameRoot,
                sourceRoot: inferSourceRoot(selected),
            };
        }
        return null;
    }

    private resolvePreview(webview: vscode.Webview | undefined, roots: FrameRoots, manifest: unknown): PreviewState {
        const sourceRoot = roots.sourceRoot;
        if (!sourceRoot || !webview) {
            return { mode: 'none', uri: null, label: 'No source preview available' };
        }

        const screenshot = findPrimaryScreenshot(manifest, sourceRoot);
        if (screenshot) {
            return {
                mode: 'image',
                uri: webview.asWebviewUri(vscode.Uri.file(screenshot)).toString(),
                label: displayPath(screenshot, this.workspaceRoot),
            };
        }

        const html = findPrimaryHtml(manifest, sourceRoot);
        if (html) {
            return {
                mode: 'html',
                uri: webview.asWebviewUri(vscode.Uri.file(html)).toString(),
                label: displayPath(html, this.workspaceRoot),
            };
        }

        return { mode: 'none', uri: null, label: 'No HTML or screenshot found' };
    }

    private findLatestExportRoot(): string | null {
        if (!this.workspaceRoot) {
            return null;
        }
        const root = path.join(this.workspaceRoot, 'artifacts', 'claude-design');
        if (!fs.existsSync(root)) {
            return null;
        }
        const candidates: Array<{ root: string; mtimeMs: number }> = [];
        walkCandidateFrames(root, candidates);
        candidates.sort((a, b) => b.mtimeMs - a.mtimeMs);
        return candidates[0]?.root ?? null;
    }
}

const CAPTURE_EXTENSIONS = new Set([
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.avif',
    '.svg',
    '.html',
    '.htm',
    '.css',
    '.js',
    '.md',
    '.pdf',
    '.pptx',
]);

function copyCaptureItem(absPath: string, destinationRoot: string): number {
    const info = fs.statSync(absPath);
    if (info.isDirectory()) {
        let count = 0;
        const base = safeSegment(path.basename(absPath));
        const targetRoot = path.join(destinationRoot, base);
        const entries = safeReadDir(absPath);
        for (const entry of entries) {
            if (entry.name === '.git' || entry.name === 'node_modules' || entry.name === 'frame') {
                continue;
            }
            count += copyCaptureItem(path.join(absPath, entry.name), targetRoot);
        }
        return count;
    }
    if (!info.isFile() || !CAPTURE_EXTENSIONS.has(path.extname(absPath).toLowerCase())) {
        return 0;
    }
    fs.mkdirSync(destinationRoot, { recursive: true });
    const target = uniquePath(path.join(destinationRoot, safeSegment(path.basename(absPath))));
    fs.copyFileSync(absPath, target);
    return 1;
}

function uniquePath(absPath: string): string {
    if (!fs.existsSync(absPath)) {
        return absPath;
    }
    const dir = path.dirname(absPath);
    const ext = path.extname(absPath);
    const stem = path.basename(absPath, ext);
    for (let i = 2; i < 10_000; i += 1) {
        const candidate = path.join(dir, `${stem}-${i}${ext}`);
        if (!fs.existsSync(candidate)) {
            return candidate;
        }
    }
    return path.join(dir, `${stem}-${Date.now()}${ext}`);
}

function timestampSlug(): string {
    return new Date().toISOString().replace(/[:.]/g, '-');
}

function safeSegment(value: string): string {
    return value.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_');
}

function inferSourceRoot(exportRoot: string): string | null {
    const source = path.join(exportRoot, 'source');
    if (fs.existsSync(source)) {
        return source;
    }
    return fs.existsSync(exportRoot) ? exportRoot : null;
}

function readJson(absPath: string, errors: string[]): unknown {
    try {
        return JSON.parse(fs.readFileSync(absPath, 'utf8'));
    } catch (error) {
        errors.push(`${displayPath(absPath, null)} unreadable: ${stringifyError(error)}`);
        return null;
    }
}

function readText(absPath: string, errors: string[]): string {
    try {
        return fs.readFileSync(absPath, 'utf8');
    } catch (error) {
        errors.push(`${displayPath(absPath, null)} unreadable: ${stringifyError(error)}`);
        return '';
    }
}

function extractGates(manifest: unknown): Array<{ level: string; status: GateStatus }> {
    if (!manifest || typeof manifest !== 'object') {
        return [];
    }
    const levels = (manifest as { levels?: unknown }).levels;
    if (!levels || typeof levels !== 'object') {
        return [];
    }
    return Object.entries(levels as Record<string, GateStatus>).map(([level, status]) => ({ level, status }));
}

function findPrimaryScreenshot(manifest: unknown, sourceRoot: string): string | null {
    const screenshots = primaryFiles(manifest, 'screenshots');
    for (const rel of screenshots) {
        const abs = path.join(path.dirname(sourceRoot), rel);
        if (fs.existsSync(abs)) {
            return abs;
        }
    }
    return findByExtension(sourceRoot, ['.png', '.jpg', '.jpeg', '.webp', '.avif', '.svg'], /screenshot|desktop|mobile|contact/i);
}

function findPrimaryHtml(manifest: unknown, sourceRoot: string): string | null {
    const html = primaryFiles(manifest, 'html');
    for (const rel of html) {
        const abs = path.join(path.dirname(sourceRoot), rel);
        if (fs.existsSync(abs)) {
            return abs;
        }
    }
    const index = path.join(sourceRoot, 'index.html');
    if (fs.existsSync(index)) {
        return index;
    }
    return findByExtension(sourceRoot, ['.html', '.htm']);
}

function primaryFiles(manifest: unknown, key: 'html' | 'screenshots'): string[] {
    if (!manifest || typeof manifest !== 'object') {
        return [];
    }
    const primary = (manifest as { primary_files?: unknown }).primary_files;
    if (!primary || typeof primary !== 'object') {
        return [];
    }
    const value = (primary as Record<string, unknown>)[key];
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function findByExtension(root: string, extensions: string[], namePattern?: RegExp): string | null {
    const queue = [root];
    while (queue.length > 0) {
        const current = queue.shift();
        if (!current) continue;
        const entries = safeReadDir(current);
        for (const entry of entries) {
            const abs = path.join(current, entry.name);
            if (entry.isDirectory()) {
                if (entry.name !== 'frame') {
                    queue.push(abs);
                }
                continue;
            }
            if (!entry.isFile()) {
                continue;
            }
            if (extensions.includes(path.extname(entry.name).toLowerCase()) && (!namePattern || namePattern.test(entry.name))) {
                return abs;
            }
        }
    }
    return null;
}

function walkCandidateFrames(root: string, candidates: Array<{ root: string; mtimeMs: number }>): void {
    const entries = safeReadDir(root);
    for (const entry of entries) {
        const abs = path.join(root, entry.name);
        if (!entry.isDirectory()) {
            continue;
        }
        const frameManifest = path.join(abs, 'frame', 'manifest.json');
        if (fs.existsSync(frameManifest)) {
            candidates.push({ root: abs, mtimeMs: fs.statSync(frameManifest).mtimeMs });
            continue;
        }
        walkCandidateFrames(abs, candidates);
    }
}

function safeReadDir(absPath: string): fs.Dirent[] {
    try {
        return fs.readdirSync(absPath, { withFileTypes: true });
    } catch {
        return [];
    }
}

function displayPath(absPath: string, workspaceRoot: string | null): string {
    if (workspaceRoot && path.isAbsolute(absPath)) {
        const rel = path.relative(workspaceRoot, absPath);
        if (!rel.startsWith('..') && !path.isAbsolute(rel)) {
            return rel.replaceAll(path.sep, '/');
        }
    }
    return absPath.replaceAll(path.sep, '/');
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
