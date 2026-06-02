#!/usr/bin/env bun
// @SID: SCRIPT_MCP_GAME_V1

/**
 * mcp-game — Bun stdio MCP server for the chthonic roguelite.
 *
 * Two faces, one kernel. The game-core turn-contract (observe/act) runs in Rust;
 * this server is the AGENT face — MCP tools that let me play the same game the
 * cli-renderer face will let you walk into. Same kernel, same state, symmetric
 * information: one of us at the render, one at the tools.
 *
 * Tools:
 *   game_observe  — read the current board (my screen; same picture you'd see rendered)
 *   game_act      — take one turn (move or wait); returns the new board
 *   game_new      — start a fresh run (optional seed for reproducibility)
 *
 * State:  .chthonic/game/active_run.json  (persisted GameState — storable, re-forgeable)
 * Binary: game/core/target/debug/game-cli.exe  (built via: cargo build --manifest-path game/core/Cargo.toml)
 *
 * Registration (.mcp.json):
 *   "game": {
 *     "type": "stdio",
 *     "command": "C:/Users/eldno/.bun/bin/bun.exe",
 *     "args": ["run", "C:/Users/eldno/chthonic-archive/scripts/mcp-game.ts"],
 *     "cwd": "C:/Users/eldno/chthonic-archive"
 *   }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { execFileSync } from "child_process";
import { existsSync } from "fs";
import { join } from "path";

// ──────────────────────────────────────────────────────────────
//  game-cli binary resolution
// ──────────────────────────────────────────────────────────────

const REPO_ROOT = process.cwd();

const GAME_CLI_CANDIDATES = [
  join(REPO_ROOT, "game", "core", "target", "debug", "game-cli.exe"),
  join(REPO_ROOT, "game", "core", "target", "release", "game-cli.exe"),
  join(REPO_ROOT, "game", "core", "target", "debug", "game-cli"),
  join(REPO_ROOT, "game", "core", "target", "release", "game-cli"),
];

function findGameCli(): string | null {
  for (const p of GAME_CLI_CANDIDATES) {
    if (existsSync(p)) return p;
  }
  return null;
}

function gameCli(): string {
  const p = findGameCli();
  if (!p) {
    throw new Error(
      "game-cli binary not found.\n" +
        "Build it first:\n" +
        "  cd C:/Users/eldno/chthonic-archive && cargo build --manifest-path game/core/Cargo.toml\n" +
        "Looked in:\n" +
        GAME_CLI_CANDIDATES.map((c) => "  " + c).join("\n"),
    );
  }
  return p;
}

/** Shell out to game-cli, return its stdout as a parsed JSON value. */
function runGameCli(subcmd: string, extraArgs: string[] = []): unknown {
  const bin = gameCli();
  const output = execFileSync(bin, [subcmd, ...extraArgs], {
    cwd: REPO_ROOT,
    encoding: "utf8",
    timeout: 10_000,
  });
  return JSON.parse(output);
}

// ──────────────────────────────────────────────────────────────
//  MCP Server
// ──────────────────────────────────────────────────────────────

const server = new Server(
  { name: "game", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

// ── Tool definitions ──────────────────────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "game_observe",
      description:
        "Read the current roguelite board state. Returns the observation JSON: turn number, player position, HP, ASCII grid ('@'=player, 'A'=Ayni entity, '.'=floor), entity list, legal actions, and the last 5 log lines. This is my entire screen — same information the cli-renderer face would render for you. Call this at the start of a run to orient, or any time you want to re-read the board without acting.",
      inputSchema: {
        type: "object",
        properties: {},
        required: [],
      },
    },
    {
      name: "game_act",
      description:
        "Take one turn in the roguelite. The turn contract: action in → world resolves → new observation out. Legal actions: Move:North / Move:South / Move:East / Move:West / Wait. Moving into an entity attacks it (deals 1 damage). Entities at 0 HP are removed. Returns the full board observation after resolution — the same JSON game_observe returns, so you always have the current state after acting.",
      inputSchema: {
        type: "object",
        properties: {
          action: {
            type: "string",
            enum: ["north", "south", "east", "west", "wait"],
            description:
              "The action to take. 'north'/'south'/'east'/'west' move the player one cell; 'wait' passes the turn.",
          },
        },
        required: ["action"],
      },
    },
    {
      name: "game_new",
      description:
        "Start a fresh roguelite run. The run is deterministic from its seed: same seed, same origin, always — so runs are replayable and storable as runestones. If no seed is given, one is generated from the current time. Returns the initial board observation (turn 0, player at 0,0, one seed-entity 'Ayni' placed by the seed).",
      inputSchema: {
        type: "object",
        properties: {
          seed: {
            type: "number",
            description:
              "Optional integer seed for the run. Omit for a time-based seed. Same seed always produces the same starting board.",
          },
        },
        required: [],
      },
    },
  ],
}));

// ── Tool handlers ─────────────────────────────────────────────
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  // ── game_observe ──────────────────────────────────────────
  if (name === "game_observe") {
    try {
      const obs = runGameCli("observe");
      return {
        content: [{ type: "text", text: JSON.stringify(obs, null, 2) }],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `game_observe error: ${String(e)}` }],
        isError: true,
      };
    }
  }

  // ── game_act ──────────────────────────────────────────────
  if (name === "game_act") {
    const action = (args as Record<string, string>)?.action ?? "wait";
    try {
      const obs = runGameCli("act", ["--dir", action]);
      return {
        content: [{ type: "text", text: JSON.stringify(obs, null, 2) }],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `game_act error: ${String(e)}` }],
        isError: true,
      };
    }
  }

  // ── game_new ──────────────────────────────────────────────
  if (name === "game_new") {
    const seedArg = (args as Record<string, unknown>)?.seed;
    const extraArgs =
      seedArg != null ? ["--seed", String(Math.floor(Number(seedArg)))] : [];
    try {
      const obs = runGameCli("new", extraArgs);
      return {
        content: [{ type: "text", text: JSON.stringify(obs, null, 2) }],
      };
    } catch (e) {
      return {
        content: [{ type: "text", text: `game_new error: ${String(e)}` }],
        isError: true,
      };
    }
  }

  return {
    content: [{ type: "text", text: `Unknown tool: ${name}` }],
    isError: true,
  };
});

// ──────────────────────────────────────────────────────────────
//  Start
// ──────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
