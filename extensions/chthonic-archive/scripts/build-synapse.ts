import { copyFileSync, existsSync, mkdirSync } from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';

const extensionRoot = process.cwd();
const workspaceManifestPath = path.join(extensionRoot, 'native', 'Cargo.toml');
const outPath = path.join(extensionRoot, 'src', 'reactor', 'synapse.node');

async function main(): Promise<void> {
    if (!existsSync(workspaceManifestPath)) {
        throw new Error(`missing Rust workspace manifest: ${workspaceManifestPath}`);
    }

    const env: Record<string, string> = { ...process.env };
    delete env.MAKEFLAGS;
    delete env.MFLAGS;

    run(['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'synapse-node', '--release'], env);

    const artifact = resolveArtifactPath();
    if (!existsSync(artifact)) {
        throw new Error(`synapse-node artifact not found: ${artifact}`);
    }

    mkdirSync(path.dirname(outPath), { recursive: true });
    copyFileSync(artifact, outPath);
    console.log(`[synapse] copied ${artifact} -> ${outPath}`);
}

function resolveArtifactPath(): string {
    const releaseDir = path.join(extensionRoot, 'native', 'target', 'release');
    switch (process.platform) {
        case 'win32':
            return path.join(releaseDir, 'synapse_node.dll');
        case 'darwin':
            return path.join(releaseDir, 'libsynapse_node.dylib');
        default:
            return path.join(releaseDir, 'libsynapse_node.so');
    }
}

function run(cmd: string[], env: Record<string, string>): void {
    const result = spawnSync(cmd[0], cmd.slice(1), {
        cwd: extensionRoot,
        env,
        stdio: 'inherit',
    });
    if (result.status !== 0) {
        throw new Error(`${cmd.join(' ')} exited with code ${result.status ?? -1}`);
    }
}

void main().catch((error) => {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`[synapse] build failed: ${message}`);
    process.exitCode = 1;
});
