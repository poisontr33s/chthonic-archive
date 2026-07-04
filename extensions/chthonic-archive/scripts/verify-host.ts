// @SID: EXT_VERIFY_HOST_V1
import { spawnSync } from 'bun';
import { existsSync, readFileSync, readdirSync } from 'fs';
import path from 'path';

type HostCheck = {
    name: string;
    cmd: string[];
    check?: (stdout: string, stderr: string) => boolean;
    autoFix?: string[];
    manualCheck?: () => ManualCheckResult;
    fix: string;
    warnOnly?: boolean;
    infoOnly?: boolean;
};

type EvidenceBasis =
    | 'manual-check'
    | 'command-exit'
    | 'command-predicate'
    | 'auto-fix'
    | 'policy-warn'
    | 'policy-info'
    | 'path-probe'
    | 'stderr-warning'
    | 'upstream-not-checked'
    | 'await-lane'
    | 'workspace-declaration'
    | 'remediation-blocked';

type EvidenceConfidence = 'local-observed' | 'local-inferred' | 'policy' | 'upstream-not-checked';

type EvidenceEntry = {
    basis: EvidenceBasis;
    claim: string;
    observed?: string;
    confidence: EvidenceConfidence;
};

type ManualCheckResult = {
    ok: boolean;
    note?: string;
    evidence?: EvidenceEntry[];
};

type CheckStatus = 'OK' | 'WARN' | 'INFO' | 'FAILED' | 'MISSING' | 'FIXED';

type EvaluatedNode = {
    name: string;
    status: CheckStatus;
    note?: string;
    fix?: string;
    hardFail: boolean;
    evidence?: EvidenceEntry[];
    children: EvaluatedNode[];
};

type CheckTreeNode = {
    name: string;
    check?: HostCheck;
    children?: CheckTreeNode[];
};

type ToolpoolSnapshot = {
    recommendedLanes?: {
        native?: string;
        sql?: string;
        infra?: string;
    };
};

type VerifyMode = {
    codexOnly: boolean;
};

type CodexExtensionProbe = {
    channel: 'insiders' | 'stable';
    dirPath: string;
    version: string;
    vscodeEngine: string | null;
};

const cyan = '\x1b[36m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const reset = '\x1b[0m';

const envOverrides: Record<string, string> = {};
const mode: VerifyMode = {
    codexOnly: process.argv.includes('--codex-only'),
};

function resolveRepoRoot(): string | null {
    const probe = runSync(['git', 'rev-parse', '--show-toplevel']);
    if (probe.threw || probe.exitCode !== 0) {
        return null;
    }
    const root = normalizeOutput(probe.stdout).split(/\r?\n/)[0]?.trim();
    return root && root.length > 0 ? root : null;
}

function mergedEnv(): Record<string, string> {
    return {
        ...process.env,
        ...envOverrides,
    };
}

function runSync(cmd: string[]): {
    exitCode: number;
    stdout: string;
    stderr: string;
    threw: boolean;
} {
    try {
        const result = spawnSync(cmd, {
            stdout: 'pipe',
            stderr: 'pipe',
            env: mergedEnv(),
        });
        return {
            exitCode: result.exitCode,
            stdout: Buffer.from(result.stdout).toString(),
            stderr: Buffer.from(result.stderr).toString(),
            threw: false,
        };
    } catch {
        return {
            exitCode: 1,
            stdout: '',
            stderr: '',
            threw: true,
        };
    }
}

function normalizeOutput(text: string): string {
    return text.replace(/\u0000/g, '').trim();
}

function firstOutputLine(text: string): string | null {
    const line = normalizeOutput(text)
        .split(/\r?\n/)
        .map((entry) => entry.trim())
        .find(Boolean);
    return line ?? null;
}

function makeEvidence(
    basis: EvidenceBasis,
    claim: string,
    observed?: string,
    confidence: EvidenceConfidence = 'local-observed',
): EvidenceEntry {
    return {
        basis,
        claim,
        observed,
        confidence,
    };
}

function formatCommandObservation(result: ReturnType<typeof runSync>): string {
    const pieces = [`exit=${result.threw ? 'threw' : result.exitCode}`];
    const stdout = firstOutputLine(result.stdout);
    const stderr = firstOutputLine(result.stderr);
    if (stdout) {
        pieces.push(`stdout=${stdout}`);
    }
    if (stderr) {
        pieces.push(`stderr=${stderr}`);
    }
    return pieces.join('; ');
}

function resolveCommandPath(command: string): string | null {
    const probe = process.platform === 'win32'
        ? runSync(['where', command])
        : runSync(['which', command]);
    if (probe.threw || probe.exitCode !== 0 || !probe.stdout.trim()) {
        return null;
    }
    const line = normalizeOutput(probe.stdout).split(/\r?\n/).map((entry) => entry.trim()).find(Boolean);
    return line ?? null;
}

function getCodexExtensionProbes(): CodexExtensionProbe[] {
    const home = process.env.USERPROFILE ?? process.env.HOME ?? '';
    if (!home) {
        return [];
    }

    const roots: Array<{ channel: 'insiders' | 'stable'; dir: string }> = [
        { channel: 'insiders', dir: path.join(home, '.vscode-insiders', 'extensions') },
        { channel: 'stable', dir: path.join(home, '.vscode', 'extensions') },
    ];

    const probes: CodexExtensionProbe[] = [];
    for (const root of roots) {
        if (!existsSync(root.dir)) {
            continue;
        }
        const dirs = readdirSync(root.dir, { withFileTypes: true })
            .filter((entry) => entry.isDirectory() && entry.name.startsWith('openai.chatgpt-'))
            .map((entry) => path.join(root.dir, entry.name));
        for (const dirPath of dirs) {
            const packagePath = path.join(dirPath, 'package.json');
            const raw = safeReadText(packagePath);
            if (!raw) {
                continue;
            }
            try {
                const parsed = JSON.parse(raw) as Record<string, unknown>;
                const version = typeof parsed.version === 'string' ? parsed.version : 'unknown';
                const engines = typeof parsed.engines === 'object' && parsed.engines ? parsed.engines as Record<string, unknown> : null;
                const vscodeEngine = engines && typeof engines.vscode === 'string' ? engines.vscode : null;
                probes.push({
                    channel: root.channel,
                    dirPath,
                    version,
                    vscodeEngine,
                });
            } catch {
                continue;
            }
        }
    }

    return probes.sort((left, right) => right.version.localeCompare(left.version, undefined, { numeric: true, sensitivity: 'base' }));
}

function hasWorkspacePackage(depName: string): boolean {
    const packagePath = path.join(process.cwd(), 'package.json');
    const raw = safeReadText(packagePath);
    if (!raw) {
        return false;
    }

    try {
        const parsed = JSON.parse(raw) as Record<string, unknown>;
        const depKeys = ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies'];
        for (const depKey of depKeys) {
            const depTable = parsed[depKey];
            if (!depTable || typeof depTable !== 'object') {
                continue;
            }
            if (Object.prototype.hasOwnProperty.call(depTable, depName)) {
                return true;
            }
        }
    } catch {
        return false;
    }

    return false;
}

function hasGlobalBunPackage(packagePath: string): boolean {
    const home = process.env.USERPROFILE ?? process.env.HOME ?? '';
    if (!home) {
        return false;
    }
    return existsSync(path.join(home, '.bun', 'install', 'global', 'node_modules', packagePath));
}

function hasPythonAgentsPackage(): boolean {
    const pythonPath = path.join(
        process.cwd(),
        '.chthonic',
        'venv',
        process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
    );
    if (!existsSync(pythonPath)) {
        return false;
    }
    const probe = runSync([pythonPath, '-c', 'import agents']);
    return !probe.threw && probe.exitCode === 0;
}

function ensureCodexCliLane(): ManualCheckResult {
    const codex = runSync(['codex', '--version']);
    if (codex.threw || codex.exitCode !== 0) {
        return {
            ok: false,
            note: 'codex CLI not found on PATH',
        };
    }

    const codexPath = resolveCommandPath('codex') ?? 'unknown';
    const version = normalizeOutput(codex.stdout).split(/\r?\n/)[0] ?? 'unknown';
    return {
        ok: true,
        note: `version=${version}\npath=${codexPath}`,
    };
}

function ensureCodexSandboxLane(): ManualCheckResult {
    const probe = runSync([
        'codex',
        'sandbox',
        'windows',
        '--full-auto',
        'pwsh',
        '-NoLogo',
        '-NoProfile',
        '-Command',
        'Write-Output chthonic-sandbox-ok',
    ]);
    const output = normalizeOutput(probe.stdout);
    if (!probe.threw && probe.exitCode === 0 && /chthonic-sandbox-ok/i.test(output)) {
        return {
            ok: true,
            note: 'native Windows restricted-token sandbox is functional',
        };
    }
    return {
        ok: false,
        note: 'native Codex Windows sandbox probe failed',
    };
}

function ensureCodexExtensionLane(): ManualCheckResult {
    const probes = getCodexExtensionProbes();
    if (probes.length === 0) {
        return {
            ok: false,
            note: 'openai.chatgpt extension not found in VS Code extension roots',
        };
    }

    const active = probes[0];
    const vscodeInsiders = runSync(['code-insiders', '--version']);
    const insidersAvailable = !vscodeInsiders.threw && vscodeInsiders.exitCode === 0;
    const insidersVersion = insidersAvailable
        ? (normalizeOutput(vscodeInsiders.stdout).split(/\r?\n/)[0] ?? 'unknown')
        : 'missing';

    const vscodeStable = runSync(['code', '--version']);
    const stableAvailable = !vscodeStable.threw && vscodeStable.exitCode === 0;
    const stableVersion = stableAvailable
        ? (normalizeOutput(vscodeStable.stdout).split(/\r?\n/)[0] ?? 'unknown')
        : 'missing';

    return {
        ok: true,
        note: [
            `channel=${active.channel}`,
            `version=${active.version}`,
            `engines.vscode=${active.vscodeEngine ?? 'unknown'}`,
            `code-insiders=${insidersVersion}`,
            `code-stable=${stableVersion}`,
            insidersAvailable
                ? 'insiders-cli=ready'
                : 'insiders-cli=optional-missing (insiders:* scripts unavailable)',
        ].join('\n'),
    };
}

function ensureOpenAiSdkLane(): ManualCheckResult {
    const codexSdkWorkspace = hasWorkspacePackage('@openai/codex-sdk');
    const agentsJsWorkspace = hasWorkspacePackage('@openai/agents');
    const openaiJsWorkspace = hasWorkspacePackage('openai');

    const codexSdkGlobal = hasGlobalBunPackage(path.join('@openai', 'codex-sdk'));
    const agentsJsGlobal = hasGlobalBunPackage(path.join('@openai', 'agents'));
    const openaiJsGlobal = hasGlobalBunPackage('openai');
    const agentsPyInstalled = hasPythonAgentsPackage();

    const codexSdkOk = codexSdkWorkspace || codexSdkGlobal;
    const agentsJsOk = agentsJsWorkspace || agentsJsGlobal;
    const openaiJsOk = openaiJsWorkspace || openaiJsGlobal;

    const allPresent = codexSdkOk && agentsJsOk && openaiJsOk;
    return {
        ok: allPresent,
        note: [
            `@openai/codex-sdk=${codexSdkOk ? 'OK' : 'MISSING'}`,
            `|- @openai/agents=${agentsJsOk ? 'OK' : 'MISSING'}`,
            `|- openai(js)=${openaiJsOk ? 'OK' : 'MISSING'}`,
            `\\- openai-agents(py package, optional)=${agentsPyInstalled ? 'present' : 'absent'}`,
        ].join('\n'),
    };
}

function ensureWetPaperNoDeleteGuard(): ManualCheckResult {
    const repoRoot = resolveRepoRoot();
    if (!repoRoot) {
        return {
            ok: true,
            note: 'git repository root unresolved; skipping non-delete guard',
        };
    }

    const status = runSync(['git', '-C', repoRoot, 'status', '--porcelain']);
    if (status.threw || status.exitCode !== 0) {
        return {
            ok: true,
            note: 'unable to read git status; skipping non-delete guard',
        };
    }

    const deletionRows = normalizeOutput(status.stdout)
        .split(/\r?\n/)
        .map((line) => line.trimEnd())
        .filter((line) => line.length >= 3)
        .filter((line) => {
            const xy = line.slice(0, 2);
            return xy.includes('D');
        });

    if (deletionRows.length === 0) {
        return {
            ok: true,
            note: 'no tracked deletions detected (WPTG compliant)',
        };
    }

    const preview = deletionRows.slice(0, 8).map((line) => line.slice(3));
    const remainder = deletionRows.length - preview.length;
    const suffix = remainder > 0 ? `\n... +${remainder} more deletions` : '';
    return {
        ok: false,
        note: `tracked deletions detected:\n${preview.join('\n')}${suffix}`,
    };
}

function loadToolpoolSnapshot(): ToolpoolSnapshot | null {
    const snapshotPath = path.join(process.cwd(), '.chthonic', 'cache', 'toolpool.json');
    if (!existsSync(snapshotPath)) {
        return null;
    }

    try {
        const raw = readFileSync(snapshotPath, 'utf8');
        return JSON.parse(raw) as ToolpoolSnapshot;
    } catch {
        return null;
    }
}

function ensureToolpoolLane(): ManualCheckResult {
    const snapshot = loadToolpoolSnapshot();
    if (!snapshot || !snapshot.recommendedLanes) {
        return {
            ok: false,
            note: 'missing .chthonic/cache/toolpool.json; run `bun run toolpool:scan` (or `mise run toolpool-scan`) to map the installed VS/SQL/tool pool',
        };
    }

    const nativeLane = snapshot.recommendedLanes.native ?? 'unknown';
    const sqlLane = snapshot.recommendedLanes.sql ?? 'unknown';
    const infraLane = snapshot.recommendedLanes.infra ?? 'unknown';
    const nativeOk = /^vs2026-.*insider(s)?$/i.test(nativeLane);
    const sqlOk = sqlLane === 'vs-dacfx' || sqlLane === 'ssms-dacfx';
    const infraOk = infraLane === 'az+bicep-ready';

    return {
        ok: nativeOk && sqlOk && infraOk,
        note: [
            `native=${nativeLane} ${nativeOk ? 'OK' : 'WARN'}`,
            `|- sql=${sqlLane} ${sqlOk ? 'OK' : 'WARN'}`,
            `\\- infra=${infraLane} ${infraOk ? 'OK' : 'WARN'}`,
        ].join('\n'),
    };
}

function ensureNodeManagerLane(): ManualCheckResult {
    const result = runSync(['bun', '--version']);
    if (!result.threw && result.exitCode === 0) {
        return { ok: true, note: 'using bun (runtime + package manager + bundler + test runner)' };
    }
    return { ok: false };
}

function workspaceNeedsSolanaLane(): boolean {
    const root = process.cwd();
    const markers = [
        path.join(root, 'Anchor.toml'),
        path.join(root, '.chthonic', 'mise.toml'),
        path.join(root, 'mise.toml'),
        path.join(root, '.mise.toml'),
    ];

    for (const marker of markers) {
        if (!existsSync(marker)) {
            continue;
        }
        const content = safeReadText(marker);
        if (!content) {
            continue;
        }
        if (/solana-cli|agave|anchor|solana-install|agave-install/i.test(content)) {
            return true;
        }
    }

    return false;
}

function ensureAgaveAnzaLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const solana = runSync(['solana', '--version']);
    const agaveVersion = runSync(['agave-install', '--version']);
    const agaveHelp = runSync(['agave-install', '--help']);
    const solanaPath = resolveCommandPath('solana');
    const agaveInstallPath = resolveCommandPath('agave-install');
    const solanaInstallPath = resolveCommandPath('solana-install');

    const hasSolana = !solana.threw && solana.exitCode === 0;
    const hasUsableAgaveInstall =
        Boolean(agaveInstallPath) &&
        ((!agaveVersion.threw && agaveVersion.exitCode === 0) || (!agaveHelp.threw && agaveHelp.exitCode === 0));
    const baseEvidence: EvidenceEntry[] = [
        makeEvidence(
            'workspace-declaration',
            needsLane ? 'workspace declares a Solana/Agave lane' : 'workspace does not declare a Solana/Agave lane',
            undefined,
            'local-inferred',
        ),
        makeEvidence('command-exit', 'solana CLI version probe', formatCommandObservation(solana)),
        makeEvidence('path-probe', 'solana path probe', solanaPath ?? 'missing'),
        makeEvidence('path-probe', 'agave-install path probe', agaveInstallPath ?? 'missing'),
        makeEvidence('command-exit', 'agave-install --version probe', formatCommandObservation(agaveVersion)),
        makeEvidence('command-exit', 'agave-install --help probe', formatCommandObservation(agaveHelp)),
        makeEvidence('path-probe', 'solana-install legacy path probe', solanaInstallPath ?? 'missing'),
        makeEvidence(
            'upstream-not-checked',
            'offline preflight does not prove latest Agave release',
            'live release source must be checked before upgrade motion',
            'upstream-not-checked',
        ),
    ];
    const blockedInstallerEvidence = makeEvidence(
        'remediation-blocked',
        'stale solana-install remediation must not be called',
        'use a usable agave-install or current Anza prebuilt release instead',
        'policy',
    );

    const note = [
        `solana=${hasSolana ? normalizeOutput(solana.stdout).split(/\r?\n/)[0] : 'MISSING'}`,
        `solana.path=${solanaPath ?? 'missing'}`,
        `agave-install.path=${agaveInstallPath ?? 'missing'}`,
        `agave-install.usable=${hasUsableAgaveInstall ? 'OK' : 'BROKEN'}`,
        `solana-install=${solanaInstallPath ? `present (${solanaInstallPath})` : 'missing (legacy/stale task target)'}`,
        'latest Agave release is not checked by offline preflight; verify live before upgrading',
    ];

    if (hasSolana && hasUsableAgaveInstall) {
        return {
            ok: true,
            note: [...note, 'update lane: agave-install update'].join('\n'),
            evidence: baseEvidence,
        };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Agave/Anza lane requirements',
            evidence: baseEvidence,
        };
    }
    if (hasSolana && agaveInstallPath && !hasUsableAgaveInstall) {
        return {
            ok: false,
            note: [
                ...note,
                'Agave CLI is present, but the Anza installer lane is broken; do not call solana-install.',
                'Repair via the current Anza Windows installer or manual prebuilt release, then re-run this check.',
            ].join('\n'),
            evidence: [...baseEvidence, blockedInstallerEvidence],
        };
    }
    if (hasSolana && !agaveInstallPath) {
        return {
            ok: false,
            note: [...note, 'Agave CLI is present, but agave-install is missing; update lane unavailable.'].join('\n'),
            evidence: [...baseEvidence, blockedInstallerEvidence],
        };
    }
    if (!hasSolana && hasUsableAgaveInstall) {
        return {
            ok: false,
            note: [...note, 'agave-install is usable, but solana CLI is missing on PATH.'].join('\n'),
            evidence: baseEvidence,
        };
    }
    return {
        ok: false,
        note: [...note, 'Agave/Anza CLI lane is not usable for this declared workspace.'].join('\n'),
        evidence: [...baseEvidence, blockedInstallerEvidence],
    };
}

function ensureAnchorLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const anchor = runSync(['anchor', '--version']);
    const avm = runSync(['avm', '--version']);

    const hasAnchor = !anchor.threw && anchor.exitCode === 0;
    const hasAvm = !avm.threw && avm.exitCode === 0;
    const avmWarning = normalizeOutput(avm.stderr);
    const note = [
        `anchor=${hasAnchor ? normalizeOutput(anchor.stdout).split(/\r?\n/)[0] : 'MISSING'}`,
        `avm=${hasAvm ? normalizeOutput(avm.stdout).split(/\r?\n/)[0] : 'MISSING'}`,
    ];
    const baseEvidence: EvidenceEntry[] = [
        makeEvidence(
            'workspace-declaration',
            needsLane ? 'workspace declares an Anchor lane' : 'workspace does not declare an Anchor lane',
            undefined,
            'local-inferred',
        ),
        makeEvidence('command-exit', 'anchor CLI version probe', formatCommandObservation(anchor)),
        makeEvidence('command-exit', 'avm version probe', formatCommandObservation(avm)),
    ];

    if (hasAnchor && hasAvm) {
        if (avmWarning) {
            return {
                ok: false,
                note: [...note, `avm warning=${avmWarning}`].join('\n'),
                evidence: [
                    ...baseEvidence,
                    makeEvidence('stderr-warning', 'avm emitted a warning while returning exit 0', avmWarning),
                ],
            };
        }
        return { ok: true, note: note.join('\n'), evidence: baseEvidence };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Anchor lane requirements',
            evidence: baseEvidence,
        };
    }
    if (hasAnchor && !hasAvm) {
        return {
            ok: false,
            note: 'anchor detected but avm missing (version management unavailable)',
            evidence: baseEvidence,
        };
    }
    if (!hasAnchor && hasAvm) {
        return {
            ok: false,
            note: 'avm detected but anchor CLI not activated',
            evidence: baseEvidence,
        };
    }
    return {
        ok: false,
        note: 'anchor + avm are both missing for declared Solana lane',
        evidence: baseEvidence,
    };
}

function ensureFrankendancerLane(): ManualCheckResult {
    return {
        ok: false,
        note: [
            'Frankendancer is the active Firedancer-family validator lane for mainnet/testnet.',
            'Track firedancer-io/firedancer releases separately from Win11 bundle compile.',
            'Not a local Windows package preflight blocker.',
        ].join('\n'),
        evidence: [
            makeEvidence(
                'await-lane',
                'Frankendancer is tracked as a validator lane, not a local Win11 compile blocker',
                'requires release/source check before validator work',
                'policy',
            ),
        ],
    };
}

function ensureFiredancerCppLane(): ManualCheckResult {
    return {
        ok: false,
        note: [
            'Await: full Firedancer C++ validator is not the local Win11 compile lane.',
            'Current upstream positions full Firedancer as heavy-development / non-production.',
            'Treat as Linux/validator research, not Agave CLI remediation.',
        ].join('\n'),
        evidence: [
            makeEvidence(
                'await-lane',
                'full Firedancer C++ is await/research for this Win11 repo lane',
                'not a package preflight remediation target',
                'policy',
            ),
        ],
    };
}

function safeReadText(filePath: string): string | null {
    try {
        return readFileSync(filePath, 'utf8');
    } catch {
        return null;
    }
}

console.log(`${cyan}[Chthonic] Running Preflight Host Verification...${reset}`);

const hostLaneNode: CheckTreeNode = {
    name: 'Host Lane Graph',
    children: [
        {
            name: 'Tool Pool Snapshot',
            check: {
                name: 'Tool Pool Snapshot',
                cmd: ['pwsh', '--version'],
                manualCheck: ensureToolpoolLane,
                warnOnly: true,
                fix: 'Run: bun run toolpool:scan (or mise run toolpool-scan)',
            },
        },
    ],
};

const codexLaneNode: CheckTreeNode = {
    name: 'Codex Agent Lanes',
    children: [
        {
            name: 'WPTG Non-Delete Guard',
            check: {
                name: 'WPTG Non-Delete Guard',
                cmd: ['git', '--version'],
                manualCheck: ensureWetPaperNoDeleteGuard,
                warnOnly: true,
                fix: 'Avoid destructive deletes. Preserve legacy artifacts and propose upcycle paths before removal.',
            },
        },
        {
            name: 'Codex CLI',
            check: {
                name: 'Codex CLI',
                cmd: ['codex', '--version'],
                manualCheck: ensureCodexCliLane,
                warnOnly: true,
                fix: 'Install Codex CLI: bun add -g @openai/codex',
            },
        },
        {
            name: 'Codex VS Code Extension',
            check: {
                name: 'Codex VS Code Extension',
                cmd: ['code-insiders', '--list-extensions'],
                manualCheck: ensureCodexExtensionLane,
                warnOnly: true,
                fix: 'Install extension openai.chatgpt in VS Code Insiders.',
            },
        },
        {
            name: 'Native Sandbox (Windows)',
            check: {
                name: 'Codex Native Sandbox (Windows)',
                cmd: ['codex', 'sandbox', 'windows', '--help'],
                manualCheck: ensureCodexSandboxLane,
                warnOnly: true,
                fix: 'Upgrade Codex CLI and ensure sandbox support is available: codex sandbox windows --help',
            },
        },
        {
            name: 'OpenAI SDK/Agent Kits',
            check: {
                name: 'OpenAI SDK/Agent Kits',
                cmd: ['bun', '--version'],
                manualCheck: ensureOpenAiSdkLane,
                warnOnly: true,
                fix: 'Install JS SDKs: bun add -D @openai/codex-sdk @openai/agents openai; optional Python package lane: uv pip install --python .chthonic/venv/Scripts/python.exe openai-agents',
            },
        },
    ],
};

const runtimeLaneNode: CheckTreeNode = {
    name: 'Runtime Lanes',
    children: [
        {
            name: 'Rust Lane',
            children: [
                {
                    name: 'Rust Toolchain',
                    check: {
                        name: 'Rust Toolchain',
                        cmd: ['rustc', '--version'],
                        fix: 'Install Rust via rustup: https://rustup.rs',
                    },
                },
                {
                    name: 'Rust Package Manager (cargo)',
                    check: {
                        name: 'Rust Package Manager (cargo)',
                        cmd: ['cargo', '--version'],
                        fix: 'Install Cargo via rustup: https://rustup.rs',
                    },
                },
                {
                    name: 'Rustup',
                    check: {
                        name: 'Rustup',
                        cmd: ['rustup', '--version'],
                        fix: 'Install rustup: https://rustup.rs',
                    },
                },
            ],
        },
        {
            name: 'Ruby Lane',
            children: [
                {
                    name: 'Ruby Manager (rv)',
                    check: {
                        name: 'Ruby Manager (rv)',
                        cmd: ['rv', '--version'],
                        warnOnly: true,
                        fix: 'Install rv (Rust-native Ruby manager): cargo install rv',
                    },
                },
                {
                    name: 'Ruby Runtime',
                    check: {
                        name: 'Ruby Runtime',
                        cmd: ['ruby', '--version'],
                        check: (stdout) => /^ruby\s+4\./i.test(stdout.trim()),
                        warnOnly: true,
                        fix: 'Install Ruby 4.x lane via rv to align with Prism lane target.',
                    },
                },
            ],
        },
        {
            name: 'Go Lane',
            children: [
                {
                    name: 'Go Manager (goup)',
                    check: {
                        name: 'Go Manager (goup)',
                        cmd: ['goup', '--version'],
                        warnOnly: true,
                        fix: 'Install goup (Rust-native Go manager): cargo install goup',
                    },
                },
            ],
        },
        {
            name: 'JavaScript Lane',
            children: [
                {
                    name: 'Runtime (bun)',
                    check: {
                        name: 'JavaScript Runtime Lane (bun)',
                        cmd: ['bun', '--version'],
                        manualCheck: ensureNodeManagerLane,
                        warnOnly: true,
                        fix: 'Install bun: https://bun.sh/docs/installation',
                    },
                },
            ],
        },
    ],
};

const solanaLaneNode: CheckTreeNode = {
    name: 'Solana Lanes',
    children: [
        {
            name: 'Agave / Anza CLI',
            check: {
                name: 'Agave / Anza CLI Lane',
                cmd: ['solana', '--version'],
                manualCheck: ensureAgaveAnzaLane,
                warnOnly: true,
                fix: 'Repair Agave/Anza installer lane: restore usable agave-install or install the current Anza prebuilt release manually.',
            },
        },
        {
            name: 'Anchor Lane',
            check: {
                name: 'Anchor Lane (anchor + avm)',
                cmd: ['anchor', '--version'],
                manualCheck: ensureAnchorLane,
                warnOnly: true,
                fix: 'Install AVM + Anchor CLI: cargo install --git https://github.com/solana-foundation/anchor avm --force && avm install latest && avm use latest',
            },
        },
        {
            name: 'Frankendancer Validator Lane',
            check: {
                name: 'Frankendancer Validator Lane',
                cmd: ['fdctl', '--version'],
                manualCheck: ensureFrankendancerLane,
                infoOnly: true,
                fix: 'Track firedancer-io/firedancer Frankendancer releases; do not wire this as a Win11 bundle blocker.',
            },
        },
        {
            name: 'Firedancer C++ Lane',
            check: {
                name: 'Firedancer C++ Lane',
                cmd: ['fdctl', '--version'],
                manualCheck: ensureFiredancerCppLane,
                infoOnly: true,
                fix: 'Await full Firedancer readiness; keep as Linux/C++ validator research lane.',
            },
        },
    ],
};

const wasmLaneNode: CheckTreeNode = {
    name: 'WASM Lanes',
    children: [
        {
            name: 'Target',
            check: {
                name: 'WASM Target',
                cmd: ['rustup', 'target', 'list', '--installed'],
                check: (stdout) => stdout.includes('wasm32-unknown-unknown'),
                autoFix: ['rustup', 'target', 'add', 'wasm32-unknown-unknown'],
                fix: 'Run: rustup target add wasm32-unknown-unknown',
            },
        },
        {
            name: 'wasm-bindgen',
            check: {
                name: 'wasm-bindgen CLI',
                cmd: ['wasm-bindgen', '--version'],
                autoFix: ['cargo', 'install', 'wasm-bindgen-cli'],
                fix: 'Install wasm-bindgen CLI: cargo install wasm-bindgen-cli',
            },
        },
    ],
};

const hygieneNode: CheckTreeNode = {
    name: 'Build Hygiene',
    children: [
        {
            name: 'MAKEFLAGS',
            check: {
                name: 'MAKEFLAGS (MSVC hygiene)',
                cmd: ['rustc', '--version'],
                manualCheck: () => {
                    const makeFlags = envOverrides.MAKEFLAGS ?? process.env.MAKEFLAGS;
                    const mflags = envOverrides.MFLAGS ?? process.env.MFLAGS;
                    const hasMakeFlags = Boolean(makeFlags && makeFlags.trim().length > 0);
                    const hasMflags = Boolean(mflags && mflags.trim().length > 0);
                    if (!hasMakeFlags && !hasMflags) {
                        return { ok: true, note: 'clean (no MAKEFLAGS/MFLAGS)' };
                    }
                    // Mirror build-ledger.ts behavior: sanitize locally instead of mutating
                    // global shell state.
                    envOverrides.MAKEFLAGS = '';
                    envOverrides.MFLAGS = '';
                    const details: string[] = [];
                    if (hasMakeFlags) details.push(`MAKEFLAGS=${makeFlags}`);
                    if (hasMflags) details.push(`MFLAGS=${mflags}`);
                    return {
                        ok: true,
                        note: `sanitized for this run (${details.join(', ')})`,
                    };
                },
                fix: 'No action required. Build wrappers sanitize MAKEFLAGS/MFLAGS per process.',
            },
        },
    ],
};

const checkTree: CheckTreeNode[] = mode.codexOnly
    ? [codexLaneNode]
    : [hostLaneNode, codexLaneNode, runtimeLaneNode, solanaLaneNode, wasmLaneNode, hygieneNode];

let failed = false;

const evaluatedTree = checkTree.map((node) => evaluateNode(node));
renderTree(evaluatedTree);
failed = evaluatedTree.some((node) => node.hardFail);
const hasWarnings = evaluatedTree.some((node) => treeHasStatus(node, 'WARN'));
const hasInfo = evaluatedTree.some((node) => treeHasStatus(node, 'INFO'));

if (failed) {
    console.log(`\n${red}[!] Host verification failed. Resolve the failing checks above.${reset}`);
    process.exit(1);
}

if (hasWarnings) {
    console.log(`\n${yellow}[!] Host verification completed with WARN lanes. No hard failures; clear WARN truth before treating this as an all-clear.${reset}`);
} else if (hasInfo) {
    console.log(`\n${cyan}[i] Host verification completed with INFO lanes. No hard failures.${reset}`);
} else {
    console.log(`\n${green}[+] Host verification passed. Ready for Oxidation.${reset}`);
}

function evaluateNode(node: CheckTreeNode): EvaluatedNode {
    if (node.check) {
        return evaluateCheck(node.check);
    }

    const children = (node.children ?? []).map((child) => evaluateNode(child));
    return {
        name: node.name,
        status: aggregateGroupStatus(children.map((child) => child.status)),
        hardFail: children.some((child) => child.hardFail),
        children,
    };
}

function policyEvidenceFor(check: HostCheck, status: CheckStatus): EvidenceEntry[] {
    if (status === 'WARN') {
        return [
            makeEvidence(
                'policy-warn',
                `${check.name} is warning-only; failure does not hard-fail this preflight`,
                undefined,
                'policy',
            ),
        ];
    }
    if (status === 'INFO') {
        return [
            makeEvidence(
                'policy-info',
                `${check.name} is informational; absence or non-readiness is not a local blocker`,
                undefined,
                'policy',
            ),
        ];
    }
    return [];
}

function evaluateCheck(check: HostCheck): EvaluatedNode {
    if (check.manualCheck) {
        const manual = check.manualCheck();
        const manualEvidence = [
            ...(manual.evidence ?? []),
            makeEvidence('manual-check', `manual check returned ok=${manual.ok}`, undefined, 'local-inferred'),
        ];
        if (manual.ok) {
            return {
                name: check.name,
                status: 'OK',
                note: manual.note,
                hardFail: false,
                evidence: manualEvidence,
                children: [],
            };
        }
        if (check.warnOnly) {
            return {
                name: check.name,
                status: 'WARN',
                note: manual.note,
                fix: check.fix,
                hardFail: false,
                evidence: [...manualEvidence, ...policyEvidenceFor(check, 'WARN')],
                children: [],
            };
        }
        if (check.infoOnly) {
            return {
                name: check.name,
                status: 'INFO',
                note: manual.note,
                fix: check.fix,
                hardFail: false,
                evidence: [...manualEvidence, ...policyEvidenceFor(check, 'INFO')],
                children: [],
            };
        }
        return {
            name: check.name,
            status: 'FAILED',
            note: manual.note,
            fix: check.fix,
            hardFail: true,
            evidence: manualEvidence,
            children: [],
        };
    }

    const proc = runSync(check.cmd);
    const stdout = proc.stdout;
    const stderr = proc.stderr;
    const commandEvidence = [
        makeEvidence(
            'command-exit',
            `${check.cmd.join(' ')} ${proc.threw || proc.exitCode !== 0 ? 'failed' : 'succeeded'}`,
            formatCommandObservation(proc),
        ),
    ];

    if (proc.threw || proc.exitCode !== 0) {
        if (check.autoFix) {
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            const fixEvidence = makeEvidence(
                'auto-fix',
                `${check.autoFix.join(' ')} returned exit=${fixProc.exitCode ?? 'unknown'}`,
                undefined,
                'local-observed',
            );
            if (fixProc.exitCode === 0) {
                return {
                    name: check.name,
                    status: 'FIXED',
                    hardFail: false,
                    evidence: [...commandEvidence, fixEvidence],
                    children: [],
                };
            }
            commandEvidence.push(fixEvidence);
        }

        if (check.warnOnly) {
            return {
                name: check.name,
                status: 'WARN',
                fix: check.fix,
                hardFail: false,
                evidence: [...commandEvidence, ...policyEvidenceFor(check, 'WARN')],
                children: [],
            };
        }
        if (check.infoOnly) {
            return {
                name: check.name,
                status: 'INFO',
                fix: check.fix,
                hardFail: false,
                evidence: [...commandEvidence, ...policyEvidenceFor(check, 'INFO')],
                children: [],
            };
        }
        return {
            name: check.name,
            status: 'MISSING',
            fix: check.fix,
            hardFail: true,
            evidence: commandEvidence,
            children: [],
        };
    }

    if (check.check && !check.check(stdout, stderr)) {
        const predicateEvidence = makeEvidence(
            'command-predicate',
            `${check.name} command exited 0 but repo predicate rejected the output`,
            [
                `stdout=${firstOutputLine(stdout) ?? '<empty>'}`,
                `stderr=${firstOutputLine(stderr) ?? '<empty>'}`,
            ].join('; '),
            'local-inferred',
        );
        const failedPredicateEvidence = [...commandEvidence, predicateEvidence];
        if (check.autoFix) {
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            const fixEvidence = makeEvidence(
                'auto-fix',
                `${check.autoFix.join(' ')} returned exit=${fixProc.exitCode ?? 'unknown'}`,
                undefined,
                'local-observed',
            );
            if (fixProc.exitCode === 0) {
                return {
                    name: check.name,
                    status: 'FIXED',
                    hardFail: false,
                    evidence: [...failedPredicateEvidence, fixEvidence],
                    children: [],
                };
            }
            failedPredicateEvidence.push(fixEvidence);
        }

        if (check.warnOnly) {
            return {
                name: check.name,
                status: 'WARN',
                fix: check.fix,
                hardFail: false,
                evidence: [...failedPredicateEvidence, ...policyEvidenceFor(check, 'WARN')],
                children: [],
            };
        }
        if (check.infoOnly) {
            return {
                name: check.name,
                status: 'INFO',
                fix: check.fix,
                hardFail: false,
                evidence: [...failedPredicateEvidence, ...policyEvidenceFor(check, 'INFO')],
                children: [],
            };
        }

        return {
            name: check.name,
            status: 'FAILED',
            fix: check.fix,
            hardFail: true,
            evidence: failedPredicateEvidence,
            children: [],
        };
    }

    const okEvidence = [...commandEvidence];
    if (check.check) {
        okEvidence.push(
            makeEvidence(
                'command-predicate',
                `${check.name} predicate accepted the command output`,
                [
                    `stdout=${firstOutputLine(stdout) ?? '<empty>'}`,
                    `stderr=${firstOutputLine(stderr) ?? '<empty>'}`,
                ].join('; '),
                'local-inferred',
            ),
        );
    }

    return {
        name: check.name,
        status: 'OK',
        hardFail: false,
        evidence: okEvidence,
        children: [],
    };
}

function renderTree(nodes: EvaluatedNode[]): void {
    for (const node of nodes) {
        console.log(`${node.name} ${colorizeStatus(node.status)}`);
        renderChildren(node.children, '');
    }
}

function treeHasStatus(node: EvaluatedNode, status: CheckStatus): boolean {
    return node.status === status || node.children.some((child) => treeHasStatus(child, status));
}

function renderChildren(children: EvaluatedNode[], prefix: string): void {
    for (let i = 0; i < children.length; i += 1) {
        const child = children[i];
        const isLast = i === children.length - 1;
        const branch = isLast ? '\\-' : '|-';
        const childPrefix = `${prefix}${isLast ? '   ' : '|  '}`;
        console.log(`${prefix}${branch} ${child.name} ${colorizeStatus(child.status)}`);
        if (child.note) {
            printIndented(child.note, childPrefix);
        }
        if (child.fix && child.status !== 'OK' && child.status !== 'FIXED') {
            printIndented(child.fix, childPrefix);
        }
        if (child.evidence && child.evidence.length > 0) {
            printEvidence(child.evidence, childPrefix);
        }
        if (child.children.length > 0) {
            renderChildren(child.children, childPrefix);
        }
    }
}

function aggregateGroupStatus(statuses: CheckStatus[]): CheckStatus {
    if (statuses.some((status) => status === 'FAILED' || status === 'MISSING')) {
        return 'FAILED';
    }
    if (statuses.some((status) => status === 'WARN')) {
        return 'WARN';
    }
    if (statuses.some((status) => status === 'INFO')) {
        return 'INFO';
    }
    if (statuses.some((status) => status === 'FIXED')) {
        return 'FIXED';
    }
    return 'OK';
}

function colorizeStatus(status: CheckStatus): string {
    switch (status) {
        case 'OK':
            return `${green}OK${reset}`;
        case 'WARN':
            return `${yellow}WARN${reset}`;
        case 'INFO':
            return `${cyan}INFO${reset}`;
        case 'FIXED':
            return `${green}FIXED${reset}`;
        case 'MISSING':
            return `${red}MISSING${reset}`;
        default:
            return `${red}FAILED${reset}`;
    }
}

function colorizeInlineStatus(text: string): string {
    return text.replace(/\b(OK|WARN|INFO|FAILED|MISSING|FIXED)\b/g, (token) => {
        return colorizeStatus(token as CheckStatus);
    });
}

function printIndented(text: string, prefix = '  '): void {
    for (const line of text.split(/\r?\n/)) {
        console.log(`${prefix}${colorizeInlineStatus(line)}`);
    }
}

function printEvidence(entries: EvidenceEntry[], prefix = '  '): void {
    for (const entry of entries) {
        printIndented(formatEvidence(entry), prefix);
    }
}

function formatEvidence(entry: EvidenceEntry): string {
    const pieces = [
        `basis=${entry.basis}`,
        `confidence=${entry.confidence}`,
        `claim=${entry.claim}`,
    ];
    if (entry.observed) {
        pieces.push(`observed=${entry.observed}`);
    }
    return pieces.join(' | ');
}

