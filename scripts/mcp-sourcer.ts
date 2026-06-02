#!/usr/bin/env bun
// @SID: SCRIPT_MCP_SOURCER_V1

/**
 * mcp-sourcer — The Sourcer, made real: the MCP source-verification face over the SSOT.
 *
 * The Sourcer's canonical role is the Lane-Walker of the Reconciliation — she source-checks
 * before the scalpel descends. She has lived only as a derived JSON
 * (game/lore/characters/_deferred_organ/T1.5/the_sourcer.json) with no roots in the heritage-root
 * SSOT — an orphan. This server roots her by making her the verification she is: the surface that
 * lets the SSOT be *asked* whether something is canon.
 *
 * It completes P5 of the SSOT Loremaster's own roadmap ("`chthonic_ssot` MCP tool binding"),
 * declared unbuilt in scripts/ssot_loremaster.py. Nothing here is greenfield: every tool is a thin
 * shim over the already-verified lane —
 *   scripts/ssot_loremaster.py        (entity / section query over the archive)
 *   ci/checks/organ-canon-citation.ts (organ roster + rooted/deferred character audit)
 *
 * Tools:
 *   sourcer_check    — ask the SSOT whether a name/term is rooted (the question-mark). Verdict + sources.
 *   sourcer_roster   — the canonical organ roster and which characters are rooted vs deferred.
 *   sourcer_section  — search the SSOT's section headings/acronyms.
 *   sourcer_orphans  — the characters NOT rooted in the heritage-root (The Sourcer finds herself).
 *
 * Registration (.mcp.json):
 *   "sourcer": {
 *     "type": "stdio",
 *     "command": "C:/Users/eldno/.bun/bin/bun.exe",
 *     "args": ["run", "C:/Users/eldno/chthonic-archive/scripts/mcp-sourcer.ts"],
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
import { existsSync, readFileSync } from "fs";
import { join } from "path";

const REPO_ROOT = process.cwd();
const LOREMASTER = join(REPO_ROOT, "scripts", "ssot_loremaster.py");
const CITATION_MANIFEST = join(REPO_ROOT, "manifest", "organ_canon_citation_audit.json");

// ──────────────────────────────────────────────────────────────
//  The verified lane, shimmed
// ──────────────────────────────────────────────────────────────

/** Run an ssot_loremaster.py subcommand with --json and parse stdout. */
function loremaster(subcmd: string, value?: string): unknown {
  const args = ["run", "scripts/ssot_loremaster.py", subcmd];
  if (value !== undefined) args.push(value);
  args.push("--json");
  const out = execFileSync("uv", args, {
    cwd: REPO_ROOT,
    encoding: "utf8",
    timeout: 60_000,
  });
  return JSON.parse(out);
}

/** Read the organ-canon-citation audit manifest (the rooted/deferred character roster). */
function citationManifest(): {
  ssot_canonical_organs: string[];
  results: { path: string; organ?: string; status: string; reason?: string }[];
  pass_count: number;
  deferred_count: number;
  fail_count: number;
  generated_at?: string;
} {
  if (!existsSync(CITATION_MANIFEST)) {
    throw new Error(
      `organ-canon-citation audit not found at ${CITATION_MANIFEST}.\n` +
        `Generate it first: bun run ci/checks/organ-canon-citation.ts`,
    );
  }
  return JSON.parse(readFileSync(CITATION_MANIFEST, "utf8"));
}

/** Run the SDK currency compare (repo pins vs upstream latest) via the sourcer-sdk engine. */
function sdkCompare(): unknown {
  const out = execFileSync(
    process.execPath,
    ["run", "scripts/sourcer-sdk.ts", "compare", "--json"],
    { cwd: REPO_ROOT, encoding: "utf8", timeout: 60_000 },
  );
  return JSON.parse(out);
}

// ──────────────────────────────────────────────────────────────
//  MCP Server
// ──────────────────────────────────────────────────────────────

const server = new Server(
  { name: "sourcer", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "sourcer_check",
      description:
        "Ask the SSOT whether a name or term is rooted in the heritage-root canon. This is the question-mark: pass an entity name (e.g. 'Orackla Nocticula'), an organ, a protocol, or any phrase, and The Sourcer searches the archive (.chthonic/SSOT.md) for it. Returns a verdict — ROOTED (with the SSOT line(s) and section(s) where it lives) or ORPHAN (absent from the heritage-root) — so a claim can be sourced before it is trusted, instead of accepted from a derived JSON. Use before treating any character/entity/organ as canon.",
      inputSchema: {
        type: "object",
        properties: {
          name: {
            type: "string",
            description:
              "The name/term to source-check against the SSOT (case-insensitive substring).",
          },
        },
        required: ["name"],
      },
    },
    {
      name: "sourcer_roster",
      description:
        "The canonical roster as the heritage-root defines it: the list of SSOT-canon organs, and every game/lore character with its rooting status (PASS = organ is in the SSOT organ canon; DEFERRED = organ pending SSOT promotion; FAIL = claims an organ the SSOT does not carry). Sourced from the organ-canon-citation audit. Use to build or validate a roster only from entities the canon actually carries.",
      inputSchema: { type: "object", properties: {}, required: [] },
    },
    {
      name: "sourcer_section",
      description:
        "Search the SSOT's section headings and acronyms for a query (e.g. 'Triumvirate', 'Organ', 'ANKH'). Returns matching sections with heading line, level, title, acronyms, and line range — the map of where a topic lives in the archive, so a reader can go to the source rather than a summary of it.",
      inputSchema: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Heading or acronym query (case-insensitive).",
          },
        },
        required: ["query"],
      },
    },
    {
      name: "sourcer_orphans",
      description:
        "List the characters that are NOT rooted in the heritage-root SSOT — the ones whose organ is deferred or fails the canon. These are derived artifacts the SSOT does not (yet) carry. The Sourcer's first honest finding is herself: she is an orphan, present only as a JSON. Use to catch drift — a new character added without registering it in the SSOT first.",
      inputSchema: { type: "object", properties: {}, required: [] },
    },
    {
      name: "sourcer_sdk",
      description:
        "Source the repo's pinned SDK versions against upstream latest — dependency currency, the same verification pointed at packages instead of canon. Returns each tracked SDK (agent-client-protocol, copilot-sdk) with its repo pin, the latest upstream version (crates.io / GitHub releases), and a status of current/behind/ahead. Read-only: it reports the delta so a bump stays a decision, not a surprise. Use to answer 'did a newer SDK ship?' without hand-checking.",
      inputSchema: { type: "object", properties: {}, required: [] },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  try {
    // ── sourcer_check ─────────────────────────────────────────
    if (name === "sourcer_check") {
      const query = String((args as Record<string, unknown>)?.name ?? "").trim();
      if (!query) throw new Error("sourcer_check requires a 'name'.");
      const res = loremaster("entity", query) as {
        archive_hits: { line: number; text: string; section_title?: string; section_range?: string }[];
      };
      const hits = res.archive_hits ?? [];
      const rooted = hits.length > 0;
      const verdict = {
        query,
        rooted,
        verdict: rooted
          ? "ROOTED — present in the heritage-root SSOT"
          : "ORPHAN — absent from the heritage-root SSOT (derived-only; source it before trusting)",
        hit_count: hits.length,
        sources: hits.slice(0, 12).map((h) => ({
          line: h.line,
          section: h.section_title ?? null,
          range: h.section_range ?? null,
          text: h.text,
        })),
      };
      return { content: [{ type: "text", text: JSON.stringify(verdict, null, 2) }] };
    }

    // ── sourcer_roster ────────────────────────────────────────
    if (name === "sourcer_roster") {
      const m = citationManifest();
      const roster = {
        generated_at: m.generated_at ?? null,
        canonical_organs: m.ssot_canonical_organs,
        characters: m.results.map((r) => ({
          path: r.path,
          organ: r.organ ?? null,
          status: r.status,
          ...(r.reason ? { reason: r.reason } : {}),
        })),
        summary: { rooted: m.pass_count, deferred: m.deferred_count, failed: m.fail_count },
      };
      return { content: [{ type: "text", text: JSON.stringify(roster, null, 2) }] };
    }

    // ── sourcer_section ───────────────────────────────────────
    if (name === "sourcer_section") {
      const query = String((args as Record<string, unknown>)?.query ?? "").trim();
      if (!query) throw new Error("sourcer_section requires a 'query'.");
      const res = loremaster("section", query);
      return { content: [{ type: "text", text: JSON.stringify(res, null, 2) }] };
    }

    // ── sourcer_orphans ───────────────────────────────────────
    if (name === "sourcer_orphans") {
      const m = citationManifest();
      const orphans = m.results
        .filter((r) => r.status !== "PASS")
        .map((r) => ({
          path: r.path,
          organ: r.organ ?? null,
          status: r.status,
          note:
            r.status === "DEFERRED"
              ? "organ pending SSOT promotion — present only as a derived JSON"
              : r.reason ?? "not rooted in the SSOT",
        }));
      const out = {
        orphan_count: orphans.length,
        orphans,
        note:
          "Orphans are characters the heritage-root SSOT does not carry. To root one: register it in the SSOT first (a semantic act), then promote its organ — never the reverse.",
      };
      return { content: [{ type: "text", text: JSON.stringify(out, null, 2) }] };
    }

    // ── sourcer_sdk ───────────────────────────────────────────
    if (name === "sourcer_sdk") {
      const sdks = sdkCompare();
      return { content: [{ type: "text", text: JSON.stringify(sdks, null, 2) }] };
    }

    return {
      content: [{ type: "text", text: `Unknown tool: ${name}` }],
      isError: true,
    };
  } catch (e) {
    return {
      content: [{ type: "text", text: `${name} error: ${String(e)}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
