#!/usr/bin/env bun
// @SID: SCRIPT_MCP_SSOT_V1

/**
 * mcp-ssot — Bun stdio MCP server: structural doctor for the catalyst (.chthonic/SSOT.md).
 *
 * The SSOT is a ~10k-line living document written in a substrate-native quasi-DSL.
 * It drifts: unbalanced bold, malformed emphasis, parse-breaking corruption, and
 * section/ordering variance. This server exposes the structural work as agent-
 * callable tools so the catalyst can be audited and improved systematically — the
 * DSL-as-linter insight turned into a service. It wraps what already exists
 * (scripts/catalyst_lint.py + the dsl-smoke grammar tool) rather than reinventing.
 *
 * Tools:
 *   ssot_lint            — bold-balance / variance audit (wraps scripts/catalyst_lint.py)
 *   ssot_parse_frontier  — where the DSL full-parse next breaks (wraps dsl-smoke/dsl-full-smoke)
 *   ssot_outline         — header/section map, for structure + ordering review
 *
 * Catalyst: .chthonic/SSOT.md
 *
 * Registration (.mcp.json):
 *   "ssot": {
 *     "type": "stdio",
 *     "command": "C:/Users/eldno/.bun/bin/bun.exe",
 *     "args": ["run", "C:/Users/eldno/chthonic-archive/scripts/mcp-ssot.ts"],
 *     "cwd": "C:/Users/eldno/chthonic-archive"
 *   }
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawnSync } from "child_process";
import { readFileSync } from "fs";
import { join } from "path";

const REPO_ROOT = process.cwd();
const SSOT_PATH = join(REPO_ROOT, ".chthonic", "SSOT.md");
const PY_ENV = { ...process.env, PYTHONUTF8: "1" };

// ── helpers ───────────────────────────────────────────────────

/** Bold-balance / variance audit via scripts/catalyst_lint.py --json. */
function runLint(path: string): unknown {
  const res = spawnSync(
    "uv",
    ["run", "scripts/catalyst_lint.py", "--json", "--path", path],
    { cwd: REPO_ROOT, encoding: "utf8", env: PY_ENV, timeout: 60_000 },
  );
  if (res.error) throw res.error;
  const out = (res.stdout || "").trim(); // exits 1 when findings exist — stdout still holds the JSON
  if (!out) throw new Error(`catalyst_lint produced no output. stderr: ${res.stderr}`);
  return JSON.parse(out);
}

interface Frontier {
  status: "OK" | "FAIL";
  fail_line?: number;
  fail_col?: number;
  expected?: string;
  first_failing_prefix?: number;
  line_text?: string;
  diagnosis?: string;
  next_action?: string;
}

/** Full-catalyst parse via the dsl-smoke grammar tool; reports the next break. */
function parseFrontier(path: string): Frontier {
  const res = spawnSync(
    "cargo",
    ["run", "-p", "dsl-smoke", "--release", "--bin", "dsl-full-smoke", "--quiet", "--", path],
    { cwd: REPO_ROOT, encoding: "utf8", timeout: 300_000 },
  );
  if (res.error) throw res.error;
  const out = `${res.stdout || ""}\n${res.stderr || ""}`;
  if (/PARSE: OK/.test(out)) return { status: "OK" };

  const f: Frontier = { status: "FAIL" };
  const pos = out.match(/-->\s*(\d+):(\d+)/);
  if (pos) {
    f.fail_line = Number(pos[1]);
    f.fail_col = Number(pos[2]);
  }
  const exp = out.match(/=\s*expected\s+(.+)/);
  if (exp) f.expected = exp[1].trim();
  const pre = out.match(/First failing prefix: lines 1\.\.(\d+)/);
  if (pre) f.first_failing_prefix = Number(pre[1]);

  const probe = f.first_failing_prefix ?? f.fail_line;
  if (probe) {
    try {
      const lines = readFileSync(path, "utf8").split("\n");
      f.line_text = (lines[probe - 1] ?? "").trim().slice(0, 300);
    } catch {
      /* leave line_text unset */
    }
  }

  // Compound past raw reporting: classify the break and hand back the next move,
  // so the diagnosis step of the peg-loop isn't re-derived by hand each time.
  if (f.line_text) {
    const structural = f.line_text.replace(/`[^`]*`/g, ""); // ignore literal ** in code spans
    const orphanBold = (structural.match(/\*\*/g) || []).length % 2 === 1;
    if (orphanBold) {
      f.diagnosis = "content-defect: unbalanced bold — an orphan ** opens a bold that runs across newlines and derails the parse downstream";
      f.next_action = `fix bold on L${probe} (drop the stray ** if a header; restore the **(...)** pair if list/prose), then re-run. ssot_lint has the full set.`;
    } else {
      f.diagnosis = `structural: parser reached '${f.expected ?? "?"}' and stopped — a construct the grammar lacks, or a non-bold malformation`;
      f.next_action = `read L${probe}: if it is a real catalyst construct, extend .chthonic/grammar/chthonic.peg (rewindable via dsl_iteration_check); if a typo/malformation, repair the line.`;
    }
  }
  return f;
}

interface Heading {
  line: number;
  level: number;
  title: string;
}

/** Header/section outline; fenced code blocks excluded. */
function outline(path: string, maxLevel: number): Heading[] {
  const lines = readFileSync(path, "utf8").split("\n");
  const out: Heading[] = [];
  let inFence = false;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trimStart().startsWith("```")) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;
    const m = line.match(/^(#{1,6})\s+(.+?)\s*$/);
    if (m && m[1].length <= maxLevel) {
      out.push({ line: i + 1, level: m[1].length, title: m[2].slice(0, 160) });
    }
  }
  return out;
}

// ── server ────────────────────────────────────────────────────

const server = new Server(
  { name: "ssot", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "ssot_lint",
      description:
        "Structural variance audit of the catalyst (.chthonic/SSOT.md). Returns every line with unbalanced markdown bold — the orphan-`**` defect that runs a bold across newlines and derails the DSL parse far downstream — each tagged with line number, kind (header/list-item/prose/table-row/blockquote), and bold-marker count. Fenced code blocks and inline-code spans are excluded so literal `**` (e.g. an `applyTo: \"**\"` glob) is not falsely flagged. Detection only: header orphans usually want the stray `**` dropped (the header already emboldens); list/prose orphans usually want the canonical `**(...)**` pair restored. Re-run after fixes to watch the count fall.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "File to lint. Defaults to .chthonic/SSOT.md." },
        },
        required: [],
      },
    },
    {
      name: "ssot_parse_frontier",
      description:
        "Runs the Chthonic DSL grammar against the FULL catalyst and reports where the parse first breaks — the next structural corruption to fix. Returns status (OK if the entire catalyst parses, else FAIL), the failing line/column, the expected token, the first-failing-prefix line (the line that introduces the break), and that line's text. The corruption-walker: fix the reported line, re-run, it advances to the next break. NOTE: a cold run compiles the Rust grammar tool and can take 1-2 minutes; warm runs are seconds.",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "Catalyst file to parse. Defaults to .chthonic/SSOT.md." },
        },
        required: [],
      },
    },
    {
      name: "ssot_outline",
      description:
        "Returns the catalyst's header/section outline — every markdown header as {line, level 1-6, title}, code fences excluded. Use it to review structure and ordering: spot duplicated section numbers, out-of-sequence headers, dual-track (Arabic §0/§1 vs Roman §I/§II) inconsistencies, and depth jumps. Pass max_level to cap depth (e.g. 3 for the top-level skeleton).",
      inputSchema: {
        type: "object",
        properties: {
          path: { type: "string", description: "File to outline. Defaults to .chthonic/SSOT.md." },
          max_level: { type: "number", description: "Maximum header depth to include (1-6). Default 6." },
        },
        required: [],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  const a = (args ?? {}) as Record<string, unknown>;
  const path = typeof a.path === "string" && a.path ? a.path : SSOT_PATH;

  try {
    if (name === "ssot_lint") {
      return { content: [{ type: "text", text: JSON.stringify(runLint(path), null, 2) }] };
    }
    if (name === "ssot_parse_frontier") {
      return { content: [{ type: "text", text: JSON.stringify(parseFrontier(path), null, 2) }] };
    }
    if (name === "ssot_outline") {
      const maxLevel = typeof a.max_level === "number" ? a.max_level : 6;
      const o = outline(path, maxLevel);
      return {
        content: [{ type: "text", text: JSON.stringify({ path, headers: o.length, outline: o }, null, 2) }],
      };
    }
  } catch (e) {
    return { content: [{ type: "text", text: `${name} error: ${String(e)}` }], isError: true };
  }
  return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
});

const transport = new StdioServerTransport();
await server.connect(transport);
