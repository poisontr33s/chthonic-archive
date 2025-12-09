// ═══════════════════════════════════════════════════════════════════════════════
// 🧬 MAS-MCP Dashboard - SSOT Handler
// Cryptographic binding to Single Source of Truth
// Implements Section XIV.3 of the Codex Brahmanica Perfectus
// ═══════════════════════════════════════════════════════════════════════════════

import { join, resolve } from "node:path";
import { createHash } from "node:crypto";

/** Default SSOT path relative to repository root */
export const SSOT_DEFAULT_PATH = ".github/copilot-instructions.md";

/**
 * Find repository root by walking up from current location.
 */
function findRepoRoot(): string | null {
  let current = resolve(import.meta.dir, "..", "..");  // Start from mas_mcp/frontend
  const root = process.platform === "win32" ? current.split(":")[0] + ":\\" : "/";
  
  while (current !== root) {
    if (Bun.file(join(current, ".git")).size) {
      return current;
    }
    current = resolve(current, "..");
  }
  
  // Check if .git exists (may be file for worktrees)
  try {
    const gitPath = join(current, ".git");
    Bun.file(gitPath);
    return current;
  } catch {
    return null;
  }
}

/**
 * Resolve the absolute path to the SSOT file.
 * 
 * Priority:
 * 1. SSOT_PATH environment variable (if set)
 * 2. Relative to detected repository root
 */
export function getSSOTPath(): string {
  // Check environment variable first
  const envPath = process.env.SSOT_PATH;
  if (envPath) {
    return envPath;
  }
  
  // Find repository root
  const repoRoot = findRepoRoot();
  if (!repoRoot) {
    throw new Error(
      `Cannot locate repository root. Set SSOT_PATH env var or ensure ` +
      `.git exists in parent directories.`
    );
  }
  
  return join(repoRoot, SSOT_DEFAULT_PATH);
}

/**
 * Canonicalize text for consistent hashing across platforms.
 * 
 * Per Section XIV.3 (SSOT-VP):
 * 1. Convert CRLF and CR to LF
 * 2. Strip trailing whitespace from each line  
 * 3. Apply Unicode NFC normalization
 * 4. Strip leading/trailing whitespace from entire document
 */
export function canonicalizeText(text: string): string {
  // Step 1: Normalize line endings
  let result = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  
  // Step 2: Strip trailing whitespace from each line
  const lines = result.split('\n').map(line => line.trimEnd());
  result = lines.join('\n');
  
  // Step 3: Unicode NFC normalization
  result = result.normalize('NFC');
  
  // Step 4: Strip document-level whitespace
  result = result.trim();
  
  return result;
}

/**
 * Compute SHA-256 hash of the canonical SSOT content.
 */
export async function computeSSOTHash(ssotPath?: string): Promise<string> {
  const path = ssotPath ?? getSSOTPath();
  const file = Bun.file(path);
  
  if (!await file.exists()) {
    throw new Error(`SSOT file not found: ${path}`);
  }
  
  const content = await file.text();
  const canonical = canonicalizeText(content);
  
  const hash = createHash('sha256');
  hash.update(canonical, 'utf8');
  return hash.digest('hex');
}

/**
 * Verify that SSOT content has not drifted since session start.
 * 
 * Per Section XIV.3: Bookend Verification
 */
export async function verifyBookend(
  hashStart: string,
  ssotPath?: string
): Promise<{ isConsistent: boolean; hashEnd: string }> {
  const hashEnd = await computeSSOTHash(ssotPath);
  return {
    isConsistent: hashStart === hashEnd,
    hashEnd,
  };
}

/**
 * Get SSOT metadata including path, size, and current hash.
 */
export async function getSSOTMetadata(): Promise<{
  path: string;
  size: number;
  hash: string;
  hashShort: string;
  timestamp: string;
}> {
  const path = getSSOTPath();
  const file = Bun.file(path);
  
  if (!await file.exists()) {
    throw new Error(`SSOT file not found: ${path}`);
  }
  
  const hash = await computeSSOTHash(path);
  
  return {
    path,
    size: file.size,
    hash,
    hashShort: hash.substring(0, 16),
    timestamp: new Date().toISOString(),
  };
}
