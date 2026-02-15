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

    // nmake (MSVC OpenSSL path) fails when GNU make flags leak.
    delete env.MAKEFLAGS;
    delete env.MFLAGS;

    // shaderc-sys requires cmake
    ensureCmake(env);

    if (process.platform === 'win32') {
        ensureWindowsPerl(env);
    }

    await run(
        ['cargo', 'build', '--manifest-path', workspaceManifestPath, '-p', 'chthonic-daemon', '--release'],
        env,
    );
    console.log('[daemon] build completed');
}

function ensureCmake(env: Record<string, string>): void {
    const result = runCapture('cmake', ['--version'], env);
    if (!result.ok) {
        throw new Error(
            'cmake not found. shaderc requires cmake for SPIR-V compilation.\n'
            + 'Install: winget install Kitware.CMake (Windows) or apt install cmake (Linux)',
        );
    }
    console.log(`[daemon] cmake: ${result.stdout.split('\n')[0].trim()}`);
}

function ensureWindowsPerl(env: Record<string, string>): void {
    const current = runCapture('perl', ['--version'], env);
    if (current.ok && !isCygwinPerl(current.stdout, current.stderr)) {
        return;
    }

    const devkitPerl = findDevKitPerl(env);
    if (!devkitPerl) {
        console.warn('[daemon] Ruby DevKit perl not found; vendored OpenSSL may fail to build.');
        return;
    }

    const perlDir = path.dirname(devkitPerl);
    env.PATH = prependPath(perlDir, env.PATH ?? '');
    env.PERL = devkitPerl;
    console.log(`[daemon] using Ruby DevKit perl: ${devkitPerl}`);
}

function findDevKitPerl(env: Record<string, string>): string | null {
    const roots = [
        rubyInstallRoot(env),
        'C:\\Ruby40-x64',
        'C:\\Ruby35-x64',
        'C:\\Ruby34-x64',
        'C:\\Ruby33-x64',
        'C:\\Ruby32-x64',
        'D:\\Ruby40-x64',
        'D:\\Ruby35-x64',
        'D:\\Ruby34-x64',
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
    console.error(`[daemon] build failed: ${message}`);
    process.exitCode = 1;
});
