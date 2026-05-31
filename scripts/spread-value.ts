#!/usr/bin/env bun
// @SID: TOOL_SPREAD_VALUE_V1
// ============================================================
// spread-value — content-value layer for the spread.
//
// Reads manifest/spread_index.json (from scripts/spread-sweep.ts),
// hashes the per-file content of the chosen project subset, builds
// a workspace-wide hash→[paths] duplicate map, magic-byte-detects
// unknown extensions, and surfaces the largest duplicate clusters
// (= the highest-value salvage / cleanup targets).
//
// Cheap-then-deep + incremental cache:
//   - .spread/file_index.ndjson is the durable cache: one row per
//     {path, size, mtime_ms, sha256, bucket, magic?}.
//   - On scan, files where (path, size, mtime_ms) matches an existing
//     cache row reuse the cached sha256/magic without re-reading bytes.
//   - First scan is slow (full hashing); subsequent scans are seconds.
//
// Usage:
//   bun run scripts/spread-value.ts --target chthonic-archive
//   bun run scripts/spread-value.ts --all                          # every project in the index
//   bun run scripts/spread-value.ts --snipes                       # all snipe-mode projects
//   bun run scripts/spread-value.ts --rebuild-cache --snipes
//   bun run scripts/spread-value.ts --min-dup-bytes 4096           # filter dup clusters by size
// ============================================================

import { createHash } from 'node:crypto';
import {
    existsSync, readFileSync, readdirSync, statSync, mkdirSync, openSync, readSync, closeSync,
    appendFileSync, writeFileSync,
} from 'node:fs';
import { dirname, join, relative, resolve, basename } from 'node:path';

const REPO_ROOT = process.cwd(); // assume invoked from repo root
const CACHE_DIR = resolve(REPO_ROOT, '.spread');
const CACHE_FILE = resolve(CACHE_DIR, 'file_index.ndjson');

// ─── Args ─────────────────────────────────────────────────────────────────
interface Args {
    target: string | null;
    all: boolean;
    snipes: boolean;
    rebuildCache: boolean;
    minDupBytes: number;
    output: string;
    indexPath: string;
    maxFilesPerProject: number;
}

function parseArgs(argv: string[]): Args {
    const args: Args = {
        target: null,
        all: false,
        snipes: false,
        rebuildCache: false,
        minDupBytes: 1024,
        output: 'manifest/spread_value.json',
        indexPath: 'manifest/spread_index.json',
        maxFilesPerProject: 50_000,
    };
    for (let i = 0; i < argv.length; i++) {
        const a = argv[i];
        if (a === '--target' && argv[i + 1]) args.target = argv[++i];
        else if (a === '--all') args.all = true;
        else if (a === '--snipes') args.snipes = true;
        else if (a === '--rebuild-cache') args.rebuildCache = true;
        else if (a === '--min-dup-bytes' && argv[i + 1]) args.minDupBytes = parseInt(argv[++i], 10);
        else if (a === '--output' && argv[i + 1]) args.output = argv[++i];
        else if (a === '--max-files-per-project' && argv[i + 1]) args.maxFilesPerProject = parseInt(argv[++i], 10);
        else if (a === '--help' || a === '-h') {
            console.log('Usage: bun run scripts/spread-value.ts [--target <name> | --snipes | --all] [--rebuild-cache] [--min-dup-bytes N]');
            process.exit(0);
        } else if (!a.startsWith('--') && !args.target) {
            args.target = a;
        }
    }
    if (!args.target && !args.all && !args.snipes) {
        args.snipes = true; // default: scan snipe-mode projects
    }
    return args;
}

// ─── Cache I/O ────────────────────────────────────────────────────────────
interface CacheRow {
    path: string;
    size: number;
    mtime_ms: number;
    sha256: string;
    bucket: string;
    magic?: string;
}

function loadCache(): Map<string, CacheRow> {
    const map = new Map<string, CacheRow>();
    if (!existsSync(CACHE_FILE)) return map;
    try {
        const raw = readFileSync(CACHE_FILE, 'utf8');
        for (const line of raw.split(/\r?\n/)) {
            if (!line.trim()) continue;
            try {
                const row = JSON.parse(line) as CacheRow;
                // Last write wins for the same path (cache append semantics)
                map.set(row.path, row);
            } catch {
                // skip malformed line
            }
        }
    } catch {
        // unreadable cache — start fresh
    }
    return map;
}

function writeCache(rows: Iterable<CacheRow>): void {
    if (!existsSync(CACHE_DIR)) mkdirSync(CACHE_DIR, { recursive: true });
    const lines: string[] = [];
    for (const r of rows) lines.push(JSON.stringify(r));
    writeFileSync(CACHE_FILE, lines.join('\n') + '\n', 'utf8');
}

// ─── Magic-byte detection ─────────────────────────────────────────────────
// Hand-rolled table for common formats. Lookup uses first 16 bytes of a file.
interface MagicRule {
    name: string;
    offset: number;
    bytes: number[]; // -1 = wildcard
}

const MAGIC_RULES: MagicRule[] = [
    // Executables / libraries
    { name: 'PE/COFF (Windows .exe/.dll)', offset: 0, bytes: [0x4d, 0x5a] }, // MZ
    { name: 'ELF (Linux/BSD binary)', offset: 0, bytes: [0x7f, 0x45, 0x4c, 0x46] },
    { name: 'Mach-O 64-bit', offset: 0, bytes: [0xcf, 0xfa, 0xed, 0xfe] },
    { name: 'Mach-O 32-bit', offset: 0, bytes: [0xce, 0xfa, 0xed, 0xfe] },
    { name: '.NET assembly', offset: 0, bytes: [0x4d, 0x5a] }, // also MZ; PE header tells more
    // Archives
    { name: 'ZIP archive (.zip/.jar/.docx/etc.)', offset: 0, bytes: [0x50, 0x4b, 0x03, 0x04] },
    { name: 'ZIP empty', offset: 0, bytes: [0x50, 0x4b, 0x05, 0x06] },
    { name: 'gzip', offset: 0, bytes: [0x1f, 0x8b] },
    { name: 'bzip2', offset: 0, bytes: [0x42, 0x5a, 0x68] },
    { name: 'xz', offset: 0, bytes: [0xfd, 0x37, 0x7a, 0x58, 0x5a, 0x00] },
    { name: '7z', offset: 0, bytes: [0x37, 0x7a, 0xbc, 0xaf, 0x27, 0x1c] },
    { name: 'tar (POSIX)', offset: 257, bytes: [0x75, 0x73, 0x74, 0x61, 0x72] }, // "ustar"
    // Images
    { name: 'PNG', offset: 0, bytes: [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a] },
    { name: 'JPEG', offset: 0, bytes: [0xff, 0xd8, 0xff] },
    { name: 'GIF87a', offset: 0, bytes: [0x47, 0x49, 0x46, 0x38, 0x37, 0x61] },
    { name: 'GIF89a', offset: 0, bytes: [0x47, 0x49, 0x46, 0x38, 0x39, 0x61] },
    { name: 'WebP (RIFF)', offset: 0, bytes: [0x52, 0x49, 0x46, 0x46] }, // RIFF; .webp/.wav both
    { name: 'BMP', offset: 0, bytes: [0x42, 0x4d] },
    // Audio/Video
    { name: 'MP3 (ID3v2)', offset: 0, bytes: [0x49, 0x44, 0x33] },
    { name: 'FLAC', offset: 0, bytes: [0x66, 0x4c, 0x61, 0x43] },
    { name: 'OGG', offset: 0, bytes: [0x4f, 0x67, 0x67, 0x53] },
    { name: 'ISO container (MP4/M4A)', offset: 4, bytes: [0x66, 0x74, 0x79, 0x70] },
    // Documents
    { name: 'PDF', offset: 0, bytes: [0x25, 0x50, 0x44, 0x46] },
    { name: 'SQLite database', offset: 0, bytes: [0x53, 0x51, 0x4c, 0x69, 0x74, 0x65, 0x20, 0x66, 0x6f, 0x72, 0x6d, 0x61, 0x74, 0x20, 0x33, 0x00] },
    // ML / GPU artifacts
    { name: 'ONNX (protobuf)', offset: 0, bytes: [0x08] }, // weak; ONNX starts with varint field-tag; not definitive
    { name: 'safetensors (JSON-header preceded by 8-byte LE length)', offset: 0, bytes: [-1, -1, -1, -1, -1, -1, -1, -1, 0x7b] }, // {  at byte 8 after 8-byte LE length
    { name: 'GGUF', offset: 0, bytes: [0x47, 0x47, 0x55, 0x46] },
    { name: 'pickle (Python)', offset: 0, bytes: [0x80, 0x04] }, // protocol 4
    { name: 'PyTorch (.pt zip)', offset: 0, bytes: [0x50, 0x4b, 0x03, 0x04] }, // zip with extras
    { name: 'NVIDIA DXCache (.nvph)', offset: 0, bytes: [0x4e, 0x56, 0x48, 0x50] }, // NVHP guess
    // SPIR-V binary
    { name: 'SPIR-V (LE)', offset: 0, bytes: [0x03, 0x02, 0x23, 0x07] },
    { name: 'SPIR-V (BE)', offset: 0, bytes: [0x07, 0x23, 0x02, 0x03] },
    // Class files
    { name: 'Java .class', offset: 0, bytes: [0xca, 0xfe, 0xba, 0xbe] },
    // wasm
    { name: 'WebAssembly (.wasm)', offset: 0, bytes: [0x00, 0x61, 0x73, 0x6d] },
];

function detectMagic(path: string, size: number): string | undefined {
    if (size === 0) return 'empty';
    const sampleSize = Math.min(512, size);
    const buf = Buffer.alloc(sampleSize);
    let fd: number;
    try {
        fd = openSync(path, 'r');
    } catch {
        return undefined;
    }
    try {
        readSync(fd, buf, 0, sampleSize, 0);
    } catch {
        closeSync(fd);
        return undefined;
    }
    closeSync(fd);

    for (const rule of MAGIC_RULES) {
        if (rule.offset + rule.bytes.length > sampleSize) continue;
        let matched = true;
        for (let i = 0; i < rule.bytes.length; i++) {
            const expected = rule.bytes[i];
            if (expected === -1) continue; // wildcard
            if (buf[rule.offset + i] !== expected) { matched = false; break; }
        }
        if (matched) return rule.name;
    }

    // Text vs binary heuristic — if no null bytes in first 512, call it text
    let hasNull = false;
    for (let i = 0; i < sampleSize; i++) {
        if (buf[i] === 0) { hasNull = true; break; }
    }
    return hasNull ? 'unknown-binary' : 'unknown-text';
}

// ─── Hashing ──────────────────────────────────────────────────────────────
const MAX_HASH_FILE_BYTES = 50 * 1024 * 1024; // 50 MiB safety cap

function sha256OfFile(path: string, size: number): string | undefined {
    if (size === 0) return 'EMPTY_FILE_SHA256';
    if (size > MAX_HASH_FILE_BYTES) return undefined; // too big, skip
    try {
        const hash = createHash('sha256');
        const buf = readFileSync(path);
        hash.update(buf);
        return hash.digest('hex');
    } catch {
        return undefined;
    }
}

// ─── Walking with cache ───────────────────────────────────────────────────
const SKIP_DIRS = new Set([
    'node_modules', 'target', 'dist', 'build', 'out', '.git', '.next', '.nuxt',
    '.cache', '.turbo', '.vite', '.parcel-cache', '__pycache__', '.venv', 'venv',
    'vendor', 'coverage', '.gradle', '.idea', 'tmp', '.tmp',
]);

interface FileVisit {
    path: string; // absolute
    rel: string;  // relative to project root
    size: number;
    mtime_ms: number;
    sha256: string | undefined;
    bucket: string;
    magic: string | undefined;
    from_cache: boolean;
}

function bucketOf(ext: string): string {
    // Lightweight bucket judgment; full classification lives in spread-sweep.
    // For dedup purposes we just need a coarse label.
    const sourceLike = /\.(ts|tsx|mts|cts|js|jsx|mjs|cjs|rs|c|cc|cpp|cxx|h|hpp|hh|hxx|inl|cu|cuh|glsl|vert|frag|comp|hlsl|wgsl|metal|py|go|rb|swift|kt|java|cs|zig|lua|dart|sh|ps1|bat|awk)$/.test(ext);
    const docLike = /\.(md|mdx|rst|txt|adoc)$/.test(ext);
    const configLike = /\.(toml|yaml|yml|json|jsonc|lock|ini|cfg|meta|asmdef|uss)$/.test(ext);
    const assetLike = /\.(png|jpg|jpeg|gif|webp|svg|bmp|ttf|otf|woff|woff2|mp3|mp4|wav|ogg)$/.test(ext);
    const binaryLike = /\.(exe|dll|so|dylib|lib|a|o|bin|dat|spv|hsaco|pyd|safetensors|gguf|pt|pth|onnx|ckpt|node|sqlite|db)$/.test(ext);
    if (sourceLike) return 'source';
    if (docLike) return 'doc';
    if (configLike) return 'config';
    if (assetLike) return 'asset';
    if (binaryLike) return 'binary';
    return 'unknown';
}

interface ProjectScanResult {
    project: { name: string; rel_path: string; root_dir: string };
    visits: FileVisit[];
    files_capped: boolean;
}

function scanProject(
    project: { name: string; rel_path: string; root_dir: string },
    cache: Map<string, CacheRow>,
    rebuildCache: boolean,
    maxFiles: number,
): ProjectScanResult {
    const visits: FileVisit[] = [];
    let cacheHits = 0;
    let cacheMisses = 0;
    let capped = false;

    function walk(dir: string, depth: number) {
        if (visits.length >= maxFiles) { capped = true; return; }
        if (depth > 6) return;
        let entries: string[];
        try { entries = readdirSync(dir); } catch { return; }
        for (const name of entries) {
            if (visits.length >= maxFiles) { capped = true; return; }
            if (name.startsWith('.') && name !== '.github' && name !== '.cargo') continue;
            if (SKIP_DIRS.has(name)) continue;
            const full = join(dir, name);
            let st;
            try { st = statSync(full); } catch { continue; }
            if (st.isDirectory()) { walk(full, depth + 1); continue; }
            if (!st.isFile()) continue;

            const dotIdx = name.lastIndexOf('.');
            const ext = dotIdx > 0 ? name.substring(dotIdx).toLowerCase() : '';
            const bucket = bucketOf(ext);
            const size = st.size;
            const mtime_ms = Math.floor(st.mtimeMs);

            // Cache lookup
            const cached = !rebuildCache ? cache.get(full) : undefined;
            if (cached && cached.size === size && cached.mtime_ms === mtime_ms) {
                cacheHits++;
                visits.push({
                    path: full, rel: relative(project.root_dir, full),
                    size, mtime_ms,
                    sha256: cached.sha256,
                    bucket: cached.bucket,
                    magic: cached.magic,
                    from_cache: true,
                });
                continue;
            }

            // Cache miss — do the work
            cacheMisses++;
            let sha: string | undefined;
            let magic: string | undefined;
            // Hash everything reasonably-sized
            sha = sha256OfFile(full, size);
            // Magic detection for unknown / binary buckets (cheap; only 512 bytes)
            if (bucket === 'unknown' || bucket === 'binary') {
                magic = detectMagic(full, size);
            }
            visits.push({
                path: full, rel: relative(project.root_dir, full),
                size, mtime_ms, sha256: sha, bucket, magic,
                from_cache: false,
            });
        }
    }

    walk(project.root_dir, 0);
    process.stderr.write(`  ${project.name.padEnd(40)} files=${visits.length.toString().padStart(5)} cached=${cacheHits.toString().padStart(5)} fresh=${cacheMisses.toString().padStart(5)}${capped ? ' [CAP]' : ''}\n`);
    return { project, visits, files_capped: capped };
}

// ─── Dedup map ────────────────────────────────────────────────────────────
interface DupCluster {
    sha256: string;
    byte_size: number;
    occurrences: number;
    bytes_wasted: number; // size * (occurrences - 1)
    paths: string[];
    bucket: string;
}

function buildDupMap(allVisits: FileVisit[]): DupCluster[] {
    const map = new Map<string, { size: number; bucket: string; paths: string[] }>();
    for (const v of allVisits) {
        if (!v.sha256 || v.sha256 === 'EMPTY_FILE_SHA256') continue;
        if (v.size === 0) continue;
        const entry = map.get(v.sha256) ?? { size: v.size, bucket: v.bucket, paths: [] };
        entry.paths.push(v.path);
        map.set(v.sha256, entry);
    }
    const clusters: DupCluster[] = [];
    for (const [sha, entry] of map) {
        if (entry.paths.length < 2) continue;
        clusters.push({
            sha256: sha,
            byte_size: entry.size,
            occurrences: entry.paths.length,
            bytes_wasted: entry.size * (entry.paths.length - 1),
            paths: entry.paths,
            bucket: entry.bucket,
        });
    }
    clusters.sort((a, b) => b.bytes_wasted - a.bytes_wasted);
    return clusters;
}

// ─── Magic mismatch detection ─────────────────────────────────────────────
function findMagicMismatches(allVisits: FileVisit[]): Array<{ path: string; ext: string; magic: string }> {
    const out: Array<{ path: string; ext: string; magic: string }> = [];
    for (const v of allVisits) {
        if (!v.magic) continue;
        if (v.magic.startsWith('unknown-')) continue;
        if (v.magic === 'empty') continue;
        const dotIdx = v.rel.lastIndexOf('.');
        const ext = dotIdx > 0 ? v.rel.substring(dotIdx).toLowerCase() : '<noext>';
        // Loose mismatch heuristic: magic name doesn't contain a token from the extension
        const extTok = ext.replace(/^\./, '').toLowerCase();
        if (extTok && !v.magic.toLowerCase().includes(extTok)) {
            out.push({ path: v.path, ext, magic: v.magic });
        }
    }
    return out;
}

// ─── Spread index types ───────────────────────────────────────────────────
interface SpreadProject {
    root_dir: string;
    rel_path: string;
    name: string;
    languages: string[];
    mode_hint: 'snipe' | 'sweep' | 'noise';
    repurposability_score: number;
}

interface SpreadIndex {
    generated_at: string;
    projects: SpreadProject[];
}

// ─── Main ─────────────────────────────────────────────────────────────────
async function main() {
    const args = parseArgs(process.argv.slice(2));

    if (!existsSync(args.indexPath)) {
        console.error(`[spread-value] missing ${args.indexPath} — run: bun run scripts/spread-sweep.ts --summary`);
        process.exit(1);
    }
    const idx = JSON.parse(readFileSync(args.indexPath, 'utf8')) as SpreadIndex;

    // Select projects
    let projects: SpreadProject[] = [];
    if (args.target) {
        const exact = idx.projects.find(p => p.name === args.target);
        if (exact) projects = [exact];
        else {
            projects = idx.projects.filter(p => p.name.includes(args.target!) || p.rel_path.includes(args.target!));
        }
    } else if (args.all) {
        projects = idx.projects;
    } else if (args.snipes) {
        projects = idx.projects.filter(p => p.mode_hint === 'snipe');
    }

    if (projects.length === 0) {
        console.error('[spread-value] no projects matched');
        process.exit(1);
    }

    console.error(`[spread-value] target: ${projects.length} project(s)`);
    console.error(`[spread-value] cache: ${CACHE_FILE} ${args.rebuildCache ? '(REBUILD)' : ''}`);

    const cache = args.rebuildCache ? new Map<string, CacheRow>() : loadCache();
    const initialCacheSize = cache.size;
    console.error(`[spread-value] cache loaded: ${initialCacheSize} rows`);

    const allVisits: FileVisit[] = [];
    for (const p of projects) {
        const result = scanProject(
            { name: p.name, rel_path: p.rel_path, root_dir: p.root_dir },
            cache,
            args.rebuildCache,
            args.maxFilesPerProject,
        );
        allVisits.push(...result.visits);
    }

    // Update cache with current state (fresh + cached rows)
    const updatedCache = new Map<string, CacheRow>(cache);
    for (const v of allVisits) {
        if (!v.sha256) continue;
        updatedCache.set(v.path, {
            path: v.path,
            size: v.size,
            mtime_ms: v.mtime_ms,
            sha256: v.sha256,
            bucket: v.bucket,
            magic: v.magic,
        });
    }
    writeCache(updatedCache.values());

    const freshCount = allVisits.filter(v => !v.from_cache).length;
    const cachedCount = allVisits.filter(v => v.from_cache).length;
    const cacheHitRate = allVisits.length > 0 ? cachedCount / allVisits.length : 0;

    // Dedup visits by absolute path before building the dup map. Snipe scans
    // can include nested project pairs (root + subproject member), so the same
    // file gets visited twice; we want it counted once.
    const visitsByPath = new Map<string, FileVisit>();
    for (const v of allVisits) {
        if (!visitsByPath.has(v.path)) visitsByPath.set(v.path, v);
    }
    const uniqueVisits = [...visitsByPath.values()];

    // Dedup analysis
    const dupClusters = buildDupMap(uniqueVisits)
        .filter(c => c.byte_size >= args.minDupBytes);

    // Magic mismatches (use unique visits so duplicates don't double-count)
    const mismatches = findMagicMismatches(uniqueVisits);

    // Bucket totals across scanned set (unique-path basis)
    const bucketTotals: Record<string, number> = {};
    const bucketBytes: Record<string, number> = {};
    for (const v of uniqueVisits) {
        bucketTotals[v.bucket] = (bucketTotals[v.bucket] || 0) + 1;
        bucketBytes[v.bucket] = (bucketBytes[v.bucket] || 0) + v.size;
    }

    const totalBytes = uniqueVisits.reduce((s, v) => s + v.size, 0);
    const wastedBytes = dupClusters.reduce((s, c) => s + c.bytes_wasted, 0);

    const out = {
        generated_at: new Date().toISOString(),
        spread_index_generated_at: idx.generated_at,
        projects_scanned: projects.map(p => p.name),
        total_files: allVisits.length,
        total_bytes: totalBytes,
        cache: {
            initial_rows: initialCacheSize,
            updated_rows: updatedCache.size,
            cache_hits: cachedCount,
            cache_misses: freshCount,
            hit_rate: cacheHitRate,
        },
        bucket_totals: bucketTotals,
        bucket_bytes: bucketBytes,
        duplicate_clusters: dupClusters,
        wasted_bytes_total: wastedBytes,
        magic_mismatches: mismatches.slice(0, 100),
        magic_mismatches_total: mismatches.length,
    };

    const outDir = dirname(args.output);
    if (outDir && !existsSync(outDir)) mkdirSync(outDir, { recursive: true });
    await Bun.write(args.output, JSON.stringify(out, null, 2));

    // Stdout summary
    console.log('');
    console.log('=== spread-value V2.2 summary ===');
    console.log(`Scanned: ${allVisits.length.toLocaleString()} files  (${(totalBytes / 1024 / 1024).toFixed(1)} MiB)`);
    console.log(`Cache:   ${cachedCount.toLocaleString()} hits / ${freshCount.toLocaleString()} fresh  (${(cacheHitRate * 100).toFixed(1)}% hit rate)`);
    console.log('');
    console.log('Bucket distribution (files / bytes):');
    for (const [b, n] of Object.entries(bucketTotals).sort((a, b) => b[1] - a[1])) {
        const bytes = bucketBytes[b] || 0;
        console.log(`  ${b.padEnd(8)} ${n.toString().padStart(7)} files  ${(bytes / 1024 / 1024).toFixed(1).padStart(8)} MiB`);
    }

    if (dupClusters.length > 0) {
        console.log('');
        console.log(`Duplicate clusters (${dupClusters.length}, ≥${args.minDupBytes} bytes/file, sorted by waste):`);
        console.log(`Total wasted bytes from duplicates: ${(wastedBytes / 1024 / 1024).toFixed(2)} MiB`);
        console.log('');
        for (const c of dupClusters.slice(0, 15)) {
            const sizeKb = (c.byte_size / 1024).toFixed(1);
            const wastedKb = (c.bytes_wasted / 1024).toFixed(1);
            console.log(`  ${c.occurrences}× ${sizeKb}KiB → ${wastedKb}KiB wasted  [${c.bucket}]`);
            for (const p of c.paths.slice(0, 3)) {
                console.log(`    ${relative(REPO_ROOT, p)}`);
            }
            if (c.paths.length > 3) console.log(`    ... +${c.paths.length - 3} more copies`);
        }
        if (dupClusters.length > 15) {
            console.log(`  ... ${dupClusters.length - 15} more clusters (full list in ${args.output})`);
        }
    } else {
        console.log('');
        console.log('No duplicate clusters above threshold.');
    }

    if (mismatches.length > 0) {
        console.log('');
        console.log(`Magic-byte mismatches (${mismatches.length} files; extension disagrees with content):`);
        for (const m of mismatches.slice(0, 10)) {
            console.log(`  ${m.ext.padEnd(10)} → magic="${m.magic}"  ${relative(REPO_ROOT, m.path)}`);
        }
        if (mismatches.length > 10) console.log(`  ... +${mismatches.length - 10} more`);
    }

    console.log('');
    console.log(`Wrote ${args.output}`);
    console.log(`Cache: ${CACHE_FILE} (${updatedCache.size} rows)`);
}

main();
