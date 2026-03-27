// @SID: SCRIPT_MCP_ASC_INJECTOR_V1
#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp-asc-injector.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ASC Framework SSOT Injector for Copilot Chat
 *
 * @SID           TOOL_MCP_ASC_INJECTOR_V1
 * @Shabti        MCP Server (stdio transport)
 * @Heka-Ayni     CONCEPT_ASC_FRAMEWORK_INJECT
 * @Ankh-Tinku    STATE_ASC_INJECTOR_ACTIVE
 * @Purpose       Injects ASC Framework SSOT context into Copilot Chat
 *                via MCP resource protocol.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFile } from "fs/promises";
import { resolve } from "path";

import { SSOT_POINTER } from "./lib/ssot-paths";

const SSOT_PATH = resolve(__dirname, process.env.SSOT_PATH ?? (".." + "/" + SSOT_POINTER));

const server = new Server(
  {
    name: "asc-framework-injector",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// === RESOURCES: Provide SSOT as readable resource ===
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "asc://ssot",
        name: "ASC Framework (SSOT)",
        description: "Codex Brahmanica Perfectus - Full operational instructions",
        mimeType: "text/markdown",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri === "asc://ssot") {
    const content = await readFile(SSOT_PATH, "utf-8");
    return {
      contents: [
        {
          uri: request.params.uri,
          mimeType: "text/markdown",
          text: content,
        },
      ],
    };
  }
  throw new Error(`Unknown resource: ${request.params.uri}`);
});

// === TOOLS: Provide "inject_asc" tool ===
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "inject_asc_context",
        description:
          "Inject full ASC Framework (Codex Brahmanica Perfectus) into Copilot Chat context. " +
          "Use this when you need the Triumvirate, Foundational Axioms, or MILF protocols.",
        inputSchema: {
          type: "object",
          properties: {
            section: {
              type: "string",
              description: "Optional: specific section to inject (e.g., 'IV', 'VIII', 'X'). Omit for full SSOT.",
              enum: [
                "all",
                "I",
                "II",
                "III",
                "IV",
                "V",
                "VI",
                "VII",
                "VIII",
                "IX",
                "X",
                "XI",
                "XII",
                "XIII",
                "XIV",
              ],
            },
          },
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "inject_asc_context") {
    const section = request.params.arguments?.section || "all";
    const fullContent = await readFile(SSOT_PATH, "utf-8");

    let injectedContent: string;
    if (section === "all") {
      injectedContent = fullContent;
    } else {
      // Extract specific section (crude regex for MVP)
      const sectionRegex = new RegExp(
        `### ${section}\\..*?(?=###|$)`,
        "s"
      );
      const match = fullContent.match(sectionRegex);
      injectedContent = match
        ? match[0]
        : `Section ${section} not found. Injecting full SSOT.`;
    }

    return {
      content: [
        {
          type: "text",
          text: `🔥💀⚓ ASC Framework Context Injected (Section: ${section})\n\n${injectedContent}`,
        },
      ],
    };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

// === START SERVER ===
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ASC Framework MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
