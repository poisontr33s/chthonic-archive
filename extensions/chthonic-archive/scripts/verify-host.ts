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

function prependPath(segment: string): void {
    const delim = process.platform === 'win32' ? ';' : ':';
    const current = envOverrides.PATH ?? process.env.PATH ?? '';
    const parts = current.split(delim).filter(Boolean);
    if (parts.some((part) => part.toLowerCase() === segment.toLowerCase())) {
        return;
    }
    envOverrides.PATH = `${segment}${delim}${current}`;
}

function rubyInstallRoot(): string | null {
    const ruby = runSync(['ruby', '-e', 'print RbConfig.ruby']);
    if (ruby.exitCode !== 0) {
        return null;
    }
    const rubyExe = ruby.stdout.trim();
    if (!rubyExe) {
        return null;
    }
    return path.dirname(path.dirname(rubyExe));
}

function findDevKitPerl(): string | null {
    const roots = [
        rubyInstallRoot(),
        'C:\\Ruby40-x64',
        'C:\\Ruby35-x64',
        'C:\\Ruby34-x64',
        'C:\\Ruby33-x64',
        'C:\\Ruby32-x64',
        'C:\\Ruby31-x64',
        'D:\\Ruby40-x64',
        'D:\\Ruby35-x64',
        'D:\\Ruby34-x64',
        'D:\\Ruby33-x64',
        'D:\\Ruby32-x64',
        'D:\\Ruby31-x64',
    ].filter((value): value is string => Boolean(value));

    const perlRelPaths = [
        path.join('msys64', 'ucrt64', 'bin', 'perl.exe'),
        path.join('msys64', 'mingw64', 'bin', 'perl.exe'),
        path.join('msys64', 'usr', 'bin', 'perl.exe'),
    ];

    // First pass: prefer Windows-native perl builds (MSWin32) for OpenSSL VC toolchains.
    for (const root of roots) {
        for (const relPath of perlRelPaths) {
            const candidate = path.join(root, relPath);
            if (!existsSync(candidate)) {
                continue;
            }
            const probe = runSync([candidate, '--version']);
            if (probe.exitCode === 0 && !isCygwinPerl(probe.stdout, probe.stderr)) {
                return candidate;
            }
        }
    }

    // Fallback pass: return the first perl we can find.
    for (const root of roots) {
        for (const relPath of perlRelPaths) {
            const candidate = path.join(root, relPath);
            if (existsSync(candidate)) {
                return candidate;
            }
        }
    }
    return null;
}

function isCygwinPerl(stdout: string, stderr: string): boolean {
    const combined = `${stdout}\n${stderr}`.toLowerCase();
    return combined.includes('cygwin');
}

function ensurePerlFromRubyDevKit(): ManualCheckResult {
    const perlInPath = runSync(['perl', '--version']);
    if (perlInPath.exitCode === 0 && !isCygwinPerl(perlInPath.stdout, perlInPath.stderr)) {
        return { ok: true, note: 'using perl from PATH' };
    }

    const devkitPerl = findDevKitPerl();
    if (!devkitPerl) {
        if (perlInPath.exitCode === 0 && isCygwinPerl(perlInPath.stdout, perlInPath.stderr)) {
            return {
                ok: false,
                note: 'PATH perl is Cygwin-based; Ruby DevKit perl was not found',
            };
        }
        return { ok: false };
    }

    const perlDir = path.dirname(devkitPerl);
    prependPath(perlDir);
    envOverrides.PERL = devkitPerl;
    const probe = runSync(['perl', '--version']);

    if (probe.exitCode === 0) {
        return {
            ok: true,
            note: `using Ruby DevKit perl: ${devkitPerl}`,
        };
    }

    return {
        ok: false,
        note: `found Ruby DevKit perl at ${devkitPerl}, but execution failed`,
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
    return {
        ok: true,
        note: `native=${nativeLane}, sql=${sqlLane}, infra=${infraLane}`,
    };
}

function ensureNodeManagerLane(): ManualCheckResult {
    const checks = [
        {
            tool: 'bun',
            args: ['--version'],
            note: 'using bun (runtime + package manager + bundler + test runner)',
        },
        {
            tool: 'fnm',
            args: ['--version'],
            note: 'bun missing; using fnm fallback lane',
        },
        {
            tool: 'volta',
            args: ['--version'],
            note: 'bun missing; using volta fallback lane',
        },
    ];
    for (const probe of checks) {
        const result = runSync([probe.tool, ...probe.args]);
        if (!result.threw && result.exitCode === 0) {
            return { ok: true, note: probe.note };
        }
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

const checks: HostCheck[] = [
    {
        name: 'Tool Pool Snapshot',
        cmd: ['pwsh', '--version'],
        manualCheck: ensureToolpoolLane,
        warnOnly: true,
        fix: 'Run: bun run toolpool:scan (or mise run toolpool-scan)',
    },
    {
        name: 'Rust Toolchain',
        cmd: ['rustc', '--version'],
        fix: 'Install Rust via rustup: https://rustup.rs',
    },
    {
        name: 'Rust Package Manager (cargo)',
        cmd: ['cargo', '--version'],
        fix: 'Install Cargo via rustup: https://rustup.rs',
    },
    {
        name: 'Rustup',
        cmd: ['rustup', '--version'],
        fix: 'Install rustup: https://rustup.rs',
    },
    {
        name: 'Ruby Manager (rv)',
        cmd: ['rv', '--version'],
        warnOnly: true,
        fix: 'Install rv (Rust-native Ruby manager): cargo install rv',
    },
    {
        name: 'Go Manager (goup)',
        cmd: ['goup', '--version'],
        warnOnly: true,
        fix: 'Install goup (Rust-native Go manager): cargo install goup',
    },
    {
        name: 'Node Manager Lane',
        cmd: ['bun', '--version'],
        manualCheck: ensureNodeManagerLane,
        warnOnly: true,
        fix: 'Install bun (preferred Node lane). Optional fallbacks: fnm or volta.',
    },
    {
        name: 'Solana Tool Suite Lane',
        cmd: ['solana', '--version'],
        manualCheck: ensureSolanaToolSuiteLane,
        warnOnly: true,
        fix: 'Install Solana Tool Suite (Agave): sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"',
    },
    {
        name: 'Anchor Lane (anchor + avm)',
        cmd: ['anchor', '--version'],
        manualCheck: ensureAnchorLane,
        warnOnly: true,
        fix: 'Install AVM + Anchor CLI: cargo install --git https://github.com/solana-foundation/anchor avm --force && avm install latest && avm use latest',
    },
    {
        name: 'WASM Target',
        cmd: ['rustup', 'target', 'list', '--installed'],
        check: (stdout) => stdout.includes('wasm32-unknown-unknown'),
        autoFix: ['rustup', 'target', 'add', 'wasm32-unknown-unknown'],
        fix: 'Run: rustup target add wasm32-unknown-unknown',
    },
    {
        name: 'wasm-bindgen CLI',
        cmd: ['wasm-bindgen', '--version'],
        autoFix: ['cargo', 'install', 'wasm-bindgen-cli'],
        fix: 'Install wasm-bindgen CLI: cargo install wasm-bindgen-cli',
    },
    {
        name: 'Perl (OpenSSL build via Ruby DevKit)',
        cmd: ['perl', '--version'],
        manualCheck: ensurePerlFromRubyDevKit,
        fix: 'Install RubyInstaller with DevKit and run `ridk install 3` so MSYS2 perl/toolchain is available.',
    },
    {
        name: 'MAKEFLAGS (MSVC OpenSSL compatibility)',
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
    {
        name: 'Ruby Runtime',
        cmd: ['ruby', '--version'],
        check: (stdout) => /^ruby\s+4\./i.test(stdout.trim()),
        warnOnly: true,
        fix: 'Install Ruby 4.x dev toolchain (RubyInstaller + ridk) to align with Prism lane target.',
    },
];

let failed = false;

for (const check of checks) {
    process.stdout.write(`Checking ${check.name}... `);
    if (check.manualCheck) {
        const manual = check.manualCheck();
        if (manual.ok) {
            console.log(`${green}OK${reset}`);
            if (manual.note) {
                console.log(`  ${manual.note}`);
            }
            continue;
        }
        if (check.warnOnly) {
            console.log(`${yellow}WARN${reset}`);
            if (manual.note) {
                console.log(`  ${manual.note}`);
            }
            console.log(`  ${check.fix}`);
            continue;
        }
        if (check.infoOnly) {
            console.log(`${cyan}INFO${reset}`);
            if (manual.note) {
                console.log(`  ${manual.note}`);
            }
            console.log(`  ${check.fix}`);
            continue;
        }
        console.log(`${red}FAILED${reset}`);
        if (manual.note) {
            console.log(`  ${manual.note}`);
        }
        console.log(`  ${check.fix}`);
        failed = true;
        continue;
    }

    const proc = runSync(check.cmd);
    const stdout = proc.stdout;
    const stderr = proc.stderr;

    if (proc.threw || proc.exitCode !== 0) {
        if (check.autoFix) {
            process.stdout.write(`${yellow}FIXING...${reset} `);
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            if (fixProc.exitCode === 0) {
                console.log(`${green}FIXED${reset}`);
                continue;
            }
        }

        if (check.warnOnly) {
            console.log(`${yellow}WARN${reset}`);
            console.log(`  ${check.fix}`);
            continue;
        }
        if (check.infoOnly) {
            console.log(`${cyan}INFO${reset}`);
            console.log(`  ${check.fix}`);
            continue;
        }
        console.log(`${red}MISSING${reset}`);
        console.log(`  ${check.fix}`);
        failed = true;
        continue;
    }

    if (check.check && !check.check(stdout, stderr)) {
        if (check.autoFix) {
            process.stdout.write(`${yellow}FIXING...${reset} `);
            const fixProc = spawnSync(check.autoFix, {
                stdout: 'inherit',
                stderr: 'inherit',
                env: mergedEnv(),
            });
            if (fixProc.exitCode === 0) {
                console.log(`${green}FIXED${reset}`);
                continue;
            }
        }

        if (check.warnOnly) {
            console.log(`${yellow}WARN${reset}`);
            console.log(`  ${check.fix}`);
            continue;
        }
        if (check.infoOnly) {
            console.log(`${cyan}INFO${reset}`);
            console.log(`  ${check.fix}`);
            continue;
        }

        console.log(`${red}FAILED${reset}`);
        console.log(`  ${check.fix}`);
        failed = true;
        continue;
    }

    console.log(`${green}OK${reset}`);
}

if (failed) {
    console.log(`\n${red}[!] Host verification failed. Resolve the failing checks above.${reset}`);
    process.exit(1);
}

console.log(`\n${green}[+] Host verification passed. Ready for Oxidation.${reset}`);
