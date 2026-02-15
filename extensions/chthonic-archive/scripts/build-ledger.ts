import { existsSync } from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';

const extensionRoot = process.cwd();
const workspaceManifestPath = path.join(extensionRoot, 'native', 'Cargo.toml');

async function main(): Promise<void> {
    if (!existsSync(workspaceManifestPath)) {
        throw new Error(`missing Rust workspace manifest: ${workspaceManifestPath}`);
    }

    const env: Record<string, string> = {
        ...process.env,
    };

    // nmake (MSVC OpenSSL path) fails when GNU make flags leak into the environment.
    delete env.MAKEFLAGS;
    delete env.MFLAGS;

    if (process.platform === 'win32') {
        ensureWindowsPerl(env);
    }

    await run(
        ['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'entropy-ledger-host', '--release'],
        env,
    );
    console.log('[ledger] build completed');
}

function ensureWindowsPerl(env: Record<string, string>): void {
    const current = runCapture('perl', ['--version'], env);
    if (current.ok && !isCygwinPerl(current.stdout, current.stderr)) {
        return;
    }

    const devkitPerl = findDevKitPerl(env);
    if (!devkitPerl) {
        throw new Error(
            'Ruby DevKit perl not found. Install RubyInstaller with DevKit and run `ridk install 3` before building ledger host.',
        );
    }

    const perlDir = path.dirname(devkitPerl);
    env.PATH = prependPath(perlDir, env.PATH ?? '');
    env.PERL = devkitPerl;

    const probe = runCapture('perl', ['--version'], env);
    if (!probe.ok || isCygwinPerl(probe.stdout, probe.stderr)) {
        throw new Error(`failed to activate Ruby DevKit perl at ${devkitPerl}`);
    }

    console.log(`[ledger] using Ruby DevKit perl: ${devkitPerl}`);
}

function findDevKitPerl(env: Record<string, string>): string | null {
    const roots = [
        rubyInstallRoot(env),
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

function rubyInstallRoot(env: Record<string, string>): string | null {
    const ruby = runCapture('ruby', ['-e', 'print RbConfig.ruby'], env);
    if (!ruby.ok) {
        return null;
    }
    const rubyExe = ruby.stdout.trim();
    if (!rubyExe) {
        return null;
    }
    return path.dirname(path.dirname(rubyExe));
}

function isCygwinPerl(stdout: string, stderr: string): boolean {
    const combined = `${stdout}\n${stderr}`.toLowerCase();
    return combined.includes('cygwin');
}

function prependPath(segment: string, currentPath: string): string {
    const delimiter = process.platform === 'win32' ? ';' : ':';
    const parts = currentPath.split(delimiter).filter(Boolean);
    if (parts.some((part) => part.toLowerCase() === segment.toLowerCase())) {
        return currentPath;
    }
    return currentPath.length > 0 ? `${segment}${delimiter}${currentPath}` : segment;
}

function runCapture(command: string, args: string[], env: Record<string, string>): {
    ok: boolean;
    stdout: string;
    stderr: string;
} {
    try {
        const result = spawnSync(command, args, {
            cwd: extensionRoot,
            env,
            encoding: 'utf8',
        });
        return {
            ok: result.status === 0,
            stdout: result.stdout ?? '',
            stderr: result.stderr ?? '',
        };
    } catch {
        return {
            ok: false,
            stdout: '',
            stderr: '',
        };
    }
}

async function run(cmd: string[], env: Record<string, string>): Promise<void> {
    const proc = Bun.spawn(cmd, {
        cwd: extensionRoot,
        stdout: 'inherit',
        stderr: 'inherit',
        stdin: 'inherit',
        env,
    });
    const code = await proc.exited;
    if (code !== 0) {
        throw new Error(`${cmd.join(' ')} exited with code ${code}`);
    }
}

void main().catch((error) => {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    console.error(`[ledger] build failed: ${message}`);
    process.exitCode = 1;
});
