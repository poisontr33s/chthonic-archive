#!/usr/bin/env bun
// @SID: SCRIPT_COUTURE_GATE_V1
// Purpose: Gate The Extreme Haute Couture Movement 1 against current Insiders,
// substrate injection, extension visual contributions, and packageability.

import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';

type StepResult = {
  name: string;
  command: string[];
  cwd: string;
  exitCode: number;
  durationMs: number;
  stdout: string;
  stderr: string;
};

type CheckResult = {
  name: string;
  ok: boolean;
  detail: string;
};

type PackageJson = {
  engines?: { vscode?: string };
  contributes?: {
    themes?: Array<{ label?: string; path?: string }>;
    iconThemes?: Array<{ id?: string; path?: string }>;
    productIconThemes?: Array<{ id?: string; path?: string }>;
  };
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
};

const repoRoot = path.resolve(import.meta.dir, '..');
const extensionRoot = path.join(repoRoot, 'extensions', 'chthonic-archive');
const manifestDir = path.join(repoRoot, 'manifest');
const reportPath = path.join(manifestDir, 'extreme-haute-couture-movement-1-gate.json');
const decoder = new TextDecoder();

const checks: CheckResult[] = [];
const steps: StepResult[] = [];

const latestStable = await fetchRelease('stable');
const latestInsider = await fetchRelease('insider');
const localInsiders = runStep('code-insiders-version', ['code-insiders', '--version'], repoRoot);
steps.push(localInsiders);

const localInsidersLines = localInsiders.stdout
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter(Boolean);
const localInsidersVersion = localInsidersLines[0] ?? 'unknown';
const localInsidersCommit = localInsidersLines[1] ?? 'unknown';

const packageJsonPath = path.join(extensionRoot, 'package.json');
const extensionPackage = readJson<PackageJson>(packageJsonPath);

addCheck(
  'official-stable-floor',
  extensionPackage.engines?.vscode === `^${latestStable}`,
  `engines.vscode=${extensionPackage.engines?.vscode ?? '(missing)'}, stable=${latestStable}`,
);
addCheck(
  'local-insiders-current',
  localInsidersVersion === latestInsider,
  `local=${localInsidersVersion}, latest=${latestInsider}, commit=${localInsidersCommit}`,
);
addCheck(
  'vscode-types-compatible',
  isVscodeTypesCompatible(extensionPackage.devDependencies?.['@types/vscode'], latestStable),
  `@types/vscode=${extensionPackage.devDependencies?.['@types/vscode'] ?? '(missing)'}, stable=${latestStable}`,
);

const sdkCheck = runStep('root-sdk-catalog-check', ['bun', 'run', 'sdk:check'], repoRoot);
steps.push(sdkCheck);
addCheck('root-sdk-catalog-check', sdkCheck.exitCode === 0, summarizeStep(sdkCheck));

const outdated = runStep('extension-outdated-check', ['bun', 'outdated', '--no-progress'], extensionRoot);
steps.push(outdated);
addCheck(
  'extension-dependencies-latest',
  outdated.exitCode === 0 && !hasOutdatedTable(outdated.stdout),
  hasOutdatedTable(outdated.stdout) ? trimOutput(outdated.stdout, 1200) : 'no outdated package table reported',
);

const substrate = runStep(
  'insiders-substrate-verify',
  [
    'pwsh',
    '-NoProfile',
    '-Command',
    "& './scripts/mica-substrate.ps1' -Verify | ConvertTo-Json -Depth 8",
  ],
  repoRoot,
);
steps.push(substrate);
const substrateJson = safeParseJson<Record<string, unknown>>(substrate.stdout);
addCheck('insiders-substrate-verify', substrate.exitCode === 0 && substrateJson?.Ok === true, summarizeStep(substrate));
addCheck(
  'substrate-targets-current-insiders',
  String(substrateJson?.Version ?? '') === latestInsider,
  `substrateVersion=${String(substrateJson?.Version ?? 'unknown')}, latestInsider=${latestInsider}`,
);

const visualContributionSummary = verifyVisualContributions(extensionPackage);

const kits = runStep('extension-kits-check', ['bun', 'run', 'insiders:kits:check'], extensionRoot);
steps.push(kits);
addCheck('extension-kits-check', kits.exitCode === 0, summarizeStep(kits));

const packaged = runStep('extension-package-insiders', ['bun', 'run', 'insiders:package'], extensionRoot);
steps.push(packaged);
const vsixPath = path.join(extensionRoot, 'chthonic-archive-insiders.vsix');
addCheck(
  'extension-package-insiders',
  packaged.exitCode === 0 && existsSync(vsixPath),
  existsSync(vsixPath)
    ? `vsix=${path.relative(repoRoot, vsixPath)}, bytes=${statSync(vsixPath).size}`
    : summarizeStep(packaged),
);

const extensionHost = runStep('extension-host-e2e', ['bun', 'run', 'test:e2e'], extensionRoot);
steps.push(extensionHost);
addCheck('extension-host-e2e', extensionHost.exitCode === 0, summarizeStep(extensionHost));

const status = checks.every((check) => check.ok) ? 'passed' : 'failed';
const report = {
  schema: 'extreme-haute-couture/movement-1-gate/v1',
  generatedAt: new Date().toISOString(),
  status,
  releases: {
    stable: latestStable,
    insider: latestInsider,
  },
  localInsiders: {
    version: localInsidersVersion,
    commit: localInsidersCommit,
    arch: localInsidersLines[2] ?? 'unknown',
  },
  extension: {
    root: path.relative(repoRoot, extensionRoot),
    enginesVscode: extensionPackage.engines?.vscode ?? null,
    vscodeTypes: extensionPackage.devDependencies?.['@types/vscode'] ?? null,
  },
  substrate: substrateJson,
  visualContributions: visualContributionSummary,
  checks,
  steps: steps.map((step) => ({
    ...step,
    stdout: trimOutput(step.stdout, 4000),
    stderr: trimOutput(step.stderr, 4000),
  })),
};

mkdirSync(manifestDir, { recursive: true });
writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');

for (const check of checks) {
  console.log(`${check.ok ? 'ok' : 'fail'} ${check.name}: ${check.detail}`);
}
console.log(`report: ${path.relative(repoRoot, reportPath)}`);

if (status !== 'passed') {
  process.exit(1);
}

async function fetchRelease(channel: 'stable' | 'insider'): Promise<string> {
  const response = await fetch(`https://update.code.visualstudio.com/api/releases/${channel}`, {
    signal: AbortSignal.timeout(20_000),
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch VS Code ${channel} releases: ${response.status} ${response.statusText}`);
  }
  const releases = await response.json() as unknown;
  if (!Array.isArray(releases) || typeof releases[0] !== 'string') {
    throw new Error(`Unexpected VS Code ${channel} release payload`);
  }
  return releases[0];
}

function verifyVisualContributions(extensionPackageData: PackageJson) {
  const contributes = extensionPackageData.contributes ?? {};
  const themes = contributes.themes ?? [];
  const iconThemes = contributes.iconThemes ?? [];
  const productIconThemes = contributes.productIconThemes ?? [];

  addCheck('color-theme-contributions-present', themes.length > 0, `count=${themes.length}`);
  addCheck('file-icon-theme-contributions-present', iconThemes.length > 0, `count=${iconThemes.length}`);
  addCheck('product-icon-theme-contributions-present', productIconThemes.length > 0, `count=${productIconThemes.length}`);

  const colorThemes = themes.map((theme) => {
    const resolved = resolveContributionPath(theme.path);
    const json = resolved ? readJson<Record<string, unknown>>(resolved) : null;
    const colors = json?.colors;
    const tokenColors = json?.tokenColors;
    const semanticTokenColors = json?.semanticTokenColors;
    const ok = Boolean(
      resolved &&
      existsSync(resolved) &&
      json &&
      (isRecord(colors) || Array.isArray(tokenColors) || isRecord(semanticTokenColors)),
    );
    addCheck(
      `color-theme:${theme.label ?? theme.path ?? '(unnamed)'}`,
      ok,
      resolved ? path.relative(repoRoot, resolved) : '(missing path)',
    );
    return {
      label: theme.label ?? null,
      path: resolved ? path.relative(repoRoot, resolved) : null,
      hasColors: isRecord(colors),
      tokenColorCount: Array.isArray(tokenColors) ? tokenColors.length : 0,
      semanticTokenColorCount: isRecord(semanticTokenColors) ? Object.keys(semanticTokenColors).length : 0,
    };
  });

  const fileIconThemes = iconThemes.map((theme) => {
    const resolved = resolveContributionPath(theme.path);
    const json = resolved ? readJson<Record<string, unknown>>(resolved) : null;
    const iconDefinitions = isRecord(json?.iconDefinitions) ? json.iconDefinitions : {};
    const missingIconPaths = collectMissingIconPaths(resolved, iconDefinitions);
    const ok = Boolean(resolved && existsSync(resolved) && Object.keys(iconDefinitions).length > 0 && missingIconPaths.length === 0);
    addCheck(
      `file-icon-theme:${theme.id ?? theme.path ?? '(unnamed)'}`,
      ok,
      `definitions=${Object.keys(iconDefinitions).length}, missing=${missingIconPaths.length}`,
    );
    return {
      id: theme.id ?? null,
      path: resolved ? path.relative(repoRoot, resolved) : null,
      iconDefinitionCount: Object.keys(iconDefinitions).length,
      missingIconPaths,
    };
  });

  const productIconThemeResults = productIconThemes.map((theme) => {
    const resolved = resolveContributionPath(theme.path);
    const json = resolved ? readJson<Record<string, unknown>>(resolved) : null;
    const iconDefinitions = isRecord(json?.iconDefinitions) ? json.iconDefinitions : {};
    const fonts = Array.isArray(json?.fonts) ? json.fonts : [];
    const missingFonts = collectMissingFonts(resolved, fonts);
    const ok = Boolean(resolved && existsSync(resolved) && Object.keys(iconDefinitions).length > 0 && fonts.length > 0 && missingFonts.length === 0);
    addCheck(
      `product-icon-theme:${theme.id ?? theme.path ?? '(unnamed)'}`,
      ok,
      `definitions=${Object.keys(iconDefinitions).length}, fonts=${fonts.length}, missingFonts=${missingFonts.length}`,
    );
    return {
      id: theme.id ?? null,
      path: resolved ? path.relative(repoRoot, resolved) : null,
      iconDefinitionCount: Object.keys(iconDefinitions).length,
      fontCount: fonts.length,
      missingFonts,
    };
  });

  return {
    colorThemes,
    fileIconThemes,
    productIconThemes: productIconThemeResults,
  };
}

function collectMissingIconPaths(themePath: string | null, iconDefinitions: Record<string, unknown>): string[] {
  if (!themePath) return ['(theme path missing)'];
  const themeDir = path.dirname(themePath);
  const missing: string[] = [];
  for (const [name, value] of Object.entries(iconDefinitions)) {
    if (!isRecord(value) || typeof value.iconPath !== 'string') {
      continue;
    }
    const resolved = path.resolve(themeDir, value.iconPath);
    if (!existsSync(resolved)) {
      missing.push(`${name}:${path.relative(repoRoot, resolved)}`);
    }
  }
  return missing;
}

function collectMissingFonts(themePath: string | null, fonts: unknown[]): string[] {
  if (!themePath) return ['(theme path missing)'];
  const themeDir = path.dirname(themePath);
  const missing: string[] = [];
  for (const [fontIndex, font] of fonts.entries()) {
    if (!isRecord(font) || !Array.isArray(font.src)) {
      missing.push(`font[${fontIndex}]:missing-src`);
      continue;
    }
    for (const [srcIndex, source] of font.src.entries()) {
      if (!isRecord(source) || typeof source.path !== 'string') {
        missing.push(`font[${fontIndex}].src[${srcIndex}]:missing-path`);
        continue;
      }
      const resolved = path.resolve(themeDir, source.path);
      if (!existsSync(resolved)) {
        missing.push(`font[${fontIndex}].src[${srcIndex}]:${path.relative(repoRoot, resolved)}`);
      }
    }
  }
  return missing;
}

function resolveContributionPath(value: string | undefined): string | null {
  if (!value) return null;
  return path.resolve(extensionRoot, value);
}

function isVscodeTypesCompatible(range: string | undefined, stable: string): boolean {
  if (!range) return false;
  return compareVersions(normalizeVersion(range), stable) <= 0;
}

function normalizeVersion(value: string): string {
  return value.replace(/^[~^<>=\s]+/, '').split('-')[0] ?? value;
}

function compareVersions(left: string, right: string): number {
  const l = left.split('.').map((part) => Number.parseInt(part, 10));
  const r = right.split('.').map((part) => Number.parseInt(part, 10));
  for (let index = 0; index < Math.max(l.length, r.length); index += 1) {
    const delta = (l[index] ?? 0) - (r[index] ?? 0);
    if (delta !== 0) return delta;
  }
  return 0;
}

function hasOutdatedTable(stdout: string): boolean {
  return stdout
    .split(/\r?\n/)
    .some((line) => /^\|\s*Package\s+\|/.test(line.trim()));
}

function runStep(name: string, command: string[], cwd: string): StepResult {
  const startedAt = Date.now();
  const result = Bun.spawnSync({
    cmd: command,
    cwd,
    stdout: 'pipe',
    stderr: 'pipe',
    windowsHide: true,
  });
  return {
    name,
    command,
    cwd,
    exitCode: result.exitCode,
    durationMs: Date.now() - startedAt,
    stdout: decoder.decode(result.stdout),
    stderr: decoder.decode(result.stderr),
  };
}

function summarizeStep(step: StepResult): string {
  const detail = step.exitCode === 0 ? step.stdout : `${step.stdout}\n${step.stderr}`;
  return `exit=${step.exitCode}; ${trimOutput(detail.trim(), 1200)}`;
}

function trimOutput(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}...<truncated>`;
}

function readJson<T>(filePath: string): T {
  return JSON.parse(readFileSync(filePath, 'utf8')) as T;
}

function safeParseJson<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

function addCheck(name: string, ok: boolean, detail: string): void {
  checks.push({ name, ok, detail });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
