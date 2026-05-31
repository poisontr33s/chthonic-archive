#!/usr/bin/env bun

// @SID: BRIDGE_SSOT_PATHS_TS_V1
// @Shabti:        Library Module
// @Shabti-Desc:   SSOT Cascade Bridge for TypeScript — re-exporting from ssot_paths.ts to avoid hardcoding SSOT paths in TS modules.
// @Type:          INFRASTRUCTURE
// @Spectrum:      WHITE
// @Zone:          THE GARDEN
// @Ogdoad:        (Standalone)

/**
* SSOT Cascade Bridge — TypeScript
*
* Mirrors the Python cascade (ssot_manifest.py → ssot_paths.py) for TS consumers.
* All SSOT path references in TypeScript MUST import from here, never hardcode.
 *
 * Canonical source: scripts/lib/ssot-paths.ts
 *
 * If the SSOT filename changes, update THIS file (and the Python manifest).
 * Downstream TS consumers resolve through these exports.
 */

import { existsSync } from "fs";
import { resolve as pathResolve } from "path";

/**
 * The primary, file-first-authority SSOT canon — the frozen monolithic
 * Codex-Brahmanica-Perfectus from which every active instruction file is
 * derived. This is THE single anchor every surface resolves to
 * (canonized in place 2026-05-31). It is the artifact that created everything
 * else; surfaces that reference "the SSOT" mean THIS file.
 */
export const SSOT_CANON = ".chthonic/SSOT.md" as const;

/**
 * Generated downstream MIRROR of SSOT_CANON, kept under this clunky-but-stable
 * name so existing repo scripts that reference it do not break (no-delete).
 * NOT the primary source — resolve SSOT_CANON first; fall back here only if the
 * canon is absent.
 */
export const SSOT_HOLDER = ".github/copilot-instructions.archive.md" as const;

/** The 85-line routing pointer. */
export const SSOT_POINTER = ".github/copilot-instructions.md" as const;

/** The historizing fork (pre-freeze snapshot). */
export const SSOT_PROTO = ".github/copilot-instructions-copy.md" as const;

/**
 * Resolve an SSOT path relative to a given root directory.
 */
export function resolveSsotPath(
  root: string,
  which: "canon" | "holder" | "pointer" | "proto" = "pointer",
): string {
  const map = { canon: SSOT_CANON, holder: SSOT_HOLDER, pointer: SSOT_POINTER, proto: SSOT_PROTO };
  // Use platform-agnostic join
  return `${root}/${map[which]}`.replace(/\\/g, "/");
}

/**
 * Assert the SSOT holder exists at the expected path.
 * Throws with a descriptive message if absent.
 */
export function assertSsotExists(root: string): void {
  const holderPath = pathResolve(root, SSOT_HOLDER);
  if (!existsSync(holderPath)) {
    throw new Error(
      `SSOT holder not found at expected path: ${holderPath}\n` +
      `Ensure repository root is correct (got: ${root})`
    );
  }
}
