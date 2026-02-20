import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { runTests } from '@vscode/test-electron';

type ExtensionSmokeCase = {
    label: string;
    extensionDevelopmentPath: string;
    extensionId: string;
    expectedCommands: string[];
    smokeCommands: string[];
};

const repoRoot = path.resolve(import.meta.dir, '..', '..', '..');
const runnerPath = path.join(import.meta.dir, 'e2e-smoke-runner.cjs');

const smokeCases: ExtensionSmokeCase[] = [
    {
        label: 'chthonic-archive',
        extensionDevelopmentPath: path.join(repoRoot, 'extensions', 'chthonic-archive'),
        extensionId: 'chthonic-archive.chthonic-archive',
        expectedCommands: [
            'chthonic.verifySSOT',
            'chthonic.refreshStatus',
            'chthonic.refreshRustification',
            'chthonic.openWebCockpit',
            'chthonic.openBunTrainingDocs',
        ],
        smokeCommands: [
            'chthonic.refreshStatus',
            'chthonic.verifySSOT',
            'chthonic.refreshRustification',
        ],
    },
    {
        label: 'chthonic-statusbar',
        extensionDevelopmentPath: path.join(repoRoot, 'extensions', 'chthonic-statusbar'),
        extensionId: 'chthonic-archive.chthonic-statusbar',
        expectedCommands: [
            'chthonic.verifySSO_T',
            'chthonic.runMetabolicCycle',
            'chthonic.showGPUStats',
            'chthonic.runHostVerify',
            'chthonic.openWebCockpitBridge',
            'chthonic.openBunTrainingDocsBridge',
        ],
        smokeCommands: [
            'chthonic.verifySSO_T',
            'chthonic.openWebCockpitBridge',
            'chthonic.openBunTrainingDocsBridge',
        ],
    },
    {
        label: 'chthonic-mandala',
        extensionDevelopmentPath: path.join(repoRoot, 'extensions', 'chthonic-mandala'),
        extensionId: 'chthonic-archive.chthonic-mandala',
        expectedCommands: [
            'chthonic.openMandala',
            'chthonic.openDependencyGraph',
            'chthonic.openHealthReport',
            'chthonic.mandalaBridge.switchTheme',
            'chthonic.mandalaBridge.openWebCockpit',
            'chthonic.mandalaBridge.openBunDocs',
        ],
        smokeCommands: [
            'chthonic.openMandala',
            'chthonic.mandalaBridge.openWebCockpit',
            'chthonic.mandalaBridge.openBunDocs',
        ],
    },
];

async function main(): Promise<void> {
    const vscodeExecutablePath = resolveCodeInsidersExecutable();
    for (const testCase of smokeCases) {
        console.log(`[e2e] running ${testCase.label}`);
        await runTests({
            extensionDevelopmentPath: testCase.extensionDevelopmentPath,
            extensionTestsPath: runnerPath,
            launchArgs: [
                '--new-window',
                '--disable-workspace-trust',
                '--skip-welcome',
                '--skip-release-notes',
                '--disable-updates',
            ],
            vscodeExecutablePath,
            extensionTestsEnv: {
                CHTHONIC_E2E_EXTENSION_ID: testCase.extensionId,
                CHTHONIC_E2E_EXPECTED_COMMANDS: JSON.stringify(testCase.expectedCommands),
                CHTHONIC_E2E_SMOKE_COMMANDS: JSON.stringify(testCase.smokeCommands),
            },
        });
        console.log(`[e2e] pass ${testCase.label}`);
    }
}

function resolveCodeInsidersExecutable(): string | undefined {
    const localAppData = process.env.LOCALAPPDATA;
    if (localAppData) {
        const insidersExe = path.join(
            localAppData,
            'Programs',
            'Microsoft VS Code Insiders',
            'Code - Insiders.exe',
        );
        if (existsSync(insidersExe)) {
            return insidersExe;
        }
    }

    const whereInsiders = spawnSync('where.exe', ['code-insiders'], {
        encoding: 'utf8',
        windowsHide: true,
    });
    if (whereInsiders.status === 0) {
        const firstMatch = whereInsiders.stdout
            .split(/\r?\n/)
            .map((line) => line.trim())
            .find((line) => line.length > 0);
        if (firstMatch && existsSync(firstMatch)) {
            return firstMatch;
        }
    }

    return undefined;
}

main().catch((error) => {
    console.error(`[e2e] failure: ${error instanceof Error ? error.stack ?? error.message : String(error)}`);
    process.exit(1);
});
