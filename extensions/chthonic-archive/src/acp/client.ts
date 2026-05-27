// @SID: EXT_CLIENT_V1
/**
 * ACP Client Implementation — handles requests FROM the agent TO us.
 * The agent asks us to read/write files, create terminals, approve permissions.
 */
import * as vscode from 'vscode';
import type {
    Client,
    Agent,
    RequestPermissionRequest,
    RequestPermissionResponse,
    SessionNotification,
    WriteTextFileRequest,
    WriteTextFileResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    CreateTerminalRequest,
    CreateTerminalResponse,
    TerminalOutputRequest,
    TerminalOutputResponse,
    WaitForTerminalExitRequest,
    WaitForTerminalExitResponse,
    KillTerminalCommandRequest,
    KillTerminalCommandResponse,
    ReleaseTerminalRequest,
    ReleaseTerminalResponse,
} from '@agentclientprotocol/sdk';

import { EventEmitter } from 'node:events';

export class ChthonicAcpClient extends EventEmitter implements Client {
    private agent: Agent | null = null;
    private terminals: Map<string, vscode.Terminal> = new Map();
    private terminalExitCodes: Map<string, number | undefined> = new Map();
    private nextTerminalId = 1;

    setAgent(agent: Agent): void {
        this.agent = agent;
    }

    getAgent(): Agent | null {
        return this.agent;
    }

    // --- Permission ---
    async requestPermission(params: RequestPermissionRequest): Promise<RequestPermissionResponse> {
        // Auto-approve everything — the agent is us, running locally.
        const allowOption = params.options.find((option) => option.kind.startsWith('allow'));
        if (allowOption) {
            return {
                outcome: {
                    outcome: 'selected',
                    optionId: allowOption.optionId,
                },
            };
        }
        return { outcome: { outcome: 'cancelled' } };
    }

    // --- Session Updates (streamed from agent) ---
    async sessionUpdate(params: SessionNotification): Promise<void> {
        this.emit('session-update', params);
    }

    // --- Filesystem ---
    async readTextFile(params: ReadTextFileRequest): Promise<ReadTextFileResponse> {
        const uri = vscode.Uri.file(params.path);
        const data = await vscode.workspace.fs.readFile(uri);
        return { content: Buffer.from(data).toString('utf-8') };
    }

    async writeTextFile(params: WriteTextFileRequest): Promise<WriteTextFileResponse> {
        const uri = vscode.Uri.file(params.path);
        await vscode.workspace.fs.writeFile(uri, Buffer.from(params.content, 'utf-8'));
        return {};
    }

    // --- Terminal ---
    async createTerminal(params: CreateTerminalRequest): Promise<CreateTerminalResponse> {
        const id = `term_${this.nextTerminalId++}`;
        const cwd = params.cwd ?? undefined;
        const terminal = vscode.window.createTerminal({
            name: `☥ Agent: ${params.command}`,
            cwd,
        });

        this.terminals.set(id, terminal);

        // Send the command
        const fullCmd = [params.command, ...(params.args || [])].join(' ');
        terminal.sendText(fullCmd);

        return { terminalId: id };
    }

    async terminalOutput(_params: TerminalOutputRequest): Promise<TerminalOutputResponse> {
        // VS Code API doesn't expose terminal output directly
        return { output: '', truncated: false };
    }

    async waitForTerminalExit(params: WaitForTerminalExitRequest): Promise<WaitForTerminalExitResponse> {
        const exitCode = this.terminalExitCodes.get(params.terminalId);
        return { exitCode: exitCode ?? 0 };
    }

    async killTerminal(params: KillTerminalCommandRequest): Promise<KillTerminalCommandResponse> {
        const terminal = this.terminals.get(params.terminalId);
        if (terminal) {
            terminal.dispose();
            this.terminals.delete(params.terminalId);
        }
        return {};
    }

    async releaseTerminal(params: ReleaseTerminalRequest): Promise<ReleaseTerminalResponse> {
        this.terminals.delete(params.terminalId);
        return {};
    }

    dispose(): void {
        for (const terminal of this.terminals.values()) {
            terminal.dispose();
        }
        this.terminals.clear();
    }
}
