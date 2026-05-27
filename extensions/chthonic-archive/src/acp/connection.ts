// @SID: EXT_CONNECTION_V1
/**
 * ACP Connection — spawns copilot.exe --acp, establishes protocol connection.
 */
import { spawn, ChildProcess } from 'node:child_process';
import { Readable, Writable } from 'node:stream';
import { ClientSideConnection, ndJsonStream, PROTOCOL_VERSION } from '@agentclientprotocol/sdk';
import type { Agent, InitializeResponse, NewSessionResponse, PromptResponse, ContentBlock } from '@agentclientprotocol/sdk';
import { ChthonicAcpClient } from './client';

const COPILOT_PATH = 'C:\\Users\\erdno\\AppData\\Local\\Microsoft\\WinGet\\Packages\\GitHub.Copilot.Prerelease_Microsoft.Winget.Source_8wekyb3d8bbwe\\copilot.exe';

export interface AcpSession {
    sessionId: string;
    agentName: string;
    agentVersion: string;
    cwd: string;
}

export class AcpConnection {
    private process: ChildProcess | null = null;
    private connection: ClientSideConnection | null = null;
    private client: ChthonicAcpClient | null = null;
    private initResponse: InitializeResponse | null = null;
    private session: AcpSession | null = null;
    private outputChannel: any;

    constructor(private readonly log: (msg: string) => void) {}

    /** Spawn copilot --acp and connect */
    async connect(cwd: string): Promise<AcpSession> {
        this.log('Spawning copilot.exe --acp...');

        this.process = spawn(COPILOT_PATH, ['--acp'], {
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd,
            env: { ...process.env },
            shell: true,
        });

        if (!this.process.stdout || !this.process.stdin) {
            throw new Error('Failed to get stdio from copilot process');
        }

        // Forward stderr for debugging
        this.process.stderr?.on('data', (data: Buffer) => {
            const line = data.toString().trim();
            if (line) this.log(`[copilot stderr] ${line}`);
        });

        this.process.on('error', (err) => {
            this.log(`[copilot error] ${err.message}`);
        });

        this.process.on('close', (code) => {
            this.log(`[copilot exited] code=${code}`);
            this.process = null;
        });

        // Create NDJSON stream from stdio
        const readable = Readable.toWeb(this.process.stdout) as ReadableStream<Uint8Array>;
        const writable = Writable.toWeb(this.process.stdin) as WritableStream<Uint8Array>;
        const stream = ndJsonStream(writable, readable);

        // Create client (handles agent→client requests)
        this.client = new ChthonicAcpClient();

        // Create protocol connection
        this.connection = new ClientSideConnection(
            (agent: Agent) => {
                this.client!.setAgent(agent);
                return this.client!;
            },
            stream,
        );

        // Initialize handshake
        this.log('Initializing ACP connection...');
        this.initResponse = await this.connection.initialize({
            protocolVersion: PROTOCOL_VERSION,
            clientInfo: {
                name: 'chthonic-archive',
                version: '0.2.0',
            },
            clientCapabilities: {
                fs: { readTextFile: true, writeTextFile: true },
                terminal: true,
            },
        });

        const agentName = this.initResponse.agentInfo?.name || 'unknown';
        const agentVersion = this.initResponse.agentInfo?.version || '?';
        this.log(`Connected: ${agentName} v${agentVersion}`);

        // Create session
        this.log('Creating ACP session...');
        let sessionResponse: NewSessionResponse;
        try {
            sessionResponse = await this.connection.newSession({ cwd, mcpServers: [] });
        } catch (e: any) {
            // Handle auth_required — open browser for GitHub login
            if (e?.code === -32000 || /auth.?required/i.test(e?.message || '')) {
                const authMethods = this.initResponse.authMethods;
                if (authMethods && authMethods.length > 0) {
                    this.log(`Auth required. Method: ${authMethods[0].name}`);
                    await this.connection.authenticate({ methodId: authMethods[0].id });
                    sessionResponse = await this.connection.newSession({ cwd, mcpServers: [] });
                } else {
                    throw new Error('Auth required but no methods available');
                }
            } else {
                throw e;
            }
        }

        this.session = {
            sessionId: sessionResponse.sessionId,
            agentName,
            agentVersion,
            cwd,
        };

        this.log(`Session: ${this.session.sessionId}`);
        return this.session;
    }

    /** Send a prompt and get streaming response via session updates */
    async prompt(text: string): Promise<PromptResponse> {
        if (!this.connection || !this.session) {
            throw new Error('Not connected');
        }

        const prompt: ContentBlock[] = [{ type: 'text', text }];
        return this.connection.prompt({
            sessionId: this.session.sessionId,
            prompt,
        });
    }

    /** Cancel current turn */
    async cancel(): Promise<void> {
        if (!this.connection || !this.session) return;
        await this.connection.cancel({ sessionId: this.session.sessionId });
    }

    /** Get the client for event subscriptions */
    getClient(): ChthonicAcpClient | null {
        return this.client;
    }

    getSession(): AcpSession | null {
        return this.session;
    }

    getInitResponse(): InitializeResponse | null {
        return this.initResponse;
    }

    isConnected(): boolean {
        return this.process !== null && this.connection !== null && this.session !== null;
    }

    /** Disconnect and kill process */
    disconnect(): void {
        if (this.process) {
            try {
                this.process.kill('SIGTERM');
                setTimeout(() => {
                    if (this.process?.exitCode === null) {
                        this.process?.kill('SIGKILL');
                    }
                }, 5000);
            } catch {}
            this.process = null;
        }
        this.client?.dispose();
        this.connection = null;
        this.session = null;
        this.initResponse = null;
    }
}
