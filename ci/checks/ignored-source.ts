#!/usr/bin/env bun
// @SID: CI_CHECK_IGNORED_SOURCE_V1

/**
 * Detect files hidden by the repo's allowlist .gitignore.
 *
 * This repo intentionally starts .gitignore with "*" to protect against
 * accidental binary/model commits. The failure mode is that new files in
 * new subdirectories can become invisible to git until a matching !rule is
 * added. This check reports any non-noise file in a managed root that's
 * been swallowed by the allowlist.
 *
 * Filer-agnostic: we do NOT gatekeep by file extension. Locality (managed
 * root) + a deny-list of obvious noise (build outputs, lockfiles, binaries,
 * images, fonts) is enough. Surface ambiguous cases for human triage rather
 * than pre-filter by a source-shape allowlist that quietly omits whichever
 * polyglot lane was added last.
 */

import { spawnSync } from "child_process";
import { statSync } from "fs";
import { relative, resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const REPORT = process.argv.includes("--report");
const CONVENTION_DOC = "docs/reference/GITIGNORE_ALLOWLIST_DISCIPLINE.md";

// Size-as-primary-signal threshold. DR-validated 2026-05-18 (see
// `reference_dr_size_based_exclusion.md` in Claude memory): comfortably above
// the double-Pareto tail-start for source files (~1 KB across C/C++/Java/Py),
// below the empirical compiled-binary floor (~200 KB for trivial C++ exe),
// well below Git's recommended single-object size (1 MB) and GitHub's 50 MB
// warning. Local probe (n=31, 2026-05-18) confirms it cleanly absorbs the
// real binary noise (.vsix 100-407 KB, .node 334 KB) without false-positives
// on hand-written source.
const SIZE_THRESHOLD_BYTES = 262144;

const MANAGED_ROOTS = [
  "ci/",
  "scripts/",
  "extensions/",
  "apps/chthonic-next/",
  "apps/chthonic-tensor-bridge/",
  "apps/flux-engine-forge/",
  "apps/flux-satellite/",
  "mcp/",
  "mas_mcp/",
  "src/",
  "native/",
];

const NOISE_PARTS = new Set([
  ".git",
  ".venv",
  "venv",
  "node_modules",
  "__pycache__",
  ".pytest_cache",
  ".ruff_cache",
  ".cache",
  ".vscode-test",
  ".next",
  ".turbo",
  "coverage",
  "scratch",
  "engines",
  "logs",
  "data",
  "amendments",
  "vcpkg_installed",
  "vcpkg-overlay-ports",
  "target",
  "build",
  "Release",
  "Debug",
  "dist",
  "obj",
  "bin",
  ".chthonic",
  "vendor",
  "site-packages",
]);

// Small-binary tail: suffixes whose files are typically BELOW the size
// threshold, so size alone won't catch them. Always-large suffixes
// (.safetensors/.pt/.pth/.ckpt/.onnx/.npy/.npz/.exe/.dll/.node) are absorbed
// by the size predicate and were trimmed here — adding them back would only
// matter if a structurally-large format ever produced a sub-256KB instance,
// which would be a surprise worth surfacing anyway.
const NOISE_SUFFIXES = [
  ".vsix",          // smallest observed in this repo: 99.7 KB
  ".lock",          // bun.lock etc., up to 171 KB observed
  ".pyc",
  ".pyo",
  ".pyd",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".webp",
  ".ico",
  ".woff",
  ".woff2",
  ".ttf",
  ".sqlite",        // observed 128 KB in scripts/test_epistemograph.sqlite
  ".sqlite3",
  ".db",
  ".log",
  ".tsbuildinfo",   // observed 145 KB
  "next-env.d.ts",
];

interface Finding {
  path: string;
  reason: string;
}

function gitIgnoredOthers(): string[] {
  const result = spawnSync(
    "git",
    [
      "ls-files",
      "--others",
      "--ignored",
      "--exclude-standard",
      "--directory",
      "--no-empty-directory",
      "-z",
      "--",
      ...MANAGED_ROOTS,
    ],
    {
      cwd: REPO_ROOT,
      encoding: "buffer",
      maxBuffer: 128 * 1024 * 1024,
    },
  );

  if (result.status !== 0) {
    const stderr = result.stderr?.toString("utf8") ?? "";
    throw new Error(`git ignored scan failed: ${stderr.trim()}`);
  }

  return result.stdout
    .toString("utf8")
    .split("\0")
    .filter(Boolean)
    .map(normalizePath);
}

function normalizePath(path: string): string {
  return path.replace(/\\/g, "/");
}

function getFileSize(path: string): number {
  try {
    return statSync(resolve(REPO_ROOT, path)).size;
  } catch {
    // File disappeared between git-ls and stat (e.g., concurrent build cleanup).
    // Treat as size-zero so it falls through to the other noise predicates.
    return 0;
  }
}

function isNoise(path: string): boolean {
  // Size first: cheapest filter that absorbs the most. Anything above the
  // threshold is presumed non-source noise regardless of extension. This is
  // the "filer-agnostic" core — new binary formats are caught automatically
  // without enumeration updates.
  if (getFileSize(path) >= SIZE_THRESHOLD_BYTES) {
    return true;
  }
  const lower = path.toLowerCase();
  if (NOISE_SUFFIXES.some((suffix) => lower.endsWith(suffix))) {
    return true;
  }
  if (lower.includes("/media/wasm/")) {
    return true;
  }
  if (lower.includes("/.deprecated/") || lower.endsWith(".meta.json")) {
    return true;
  }
  // Deliberate disabled-source quarantine. These files are preserved on disk
  // while their active lane is removed from the extension build.
  if (lower.endsWith(".unused.off") || lower.includes(".unused.off/")) {
    return true;
  }
  // scripts/_foo.* — underscore-prefix is the temp convention regardless of extension.
  if (/^scripts\/_[^/]+$/i.test(path)) {
    return true;
  }
  // IDE / terminal tool capture artifacts: "<Tool> tool (input|output) (xxxxxx).txt".
  if (/\btool (input|output) \([a-z0-9]+\)\.txt$/i.test(path)) {
    return true;
  }
  return normalizePath(path)
    .split("/")
    .some((part) => NOISE_PARTS.has(part) || part.startsWith(".venv"));
}

function isInManagedRoot(path: string): boolean {
  return MANAGED_ROOTS.some((root) => path.startsWith(root));
}

function buildFinding(path: string): Finding | null {
  if (isNoise(path)) return null;
  if (!isInManagedRoot(path)) return null;
  return {
    path,
    reason: "file in managed root is ignored by .gitignore",
  };
}

function renderHuman(findings: Finding[]): void {
  if (findings.length === 0) {
    console.log("[ignored-source] ok: no ignored files in managed roots");
    return;
  }

  console.error(`[ignored-source] found ${findings.length} ignored file(s) in managed roots:`);
  for (const finding of findings.slice(0, 80)) {
    console.error(`  ${finding.path}`);
    console.error(`    ${finding.reason}`);
  }
  if (findings.length > 80) {
    console.error(`  ... ${findings.length - 80} more`);
  }
  console.error("");
  console.error("Fix: add a narrow !rule to .gitignore for the new source lane, or move the file into an already-allowed source lane.");
  console.error("Inspect one file with: git check-ignore -v <path>");
  console.error(`Convention: ${CONVENTION_DOC}`);
}

try {
  const findings = gitIgnoredOthers()
    .map(buildFinding)
    .filter((finding): finding is Finding => finding !== null)
    .sort((a, b) => a.path.localeCompare(b.path));

  if (REPORT) {
    process.stdout.write(JSON.stringify({
      repoRoot: relative(process.cwd(), REPO_ROOT) || ".",
      count: findings.length,
      findings,
    }, null, 2) + "\n");
  } else {
    renderHuman(findings);
  }

  process.exit(findings.length > 0 ? 1 : 0);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`[ignored-source] failed: ${message}`);
  process.exit(1);
}
