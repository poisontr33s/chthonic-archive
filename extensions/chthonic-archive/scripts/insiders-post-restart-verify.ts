import { spawnSync } from 'bun';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
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

type Snapshot = {
    generatedAt: string;
    sequence: string[];
    insidersVersion: string[];
    installedExtensions: ExtensionVersion[];
    changedSincePrevious: ChangeRecord[];
    stepResults: StepResult[];
};

const extensionRoot = process.cwd();
const repoRoot = path.resolve(extensionRoot, '..', '..');
const cacheDir = path.join(extensionRoot, '.chthonic', 'cache');

const latestSnapshotPath = path.join(cacheDir, 'insiders-post-restart-verify-latest.json');
const runStamp = new Date().toISOString().replace(/[.:]/g, '-');
const stampedSnapshotPath = path.join(cacheDir, `insiders-post-restart-verify-${runStamp}.json`);

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

    const parsedInsidersVersion = insidersVersion.stdout
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
    const installedExtensions = parseExtensions(extensionList.stdout);
    const changedSincePrevious = computeChanges(previous, installedExtensions);

    const snapshot: Snapshot = {
        generatedAt: new Date().toISOString(),
        sequence: [
            'restart-insiders',
            'restart-extensions',
            'verify-after-restart',
        ],
        insidersVersion: parsedInsidersVersion,
        installedExtensions,
        changedSincePrevious,
        stepResults,
    };
    writeSnapshot(snapshot);

    console.log('\n[post-restart] verification complete');
    console.log(`[post-restart] snapshot: ${stampedSnapshotPath}`);
    console.log(`[post-restart] latest:   ${latestSnapshotPath}`);
    console.log(`[post-restart] extension version changes since previous snapshot: ${changedSincePrevious.length}`);
}

run();
