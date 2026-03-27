// @SID: EXT_INSIDERS_POST_RESTART_VERIFY_V1
import { spawnSync } from 'bun';
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'fs';
import path from 'path';

type StepResult = {
    name: string;
    command: string[];
    cwd: string;
    exitCode: number;
    durationMs: number;
    stdout: string;
    stderr: string;
};

type ExtensionVersion = {
    id: string;
    version: string;
};

type ChangeRecord = {
    id: string;
    before: string;
    after: string;
};

type InsidersChangeRecord = {
    before: string[];
    after: string[];
};

type RestartGate = {
    required: boolean;
    reasons: string[];
    currentCommit: string | null;
    latestCommitOnDisk: string | null;
    duplicateExtensionInstalls: string[];
};

type Snapshot = {
    generatedAt: string;
    sequence: string[];
    insidersVersion: string[];
    restartGate: RestartGate;
    insidersChangedSincePrevious: InsidersChangeRecord | null;
    installedExtensions: ExtensionVersion[];
    changedSincePrevious: ChangeRecord[];
    verification: {
        performed: boolean;
        skippedReason: string | null;
    };
    stepResults: StepResult[];
};

const extensionRoot = process.cwd();
const repoRoot = path.resolve(extensionRoot, '..', '..');
const cacheDir = path.join(extensionRoot, '.chthonic', 'cache');

const latestSnapshotPath = path.join(cacheDir, 'insiders-post-restart-verify-latest.json');
const runStamp = new Date().toISOString().replace(/[.:]/g, '-');
const stampedSnapshotPath = path.join(cacheDir, `insiders-post-restart-verify-${runStamp}.json`);

function argValue(flag: string): string | null {
    const direct = process.argv.find((value) => value.startsWith(`${flag}=`));
    if (direct) {
        return direct.slice(`${flag}=`.length);
    }
    const index = process.argv.indexOf(flag);
    if (index >= 0 && process.argv[index + 1]) {
        return process.argv[index + 1];
    }
    return null;
}

const mode = {
    gateOnly: process.argv.includes('--gate-only'),
    allowStale: process.argv.includes('--allow-stale'),
    force: process.argv.includes('--force'),
    withAiLanes: process.argv.includes('--with-ai-lanes'),
    artCopNoLlm: process.argv.includes('--artcop-no-llm'),
    artCopImages: argValue('--artcop-images'),
    artCopImagesDir: argValue('--artcop-images-dir'),
    artCopMaxImages: argValue('--artcop-max-images'),
    rankLimit: argValue('--rank-limit'),
    rankVramGb: argValue('--rank-vram-gb'),
};

function runCommand(name: string, command: string[], cwd: string): StepResult {
    const startedAt = Date.now();
    const run = spawnSync(command, {
        cwd,
        stdout: 'pipe',
        stderr: 'pipe',
        windowsHide: true,
    });
    const durationMs = Date.now() - startedAt;
    const stdout = Buffer.from(run.stdout).toString();
    const stderr = Buffer.from(run.stderr).toString();
    const exitCode = run.exitCode ?? 1;

    console.log(`\n[post-restart] ${name}`);
    console.log(`[post-restart] cwd=${cwd}`);
    console.log(`[post-restart] cmd=${command.join(' ')}`);
    if (stdout.trim().length > 0) {
        console.log(stdout.trimEnd());
    }
    if (stderr.trim().length > 0) {
        console.error(stderr.trimEnd());
    }

    if (exitCode !== 0) {
        throw new Error(`${name} failed with exit code ${exitCode}`);
    }

    return {
        name,
        command,
        cwd,
        exitCode,
        durationMs,
        stdout,
        stderr,
    };
}

function runOptionalCommand(name: string, command: string[], cwd: string): StepResult {
    try {
        return runCommand(name, command, cwd);
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        console.warn(`\n[post-restart] optional step failed: ${name}`);
        console.warn(`[post-restart] ${message}`);
        return {
            name: `${name} (optional-failed)`,
            command,
            cwd,
            exitCode: 1,
            durationMs: 0,
            stdout: '',
            stderr: message,
        };
    }
}

function parseExtensions(output: string): ExtensionVersion[] {
    return output
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
            const at = line.lastIndexOf('@');
            if (at <= 0) {
                return null;
            }
            return {
                id: line.slice(0, at),
                version: line.slice(at + 1),
            };
        })
        .filter((entry): entry is ExtensionVersion => entry !== null)
        .sort((left, right) => left.id.localeCompare(right.id));
}

function readPreviousSnapshot(): Snapshot | null {
    if (!existsSync(latestSnapshotPath)) {
        return null;
    }
    try {
        const raw = readFileSync(latestSnapshotPath, 'utf8');
        return JSON.parse(raw) as Snapshot;
    } catch {
        return null;
    }
}

function computeChanges(previous: Snapshot | null, current: ExtensionVersion[]): ChangeRecord[] {
    if (!previous) {
        return [];
    }

    const oldMap = new Map<string, string>();
    for (const entry of previous.installedExtensions) {
        oldMap.set(entry.id, entry.version);
    }

    const changes: ChangeRecord[] = [];
    for (const entry of current) {
        const previousVersion = oldMap.get(entry.id);
        if (!previousVersion) {
            changes.push({
                id: entry.id,
                before: '(not-installed)',
                after: entry.version,
            });
            continue;
        }
        if (previousVersion !== entry.version) {
            changes.push({
                id: entry.id,
                before: previousVersion,
                after: entry.version,
            });
        }
    }
    return changes.sort((left, right) => left.id.localeCompare(right.id));
}

function computeInsidersChange(previous: Snapshot | null, current: string[]): InsidersChangeRecord | null {
    if (!previous) {
        return null;
    }

    const before = previous.insidersVersion ?? [];
    const sameLength = before.length === current.length;
    const sameValues = sameLength && before.every((value, index) => value === current[index]);
    if (sameValues) {
        return null;
    }

    return {
        before,
        after: current,
    };
}

function parseCurrentCommit(insidersVersion: string[]): string | null {
    const candidate = insidersVersion[1]?.trim();
    if (!candidate || !/^[0-9a-f]{40}$/i.test(candidate)) {
        return null;
    }
    return candidate;
}

function findLatestCommitOnDisk(): string | null {
    const localAppData = process.env.LOCALAPPDATA;
    if (!localAppData) {
        return null;
    }
    const installRoot = path.join(localAppData, 'Programs', 'Microsoft VS Code Insiders');
    if (!existsSync(installRoot)) {
        return null;
    }

    const commitDirs = readdirSync(installRoot, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() && /^[0-9a-f]{10}$/i.test(entry.name))
        .map((entry) => ({
            shortCommit: entry.name,
            mtimeMs: statSync(path.join(installRoot, entry.name)).mtimeMs,
        }))
        .sort((left, right) => right.mtimeMs - left.mtimeMs);

    return commitDirs[0]?.shortCommit ?? null;
}

function parseExtensionFolderIdentity(folderName: string): string | null {
    const parts = folderName.split('-');
    for (let i = parts.length - 1; i >= 1; i -= 1) {
        if (/^\d/.test(parts[i])) {
            return parts.slice(0, i).join('-');
        }
    }
    return null;
}

function findDuplicateExtensionInstalls(): string[] {
    const home = process.env.USERPROFILE ?? process.env.HOME;
    if (!home) {
        return [];
    }
    const extensionRoot = path.join(home, '.vscode-insiders', 'extensions');
    if (!existsSync(extensionRoot)) {
        return [];
    }

    const groups = new Map<string, number>();
    for (const entry of readdirSync(extensionRoot, { withFileTypes: true })) {
        if (!entry.isDirectory()) {
            continue;
        }
        const id = parseExtensionFolderIdentity(entry.name);
        if (!id) {
            continue;
        }
        groups.set(id, (groups.get(id) ?? 0) + 1);
    }

    return [...groups.entries()]
        .filter(([, count]) => count > 1)
        .map(([id]) => id)
        .sort((left, right) => left.localeCompare(right));
}

function computeRestartGate(insidersVersion: string[]): RestartGate {
    const reasons: string[] = [];
    const currentCommit = parseCurrentCommit(insidersVersion);
    const currentShortCommit = currentCommit ? currentCommit.slice(0, 10) : null;
    const latestCommitOnDisk = findLatestCommitOnDisk();
    const duplicateExtensionInstalls = findDuplicateExtensionInstalls();

    if (currentShortCommit && latestCommitOnDisk && currentShortCommit !== latestCommitOnDisk) {
        reasons.push(
            `VS Code Insiders pending product update detected (running=${currentShortCommit}, staged=${latestCommitOnDisk})`,
        );
    }

    if (duplicateExtensionInstalls.length > 0) {
        reasons.push(`duplicate extension installs detected: ${duplicateExtensionInstalls.join(', ')}`);
    }

    return {
        required: reasons.length > 0,
        reasons,
        currentCommit,
        latestCommitOnDisk,
        duplicateExtensionInstalls,
    };
}

function writeSnapshot(snapshot: Snapshot): void {
    mkdirSync(cacheDir, { recursive: true });
    const data = `${JSON.stringify(snapshot, null, 2)}\n`;
    writeFileSync(stampedSnapshotPath, data, 'utf8');
    writeFileSync(latestSnapshotPath, data, 'utf8');
}

function run(): void {
    console.log('[post-restart] sequence contract');
    console.log('[post-restart] 1) Restart VS Code Insiders for product update');
    console.log('[post-restart] 2) Restart extension(s) from cogwheel if prompted');
    console.log('[post-restart] 3) Run this lane to verify what changed');

    const previous = readPreviousSnapshot();
    const stepResults: StepResult[] = [];

    const insidersVersion = runCommand(
        'VS Code Insiders version',
        ['code-insiders', '--version'],
        repoRoot,
    );
    stepResults.push(insidersVersion);

    const extensionList = runCommand(
        'VS Code Insiders extension versions',
        ['code-insiders', '--list-extensions', '--show-versions'],
        repoRoot,
    );
    stepResults.push(extensionList);

    const parsedInsidersVersion = insidersVersion.stdout
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
    const installedExtensions = parseExtensions(extensionList.stdout);
    const restartGate = computeRestartGate(parsedInsidersVersion);
    const insidersChangedSincePrevious = computeInsidersChange(previous, parsedInsidersVersion);
    const changedSincePrevious = computeChanges(previous, installedExtensions);
    const hasUpdateDelta = Boolean(insidersChangedSincePrevious) || changedSincePrevious.length > 0;

    console.log(`[post-restart] restart required (pending updates): ${restartGate.required ? 'yes' : 'no'}`);
    if (restartGate.reasons.length > 0) {
        for (const reason of restartGate.reasons) {
            console.log(`[post-restart] restart reason: ${reason}`);
        }
    }

    if (mode.gateOnly || (restartGate.required && !mode.allowStale)) {
        const skippedReason = mode.gateOnly
            ? 'gate-only mode'
            : 'restart-required-before-verify';
        const snapshot: Snapshot = {
            generatedAt: new Date().toISOString(),
            sequence: mode.gateOnly
                ? ['check-restart-gate']
                : ['pending-update-detected', 'restart-required-before-verify'],
            insidersVersion: parsedInsidersVersion,
            restartGate,
            insidersChangedSincePrevious,
            installedExtensions,
            changedSincePrevious,
            verification: {
                performed: false,
                skippedReason,
            },
            stepResults,
        };
        writeSnapshot(snapshot);

        if (mode.gateOnly) {
            console.log('[post-restart] gate-only check complete');
            console.log(`[post-restart] snapshot: ${stampedSnapshotPath}`);
            return;
        }

        console.log('[post-restart] deep verification skipped because restart is still required');
        console.log('[post-restart] apply update from cogwheel, restart VS Code Insiders, then rerun this lane');
        console.log(`[post-restart] snapshot: ${stampedSnapshotPath}`);
        return;
    }

    if (!hasUpdateDelta && !mode.force) {
        const snapshot: Snapshot = {
            generatedAt: new Date().toISOString(),
            sequence: ['no-update-delta', 'verification-skipped'],
            insidersVersion: parsedInsidersVersion,
            restartGate,
            insidersChangedSincePrevious,
            installedExtensions,
            changedSincePrevious,
            verification: {
                performed: false,
                skippedReason: 'no-update-delta-since-previous-snapshot',
            },
            stepResults,
        };
        writeSnapshot(snapshot);
        console.log('[post-restart] no update delta since previous snapshot; skipping deep verification');
        console.log('[post-restart] use --force to run full verification anyway');
        console.log(`[post-restart] snapshot: ${stampedSnapshotPath}`);
        return;
    }

    stepResults.push(runCommand(
        'Tool pool scan',
        ['bun', 'run', 'scripts/toolpool-scan.ts', '--quiet'],
        extensionRoot,
    ));
    stepResults.push(runCommand(
        'Host verification',
        ['bun', 'run', 'scripts/verify-host.ts'],
        extensionRoot,
    ));
    stepResults.push(runCommand(
        'Archive compile',
        ['bun', 'run', 'compile'],
        extensionRoot,
    ));
    stepResults.push(runCommand(
        'Statusbar compile',
        ['bun', 'run', '--cwd', 'extensions/chthonic-statusbar', 'compile'],
        repoRoot,
    ));
    stepResults.push(runCommand(
        'Mandala compile',
        ['bun', 'run', '--cwd', 'extensions/chthonic-mandala', 'compile'],
        repoRoot,
    ));
    stepResults.push(runCommand(
        'Extension E2E smoke',
        ['bun', 'run', '--cwd', 'extensions/chthonic-archive', 'test:e2e'],
        repoRoot,
    ));
    stepResults.push(runCommand(
        'Archaeology diagnostics',
        ['bun', 'test', 'dumpster-dive/forge/extension-archaeology/diagnostics-tests'],
        repoRoot,
    ));
    stepResults.push(runCommand(
        'Bun strict audit',
        ['bun', 'run', 'scripts/bun-practices-audit.ts', '--strict'],
        repoRoot,
    ));

    if (mode.withAiLanes) {
        const hfRankerPath = path.join(repoRoot, 'scripts', 'hf-model-ranker.ts');
        if (existsSync(hfRankerPath)) {
            const hfArgs = [
                'bun',
                'run',
                'scripts/hf-model-ranker.ts',
                '--limit',
                mode.rankLimit ?? '80',
            ];
            if (mode.rankVramGb) {
                hfArgs.push('--target-vram-gb', mode.rankVramGb);
            }
            stepResults.push(runOptionalCommand(
                'HF model ranking refresh',
                hfArgs,
                repoRoot,
            ));
        } else {
            console.warn('[post-restart] skipping HF ranking refresh (scripts/hf-model-ranker.ts missing)');
        }

        const artCopPath = path.join(repoRoot, 'scripts', 'vscode-art-cop.ts');
        if (existsSync(artCopPath)) {
            const artCopArgs = [
                'bun',
                'run',
                'scripts/vscode-art-cop.ts',
            ];
            if (mode.artCopImages) {
                artCopArgs.push('--images', mode.artCopImages);
            } else {
                artCopArgs.push(
                    '--images-dir',
                    mode.artCopImagesDir ?? 'bun-playwright-poc',
                    '--max-images',
                    mode.artCopMaxImages ?? '4',
                );
            }
            if (mode.artCopNoLlm) {
                artCopArgs.push('--no-llm');
            }
            stepResults.push(runOptionalCommand(
                'ArtCop VS Code UI audit',
                artCopArgs,
                repoRoot,
            ));
        } else {
            console.warn('[post-restart] skipping ArtCop audit (scripts/vscode-art-cop.ts missing)');
        }
    }

    const snapshot: Snapshot = {
        generatedAt: new Date().toISOString(),
        sequence: [
            'restart-insiders',
            'restart-extensions',
            'verify-after-restart',
            ...(mode.withAiLanes ? ['ai-review-lanes'] : []),
        ],
        insidersVersion: parsedInsidersVersion,
        restartGate,
        insidersChangedSincePrevious,
        installedExtensions,
        changedSincePrevious,
        verification: {
            performed: true,
            skippedReason: null,
        },
        stepResults,
    };
    writeSnapshot(snapshot);

    console.log('\n[post-restart] verification complete');
    console.log(`[post-restart] snapshot: ${stampedSnapshotPath}`);
    console.log(`[post-restart] latest:   ${latestSnapshotPath}`);
    if (insidersChangedSincePrevious) {
        console.log('[post-restart] insiders build changed since previous snapshot: yes');
    } else {
        console.log('[post-restart] insiders build changed since previous snapshot: no');
    }
    console.log(`[post-restart] extension version changes since previous snapshot: ${changedSincePrevious.length}`);
    if (!insidersChangedSincePrevious && changedSincePrevious.length === 0) {
        console.log('[post-restart] note: no product/extension delta detected. If you expected an update, apply from the cogwheel and restart, then run this lane again.');
    }
}

run();
