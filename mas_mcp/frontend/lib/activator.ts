/**
 * MAS-MCP Cycle Activator
 * 
 * IPC Bridge between Bun/Next.js frontend and Python/uv backend.
 * Implements the Bun.spawn + uv run protocol from Gemini 3 Research Report.
 * 
 * @see Section 4.1 - "The Bun.spawn + uv run Protocol"
 * @ssot .github/copilot-instructions.md
 */

import { spawn, type Subprocess } from "bun";
import { join, dirname } from "path";

// ============================================================================
// Types
// ============================================================================

export interface CycleResult {
  success: boolean;
  cycle_id: string;
  ssot_hash: string;
  timestamp: string;
  duration_ms: number;
  milfs_activated: string[];
  artifacts_generated: string[];
  errors?: string[];
}

export interface CycleOptions {
  /** Run in quiet mode (JSON-only output) */
  quiet?: boolean;
  /** Specific MILF IDs to activate */
  milfs?: string[];
  /** Force CPU-only execution (disable GPU) */
  cpuOnly?: boolean;
  /** Timeout in milliseconds (default: 300000 = 5 minutes) */
  timeout?: number;
}

export interface ActivatorConfig {
  /** Path to project root (where pyproject.toml lives) */
  projectRoot: string;
  /** Python version to enforce */
  pythonVersion: string;
  /** Enable verbose logging to stderr */
  verbose: boolean;
}

export type CycleStatus = 
  | "idle"
  | "spawned"
  | "processing"
  | "complete"
  | "error"
  | "timeout";

export interface CycleState {
  status: CycleStatus;
  pid?: number;
  startTime?: number;
  lastUpdate?: string;
  progress?: number;
}

// ============================================================================
// Activator Class
// ============================================================================

export class CycleActivator {
  private config: ActivatorConfig;
  private state: CycleState = { status: "idle" };
  private activeProcess: Subprocess | null = null;

  constructor(config?: Partial<ActivatorConfig>) {
    // Default configuration - assumes frontend is in mas_mcp/frontend/
    this.config = {
      projectRoot: config?.projectRoot ?? join(dirname(import.meta.dir), ".."),
      pythonVersion: config?.pythonVersion ?? "3.13",
      verbose: config?.verbose ?? false,
    };
  }

  /**
   * Get current cycle state
   */
  getState(): CycleState {
    return { ...this.state };
  }

  /**
   * Check if a cycle is currently running
   */
  isRunning(): boolean {
    return this.state.status === "spawned" || this.state.status === "processing";
  }

  /**
   * Start a new cycle
   * 
   * @returns Promise resolving to CycleResult or rejecting with error
   */
  async startCycle(options: CycleOptions = {}): Promise<CycleResult> {
    if (this.isRunning()) {
      throw new Error("Cycle already in progress. Wait for completion or call abort().");
    }

    const timeout = options.timeout ?? 300_000; // 5 minute default
    const args = this.buildArgs(options);

    this.state = {
      status: "spawned",
      startTime: Date.now(),
    };

    try {
      const result = await this.executeWithTimeout(args, timeout);
      this.state = { status: "complete" };
      return result;
    } catch (error) {
      this.state = { 
        status: "error",
        lastUpdate: error instanceof Error ? error.message : String(error),
      };
      throw error;
    }
  }

  /**
   * Abort a running cycle
   */
  abort(): boolean {
    if (this.activeProcess && this.isRunning()) {
      this.activeProcess.kill("SIGTERM");
      this.state = { status: "idle" };
      this.activeProcess = null;
      return true;
    }
    return false;
  }

  // --------------------------------------------------------------------------
  // Private Methods
  // --------------------------------------------------------------------------

  private buildArgs(options: CycleOptions): string[] {
    const args = ["uv", "run", "scripts/run_cycle.py"];
    
    if (options.quiet !== false) {
      args.push("--quiet");
    }
    
    if (options.cpuOnly) {
      args.push("--cpu-only");
    }
    
    if (options.milfs && options.milfs.length > 0) {
      args.push("--milfs", options.milfs.join(","));
    }

    return args;
  }

  private async executeWithTimeout(args: string[], timeout: number): Promise<CycleResult> {
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.abort();
        this.state = { status: "timeout" };
        reject(new Error(`Cycle timed out after ${timeout}ms`));
      }, timeout);

      this.spawnProcess(args)
        .then(resolve)
        .catch(reject)
        .finally(() => clearTimeout(timeoutId));
    });
  }

  private async spawnProcess(args: string[]): Promise<CycleResult> {
    const env = this.buildEnvironment();

    if (this.config.verbose) {
      console.error(`[Activator] Spawning: ${args.join(" ")}`);
      console.error(`[Activator] CWD: ${this.config.projectRoot}`);
    }

    this.activeProcess = spawn(args, {
      cwd: this.config.projectRoot,
      env,
      stdin: "ignore",
      stdout: "pipe",
      stderr: "pipe",
    });

    this.state.pid = this.activeProcess.pid;
    this.state.status = "processing";

    // Collect output streams
    const [stdout, stderr] = await Promise.all([
      this.collectStream(this.activeProcess.stdout),
      this.collectStream(this.activeProcess.stderr),
    ]);

    // Wait for process exit
    const exitCode = await this.activeProcess.exited;
    this.activeProcess = null;

    if (this.config.verbose && stderr) {
      console.error(`[Activator] stderr:\n${stderr}`);
    }

    if (exitCode !== 0) {
      throw new Error(`Cycle failed with exit code ${exitCode}: ${stderr || stdout}`);
    }

    // Parse JSON result from stdout
    try {
      const result = JSON.parse(stdout.trim()) as CycleResult;
      return result;
    } catch (parseError) {
      throw new Error(`Failed to parse cycle output as JSON: ${stdout.substring(0, 200)}`);
    }
  }

  private buildEnvironment(): Record<string, string> {
    return {
      ...process.env,
      // Critical: Silence uv's progress output to keep stdout clean for JSON
      UV_NO_PROGRESS: "1",
      // Ensure we use the exact Python version we expect
      UV_PYTHON: this.config.pythonVersion,
      // Disable color codes that could corrupt JSON parsing
      NO_COLOR: "1",
      FORCE_COLOR: "0",
      // Ensure Python doesn't buffer output
      PYTHONUNBUFFERED: "1",
    } as Record<string, string>;
  }

  private async collectStream(stream: ReadableStream<Uint8Array> | number | null | undefined): Promise<string> {
    // Handle null, undefined, or file descriptor (number) cases
    if (!stream || typeof stream === 'number') return "";
    
    const chunks: Uint8Array[] = [];
    const reader = stream.getReader();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) chunks.push(value);
      }
    } finally {
      reader.releaseLock();
    }

    const decoder = new TextDecoder();
    return chunks.map(chunk => decoder.decode(chunk)).join("");
  }
}

// ============================================================================
// Convenience Functions
// ============================================================================

/** Singleton instance for simple usage */
let defaultActivator: CycleActivator | null = null;

export function getActivator(config?: Partial<ActivatorConfig>): CycleActivator {
  if (!defaultActivator) {
    defaultActivator = new CycleActivator(config);
  }
  return defaultActivator;
}

/**
 * Quick-start a cycle with default options
 */
export async function runCycle(options?: CycleOptions): Promise<CycleResult> {
  return getActivator().startCycle(options);
}

// ============================================================================
// Additional Result Types for Extended Operations
// ============================================================================

export interface StatusResult {
  running: boolean;
  status: CycleStatus;
  pid?: number;
  uptime_ms?: number;
  last_update?: string;
}

export interface ProbeResult {
  success: boolean;
  duration_ms: number;
  cuda_available: boolean;
  cuda_version?: string;
  cudnn_available?: boolean;
  tensorrt_available?: boolean;
  onnx_providers?: string[];
  gpu_name?: string;
  gpu_memory_mb?: number;
  errors?: string[];
  data?: Record<string, unknown>;
}

export interface ActivateResult {
  success: boolean;
  profile_used: string;
  activated: string[];
  rejected: string[];
  summary: {
    total: number;
    activated: number;
    rejected: number;
  };
  error?: string;
}

export interface ActivateOptions {
  profile?: string;
  dry_run?: boolean;
}

// ============================================================================
// Extended Activator Methods
// ============================================================================

// Extend CycleActivator with additional methods via prototype
declare module "./activator" {
  interface CycleActivator {
    checkStatus(): Promise<StatusResult>;
    runProbe(): Promise<ProbeResult>;
    activateMilfs(options?: ActivateOptions): Promise<ActivateResult>;
  }
}

CycleActivator.prototype.checkStatus = async function(): Promise<StatusResult> {
  const state = this.getState();
  return {
    running: this.isRunning(),
    status: state.status,
    pid: state.pid,
    uptime_ms: state.startTime ? Date.now() - state.startTime : undefined,
    last_update: state.lastUpdate,
  };
};

CycleActivator.prototype.runProbe = async function(): Promise<ProbeResult> {
  const startTime = Date.now();
  const args = ["uv", "run", "scripts/probe_gpu_compatibility.py", "--json"];
  
  try {
    const proc = spawn(args, {
      cwd: (this as any).config.projectRoot,
      env: {
        ...process.env,
        UV_NO_PROGRESS: "1",
        PYTHONUNBUFFERED: "1",
        NO_COLOR: "1",
      } as Record<string, string>,
      stdin: "ignore",
      stdout: "pipe",
      stderr: "pipe",
    });

    const [stdout, stderr] = await Promise.all([
      collectStream(proc.stdout),
      collectStream(proc.stderr),
    ]);

    const exitCode = await proc.exited;
    const duration_ms = Date.now() - startTime;

    if (exitCode !== 0) {
      return {
        success: false,
        duration_ms,
        cuda_available: false,
        errors: [stderr || `Exit code ${exitCode}`],
      };
    }

    try {
      const data = JSON.parse(stdout.trim());
      return {
        success: true,
        duration_ms,
        cuda_available: data.cuda?.available ?? false,
        cuda_version: data.cuda?.version,
        cudnn_available: data.cudnn?.available,
        tensorrt_available: data.tensorrt?.available,
        onnx_providers: data.onnx?.providers,
        gpu_name: data.cuda?.device_name,
        gpu_memory_mb: data.cuda?.memory_total_mb,
        data,
      };
    } catch {
      return {
        success: false,
        duration_ms,
        cuda_available: false,
        errors: [`Failed to parse probe output: ${stdout.substring(0, 200)}`],
      };
    }
  } catch (error) {
    return {
      success: false,
      duration_ms: Date.now() - startTime,
      cuda_available: false,
      errors: [error instanceof Error ? error.message : String(error)],
    };
  }
};

CycleActivator.prototype.activateMilfs = async function(
  options: ActivateOptions = {}
): Promise<ActivateResult> {
  const { profile = "inference_default", dry_run = false } = options;
  const args = ["uv", "run", "scripts/milf_activator.py", "--profile", profile, "--json"];
  
  if (dry_run) {
    args.push("--dry-run");
  }

  try {
    const proc = spawn(args, {
      cwd: (this as any).config.projectRoot,
      env: {
        ...process.env,
        UV_NO_PROGRESS: "1",
        PYTHONUNBUFFERED: "1",
        NO_COLOR: "1",
      } as Record<string, string>,
      stdin: "ignore",
      stdout: "pipe",
      stderr: "pipe",
    });

    const [stdout, stderr] = await Promise.all([
      collectStream(proc.stdout),
      collectStream(proc.stderr),
    ]);

    const exitCode = await proc.exited;

    if (exitCode !== 0) {
      return {
        success: false,
        profile_used: profile,
        activated: [],
        rejected: [],
        summary: { total: 0, activated: 0, rejected: 0 },
        error: stderr || `Exit code ${exitCode}`,
      };
    }

    try {
      const data = JSON.parse(stdout.trim());
      return {
        success: true,
        profile_used: profile,
        activated: data.activated ?? [],
        rejected: data.rejected ?? [],
        summary: data.summary ?? { total: 0, activated: 0, rejected: 0 },
      };
    } catch {
      return {
        success: false,
        profile_used: profile,
        activated: [],
        rejected: [],
        summary: { total: 0, activated: 0, rejected: 0 },
        error: `Failed to parse activator output: ${stdout.substring(0, 200)}`,
      };
    }
  } catch (error) {
    return {
      success: false,
      profile_used: profile,
      activated: [],
      rejected: [],
      summary: { total: 0, activated: 0, rejected: 0 },
      error: error instanceof Error ? error.message : String(error),
    };
  }
};

// Helper function for collecting stream output
async function collectStream(stream: ReadableStream<Uint8Array> | number | null | undefined): Promise<string> {
  // Handle null, undefined, or file descriptor (number) cases
  if (!stream || typeof stream === 'number') return "";
  
  const chunks: Uint8Array[] = [];
  const reader = stream.getReader();
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const decoder = new TextDecoder();
  return chunks.map(chunk => decoder.decode(chunk)).join("");
}

// ============================================================================
// CLI Entrypoint (when run directly with `bun run lib/activator.ts`)
// ============================================================================

if (import.meta.main) {
  console.log("🔄 MAS-MCP Cycle Activator");
  console.log("==========================");
  
  const activator = new CycleActivator({ verbose: true });
  
  try {
    console.log("Starting cycle...\n");
    const result = await activator.startCycle({ quiet: true });
    
    console.log("\n✅ Cycle Complete!");
    console.log(`   ID: ${result.cycle_id}`);
    console.log(`   Duration: ${result.duration_ms}ms`);
    console.log(`   SSOT Hash: ${result.ssot_hash.substring(0, 16)}...`);
    console.log(`   MILFs Activated: ${result.milfs_activated.length}`);
    console.log(`   Artifacts: ${result.artifacts_generated.length}`);
  } catch (error) {
    console.error("\n❌ Cycle Failed:", error);
    process.exit(1);
  }
}
