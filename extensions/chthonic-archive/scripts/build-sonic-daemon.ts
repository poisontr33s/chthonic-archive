// @SID: EXT_BUILD_SONIC_DAEMON_V1
// Build the sonic-daemon (WASAPI loopback capture). Clone of build-daemon.ts,
// minus the cmake/shaderc check — cpal is pure Rust and needs no C toolchain.
import { existsSync } from 'fs';
import path from 'path';

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

    await run(
        ['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'sonic-daemon', '--release'],
        env,
    );
    console.log('[sonic-daemon] build completed');
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
    console.error(`[sonic-daemon] build failed: ${message}`);
    process.exitCode = 1;
});
