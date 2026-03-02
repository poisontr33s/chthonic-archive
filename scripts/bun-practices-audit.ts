#!/usr/bin/env bun
import { mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';

type IssueLevel = 'warn' | 'error';

type Issue = {
  level: IssueLevel;
  category: 'package-script' | 'tsconfig' | 'source';
  file: string;
  message: string;
};

type Report = {
  createdAt: string;
  root: string;
  sourceFileCount: number;
  packageCount: number;
  tsconfigCount: number;
  issues: Issue[];
};

const root = process.cwd();
const cacheDir = path.join(root, '.chthonic', 'cache');
const outputPath = path.join(cacheDir, 'bun-practices-audit.json');
const strict = process.argv.includes('--strict');
const jsonOnly = process.argv.includes('--json');

const skipDirs = new Set([
  '.git',
  '.chthonic',
  '.vscode-test',
  'node_modules',
  'dist',
  'target',
  '.venv',
  '.next',
  '.turbo',
]);

const sourceExtensions = new Set(['.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx']);

function walk(dir: string, out: string[]): void {
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory()) {
      if (skipDirs.has(entry.name)) {
        continue;
      }
      walk(path.join(dir, entry.name), out);
      continue;
    }
    out.push(path.join(dir, entry.name));
  }
}

function rel(p: string): string {
  return path.relative(root, p).replaceAll('\\', '/');
}

function parseJson(filePath: string): unknown {
  try {
    return JSON.parse(readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

function collectFiles(): string[] {
  const all: string[] = [];
  walk(root, all);
  return all;
}

function checkPackageScripts(filePath: string, issues: Issue[]): void {
  const parsed = parseJson(filePath);
  if (!parsed || typeof parsed !== 'object') {
    issues.push({
      level: 'warn',
      category: 'package-script',
      file: rel(filePath),
      message: 'package.json is unreadable or invalid JSON',
    });
    return;
  }

  const pkg = parsed as { scripts?: Record<string, string> };
  const scripts = pkg.scripts ?? {};
  for (const [name, value] of Object.entries(scripts)) {
    if (/\b(npm|pnpm|yarn|npx)\b/i.test(value)) {
      issues.push({
        level: 'warn',
        category: 'package-script',
        file: rel(filePath),
        message: `script '${name}' uses npm/pnpm/yarn/npx; prefer bun-native invocation`,
      });
    }

    if (/(^|\s)node\s+/.test(value) && !/--target\s+node/.test(value)) {
      issues.push({
        level: 'warn',
        category: 'package-script',
        file: rel(filePath),
        message: `script '${name}' invokes node directly; prefer 'bun run' or 'bun x'`,
      });
    }
  }
}

function checkTsconfig(filePath: string, issues: Issue[]): void {
  if (path.basename(filePath).toLowerCase() === 'tsconfig.bun-base.json') {
    return;
  }

  const parsed = parseJson(filePath);
  if (!parsed || typeof parsed !== 'object') {
    issues.push({
      level: 'warn',
      category: 'tsconfig',
      file: rel(filePath),
      message: 'tsconfig is unreadable or invalid JSON',
    });
    return;
  }

  const tsconfig = parsed as {
    extends?: string;
    compilerOptions?: Record<string, unknown>;
  };

  const compiler = tsconfig.compilerOptions ?? {};
  const usesBase = typeof tsconfig.extends === 'string' && tsconfig.extends.endsWith('tsconfig.bun-base.json');

  const moduleResolution = compiler.moduleResolution;
  const moduleKind = compiler.module;
  const noEmit = compiler.noEmit;
  const strictMode = compiler.strict;
  const moduleResolutionNormalized =
    typeof moduleResolution === 'string' ? moduleResolution.toLowerCase() : '';
  const moduleKindNormalized = typeof moduleKind === 'string' ? moduleKind.toLowerCase() : '';

  if (
    !usesBase
    && !(
      moduleResolutionNormalized === 'bundler'
      && moduleKindNormalized === 'preserve'
      && noEmit === true
      && strictMode === true
    )
  ) {
    issues.push({
      level: 'warn',
      category: 'tsconfig',
      file: rel(filePath),
      message:
        "does not extend shared Bun base and is missing canonical Bun compiler defaults (module=Preserve, moduleResolution=Bundler, strict=true, noEmit=true)",
    });
  }

  if (typeof moduleResolution === 'string' && moduleResolutionNormalized !== 'bundler') {
    issues.push({
      level: 'warn',
      category: 'tsconfig',
      file: rel(filePath),
      message: `moduleResolution is '${moduleResolution}', expected 'Bundler' for Bun lanes`,
    });
  }

  if (typeof moduleKind === 'string' && moduleKindNormalized !== 'preserve') {
    issues.push({
      level: 'warn',
      category: 'tsconfig',
      file: rel(filePath),
      message: `module is '${moduleKind}', expected 'Preserve' for Bun lanes`,
    });
  }

  if (noEmit === false) {
    issues.push({
      level: 'warn',
      category: 'tsconfig',
      file: rel(filePath),
      message: "noEmit=false detected; prefer noEmit=true when Bun handles transpilation",
    });
  }
}

function checkSourceFile(filePath: string, issues: Issue[]): void {
  const extension = path.extname(filePath).toLowerCase();
  if (!sourceExtensions.has(extension)) {
    return;
  }

  const normalized = rel(filePath);
  const content = readFileSync(filePath, 'utf8');

  if ((extension === '.js' || extension === '.mjs' || extension === '.cjs') && /@ts-ignore/.test(content)) {
    issues.push({
      level: 'warn',
      category: 'source',
      file: normalized,
      message: 'contains @ts-ignore; audit if it can be removed in Bun lane',
    });
  }
}

function main(): number {
  const files = collectFiles();
  const sourceFiles = files.filter((filePath) => sourceExtensions.has(path.extname(filePath).toLowerCase()));
  const packageFiles = files.filter((filePath) => path.basename(filePath) === 'package.json');
  const tsconfigFiles = files.filter((filePath) => /^tsconfig(\..+)?\.json$/i.test(path.basename(filePath)));
  const issues: Issue[] = [];

  for (const packagePath of packageFiles) {
    checkPackageScripts(packagePath, issues);
  }

  for (const tsconfigPath of tsconfigFiles) {
    checkTsconfig(tsconfigPath, issues);
  }

  for (const sourcePath of sourceFiles) {
    checkSourceFile(sourcePath, issues);
  }

  const report: Report = {
    createdAt: new Date().toISOString(),
    root,
    sourceFileCount: sourceFiles.length,
    packageCount: packageFiles.length,
    tsconfigCount: tsconfigFiles.length,
    issues,
  };

  mkdirSync(cacheDir, { recursive: true });
  writeFileSync(outputPath, JSON.stringify(report, null, 2), 'utf8');

  if (jsonOnly) {
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  } else {
    console.log('[bun-audit] Bun Practices Sweep');
    console.log(`[bun-audit] source files: ${report.sourceFileCount}`);
    console.log(`[bun-audit] package.json files: ${report.packageCount}`);
    console.log(`[bun-audit] tsconfig files: ${report.tsconfigCount}`);
    console.log(`[bun-audit] issues: ${report.issues.length}`);
    console.log(`[bun-audit] report: ${rel(outputPath)}`);

    const byCategory = new Map<Issue['category'], Issue[]>();
    for (const issue of report.issues) {
      const bucket = byCategory.get(issue.category) ?? [];
      bucket.push(issue);
      byCategory.set(issue.category, bucket);
    }

    for (const [category, categoryIssues] of byCategory.entries()) {
      console.log(`\n[bun-audit] ${category} (${categoryIssues.length})`);
      for (const issue of categoryIssues.slice(0, 20)) {
        console.log(`  - ${issue.file}: ${issue.message}`);
      }
      if (categoryIssues.length > 20) {
        console.log(`  ... +${categoryIssues.length - 20} more`);
      }
    }
  }

  const hasErrors = report.issues.some((issue) => issue.level === 'error');
  const hasWarnings = report.issues.some((issue) => issue.level === 'warn');
  if (strict && (hasErrors || hasWarnings)) {
    return 1;
  }
  return 0;
}

process.exit(main());
