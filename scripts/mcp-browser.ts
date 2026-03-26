#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: mcp-browser.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ bun-playwright-poc/src/index.ts
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * MCP Browser Server — Bun-native Chrome automation via bun-cdp
 *
 * @SID           TOOL_MCP_BROWSER_V1
 * @Shabti        MCP Server (stdio transport)
 * @Heka-Ayni     CONCEPT_MCP_BROWSER_CDP
 * @Ankh-Tinku    STATE_MCP_BROWSER_ACTIVE
 * @Purpose       Replaces the dead Playwright MCP entry. Uses raw CDP
 *                over WebSocket (proven working where Playwright's IPC
 *                crashes Bun).
 *
 * @UpstreamReady When Playwright IPC no longer crashes Bun, this server
 *                can be replaced by @playwright/mcp (already in devDeps).
 *                mcp.json config: "command": "bunx", "args": ["@playwright/mcp@latest"]
 *                See: https://github.com/microsoft/playwright-mcp
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { resolve } from "path";
import { writeFile, mkdir } from "fs/promises";

// bun-cdp lives in the sibling poc directory
const BUN_CDP_ROOT = resolve(__dirname, "../bun-playwright-poc/src");

// bun-cdp loaded lazily inside ensureBrowser() to avoid startup crash
// if Chrome/bun-cdp is unavailable.
let _cdpModule: { launchBrowser: any; createPage: any } | null = null;
type BunCDPInstance = any;
type CDPPageInstance = any;

async function loadCDP() {
  if (!_cdpModule) {
    _cdpModule = await import(resolve(BUN_CDP_ROOT, "index.ts"));
  }
  return _cdpModule;
}

// ═══════════════════════════════════════════════════════════════════════════════
// STATE — single browser instance, reused across tool calls
// ═══════════════════════════════════════════════════════════════════════════════

let browser: BunCDPInstance | null = null;
let page: CDPPageInstance | null = null;

async function ensureBrowser(): Promise<{ browser: BunCDPInstance; page: CDPPageInstance }> {
  const cdp = await loadCDP();
  if (!browser || !browser.isConnected()) {
    browser = await cdp.launchBrowser({ headless: true });
    page = await cdp.createPage(browser, "about:blank");
  }
  return { browser: browser!, page: page! };
}

// ═══════════════════════════════════════════════════════════════════════════════
// MCP SERVER
// ═══════════════════════════════════════════════════════════════════════════════

const server = new Server(
  { name: "bun-cdp-browser", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "browser_navigate",
      description:
        "Navigate to a URL and return page title + URL. Launches browser on first call.",
      inputSchema: {
        type: "object" as const,
        properties: {
          url: { type: "string", description: "URL to navigate to" },
        },
        required: ["url"],
      },
    },
    {
      name: "browser_screenshot",
      description:
        "Take a PNG screenshot of the current page. Returns base64-encoded image.",
      inputSchema: {
        type: "object" as const,
        properties: {
          path: {
            type: "string",
            description: "Optional file path to save the screenshot",
          },
        },
        required: [],
      },
    },
    {
      name: "browser_click",
      description: "Click an element matching a CSS selector.",
      inputSchema: {
        type: "object" as const,
        properties: {
          selector: { type: "string", description: "CSS selector" },
        },
        required: ["selector"],
      },
    },
    {
      name: "browser_fill",
      description: "Fill a text input matching a CSS selector.",
      inputSchema: {
        type: "object" as const,
        properties: {
          selector: { type: "string", description: "CSS selector" },
          value: { type: "string", description: "Text to fill" },
        },
        required: ["selector", "value"],
      },
    },
    {
      name: "browser_evaluate",
      description:
        "Evaluate a JavaScript expression in the page context and return the result.",
      inputSchema: {
        type: "object" as const,
        properties: {
          expression: {
            type: "string",
            description: "JavaScript expression to evaluate",
          },
        },
        required: ["expression"],
      },
    },
    {
      name: "browser_text_content",
      description:
        "Get text content of an element matching a CSS selector.",
      inputSchema: {
        type: "object" as const,
        properties: {
          selector: { type: "string", description: "CSS selector" },
        },
        required: ["selector"],
      },
    },
    {
      name: "browser_close",
      description: "Close the browser instance and release resources.",
      inputSchema: {
        type: "object" as const,
        properties: {},
        required: [],
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name } = request.params;
  const args = (request.params.arguments ?? {}) as Record<string, string>;

  try {
    switch (name) {
      case "browser_navigate": {
        const { page: p } = await ensureBrowser();
        await p.goto(args.url);
        const title = await p.title();
        const url = await p.url();
        return {
          content: [
            { type: "text", text: `Navigated to: ${url}\nTitle: ${title}` },
          ],
        };
      }

      case "browser_screenshot": {
        const { page: p } = await ensureBrowser();
        const buf = await p.screenshot({ format: "png" });
        const b64 = Buffer.from(buf).toString("base64");

        if (args.path) {
          const dir = resolve(args.path, "..");
          await mkdir(dir, { recursive: true });
          await writeFile(args.path, Buffer.from(buf));
          return {
            content: [
              { type: "text", text: `Screenshot saved to ${args.path}` },
            ],
          };
        }

        return {
          content: [
            {
              type: "image",
              data: b64,
              mimeType: "image/png",
            },
          ],
        };
      }

      case "browser_click": {
        const { page: p } = await ensureBrowser();
        await p.click(args.selector);
        return {
          content: [
            { type: "text", text: `Clicked: ${args.selector}` },
          ],
        };
      }

      case "browser_fill": {
        const { page: p } = await ensureBrowser();
        await p.fill(args.selector, args.value);
        return {
          content: [
            {
              type: "text",
              text: `Filled ${args.selector} with "${args.value}"`,
            },
          ],
        };
      }

      case "browser_evaluate": {
        const { page: p } = await ensureBrowser();
        const result = await p.evaluate(args.expression);
        return {
          content: [
            {
              type: "text",
              text:
                typeof result === "string"
                  ? result
                  : JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case "browser_text_content": {
        const { page: p } = await ensureBrowser();
        const text = await p.textContent(args.selector);
        return {
          content: [{ type: "text", text: text ?? "(no text content)" }],
        };
      }

      case "browser_close": {
        if (browser) {
          await browser.close();
          browser = null;
          page = null;
        }
        return {
          content: [{ type: "text", text: "Browser closed" }],
        };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      content: [{ type: "text", text: `Error: ${msg}` }],
      isError: true,
    };
  }
});

// Cleanup on exit
process.on("SIGINT", async () => {
  if (browser) await browser.close();
  process.exit(0);
});

// Start
const transport = new StdioServerTransport();
await server.connect(transport);
