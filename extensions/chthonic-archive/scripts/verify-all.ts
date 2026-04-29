#!/usr/bin/env bun
// @SID: EXT_VERIFY_ALL_V1
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const extensionRoot = path.resolve(import.meta.dir, '..');
const repoRoot = path.resolve(extensionRoot, '..', '..');
const manifestDir = path.join(repoRoot, 'manifest');

type LaneStatus = 'MISSING' | 'PRESENT' | 'SMOKE_OK' | 'SMOKE_FAIL';

interface LaneResult {
    name: string;
    status: LaneStatus;
    artifactPath?: string;
    artifactCandidates: string[];
    smokeNote?: string;
    error?: string;
}

const platformExe = process.platform === 'win32' ? '.exe' : '';
const platformDll = process.platform === 'win32' ? '.dll' : process.platform === 'darwin' ? '.dylib' : '.so';

const lanes: LaneResult[] = [
    verifySynapseNode(),
    verifyChthonicDaemon(),
    verifyEntropyLedgerHost(),
];

const overall = lanes.every((lane) => lane.status === 'SMOKE_OK' || lane.status === 'PRESENT')
    ? 'passed'
    : 'failed';

const report = {
    schema: 'verify_all/v1',
    emittedAt: new Date().toISOString(),
    platform: process.platform,
    arch: process.arch,
    status: overall,
    lanes,
};

mkdirSync(manifestDir, { recursive: true });
writeFileSync(path.join(manifestDir, 'verify_all.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
process.exit(overall === 'passed' ? 0 : 1);

function verifySynapseNode(): LaneResult {
    const platformArtifact = `synapse-${process.platform}-${process.arch}.node`;
    const candidates = [
        path.join(extensionRoot, 'native', 'dist', platformArtifact),
        path.join(extensionRoot, 'src', 'reactor', 'synapse.node'),
        path.join(extensionRoot, 'native', 'target', 'release', `synapse_node${platformDll}`),
    ];
    const found = candidates.find((p) => existsSync(p));
    if (!found) {
        return {
            name: 'synapse-node',
            status: 'MISSING',
            artifactCandidates: candidates,
            error: 'no synapse.node artifact in any expected location',
        };
    }

    try {
        const req = createRequire(import.meta.filename);
        const binding = req(found) as { SynapseReader?: unknown };
        if (typeof binding.SynapseReader !== 'function') {
            return {
                name: 'synapse-node',
                status: 'SMOKE_FAIL',
                artifactPath: found,
                artifactCandidates: candidates,
                error: 'binding loaded but SynapseReader export missing',
            };
        }
        return {
            name: 'synapse-node',
            status: 'SMOKE_OK',
            artifactPath: found,
            artifactCandidates: candidates,
            smokeNote: 'createRequire() loaded the .node and SynapseReader is exported',
        };
    } catch (error) {
        return {
            name: 'synapse-node',
            status: 'SMOKE_FAIL',
            artifactPath: found,
            artifactCandidates: candidates,
            error: error instanceof Error ? error.message : String(error),
        };
    }
}

function verifyChthonicDaemon(): LaneResult {
    const candidates = [
        path.join(extensionRoot, 'native', 'target', 'release', `chthonic-daemon${platformExe}`),
        path.join(extensionRoot, 'native', 'target', 'debug', `chthonic-daemon${platformExe}`),
    ];
    const found = candidates.find((p) => existsSync(p));
    if (!found) {
        return {
            name: 'chthonic-daemon',
            status: 'MISSING',
            artifactCandidates: candidates,
            error: 'no chthonic-daemon binary in target/{release,debug}',
        };
    }

    const result = spawnSync(found, ['--help'], { encoding: 'utf8', timeout: 5000 });
    if (result.status === 0 && result.stdout.includes('--workspace')) {
        return {
            name: 'chthonic-daemon',
            status: 'SMOKE_OK',
            artifactPath: found,
            artifactCandidates: candidates,
            smokeNote: '--help reports --workspace flag; daemon CLI surface intact',
        };
    }
    return {
        name: 'chthonic-daemon',
        status: 'SMOKE_FAIL',
        artifactPath: found,
        artifactCandidates: candidates,
        error: `--help exit=${result.status}; stderr=${result.stderr.slice(0, 200)}`,
    };
}

function verifyEntropyLedgerHost(): LaneResult {
    const candidates = [
        path.join(extensionRoot, 'native', 'target', 'release', `entropy-ledger-host${platformExe}`),
        path.join(extensionRoot, 'native', 'target', 'debug', `entropy-ledger-host${platformExe}`),
    ];
    const found = candidates.find((p) => existsSync(p));
    if (!found) {
        return {
            name: 'entropy-ledger-host',
            status: 'MISSING',
            artifactCandidates: candidates,
            error: 'no entropy-ledger-host binary in target/{release,debug}',
        };
    }

    const result = spawnSync(found, ['--help'], { encoding: 'utf8', timeout: 5000 });
    if (result.status === 0 || result.status === 2) {
        return {
            name: 'entropy-ledger-host',
            status: 'SMOKE_OK',
            artifactPath: found,
            artifactCandidates: candidates,
            smokeNote: `--help exit=${result.status}; binary executes without crash`,
        };
    }
    return {
        name: 'entropy-ledger-host',
        status: 'SMOKE_FAIL',
        artifactPath: found,
        artifactCandidates: candidates,
        error: `--help exit=${result.status}; stderr=${result.stderr.slice(0, 200)}`,
    };
}
