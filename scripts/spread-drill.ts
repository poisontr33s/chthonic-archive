#!/usr/bin/env bun
// @SID: TOOL_SPREAD_DRILL_V1
// ============================================================
// spread-drill — per-project deep extraction over a snipe target.
//
// Reads manifest/spread_index.json (emitted by scripts/spread-sweep.ts),
// resolves a named project (by name match or rel_path prefix), walks its
// source files, and extracts structured per-file data:
//
//   - TS/JS family: imports + exports via Bun.Transpiler.scan
//   - Rust: top-level pub items (fn / struct / enum / trait / mod / use)
//   - Light extraction for native (.c/.cpp/.cu/.glsl): symbol counts only
//
// Outputs to manifest/spread_drill_<safe-name>.json + summary on stdout.
//
// Usage:
//   bun run scripts/spread-drill.ts <project-name-or-relpath>
//   bun run scripts/spread-drill.ts --name chthonic-archive --output custom/path.json
//   bun run scripts/spread-drill.ts chthonic-archive --max-files 200
//   bun run scripts/spread-drill.ts --list                  # list all snipe candidates
// ============================================================

import { existsSync, readdirSync, readFileSync, statSync, mkdirSync } from 'node:fs';
import { join, relative, dirname, basename } from 'node:path';

const REPO_ROOT = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]):/, '$1:');

// ─── Args ─────────────────────────────────────────────────────────────────
interface Args {
    target: string | null;
    output: string | null;
    maxFiles: number;
    list: boolean;
    indexPath: string;
}

function parseArgs(argv: string[]): Args {
    const args: Args = {
        target: null,
        output: null,
        maxFiles: 500,
        list: false,
        indexPath: 'manifest/spread_index.json',
    };
    let i = 0;
    while (i < argv.length) {
        const a = argv[i];
        if (a === '--name' && argv[i + 1]) { args.target = argv[++i]; }
        else if (a === '--output' && argv[i + 1]) { args.output = argv[++i]; }
        else if (a === '--max-files' && argv[i + 1]) { args.maxFiles = parseInt(argv[++i], 10); }
        else if (a === '--list') { args.list = true; }
        else if (a === '--index' && argv[i + 1]) { args.indexPath = argv[++i]; }
        else if (a === '--help' || a === '-h') {
            console.log('Usage: bun run scripts/spread-drill.ts <project-name> [--max-files N] [--output path]');
            console.log('       bun run scripts/spread-drill.ts --list      # show snipe candidates');
            process.exit(0);
        }
        else if (!a.startsWith('--') && !args.target) { args.target = a; }
        i++;
    }
    return args;
}

// ─── Spread index types ───────────────────────────────────────────────────
interface SpreadProject {
    root_dir: string;
    rel_path: string;
    name: string;
    languages: string[];
    mode_hint: 'snipe' | 'sweep' | 'noise';
    has_native_stack: boolean;
    repurposability_score: number;
    total_source_lines: number;
    file_counts: Record<string, number>;
    line_counts: Record<string, number>;
    interesting_signals: string[];
}

interface SpreadIndex {
    generated_at: string;
    root_dirs: string[];
    project_count: number;
    projects: SpreadProject[];
}

// ─── Extraction ────────────────────────────────────────────────────────────
const TS_EXTS = new Set(['.ts', '.tsx', '.mts', '.cts', '.js', '.jsx', '.mjs', '.cjs']);
const RUST_EXTS = new Set(['.rs']);
const NATIVE_EXTS = new Set([
    '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh', '.hxx',
    '.cu', '.cuh',
    '.glsl', '.vert', '.frag', '.comp', '.tesc', '.tese', '.geom',
    '.hlsl', '.wgsl', '.metal',
]);

const SKIP_DIRS = new Set([
    'node_modules', 'target', 'dist', 'build', 'out', '.git', '.next', '.nuxt',
    '.cache', '.turbo', '.vite', '.parcel-cache', '__pycache__', '.venv', 'venv',
    'vendor', 'coverage', '.gradle', '.idea', 'tmp', '.tmp',
]);

interface FileExtract {
    path: string;
    ext: string;
    kind: 'ts' | 'rust' | 'native' | 'other';
    lines: number;
    bytes: number;
    // TS-family extraction
    imports?: string[];
    exports?: string[];
    // Rust extraction
    pub_items?: { kind: string; name: string }[];
    // Native: count of function-like symbols (heuristic)
    symbol_hints?: number;
}

const MAX_FILE_BYTES = 1024 * 1024; // 1 MiB cap per file

function extractTS(content: string): { imports: string[]; exports: string[] } {
    try {
        const transpiler = new Bun.Transpiler({ loader: 'tsx' });
        const scan = transpiler.scan(content);
        // dedup
        const imports = Array.from(new Set(scan.imports.map((i: any) => i.path)));
        const exports = Array.from(new Set(scan.exports));
        return { imports, exports };
    } catch {
        return { imports: [], exports: [] };
    }
}

const RUST_PUB_RE = /^\s*pub(?:\s*\([^)]*\))?\s+(fn|struct|enum|trait|mod|const|static|type|use)\s+([A-Za-z_][A-Za-z0-9_]*)/gm;
function extractRust(content: string): { pub_items: { kind: string; name: string }[] } {
    const items: { kind: string; name: string }[] = [];
    let m: RegExpExecArray | null;
    while ((m = RUST_PUB_RE.exec(content)) !== null) {
        items.push({ kind: m[1], name: m[2] });
    }
    return { pub_items: items };
}

// Light native symbol heuristic: count lines that look like function definitions
// (return-type name(args) { pattern), without trying to parse C/C++ properly.
const NATIVE_SYM_RE = /^[A-Za-z_][A-Za-z0-9_*\s&<>:]*\s+[A-Za-z_][A-Za-z0-9_]*\s*\([^;]*\)\s*(?:const\s*)?\{/gm;
function extractNative(content: string): { symbol_hints: number } {
    let count = 0;
    NATIVE_SYM_RE.lastIndex = 0;
    while (NATIVE_SYM_RE.exec(content) !== null) count++;
    return { symbol_hints: count };
}

function walkProjectFiles(rootDir: string, maxFiles: number): FileExtract[] {
    const out: FileExtract[] = [];
    let visited = 0;

    function walk(dir: string, depth: number) {
        if (out.length >= maxFiles || depth > 5) return;
        let entries: string[];
        try { entries = readdirSync(dir); } catch { return; }
        for (const name of entries) {
            if (out.length >= maxFiles) return;
            if (name.startsWith('.') && name !== '.cargo') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(dir, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) { walk(full, depth + 1); continue; }
            if (!st.isFile()) continue;
            visited++;
            const dotIdx = name.lastIndexOf('.');
            if (dotIdx < 0) continue;
            const ext = name.substring(dotIdx).toLowerCase();
            let kind: FileExtract['kind'];
            if (TS_EXTS.has(ext)) kind = 'ts';
            else if (RUST_EXTS.has(ext)) kind = 'rust';
            else if (NATIVE_EXTS.has(ext)) kind = 'native';
            else continue;

            if (st.size > MAX_FILE_BYTES) {
                // record presence but skip the extraction
                out.push({
                    path: relative(rootDir, full),
                    ext, kind,
                    lines: Math.round(st.size / 50),
                    bytes: st.size,
                });
                continue;
            }

            let content: string;
            try { content = readFileSync(full, 'utf8'); } catch { continue; }
            const lines = content.split(/\r?\n/).length;
            const rec: FileExtract = {
                path: relative(rootDir, full),
                ext, kind,
                lines,
                bytes: st.size,
            };
            if (kind === 'ts') Object.assign(rec, extractTS(content));
            else if (kind === 'rust') Object.assign(rec, extractRust(content));
            else if (kind === 'native') Object.assign(rec, extractNative(content));
            out.push(rec);
        }
    }
    walk(rootDir, 0);
    return out;
}

// ─── Project resolution ───────────────────────────────────────────────────
function resolveProject(idx: SpreadIndex, target: string): SpreadProject | null {
    const projects = idx.projects ?? [];
    // 1. Exact name match (snipe-preferred)
    const exactNameSnipes = projects.filter(p => p.name === target && p.mode_hint === 'snipe');
    if (exactNameSnipes.length > 0) {
        return exactNameSnipes.sort((a, b) => b.repurposability_score - a.repurposability_score)[0];
    }
    // 2. Exact name match (any mode)
    const exactName = projects.filter(p => p.name === target);
    if (exactName.length > 0) {
        return exactName.sort((a, b) => b.repurposability_score - a.repurposability_score)[0];
    }
    // 3. rel_path exact match
    const exactPath = projects.find(p => p.rel_path === target);
    if (exactPath) return exactPath;
    // 4. rel_path suffix match (e.g. user passes "chthonic-archive" matches "chthonic-archive\extensions\chthonic-archive")
    const suffixMatches = projects.filter(p => p.rel_path.endsWith(target));
    if (suffixMatches.length > 0) {
        return suffixMatches.sort((a, b) => b.repurposability_score - a.repurposability_score)[0];
    }
    // 5. Substring match
    const subMatches = projects.filter(p => p.name.includes(target) || p.rel_path.includes(target));
    if (subMatches.length === 1) return subMatches[0];
    if (subMatches.length > 1) {
        return subMatches.sort((a, b) => b.repurposability_score - a.repurposability_score)[0];
    }
    return null;
}

function safeName(s: string): string {
    return s.replace(/[^A-Za-z0-9._-]/g, '_').replace(/^_+|_+$/g, '');
}

// ─── Main ─────────────────────────────────────────────────────────────────
async function main() {
    const args = parseArgs(process.argv.slice(2));

    if (!existsSync(args.indexPath)) {
        console.error(`[spread-drill] missing ${args.indexPath} — run: bun run scripts/spread-sweep.ts --summary`);
        process.exit(1);
    }

    const idx = JSON.parse(readFileSync(args.indexPath, 'utf8')) as SpreadIndex;

    if (args.list) {
        const snipes = (idx.projects ?? []).filter(p => p.mode_hint === 'snipe');
        console.log(`Snipe candidates (${snipes.length}):`);
        for (const p of snipes) {
            console.log(`  [${p.repurposability_score}] ${p.name} (${p.languages.join('+')}) — ${p.rel_path}`);
        }
        process.exit(0);
    }

    if (!args.target) {
        console.error('[spread-drill] target required: pass a project name, rel_path, or --list to see options');
        process.exit(1);
    }

    const project = resolveProject(idx, args.target);
    if (!project) {
        console.error(`[spread-drill] no project resolved for "${args.target}"`);
        console.error(`[spread-drill] try --list to see snipe candidates`);
        process.exit(1);
    }

    console.error(`[spread-drill] target: ${project.name} (${project.languages.join('+')}) at ${project.root_dir}`);
    console.error(`[spread-drill] walking files (max ${args.maxFiles})...`);

    const extracts = walkProjectFiles(project.root_dir, args.maxFiles);

    // Aggregations
    const tsFiles = extracts.filter(e => e.kind === 'ts');
    const rustFiles = extracts.filter(e => e.kind === 'rust');
    const nativeFiles = extracts.filter(e => e.kind === 'native');

    // Cross-file aggregates: most-imported (popularity), most-exporting (richness)
    const importCounts = new Map<string, number>();
    for (const f of tsFiles) {
        for (const imp of f.imports ?? []) importCounts.set(imp, (importCounts.get(imp) || 0) + 1);
    }
    const topImports = [...importCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 20);

    const allRustPubKinds = new Map<string, number>();
    for (const f of rustFiles) {
        for (const it of f.pub_items ?? []) {
            allRustPubKinds.set(it.kind, (allRustPubKinds.get(it.kind) || 0) + 1);
        }
    }

    const richestTs = tsFiles
        .filter(f => (f.exports?.length ?? 0) > 0)
        .sort((a, b) => (b.exports?.length ?? 0) - (a.exports?.length ?? 0))
        .slice(0, 10);

    const richestRust = rustFiles
        .filter(f => (f.pub_items?.length ?? 0) > 0)
        .sort((a, b) => (b.pub_items?.length ?? 0) - (a.pub_items?.length ?? 0))
        .slice(0, 10);

    const output = {
        generated_at: new Date().toISOString(),
        spread_index_generated_at: idx.generated_at,
        project: {
            name: project.name,
            rel_path: project.rel_path,
            root_dir: project.root_dir,
            languages: project.languages,
            mode_hint: project.mode_hint,
            repurposability_score: project.repurposability_score,
        },
        file_count: extracts.length,
        ts_file_count: tsFiles.length,
        rust_file_count: rustFiles.length,
        native_file_count: nativeFiles.length,
        rust_pub_kinds: Object.fromEntries(allRustPubKinds),
        top_imports: topImports.map(([path, count]) => ({ path, count })),
        files: extracts,
    };

    const outputPath = args.output || `manifest/spread_drill_${safeName(project.name)}.json`;
    const outDir = dirname(outputPath);
    if (outDir && !existsSync(outDir)) mkdirSync(outDir, { recursive: true });
    await Bun.write(outputPath, JSON.stringify(output, null, 2));

    console.log('');
    console.log(`=== spread-drill: ${project.name} ===`);
    console.log(`Path: ${project.rel_path}`);
    console.log(`Languages: ${project.languages.join('+')} | Mode: ${project.mode_hint} | Score: ${project.repurposability_score}`);
    console.log(`Files extracted: ${extracts.length} (ts=${tsFiles.length} rust=${rustFiles.length} native=${nativeFiles.length})`);

    if (allRustPubKinds.size > 0) {
        console.log('');
        console.log('Rust pub items by kind:');
        for (const [kind, n] of [...allRustPubKinds.entries()].sort((a, b) => b[1] - a[1])) {
            console.log(`  pub ${kind.padEnd(8)} ${n}`);
        }
    }

    if (richestRust.length > 0) {
        console.log('');
        console.log(`Top ${richestRust.length} Rust files by pub-item count:`);
        for (const f of richestRust) {
            console.log(`  ${(f.pub_items?.length ?? 0).toString().padStart(4)}  ${f.path}`);
        }
    }

    if (richestTs.length > 0) {
        console.log('');
        console.log(`Top ${richestTs.length} TS/JS files by export count:`);
        for (const f of richestTs) {
            console.log(`  ${(f.exports?.length ?? 0).toString().padStart(4)}  ${f.path}`);
        }
    }

    if (topImports.length > 0) {
        console.log('');
        console.log(`Top ${Math.min(topImports.length, 20)} imports (popularity within project):`);
        for (const [path, count] of topImports.slice(0, 20)) {
            console.log(`  ${count.toString().padStart(4)}  ${path}`);
        }
    }

    console.log('');
    console.log(`Wrote ${outputPath}`);
}

main();
