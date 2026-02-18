import { existsSync } from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';

const extensionRoot = process.cwd();
const workspaceManifestPath = path.join(extensionRoot, 'native', 'Cargo.toml');

async function main(): Promise<void> {
    if (!existsSync(workspaceManifestPath)) {
        throw new Error(`missing Rust workspace manifest: ${workspaceManifestPath}`);
    }

    const env: Record<string, string> = {
        ...process.env,
    };

    // nmake fails when GNU make flags leak from parent shells.
    delete env.MAKEFLAGS;
    delete env.MFLAGS;

    // shaderc-sys requires cmake
    ensureCmake(env);

    await run(
        ['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'chthonic-daemon', '--release'],
        env,
    );
    console.log('[daemon] build completed');
}

function ensureCmake(env: Record<string, string>): void {
    const result = runCapture('cmake', ['--version'], env);
    if (!result.ok) {
        throw new Error(
            'cmake not found. shaderc requires cmake for SPIR-V compilation.\n'
            + 'Install: winget install Kitware.CMake (Windows) or apt install cmake (Linux)',
        );
    }
    console.log(`[daemon] cmake: ${result.stdout.split('\n')[0].trim()}`);
}

function runCapture(command: string, args: string[], env: Record<string, string>): {
    ok: boolean;
    stdout: string;
    stderr: string;
} {
    try {
        const result = spawnSync(command, args, {
            cwd: extensionRoot,
            env,
            encoding: 'utf8',
        });
        return {
            ok: result.status === 0,
            stdout: result.stdout ?? '',
            stderr: result.stderr ?? '',
        };
    } catch {
        return {
            ok: false,
            stdout: '',
            stderr: '',
        };
    }
}

async function run(cmd: string[], env: Record<string, string>): Promise<void> {
    const proc = Bun.spawn(cmd, {
        cwd: extensionRoot,
        stdout: 'inherit',
        stderr: 'inherit',
        stdin: 'inherit',
        env,
    });
    const code = await proc.exited;
    if (code !== 0) {
        throw new Error(`${cmd.join(' ')} exited with code ${code}`);
    }
}

void main().catch((error) => {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`[daemon] build failed: ${message}`);
    process.exitCode = 1;
});
