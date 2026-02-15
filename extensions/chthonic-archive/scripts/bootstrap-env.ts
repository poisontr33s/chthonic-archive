import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

const extensionRoot = process.cwd();
const chthonicRoot = path.join(extensionRoot, '.chthonic');
const venvPath = path.join(chthonicRoot, 'venv');
const pythonRequirementsPath = path.join(chthonicRoot, 'python', 'requirements.txt');
const isWin = process.platform === 'win32';
const pythonBinary = path.join(venvPath, isWin ? 'Scripts/python.exe' : 'bin/python');

async function main(): Promise<void> {
    fs.mkdirSync(chthonicRoot, { recursive: true });

    if (!fs.existsSync(pythonRequirementsPath)) {
        console.warn('[bootstrap] .chthonic/python/requirements.txt missing; skipping uv bootstrap.');
        return;
    }

    try {
        if (!fs.existsSync(pythonBinary)) {
            await run('uv', ['venv', venvPath]);
        }
        await run('uv', ['pip', 'sync', '--python', pythonBinary, pythonRequirementsPath]);
        console.log('[bootstrap] uv environment synced under .chthonic/venv');
    } catch (error) {
        console.warn(`[bootstrap] skipped: ${stringifyError(error)}`);
    }
}

function run(command: string, args: string[]): Promise<void> {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: extensionRoot,
            stdio: 'inherit',
        });
        child.on('error', reject);
        child.on('exit', (code) => {
            if (code === 0) {
                resolve();
                return;
            }
            reject(new Error(`${command} ${args.join(' ')} exited with code ${code ?? -1}`));
        });
    });
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

void main();
