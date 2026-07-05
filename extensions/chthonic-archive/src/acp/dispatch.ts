#!/usr/bin/env bun
// @SID: EXT_DISPATCH_V1
/**
 * Agent dispatch — picks which agent binary to spawn for a given task.
 *
 * Parallel arsenal contract ([[reference-parallel-arsenal-bridges]]):
 *  - Rail A: chthonic-copilot-bridge   (Rust, github-copilot-sdk = 1.0.0-beta.9 wire)
 *  - Rail B: chthonic-acp-bridge       (Rust, agent-client-protocol = 0.12 wire)
 *  - Default ACP: spawn `copilot --acp` directly (current AcpConnection behavior)
 *
 * This module is additive and read-only against the existing AcpConnection.
 * It surfaces the AgentSpec data; callers decide which client implementation
 * to drive it through. The current AcpConnection in ./connection.ts is the
 * 'acp-direct' lane (spawn copilot.exe --acp). Future Rust-bridge lanes will
 * spawn a different binary that emits one-shot stdout (different protocol
 * shape than ACP, so a separate client implementation is needed).
 */

import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

// ─── Agent specs ──────────────────────────────────────────────────────────

/** Wire protocol shape — informs the caller which client implementation to use. */
export type AgentProtocol = 'acp' | 'oneshot-stdio';

export interface AgentSpec {
    /** Display name (for logs + UI). */
    name: string;
    /** Absolute path to the binary to spawn. */
    command: string;
    /** Args passed to the binary. */
    args: string[];
    /** Wire protocol the binary speaks. */
    protocol: AgentProtocol;
    /** Diagnostic note (e.g. "resolved from $COPILOT_CLI_PATH"). */
    resolution: string;
}

/** Routing key — what kind of agent the task wants. */
export type AgentKind =
    | 'acp-direct'       // spawn copilot.exe --acp (current default)
    | 'copilot-sdk'      // spawn chthonic-copilot-bridge.exe
    | 'acp-bridge'       // spawn chthonic-acp-bridge.exe
    | 'auto';            // pick based on context (currently == 'acp-direct')

// ─── Copilot path resolution ──────────────────────────────────────────────

/**
 * Resolve the copilot CLI binary. Honors $COPILOT_CLI_PATH first, then
 * a small set of known install locations on Windows, then bare "copilot"
 * on PATH. Returns the resolved path plus a one-line resolution note.
 *
 * NOTE: the existing extensions/chthonic-archive/src/acp/connection.ts pins
 * a hardcoded path under a different username ("eldno") — that's residue
 * from a robocopy migration off an older laptop account that wasn't cleaned
 * up post-move, not a typo. The path doesn't resolve on the current desktop
 * regardless of why. This resolver is the durable fix — when AcpConnection
 * is updated to use it, the migration-residue line goes away.
 */
export function resolveCopilotPath(): { path: string; resolution: string } {
    const fromEnv = process.env.COPILOT_CLI_PATH;
    if (fromEnv && existsSync(fromEnv)) {
        return { path: fromEnv, resolution: 'from $COPILOT_CLI_PATH' };
    }

    const home = process.env.USERPROFILE || process.env.HOME || '';
    const wingetPath = home
        ? join(
              home,
              'AppData\\Local\\Microsoft\\WinGet\\Packages\\GitHub.Copilot.Prerelease_Microsoft.Winget.Source_8wekyb3d8bbwe\\copilot.exe',
          )
        : '';
    if (wingetPath && existsSync(wingetPath)) {
        return { path: wingetPath, resolution: 'from WinGet Prerelease install' };
    }

    // Final fallback: bare name, relies on PATH at spawn time.
    return { path: 'copilot', resolution: 'bare name (relies on PATH)' };
}

// ─── Bridge-binary resolution ─────────────────────────────────────────────

/**
 * Locate a Rust bridge binary built from extensions/.../native/. Looks at
 * release first, then debug. Returns null if neither exists.
 *
 * `repoRoot` is the chthonic-archive repo root. When called from within the
 * extension, pass `vscode.workspace.workspaceFolders?.[0].uri.fsPath`.
 */
export function locateBridgeBinary(
    repoRoot: string,
    crateName: 'chthonic-copilot-bridge' | 'chthonic-acp-bridge',
): { path: string; profile: 'release' | 'debug' } | null {
    const nativeRoot = join(repoRoot, 'extensions', 'chthonic-archive', 'native');
    const isWin = process.platform === 'win32';
    const exe = isWin ? `${crateName}.exe` : crateName;

    const releasePath = join(nativeRoot, 'target', 'release', exe);
    if (existsSync(releasePath)) return { path: releasePath, profile: 'release' };

    const debugPath = join(nativeRoot, 'target', 'debug', exe);
    if (existsSync(debugPath)) return { path: debugPath, profile: 'debug' };

    return null;
}

// ─── Routing ──────────────────────────────────────────────────────────────

/**
 * Choose an agent for the given task kind. The dispatcher contract:
 *
 *  - 'acp-direct' / 'auto' → spawn `copilot --acp` (current AcpConnection)
 *  - 'copilot-sdk'         → spawn chthonic-copilot-bridge built binary
 *  - 'acp-bridge'          → spawn chthonic-acp-bridge built binary
 *
 * For the two Rust-bridge kinds, `repoRoot` is required so we can locate
 * the built binary. If the bridge binary isn't built (target/release or
 * target/debug missing), returns null so the caller can surface "run
 * cargo build" guidance to the user rather than spawn a missing path.
 */
export function chooseAgent(
    kind: AgentKind,
    options: { repoRoot?: string } = {},
): AgentSpec | null {
    switch (kind) {
        case 'auto':
        case 'acp-direct': {
            const { path, resolution } = resolveCopilotPath();
            return {
                name: 'copilot --acp (direct)',
                command: path,
                args: ['--acp'],
                protocol: 'acp',
                resolution,
            };
        }

        case 'copilot-sdk': {
            if (!options.repoRoot) return null;
            const located = locateBridgeBinary(options.repoRoot, 'chthonic-copilot-bridge');
            if (!located) return null;
            return {
                name: 'chthonic-copilot-bridge',
                command: located.path,
                args: [],
                protocol: 'oneshot-stdio',
                resolution: `Rust bridge (${located.profile} build)`,
            };
        }

        case 'acp-bridge': {
            if (!options.repoRoot) return null;
            const located = locateBridgeBinary(options.repoRoot, 'chthonic-acp-bridge');
            if (!located) return null;
            return {
                name: 'chthonic-acp-bridge',
                command: located.path,
                args: [],
                protocol: 'oneshot-stdio',
                resolution: `Rust bridge (${located.profile} build)`,
            };
        }
    }
}

/** Convenience: name + path one-liner for log output. */
export function describeAgent(spec: AgentSpec): string {
    return `${spec.name} [${spec.protocol}] @ ${spec.command} (${spec.resolution})`;
}

