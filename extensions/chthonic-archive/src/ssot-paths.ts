// @SID: EXT_SSOT_PATHS_V1
/**
 * SSOT Cascade Bridge — Extension-local mirror
 *
 * Canonical source: scripts/lib/ssot-paths.ts
 * This file mirrors the SSOT path constants for the VS Code extension build context.
 * If the SSOT filename changes, update the canonical source first, then sync here.
 */

/** The frozen monolithic SSOT — 9208-line archive. */
export const SSOT_HOLDER = ".github/copilot-instructions.archive.md";

/** The 85-line routing pointer. */
export const SSOT_POINTER = ".github/copilot-instructions.md";

/** The historizing fork (pre-freeze snapshot). */
export const SSOT_PROTO = ".github/copilot-instructions-copy.md";
