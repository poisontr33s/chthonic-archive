#!/usr/bin/env bun
// @SID: SCRIPT_SDK_PROBE_V1
// SID: CHTHONIC_SDK_PROBE_TS_V1
// Purpose: Bun-first dry probe for official SDK surfaces before integration.

type Verdict = 'native' | 'compatible' | 'cli-only' | 'missing' | 'blocked';

interface SdkCandidate {
  id: string;
  packageName: string;
  lane: 'vscode' | 'electron' | 'mcp' | 'openai' | 'anthropic';
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

const SDK_CANDIDATES: SdkCandidate[] = [
  {
    id: 'vscode-dts',
    packageName: '@vscode/dts',
    lane: 'vscode',
    official: 'https://code.visualstudio.com/api/advanced-topics/using-proposed-api',
    install: 'bun add -D @vscode/dts@latest',
    probes: [],
    expected: 'cli-only',
  },
  {
    id: 'vscode-test-electron',
    packageName: '@vscode/test-electron',
    lane: 'vscode',
    official: 'https://code.visualstudio.com/api/working-with-extensions/testing-extension',
    install: 'bun add -D @vscode/test-electron@latest',
    probes: ['@vscode/test-electron'],
    expected: 'compatible',
  },
  {
    id: 'vscode-test-web',
    packageName: '@vscode/test-web',
    lane: 'vscode',
    official: 'https://code.visualstudio.com/api/extension-guides/web-extensions',
    install: 'bun add -D @vscode/test-web@latest',
    probes: ['@vscode/test-web'],
    expected: 'compatible',
  },
  {
    id: 'vscode-test-cli',
    packageName: '@vscode/test-cli',
    lane: 'vscode',
    official: 'https://code.visualstudio.com/api/working-with-extensions/testing-extension',
    install: 'bun add -D @vscode/test-cli@latest',
    probes: ['@vscode/test-cli'],
    expected: 'cli-only',
  },
  {
    id: 'vscode-vsce',
    packageName: '@vscode/vsce',
    lane: 'vscode',
    official: 'https://code.visualstudio.com/api/working-with-extensions/publishing-extension',
    install: 'bun add -D @vscode/vsce@latest',
    probes: ['@vscode/vsce'],
    expected: 'cli-only',
  },
  {
    id: 'mcp-typescript',
    packageName: '@modelcontextprotocol/sdk',
    lane: 'mcp',
    official: 'https://modelcontextprotocol.io/docs',
    install: 'bun add @modelcontextprotocol/sdk@latest',
    probes: [
      '@modelcontextprotocol/sdk/types.js',
      '@modelcontextprotocol/sdk/server/index.js',
      '@modelcontextprotocol/sdk/client/index.js',
    ],
    expected: 'native',
  },
  {
    id: 'openai-node',
    packageName: 'openai',
    lane: 'openai',
    official: 'https://platform.openai.com/docs/libraries',
    install: 'bun add openai@latest',
    probes: ['openai'],
    expected: 'compatible',
  },
  {
    id: 'openai-agents',
    packageName: '@openai/agents',
    lane: 'openai',
    official: 'https://openai.github.io/openai-agents-js/',
    install: 'bun add @openai/agents@latest zod@latest',
    probes: ['@openai/agents'],
    expected: 'compatible',
  },
  {
    id: 'openai-codex-sdk',
    packageName: '@openai/codex-sdk',
    lane: 'openai',
    official: 'https://developers.openai.com/codex/sdk/',
    install: 'bun add @openai/codex-sdk@latest',
    probes: ['@openai/codex-sdk'],
    expected: 'compatible',
  },
  {
    id: 'anthropic-sdk',
    packageName: '@anthropic-ai/sdk',
    lane: 'anthropic',
    official: 'https://docs.anthropic.com/',
    install: 'bun add @anthropic-ai/sdk@latest',
    probes: ['@anthropic-ai/sdk'],
    expected: 'compatible',
  },
  {
    id: 'claude-agent-sdk',
    packageName: '@anthropic-ai/claude-agent-sdk',
    lane: 'anthropic',
    official: 'https://docs.anthropic.com/',
    install: 'bun add @anthropic-ai/claude-agent-sdk@latest',
    probes: ['@anthropic-ai/claude-agent-sdk'],
    expected: 'compatible',
  },
];

const args = new Set(Bun.argv.slice(2));
const sdkArg = readOption('--sdk');
const json = args.has('--json');
const write = args.has('--write');
const list = args.has('--list');

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
  await Bun.write('manifest/sdk-probes/latest.json', `${JSON.stringify(report, null, 2)}\n`);
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

function readOption(name: string): string | null {
  const index = Bun.argv.indexOf(name);
  if (index === -1) return null;
  return Bun.argv[index + 1] ?? null;
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
