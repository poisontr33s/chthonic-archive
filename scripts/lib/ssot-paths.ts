#!/usr/bin/env bun

/**
 * SSOT Cascade Bridge — TypeScript
 *
 * Mirrors the Python cascade (ssot_manifest.py → ssot_paths.py) for TS consumers.
 * All SSOT path references in TypeScript MUST import from here, never hardcode.
 *
 * @SID: BRIDGE_SSOT_PATHS_TS_V1
 * @Type: INFRASTRUCTURE
 * @Spectrum: WHITE
 * @Zone: THE GARDEN
 *
 * If the SSOT filename changes, update THIS file (and the Python manifest).
 * Downstream TS consumers resolve through these exports.
 */

import { existsSync } from "fs";
import { resolve as pathResolve } from "path";

/** The frozen monolithic SSOT. */
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
  which: "holder" | "pointer" | "proto" = "pointer",
): string {
  const map = { holder: SSOT_HOLDER, pointer: SSOT_POINTER, proto: SSOT_PROTO };
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
