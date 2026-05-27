// @SID: EXT_CONNECTION_V1
/**
 * Chthonic SDK Connection — spawns bun harness and communicates via JSON-lines.
 * Replaces the ACP connection (src/acp/connection.ts).
 */
import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as readline from 'readline';
import * as path from 'path';

export interface SdkEvent {
    type: string;
    data: any;
    id?: string;
    timestamp?: string;
}

export interface HarnessMessage {
    type: string;
    id?: string;
    event?: SdkEvent;
    data?: any;
    message?: string;
    login?: string;
    version?: string;
    sdk?: string;
}

type MessageHandler = (msg: HarnessMessage) => void;

export class SdkConnection {
    private process: child_process.ChildProcess | null = null;
    private rl: readline.Interface | null = null;
    private handlers = new Set<MessageHandler>();
    private authenticated = false;
    private ready = false;

    constructor(
        private readonly harnessPath: string,
        private readonly log: (msg: string) => void,
    ) {}

    async start(): Promise<void> {
        if (this.process) return;

        const harnessDir = path.dirname(this.harnessPath);
        const harnessFile = path.basename(this.harnessPath);

        this.process = child_process.spawn('bun', ['run', harnessFile], {
            cwd: harnessDir,
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env },
        });

        this.process.stderr?.on('data', (data: Buffer) => {
            this.log(`[harness stderr] ${data.toString().trim()}`);
        });

        this.process.on('close', (code) => {
            this.log(`[harness] exited with code ${code}`);
            this.process = null;
            this.rl = null;
            this.ready = false;
            this.authenticated = false;
        });

        this.rl = readline.createInterface({ input: this.process.stdout! });
        this.rl.on('line', (line: string) => {
            try {
                const msg: HarnessMessage = JSON.parse(line);
                if (msg.type === 'ready') {
                    this.ready = true;
                    this.log(`[harness] ready: ${msg.sdk}`);
                }
                for (const handler of this.handlers) {
                    handler(msg);
                }
            } catch {
                this.log(`[harness] non-JSON: ${line.substring(0, 200)}`);
            }
        });

        // Wait for ready signal
        await new Promise<void>((resolve, reject) => {
            const timeout = setTimeout(() => reject(new Error('Harness startup timeout')), 15000);
            const check = (msg: HarnessMessage) => {
                if (msg.type === 'ready') {
                    clearTimeout(timeout);
                    this.handlers.delete(check);
                    resolve();
                }
            };
            this.handlers.add(check);
        });
    }

    async authenticate(token: string, login: string): Promise<void> {
        this.send({ cmd: 'auth', token, login });
        await this.waitFor('auth_ok');
        this.authenticated = true;
        this.log(`[harness] authenticated as ${login}`);
    }

    query(
        id: string,
        prompt: string,
        workingDirectory: string,
        onEvent: (event: SdkEvent) => void,
        options?: { model?: string; reasoningEffort?: string },
    ): Promise<void> {
        return new Promise((resolve, reject) => {
            const handler = (msg: HarnessMessage) => {
                if (msg.id !== id) return;
                if (msg.type === 'event' && msg.event) {
                    onEvent(msg.event);
                } else if (msg.type === 'done') {
                    this.handlers.delete(handler);
                    resolve();
                } else if (msg.type === 'cancelled') {
                    this.handlers.delete(handler);
                    resolve();
                } else if (msg.type === 'error') {
                    this.handlers.delete(handler);
                    reject(new Error(msg.message || 'Query failed'));
                }
            };
            this.handlers.add(handler);

            this.send({
                cmd: 'query',
                id,
                prompt,
                workingDirectory,
                model: options?.model,
                reasoningEffort: options?.reasoningEffort,
            });
        });
    }

    cancel(id: string): void {
        this.send({ cmd: 'cancel', id });
    }

    async getModels(): Promise<any[]> {
        this.send({ cmd: 'models' });
        const msg = await this.waitFor('models');
        return msg.data || [];
    }

    isReady(): boolean {
        return this.ready && this.authenticated && this.process !== null;
    }

    stop(): void {
        if (this.process) {
            this.process.kill();
            this.process = null;
        }
        this.rl = null;
        this.ready = false;
        this.authenticated = false;
        this.handlers.clear();
    }

    private send(obj: any): void {
        if (!this.process?.stdin?.writable) {
            throw new Error('Harness not running');
        }
        this.process.stdin.write(JSON.stringify(obj) + '\n');
    }

    private waitFor(type: string, timeout = 15000): Promise<HarnessMessage> {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.handlers.delete(handler);
                reject(new Error(`Timeout waiting for ${type}`));
            }, timeout);
            const handler = (msg: HarnessMessage) => {
                if (msg.type === type) {
                    clearTimeout(timer);
                    this.handlers.delete(handler);
                    resolve(msg);
                } else if (msg.type === 'error') {
                    clearTimeout(timer);
                    this.handlers.delete(handler);
                    reject(new Error(msg.message || 'Error'));
                }
            };
            this.handlers.add(handler);
        });
    }
}
