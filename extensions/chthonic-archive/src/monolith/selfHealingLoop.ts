import * as fs from 'fs';
import * as path from 'path';
import * as childProcess from 'child_process';
import * as vscode from 'vscode';

interface RuntimeProbe {
    language: 'python' | 'ruby' | 'go';
    command: string;
    args: string[];
}

interface RuntimeState {
    language: 'python' | 'ruby' | 'go';
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
        const probes: RuntimeProbe[] = [
            { language: 'python', command: 'python', args: ['-c', 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")'] },
            { language: 'ruby', command: 'ruby', args: ['-e', 'print RUBY_VERSION'] },
            { language: 'go', command: 'go', args: ['env', 'GOVERSION'] },
        ];

        const states: RuntimeState[] = [];
        for (const probe of probes) {
            try {
                const version = await execOutput(probe.command, probe.args, this.workspaceRoot);
                const cleaned = normalizeVersion(version, probe.language);
                if (!cleaned) {
                    continue;
                }
                states.push({ language: probe.language, version: cleaned });
            } catch (error) {
                this.output.appendLine(`[slab-heal] probe ${probe.language} failed: ${stringifyError(error)}`);
            }
        }
        return states;
    }

    private async isEol(language: RuntimeState['language'], version: string): Promise<boolean> {
        const response = await fetch(`${this.options.eolApiBase}/${language}.json`, {
            headers: { accept: 'application/json' },
        });
        if (!response.ok) {
            throw new Error(`endoflife query failed for ${language}: ${response.status}`);
        }

        const payload = await response.json();
        if (!Array.isArray(payload)) {
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

    private async repair(stale: RuntimeState[]): Promise<void> {
        await execPassthrough('mise', ['upgrade'], this.workspaceRoot, this.output);
        await execPassthrough('mise', ['reshim'], this.workspaceRoot, this.output);

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
        default:
            return value;
    }
}

function cycleForVersion(language: RuntimeState['language'], version: string): string {
    const parts = version.split('.');
    if (language === 'go') {
        return parts.slice(0, 2).join('.');
    }
    return parts.slice(0, 2).join('.');
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}
