#!/usr/bin/env bun

// @SID: SCRIPT_CROSS_CRITIQUE_V1

/**
 * SID: CROSS_CRITIQUE_2026_03_13
 * Purpose: Parallel blind-write + automated merge for SSOT entity sections.
 *
 * Protocol (Option C — hybrid parallel generation, single-pass merge):
 *   Round 1: Opus 4.6 and Sonnet 4.6 blind-write the same section in parallel.
 *   Round 2: A merge call receives both outputs cold and synthesizes the hybrid.
 *
 * AUTH NOTE:
 *   Requires ANTHROPIC_API_KEY (paid API credits, separate from Claude Pro subscription).
 *   If you only have Claude Pro / Copilot subscription, use the in-chat protocol instead:
 *   See .github/instructions/cross-critique-protocol.instructions.md
 *   (1 Explore subagent call, runs entirely within Copilot Chat, no API key needed)
 *
 * Usage:
 *   bun run scripts/cross-critique.ts --section "Curatrix Clitoris" --start 5218 --end 5260
 *   bun run scripts/cross-critique.ts --section "Claudine Salt Wrap" --start 4080 --end 4100 --out critique-output.md
 *   bun run scripts/cross-critique.ts --help
 *
 * Env: ANTHROPIC_API_KEY (required)
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";
import { SSOT_HOLDER } from "./lib/ssot-paths";

// ── CLI args ──────────────────────────────────────────────────────────────────

interface Args {
  section: string;
  start: number;
  end: number;
  ssotPath: string;
  out: string | null;
  opusModel: string;
  sonnetModel: string;
  mergeModel: string;
  maxTokens: number;
  help: boolean;
}

function parseArgs(): Args {
  const args = process.argv.slice(2);
  const defaults: Args = {
    section: "",
    start: 0,
    end: 0,
    ssotPath: path.resolve(import.meta.dir, "..", SSOT_HOLDER),
    out: null,
    opusModel: "claude-opus-4-0",
    sonnetModel: "claude-sonnet-4-5-20250514",
    mergeModel: "claude-opus-4-0",
    maxTokens: 2048,
    help: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case "--section":
        defaults.section = args[++i] ?? "";
        break;
      case "--start":
        defaults.start = parseInt(args[++i] ?? "0", 10);
        break;
      case "--end":
        defaults.end = parseInt(args[++i] ?? "0", 10);
        break;
      case "--ssot":
        defaults.ssotPath = path.resolve(args[++i] ?? "");
        break;
      case "--out":
        defaults.out = args[++i] ?? null;
        break;
      case "--opus-model":
        defaults.opusModel = args[++i] ?? defaults.opusModel;
        break;
      case "--sonnet-model":
        defaults.sonnetModel = args[++i] ?? defaults.sonnetModel;
        break;
      case "--merge-model":
        defaults.mergeModel = args[++i] ?? defaults.mergeModel;
        break;
      case "--max-tokens":
        defaults.maxTokens = parseInt(args[++i] ?? "2048", 10);
        break;
      case "--help":
      case "-h":
        defaults.help = true;
        break;
    }
  }
  return defaults;
}

function printHelp(): void {
  console.log(`
cross-critique.ts — Parallel blind-write + automated merge for SSOT entity sections.

USAGE:
  bun run scripts/cross-critique.ts --section <name> --start <line> --end <line> [options]

REQUIRED:
  --section <name>     Human label for the section being rewritten (e.g. "Curatrix Clitoris")
  --start <line>       1-based start line of SSOT context window
  --end <line>         1-based end line of SSOT context window

OPTIONS:
  --ssot <path>        Path to SSOT file (default: ${SSOT_HOLDER})
  --out <path>         Write output to file instead of stdout
  --opus-model <id>    Opus model ID (default: claude-opus-4-0)
  --sonnet-model <id>  Sonnet model ID (default: claude-sonnet-4-5-20250514)
  --merge-model <id>   Model for merge step (default: claude-opus-4-0)
  --max-tokens <n>     Max output tokens per call (default: 2048)
  -h, --help           Show this help
  `);
}

// ── Anthropic API ─────────────────────────────────────────────────────────────

const ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages";

async function callAnthropic(
  model: string,
  systemPrompt: string,
  userPrompt: string,
  maxTokens: number,
): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY not set in environment");
  }

  const response = await fetch(ANTHROPIC_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Anthropic API error ${response.status}: ${body}`);
  }

  const data = (await response.json()) as {
    content: Array<{ type: string; text?: string }>;
  };

  const text = data.content
    .filter((block) => block.type === "text" && block.text)
    .map((block) => block.text!)
    .join("\n");

  return text;
}

// ── Prompts ───────────────────────────────────────────────────────────────────

function blindWriteSystem(sectionName: string): string {
  return `You are rewriting a section of the SSOT (Single Source of Truth) for a literary entity profile archive.

CONSTRAINTS:
- Archival register only — no lyric drift, no YA softening, no purple prose
- Must include an Ornamental Necessity (ON) tag with FA⁵ designation
- Body prose target: 100-150 words
- The section must be self-contained and voice-consistent with the entity's profile
- Do NOT use placeholder phrases like "most concentrated nerve cluster" or other templates
- Each entity has a unique vocabulary domain — respect it

OUTPUT FORMAT:
Return ONLY the rewritten section content (markdown). No commentary, no preamble, no "here is my version".`;
}

function blindWriteUser(sectionName: string, context: string): string {
  return `Rewrite the section "${sectionName}" based on the following SSOT context window.
The context includes the entity's flanking sections for voice/register reference.
Your output replaces the named section only — do not rewrite flanking content.

--- SSOT CONTEXT ---
${context}
--- END CONTEXT ---

Write the "${sectionName}" section now.`;
}

function mergeSystem(): string {
  return `You are a literary editor merging two independently written versions of the same SSOT section.

Your job:
1. Identify the strongest elements of each version (opening, middle, closing, ON tag, register, metaphor, economy)
2. Produce a HYBRID that takes the best from each
3. After the hybrid, provide a brief MERGE NOTES section explaining which lines came from which version and why

CONSTRAINTS:
- Archival register only
- Must include Ornamental Necessity (ON) tag with FA⁵
- Body prose: 100-150 words
- The hybrid must read as a single coherent piece, not a stitched collage

OUTPUT FORMAT:
## Hybrid Version
[the merged section]

## Merge Notes
[brief explanation of sourcing decisions]`;
}

function mergeUser(sectionName: string, versionA: string, versionB: string, context: string): string {
  return `Merge the two blind-written versions of "${sectionName}" below.
Both were written independently with identical context. Neither author saw the other's work.

--- ENTITY CONTEXT (for register/voice reference) ---
${context}
--- END CONTEXT ---

--- VERSION A (Opus) ---
${versionA}
--- END VERSION A ---

--- VERSION B (Sonnet) ---
${versionB}
--- END VERSION B ---

Produce the hybrid version and merge notes now.`;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = parseArgs();

  if (args.help) {
    printHelp();
    process.exit(0);
  }

  if (!args.section || !args.start || !args.end) {
    console.error("ERROR: --section, --start, and --end are required. Use --help for usage.");
    process.exit(1);
  }

  if (!existsSync(args.ssotPath)) {
    console.error(`ERROR: SSOT file not found: ${args.ssotPath}`);
    process.exit(1);
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("ERROR: ANTHROPIC_API_KEY not set in environment.");
    process.exit(1);
  }

  // Read context window
  const lines = readFileSync(args.ssotPath, "utf-8").split("\n");
  const contextLines = lines.slice(args.start - 1, args.end);
  const context = contextLines.join("\n");

  console.log(`\n╔══════════════════════════════════════════════════════════════╗`);
  console.log(`║  CROSS-CRITIQUE: ${args.section.padEnd(42)} ║`);
  console.log(`╠══════════════════════════════════════════════════════════════╣`);
  console.log(`║  SSOT lines: ${args.start}-${args.end} (${contextLines.length} lines)`.padEnd(63) + `║`);
  console.log(`║  Opus model:  ${args.opusModel}`.padEnd(63) + `║`);
  console.log(`║  Sonnet model: ${args.sonnetModel}`.padEnd(63) + `║`);
  console.log(`║  Merge model:  ${args.mergeModel}`.padEnd(63) + `║`);
  console.log(`╚══════════════════════════════════════════════════════════════╝\n`);

  // ── Round 1: Parallel blind-writes ──────────────────────────────────────
  console.log("⏳ Round 1: Parallel blind-writes (Opus + Sonnet)...");
  const t1 = performance.now();

  const [opusVersion, sonnetVersion] = await Promise.all([
    callAnthropic(
      args.opusModel,
      blindWriteSystem(args.section),
      blindWriteUser(args.section, context),
      args.maxTokens,
    ),
    callAnthropic(
      args.sonnetModel,
      blindWriteSystem(args.section),
      blindWriteUser(args.section, context),
      args.maxTokens,
    ),
  ]);

  const t1Elapsed = ((performance.now() - t1) / 1000).toFixed(1);
  console.log(`✅ Round 1 complete (${t1Elapsed}s)\n`);

  // ── Round 2: Automated merge ────────────────────────────────────────────
  console.log("⏳ Round 2: Automated merge...");
  const t2 = performance.now();

  const hybrid = await callAnthropic(
    args.mergeModel,
    mergeSystem(),
    mergeUser(args.section, opusVersion, sonnetVersion, context),
    args.maxTokens,
  );

  const t2Elapsed = ((performance.now() - t2) / 1000).toFixed(1);
  console.log(`✅ Round 2 complete (${t2Elapsed}s)\n`);

  // ── Output ──────────────────────────────────────────────────────────────
  const totalElapsed = ((performance.now() - t1) / 1000).toFixed(1);

  const output = `# Cross-Critique: ${args.section}
> Generated: ${new Date().toISOString()}
> SSOT lines: ${args.start}-${args.end}
> Opus model: ${args.opusModel} | Sonnet model: ${args.sonnetModel} | Merge model: ${args.mergeModel}
> Total time: ${totalElapsed}s (Round 1: ${t1Elapsed}s, Round 2: ${t2Elapsed}s)

---

## Version A — Opus (${args.opusModel})

${opusVersion}

---

## Version B — Sonnet (${args.sonnetModel})

${sonnetVersion}

---

${hybrid}
`;

  if (args.out) {
    writeFileSync(args.out, output, "utf-8");
    console.log(`📝 Written to: ${args.out}`);
  } else {
    console.log(output);
  }

  console.log(`\n⏱️  Total wall-clock: ${totalElapsed}s`);
}

main().catch((err) => {
  console.error("FATAL:", err instanceof Error ? err.message : err);
  process.exit(1);
});
