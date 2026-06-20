#!/usr/bin/env bun

// @SID: DIFF_CACHE_V1

// Diagnostic-only: diff cache files between Bun (.spread/file_index.ndjson)
// and Rust (.spread/file_index_rust.ndjson) to find walker divergence.

import { readFileSync } from 'node:fs';

function loadPaths(file: string): Set<string> {
    const set = new Set<string>();
    try {
        const raw = readFileSync(file, 'utf8');
        for (const line of raw.split(/\r?\n/)) {
            if (!line.trim()) continue;
            try {
                const row = JSON.parse(line);
                let p: string = row.path || '';
                // Strip Windows long-path prefix \\?\
                if (p.startsWith('\\\\?\\')) p = p.slice(4);
                // Normalize backslashes + case
                p = p.replace(/\\/g, '/').toLowerCase();
                set.add(p);
            } catch {}
        }
    } catch (e) {
        console.error(`failed to load ${file}: ${e}`);
    }
    return set;
}

const bun = loadPaths('.spread/file_index.ndjson');
const rust = loadPaths('.spread/file_index_rust.ndjson');

console.log(`bun rows : ${bun.size}`);
console.log(`rust rows: ${rust.size}`);

const onlyBun: string[] = [];
const onlyRust: string[] = [];
for (const p of bun) if (!rust.has(p)) onlyBun.push(p);
for (const p of rust) if (!bun.has(p)) onlyRust.push(p);

console.log(`only-in-bun : ${onlyBun.length}`);
console.log(`only-in-rust: ${onlyRust.length}`);

function topAreas(paths: string[], depth: number, n: number) {
    const counts = new Map<string, number>();
    for (const p of paths) {
        const parts = p.split('/');
        const key = parts.slice(0, depth).join('/');
        counts.set(key, (counts.get(key) || 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
}

console.log('\n--- top areas (depth 6) only-in-bun ---');
for (const [k, c] of topAreas(onlyBun, 6, 20)) {
    console.log(`  ${c.toString().padStart(5)}  ${k}`);
}

console.log('\n--- top areas (depth 6) only-in-rust ---');
for (const [k, c] of topAreas(onlyRust, 6, 20)) {
    console.log(`  ${c.toString().padStart(5)}  ${k}`);
}

console.log('\n--- sample only-in-bun paths ---');
for (const p of onlyBun.slice(0, 10)) console.log(`  ${p}`);

console.log('\n--- sample only-in-rust paths ---');
for (const p of onlyRust.slice(0, 10)) console.log(`  ${p}`);
