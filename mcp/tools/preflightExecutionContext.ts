import { platform, type } from "node:os";
import { version, versions } from "node:process";

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
  const shell = process.env.SHELL;
  if (shell) {
    // Extract shell name from path
    const shellName = shell.split("/").pop() || null;
    return shellName;
  }

  return null;
}

/**
 * Detect runtime and verify it's Bun or Node-compatible.
 * Throws if runtime cannot be identified.
 */
function detectRuntime(): { runtime: string; node_compat: boolean; bun_version?: string; node_version?: string } {
  // Check for Bun runtime
  if (typeof Bun !== "undefined") {
    return {
      runtime: "bun",
      node_compat: true,
      bun_version: Bun.version,
    };
  }

  // Check for Node.js
  if (versions.node) {
    return {
      runtime: "node",
      node_compat: true,
      node_version: versions.node,
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
  const osType = type();

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

  // Map platform to OS name
  const osName = osPlatform === "win32"
    ? "windows"
    : osPlatform === "darwin"
    ? "macos"
    : osPlatform === "linux"
    ? "linux"
    : osPlatform;

  // Shell sovereignty status
  // In this implementation, cross-shell is never detected because we don't spawn processes
  // Status is "clean" if shell was successfully inferred
  const shellSovereignty = {
    status: "clean" as const,
    cross_shell_detected: false,
    canonical_shell: shell,
  };

  return {
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
  };
}
