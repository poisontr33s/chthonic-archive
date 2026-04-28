// @SID: EXT_E2E_EXTENSION_HOST_V1
import { existsSync } from 'node:fs';
import path from 'node:path';
import { runTests } from '@vscode/test-electron';

type ExtensionSmokeCase = {
    label: string;
    extensionDevelopmentPath: string;
    extensionId: string;
    workspacePath?: string;
    workspaceSettings?: Record<string, unknown>;
    expectedCommands: string[];
    smokeCommands: string[];
};

const repoRoot = path.resolve(import.meta.dir, '..', '..', '..');
const runnerPath = path.join(import.meta.dir, 'e2e-smoke-runner.cjs');
const daemonBinary = process.platform === 'win32' ? 'chthonic-daemon.exe' : 'chthonic-daemon';

const smokeCases: ExtensionSmokeCase[] = [
    {
        label: 'chthonic-archive',
        extensionDevelopmentPath: path.join(repoRoot, 'extensions', 'chthonic-archive'),
        extensionId: 'chthonic-archive.chthonic-archive',
        workspacePath: repoRoot,
        workspaceSettings: {
            'security.allowNativeSidecars': true,
            'reactor.enabled': true,
            'reactor.headlessVulkan': false,
            'reactor.transport': 'jsonl',
            'reactor.daemonBinaryPath': path.join(repoRoot, 'extensions', 'chthonic-archive', 'native', 'target', 'debug', daemonBinary),
        },
        expectedCommands: [
            'chthonic.openStylusInput',
            'chthonic.entropyRefresh',
            'chthonic.activateCockpit',
            'chthonic.deepFocus',
            'chthonic.restoreOrder',
            'chthonic.slabHeal',
            'chthonic.refreshRustification',
            'chthonic.annoDetect',
            'chthonic.reactorSediment',
            'chthonic.openWebCockpit',
            'chthonic.startWebCockpit',
            'chthonic.openBunTrainingDocs',
            'chthonic.postRestartVerify',
            'chthonic.restartGate',
            'chthonic.runtimeStatus',
            'chthonic.switchTheme',
            'chthonic.verifySSOT',
            'chthonic.refreshStatus',
            'chthonic.pasteRenderedAiMarkdown',
        ],
        smokeCommands: [
            'chthonic.refreshStatus',
            'chthonic.verifySSOT',
            'chthonic.refreshRustification',
            'chthonic.runtimeStatus',
            'chthonic.entropyRefresh',
            'chthonic.annoDetect',
            'chthonic.reactorSediment',
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
    const vscodeExecutablePath = resolveInsidersCli();
    if (!vscodeExecutablePath) {
        throw new Error('Unable to resolve VS Code Insiders CLI (code-insiders.cmd)');
    }

    for (const testCase of smokeCases) {
        console.log(`[e2e] running ${testCase.label}`);
        const launchArgs = [
            '--new-window',
            '--disable-workspace-trust',
            '--skip-welcome',
            '--skip-release-notes',
            '--disable-updates',
        ];
        if (testCase.workspacePath) {
            launchArgs.push(testCase.workspacePath);
        }
        await runTests({
            extensionDevelopmentPath: testCase.extensionDevelopmentPath,
            extensionTestsPath: runnerPath,
            launchArgs,
            vscodeExecutablePath,
            extensionTestsEnv: {
                CHTHONIC_E2E_EXTENSION_ID: testCase.extensionId,
                CHTHONIC_E2E_EXPECTED_COMMANDS: JSON.stringify(testCase.expectedCommands),
                CHTHONIC_E2E_SMOKE_COMMANDS: JSON.stringify(testCase.smokeCommands),
                CHTHONIC_E2E_WORKSPACE_SETTINGS: JSON.stringify(testCase.workspaceSettings ?? {}),
            },
        });
        console.log(`[e2e] pass ${testCase.label}`);
    }
}

function resolveInsidersCli(): string | null {
    const localAppData = process.env.LOCALAPPDATA;
    if (!localAppData) {
        return null;
    }

    const insidersCli = path.join(
        localAppData,
        'Programs',
        'Microsoft VS Code Insiders',
        'bin',
        'code-insiders.cmd',
    );
    if (existsSync(insidersCli)) {
        return insidersCli;
    }

    return null;
}

main().catch((error) => {
    console.error(`[e2e] failure: ${error instanceof Error ? error.stack ?? error.message : String(error)}`);
    process.exit(1);
});
