#!/usr/bin/env bun
// @SID: TOOL_SPREAD_EXT_CENSUS_V1
// ============================================================
// spread-ext-census — workspace-wide file-extension distribution.
//
// Walks all configured root dirs (default: parent-of-cwd), skipping the
// same SKIP_DIRS + VENDORED_PATH_PATTERNS as spread-sweep. Emits the full
// distribution of file extensions across the entire poly-repo surface:
//
//   - total file count per extension
//   - distinct project count per extension (project = nearest ancestor
//     containing package.json or Cargo.toml; fallback = first-level dir
//     under the scan root)
//   - sample paths per extension (top-3)
//
// Companion to spread-sweep: spread-sweep uses a hand-curated COUNTED_EXTS
// set, which silently omits anything not in the allowlist. This census
// reveals what's actually present, so the curated set can be expanded
// against ground truth rather than guesswork.
//
// Usage:
//   bun run scripts/spread-ext-census.ts                          # default roots
//   bun run scripts/spread-ext-census.ts --roots <a>,<b>
//   bun run scripts/spread-ext-census.ts --output manifest/spread_ext_census.json
//   bun run scripts/spread-ext-census.ts --min-count 5            # only show exts with >=5 files
//   bun run scripts/spread-ext-census.ts --no-summary             # skip stdout summary
// ============================================================

import { readdirSync, statSync, existsSync, mkdirSync } from 'node:fs';
import { join, resolve, relative, dirname } from 'node:path';

// ─── Shared skip set (kept in sync with spread-sweep) ─────────────────────
const SKIP_DIRS = new Set([
    'node_modules', 'target', 'dist', 'build', 'out', '.git', '.next', '.nuxt',
    '.cache', '.turbo', '.vite', '.parcel-cache', '.svelte-kit', '.angular',
    '__pycache__', '.venv', 'venv', 'env', '.tox', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'vendor', 'Pods', '.gradle', '.idea', '.vscode-test',
    'coverage', '.nyc_output', '.jest-cache',
    'tmp', '.tmp', 'temp', '.temp',
]);

const VENDORED_PATH_PATTERNS = [
    'vcpkg/buildtrees', 'vcpkg/packages', 'vcpkg/installed',
    '.cargo/registry', '.cargo/git/checkouts',
    'rv/library/', 'rv-test-rubies', '/buildtrees/',
    '/.rustup/', 'AppData/Local/Programs/', 'AppData/Roaming/',
    '/site-packages/', '/.gem/', '/Library/Caches/',
];

function isVendoredPath(absPath: string): boolean {
    const norm = absPath.replace(/\\/g, '/');
    return VENDORED_PATH_PATTERNS.some(p => norm.includes(p));
}

// ─── Args ─────────────────────────────────────────────────────────────────
interface Args {
    roots: string[];
    output: string;
    minCount: number;
    noSummary: boolean;
    maxFilesPerRoot: number;
}

function parseArgs(argv: string[]): Args {
    const args: Args = {
        roots: [],
        output: 'manifest/spread_ext_census.json',
        minCount: 1,
        noSummary: false,
        maxFilesPerRoot: 500_000,
    };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--roots' && argv[i + 1]) {
            args.roots = argv[++i].split(',').map(s => s.trim()).filter(Boolean);
        } else if (a === '--output' && argv[i + 1]) {
            args.output = argv[++i];
        } else if (a === '--min-count' && argv[i + 1]) {
            args.minCount = parseInt(argv[++i], 10);
        } else if (a === '--no-summary') {
            args.noSummary = true;
        } else if (a === '--max-files-per-root' && argv[i + 1]) {
            args.maxFilesPerRoot = parseInt(argv[++i], 10);
        } else if (a === '--help' || a === '-h') {
            console.log(
                'Usage: bun run scripts/spread-ext-census.ts [--roots a,b,c] [--output path] [--min-count N] [--no-summary]',
            );
            process.exit(0);
        }
    }
    if (args.roots.length === 0) {
        args.roots = [resolve(process.cwd(), '..')];
    }
    return args;
}

// ─── Project owner (nearest ancestor with project marker) ─────────────────
function findProjectOwner(filePath: string, scanRoot: string): string {
    // Walk up from the file's dir until we hit one with package.json / Cargo.toml,
    // or until we reach the scan root. Return that owner dir's path (relative to
    // scan root). If nothing found, use first-level dir under scan root.
    let dir = dirname(filePath);
    const scanRootNorm = resolve(scanRoot);
    while (dir.length >= scanRootNorm.length) {
        try {
            const entries = readdirSync(dir);
            if (entries.includes('package.json') || entries.includes('Cargo.toml')) {
                return relative(scanRootNorm, dir) || '.';
            }
        } catch {
            // ignore
        }
        const parent = dirname(dir);
        if (parent === dir) break;
        dir = parent;
        if (!dir.startsWith(scanRootNorm)) break;
    }
    // Fallback: first-level dir under scan root
    const rel = relative(scanRootNorm, filePath);
    const firstSep = rel.indexOf(/[\\/]/.exec(rel)?.[0] ?? '');
    return firstSep > 0 ? rel.substring(0, firstSep) : '.';
}

// ─── Walk ─────────────────────────────────────────────────────────────────
interface ExtRecord {
    ext: string;
    file_count: number;
    project_count: number;
    sample_paths: string[];
    sample_projects: string[];
}

function censusRoot(root: string, cap: number): {
    ext_to_files: Map<string, string[]>;
    ext_to_projects: Map<string, Set<string>>;
    files_visited: number;
    files_capped: boolean;
} {
    const ext_to_files = new Map<string, string[]>();
    const ext_to_projects = new Map<string, Set<string>>();
    let visited = 0;
    let capped = false;
    const rootResolved = resolve(root);

    function walk(dir: string, depth: number) {
        if (visited >= cap) { capped = true; return; }
        if (depth > 10) return;
        if (isVendoredPath(dir)) return;
        let entries: string[];
        try { entries = readdirSync(dir); } catch { return; }
        for (const name of entries) {
            if (visited >= cap) { capped = true; return; }
            if (name.startsWith('.') && name !== '.github' && name !== '.cargo' && name !== '.vscode') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(dir, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) {
                walk(full, depth + 1);
            } else if (st.isFile()) {
                visited++;
                // Determine extension; files with NO extension get a sentinel '<noext>'
                let ext: string;
                const dotIdx = name.lastIndexOf('.');
                if (dotIdx <= 0) {
                    ext = '<noext>';
                } else {
                    ext = name.substring(dotIdx).toLowerCase();
                    // Sanity cap: drop ridiculous "extensions" (e.g. file.ABCDEFGHIJ where
                    // the dot was part of a SHA or version). Keep alphanumeric + a few signs.
                    if (ext.length > 12 || !/^\.[a-z0-9._+-]+$/.test(ext)) {
                        ext = '<weird-ext>';
                    }
                }
                // Record file
                if (!ext_to_files.has(ext)) ext_to_files.set(ext, []);
                const filesList = ext_to_files.get(ext)!;
                if (filesList.length < 3) filesList.push(relative(rootResolved, full));
                // Record project owner — only compute when needed (cheaper)
                if (!ext_to_projects.has(ext)) ext_to_projects.set(ext, new Set());
                const projSet = ext_to_projects.get(ext)!;
                // Cheap optimization: only resolve project owner up to N times per ext
                if (projSet.size < 50) {
                    const owner = findProjectOwner(full, rootResolved);
                    projSet.add(owner);
                }
            }
        }
    }

    walk(rootResolved, 0);
    return { ext_to_files, ext_to_projects, files_visited: visited, files_capped: capped };
}

// ─── Aggregation ──────────────────────────────────────────────────────────
function buildExtRecords(
    perRoot: Array<ReturnType<typeof censusRoot>>,
): { records: ExtRecord[]; total_files: number } {
    // Need to also track the FULL file-count per ext, not just sample count.
    // Walking again is wasteful, so we collect file counts during the walk via
    // a parallel structure. Re-do: extend censusRoot to return per-ext file counts.
    // For now, file_count = sum of sample-list overflow signals; rebuild from
    // ext_to_files length is wrong (capped at 3). Fix: walk results separately.
    throw new Error('see censusRootWithCounts below');
}

// Replacement implementation with a true count
function censusRootWithCounts(root: string, cap: number): {
    ext_to_count: Map<string, number>;
    ext_to_sample_files: Map<string, string[]>;
    ext_to_projects: Map<string, Set<string>>;
    files_visited: number;
    files_capped: boolean;
} {
    const ext_to_count = new Map<string, number>();
    const ext_to_sample_files = new Map<string, string[]>();
    const ext_to_projects = new Map<string, Set<string>>();
    let visited = 0;
    let capped = false;
    const rootResolved = resolve(root);

    function walk(dir: string, depth: number) {
        if (visited >= cap) { capped = true; return; }
        if (depth > 10) return;
        if (isVendoredPath(dir)) return;
        let entries: string[];
        try { entries = readdirSync(dir); } catch { return; }
        for (const name of entries) {
            if (visited >= cap) { capped = true; return; }
            if (name.startsWith('.') && name !== '.github' && name !== '.cargo' && name !== '.vscode') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(dir, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) {
                walk(full, depth + 1);
            } else if (st.isFile()) {
                visited++;
                let ext: string;
                const dotIdx = name.lastIndexOf('.');
                if (dotIdx <= 0) {
                    ext = '<noext>';
                } else {
                    ext = name.substring(dotIdx).toLowerCase();
                    if (ext.length > 12 || !/^\.[a-z0-9._+-]+$/.test(ext)) {
                        ext = '<weird-ext>';
                    }
                }
                ext_to_count.set(ext, (ext_to_count.get(ext) || 0) + 1);
                const samples = ext_to_sample_files.get(ext) ?? [];
                if (samples.length < 3) samples.push(relative(rootResolved, full));
                ext_to_sample_files.set(ext, samples);
                const projs = ext_to_projects.get(ext) ?? new Set<string>();
                // Bump cap so project counts are honest beyond 50 — small memory
                // cost vs. accurate project-count column the conductor needs.
                if (projs.size < 1000) {
                    projs.add(findProjectOwner(full, rootResolved));
                    ext_to_projects.set(ext, projs);
                }
            }
        }
    }

    walk(rootResolved, 0);
    return { ext_to_count, ext_to_sample_files, ext_to_projects, files_visited: visited, files_capped: capped };
}

// ─── Main ─────────────────────────────────────────────────────────────────
function main() {
    const args = parseArgs(process.argv.slice(2));

    console.error(`[ext-census] roots=${args.roots.join(',')}`);

    const merged = {
        ext_to_count: new Map<string, number>(),
        ext_to_sample_files: new Map<string, string[]>(),
        ext_to_projects: new Map<string, Set<string>>(),
        total_visited: 0,
        any_capped: false,
    };

    for (const root of args.roots) {
        const result = censusRootWithCounts(root, args.maxFilesPerRoot);
        merged.total_visited += result.files_visited;
        if (result.files_capped) merged.any_capped = true;
        for (const [ext, n] of result.ext_to_count) {
            merged.ext_to_count.set(ext, (merged.ext_to_count.get(ext) || 0) + n);
        }
        for (const [ext, samples] of result.ext_to_sample_files) {
            const existing = merged.ext_to_sample_files.get(ext) ?? [];
            for (const s of samples) if (existing.length < 5) existing.push(s);
            merged.ext_to_sample_files.set(ext, existing);
        }
        for (const [ext, projs] of result.ext_to_projects) {
            const existing = merged.ext_to_projects.get(ext) ?? new Set<string>();
            for (const p of projs) existing.add(p);
            merged.ext_to_projects.set(ext, existing);
        }
        console.error(`[ext-census]   ${root}: ${result.files_visited.toLocaleString()} files visited${result.files_capped ? ' (CAPPED)' : ''}`);
    }

    const records: ExtRecord[] = [];
    for (const [ext, count] of merged.ext_to_count) {
        if (count < args.minCount) continue;
        records.push({
            ext,
            file_count: count,
            project_count: merged.ext_to_projects.get(ext)?.size ?? 0,
            sample_paths: merged.ext_to_sample_files.get(ext) ?? [],
            sample_projects: Array.from(merged.ext_to_projects.get(ext) ?? []).slice(0, 5),
        });
    }
    records.sort((a, b) => b.file_count - a.file_count);

    const output = {
        generated_at: new Date().toISOString(),
        root_dirs: args.roots.map(r => resolve(r)),
        total_files_visited: merged.total_visited,
        any_capped: merged.any_capped,
        unique_extensions: records.length,
        min_count_threshold: args.minCount,
        extensions: records,
    };

    const outDir = dirname(args.output);
    if (outDir && !existsSync(outDir)) mkdirSync(outDir, { recursive: true });
    Bun.write(args.output, JSON.stringify(output, null, 2));

    console.error(`[ext-census] wrote ${records.length} unique extensions to ${args.output}`);

    if (!args.noSummary) {
        console.log('');
        console.log('=== spread-ext-census ===');
        console.log(`Files visited: ${merged.total_visited.toLocaleString()}  unique extensions: ${records.length}${merged.any_capped ? '  [CAPPED]' : ''}`);
        console.log('');
        console.log('All extensions (file_count / project_count, sorted by file_count):');
        for (const r of records) {
            const projPart = r.project_count > 0 ? `${r.project_count.toString().padStart(4)} proj` : '       ';
            console.log(`  ${r.ext.padEnd(14)} ${r.file_count.toString().padStart(7)} files  ${projPart}`);
        }
    }
}

main();
