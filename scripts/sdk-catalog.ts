#!/usr/bin/env bun
// @SID: SCRIPT_SDK_CATALOG_V1
// Purpose: Bun-native SDK catalog reader and one-shot latest refresh runner.

type Target = 'dependencies' | 'devDependencies';

interface ManagedPackage {
  id: string;
  kind: 'sdk' | 'support';
  name: string;
  target: Target;
  lane: string;
  expected: string;
  official: string;
  probes: string[];
  tag?: string;
}

interface SdkCatalog {
  catalog: {
    name: string;
    defaultTag: string;
    probeReport: string;
  };
  managed: ManagedPackage[];
}

const args = new Set(Bun.argv.slice(2));
const catalogPath = readOption('--catalog') ?? 'sdk-catalog.toml';
const dryRun = args.has('--dry-run');
const catalog = await readCatalog(catalogPath);

if (args.has('--help') || Bun.argv.length <= 2) {
  printHelp();
  process.exit(0);
}

if (args.has('--json')) {
  console.log(JSON.stringify(catalog, null, 2));
  process.exit(0);
}

if (args.has('--list')) {
  printCatalog(catalog);
  process.exit(0);
}

if (args.has('--check')) {
  const failures = await checkPackageJson(catalog.managed);
  if (failures.length > 0) {
    for (const failure of failures) console.error(`missing ${failure}`);
    process.exit(1);
  }
  console.log(`ok ${catalog.managed.length} managed package(s) present`);
}

if (args.has('--install') || args.has('--refresh')) {
  await installLatest(catalog, dryRun);
}

if (args.has('--refresh') || args.has('--probe')) {
  await run(['bun', 'run', 'sdk:probe:write'], dryRun);
}

async function readCatalog(path: string): Promise<SdkCatalog> {
  const file = Bun.file(path);
  if (!(await file.exists())) {
    throw new Error(`SDK catalog not found: ${path}`);
  }

  const parsed = Bun.TOML.parse(await file.text()) as Partial<SdkCatalog>;
  const catalogConfig = parsed.catalog ?? {};
  const managed = parsed.managed ?? [];

  return {
    catalog: {
      name: requireString(catalogConfig.name, 'catalog.name'),
      defaultTag: requireString(catalogConfig.defaultTag, 'catalog.defaultTag'),
      probeReport: requireString(catalogConfig.probeReport, 'catalog.probeReport'),
    },
    managed: managed.map(normalizeManagedPackage),
  };
}

function normalizeManagedPackage(entry: unknown): ManagedPackage {
  const record = entry as Partial<ManagedPackage>;
  const target = requireString(record.target, 'managed.target');
  if (target !== 'dependencies' && target !== 'devDependencies') {
    throw new Error(`managed.target must be dependencies or devDependencies: ${target}`);
  }

  const kind = requireString(record.kind, 'managed.kind');
  if (kind !== 'sdk' && kind !== 'support') {
    throw new Error(`managed.kind must be sdk or support: ${kind}`);
  }

  return {
    id: requireString(record.id, 'managed.id'),
    kind,
    name: requireString(record.name, 'managed.name'),
    target,
    lane: requireString(record.lane, 'managed.lane'),
    expected: requireString(record.expected, 'managed.expected'),
    official: requireString(record.official, 'managed.official'),
    probes: Array.isArray(record.probes) ? record.probes.map(String) : [],
    tag: record.tag ? String(record.tag) : undefined,
  };
}

async function installLatest(catalogData: SdkCatalog, dry: boolean): Promise<void> {
  const dependencySpecs = specsForTarget(catalogData, 'dependencies');
  const devDependencySpecs = specsForTarget(catalogData, 'devDependencies');

  if (dependencySpecs.length > 0) {
    await run(['bun', 'add', ...dependencySpecs], dry);
  }

  if (devDependencySpecs.length > 0) {
    await run(['bun', 'add', '-D', ...devDependencySpecs], dry);
  }
}

function specsForTarget(catalogData: SdkCatalog, target: Target): string[] {
  return catalogData.managed
    .filter(entry => entry.target === target)
    .map(entry => `${entry.name}@${entry.tag ?? catalogData.catalog.defaultTag}`);
}

async function checkPackageJson(managed: ManagedPackage[]): Promise<string[]> {
  const packageJson = await Bun.file('package.json').json() as {
    dependencies?: Record<string, string>;
    devDependencies?: Record<string, string>;
  };

  return managed
    .filter(entry => !packageJson[entry.target]?.[entry.name])
    .map(entry => `${entry.name} in ${entry.target}`);
}

async function run(cmd: string[], dry: boolean): Promise<void> {
  console.log(dry ? `dry-run ${cmd.join(' ')}` : cmd.join(' '));
  if (dry) return;

  const proc = Bun.spawn({
    cmd,
    stdout: 'inherit',
    stderr: 'inherit',
    stdin: 'inherit',
  });
  const exitCode = await proc.exited;
  if (exitCode !== 0) process.exit(exitCode);
}

function printCatalog(catalogData: SdkCatalog): void {
  console.log(`${catalogData.catalog.name} (${catalogData.catalog.defaultTag})`);
  for (const target of ['dependencies', 'devDependencies'] as const) {
    console.log(`\n${target}`);
    for (const entry of catalogData.managed.filter(item => item.target === target)) {
      const tag = entry.tag ?? catalogData.catalog.defaultTag;
      console.log(`  ${entry.id.padEnd(24)} ${entry.name}@${tag} ${entry.kind}/${entry.lane}`);
    }
  }
}

function printHelp(): void {
  console.log(`sdk-catalog

Usage:
  bun run scripts/sdk-catalog.ts --list
  bun run scripts/sdk-catalog.ts --check
  bun run scripts/sdk-catalog.ts --refresh [--dry-run]
  bun run scripts/sdk-catalog.ts --install [--dry-run]
  bun run scripts/sdk-catalog.ts --probe [--dry-run]

Options:
  --catalog <path>  Use a different SDK catalog TOML.
  --json            Print parsed catalog JSON.
`);
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
