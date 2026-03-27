// @SID: EXT_ENTROPYWORKER_V1
import * as fs from 'fs/promises';
import * as path from 'path';
import { parentPort } from 'worker_threads';
import type {
    EntropyFileRecord,
    EntropyGraphEdge,
    EntropyGraphNode,
    EntropyGraphPayload,
    EntropyWorkerEvent,
    EntropyWorkerRequest,
} from './types';

const EXCLUDED_DIRS = new Set([
    '.git',
    '.hg',
    '.svn',
    '.next',
    '.venv',
    'node_modules',
    'target',
    'dist',
    'build',
    'coverage',
    '.turbo',
    '.cache',
    '.idea',
    '.vscode',
]);

const ALLOWED_EXTENSIONS = new Set([
    '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
    '.py', '.rs', '.rb', '.sol',
    '.json', '.toml', '.yaml', '.yml', '.md',
]);

const MAX_FILE_BYTES = 256 * 1024;
const BATCH_SIZE = 200;

const records = new Map<string, EntropyFileRecord>();
const dependencies = new Map<string, string[]>();

let activeRoot = '';

if (!parentPort) {
    throw new Error('entropyWorker must run inside worker_threads');
}

parentPort.on('message', async (request: EntropyWorkerRequest) => {
    try {
        switch (request.type) {
            case 'scan':
                activeRoot = request.root;
                await runScan(request.root, request.maxFiles);
                break;
            case 'refresh-file':
                if (!request.path.startsWith(request.root)) {
                    break;
                }
                await refreshSingleFile(request.root, request.path);
                break;
            case 'graph':
                postMessage({
                    type: 'graph-result',
                    graph: buildGraph(request.limit),
                });
                break;
            case 'stop':
                process.exit(0);
                break;
        }
    } catch (error) {
        postMessage({
            type: 'error',
            message: 'Worker request failed',
            detail: stringifyError(error),
        });
    }
});

async function runScan(root: string, maxFiles: number): Promise<void> {
    const started = Date.now();
    const files = await collectFiles(root, maxFiles);

    const changed: EntropyFileRecord[] = [];
    for (const file of files) {
        const record = await analyzeFile(root, file);
        if (!record) {
            continue;
        }
        records.set(record.path, record);
        changed.push(record);

        if (changed.length >= BATCH_SIZE) {
            postMessage({
                type: 'scan-progress',
                records: changed.splice(0, changed.length),
            });
        }
    }

    if (changed.length > 0) {
        postMessage({
            type: 'scan-progress',
            records: changed,
        });
    }

    postMessage({
        type: 'scan-complete',
        total: records.size,
        durationMs: Date.now() - started,
    });
}

async function refreshSingleFile(root: string, filePath: string): Promise<void> {
    const record = await analyzeFile(root, filePath);
    if (record) {
        records.set(record.path, record);
        postMessage({
            type: 'scan-progress',
            records: [record],
        });
    }
}

async function collectFiles(root: string, maxFiles: number): Promise<string[]> {
    const output: string[] = [];
    const stack: string[] = [root];

    while (stack.length > 0 && output.length < maxFiles) {
        const current = stack.pop();
        if (!current) {
            continue;
        }

        let entries: Array<import('fs').Dirent>;
        try {
            entries = await fs.readdir(current, { withFileTypes: true });
        } catch {
            continue;
        }

        for (const entry of entries) {
            if (output.length >= maxFiles) {
                break;
            }

            const fullPath = path.join(current, entry.name);
            if (entry.isDirectory()) {
                if (!EXCLUDED_DIRS.has(entry.name)) {
                    stack.push(fullPath);
                }
                continue;
            }

            if (!entry.isFile()) {
                continue;
            }

            if (!ALLOWED_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
                continue;
            }

            output.push(fullPath);
        }
    }

    return output;
}

async function analyzeFile(root: string, absolutePath: string): Promise<EntropyFileRecord | null> {
    let stat: import('fs').Stats;
    try {
        stat = await fs.stat(absolutePath);
    } catch {
        return null;
    }

    if (stat.size > MAX_FILE_BYTES) {
        return null;
    }

    let source = '';
    try {
        source = await fs.readFile(absolutePath, 'utf8');
    } catch {
        return null;
    }

    const relativePath = normalizePath(path.relative(root, absolutePath));
    const ext = path.extname(relativePath).toLowerCase();
    const language = ext.replace('.', '') || 'text';

    const lines = source.split(/\r?\n/);
    const lineCount = lines.length;

    const branchHits = countMatches(source, /\b(if|else if|elif|for|while|switch|case|catch|match|when|unless|rescue)\b/g);
    const booleanHits = countMatches(source, /&&|\|\||\?/g);
    const functionHits = countMatches(source, /\b(function|def|fn|class|trait|impl)\b/g);
    const debtHits = countMatches(source, /\b(TODO|FIXME|HACK|XXX|BUG)\b/gi);
    const longLines = lines.filter((line) => line.length > 120).length;

    const complexity = branchHits + Math.floor(booleanHits / 2) + Math.floor(functionHits / 3);
    const debt = debtHits + Math.floor(longLines / 15);
    const freshness = computeFreshness(stat.mtimeMs);

    const entropy = clamp01(
        (normalize(complexity, 0, 40) * 0.56)
        + (normalize(debt, 0, 10) * 0.31)
        + ((1 - freshness) * 0.13),
    );

    dependencies.set(relativePath, extractDependencies(source, relativePath, ext));

    return {
        path: relativePath,
        entropy,
        complexity,
        debt,
        freshness,
        mtimeMs: stat.mtimeMs,
        language,
        lines: lineCount,
    };
}

function extractDependencies(source: string, relativePath: string, ext: string): string[] {
    const found = new Set<string>();
    const add = (value: string | undefined) => {
        if (!value) {
            return;
        }
        const cleaned = value.trim();
        if (!cleaned || cleaned.startsWith('node:')) {
            return;
        }
        found.add(cleaned);
    };

    if (ext === '.ts' || ext === '.tsx' || ext === '.js' || ext === '.jsx' || ext === '.mjs' || ext === '.cjs') {
        const importPattern = /(?:import|export)\s+.*?from\s+['"]([^'"]+)['"]|require\(\s*['"]([^'"]+)['"]\s*\)/g;
        let match: RegExpExecArray | null = null;
        while ((match = importPattern.exec(source)) !== null) {
            const specifier = match[1] || match[2];
            add(resolveRelativeSpecifier(relativePath, specifier));
        }
    } else if (ext === '.py') {
        const importPattern = /^\s*(?:from\s+([A-Za-z0-9_\.]+)\s+import|import\s+([A-Za-z0-9_\.]+))/gm;
        let match: RegExpExecArray | null = null;
        while ((match = importPattern.exec(source)) !== null) {
            add(match[1] || match[2]);
        }
    } else if (ext === '.rs') {
        const usePattern = /^\s*use\s+([A-Za-z0-9_:]+)\s*;/gm;
        let match: RegExpExecArray | null = null;
        while ((match = usePattern.exec(source)) !== null) {
            add(match[1]);
        }
    } else if (ext === '.rb') {
        const requirePattern = /^\s*require(?:_relative)?\s+['"]([^'"]+)['"]/gm;
        let match: RegExpExecArray | null = null;
        while ((match = requirePattern.exec(source)) !== null) {
            add(match[1]);
        }
    }

    return Array.from(found);
}

function buildGraph(limit: number): EntropyGraphPayload {
    const ranked = Array.from(records.values())
        .sort((a, b) => b.entropy - a.entropy)
        .slice(0, Math.max(20, Math.min(limit, 800)));

    const nodeIds = new Set(ranked.map((entry) => entry.path));
    const edges: EntropyGraphEdge[] = [];

    for (const node of ranked) {
        const deps = dependencies.get(node.path) ?? [];
        let emitted = 0;
        for (const dep of deps) {
            if (emitted >= 8) {
                break;
            }
            const target = resolveDependencyTarget(node.path, dep, nodeIds);
            if (!target || target === node.path) {
                continue;
            }
            edges.push({
                source: node.path,
                target,
                weight: 1,
            });
            emitted += 1;
        }
    }

    const degreeMap = new Map<string, number>();
    for (const node of ranked) {
        degreeMap.set(node.path, 0);
    }
    for (const edge of edges) {
        degreeMap.set(edge.source, (degreeMap.get(edge.source) ?? 0) + 1);
        degreeMap.set(edge.target, (degreeMap.get(edge.target) ?? 0) + 1);
    }

    const nodes = layoutNodes(ranked, degreeMap);
    return {
        nodes,
        edges,
        generatedAt: Date.now(),
    };
}

function layoutNodes(
    ranked: EntropyFileRecord[],
    degreeMap: Map<string, number>,
): EntropyGraphNode[] {
    const buckets: EntropyFileRecord[][] = [[], [], [], [], []];
    for (const item of ranked) {
        if (item.entropy >= 0.85) {
            buckets[0].push(item);
        } else if (item.entropy >= 0.65) {
            buckets[1].push(item);
        } else if (item.entropy >= 0.45) {
            buckets[2].push(item);
        } else if (item.entropy >= 0.25) {
            buckets[3].push(item);
        } else {
            buckets[4].push(item);
        }
    }

    const nodes: EntropyGraphNode[] = [];
    const baseRadius = 120;
    const ringStep = 95;

    for (let ring = 0; ring < buckets.length; ring += 1) {
        const bucket = buckets[ring];
        const radius = baseRadius + (ring * ringStep);

        bucket.forEach((item, index) => {
            const angle = (Math.PI * 2 * index) / Math.max(bucket.length, 1);
            const noise = pseudoNoise(item.path) * 24;
            nodes.push({
                id: item.path,
                label: path.basename(item.path),
                entropy: item.entropy,
                degree: degreeMap.get(item.path) ?? 0,
                x: Math.cos(angle) * (radius + noise),
                y: Math.sin(angle) * (radius + noise),
            });
        });
    }

    return nodes;
}

function resolveDependencyTarget(originPath: string, dependency: string, nodes: Set<string>): string | null {
    if (dependency.startsWith('.')) {
        const baseDir = path.dirname(originPath);
        const resolved = normalizePath(path.join(baseDir, dependency));
        if (nodes.has(resolved)) {
            return resolved;
        }
        const withTs = `${resolved}.ts`;
        const withPy = `${resolved}.py`;
        const withRs = `${resolved}.rs`;
        if (nodes.has(withTs)) {
            return withTs;
        }
        if (nodes.has(withPy)) {
            return withPy;
        }
        if (nodes.has(withRs)) {
            return withRs;
        }
    }

    for (const nodePath of nodes) {
        if (nodePath.endsWith(dependency) || nodePath.includes(`${dependency}.`)) {
            return nodePath;
        }
    }

    return null;
}

function resolveRelativeSpecifier(originPath: string, specifier: string): string {
    if (!specifier.startsWith('.')) {
        return specifier;
    }

    const originDir = path.dirname(originPath);
    return normalizePath(path.join(originDir, specifier));
}

function normalizePath(rawPath: string): string {
    return rawPath.replace(/\\/g, '/');
}

function countMatches(source: string, pattern: RegExp): number {
    const matches = source.match(pattern);
    return matches ? matches.length : 0;
}

function computeFreshness(mtimeMs: number): number {
    const ageHours = Math.max(0, (Date.now() - mtimeMs) / (1000 * 60 * 60));
    // Exponential decay to keep recent edits visibly "alive".
    return clamp01(Math.exp(-(ageHours / 96)));
}

function normalize(value: number, min: number, max: number): number {
    if (max <= min) {
        return 0;
    }
    return clamp01((value - min) / (max - min));
}

function clamp01(value: number): number {
    if (value < 0) {
        return 0;
    }
    if (value > 1) {
        return 1;
    }
    return value;
}

function pseudoNoise(value: string): number {
    let hash = 0;
    for (let i = 0; i < value.length; i += 1) {
        hash = ((hash << 5) - hash) + value.charCodeAt(i);
        hash |= 0;
    }
    return (Math.abs(hash) % 1000) / 1000;
}

function stringifyError(error: unknown): string {
    if (error instanceof Error) {
        return `${error.name}: ${error.message}\n${error.stack ?? ''}`.trim();
    }
    return String(error);
}

function postMessage(event: EntropyWorkerEvent): void {
    parentPort?.postMessage(event);
}

// Keep TS/Node happy in worker context when the parent disappears unexpectedly.
process.on('disconnect', () => {
    if (activeRoot) {
        process.exit(0);
    }
});
