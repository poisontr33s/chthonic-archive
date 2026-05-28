#!/usr/bin/env bun
// @SID: TOOL_SPREAD_SWEEP_V1
// ============================================================
// spread-sweep — wide-angle structured-data discovery across the
// user's polyglot project surface. No-dead-code stance: index
// everything found, let downstream filtering decide what's hot.
//
// Auto-glob-tracked via manifest/*_index.{json,md} per the
// gitological lens stack convention.
//
// Usage:
//   bun run scripts/spread-sweep.ts                          # default: scan parent of cwd
//   bun run scripts/spread-sweep.ts --roots <dir1>,<dir2>
//   bun run scripts/spread-sweep.ts --output manifest/spread_index.json
//   bun run scripts/spread-sweep.ts --max-depth 4 --summary
//
// Discovers:
//   - Node-family projects (package.json present)
//   - Rust crates / workspaces (Cargo.toml present)
// Extracts:
//   - Project metadata (name, version, deps, scripts, framework heuristics)
//   - File-type histogram (top-level src/ + root counts by extension)
//   - Package manager hint (from lockfile presence: bun.lock, package-lock.json, yarn.lock, pnpm-lock.yaml)
//   - Workspace membership detection
//
// Output shape mirrors manifest/<lens>_index.json convention:
//   { generated_at, root_dirs, project_count, projects: [...] }
// ============================================================

import { readdirSync, readFileSync, statSync, existsSync, mkdirSync } from 'node:fs';
import { join, resolve, relative, basename, dirname, sep } from 'node:path';

// ─── CLI args ─────────────────────────────────────────────────────────────
interface Args {
    roots: string[];
    output: string;
    maxDepth: number;
    summary: boolean;
    quiet: boolean;
}

function parseArgs(argv: string[]): Args {
    const args: Args = {
        roots: [],
        output: 'manifest/spread_index.json',
        maxDepth: 6,
        summary: false,
        quiet: false,
    };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--roots' && argv[i + 1]) {
            args.roots = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
        } else if (a === '--output' && argv[i + 1]) {
            args.output = argv[++i];
        } else if (a === '--max-depth' && argv[i + 1]) {
            args.maxDepth = parseInt(argv[++i], 10);
        } else if (a === '--summary') {
            args.summary = true;
        } else if (a === '--quiet') {
            args.quiet = true;
        } else if (a === '--help' || a === '-h') {
            console.log(
                'Usage: bun run scripts/spread-sweep.ts [--roots a,b,c] [--output path] [--max-depth N] [--summary] [--quiet]',
            );
            process.exit(0);
        }
    }
    if (args.roots.length === 0) {
        // Default: the parent dir of cwd, which holds the user's sibling project workspaces.
        args.roots = [resolve(process.cwd(), '..')];
    }
    return args;
}

// ─── Skip set ─────────────────────────────────────────────────────────────
// Directories never worth descending into (heavy, derived, or noise).
const SKIP_DIRS = new Set([
    'node_modules', 'target', 'dist', 'build', 'out', '.git', '.next', '.nuxt',
    '.cache', '.turbo', '.vite', '.parcel-cache', '.svelte-kit', '.angular',
    '__pycache__', '.venv', 'venv', 'env', '.tox', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'vendor', 'Pods', '.gradle', '.idea', '.vscode-test',
    'coverage', '.nyc_output', '.jest-cache',
    'tmp', '.tmp', 'temp', '.temp',
]);

// Path substrings that indicate vendored / third-party / install-tree content.
// Projects whose absolute path contains any of these are filtered out of the index.
// Normalized to forward slashes before matching so the patterns work on Windows + POSIX.
const VENDORED_PATH_PATTERNS = [
    'vcpkg/buildtrees',
    'vcpkg/packages',
    'vcpkg/installed',
    '.cargo/registry',
    '.cargo/git/checkouts',
    'rv/library/',           // R package library installs
    'rv-test-rubies',        // bundled Ruby build trees
    '/buildtrees/',
    '/.rustup/',
    'AppData/Local/Programs/',   // Windows installed apps
    'AppData/Roaming/',
    '/site-packages/',
    '/.gem/',
    '/Library/Caches/',
];

function isVendoredPath(absPath: string): boolean {
    const norm = absPath.replace(/\\/g, '/');
    return VENDORED_PATH_PATTERNS.some(p => norm.includes(p));
}

// Files that, when present at a project root, suggest the project is a vendored
// upstream-installed copy (LICENSE typically at the root of a published package).
// Used as a *secondary* signal — combined with depth >= 3 from the scan root.
const LICENSE_FILENAMES = new Set([
    'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'LICENSE.rst',
    'LICENCE', 'LICENCE.md', 'LICENCE.txt',
    'COPYING', 'COPYING.txt', 'COPYING.md',
]);

function looksLikeInstalledPackage(dir: string, entries: string[], depthFromRoot: number): boolean {
    // Heuristic: deep in the tree + has LICENSE + has no signs of active dev (no .git, no scripts dir)
    if (depthFromRoot < 3) return false;
    const hasLicense = entries.some(n => LICENSE_FILENAMES.has(n));
    if (!hasLicense) return false;
    // If it has a .git dir or a typical project root structure, it's user code with a license.
    if (entries.includes('.git')) return false;
    if (entries.includes('CHANGELOG.md') && entries.includes('package.json')) {
        // Could be either; lean on path-pattern check above
        return false;
    }
    return true;
}

// File extensions worth counting (per project root) — wide spread.
const COUNTED_EXTS = new Set([
    // TS/JS family
    '.ts', '.tsx', '.mts', '.cts',
    '.js', '.jsx', '.mjs', '.cjs',
    // Rust + config
    '.rs', '.toml',
    // C/C++ family
    '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh', '.hxx', '.inl',
    // CUDA / GPU compute
    '.cu', '.cuh', '.ptx',
    // Vulkan / shader family
    '.glsl', '.vert', '.frag', '.comp', '.tesc', '.tese', '.geom',
    '.spv', '.hlsl', '.wgsl', '.metal',
    // Native peers
    '.zig', '.swift', '.kt', '.java', '.cs', '.mm', '.m',
    '.nim', '.v', '.scala', '.clj', '.ex', '.exs', '.lua', '.dart',
    '.ml', '.mli', '.fs', '.fsx', '.hs',
    // Scripting / data
    '.py', '.go', '.rb', '.pl', '.r', '.jl',
    '.json', '.yaml', '.yml', '.md',
    '.vue', '.svelte', '.astro',
    '.html', '.css', '.scss', '.sass', '.less',
    // Build / pkg config
    '.lock',
]);

// Source-code extensions (line counts get computed for these; configs only get file counts)
const SOURCE_EXTS = new Set([
    '.ts', '.tsx', '.mts', '.cts',
    '.js', '.jsx', '.mjs', '.cjs',
    '.rs',
    '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh', '.hxx', '.inl',
    '.cu', '.cuh',
    '.glsl', '.vert', '.frag', '.comp', '.tesc', '.tese', '.geom',
    '.hlsl', '.wgsl', '.metal',
    '.zig', '.swift', '.kt', '.java', '.cs', '.mm', '.m',
    '.nim', '.v', '.scala', '.clj', '.ex', '.exs', '.lua', '.dart',
    '.ml', '.mli', '.fs', '.fsx', '.hs',
    '.py', '.go', '.rb', '.pl', '.r', '.jl',
    '.vue', '.svelte', '.astro',
]);

// Config files worth recording by full name (in addition to extension-based counts)
const CONFIG_FILENAMES = new Set([
    'tsconfig.json', 'tsconfig.base.json',
    'rust-toolchain.toml', 'rust-toolchain',
    'vite.config.ts', 'vite.config.js', 'vite.config.mjs',
    'vitest.config.ts', 'vitest.config.js',
    'esbuild.config.ts', 'esbuild.config.js', 'esbuild.config.mjs',
    'rollup.config.ts', 'rollup.config.js', 'rollup.config.mjs',
    'webpack.config.ts', 'webpack.config.js',
    'biome.json', 'biome.jsonc',
    'eslint.config.js', 'eslint.config.mjs', '.eslintrc.json', '.eslintrc.js',
    'prettier.config.js', '.prettierrc.json', '.prettierrc',
    'tailwind.config.ts', 'tailwind.config.js',
    'postcss.config.js', 'postcss.config.ts',
    'jest.config.ts', 'jest.config.js',
    'turbo.json', 'nx.json',
    'pyproject.toml', 'uv.toml', 'requirements.txt', 'setup.py',
    'CMakeLists.txt', 'meson.build', 'Makefile', 'BUILD', 'BUILD.bazel',
    'shader.toml', 'shaderc.toml',
    '.cargo/config.toml',
    'bunfig.toml',
    'deno.json', 'deno.jsonc',
]);

// ─── Project discovery ────────────────────────────────────────────────────
interface ProjectMarker {
    path: string; // absolute dir
    rel: string; // relative to scan root
    has_package_json: boolean;
    has_cargo_toml: boolean;
}

function walkForProjects(root: string, maxDepth: number): ProjectMarker[] {
    const found: ProjectMarker[] = [];
    const rootResolved = resolve(root);

    function walk(dir: string, depth: number) {
        if (depth > maxDepth) return;

        let entries: string[];
        try {
            entries = readdirSync(dir);
        } catch {
            return;
        }

        const hasPkg = entries.includes('package.json');
        const hasCargo = entries.includes('Cargo.toml');

        if (hasPkg || hasCargo) {
            // Vendored-path filter: skip if anywhere in the install-tree patterns.
            const vendored = isVendoredPath(dir);
            const installed = looksLikeInstalledPackage(dir, entries, depth);
            if (vendored || installed) {
                // Don't record this as a project, and don't descend.
                return;
            }
            found.push({
                path: dir,
                rel: relative(rootResolved, dir) || '.',
                has_package_json: hasPkg,
                has_cargo_toml: hasCargo,
            });
            // At depth 0 (the scan root itself), always keep descending — the root
            // may have its own package.json (user-home globals like @anthropic-ai/claude-code)
            // while still containing sibling workspace subdirs.
            // At deeper depths, don't descend past a project boundary unless it's
            // monorepo-shaped (packages/, apps/, crates/, tools/ children present).
            if (depth > 0) {
                const looksLikeMonorepo = entries.includes('packages') || entries.includes('apps') || entries.includes('crates') || entries.includes('tools');
                if (!looksLikeMonorepo) return;
            }
        }

        for (const name of entries) {
            if (name.startsWith('.') && name !== '.github') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(dir, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) {
                walk(full, depth + 1);
            }
        }
    }

    walk(rootResolved, 0);
    return found;
}

// ─── Per-project extraction ───────────────────────────────────────────────
interface ExtCounts { [ext: string]: number; }

interface ScanResult {
    file_counts: ExtCounts;
    line_counts: ExtCounts;
    config_files_found: string[]; // relative paths
    files_visited: number;
    files_capped: boolean;
}

// Per-file size cap for line counting — don't open multi-MB blobs.
const MAX_FILE_BYTES_FOR_LINECOUNT = 2 * 1024 * 1024;

function countLines(path: string, sizeBytes: number): number {
    if (sizeBytes > MAX_FILE_BYTES_FOR_LINECOUNT) {
        // Approximate by file-size / 50 (rough avg bytes/line); flagged
        // implicitly by being too large to read.
        return Math.round(sizeBytes / 50);
    }
    try {
        const buf = readFileSync(path);
        let n = 0;
        for (let i = 0; i < buf.length; i++) {
            if (buf[i] === 0x0a) n++; // LF
        }
        // Count last line if file doesn't end with newline
        if (buf.length > 0 && buf[buf.length - 1] !== 0x0a) n++;
        return n;
    } catch {
        return 0;
    }
}

function scanProjectFiles(dir: string, maxFiles: number = 5000): ScanResult {
    const result: ScanResult = {
        file_counts: {},
        line_counts: {},
        config_files_found: [],
        files_visited: 0,
        files_capped: false,
    };

    function walk(d: string, depth: number) {
        if (result.files_visited >= maxFiles) {
            result.files_capped = true;
            return;
        }
        if (depth > 4) return;
        let entries: string[];
        try { entries = readdirSync(d); } catch { return; }
        for (const name of entries) {
            if (result.files_visited >= maxFiles) {
                result.files_capped = true;
                return;
            }
            if (name.startsWith('.') && name !== '.github' && name !== '.cargo') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(d, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) {
                walk(full, depth + 1);
            } else if (st.isFile()) {
                result.files_visited++;
                // Config file detection by full name
                if (CONFIG_FILENAMES.has(name)) {
                    result.config_files_found.push(relative(dir, full));
                }
                // Extension-based counting
                const dotIdx = name.lastIndexOf('.');
                if (dotIdx > 0) {
                    const ext = name.substring(dotIdx).toLowerCase();
                    if (COUNTED_EXTS.has(ext)) {
                        result.file_counts[ext] = (result.file_counts[ext] || 0) + 1;
                        if (SOURCE_EXTS.has(ext)) {
                            const lines = countLines(full, st.size);
                            result.line_counts[ext] = (result.line_counts[ext] || 0) + lines;
                        }
                    }
                }
            }
        }
    }

    walk(dir, 0);
    return result;
}

interface NodeMeta {
    name?: string;
    version?: string;
    description?: string;
    type?: string;
    main?: string;
    module?: string;
    license?: string;
    package_manager: 'bun' | 'npm' | 'yarn' | 'pnpm' | 'unknown';
    dep_count: number;
    dev_dep_count: number;
    scripts: string[];
    framework_hints: string[];
    workspace_root: boolean;
}

function extractNodeMeta(dir: string): NodeMeta | undefined {
    const pkgPath = join(dir, 'package.json');
    let pkg: any;
    try {
        pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
    } catch {
        return undefined;
    }

    const deps = pkg.dependencies || {};
    const devDeps = pkg.devDependencies || {};
    const allDeps = { ...deps, ...devDeps };

    // Package manager detection from lockfile presence
    let pm: NodeMeta['package_manager'] = 'unknown';
    if (existsSync(join(dir, 'bun.lock')) || existsSync(join(dir, 'bun.lockb'))) pm = 'bun';
    else if (existsSync(join(dir, 'pnpm-lock.yaml'))) pm = 'pnpm';
    else if (existsSync(join(dir, 'yarn.lock'))) pm = 'yarn';
    else if (existsSync(join(dir, 'package-lock.json'))) pm = 'npm';

    // Framework heuristics — additive list, order matters for readability
    const hints: string[] = [];
    if (allDeps['react'] || allDeps['react-dom']) hints.push('react');
    if (allDeps['vue']) hints.push('vue');
    if (allDeps['svelte']) hints.push('svelte');
    if (allDeps['solid-js']) hints.push('solid');
    if (allDeps['electron']) hints.push('electron');
    if (allDeps['next']) hints.push('next');
    if (allDeps['nuxt']) hints.push('nuxt');
    if (allDeps['vite']) hints.push('vite');
    if (allDeps['esbuild']) hints.push('esbuild');
    if (allDeps['vscode'] || pkg.engines?.vscode) hints.push('vscode-extension');
    if (allDeps['@anthropic-ai/sdk'] || allDeps['@anthropic-ai/claude-agent-sdk']) hints.push('anthropic-sdk');
    if (allDeps['@agentclientprotocol/sdk']) hints.push('acp');
    if (allDeps['openai']) hints.push('openai');
    if (allDeps['@openai/agents']) hints.push('openai-agents');
    if (allDeps['langchain'] || allDeps['@langchain/core']) hints.push('langchain');
    if (allDeps['express'] || allDeps['fastify'] || allDeps['hono'] || allDeps['koa']) hints.push('http-server');
    if (allDeps['mcp']) hints.push('mcp');
    if (pkg.bin) hints.push('cli');

    return {
        name: pkg.name,
        version: pkg.version,
        description: pkg.description,
        type: pkg.type,
        main: pkg.main,
        module: pkg.module,
        license: pkg.license,
        package_manager: pm,
        dep_count: Object.keys(deps).length,
        dev_dep_count: Object.keys(devDeps).length,
        scripts: Object.keys(pkg.scripts || {}),
        framework_hints: hints,
        workspace_root: Array.isArray(pkg.workspaces) || typeof pkg.workspaces === 'object',
    };
}

interface RustMeta {
    name?: string;
    version?: string;
    edition?: string;
    rust_version?: string;
    license?: string;
    is_workspace: boolean;
    workspace_member_count: number;
    has_bin: boolean;
    has_lib: boolean;
    dep_count: number;
}

function extractRustMeta(dir: string): RustMeta | undefined {
    const cargoPath = join(dir, 'Cargo.toml');
    let raw: string;
    try {
        raw = readFileSync(cargoPath, 'utf-8');
    } catch {
        return undefined;
    }

    // Light-touch TOML parsing without a real TOML parser dep — line-grep for the
    // fields we care about. Sufficient for inventory; if downstream filtering needs
    // richer extraction, swap in `@iarna/toml` or similar then.
    const lineOf = (key: string): string | undefined => {
        const re = new RegExp(`^\\s*${key.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&')}\\s*=\\s*"([^"]*)"`, 'm');
        const m = raw.match(re);
        return m?.[1];
    };

    const isWorkspace = /^\[workspace\]/m.test(raw);
    const isPackage = /^\[package\]/m.test(raw);
    const hasBin = /^\[\[bin\]\]/m.test(raw);
    const hasLib = /^\[lib\]/m.test(raw);

    // Workspace member array — count lines between members = [ and ]
    let memberCount = 0;
    if (isWorkspace) {
        const m = raw.match(/members\s*=\s*\[([\s\S]*?)\]/m);
        if (m) {
            memberCount = (m[1].match(/"[^"]+"/g) || []).length;
        }
    }

    // Dep count — count lines in [dependencies] section
    let depCount = 0;
    const depMatch = raw.match(/^\[dependencies\]([\s\S]*?)(^\[|\Z)/m);
    if (depMatch) {
        depCount = (depMatch[1].match(/^\s*[a-zA-Z0-9_-]+\s*=/gm) || []).length;
    }

    return {
        name: isPackage ? lineOf('name') : undefined,
        version: lineOf('version'),
        edition: lineOf('edition'),
        rust_version: lineOf('rust-version'),
        license: lineOf('license'),
        is_workspace: isWorkspace,
        workspace_member_count: memberCount,
        has_bin: hasBin,
        has_lib: hasLib,
        dep_count: depCount,
    };
}

// ─── Project record ────────────────────────────────────────────────────────
type ModeHint = 'snipe' | 'sweep' | 'noise';

interface ProjectRecord {
    root_dir: string;
    rel_path: string;
    name: string;
    languages: string[];
    node?: NodeMeta;
    rust?: RustMeta;
    file_counts: ExtCounts;
    line_counts: ExtCounts;
    total_source_lines: number;
    config_files: string[];
    has_native_stack: boolean; // C/C++/CUDA/Vulkan-shaders present
    files_capped: boolean;
    repurposability_score: number;
    interesting_signals: string[];
    mode_hint: ModeHint;
}

const NATIVE_EXTS = new Set([
    '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh', '.hxx', '.inl',
    '.cu', '.cuh',
    '.glsl', '.vert', '.frag', '.comp', '.tesc', '.tese', '.geom',
    '.hlsl', '.wgsl', '.metal',
]);

function scoreRepurposability(rec: Omit<ProjectRecord, 'repurposability_score' | 'interesting_signals' | 'mode_hint'>): {
    score: number;
    signals: string[];
} {
    const signals: string[] = [];
    let score = 0;

    if (rec.node) {
        if (rec.node.framework_hints.length > 0) {
            score += rec.node.framework_hints.length;
            signals.push(`frameworks:${rec.node.framework_hints.join('+')}`);
        }
        if (rec.node.workspace_root) {
            score += 2;
            signals.push('workspace_root');
        }
        if (rec.node.scripts.length > 3) {
            score += 1;
            signals.push(`scripts:${rec.node.scripts.length}`);
        }
        if (rec.node.dep_count > 10) {
            score += 1;
            signals.push('deps:rich');
        }
    }

    if (rec.rust) {
        if (rec.rust.is_workspace) {
            score += 2;
            signals.push(`rust-workspace:${rec.rust.workspace_member_count}`);
        }
        if (rec.rust.has_bin) {
            score += 1;
            signals.push('rust-bin');
        }
        if (rec.rust.has_lib) {
            score += 1;
            signals.push('rust-lib');
        }
        if (rec.rust.edition === '2024') {
            score += 1;
            signals.push('edition-2024');
        }
    }

    // Native/GPU stack presence — a strong "snipe" signal
    if (rec.has_native_stack) {
        score += 3;
        const nativeExts = Object.keys(rec.file_counts).filter(e => NATIVE_EXTS.has(e));
        signals.push(`native:${nativeExts.slice(0, 6).join('+')}`);
    }

    // Source-line size (more meaningful than file count)
    if (rec.total_source_lines > 10000) {
        score += 3;
        signals.push(`lines:${rec.total_source_lines}`);
    } else if (rec.total_source_lines > 1000) {
        score += 2;
        signals.push(`lines:${rec.total_source_lines}`);
    } else if (rec.total_source_lines > 100) {
        score += 1;
    }

    // Config file richness — more configs = more substantive build
    if (rec.config_files.length >= 5) {
        score += 1;
        signals.push(`configs:${rec.config_files.length}`);
    }

    return { score, signals };
}

function classifyMode(rec: Omit<ProjectRecord, 'mode_hint'>): ModeHint {
    // SNIPE: high-score project with distinct character — drill in
    if (rec.repurposability_score >= 8) return 'snipe';
    if (rec.has_native_stack && rec.total_source_lines > 500) return 'snipe';
    if (rec.languages.length > 1) return 'snipe'; // polyglot is always snipe-worthy
    if (rec.node?.framework_hints.some(f => ['acp', 'anthropic-sdk', 'mcp', 'vscode-extension', 'electron'].includes(f))) {
        return 'snipe';
    }

    // NOISE: tiny, no source, no signals
    if (rec.total_source_lines === 0 && rec.config_files.length === 0) return 'noise';
    if (rec.repurposability_score <= 1 && rec.total_source_lines < 100) return 'noise';

    // SWEEP: mid-tier — batch-processable, look at the class not the instance
    return 'sweep';
}

// ─── Main ─────────────────────────────────────────────────────────────────
function main() {
    const args = parseArgs(process.argv.slice(2));

    if (!args.quiet) {
        console.error(`[spread-sweep] roots=${args.roots.join(',')} max-depth=${args.maxDepth}`);
    }

    const allMarkers: ProjectMarker[] = [];
    for (const root of args.roots) {
        const markers = walkForProjects(root, args.maxDepth);
        allMarkers.push(...markers);
    }

    if (!args.quiet) {
        console.error(`[spread-sweep] discovered ${allMarkers.length} project markers`);
    }

    const projects: ProjectRecord[] = [];
    for (const marker of allMarkers) {
        const node = marker.has_package_json ? extractNodeMeta(marker.path) : undefined;
        const rust = marker.has_cargo_toml ? extractRustMeta(marker.path) : undefined;
        const scan = scanProjectFiles(marker.path);

        const languages: string[] = [];
        if (node) languages.push('node');
        if (rust) languages.push('rust');
        // Detect native/GPU presence and add to languages
        const hasNative = Object.keys(scan.file_counts).some(e => NATIVE_EXTS.has(e));
        if (hasNative) {
            const hasC = ['.c', '.cc', '.cpp', '.cxx'].some(e => scan.file_counts[e]);
            const hasCUDA = ['.cu', '.cuh'].some(e => scan.file_counts[e]);
            const hasShader = ['.glsl', '.vert', '.frag', '.comp', '.hlsl', '.wgsl', '.metal'].some(e => scan.file_counts[e]);
            if (hasC) languages.push('c/cpp');
            if (hasCUDA) languages.push('cuda');
            if (hasShader) languages.push('shaders');
        }

        const name = node?.name || rust?.name || basename(marker.path);

        const totalSourceLines = Object.entries(scan.line_counts)
            .reduce((sum, [, n]) => sum + n, 0);

        const partial = {
            root_dir: marker.path,
            rel_path: marker.rel,
            name,
            languages,
            node,
            rust,
            file_counts: scan.file_counts,
            line_counts: scan.line_counts,
            total_source_lines: totalSourceLines,
            config_files: scan.config_files_found,
            has_native_stack: hasNative,
            files_capped: scan.files_capped,
        };
        const { score, signals } = scoreRepurposability(partial);
        const withScore = {
            ...partial,
            repurposability_score: score,
            interesting_signals: signals,
        };
        const mode = classifyMode(withScore);
        projects.push({
            ...withScore,
            mode_hint: mode,
        });
    }

    // Sort by repurposability descending (downstream filtering reads top-N).
    projects.sort((a, b) => b.repurposability_score - a.repurposability_score);

    const out = {
        generated_at: new Date().toISOString(),
        root_dirs: args.roots.map(r => resolve(r)),
        project_count: projects.length,
        projects,
    };

    // Ensure output dir exists.
    const outDir = dirname(args.output);
    if (outDir && !existsSync(outDir)) {
        mkdirSync(outDir, { recursive: true });
    }
    Bun.write(args.output, JSON.stringify(out, null, 2));

    if (!args.quiet) {
        console.error(`[spread-sweep] wrote ${projects.length} projects to ${args.output}`);
    }

    if (args.summary) {
        const totalNode = projects.filter(p => p.node).length;
        const totalRust = projects.filter(p => p.rust).length;
        const totalPoly = projects.filter(p => p.node && p.rust).length;
        const totalNative = projects.filter(p => p.has_native_stack).length;
        const pmCounts: Record<string, number> = {};
        for (const p of projects) {
            if (p.node) pmCounts[p.node.package_manager] = (pmCounts[p.node.package_manager] || 0) + 1;
        }
        const frameworkCounts: Record<string, number> = {};
        for (const p of projects) {
            for (const f of p.node?.framework_hints || []) {
                frameworkCounts[f] = (frameworkCounts[f] || 0) + 1;
            }
        }
        const modeCounts: Record<ModeHint, number> = { snipe: 0, sweep: 0, noise: 0 };
        for (const p of projects) modeCounts[p.mode_hint]++;

        // Total source-lines aggregated per language across the spread
        const totalLinesByExt: ExtCounts = {};
        for (const p of projects) {
            for (const [ext, n] of Object.entries(p.line_counts)) {
                totalLinesByExt[ext] = (totalLinesByExt[ext] || 0) + n;
            }
        }
        const topLangs = Object.entries(totalLinesByExt)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const snipes = projects.filter(p => p.mode_hint === 'snipe');
        const nativeProjects = projects.filter(p => p.has_native_stack).slice(0, 8);

        console.log('');
        console.log('=== spread-sweep V1.5 summary ===');
        console.log(`Projects: ${projects.length}  (node=${totalNode} rust=${totalRust} polyglot=${totalPoly} native-stack=${totalNative})`);
        console.log(`Modes: snipe=${modeCounts.snipe}  sweep=${modeCounts.sweep}  noise=${modeCounts.noise}`);
        console.log(`Package managers: ${Object.entries(pmCounts).map(([k, v]) => `${k}=${v}`).join(' ')}`);
        console.log(`Frameworks: ${Object.entries(frameworkCounts).sort((a, b) => b[1] - a[1]).slice(0, 12).map(([k, v]) => `${k}=${v}`).join(' ')}`);
        console.log('');
        console.log('Total source lines by language (top 10):');
        for (const [ext, n] of topLangs) {
            console.log(`  ${ext.padEnd(8)} ${n.toLocaleString()}`);
        }
        console.log('');
        console.log(`Snipe candidates (${snipes.length}, top 10 shown):`);
        for (const p of snipes.slice(0, 10)) {
            const tag = p.languages.join('+');
            console.log(`  [${p.repurposability_score}] ${p.name} (${tag}) ${p.rel_path}`);
            if (p.interesting_signals.length > 0) {
                console.log(`         ${p.interesting_signals.join(' · ')}`);
            }
        }
        if (nativeProjects.length > 0) {
            console.log('');
            console.log(`Native/GPU stack projects (${totalNative} total, top 8 shown):`);
            for (const p of nativeProjects) {
                const nativeFiles = Object.entries(p.file_counts)
                    .filter(([e]) => NATIVE_EXTS.has(e))
                    .map(([e, n]) => `${e}=${n}`)
                    .join(' ');
                const nativeLines = Object.entries(p.line_counts)
                    .filter(([e]) => NATIVE_EXTS.has(e))
                    .reduce((s, [, n]) => s + n, 0);
                console.log(`  ${p.name} (${p.rel_path})`);
                console.log(`    files: ${nativeFiles}`);
                console.log(`    native lines: ${nativeLines.toLocaleString()}`);
            }
        }
    }
}

main();
