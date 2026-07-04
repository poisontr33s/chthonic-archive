// Inference adapter — spawn `claude --print --output-format=stream-json`, emit events.
// This is the only place that talks to Anthropic (transitively, via the CLI).
import { spawn, ChildProcess } from "node:child_process";
import { EventEmitter } from "node:events";

export interface StreamEvent {
  type: string;
  data: any;
  [key: string]: any;
}

export class CliInference extends EventEmitter {
  private child: ChildProcess | null = null;

  constructor(private readonly cliPath = "claude") {
    super();
  }

  send(prompt: string, opts: { cwd?: string } = {}) {
    if (this.child) this.child.kill();
    this.child = spawn(
      this.cliPath,
      ["--print", "--output-format", "stream-json", "--include-partial-messages", prompt],
      { cwd: opts.cwd, shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] }
    );

    let buf = "";
    this.child.stdout?.on("data", chunk => {
      buf += chunk.toString();
      let nl;
      while ((nl = buf.indexOf("\n")) !== -1) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        try {
          const evt: StreamEvent = JSON.parse(line);
          this.emit("event", evt);
        } catch { /* skip malformed line */ }
      }
    });

    this.child.stderr?.on("data", d => this.emit("event", { type: "error", data: d.toString() } as StreamEvent));
    this.child.on("close", code => this.emit("event", { type: "done", data: { code } } as StreamEvent));
  }

  dispose() { this.child?.kill(); this.child = null; }
}

export function streamEventText(e: StreamEvent): string {
  if (e.type === "message") {
    return textFromUnknown(e.data?.delta ?? e.data?.text ?? e.data);
  }
  if (e.type === "content_block_delta") {
    return textFromUnknown(e.delta?.text ?? e.data?.delta?.text);
  }
  if (e.type === "assistant") {
    const message = e.message ?? e.data?.message ?? e.data;
    return textFromContent(message?.content ?? message);
  }
  if (e.type === "partial_message") {
    const message = e.message ?? e.data?.message ?? e.data;
    return textFromContent(message?.content ?? message);
  }
  return "";
}

export function streamEventError(e: StreamEvent): string | null {
  if (e.type === "error") return textFromUnknown(e.data ?? e.error ?? e.message) || "stream error";
  if (e.type === "result" && (e.is_error || e.subtype === "error")) {
    return textFromUnknown(e.result ?? e.data ?? e.error) || "Claude CLI result error";
  }
  return null;
}

export function streamEventDone(e: StreamEvent): boolean {
  return e.type === "done" || e.type === "result" || e.type === "message_stop";
}

function textFromContent(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(item => textFromUnknown(item?.text ?? item?.content)).filter(Boolean).join("");
  }
  return textFromUnknown(value);
}

function textFromUnknown(value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    return textFromUnknown(obj.text ?? obj.delta ?? obj.content);
  }
  return "";
}
