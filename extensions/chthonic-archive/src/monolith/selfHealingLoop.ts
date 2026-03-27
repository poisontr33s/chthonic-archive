// @SID: EXT_SELFHEALINGLOOP_V1
import * as fs from 'fs';
import * as path from 'path';
import * as childProcess from 'child_process';
import * as vscode from 'vscode';

interface RuntimeProbe {
    language: 'python' | 'ruby' | 'go' | 'rust' | 'solana' | 'visual-studio';
    command: string;
    args: string[];
}

interface ProbeCandidate {
    command: string;
    args: string[];
}

interface RuntimeState {
    language: 'python' | 'ruby' | 'go' | 'rust' | 'solana' | 'visual-studio';
    version: string;
}

interface EolCycle {
    cycle?: string;
    eol?: boolean | string | null;
}

interface SelfHealingOptions {
    intervalMs: number;
    eolApiBase: string;
}

interface VsAuditSummary {
    allRequiredComponentsPresent: boolean;
    allCriticalBinariesPresent: boolean;
    missingComponentCount: number;
    missingBinaryCount: number;
}

export class SelfHealingLoop implements vscode.Disposable {
    private timer: NodeJS.Timeout | null = null;
    private running = false;
    private options: SelfHealingOptions = {
        intervalMs: 6 * 60 * 60 * 1000,
        eolApiBase: 'https://endoflife.date/api',
    };

    constructor(
        private readonly output: vscode.OutputChannel,
        private readonly envCollection: vscode.EnvironmentVariableCollection,
        private readonly workspaceRoot: string | null,
    ) {}

    start(options: SelfHealingOptions): void {
        this.options = options;
        this.stopTimer();
        this.timer = setInterval(() => {
            void this.runNow('interval');
        }, Math.max(60_000, options.intervalMs));
    }

    async runNow(trigger: 'manual' | 'interval' = 'manual'): Promise<void> {
        if (this.running) {
            this.output.appendLine('[slab-heal] skipped; already running');
            return;
        }

        this.running = true;
        try {
            const vsAudit = await this.auditVsToolchain();
            if (vsAudit && (!vsAudit.allRequiredComponentsPresent || !vsAudit.allCriticalBinariesPresent)) {
                this.output.appendLine(
                    `[slab-heal] vs2026 audit drift detected: components=${vsAudit.missingComponentCount}, binaries=${vsAudit.missingBinaryCount}`,
                );
            }

            const states = await this.collectRuntimeStates();
            if (states.length === 0) {
                this.output.appendLine('[slab-heal] no runtime states detected; skipping');
                return;
            }

            const stale: RuntimeState[] = [];
            for (const state of states) {
                const eol = await this.isEol(state.language, state.version);
                if (eol) {
                    stale.push(state);
                }
            }

            if (stale.length === 0) {
                this.output.appendLine(`[slab-heal] ${trigger}: all slab runtimes are supported`);
                return;
            }

            this.output.appendLine(`[slab-heal] ${trigger}: stale runtimes detected: ${stale.map((entry) => `${entry.language}@${entry.version}`).join(', ')}`);
            await this.repair(stale);
        } catch (error) {
            this.output.appendLine(`[slab-heal] run failed: ${stringifyError(error)}`);
        } finally {
            this.running = false;
        }
    }

    dispose(): void {
        this.stopTimer();
    }

    private stopTimer(): void {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }

    private async collectRuntimeStates(): Promise<RuntimeState[]> {
        const probePlans: RuntimeProbe[] = [
            { language: 'python', command: process.platform === 'win32' ? 'python3' : 'python', args: ['-c', 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")'] },
            { language: 'ruby', command: 'ruby', args: ['-e', 'print RUBY_VERSION'] },
            { language: 'go', command: 'go', args: ['env', 'GOVERSION'] },
            { language: 'rust', command: 'rustc', args: ['--version'] },
            { language: 'solana', command: 'solana', args: ['--version'] },
        ];

        const states: RuntimeState[] = [];
        for (const probe of probePlans) {
            const candidates = expandProbeCandidates(probe);
            const result = await tryProbeCandidates(candidates, this.workspaceRoot);
            if (!result.version) {
                this.output.appendLine(
                    `[slab-heal] probe ${probe.language} failed (${formatProbeCandidates(candidates)}): ${stringifyError(result.error)}`,
                );
                continue;
            }

            const cleaned = normalizeVersion(result.version, probe.language);
            if (!cleaned) {
                continue;
            }
            states.push({ language: probe.language, version: cleaned });
        }

        const vsVersion = await detectVisualStudioVersion(this.workspaceRoot);
        if (vsVersion) {
            states.push({ language: 'visual-studio', version: vsVersion });
        } else {
            this.output.appendLine('[slab-heal] probe visual-studio failed: VS 2026 Insiders not detected');
        }

        return states;
    }

    private async isEol(language: RuntimeState['language'], version: string): Promise<boolean> {
        const payload = await this.fetchCycles(language);
        if (!payload || !Array.isArray(payload)) {
            return false;
        }

        const cycle = cycleForVersion(language, version);
        const match = payload.find((entry) => {
            const typed = entry as EolCycle;
            return typed.cycle === cycle || typed.cycle === cycle.split('.').slice(0, 1).join('.');
        }) as EolCycle | undefined;

        if (!match || match.eol == null) {
            return false;
        }
        if (typeof match.eol === 'boolean') {
            return match.eol;
        }

        const eolDate = Date.parse(match.eol);
        if (Number.isNaN(eolDate)) {
            return false;
        }
        return eolDate <= Date.now();
    }

    private async fetchCycles(language: RuntimeState['language']): Promise<EolCycle[] | null> {
        const productCandidates = productAliases(language);
        for (const product of productCandidates) {
            const response = await fetch(`${this.options.eolApiBase}/${product}.json`, {
                headers: { accept: 'application/json' },
            });
            if (!response.ok) {
                continue;
            }
            const payload = await response.json();
            if (Array.isArray(payload)) {
                return payload as EolCycle[];
            }
        }
        this.output.appendLine(`[slab-heal] endoflife feed unavailable for ${language}; skipping lifecycle gate`);
        return null;
    }

    private async repair(stale: RuntimeState[]): Promise<void> {
        const hasMise = await commandExists('mise', this.workspaceRoot);
        if (hasMise) {
            await execPassthrough('mise', ['upgrade'], this.workspaceRoot, this.output);
            await execPassthrough('mise', ['reshim'], this.workspaceRoot, this.output);
        } else {
            this.output.appendLine('[slab-heal] mise not found on PATH; skipped upgrade/reshim');
        }
        await this.refreshToolpoolSnapshot();

        const includePath = await this.relinkVsHeaders();
        if (includePath) {
            this.output.appendLine(`[slab-heal] relinked MSVC headers at ${includePath}`);
        } else {
            this.output.appendLine('[slab-heal] VS include relink skipped (MSVC path not found)');
        }

        vscode.window.showInformationMessage(
            `Chthonic self-heal complete: ${stale.map((entry) => `${entry.language}@${entry.version}`).join(', ')}`,
        );
    }

    private async relinkVsHeaders(): Promise<string | null> {
        const includePath = await detectVsIncludePath(this.workspaceRoot);
        if (!includePath || !this.workspaceRoot) {
            return null;
        }

        const linkRoot = path.join(this.workspaceRoot, '.chthonic', 'native', 'msvc');
        const linkPath = path.join(linkRoot, 'include');
        fs.mkdirSync(linkRoot, { recursive: true });

        try {
            fs.rmSync(linkPath, { recursive: true, force: true });
        } catch {
            // no-op
        }

        try {
            fs.symlinkSync(includePath, linkPath, 'junction');
        } catch (error) {
            const manifestPath = path.join(linkRoot, 'include.path.txt');
            fs.writeFileSync(manifestPath, includePath, 'utf8');
            this.output.appendLine(`[slab-heal] symlink failed; wrote include manifest ${manifestPath}: ${stringifyError(error)}`);
        }

        this.envCollection.replace('CHTHONIC_VS_CPP_INCLUDE', includePath);
        this.envCollection.prepend('INCLUDE', `${includePath};`);
        return includePath;
    }

    private async auditVsToolchain(): Promise<VsAuditSummary | null> {
        const extensionRoot = resolveExtensionRoot(this.workspaceRoot);
        if (!extensionRoot) {
            return null;
        }

        const auditScript = path.join(extensionRoot, 'scripts', 'vs2026_audit.ps1');
        if (!fs.existsSync(auditScript)) {
            return null;
        }

        try {
            const raw = await execOutput('pwsh', ['-NoProfile', '-File', auditScript, '-Json'], extensionRoot);
            const parsed = JSON.parse(raw) as { summary?: VsAuditSummary };
            return parsed.summary ?? null;
        } catch (error) {
            this.output.appendLine(`[slab-heal] vs2026 audit script failed: ${stringifyError(error)}`);
            return null;
        }
    }

    private async refreshToolpoolSnapshot(): Promise<void> {
        const extensionRoot = resolveExtensionRoot(this.workspaceRoot);
        if (!extensionRoot) {
            return;
        }

        const scannerPath = path.join(extensionRoot, 'scripts', 'toolpool-scan.ts');
        if (!fs.existsSync(scannerPath)) {
            return;
        }

        try {
            await execPassthrough('bun', ['run', 'scripts/toolpool-scan.ts', '--write-env', '--quiet'], extensionRoot, this.output);
            this.output.appendLine('[slab-heal] tool-pool snapshot refreshed');
        } catch (error) {
            this.output.appendLine(`[slab-heal] tool-pool snapshot failed: ${stringifyError(error)}`);
        }
    }
}

function expandProbeCandidates(probe: RuntimeProbe): ProbeCandidate[] {
    if (probe.language === 'python' && process.platform === 'win32') {
        return [
            { command: 'python3', args: probe.args },
            { command: 'py', args: ['-3', ...probe.args] },
            { command: 'python', args: probe.args },
        ];
    }

    if (probe.language === 'go' && process.platform === 'win32') {
        return [
            { command: 'go', args: probe.args },
            { command: 'goup', args: ['go', ...probe.args] },
            { command: 'goup', args: ['current'] },
        ];
    }

    return [{ command: probe.command, args: probe.args }];
}

function formatProbeCandidates(candidates: ProbeCandidate[]): string {
    return candidates
        .map((candidate) => `${candidate.command} ${candidate.args.join(' ')}`.trim())
        .join(' | ');
}

async function tryProbeCandidates(
    candidates: ProbeCandidate[],
    cwd: string | null,
): Promise<{ version: string | null; error: unknown }> {
    let lastError: unknown = new Error('no probe candidates defined');
    for (const candidate of candidates) {
        try {
            const version = await execOutput(candidate.command, candidate.args, cwd);
            if (version.trim().length > 0) {
                return { version, error: null };
            }
            lastError = new Error(`${candidate.command} returned empty output`);
        } catch (error) {
            lastError = error;
        }
    }
    return { version: null, error: lastError };
}

async function detectVsIncludePath(workspaceRoot: string | null): Promise<string | null> {
    const vswhere = path.join(
        process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)',
        'Microsoft Visual Studio',
        'Installer',
        'vswhere.exe',
    );

    if (fs.existsSync(vswhere)) {
        try {
            const installationPath = await execOutput(
                vswhere,
                [
                    '-latest',
                    '-products',
                    '*',
                    '-requires',
                    'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                    '-property',
                    'installationPath',
                ],
                workspaceRoot,
            );
            const include = resolveNewestMsvcInclude(installationPath.trim());
            if (include) {
                return include;
            }
        } catch {
            // ignore and continue with fallback probing
        }
    }

    const fallbackRoots = [
        'C:\\Program Files\\Microsoft Visual Studio\\18',
        'C:\\Program Files\\Microsoft Visual Studio\\2026',
        'C:\\Program Files\\Microsoft Visual Studio\\2022',
    ];
    for (const root of fallbackRoots) {
        const include = resolveNewestMsvcInclude(root);
        if (include) {
            return include;
        }
    }

    return null;
}

function resolveExtensionRoot(workspaceRoot: string | null): string | null {
    if (!workspaceRoot) {
        return null;
    }

    const nested = path.join(workspaceRoot, 'extensions', 'chthonic-archive');
    if (fs.existsSync(path.join(nested, 'package.json'))) {
        return nested;
    }
    if (fs.existsSync(path.join(workspaceRoot, 'package.json'))) {
        return workspaceRoot;
    }
    return null;
}

async function detectVisualStudioVersion(workspaceRoot: string | null): Promise<string | null> {
    const vswhere = path.join(
        process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)',
        'Microsoft Visual Studio',
        'Installer',
        'vswhere.exe',
    );

    if (!fs.existsSync(vswhere)) {
        return null;
    }

    const laneQueries: string[][] = [
        ['-prerelease', '-latest', '-products', 'Microsoft.VisualStudio.Product.Professional', '-property', 'installationVersion'],
        ['-prerelease', '-latest', '-products', 'Microsoft.VisualStudio.Product.BuildTools', '-property', 'installationVersion'],
    ];

    for (const query of laneQueries) {
        try {
            const version = await execOutput(vswhere, query, workspaceRoot);
            const trimmed = version.trim();
            if (trimmed.length > 0) {
                return trimmed;
            }
        } catch {
            // no-op: probe next lane
        }
    }

    return null;
}

function resolveNewestMsvcInclude(basePath: string): string | null {
    if (!fs.existsSync(basePath)) {
        return null;
    }

    const candidates: string[] = [];
    const stack = [basePath];
    while (stack.length > 0) {
        const next = stack.pop()!;
        let entries: fs.Dirent[] = [];
        try {
            entries = fs.readdirSync(next, { withFileTypes: true });
        } catch {
            continue;
        }

        for (const entry of entries) {
            const full = path.join(next, entry.name);
            if (!entry.isDirectory()) {
                continue;
            }
            if (entry.name === 'include' && full.includes(`${path.sep}VC${path.sep}Tools${path.sep}MSVC${path.sep}`)) {
                candidates.push(full);
                continue;
            }
            stack.push(full);
        }
    }

    if (candidates.length === 0) {
        return null;
    }
    candidates.sort((a, b) => b.localeCompare(a, undefined, { numeric: true, sensitivity: 'base' }));
    return candidates[0];
}

async function execOutput(command: string, args: string[], cwd: string | null): Promise<string> {
    return new Promise<string>((resolve, reject) => {
        childProcess.execFile(command, args, {
            cwd: cwd || undefined,
            windowsHide: true,
            timeout: 15_000,
        }, (error, stdout, stderr) => {
            if (error) {
                reject(new Error(`${command} ${args.join(' ')} failed: ${stderr || error.message}`));
                return;
            }
            resolve(String(stdout).trim());
        });
    });
}

async function commandExists(command: string, cwd: string | null): Promise<boolean> {
    if (process.platform === 'win32') {
        try {
            await execOutput('where', [command], cwd);
            return true;
        } catch {
            return false;
        }
    }

    try {
        await execOutput('which', [command], cwd);
        return true;
    } catch {
        return false;
    }
}

async function execPassthrough(
    command: string,
    args: string[],
    cwd: string | null,
    output: vscode.OutputChannel,
): Promise<void> {
    await new Promise<void>((resolve, reject) => {
        const proc = childProcess.spawn(command, args, {
            cwd: cwd || undefined,
            windowsHide: true,
            stdio: ['ignore', 'pipe', 'pipe'],
        });

        proc.stdout.on('data', (chunk: Buffer) => {
            output.appendLine(`[slab-heal] ${chunk.toString().trimEnd()}`);
        });
        proc.stderr.on('data', (chunk: Buffer) => {
            output.appendLine(`[slab-heal] ${chunk.toString().trimEnd()}`);
        });
        proc.on('error', reject);
        proc.on('exit', (code) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`${command} ${args.join(' ')} exited with code ${code ?? -1}`));
            }
        });
    });
}

function normalizeVersion(raw: string, language: RuntimeState['language']): string {
    const value = raw.trim();
    if (!value) {
        return '';
    }

    switch (language) {
        case 'go':
            return value.replace(/^go/i, '');
        case 'rust':
            return value.replace(/^rustc\s+/i, '').split(/\s+/)[0] ?? '';
        case 'solana':
            return value.replace(/^solana-cli\s+/i, '').split(/\s+/)[0] ?? '';
        case 'visual-studio':
            return value.split(/\s+/)[0] ?? '';
        default:
            return value;
    }
}

function cycleForVersion(language: RuntimeState['language'], version: string): string {
    const parts = version.split('.');
    if (language === 'go') {
        return parts.slice(0, 2).join('.');
    }
    if (language === 'solana') {
        return parts.slice(0, 1).join('.');
    }
    if (language === 'visual-studio') {
        return parts.slice(0, 2).join('.');
    }
    return parts.slice(0, 2).join('.');
}

function productAliases(language: RuntimeState['language']): string[] {
    switch (language) {
        case 'solana':
            return ['solana', 'agave', 'solana-cli'];
        case 'visual-studio':
            return ['visual-studio'];
        default:
            return [language];
    }
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
