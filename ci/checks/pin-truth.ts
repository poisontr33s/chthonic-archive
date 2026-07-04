#!/usr/bin/env bun
// @SID: CI_CHECK_PIN_TRUTH_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/pin-truth.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Truth membrane: version claims vs pins vs floating lanes)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/pin-truth.ts — version declaration truth membrane.
 *
 * This is NOT a "latest version" checker. Network/current-upstream truth is
 * time-bearing and belongs in a conductor-timed research pass. This check
 * guards the local law surface: files that declare tool/dependency versions,
 * floating channels, and comments that claim "latest/current/stable" while
 * spelling concrete pins.
 *
 * Root incident (2026-07-04): host preflight said green/yellow while the
 * underlying Solana/Agave lane mixed a usable CLI, a broken installer, a
 * missing legacy installer, stale docs, and several distinct upstream release
 * bands. Same disease in dependency/tool files: "latest" and "stable" are
 * different truth types from "v3.1.10" or "1.96.0". A resolver can float, a
 * manifest can range, and a lockfile can pin; collapsing those categories
 * creates false positives and false clearances.
 *
 * Exit semantics:
 *   --staged  STRICT on staged in-scope files only when a contradiction is
 *             introduced (exit 1).
 *   default   Advisory scan of all tracked in-scope files (exit 0).
 *
 * Usage:
 *   bun run ci/checks/pin-truth.ts
 *   bun run ci/checks/pin-truth.ts --staged
 *   bun run ci/checks/pin-truth.ts --report
 *   bun run ci/checks/pin-truth.ts --locks
 *   bun run ci/checks/pin-truth.ts --history
 */

import { spawnSync } from "child_process";
import { readFileSync } from "fs";
import path from "path";

const STAGED = process.argv.includes("--staged");
const REPORT = process.argv.includes("--report");
const SHOW_LOCKS = process.argv.includes("--locks") || process.argv.includes("--locked");
const SHOW_HISTORY = process.argv.includes("--history") || process.argv.includes("--provenance");
const REPO_ROOT = path.resolve(import.meta.dir, "../..");

type SpecKind = "exact-pin" | "major-pin" | "range" | "floating" | "local" | "unknown";
type Surface = "package-json" | "cargo-toml" | "toml" | "dot-version" | "go-mod" | "requirements";
type LockManager = "cargo" | "bun" | "uv" | "unknown";

type PinRecord = {
  file: string;
  line: number;
  surface: Surface;
  name: string;
  spec: string;
  kind: SpecKind;
};

type Contradiction = {
  file: string;
  line: number;
  kind: "latest-claim-with-pin" | "floating-word-with-exact-version";
  claim: string;
  observed: string;
};

type LockRecord = {
  file: string;
  line: number;
  manager: LockManager;
  name: string;
  version: string;
};

type GitProvenance = {
  file: string;
  commit: string;
  committedAt: string;
  subject: string;
};

const IN_SCOPE_BASENAMES = new Set([
  "package.json",
  "Cargo.toml",
  "pyproject.toml",
  "uv.toml",
  "bunfig.toml",
  "mise.toml",
  ".mise.toml",
  "rust-toolchain.toml",
  ".tool-versions",
  ".python-version",
  ".ruby-version",
  ".node-version",
  "go.mod",
]);

const LOCK_BASENAMES = new Set([
  "Cargo.lock",
  "bun.lock",
  "bun.lockb",
  "package-lock.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "uv.lock",
]);

const FLOATING_CLAIM_WORDS = /\b(latest|current|floating|unpinned|unpin|never a legacy pin|track latest|tracks latest)\b/i;
const EXACT_VERSION = /\bv?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?\b/;
const STRING_ASSIGNMENT = /^\s*([A-Za-z0-9_.-]+)\s*=\s*["']([^"']+)["']/;

function gitFiles(args: string[]): string[] {
  const result = spawnSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" });
  return (result.stdout ?? "").split(/\r?\n/).filter(Boolean);
}

function gitText(args: string[]): string {
  const result = spawnSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" });
  return (result.stdout ?? "").trim();
}

function rel(pathLike: string): string {
  return pathLike.replace(/\\/g, "/");
}

function basename(file: string): string {
  return rel(file).split("/").pop() ?? file;
}

function isRequirements(file: string): boolean {
  const base = basename(file).toLowerCase();
  return base === "requirements.txt" || /^requirements[-_.].+\.txt$/.test(base);
}

function inScope(file: string): boolean {
  const base = basename(file);
  if (LOCK_BASENAMES.has(base)) return false;
  return IN_SCOPE_BASENAMES.has(base) || isRequirements(file);
}

function isLockFile(file: string): boolean {
  return LOCK_BASENAMES.has(basename(file));
}

function collectTrackedSurface(): string[] {
  return STAGED
    ? gitFiles(["diff", "--cached", "--name-only", "--diff-filter=ACM"])
    : gitFiles(["ls-files"]);
}

function readLines(file: string): string[] {
  if (STAGED) {
    const staged = spawnSync("git", ["show", `:${rel(file)}`], {
      cwd: REPO_ROOT,
      encoding: "utf8",
      maxBuffer: 50 * 1024 * 1024,
    });
    if ((staged.status ?? 1) === 0) {
      return (staged.stdout ?? "").replace(/^\uFEFF/, "").split(/\r?\n/);
    }
  }
  try {
    return readFileSync(path.resolve(REPO_ROOT, file), "utf8").replace(/^\uFEFF/, "").split(/\r?\n/);
  } catch {
    return [];
  }
}

function classifySpec(spec: string): SpecKind {
  const s = spec.trim();
  if (/^(latest|current|stable|edge|nightly|beta|canary)$/i.test(s)) return "floating";
  if (/^(workspace:|file:|link:|path:|\.\.?[\\/])/.test(s)) return "local";
  if (/^[~^<>=*]/.test(s) || /\s+\|\|\s+/.test(s) || /[<>]=?/.test(s)) return "range";
  if (/^\d+$/.test(s) || /^v?\d+$/i.test(s)) return "major-pin";
  if (/^v?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?$/i.test(s)) return "exact-pin";
  return "unknown";
}

function surfaceFor(file: string): Surface {
  const base = basename(file);
  if (base === "package.json") return "package-json";
  if (base === "Cargo.toml") return "cargo-toml";
  if (base === "go.mod") return "go-mod";
  if (isRequirements(file)) return "requirements";
  if (base.startsWith(".")) return "dot-version";
  return "toml";
}

function findJsonLine(lines: string[], key: string): number {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`"${escaped}"\\s*:`);
  const idx = lines.findIndex((line) => re.test(line));
  return idx >= 0 ? idx + 1 : 1;
}

function scanPackageJson(file: string, lines: string[]): PinRecord[] {
  try {
    const parsed = JSON.parse(lines.join("\n")) as Record<string, unknown>;
    const records: PinRecord[] = [];
    const sections = ["engines", "dependencies", "devDependencies", "optionalDependencies", "peerDependencies"];
    for (const section of sections) {
      const table = parsed[section];
      if (!table || typeof table !== "object" || Array.isArray(table)) continue;
      for (const [name, value] of Object.entries(table as Record<string, unknown>)) {
        if (typeof value !== "string") continue;
        records.push({
          file,
          line: findJsonLine(lines, name),
          surface: "package-json",
          name: `${section}.${name}`,
          spec: value,
          kind: classifySpec(value),
        });
      }
    }
    return records;
  } catch {
    return [];
  }
}

function scanCargoOrToml(file: string, lines: string[]): PinRecord[] {
  const surface = surfaceFor(file);
  const records: PinRecord[] = [];
  for (let i = 0; i < lines.length; i += 1) {
    const raw = lines[i];
    const code = raw.split("#", 1)[0];
    const m = code.match(STRING_ASSIGNMENT);
    if (!m) continue;
    const name = m[1];
    const spec = m[2];
    if (!/[0-9]|latest|stable|current|edge|nightly|beta|canary/i.test(spec)) continue;
    records.push({
      file,
      line: i + 1,
      surface,
      name,
      spec,
      kind: classifySpec(spec),
    });
  }
  return records;
}

function scanDotVersion(file: string, lines: string[]): PinRecord[] {
  const first = lines.map((line) => line.trim()).find((line) => line && !line.startsWith("#"));
  if (!first) return [];
  return [{
    file,
    line: lines.findIndex((line) => line.trim() === first) + 1,
    surface: "dot-version",
    name: basename(file),
    spec: first,
    kind: classifySpec(first),
  }];
}

function scanGoMod(file: string, lines: string[]): PinRecord[] {
  const records: PinRecord[] = [];
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trim();
    const m = line.match(/^(go|toolchain)\s+(\S+)/);
    if (!m) continue;
    records.push({
      file,
      line: i + 1,
      surface: "go-mod",
      name: m[1],
      spec: m[2],
      kind: classifySpec(m[2].replace(/^go/, "")),
    });
  }
  return records;
}

function scanRequirements(file: string, lines: string[]): PinRecord[] {
  const records: PinRecord[] = [];
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trim();
    if (!line || line.startsWith("#")) continue;
    const m = line.match(/^([A-Za-z0-9_.-]+)\s*(==|~=|>=|<=|>|<)\s*([^;\s]+)/);
    if (!m) continue;
    records.push({
      file,
      line: i + 1,
      surface: "requirements",
      name: m[1],
      spec: `${m[2]}${m[3]}`,
      kind: m[2] === "==" ? "exact-pin" : "range",
    });
  }
  return records;
}

function lockManagerFor(file: string): LockManager {
  const base = basename(file);
  if (base === "Cargo.lock") return "cargo";
  if (base === "bun.lock" || base === "bun.lockb") return "bun";
  if (base === "uv.lock") return "uv";
  return "unknown";
}

function scanTomlPackageLock(file: string, lines: string[], manager: LockManager): LockRecord[] {
  const records: LockRecord[] = [];
  let packageStart = 0;
  let name: string | null = null;
  let version: string | null = null;

  function flush(): void {
    if (!name || !version) return;
    records.push({
      file,
      line: packageStart || 1,
      manager,
      name,
      version,
    });
  }

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (/^\s*\[\[package\]\]\s*$/.test(line)) {
      flush();
      packageStart = i + 1;
      name = null;
      version = null;
      continue;
    }
    const nameMatch = line.match(/^\s*name\s*=\s*"([^"]+)"/);
    if (nameMatch) {
      name = nameMatch[1];
      continue;
    }
    const versionMatch = line.match(/^\s*version\s*=\s*"([^"]+)"/);
    if (versionMatch) {
      version = versionMatch[1];
    }
  }
  flush();
  return records;
}

function scanBunLock(file: string, lines: string[]): LockRecord[] {
  const records: LockRecord[] = [];
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const m = line.match(/^\s*"([^"]+)":\s*\[\s*"([^"]+)"/);
    if (!m) continue;
    const name = m[1];
    const resolved = m[2];
    const prefix = `${name}@`;
    const version = resolved.startsWith(prefix)
      ? resolved.slice(prefix.length)
      : resolved.slice(resolved.lastIndexOf("@") + 1);
    if (!version || version === resolved || !EXACT_VERSION.test(version)) continue;
    records.push({
      file,
      line: i + 1,
      manager: "bun",
      name,
      version,
    });
  }
  return records;
}

function scanLockRecords(file: string, lines: string[]): LockRecord[] {
  const manager = lockManagerFor(file);
  if (manager === "cargo" || manager === "uv") {
    return scanTomlPackageLock(file, lines, manager);
  }
  if (manager === "bun") {
    return scanBunLock(file, lines);
  }
  return [];
}

function scanRecords(file: string, lines: string[]): PinRecord[] {
  const base = basename(file);
  if (base === "package.json") return scanPackageJson(file, lines);
  if (base === "go.mod") return scanGoMod(file, lines);
  if (isRequirements(file)) return scanRequirements(file, lines);
  if (base.startsWith(".") && base.endsWith("-version")) return scanDotVersion(file, lines);
  return scanCargoOrToml(file, lines);
}

function scanContradictions(file: string, lines: string[]): Contradiction[] {
  const contradictions: Contradiction[] = [];
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const hasFloatingClaim =
      FLOATING_CLAIM_WORDS.test(line) ||
      /\blatest\s+stable\b/i.test(line) ||
      /\bstable\s+latest\b/i.test(line);
    if (!hasFloatingClaim || !EXACT_VERSION.test(line)) continue;
    const lower = line.toLowerCase();
    // Allow dated provenance comments. A date next to "latest" is not itself a
    // tool pin; it is often the audit timestamp.
    if (/\b20\d\d-\d\d-\d\d\b/.test(line) && !/v?\d+\.\d+/.test(line.replace(/\b20\d\d-\d\d-\d\d\b/g, ""))) {
      continue;
    }
    const kind = /latest|current/.test(lower)
      ? "latest-claim-with-pin"
      : "floating-word-with-exact-version";
    contradictions.push({
      file,
      line: i + 1,
      kind,
      claim: line.trim(),
      observed: "floating/version-language and concrete version literal share one line",
    });
  }
  return contradictions;
}

function gitProvenance(file: string): GitProvenance | null {
  const out = gitText(["log", "-1", "--format=%cI%x09%h%x09%s", "--", file]);
  if (!out) return null;
  const [committedAt = "", commit = "", ...subjectParts] = out.split("\t");
  return {
    file,
    commit,
    committedAt,
    subject: subjectParts.join("\t"),
  };
}

function uniqueFiles(recordsToTrace: Array<{ file: string }>): string[] {
  return [...new Set(recordsToTrace.map((record) => record.file))].sort();
}

const trackedSurface = collectTrackedSurface();
const files = trackedSurface.filter(inScope);
const lockFiles = trackedSurface.filter(isLockFile);
const records: PinRecord[] = [];
const lockRecords: LockRecord[] = [];
const contradictions: Contradiction[] = [];

for (const file of files) {
  const lines = readLines(file);
  records.push(...scanRecords(file, lines));
  contradictions.push(...scanContradictions(file, lines));
}

for (const file of lockFiles) {
  lockRecords.push(...scanLockRecords(file, readLines(file)));
}

const provenanceTargets = SHOW_HISTORY
  ? [...new Set([...files, ...lockFiles])].sort()
  : STAGED
    ? uniqueFiles(contradictions)
    : [];
const provenance = provenanceTargets
  .map(gitProvenance)
  .filter((entry): entry is GitProvenance => Boolean(entry));

const counts = records.reduce<Record<SpecKind, number>>((acc, record) => {
  acc[record.kind] = (acc[record.kind] ?? 0) + 1;
  return acc;
}, {
  "exact-pin": 0,
  "major-pin": 0,
  range: 0,
  floating: 0,
  local: 0,
  unknown: 0,
});

const lockCounts = lockRecords.reduce<Record<LockManager, number>>((acc, record) => {
  acc[record.manager] = (acc[record.manager] ?? 0) + 1;
  return acc;
}, {
  cargo: 0,
  bun: 0,
  uv: 0,
  unknown: 0,
});

if (REPORT) {
  process.stdout.write(JSON.stringify({
    mode: STAGED ? "staged" : "advisory",
    scannedFiles: files.length,
    lockFiles: lockFiles.length,
    counts,
    lockCounts,
    contradictions,
    provenance,
    records,
    lockRecords,
  }, null, 2) + "\n");
  process.exit(STAGED && contradictions.length > 0 ? 1 : 0);
}

console.log(
  `[pin-truth] ℹ ${files.length} manifest/config file(s); ` +
  `exact=${counts["exact-pin"]} major=${counts["major-pin"]} range=${counts.range} ` +
  `floating=${counts.floating} local=${counts.local} unknown=${counts.unknown}`
);
console.log(
  `[pin-truth] ℹ ${lockFiles.length} lockfile(s); ` +
  `locked=${lockRecords.length} [cargo=${lockCounts.cargo} bun=${lockCounts.bun} uv=${lockCounts.uv}]`
);

if (SHOW_LOCKS) {
  const byFile = new Map<string, LockRecord[]>();
  for (const record of lockRecords) {
    const existing = byFile.get(record.file) ?? [];
    existing.push(record);
    byFile.set(record.file, existing);
  }
  for (const file of lockFiles) {
    const locked = byFile.get(file) ?? [];
    console.log(`[pin-truth] lock ${file} (${locked.length})`);
    for (const record of locked.slice(0, 20)) {
      console.log(`  ${record.name}@${record.version}`);
    }
    if (locked.length > 20) {
      console.log(`  ... +${locked.length - 20} more`);
    }
  }
}

if (provenance.length > 0) {
  const label = SHOW_HISTORY ? "history" : "staged-history";
  console.log(`[pin-truth] ${label} (${provenance.length})`);
  for (const p of provenance.slice(0, SHOW_HISTORY ? 40 : provenance.length)) {
    console.log(`  ${p.file} | ${p.committedAt} | ${p.commit} | ${p.subject}`);
  }
  if (SHOW_HISTORY && provenance.length > 40) {
    console.log(`  ... +${provenance.length - 40} more`);
  }
}

function problemLine(message: string): void {
  if (STAGED) {
    console.error(message);
  } else {
    console.log(message);
  }
}

if (contradictions.length > 0) {
  const verb = STAGED ? "✗" : "⚠";
  problemLine(`[pin-truth] ${verb} ${contradictions.length} version-claim contradiction(s):`);
  for (const c of contradictions) {
    problemLine(`  ${c.file}:${c.line} [${c.kind}] ${c.claim}`);
  }
  problemLine(
    "  Fix: separate the local declaration type from live-latest claims. " +
    "Use words like pinned/range/floating, or move live upstream facts into a dated source ledger."
  );
} else {
  console.log("[pin-truth] ✓ no local version-claim contradictions found");
}

process.exit(STAGED && contradictions.length > 0 ? 1 : 0);
