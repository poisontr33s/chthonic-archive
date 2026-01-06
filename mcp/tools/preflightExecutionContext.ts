import { platform, type as osTypeFn } from "bun:os";
import { versions } from "bun:process";

/**
 * Preflight Execution Context Tool
 *
 * Reports execution environment with explicit refusal of ambiguity.
 * Externalizes shell sovereignty and governance rules as MCP semantics.
 *
 * Governance alignment:
 * - F1: Shell sovereignty (no cross-shell execution)
 * - F3: Permission preflight (explicit unknown state)
 * - F4: No false progress (refuse if ambiguous)
 */

interface ExecutionContext {
  execution_abi: {
    os: string;
    platform: string;
    shell: string;
    runtime: string;
    node_compat: boolean;
    bun_version?: string;
    node_version?: string;
  };
  shell_sovereignty: {
    status: "clean" | "ambiguous";
    cross_shell_detected: boolean;
    canonical_shell: string | null;
  };
  permissions: {
    repo_mutation: "unknown";
    git_commit: "unknown";
    git_push: "unknown";
  };
  governance: {
    shell_mismatch_retryable: false;
    permission_required_before_narration: true;
    structural_failures_non_retryable: true;
  };
  governance_version?: string;
}

/**
 * Infer canonical shell from environment.
 * Returns null if cannot be determined (triggers tool failure).
 */
function inferShell(): string | null {
  // On Windows, PowerShell is canonical per governance
  if (platform() === "win32") {
    return "pwsh";
  }

  // On Unix-like systems, check SHELL env var
  const shell = (globalThis as any).process?.env?.SHELL || null;
  if (shell) {
    // Extract shell name from path, normalize
    const parts = shell.split("/");
    const shellName = parts[parts.length - 1] || null;
    return shellName;
  }

  return null;
}

/**
 * Detect runtime and verify it's Bun or Node-compatible.
 * Throws if runtime cannot be identified.
 */
function detectRuntime(): {
  runtime: string;
  node_compat: boolean;
  bun_version?: string;
  node_version?: string;
} {
  // Check for Bun runtime via globalThis
  if (typeof (globalThis as any).Bun !== "undefined") {
    const bun = (globalThis as any).Bun;
    return {
      runtime: "bun",
      node_compat: true,
      bun_version: bun.version,
    };
  }

  // Check for Node.js via process.versions.node
  const nodeVersion = (globalThis as any).process?.versions?.node || versions?.node;
  if (nodeVersion) {
    return {
      runtime: "node",
      node_compat: true,
      node_version: nodeVersion,
    };
  }

  // Unknown runtime - refuse to continue
  throw new Error("Runtime detection failed: neither Bun nor Node detected");
}

/**
 * Preflight execution context check.
 *
 * Hard-fails if:
 * - Shell cannot be identified
 * - Runtime is neither Bun nor Node-compatible
 * - OS inference fails
 *
 * Never spawns processes, never mutates environment, never simulates permission.
 */
export async function preflightExecutionContext(): Promise<ExecutionContext> {
  // Detect OS
  const osPlatform = platform();
  const osType = osTypeFn();

  if (!osPlatform || !osType) {
    throw new Error("OS detection failed: platform or type unavailable");
  }

  // Detect runtime
  const runtimeInfo = detectRuntime();

  // Infer shell
  const shell = inferShell();
  if (!shell) {
    throw new Error("Shell detection failed: cannot determine canonical shell");
  }

  // Map platform to OS name (normalized)
  const osName =
    osPlatform === "win32" ? "windows" : osPlatform === "darwin" ? "macos" : osPlatform === "linux" ? "linux" : osPlatform;

  // Shell sovereignty status
  // In this implementation, cross-shell is never detected because we don't spawn processes.
  // Status is "clean" if shell was successfully inferred.
  const shellSovereignty = {
    status: "clean" as const,
    cross_shell_detected: false,
    canonical_shell: shell,
  };

  const result: ExecutionContext = {
    execution_abi: {
      os: osName,
      platform: osPlatform,
      shell,
      runtime: runtimeInfo.runtime,
      node_compat: runtimeInfo.node_compat,
      ...(runtimeInfo.bun_version && { bun_version: runtimeInfo.bun_version }),
      ...(runtimeInfo.node_version && { node_version: runtimeInfo.node_version }),
    },
    shell_sovereignty: shellSovereignty,
    permissions: {
      repo_mutation: "unknown",
      git_commit: "unknown",
      git_push: "unknown",
    },
    governance: {
      shell_mismatch_retryable: false,
      permission_required_before_narration: true,
      structural_failures_non_retryable: true,
    },
    governance_version: "session-learning.v1",
  };

  return result;
}
