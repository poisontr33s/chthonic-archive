import * as fs from 'fs';
import * as path from 'path';

const extensionRoot = process.cwd();
const chthonicRoot = path.join(extensionRoot, '.chthonic');
const pythonProjectPath = path.join(chthonicRoot, 'python');
const pythonVenvPath = path.join(chthonicRoot, 'venv');
const isWin = process.platform === 'win32';
const pythonExecutable = path.join(pythonVenvPath, isWin ? 'Scripts/python.exe' : 'bin/python');
const ruffExecutable = path.join(pythonVenvPath, isWin ? 'Scripts/ruff.exe' : 'bin/ruff');

async function main(): Promise<void> {
    fs.mkdirSync(chthonicRoot, { recursive: true });

    if (!fs.existsSync(path.join(pythonProjectPath, 'pyproject.toml'))) {
        throw new Error(`missing pyproject: ${path.join(pythonProjectPath, 'pyproject.toml')}`);
    }

    await run(['uv', 'python', 'install', '3.14t']);
    await run(['uv', 'venv', '--clear', pythonVenvPath, '--python', '3.14t']);
    await run(
        ['uv', 'sync', '--project', pythonProjectPath, '--python', pythonExecutable],
        { UV_PROJECT_ENVIRONMENT: pythonVenvPath },
    );

    if (!fs.existsSync(ruffExecutable)) {
        throw new Error(`ruff missing at ${ruffExecutable}`);
    }

    console.log(`[oxidized] Python runtime ready: ${pythonExecutable}`);
    console.log(`[oxidized] Ruff binary ready: ${ruffExecutable}`);
}

async function run(cmd: string[], extraEnv: Record<string, string> = {}): Promise<void> {
    const proc = Bun.spawn(cmd, {
        cwd: extensionRoot,
        stdout: 'inherit',
        stderr: 'inherit',
        stdin: 'inherit',
        env: {
            ...process.env,
            ...extraEnv,
        },
    });
    const code = await proc.exited;
    if (code !== 0) {
        throw new Error(`${cmd.join(' ')} exited with code ${code}`);
    }
}

void main().catch((error) => {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`[oxidized] setup failed: ${message}`);
    process.exitCode = 1;
});
