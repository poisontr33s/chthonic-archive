import { spawnSync } from 'bun';
import { existsSync, readFileSync } from 'fs';
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

type ManualCheckResult = {
    ok: boolean;
    note?: string;
};

type CheckStatus = 'OK' | 'WARN' | 'INFO' | 'FAILED' | 'MISSING' | 'FIXED';

type EvaluatedNode = {
    name: string;
    status: CheckStatus;
    note?: string;
    fix?: string;
    hardFail: boolean;
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

const cyan = '\x1b[36m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const reset = '\x1b[0m';

const envOverrides: Record<string, string> = {};

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

function ensureSolanaToolSuiteLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const solana = runSync(['solana', '--version']);
    const agave = runSync(['agave-install', '--version']);

    const hasSolana = !solana.threw && solana.exitCode === 0;
    const hasAgaveInstall = !agave.threw && agave.exitCode === 0;

    if (hasSolana && hasAgaveInstall) {
        return { ok: true, note: 'solana + agave-install detected' };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Solana lane requirements',
        };
    }
    if (hasSolana && !hasAgaveInstall) {
        return {
            ok: false,
            note: 'solana detected but agave-install missing (update lane unavailable)',
        };
    }
    if (!hasSolana && hasAgaveInstall) {
        return {
            ok: false,
            note: 'agave-install detected but solana CLI missing on PATH',
        };
    }
    return {
        ok: false,
        note: 'solana + agave-install are both missing for declared Solana lane',
    };
}

function ensureAnchorLane(): ManualCheckResult {
    const needsLane = workspaceNeedsSolanaLane();
    const anchor = runSync(['anchor', '--version']);
    const avm = runSync(['avm', '--version']);

    const hasAnchor = !anchor.threw && anchor.exitCode === 0;
    const hasAvm = !avm.threw && avm.exitCode === 0;

    if (hasAnchor && hasAvm) {
        return { ok: true, note: 'anchor + avm detected' };
    }
    if (!needsLane) {
        return {
            ok: true,
            note: 'workspace does not currently declare Anchor lane requirements',
        };
    }
    if (hasAnchor && !hasAvm) {
        return {
            ok: false,
            note: 'anchor detected but avm missing (version management unavailable)',
        };
    }
    if (!hasAnchor && hasAvm) {
        return {
            ok: false,
            note: 'avm detected but anchor CLI not activated',
        };
    }
    return {
        ok: false,
        note: 'anchor + avm are both missing for declared Solana lane',
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

const checkTree: CheckTreeNode[] = [
    {
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
    },
    {
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
    },
    {
        name: 'Solana Lanes',
        children: [
            {
                name: 'Tool Suite',
                check: {
                    name: 'Solana Tool Suite Lane',
                    cmd: ['solana', '--version'],
                    manualCheck: ensureSolanaToolSuiteLane,
                    warnOnly: true,
                    fix: 'Install Solana Tool Suite (Agave): sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"',
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
        ],
    },
    {
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
    },
    {
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
    },
];

let failed = false;

const evaluatedTree = checkTree.map((node) => evaluateNode(node));
renderTree(evaluatedTree);
failed = evaluatedTree.some((node) => node.hardFail);

if (failed) {
    console.log(`\n${red}[!] Host verification failed. Resolve the failing checks above.${reset}`);
    process.exit(1);
}

console.log(`\n${green}[+] Host verification passed. Ready for Oxidation.${reset}`);

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

function evaluateCheck(check: HostCheck): EvaluatedNode {
    if (check.manualCheck) {
        const manual = check.manualCheck();
        if (manual.ok) {
            return {
                name: check.name,
                status: 'OK',
                note: manual.note,
                hardFail: false,
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
                children: [],
            };
        }
        return {
            name: check.name,
            status: 'FAILED',
            note: manual.note,
            fix: check.fix,
            hardFail: true,
            children: [],
        };
    }

    const proc = runSync(check.cmd);
    const stdout = proc.stdout;
    const stderr = proc.stderr;

    if (proc.threw || proc.exitCode !== 0) {
        if (check.autoFix) {
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            if (fixProc.exitCode === 0) {
                return {
                    name: check.name,
                    status: 'FIXED',
                    hardFail: false,
                    children: [],
                };
            }
        }

        if (check.warnOnly) {
            return {
                name: check.name,
                status: 'WARN',
                fix: check.fix,
                hardFail: false,
                children: [],
            };
        }
        if (check.infoOnly) {
            return {
                name: check.name,
                status: 'INFO',
                fix: check.fix,
                hardFail: false,
                children: [],
            };
        }
        return {
            name: check.name,
            status: 'MISSING',
            fix: check.fix,
            hardFail: true,
            children: [],
        };
    }

    if (check.check && !check.check(stdout, stderr)) {
        if (check.autoFix) {
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            if (fixProc.exitCode === 0) {
                return {
                    name: check.name,
                    status: 'FIXED',
                    hardFail: false,
                    children: [],
                };
            }
        }

        if (check.warnOnly) {
            return {
                name: check.name,
                status: 'WARN',
                fix: check.fix,
                hardFail: false,
                children: [],
            };
        }
        if (check.infoOnly) {
            return {
                name: check.name,
                status: 'INFO',
                fix: check.fix,
                hardFail: false,
                children: [],
            };
        }

        return {
            name: check.name,
            status: 'FAILED',
            fix: check.fix,
            hardFail: true,
            children: [],
        };
    }

    return {
        name: check.name,
        status: 'OK',
        hardFail: false,
        children: [],
    };
}

function renderTree(nodes: EvaluatedNode[]): void {
    for (const node of nodes) {
        console.log(`${node.name} ${colorizeStatus(node.status)}`);
        renderChildren(node.children, '');
    }
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

function printIndented(text: string, prefix = '  '): void {
    for (const line of text.split(/\r?\n/)) {
        console.log(`${prefix}${line}`);
    }
}
