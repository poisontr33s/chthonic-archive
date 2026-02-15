import { spawnSync } from 'bun';
import { existsSync } from 'fs';
import path from 'path';

type HostCheck = {
    name: string;
    cmd: string[];
    check?: (stdout: string, stderr: string) => boolean;
    autoFix?: string[];
    manualCheck?: () => ManualCheckResult;
    fix: string;
    warnOnly?: boolean;
};

type ManualCheckResult = {
    ok: boolean;
    note?: string;
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

    for (const root of roots) {
        const candidate = path.join(root, 'msys64', 'usr', 'bin', 'perl.exe');
        if (existsSync(candidate)) {
            return candidate;
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

console.log(`${cyan}[Chthonic] Running Preflight Host Verification...${reset}`);

const checks: HostCheck[] = [
    {
        name: 'Rust Toolchain',
        cmd: ['rustc', '--version'],
        fix: 'Install Rust via rustup: https://rustup.rs',
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
            const value = envOverrides.MAKEFLAGS ?? process.env.MAKEFLAGS;
            if (!value || value.trim().length === 0) {
                return { ok: true };
            }
            return { ok: false, note: `MAKEFLAGS=${value}` };
        },
        warnOnly: true,
        fix: 'Unset MAKEFLAGS for MSVC OpenSSL builds. The ledger wrapper script strips it automatically.',
    },
    {
        name: 'Solana CLI',
        cmd: ['solana', '--version'],
        warnOnly: true,
        fix: 'Install Solana Tool Suite for local validator mode.',
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
