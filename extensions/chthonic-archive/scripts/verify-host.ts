import { spawnSync } from 'bun';

type HostCheck = {
    name: string;
    cmd: string[];
    check?: (stdout: string, stderr: string) => boolean;
    autoFix?: string[];
    fix: string;
    warnOnly?: boolean;
};

const cyan = '\x1b[36m';
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const red = '\x1b[31m';
const reset = '\x1b[0m';

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
        fix: 'Install wasm-bindgen CLI: cargo install wasm-bindgen-cli',
    },
    {
        name: 'Perl (OpenSSL build)',
        cmd: ['perl', '--version'],
        check: (stdout) => !stdout.toLowerCase().includes('cygwin'),
        fix: 'Install Strawberry Perl or a Windows-native Perl (Git Bash/Cygwin Perl can fail OpenSSL VC builds).',
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
    let proc:
        | {
            exitCode: number;
            stdout: Buffer | Uint8Array;
            stderr: Buffer | Uint8Array;
        }
        | null = null;

    try {
        const result = spawnSync(check.cmd, {
            stdout: 'pipe',
            stderr: 'pipe',
        });
        proc = {
            exitCode: result.exitCode,
            stdout: result.stdout,
            stderr: result.stderr,
        };
    } catch {
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

    const stdout = Buffer.from(proc.stdout).toString();
    const stderr = Buffer.from(proc.stderr).toString();

    if (proc.exitCode !== 0) {
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
