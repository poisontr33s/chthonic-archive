// Bridge to the Claude Code extension. We never read its credentials directly;
// we shell out to the `claude` CLI which Claude Code installs + keeps signed in.
import * as vscode from "vscode";
import { spawn } from "node:child_process";

export class ClaudeCodeBridge {
  readonly ready: boolean;
  readonly api: any | null;

  private constructor(ready: boolean, api: any | null) {
    this.ready = ready;
    this.api = api;
  }

  static async connect(): Promise<ClaudeCodeBridge> {
    const ext = vscode.extensions.getExtension("anthropic.claude-code");
    if (!ext) return new ClaudeCodeBridge(false, null);
    if (!ext.isActive) {
      try { await ext.activate(); } catch { /* keep going */ }
    }
    // Forward-looking: if Claude Code grows a public exports surface, use it.
    const api = (ext.exports && typeof ext.exports === "object") ? ext.exports : null;
    return new ClaudeCodeBridge(true, api);
  }

  /** Probe the CLI to confirm sign-in. Resolves with stdout or rejects. */
  whoami(): Promise<string> {
    return new Promise((resolve, reject) => {
      const p = spawn("claude", ["whoami"], { shell: process.platform === "win32" });
      let out = "", err = "";
      p.stdout.on("data", d => out += d);
      p.stderr.on("data", d => err += d);
      p.on("close", code => code === 0 ? resolve(out.trim()) : reject(new Error(err.trim() || "claude whoami failed")));
    });
  }
}
