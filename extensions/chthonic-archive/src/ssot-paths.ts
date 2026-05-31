// @SID: EXT_SSOT_PATHS_V1
/**
 * SSOT Cascade Bridge — Extension-local mirror
 *
 * Canonical source: scripts/lib/ssot-paths.ts
 * This file mirrors the SSOT path constants for the VS Code extension build context.
 * If the SSOT filename changes, update the canonical source first, then sync here.
 */

/**
 * Primary file-first-authority SSOT canon — the frozen monolithic
 * Codex-Brahmanica-Perfectus, the artifact every active instruction file
 * derives from. THE single anchor all surfaces resolve to (canonized in place
 * 2026-05-31). Mirror of scripts/lib/ssot-paths.ts:SSOT_CANON.
 */
export const SSOT_CANON = ".chthonic/SSOT.md";

/** Generated downstream MIRROR of SSOT_CANON (kept for legacy script refs; not primary). */
export const SSOT_HOLDER = ".github/copilot-instructions.archive.md";

/** The 85-line routing pointer. */
export const SSOT_POINTER = ".github/copilot-instructions.md";

/** The historizing fork (pre-freeze snapshot). */
export const SSOT_PROTO = ".github/copilot-instructions-copy.md";
