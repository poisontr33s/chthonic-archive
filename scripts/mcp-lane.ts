#!/usr/bin/env bun
// @SID: SCRIPT_MCP_LANE_V1
/**
 * mcp-lane -- MCP server that abstracts the parallel-lane launcher into a tool.
 *
 * Wraps the SAME method as scripts/launch-sonnet-lane.ps1 (the `claude --model ... --effort ...`
 * launch), exposed as the `launch_lane` tool so an agent can spin up a pre-scoped Sonnet lane
 * programmatically -- the floor past tokenomics: self-orchestration, not just quota reuse.
 *
 * dry_run returns the exact spawn + whether `claude` is reachable WITHOUT launching. The smoke
 * test (scripts/verify-lane-launch.ts) rides that path: it answers "will this launch?" before it
 * fires. The actual new-window interactive spawn is the conductor's one-time confirm (a real test
 * would pop windows + burn quota), so it is deliberately NOT auto-fired here.
 *
 * Registration (.mcp.json):
 *   "lane": { "type":"stdio", "command":"C:/Users/eldno/.bun/bin/bun.exe",
 *             "args":["run","C:/Users/eldno/chthonic-archive/scripts/mcp-lane.ts"],
 *             "cwd":"C:/Users/eldno/chthonic-archive" }
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { join } from "path";

export interface LaunchOpts {
  model?: string;
  effort?: string;
}
export interface LaunchPlan {
  script: string;
  spawnCmd: string;
  spawnArgs: string[];
  human: string;
}

const EFFORTS = ["low", "medium", "high", "xhigh", "max"];

/** Pure: the new-window spawn that reuses launch-sonnet-lane.ps1 (the default method, one level up). */
export function buildLaunch(repoRoot: string, opts: LaunchOpts = {}): LaunchPlan {
  const model = (opts.model ?? "sonnet").trim() || "sonnet";
  const effort = EFFORTS.includes((opts.effort ?? "").trim()) ? (opts.effort as string).trim() : "max";
  const script = join(repoRoot, "scripts", "launch-sonnet-lane.ps1");
  // A new pwsh window running the script -> the interactive lane, identical to the manual path.
  const startProcess =
    `Start-Process pwsh -ArgumentList @('-NoExit','-NoProfile','-File','${script}','-Model','${model}','-Effort','${effort}')`;
  return {
    script,
    spawnCmd: "pwsh",
    spawnArgs: ["-NoProfile", "-Command", startProcess],
    human: `claude --model ${model} --effort ${effort} --name sonnet-lane (new window, via ${script})`,
  };
}

function claudePath(): string | null {
  return Bun.which("claude");
}

const server = new Server({ name: "lane", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "launch_lane",
      description:
        "Spawn the parallel Sonnet lane -- a second Claude Code session on its own quota lane, pre-scoped (Python embedding/clustering, off the Rust daemon). Wraps scripts/launch-sonnet-lane.ps1 (the same method as the manual launch), opened in a new terminal window. Set dry_run=true to get the exact spawn + whether `claude` is reachable WITHOUT launching (the smoke-test path). model defaults to 'sonnet' (plan weekly quota); effort defaults to 'max' (max thinking, one of low|medium|high|xhigh|max).",
      inputSchema: {
        type: "object",
        properties: {
          model: { type: "string", description: "Model alias/id (default 'sonnet' = plan weekly quota)." },
          effort: { type: "string", description: "Effort/thinking: low|medium|high|xhigh|max (default 'max')." },
          dry_run: { type: "boolean", description: "If true, return the plan + claude availability without launching." },
        },
        required: [],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name !== "launch_lane") {
    return { content: [{ type: "text", text: `Unknown tool: ${req.params.name}` }], isError: true };
  }
  const args = (req.params.arguments ?? {}) as Record<string, unknown>;
  const dryRun = args.dry_run === true;
  const plan = buildLaunch(process.cwd(), { model: args.model as string, effort: args.effort as string });
  const claude = claudePath();

  if (dryRun || !claude) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              dry_run: dryRun,
              claude_found: !!claude,
              claude_path: claude,
              would_launch: plan.human,
              spawn: `${plan.spawnCmd} ${plan.spawnArgs.join(" ")}`,
              note: claude
                ? dryRun
                  ? "dry run -- nothing launched"
                  : "would launch"
                : "claude not on PATH -- cannot launch",
            },
            null,
            2,
          ),
        },
      ],
    };
  }

  try {
    const child = Bun.spawn([plan.spawnCmd, ...plan.spawnArgs], {
      stdin: "ignore",
      stdout: "ignore",
      stderr: "ignore",
    });
    child.unref?.();
    return { content: [{ type: "text", text: `launched: ${plan.human}` }] };
  } catch (e) {
    return { content: [{ type: "text", text: `launch_lane soft-fail: ${String(e)}` }] };
  }
});

// Start the server only when run directly -- the smoke test imports buildLaunch without this firing.
if (import.meta.main) {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
