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

    // nmake fails when GNU make flags leak into the environment.
    delete env.MAKEFLAGS;
    delete env.MFLAGS;

    await run(
        ['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'entropy-ledger-host', '--release'],
        env,
    );
    console.log('[ledger] build completed');
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
    console.error(`[ledger] build failed: ${message}`);
    process.exitCode = 1;
});
