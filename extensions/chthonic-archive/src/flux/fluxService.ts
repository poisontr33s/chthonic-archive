// @SID: EXT_FLUX_SERVICE_V1
import { execFileSync } from 'node:child_process';
import * as crypto from 'node:crypto';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as vscode from 'vscode';
import { FluxLauncherViewProvider, type FluxLauncherState } from './fluxLauncherView';
import { FluxPanel } from './fluxPanel';

const SECRET_KEY = 'chthonic.flux.masterSecret';
const DEFAULT_BRIDGE_RELATIVE = 'apps/chthonic-tensor-bridge';

export interface FluxBridge {
    setMasterSecret(secret: string): void;
    clearMasterSecret(): void;
    hardwareFingerprint(): { gpuUuid: string; machineGuid: string };
    startSatellite(opts: {
        uvPath: string; cwd: string;
        pipeName?: string; mmfName?: string; ditPipeName?: string;
    }): Promise<void>;
    stopSatellite(graceful: boolean): Promise<void>;
    healthCheck(): Promise<{ raw: string }>;
    generate(req: {
        prompt: string; steps: number; guidance: number;
        width: number; height: number; seed: number;
    }): Promise<{ buffer: Buffer; genMs: number; width: number; height: number; channels: number }>;
    loadEngine(opts: {
        enginePath: string; sealPath?: string; ditPipeName?: string;
    }): Promise<{ ioTensors: string[]; ditPipeName: string }>;
    unloadEngine(): Promise<void>;
}

const DEFAULT_DIT_PIPE = '\\\\.\\pipe\\chthonic-flux-dit';
const ENGINE_BASENAME = 'flux1-dev-sm89';

export class FluxService implements vscode.Disposable {
    private bridge: FluxBridge | null = null;
    private panel: FluxPanel | null = null;
    private launcherProvider: FluxLauncherViewProvider | null = null;
    private satelliteRunning = false;
    private statusBarItem: vscode.StatusBarItem | null = null;
    private readonly secretCache = { value: null as string | null };

    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly output: vscode.OutputChannel,
        private readonly workspaceRoot: string | null,
    ) {}

    dispose(): void {
        if (this.bridge) {
            if (this.satelliteRunning) {
                void this.bridge.stopSatellite(true).catch(() => undefined);
            }
            // Free the resident engine on shutdown too. The bridge's static
            // engine holder is otherwise only reclaimed on extension-host
            // process death; an orderly dispose should release it now.
            void this.bridge.unloadEngine().catch(() => undefined);
            try { this.bridge.clearMasterSecret(); } catch { /* ignore */ }
        }
        this.panel?.dispose();
        this.launcherProvider?.dispose();
    }

    register(): void {
        // Reap any orphaned satellite from a prior unclean exit BEFORE anything
        // else — frees the ~6 GB a zombie holds. Belt-and-suspenders to the
        // bridge's kill-on-close Job Object (which covers the normal hard-exit
        // path); this catches zombies that predate the job fix or escaped it.
        this.reapStaleSatellite();
        this.launcherProvider = new FluxLauncherViewProvider(
            this.launcherState(),
            (command) => void this.dispatchLauncherCommand(command),
        );
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 50);
        this.statusBarItem.command = 'chthonic.flux.openPanel';
        this.refreshStatusBar();
        this.statusBarItem.show();
        this.context.subscriptions.push(
            vscode.window.registerWebviewViewProvider(FluxLauncherViewProvider.viewType, this.launcherProvider),
            vscode.commands.registerCommand('chthonic.flux.openPanel', () => this.openPanel()),
            vscode.commands.registerCommand('chthonic.flux.focusLauncher', () => this.focusLauncher()),
            vscode.commands.registerCommand('chthonic.flux.verifyPresence', () => this.verifyPresence()),
            vscode.commands.registerCommand('chthonic.flux.showOutput', () => this.showOutput()),
            vscode.commands.registerCommand('chthonic.flux.startBackend', () => this.startBackend()),
            vscode.commands.registerCommand('chthonic.flux.stopBackend', () => this.stopBackend()),
            vscode.commands.registerCommand('chthonic.flux.rotateSecret', () => this.rotateSecret()),
            vscode.commands.registerCommand('chthonic.flux.setMasterSecret', () => this.setMasterSecretInteractive()),
            vscode.commands.registerCommand('chthonic.flux.revealMasterSecret', () => this.revealMasterSecret()),
            this.statusBarItem,
            this,
        );
        this.publishLauncherState();
        if (vscode.workspace.getConfiguration('chthonic.flux').get<boolean>('showPresenceOnStartup', true)) {
            setTimeout(() => {
                void this.announcePresence('startup');
            }, 900);
        }
    }

    private refreshStatusBar(): void {
        if (!this.statusBarItem) return;
        if (this.satelliteRunning) {
            this.statusBarItem.text = '$(zap) FLUX: running';
            this.statusBarItem.tooltip = 'Chthonic FLUX satellite running — click to open panel';
        } else {
            this.statusBarItem.text = '$(circle-outline) FLUX: idle';
            this.statusBarItem.tooltip = 'Chthonic FLUX idle — click to open panel and start';
        }
        this.publishLauncherState();
    }

    private launcherState(): FluxLauncherState {
        const bridgeCandidates = this.bridgePathCandidates();
        return {
            version: String(this.context.extension.packageJSON.version ?? 'unknown'),
            workspaceRoot: this.workspaceRoot,
            satelliteRunning: this.satelliteRunning,
            bridgeAvailable: bridgeCandidates.some((candidate) => fs.existsSync(candidate)),
            bridgeCandidates,
        };
    }

    private publishLauncherState(): void {
        this.launcherProvider?.update(this.launcherState());
    }

    private async dispatchLauncherCommand(command: 'openPanel' | 'startBackend' | 'stopBackend' | 'verifyPresence' | 'showOutput'): Promise<void> {
        switch (command) {
            case 'openPanel':
                await this.openPanel();
                break;
            case 'startBackend':
                await this.startBackend();
                break;
            case 'stopBackend':
                await this.stopBackend();
                break;
            case 'verifyPresence':
                await this.verifyPresence();
                break;
            case 'showOutput':
                this.showOutput();
                break;
        }
    }

    private showOutput(): void {
        this.output.show(true);
        this.output.appendLine(`[flux] output revealed; extension v${this.context.extension.packageJSON.version ?? 'unknown'}`);
    }

    private async focusLauncher(): Promise<void> {
        await vscode.commands.executeCommand('workbench.view.extension.chthonic-archive');
        await vscode.commands.executeCommand(`${FluxLauncherViewProvider.viewType}.focus`);
        this.publishLauncherState();
    }

    private async verifyPresence(): Promise<void> {
        await this.focusLauncher();
        await this.announcePresence('manual');
    }

    private async announcePresence(reason: 'startup' | 'manual'): Promise<void> {
        this.publishLauncherState();
        const version = String(this.context.extension.packageJSON.version ?? 'unknown');
        this.output.appendLine(`[flux] presence verified (${reason}); extension=chthonic-archive.chthonic-archive@${version}`);
        const choice = await vscode.window.showInformationMessage(
            `Chthonic FLUX is active (v${version}).`,
            'Open Panel',
            'Show FLUX Gate',
            'Show Output',
        );
        if (choice === 'Open Panel') {
            await this.openPanel();
        } else if (choice === 'Show FLUX Gate') {
            await this.focusLauncher();
        } else if (choice === 'Show Output') {
            this.showOutput();
        }
    }

    private loadBridge(): FluxBridge | null {
        if (this.bridge) return this.bridge;
        const candidates = this.bridgePathCandidates();
        for (const p of candidates) {
            if (fs.existsSync(p)) {
                try {
                    this.bridge = require(p) as FluxBridge;
                    this.output.appendLine(`[flux] loaded native bridge: ${p}`);
                    return this.bridge;
                } catch (e) {
                    this.output.appendLine(`[flux] bridge at ${p} failed to load: ${(e as Error).message}`);
                }
            }
        }
        this.output.appendLine(
            `[flux] native bridge NOT found. Tried:\n  ${candidates.join('\n  ')}\n` +
            `Build it with: bun install (in apps/chthonic-tensor-bridge)`,
        );
        return null;
    }

    private bridgePathCandidates(): string[] {
        const out: string[] = [];
        const cfg = vscode.workspace.getConfiguration('chthonic.flux').get<string>('bridgePath');
        if (cfg) out.push(cfg);
        if (this.workspaceRoot) {
            out.push(path.join(this.workspaceRoot, DEFAULT_BRIDGE_RELATIVE, 'build', 'Release', 'chthonic_tensor_bridge.node'));
            out.push(path.join(this.workspaceRoot, DEFAULT_BRIDGE_RELATIVE, 'index.js'));
        }
        out.push(path.join(this.context.extensionPath, 'native', 'chthonic_tensor_bridge.node'));
        return out;
    }

    private async ensureMasterSecret(): Promise<string> {
        if (this.secretCache.value) return this.secretCache.value;
        let secret = await this.context.secrets.get(SECRET_KEY);
        if (!secret || secret.length < 32) {
            // Generate AND surface — no auto-buried secret. The operator needs
            // this value to drive the forge; hiding it makes the forge step
            // impossible.
            secret = crypto.randomBytes(32).toString('hex');
            await this.context.secrets.store(SECRET_KEY, secret);
            this.output.appendLine('[flux] generated a fresh 64-char master secret');
            const choice = await vscode.window.showInformationMessage(
                'FLUX master secret generated. The forge needs this same secret on stdin. Copy it now and store it somewhere durable — losing it means re-forging the engine.',
                { modal: true },
                'Copy to clipboard',
                'Show secret',
            );
            if (choice === 'Copy to clipboard') {
                await vscode.env.clipboard.writeText(secret);
                vscode.window.showInformationMessage('Master secret copied. Save it before you close the clipboard.');
            } else if (choice === 'Show secret') {
                vscode.window.showInformationMessage(`Master secret: ${secret}`, { modal: true });
            }
        }
        this.secretCache.value = secret;
        return secret;
    }

    private async setMasterSecretInteractive(): Promise<void> {
        const existing = await this.context.secrets.get(SECRET_KEY);
        if (existing) {
            const choice = await vscode.window.showWarningMessage(
                'A FLUX master secret already exists in SecretStorage. Replacing it will invalidate the currently-sealed engine. Continue?',
                { modal: true },
                'Replace',
            );
            if (choice !== 'Replace') return;
        }
        const value = await vscode.window.showInputBox({
            prompt: 'Paste the FLUX master secret (>= 32 chars; same string used by flux-engine-forge stdin).',
            password: true,
            ignoreFocusOut: true,
            validateInput: (v) => (v && v.length >= 32) ? null : 'Must be at least 32 characters.',
        });
        if (!value) return;
        if (this.satelliteRunning) await this.stopBackend();
        await this.context.secrets.store(SECRET_KEY, value);
        this.secretCache.value = value;
        this.output.appendLine('[flux] master secret set from operator input');
        vscode.window.showInformationMessage('FLUX master secret stored. Forge with this secret, then run "Open Panel".');
    }

    private async revealMasterSecret(): Promise<void> {
        const confirm = await vscode.window.showWarningMessage(
            'Reveal the FLUX master secret? It will be copied to your clipboard. Only do this on a trusted machine and clear the clipboard afterward.',
            { modal: true },
            'Reveal',
        );
        if (confirm !== 'Reveal') return;
        const secret = await this.context.secrets.get(SECRET_KEY);
        if (!secret) {
            vscode.window.showWarningMessage('No FLUX master secret in SecretStorage yet. Run "Open Panel" to generate one, or "Set Master Secret" to paste an existing one.');
            return;
        }
        await vscode.env.clipboard.writeText(secret);
        vscode.window.showInformationMessage(`Master secret copied to clipboard (${secret.length} chars). Clear the clipboard when done.`);
    }

    private async rotateSecret(): Promise<void> {
        const confirm = await vscode.window.showWarningMessage(
            'Rotating the FLUX master secret will invalidate the existing sealed engine. You will need to re-run flux-engine-forge with the new secret. Continue?',
            { modal: true },
            'Rotate',
        );
        if (confirm !== 'Rotate') return;
        if (this.satelliteRunning) await this.stopBackend();
        const fresh = crypto.randomBytes(32).toString('hex');
        await this.context.secrets.store(SECRET_KEY, fresh);
        this.secretCache.value = fresh;
        this.output.appendLine('[flux] master secret rotated. Re-forge required.');
        const choice = await vscode.window.showInformationMessage(
            `FLUX master secret rotated. Copy the new one now; re-forge needed before next use.`,
            { modal: true },
            'Copy to clipboard',
        );
        if (choice === 'Copy to clipboard') {
            await vscode.env.clipboard.writeText(fresh);
        }
    }

    private async startBackend(): Promise<void> {
        const bridge = this.loadBridge();
        if (!bridge) {
            vscode.window.showErrorMessage('FLUX bridge addon not built. Run `bun install` in apps/chthonic-tensor-bridge.');
            return;
        }
        if (this.satelliteRunning) {
            vscode.window.showInformationMessage('FLUX satellite already running.');
            return;
        }
        if (!this.workspaceRoot) {
            vscode.window.showErrorMessage('Open the chthonic-archive workspace first.');
            return;
        }
        const cwd = path.join(this.workspaceRoot, 'apps', 'flux-satellite');
        const uvPath = vscode.workspace.getConfiguration('chthonic.flux').get<string>('uvPath') || 'uv';
        const engineDir = path.join(this.workspaceRoot, 'apps', 'flux-satellite', 'engines');
        const plainPath = path.join(engineDir, `${ENGINE_BASENAME}.engine.plain`);
        const enginePath = path.join(engineDir, `${ENGINE_BASENAME}.engine.enc`);
        const sealPath = path.join(engineDir, `${ENGINE_BASENAME}.seal.json`);
        const ditPipeName = vscode.workspace.getConfiguration('chthonic.flux').get<string>('ditPipeName') || DEFAULT_DIT_PIPE;

        // Two lanes: plaintext (preferred when present, no secret needed) or
        // sealed (encrypted .enc + .seal.json with master secret).
        const havePlain = fs.existsSync(plainPath);
        const haveSealed = fs.existsSync(enginePath) && fs.existsSync(sealPath);

        if (!havePlain && !haveSealed) {
            vscode.window.showErrorMessage(
                `FLUX engine not installed. Expected either ${path.basename(plainPath)} ` +
                `(plain lane) or ${path.basename(enginePath)} + ${path.basename(sealPath)} ` +
                `(sealed lane) in ${engineDir}. ` +
                `Plain lane: \`uv run --directory apps/flux-engine-forge -m flux_engine_forge --install-plain\` ` +
                `after a successful forge.`,
            );
            return;
        }

        // Sealed lane requires the secret in process memory; plain lane does not.
        let loadOpts: { enginePath: string; sealPath?: string; ditPipeName: string };
        let progressTitle: string;
        if (havePlain) {
            loadOpts = { enginePath: plainPath, ditPipeName };
            progressTitle = 'FLUX: loading plain engine + spawning satellite';
        } else {
            const secret = await this.ensureMasterSecret();
            bridge.setMasterSecret(secret);
            loadOpts = { enginePath, sealPath, ditPipeName };
            progressTitle = 'FLUX: unsealing engine + spawning satellite';
        }

        await vscode.window.withProgress(
            { location: vscode.ProgressLocation.Notification, title: progressTitle, cancellable: false },
            async () => {
                try {
                    const loaded = await bridge.loadEngine(loadOpts);
                    this.output.appendLine(`[flux] engine loaded (${havePlain ? 'plain' : 'sealed'}); IO tensors: ${loaded.ioTensors.join(', ')}`);
                    await bridge.startSatellite({ uvPath, cwd, ditPipeName });
                    this.satelliteRunning = true;
                    this.refreshStatusBar();
                    this.publishLauncherState();
                    this.output.appendLine('[flux] satellite running');
                } catch (e) {
                    if (!havePlain) bridge.clearMasterSecret();
                    try { await bridge.unloadEngine(); } catch { /* ignore */ }
                    const err = e as Error & { code?: string };
                    this.output.appendLine(`[flux] start failed: ${err.code ?? ''} ${err.message}`);
                    throw e;
                }
            },
        );
    }

    private async stopBackend(): Promise<void> {
        if (!this.bridge) return;
        if (this.satelliteRunning) {
            try { await this.bridge.stopSatellite(true); } catch { /* ignore */ }
            this.satelliteRunning = false;
        }
        // Unload the engine too. stopSatellite only kills the python satellite;
        // the ~22 GB TRT engine stays resident in the bridge — in VRAM, or in
        // WDDM "shared" host RAM when it overflows the card — until unloadEngine
        // or extension-host death. Without this, "stop" freed nothing and a full
        // VS Code restart was the only way to reclaim the memory. Idempotent:
        // unloadEngine on an empty holder is a no-op, so it also covers the
        // stranded-engine case (engine loaded, satellite never came up).
        try { await this.bridge.unloadEngine(); } catch { /* ignore */ }
        try { this.bridge.clearMasterSecret(); } catch { /* ignore */ }
        this.refreshStatusBar();
        this.publishLauncherState();
        this.output.appendLine('[flux] backend stopped — satellite down, engine unloaded (VRAM / shared RAM freed)');
    }

    // Reap a satellite orphaned by a prior unclean exit. The satellite writes
    // its PID to logs/flux-satellite.pid and unlinks it on clean shutdown
    // (lifecycle.py), so the file's presence at startup means the last run did
    // NOT exit cleanly — a candidate ~6 GB zombie. We only kill a PID that is
    // (a) alive and (b) verified to actually be a flux satellite, so a recycled
    // PID belonging to an unrelated process is never touched. Runs only when the
    // pid file exists, so the verification spawn is off the hot path.
    private reapStaleSatellite(): void {
        if (!this.workspaceRoot) return;
        const pidFile = path.join(this.workspaceRoot, 'apps', 'flux-satellite', 'logs', 'flux-satellite.pid');
        if (!fs.existsSync(pidFile)) return;

        let pid = 0;
        try {
            pid = Number.parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10);
        } catch {
            return;
        }
        const dropPidFile = () => { try { fs.unlinkSync(pidFile); } catch { /* ignore */ } };

        if (!Number.isInteger(pid) || pid <= 0) {
            dropPidFile();
            return;
        }

        // process.kill(pid, 0) probes liveness: throws ESRCH if gone, EPERM if
        // alive but not signalable by us (still counts as alive).
        let alive = true;
        try {
            process.kill(pid, 0);
        } catch (e) {
            alive = (e as NodeJS.ErrnoException).code === 'EPERM';
        }
        if (!alive) {
            dropPidFile();
            this.output.appendLine(`[flux] cleared stale pid file (pid ${pid} not running)`);
            return;
        }

        if (!this.processIsSatellite(pid)) {
            dropPidFile();
            this.output.appendLine(`[flux] pid ${pid} is alive but not a flux satellite — left untouched; stale pid file cleared`);
            return;
        }

        try {
            process.kill(pid);
            this.output.appendLine(`[flux] reaped stale satellite (pid ${pid}; freed the orphaned ~6 GB from a prior unclean exit)`);
        } catch (e) {
            this.output.appendLine(`[flux] could not reap stale satellite pid ${pid}: ${(e as Error).message}`);
        }
        dropPidFile();
    }

    // Confirm a PID is actually our python flux-satellite via CIM command-line
    // match, so a reused PID is never killed. Windows-only; only invoked in the
    // rare zombie case (pid file present).
    private processIsSatellite(pid: number): boolean {
        try {
            const out = execFileSync(
                'powershell',
                [
                    '-NoProfile', '-Command',
                    `(Get-CimInstance Win32_Process -Filter "ProcessId=${pid}" -ErrorAction SilentlyContinue).CommandLine`,
                ],
                { timeout: 5000, encoding: 'utf8', windowsHide: true },
            );
            return /flux_satellite/i.test(out);
        } catch {
            return false;
        }
    }

    private async openPanel(): Promise<void> {
        if (!this.panel) {
            this.panel = new FluxPanel(this.context, this.output, {
                onGenerate: (req) => this.handleGenerate(req),
                onStart: () => this.startBackend(),
                onStop: () => this.stopBackend(),
            });
            this.context.subscriptions.push(this.panel);
        }
        this.panel.reveal();
    }

    private async handleGenerate(req: { prompt: string; steps: number; guidance: number; width: number; height: number; seed: number }) {
        if (!this.satelliteRunning) await this.startBackend();
        const bridge = this.loadBridge();
        if (!bridge) throw new Error('bridge not loaded');
        return bridge.generate(req);
    }
}
