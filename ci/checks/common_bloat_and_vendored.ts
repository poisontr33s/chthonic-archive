/**
 * ci/checks/common_bloat_and_vendored.ts
 *
 * Centralized list of directories and path fragments that should be excluded
 * from CI scans (link-audit, homepath-portability, etc.) to minimize noise
 * from standard build artifacts and third-party dependencies.
 */

export const COMMON_SKIP_DIRS = [
  "debugging_data/",
  "manifest/",
  "node_modules/",
  "target/",
  ".git/",
  ".venv/",
  "__pycache__/",
  ".vs/",
  ".ruff_cache/",
  ".pytest_cache/",
  ".cache/",
];

export const COMMON_EXEMPT_PARTS = [
  "/cache/",
  "\\cache\\",
  "/manifest/",
  "\\manifest\\",
  "/node_modules/",
  "\\node_modules\\",
  "/target/",
  "\\target\\",
  // Audit-tool captures that happen to live in .vscode/ rather than manifest/ -
  // same output class (a resolved path recorded at scan time), not source.
  ".vscode/audit_",
  ".vscode\\audit_",
];
