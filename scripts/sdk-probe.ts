#!/usr/bin/env bun
// @SID: SCRIPT_SDK_PROBE_V1
// SID: CHTHONIC_SDK_PROBE_TS_V1
// Purpose: Bun-first dry probe for official SDK surfaces before integration.

type Verdict = 'native' | 'compatible' | 'cli-only' | 'missing' | 'blocked';

interface SdkCandidate {
  id: string;
  packageName: string;
  lane: string;
  official: string;
  install: string;
  probes: string[];
  expected: Verdict;
}

interface ProbeResult {
  id: string;
  packageName: string;
  lane: string;
  official: string;
  install: string;
  version: string | null;
  verdict: Verdict;
  probes: Array<{
    specifier: string;
    ok: boolean;
    exports?: string[];
    error?: string;
  }>;
}

const args = new Set(Bun.argv.slice(2));
const catalogPath = readOption('--catalog') ?? 'sdk-catalog.toml';
const sdkArg = readOption('--sdk');
const json = args.has('--json');
const write = args.has('--write');
const list = args.has('--list');
const catalog = await readCatalog(catalogPath);
const SDK_CANDIDATES = catalog.candidates;

if (list) {
  print(SDK_CANDIDATES.map(({ id, packageName, lane, install, official }) => ({
    id,
    packageName,
    lane,
    install,
    official,
  })));
  process.exit(0);
}

const selected = sdkArg
  ? SDK_CANDIDATES.filter(candidate => candidate.id === sdkArg || candidate.packageName === sdkArg)
  : SDK_CANDIDATES;

if (selected.length === 0) {
  console.error(`Unknown SDK candidate: ${sdkArg}`);
  process.exit(2);
}

const results: ProbeResult[] = [];
for (const candidate of selected) {
  results.push(await probeCandidate(candidate));
}

const report = {
  generatedAt: new Date().toISOString(),
  runtime: {
    bun: Bun.version,
    platform: process.platform,
    arch: process.arch,
  },
  results,
};

if (write) {
  await Bun.write(catalog.probeReport, `${JSON.stringify(report, null, 2)}\n`);
}

print(report);

const failed = results.some(result => result.verdict === 'blocked');
process.exit(failed ? 1 : 0);

async function probeCandidate(candidate: SdkCandidate): Promise<ProbeResult> {
  const version = await readPackageVersion(candidate.packageName);
  if (!version) {
    return {
      id: candidate.id,
      packageName: candidate.packageName,
      lane: candidate.lane,
      official: candidate.official,
      install: candidate.install,
      version: null,
      verdict: 'missing',
      probes: candidate.probes.map(specifier => ({
        specifier,
        ok: false,
        error: 'package not installed',
      })),
    };
  }

  const probes = [];
  for (const specifier of candidate.probes) {
    try {
      const imported = await import(specifier);
      probes.push({
        specifier,
        ok: true,
        exports: Object.keys(imported).slice(0, 24),
      });
    } catch (error) {
      probes.push({
        specifier,
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const okCount = probes.filter(probe => probe.ok).length;
  let verdict: Verdict = candidate.expected;
  if (okCount === 0) {
    verdict = candidate.expected === 'cli-only' ? 'cli-only' : 'blocked';
  }

  return {
    id: candidate.id,
    packageName: candidate.packageName,
    lane: candidate.lane,
    official: candidate.official,
    install: candidate.install,
    version,
    verdict,
    probes,
  };
}

async function readPackageVersion(packageName: string): Promise<string | null> {
  const parts = packageName.startsWith('@') ? packageName.split('/') : [packageName];
  const packageJson = ['node_modules', ...parts, 'package.json'].join('/');
  const file = Bun.file(packageJson);
  if (!(await file.exists())) return null;

  try {
    const data = await file.json() as { version?: string };
    return data.version ?? null;
  } catch {
    return null;
  }
}

async function readCatalog(path: string): Promise<{ probeReport: string; candidates: SdkCandidate[] }> {
  const file = Bun.file(path);
  if (!(await file.exists())) {
    throw new Error(`SDK catalog not found: ${path}`);
  }

  const parsed = Bun.TOML.parse(await file.text()) as {
    catalog?: {
      defaultTag?: string;
      probeReport?: string;
    };
    managed?: Array<{
      id?: string;
      kind?: string;
      name?: string;
      target?: string;
      lane?: string;
      expected?: Verdict;
      official?: string;
      probes?: string[];
      tag?: string;
    }>;
  };

  const defaultTag = parsed.catalog?.defaultTag ?? 'latest';
  const probeReport = parsed.catalog?.probeReport ?? 'manifest/sdk-probes/latest.json';
  const candidates = (parsed.managed ?? [])
    .filter(entry => entry.kind === 'sdk')
    .map(entry => {
      const packageName = requireString(entry.name, 'managed.name');
      const target = requireString(entry.target, 'managed.target');
      const tag = entry.tag ?? defaultTag;
      return {
        id: requireString(entry.id, 'managed.id'),
        packageName,
        lane: requireString(entry.lane, 'managed.lane'),
        official: requireString(entry.official, 'managed.official'),
        install: target === 'devDependencies'
          ? `bun add -D ${packageName}@${tag}`
          : `bun add ${packageName}@${tag}`,
        probes: Array.isArray(entry.probes) ? entry.probes.map(String) : [],
        expected: normalizeVerdict(entry.expected),
      };
    });

  return { probeReport, candidates };
}

function normalizeVerdict(value: unknown): Verdict {
  if (
    value === 'native'
    || value === 'compatible'
    || value === 'cli-only'
    || value === 'missing'
    || value === 'blocked'
  ) {
    return value;
  }
  throw new Error(`Invalid expected verdict: ${String(value)}`);
}

function readOption(name: string): string | null {
  const index = Bun.argv.indexOf(name);
  if (index === -1) return null;
  return Bun.argv[index + 1] ?? null;
}

function requireString(value: unknown, label: string): string {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`Missing required string: ${label}`);
  }
  return value;
}

function print(value: unknown): void {
  if (json || write || typeof value !== 'object') {
    console.log(JSON.stringify(value, null, 2));
    return;
  }

  if ('results' in (value as { results?: unknown })) {
    const report = value as { results: ProbeResult[] };
    for (const result of report.results) {
      const version = result.version ?? 'not installed';
      console.log(`${result.id} ${version} ${result.verdict}`);
      for (const probe of result.probes) {
        const suffix = probe.ok ? `exports=${probe.exports?.length ?? 0}` : probe.error;
        console.log(`  ${probe.ok ? 'ok' : 'no'} ${probe.specifier} ${suffix}`);
      }
    }
    return;
  }

  console.log(JSON.stringify(value, null, 2));
}
