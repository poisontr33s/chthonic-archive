import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

const extensionRoot = process.cwd();
const chthonicRoot = path.join(extensionRoot, '.chthonic');
const pythonProjectPath = path.join(chthonicRoot, 'python');
const venvPath = path.join(chthonicRoot, 'venv');
const isWin = process.platform === 'win32';
const pythonBinary = path.join(venvPath, isWin ? 'Scripts/python.exe' : 'bin/python');

async function main(): Promise<void> {
    fs.mkdirSync(chthonicRoot, { recursive: true });
    const pyprojectPath = path.join(pythonProjectPath, 'pyproject.toml');

    if (!fs.existsSync(pyprojectPath)) {
        console.warn(`[bootstrap] missing ${pyprojectPath}; skipping Python setup.`);
        return;
    }

    try {
        await run('uv', ['python', 'install', '3.14t']);
    } catch (error) {
        console.warn(`[bootstrap] uv python install 3.14t skipped: ${stringifyError(error)}`);
    }

    try {
        await run('uv', ['venv', '--clear', venvPath, '--python', '3.14t']);
    } catch (error) {
        console.warn(`[bootstrap] creating 3.14t venv failed, falling back to default interpreter: ${stringifyError(error)}`);
        await run('uv', ['venv', '--clear', venvPath]);
    }

    await run('uv', [
        'sync',
        '--project',
        pythonProjectPath,
        '--python',
        pythonBinary,
    ], {
        UV_PROJECT_ENVIRONMENT: venvPath,
    });

    console.log('[bootstrap] .chthonic/venv synced from pyproject via uv');
}

function run(command: string, args: string[], env: Record<string, string> = {}): Promise<void> {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: extensionRoot,
            stdio: 'inherit',
            env: {
                ...process.env,
                ...env,
            },
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

void main().catch((error) => {
    console.warn(`[bootstrap] skipped: ${stringifyError(error)}`);
});
