// @SID: EXT_WEBVIEW_HMR_SMOKE_V1
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { runTests } from '@vscode/test-electron';

const repoRoot = path.resolve(import.meta.dir, '..', '..', '..');
const extensionDevelopmentPath = path.join(repoRoot, 'extensions', 'chthonic-archive');
const runnerPath = path.join(import.meta.dir, 'webview-hmr-smoke-runner.cjs');

async function main(): Promise<void> {
    const surfaces = resolveSurfaces();
    const resultPath = process.env.CHTHONIC_WEBVIEW_HMR_RESULT
        ?? path.join(repoRoot, 'manifest', `webview_hmr_smoke_${surfaces.join('_')}.json`);
    console.log(`[webview-hmr] surfaces=${surfaces.join(',')}`);
    console.log(`[webview-hmr] result=${resultPath}`);

    delete process.env.ELECTRON_RUN_AS_NODE;
    delete process.env.VSCODE_DEV;

    await runTests({
        extensionDevelopmentPath,
        extensionTestsPath: runnerPath,
        version: 'stable',
        platform: 'win32-x64-archive',
        launchArgs: [
            '--new-window',
            '--disable-workspace-trust',
            '--skip-welcome',
            '--skip-release-notes',
            '--disable-updates',
            repoRoot,
        ],
        extensionTestsEnv: {
            CHTHONIC_WEBVIEW_HMR_SURFACES: JSON.stringify(surfaces),
            CHTHONIC_WEBVIEW_HMR_RESULT: resultPath,
            CHTHONIC_E2E_EXTENSION_ID: 'chthonic-archive.chthonic-archive',
        },
    });

    if (!existsSync(resultPath)) {
        throw new Error(`Webview HMR smoke completed without writing result artifact: ${resultPath}`);
    }
    console.log(readFileSync(resultPath, 'utf8'));
}

function resolveSurfaces(): string[] {
    const surfaceArg = process.argv.find((arg) => arg.startsWith('--surface='));
    const surfacesArg = process.argv.find((arg) => arg.startsWith('--surfaces='));
    const raw = surfaceArg?.slice('--surface='.length) ?? surfacesArg?.slice('--surfaces='.length);
    if (!raw) {
        return ['stylus', 'loom', 'ankh', 'abyssal'];
    }
    return raw
        .split(',')
        .map((surface) => surface.trim())
        .filter(Boolean);
}

main().catch((error) => {
    console.error(`[webview-hmr] failure: ${error instanceof Error ? error.stack ?? error.message : String(error)}`);
    process.exit(1);
});
