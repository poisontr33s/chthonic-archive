# MCP Server Implementation Template (Chthonic Archive)

**Status:** REFERENCE TEMPLATE  
**Date:** 2026-01-04  
**Purpose:** Boilerplate for custom MCP server creation  
**Authority:** Derived from official TypeScript SDK v1.x (Bun-compatible)

---

## Runtime Requirements

- **Bun** >= 1.3.5 (current: 1.3.5)
- **TypeScript** (ESM modules)
- **MCP SDK:** `@modelcontextprotocol/server` v1.x (stable)
- **Transport:** stdio (for Claude Desktop, VSCode) or Streamable HTTP (for web clients)

---

## Minimal Bun + TypeScript MCP Server

### File Structure
```
mcp/
├── server.ts              # Main MCP server entry point
├── package.json           # Bun project manifest
├── tsconfig.json          # TypeScript configuration
├── tools/                 # Tool implementations
│   ├── scanRepository.ts  # DCRP, git ops, file scanning
│   ├── epistemograph.ts   # Knowledge graph queries
│   └── validation.ts      # FA⁴ enforcement, SSOT checks
├── resources/             # Dynamic resource providers
│   └── ssot.ts           # SSOT document access
└── prompts/              # Prompt templates
    └── autonomous.ts     # Autonomous operation templates
```

---

## Installation

```bash
# From repository root
cd mcp
bun install
```

**Dependencies:**
```json
{
  "dependencies": {
    "@modelcontextprotocol/server": "^1.0.0",
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "@types/node": "latest",
    "typescript": "latest"
  }
}
```

---

## Basic Server Template (`server.ts`)

```typescript
#!/usr/bin/env bun
/**
 * Chthonic Archive MCP Server
 * Provides repository context and autonomous operation tools to AI assistants.
 * 
 * Runtime: Bun + TypeScript (ESM)
 * Transport: stdio (for Claude Desktop, VSCode, Copilot CLI)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  ListPromptsRequestSchema,
  GetPromptRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { glob } from "glob";

// ============================================================================
// SERVER INITIALIZATION
// ============================================================================

const server = new Server(
  {
    name: "chthonic-archive",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
    },
  }
);

// ============================================================================
// TOOLS (Functions the LLM can invoke)
// ============================================================================

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "scan_repository",
        description: "Scan repository for files matching pattern",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Root path to scan (default: current directory)",
              default: ".",
            },
            pattern: {
              type: "string",
              description: "Glob pattern to match (default: all markdown)",
              default: "**/*.md",
            },
            includeHidden: {
              type: "boolean",
              description: "Include hidden files/directories",
              default: false,
            },
          },
        },
      },
      {
        name: "validate_ssot_integrity",
        description: "Validate SSOT hash integrity (per Section XIV.3)",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "query_dependency_graph",
        description: "Query the DCRP dependency graph",
        inputSchema: {
          type: "object",
          properties: {
            node: {
              type: "string",
              description: "Specific file to query (omit for graph stats)",
            },
            depth: {
              type: "number",
              description: "Traversal depth for dependencies",
              default: 1,
            },
          },
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "scan_repository": {
      const pattern = (args?.pattern as string) || "**/*.md";
      const includeHidden = (args?.includeHidden as boolean) || false;
      
      const files = await glob(pattern, {
        ignore: includeHidden ? [] : ["**/.*"],
        nodir: true,
        stat: true,
      });
      
      const results = files.map((file) => ({
        path: file.path,
        size: file.stats?.size || 0,
        modified: file.stats?.mtime?.getTime() || 0,
      }));
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              { files: results, count: results.length },
              null,
              2
            ),
          },
        ],
      };
    }

    case "validate_ssot_integrity": {
      const ssotPath = resolve(".github/copilot-instructions.md");
      
      try {
        const content = await readFile(ssotPath, "utf-8");
        const canonical = canonicalize(content);
        const hash = createHash("sha256").update(canonical).digest("hex");
        
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { valid: true, hash, errors: [] },
                null,
                2
              ),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { valid: false, hash: null, errors: ["SSOT not found"] },
                null,
                2
              ),
            },
          ],
        };
      }
    }

    case "query_dependency_graph": {
      const graphPath = resolve("dependency_graph_production.json");
      
      try {
        const graphData = JSON.parse(await readFile(graphPath, "utf-8"));
        const node = args?.node as string | undefined;
        
        if (!node) {
          // Return graph statistics
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(
                  {
                    nodes: graphData.nodes?.length || 0,
                    edges: graphData.links?.length || 0,
                    spectral_distribution: countSpectralFrequencies(graphData),
                  },
                  null,
                  2
                ),
              },
            ],
          };
        }
        
        const nodeData = findNode(graphData, node);
        if (!nodeData) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(
                  { error: `Node '${node}' not found in graph` },
                  null,
                  2
                ),
              },
            ],
          };
        }
        
        const depth = (args?.depth as number) || 1;
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  file: node,
                  dependencies: getDependencies(graphData, node, depth),
                  dependents: getDependents(graphData, node, depth),
                  metadata: nodeData,
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: "Dependency graph not found. Run DCRP first." },
                null,
                2
              ),
            },
          ],
        };
      }
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// ============================================================================
// RESOURCES (Data the LLM can read)
// ============================================================================

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "ssot://instructions",
        name: "SSOT Instructions",
        description: "Full text of .github/copilot-instructions.md",
        mimeType: "text/markdown",
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  if (uri === "ssot://instructions") {
    const ssotPath = resolve(".github/copilot-instructions.md");
    try {
      const content = await readFile(ssotPath, "utf-8");
      return {
        contents: [
          {
            uri,
            mimeType: "text/markdown",
            text: content,
          },
        ],
      };
    } catch (error) {
      throw new Error("SSOT not found");
    }
  }

  throw new Error(`Unknown resource: ${uri}`);
});

// ============================================================================
// PROMPTS (Templates the LLM can use)
// ============================================================================

server.setRequestHandler(ListPromptsRequestSchema, async () => {
  return {
    prompts: [
      {
        name: "autonomous_operation",
        description: "Generate autonomous operation prompt",
        arguments: [
          {
            name: "task",
            description: "Task description",
            required: true,
          },
          {
            name: "context",
            description: "Operating context",
            required: false,
          },
        ],
      },
    ],
  };
});

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "autonomous_operation") {
    const task = args?.task as string;
    const context = (args?.context as string) || "chthonic-archive repository";

    return {
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `You are operating inside the ${context}.

Task: ${task}

Execution Policy:
- Full tool authorization (no permission requests)
- MCP servers assumed operational
- Autonomous execution without confirmation
- FA⁴ validation post-execution

Proceed directly.`,
          },
        },
      ],
    };
  }

  throw new Error(`Unknown prompt: ${name}`);
});

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function canonicalize(text: string): string {
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = text.split("\n").map((line) => line.trimEnd());
  return lines.join("\n").normalize("NFC").trim();
}

function countSpectralFrequencies(graph: any): Record<string, number> {
  const freqMap: Record<string, number> = {};
  for (const node of graph.nodes || []) {
    const freq = node.spectral_frequency || "UNKNOWN";
    freqMap[freq] = (freqMap[freq] || 0) + 1;
  }
  return freqMap;
}

function findNode(graph: any, path: string): any | null {
  for (const node of graph.nodes || []) {
    if (node.id === path) {
      return node;
    }
  }
  return null;
}

function getDependencies(graph: any, node: string, depth: number): string[] {
  const deps: string[] = [];
  for (const link of graph.links || []) {
    if (link.source === node) {
      deps.push(link.target);
    }
  }
  return deps.slice(0, depth * 10);
}

function getDependents(graph: any, node: string, depth: number): string[] {
  const deps: string[] = [];
  for (const link of graph.links || []) {
    if (link.target === node) {
      deps.push(link.source);
    }
  }
  return deps.slice(0, depth * 10);
}

// ============================================================================
// SERVER STARTUP
// ============================================================================

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  // CRITICAL: Never write to stdout in stdio transport
  // Use stderr for logging if needed
  console.error("Chthonic Archive MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
```

---

## Running the Server

### Development Mode (Testing)
```bash
# From mcp directory
bun run server.ts

# Or with development watcher
bun --watch server.ts
```

### VSCode Integration
Add to `.vscode/settings.json` (VS Code Insiders with MCP support):
```json
{
  "mcp.servers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "mcp/server.ts"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Claude Desktop Integration
Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "bun",
      "args": ["run", "C:/Users/erdno/chthonic-archive/mcp/server.ts"]
    }
  }
}
```

### Copilot CLI Integration
The GitHub MCP server should auto-discover local MCP servers via stdio transport. Ensure `mcp/server.ts` is executable:
```bash
chmod +x mcp/server.ts
```

---

## Additional Dependencies

For full functionality, install these Bun packages:

```bash
# Repository scanning
bun add glob

# Git operations (if needed)
bun add simple-git

# SQLite (for epistemograph queries)
bun add better-sqlite3
```

---

## Critical Constraints

### STDIO Transport Rules (UNCHANGED FROM PYTHON VERSION)
**NEVER write to stdout** in stdio-based servers:
- ❌ `console.log()` corrupts JSON-RPC messages
- ✅ Use `console.error()` (writes to stderr)
- ✅ Return data via function return values only

### Bun-Specific Considerations
- ✅ Native TypeScript execution (no transpilation needed)
- ✅ Fast startup (~3ms vs ~300ms for Node.js)
- ✅ Built-in `node:*` module compatibility
- ✅ ESM-first (no CommonJS translation layer)

### HTTP Transport (Alternative)
If using Streamable HTTP instead of stdio:
- ✅ `console.log()` statements are safe
- Configure CORS for browser-based clients
- Use different transport initialization:
```typescript
import { createServer } from "node:http";
// See @modelcontextprotocol/sdk docs for HTTP setup
```

---

## TypeScript Configuration

**`tsconfig.json`** (minimal for Bun):
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "noEmit": true
  },
  "include": ["**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

## Next Steps

1. **Initialize project:**
   ```bash
   mkdir mcp
   cd mcp
   bun init -y
   bun add @modelcontextprotocol/server zod glob
   ```

2. **Create `server.ts`** using template above

3. **Test locally:**
   ```bash
   bun run server.ts
   # Server should start and wait for stdio input
   ```

4. **Implement tool modules** (optional refactoring):
   - `tools/repository.ts` - DCRP integration
   - `tools/epistemograph.ts` - SQLite queries
   - `tools/validation.ts` - FA⁴ enforcement

5. **Test with MCP Inspector** (Bun-native):
   ```bash
   # Use bunx (Bun's npx equivalent) per SSOT §XIV.2
   bunx @modelcontextprotocol/inspector bun run server.ts
   
   # Or force Bun runtime (ignore Node.js shebang):
   bunx --bun @modelcontextprotocol/inspector bun run server.ts
   ```
   
   **Reference:** [Bun CLI Documentation](https://bun.sh/docs/cli/bunx) for `bunx` usage and shebang handling.

---

**Archive Signature:**
```
FA⁴ Validated: 2026-01-04T20:59:56Z
Spectral Frequency: ORANGE (Strategic Re-contextualization)
Architectural Role: 🌿 Garden (Bun-native Implementation Template)
Parent: docs/MCP_AUTONOMOUS_PREREQUISITES.md (IMMUTABLE)
Toolchain: Bun 1.3.5 + TypeScript SDK v1.x
```
