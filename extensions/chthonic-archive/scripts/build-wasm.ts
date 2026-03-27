// @SID: EXT_BUILD_WASM_V1
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';

const extensionRoot = process.cwd();
const workspaceManifestPath = path.join(extensionRoot, 'native', 'Cargo.toml');
const targetDir = path.join(extensionRoot, 'native', 'target');
const wasmOutDir = path.join(extensionRoot, 'media', 'wasm', 'pkg');
const wasmTargets: readonly WasmTarget[] = [
    {
        packageName: 'entropy_renderer_wasm',
        artifactName: 'entropy_renderer_wasm',
    },
    {
        packageName: 'chthonic_loom',
        artifactName: 'chthonic_loom',
    },
];

async function main(): Promise<void> {
    if (!fs.existsSync(workspaceManifestPath)) {
        throw new Error(`missing Rust workspace manifest: ${workspaceManifestPath}`);
    }
    const hasWasmTarget = await isWasmTargetInstalled();
    if (!hasWasmTarget) {
        throw new Error('missing rust target wasm32-unknown-unknown. Run: rustup target add wasm32-unknown-unknown');
    }

    fs.mkdirSync(wasmOutDir, { recursive: true });

    const wasmOptAvailable = await hasWasmOpt();

    for (const target of wasmTargets) {
        const artifactPath = path.join(
            targetDir,
            'wasm32-unknown-unknown',
            'release',
            `${target.artifactName}.wasm`,
        );

        await run('cargo', [
            'build',
            '--manifest-path',
            workspaceManifestPath,
            '-p',
            target.packageName,
            '--target',
            'wasm32-unknown-unknown',
            '--release',
        ]);

        await run('wasm-bindgen', [
            '--target',
            'web',
            '--out-dir',
            wasmOutDir,
            artifactPath,
        ]);

        if (wasmOptAvailable) {
            const boundWasmPath = path.join(wasmOutDir, `${target.artifactName}_bg.wasm`);
            await run('wasm-opt', ['-Oz', boundWasmPath, '-o', boundWasmPath]);
        }
    }

    console.log(`[wasm] generated bindings at ${wasmOutDir}`);
}

type WasmTarget = {
    packageName: string;
    artifactName: string;
};

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

async function isWasmTargetInstalled(): Promise<boolean> {
    const output = await runCapture('rustup', ['target', 'list', '--installed']);
    if (!output.ok) {
        return false;
    }
    return output.stdout.includes('wasm32-unknown-unknown');
}

async function hasWasmOpt(): Promise<boolean> {
    const output = await runCapture('wasm-opt', ['--version']);
    return output.ok;
}

function runCapture(command: string, args: string[]): Promise<{ ok: boolean; stdout: string; stderr: string }> {
    return new Promise((resolve) => {
        const child = spawn(command, args, {
            cwd: extensionRoot,
            stdio: ['ignore', 'pipe', 'pipe'],
        });
        const stdout: string[] = [];
        const stderr: string[] = [];
        child.stdout?.on('data', (chunk: Buffer) => stdout.push(chunk.toString()));
        child.stderr?.on('data', (chunk: Buffer) => stderr.push(chunk.toString()));
        child.on('error', () => {
            resolve({
                ok: false,
                stdout: stdout.join(''),
                stderr: stderr.join(''),
            });
        });
        child.on('exit', (code) => {
            resolve({
                ok: code === 0,
                stdout: stdout.join(''),
                stderr: stderr.join(''),
            });
        });
    });
}

void main().catch((error) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(`[wasm] build failed: ${message}`);
    process.exitCode = 1;
});
