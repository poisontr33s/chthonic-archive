import * as fs from 'fs';
import * as path from 'path';
import { spawnSync } from 'child_process';

type ScanOptions = {
    json: boolean;
    quiet: boolean;
    writeEnv: boolean;
};

type CliProbe = {
    name: string;
    path: string | null;
    exists: boolean;
    version: string | null;
    exitCode: number;
    stderr: string | null;
};

type BinaryProbe = {
    name: string;
    path: string;
    exists: boolean;
    source: string;
};

type VsInstance = {
    product: string;
    instanceId: string;
    installationPath: string;
    installationVersion: string;
    channelId: string | null;
    msvcRoot: string | null;
};

type ToolpoolReport = {
    timestamp: string;
    host: {
        platform: NodeJS.Platform;
        release: string;
        arch: string;
    };
    output: {
        reportPath: string;
        envPath: string;
    };
    vs: {
        professional: VsInstance | null;
        buildTools: VsInstance | null;
    };
    sql: {
        sqlPackagePath: string | null;
        source: string | null;
    };
    binaries: BinaryProbe[];
    commands: CliProbe[];
    recommendedLanes: {
        native: string;
        python: string;
        ruby: string;
        go: string;
        node: string;
        sql: string;
        infra: string;
    };
};

type ExecResult = {
    exitCode: number;
    stdout: string;
    stderr: string;
    error: string | null;
};

const extensionRoot = process.cwd();
const cacheDir = path.join(extensionRoot, '.chthonic', 'cache');
const reportPath = path.join(cacheDir, 'toolpool.json');
const envPath = path.join(cacheDir, 'toolpool.env');

const args = new Set(process.argv.slice(2));
const options: ScanOptions = {
    json: args.has('--json'),
    quiet: args.has('--quiet'),
    writeEnv: args.has('--write-env'),
};

function execCapture(command: string, argv: string[]): ExecResult {
    try {
        const result = spawnSync(command, argv, {
            cwd: extensionRoot,
            windowsHide: true,
            timeout: 12_000,
            encoding: 'utf8',
        });
        return {
            exitCode: result.status ?? 1,
            stdout: (result.stdout ?? '').trim(),
            stderr: (result.stderr ?? '').trim(),
            error: result.error ? String(result.error.message || result.error) : null,
        };
    } catch (error) {
        return {
            exitCode: 1,
            stdout: '',
            stderr: '',
            error: stringifyError(error),
        };
    }
}

function resolveCommandPath(command: string): string | null {
    if (process.platform === 'win32') {
        const where = execCapture('where', [command]);
        if (where.exitCode !== 0 || !where.stdout) {
            return null;
        }
        return where.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0] ?? null;
    }

    const which = execCapture('which', [command]);
    if (which.exitCode !== 0 || !which.stdout) {
        return null;
    }
    return which.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0] ?? null;
}

function probeCommand(name: string, argv: string[]): CliProbe {
    const resolved = resolveCommandPath(name);
    if (!resolved) {
        return {
            name,
            path: null,
            exists: false,
            version: null,
            exitCode: 127,
            stderr: null,
        };
    }

    const run = execCapture(name, argv);
    const version = run.stdout ? run.stdout.split(/\r?\n/)[0].trim() : null;
    return {
        name,
        path: resolved,
        exists: true,
        version,
        exitCode: run.exitCode,
        stderr: run.stderr || run.error,
    };
}

function resolveVswherePath(): string | null {
    const candidate = path.join('C:', 'Program Files (x86)', 'Microsoft Visual Studio', 'Installer', 'vswhere.exe');
    return fs.existsSync(candidate) ? candidate : null;
}

function parseVsInstance(raw: unknown, product: string): VsInstance | null {
    if (!raw || typeof raw !== 'object') {
        return null;
    }

    const typed = raw as Record<string, unknown>;
    const installationPath = typeof typed.installationPath === 'string' ? typed.installationPath : null;
    const instanceId = typeof typed.instanceId === 'string' ? typed.instanceId : null;
    const installationVersion = typeof typed.installationVersion === 'string' ? typed.installationVersion : '';
    const channelId = typeof typed.channelId === 'string' ? typed.channelId : null;

    if (!installationPath || !instanceId) {
        return null;
    }

    return {
        product,
        instanceId,
        installationPath,
        installationVersion,
        channelId,
        msvcRoot: resolveLatestMsvcRoot(installationPath),
    };
}

function getLatestVsInstance(vswhere: string, productId: string, product: string): VsInstance | null {
    const probe = execCapture(vswhere, ['-prerelease', '-latest', '-products', productId, '-format', 'json']);
    if (probe.exitCode !== 0 || !probe.stdout) {
        return null;
    }

    try {
        const parsed = JSON.parse(probe.stdout) as unknown;
        if (Array.isArray(parsed)) {
            return parseVsInstance(parsed[0], product);
        }
        return parseVsInstance(parsed, product);
    } catch {
        return null;
    }
}

function resolveLatestMsvcRoot(installPath: string): string | null {
    const root = path.join(installPath, 'VC', 'Tools', 'MSVC');
    if (!fs.existsSync(root)) {
        return null;
    }

    const dirs = fs.readdirSync(root, { withFileTypes: true })
        .filter((entry) => entry.isDirectory())
        .map((entry) => path.join(root, entry.name))
        .sort((a, b) => b.localeCompare(a, undefined, { numeric: true, sensitivity: 'base' }));

    return dirs[0] ?? null;
}

function resolveWindowsKitRc(): string | null {
    const sdkBinRoot = path.join('C:', 'Program Files (x86)', 'Windows Kits', '10', 'bin');
    if (!fs.existsSync(sdkBinRoot)) {
        return null;
    }

    const candidates = fs.readdirSync(sdkBinRoot, { withFileTypes: true })
        .filter((entry) => entry.isDirectory())
        .map((entry) => path.join(sdkBinRoot, entry.name, 'x64', 'rc.exe'))
        .filter((candidate) => fs.existsSync(candidate))
        .sort((a, b) => b.localeCompare(a, undefined, { numeric: true, sensitivity: 'base' }));

    return candidates[0] ?? null;
}

function resolveSqlPackage(pro: VsInstance | null, bt: VsInstance | null): { path: string | null; source: string | null } {
    const candidates: Array<{ source: string; path: string }> = [];

    if (process.env.SQL_DEV_KIT_PATH) {
        candidates.push({
            source: 'env:SQL_DEV_KIT_PATH',
            path: path.join(process.env.SQL_DEV_KIT_PATH, 'SqlPackage.exe'),
        });
    }

    for (const vs of [pro, bt]) {
        if (!vs) {
            continue;
        }
        candidates.push({
            source: `${vs.product}:sqldb`,
            path: path.join(vs.installationPath, 'Common7', 'IDE', 'Extensions', 'Microsoft', 'SQLDB', 'DAC', 'SqlPackage.exe'),
        });
    }

    const ssmsVersions = ['21', '20', '19'];
    for (const major of ssmsVersions) {
        candidates.push({
            source: `ssms-${major}`,
            path: path.join('C:', 'Program Files', `Microsoft SQL Server Management Studio ${major}`, 'Common7', 'IDE', 'Extensions', 'Microsoft', 'SQLDB', 'DAC', 'SqlPackage.exe'),
        });
        candidates.push({
            source: `ssms-${major}-x86`,
            path: path.join('C:', 'Program Files (x86)', `Microsoft SQL Server Management Studio ${major}`, 'Common7', 'IDE', 'Extensions', 'Microsoft', 'SQLDB', 'DAC', 'SqlPackage.exe'),
        });
    }

    for (const candidate of candidates) {
        if (fs.existsSync(candidate.path)) {
            return {
                path: candidate.path,
                source: candidate.source,
            };
        }
    }

    return { path: null, source: null };
}

function probeBinary(name: string, filePath: string | null, source: string): BinaryProbe {
    return {
        name,
        path: filePath ?? '',
        exists: Boolean(filePath && fs.existsSync(filePath)),
        source,
    };
}

function hasCommand(commands: CliProbe[], name: string): boolean {
    return commands.some((entry) => entry.name === name && entry.exists);
}

function determineNativeLane(binaries: BinaryProbe[], pro: VsInstance | null, bt: VsInstance | null): string {
    const hasCl = binaries.some((item) => item.name === 'cl.exe' && item.exists);
    const hasCmake = binaries.some((item) => item.name === 'cmake.exe' && item.exists);
    const hasNinja = binaries.some((item) => item.name === 'ninja.exe' && item.exists);
    if (hasCl && hasCmake && hasNinja && pro) {
        return 'vs2026-professional-insider';
    }
    if (hasCl && hasCmake && hasNinja && bt) {
        return 'vs2026-buildtools-insider';
    }
    return 'legacy-or-incomplete';
}

function determineInfraLane(commands: CliProbe[]): string {
    const hasAz = hasCommand(commands, 'az');
    const hasBicep = hasCommand(commands, 'bicep');
    if (hasAz && hasBicep) {
        return 'az+bicep-ready';
    }
    if (hasAz) {
        return 'az-only';
    }
    if (hasBicep) {
        return 'bicep-only';
    }
    return 'not-provisioned';
}

function writeEnvFile(report: ToolpoolReport): void {
    const lines: string[] = [];
    lines.push(`# generated ${report.timestamp}`);
    lines.push(`CHTHONIC_TOOLPOOL_REPORT=${quoteEnv(report.output.reportPath)}`);
    lines.push(`CHTHONIC_NATIVE_LANE=${quoteEnv(report.recommendedLanes.native)}`);
    lines.push(`CHTHONIC_SQL_LANE=${quoteEnv(report.recommendedLanes.sql)}`);

    if (report.vs.professional) {
        lines.push(`VSINSTALLDIR=${quoteEnv(report.vs.professional.installationPath)}`);
        lines.push(`VCINSTALLDIR=${quoteEnv(path.join(report.vs.professional.installationPath, 'VC'))}`);
    } else if (report.vs.buildTools) {
        lines.push(`VSINSTALLDIR=${quoteEnv(report.vs.buildTools.installationPath)}`);
        lines.push(`VCINSTALLDIR=${quoteEnv(path.join(report.vs.buildTools.installationPath, 'VC'))}`);
    }

    const msvc = report.vs.professional?.msvcRoot ?? report.vs.buildTools?.msvcRoot ?? null;
    if (msvc) {
        lines.push(`CHTHONIC_MSVC_ROOT=${quoteEnv(msvc)}`);
    }

    const rcBinary = report.binaries.find((item) => item.name === 'rc.exe' && item.exists);
    if (rcBinary) {
        lines.push(`CHTHONIC_WINSDK_RC=${quoteEnv(rcBinary.path)}`);
    }

    if (report.sql.sqlPackagePath) {
        lines.push(`CHTHONIC_SQLPACKAGE_PATH=${quoteEnv(report.sql.sqlPackagePath)}`);
    }

    fs.writeFileSync(envPath, `${lines.join('\n')}\n`, 'utf8');
}

function quoteEnv(value: string): string {
    return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}`;
    }
    return String(error);
}

function run(): void {
    if (process.platform !== 'win32') {
        throw new Error('toolpool-scan is currently implemented for Windows hosts only.');
    }

    fs.mkdirSync(cacheDir, { recursive: true });

    const vswhere = resolveVswherePath();
    const pro = vswhere ? getLatestVsInstance(vswhere, 'Microsoft.VisualStudio.Product.Professional', 'professional') : null;
    const bt = vswhere ? getLatestVsInstance(vswhere, 'Microsoft.VisualStudio.Product.BuildTools', 'build-tools') : null;

    const msvcRoot = pro?.msvcRoot ?? bt?.msvcRoot ?? null;
    const installRoot = pro?.installationPath ?? bt?.installationPath ?? null;
    const rcBinary = resolveWindowsKitRc();
    const sql = resolveSqlPackage(pro, bt);

    const binaries: BinaryProbe[] = [
        probeBinary('cl.exe', msvcRoot ? path.join(msvcRoot, 'bin', 'Hostx64', 'x64', 'cl.exe') : null, 'msvc'),
        probeBinary('clang-cl.exe', installRoot ? path.join(installRoot, 'VC', 'Tools', 'Llvm', 'x64', 'bin', 'clang-cl.exe') : null, 'llvm'),
        probeBinary('lld-link.exe', installRoot ? path.join(installRoot, 'VC', 'Tools', 'Llvm', 'x64', 'bin', 'lld-link.exe') : null, 'llvm'),
        probeBinary('cmake.exe', installRoot ? path.join(installRoot, 'Common7', 'IDE', 'CommonExtensions', 'Microsoft', 'CMake', 'CMake', 'bin', 'cmake.exe') : null, 'vs-cmake'),
        probeBinary('ninja.exe', installRoot ? path.join(installRoot, 'Common7', 'IDE', 'CommonExtensions', 'Microsoft', 'CMake', 'Ninja', 'ninja.exe') : null, 'vs-cmake'),
        probeBinary('rc.exe', rcBinary, 'windows-sdk'),
        probeBinary('SqlPackage.exe', sql.path, sql.source ?? 'sql'),
        probeBinary('libcmt.lib (spectre)', msvcRoot ? path.join(msvcRoot, 'lib', 'spectre', 'x64', 'libcmt.lib') : null, 'msvc-spectre'),
    ];

    const commandArgs = new Map<string, string[]>([
        ['mise', ['--version']],
        ['uv', ['--version']],
        ['rv', ['--version']],
        ['ruby', ['--version']],
        ['goup', ['--version']],
        ['go', ['version']],
        ['rustc', ['--version']],
        ['cargo', ['--version']],
        ['solana', ['--version']],
        ['solana-install', ['--version']],
        ['agave-install', ['--version']],
        ['bun', ['--version']],
        ['az', ['version', '--query', '"azure-cli"', '--output', 'tsv']],
        ['bicep', ['--version']],
        ['kubectl', ['version', '--client=true', '--short=true']],
        ['terraform', ['version']],
        ['pwsh', ['--version']],
    ]);

    const commands = [...commandArgs.entries()].map(([name, argv]) => probeCommand(name, argv));

    const report: ToolpoolReport = {
        timestamp: new Date().toISOString(),
        host: {
            platform: process.platform,
            release: process.release.name,
            arch: process.arch,
        },
        output: {
            reportPath,
            envPath,
        },
        vs: {
            professional: pro,
            buildTools: bt,
        },
        sql: {
            sqlPackagePath: sql.path,
            source: sql.source,
        },
        binaries,
        commands,
        recommendedLanes: {
            native: determineNativeLane(binaries, pro, bt),
            python: hasCommand(commands, 'uv') ? 'uv' : 'python-system',
            ruby: hasCommand(commands, 'rv') ? 'rv' : (hasCommand(commands, 'ruby') ? 'ruby-system' : 'ruby-missing'),
            go: hasCommand(commands, 'goup') ? 'goup' : (hasCommand(commands, 'go') ? 'go-system' : 'go-missing'),
            node: hasCommand(commands, 'bun') ? 'bun' : 'node-missing',
            sql: sql.path ? (sql.source?.startsWith('ssms') ? 'ssms-dacfx' : 'vs-dacfx') : 'sqlpackage-missing',
            infra: determineInfraLane(commands),
        },
    };

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
    if (options.writeEnv) {
        writeEnvFile(report);
    }

    if (options.json) {
        process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
        return;
    }

    if (!options.quiet) {
        const commandFound = report.commands.filter((entry) => entry.exists).length;
        const binaryFound = report.binaries.filter((entry) => entry.exists).length;
        console.log(`[toolpool] report: ${reportPath}`);
        console.log(`[toolpool] binaries: ${binaryFound}/${report.binaries.length} present`);
        console.log(`[toolpool] commands: ${commandFound}/${report.commands.length} present`);
        console.log(`[toolpool] lane: native=${report.recommendedLanes.native}`);
        console.log(`[toolpool]   |- sql=${report.recommendedLanes.sql}`);
        console.log(`[toolpool]   \\- infra=${report.recommendedLanes.infra}`);
        if (options.writeEnv) {
            console.log(`[toolpool] env: ${envPath}`);
        }
    }
}

try {
    run();
} catch (error) {
    console.error(`[toolpool] scan failed: ${stringifyError(error)}`);
    process.exitCode = 1;
}
