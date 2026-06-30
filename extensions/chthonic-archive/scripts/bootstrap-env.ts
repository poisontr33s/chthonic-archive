// @SID: EXT_BOOTSTRAP_ENV_V1
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

const extensionRoot = process.cwd();
const chthonicRoot = path.join(extensionRoot, '.chthonic');
const pythonProjectPath = path.join(chthonicRoot, 'python');
const venvPath = path.join(chthonicRoot, 'venv');
const rubyProjectPath = path.join(chthonicRoot, 'ruby');
const rubyGemfilePath = path.join(rubyProjectPath, 'Gemfile');
const rubyBundlePath = path.join(rubyProjectPath, 'vendor', 'bundle');
const isWin = process.platform === 'win32';
const pythonBinary = path.join(venvPath, isWin ? 'Scripts/python.exe' : 'bin/python');
const rvCommand = resolveCommand(isWin ? 'rvw' : 'rv', isWin ? ['rvw.exe', 'rv.exe', 'rvw.cmd', 'rv.cmd', 'rvw.bat', 'rv.bat'] : ['rv']);

async function main(): Promise<void> {
    fs.mkdirSync(chthonicRoot, { recursive: true });
    const pyprojectPath = path.join(pythonProjectPath, 'pyproject.toml');

    try {
        await run('bun', ['run', 'scripts/toolpool-scan.ts', '--write-env', '--quiet']);
    } catch (error) {
        console.warn(`[bootstrap] tool-pool scan skipped: ${stringifyError(error)}`);
    }

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

    if (fs.existsSync(rubyGemfilePath)) {
        try {
            await run(rvCommand, ['r', '--no-install', 'bundle', 'install', '--gemfile', rubyGemfilePath], {
                BUNDLE_GEMFILE: rubyGemfilePath,
                BUNDLE_PATH: rubyBundlePath,
            });
            console.log('[bootstrap] Ruby gems installed from .chthonic/ruby/Gemfile');
        } catch (error) {
            console.warn(`[bootstrap] ruby bundle install skipped: ${stringifyError(error)}`);
        }
    }
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

function resolveCommand(command: string, candidates: string[]): string {
    const pathValue = process.env.PATH ?? '';
    for (const entry of pathValue.split(path.delimiter)) {
        if (!entry) {
            continue;
        }

        for (const candidate of candidates) {
            const fullPath = path.join(entry, candidate);
            if (fs.existsSync(fullPath)) {
                return fullPath;
            }
        }
    }

    return command;
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
