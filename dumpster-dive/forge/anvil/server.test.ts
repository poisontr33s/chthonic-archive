// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: server.test.ts
// ║ MCP client integration - Observatory communication layer
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE
// ║ Architectural Role: 🔭 THE OBSERVATORY
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║  (Standalone file - no detected dependencies)
// ╚════════════════════════════════════════════════════════════════════════════

import { describe, it, expect } from "bun:test";
import { spawn } from "bun";

describe("MCP Server Integration Tests", () => {
  it("should respond to ping with pong", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(JSON.stringify({ id: 1, method: "tools/call", params: { name: "ping" } }) + "\n");

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(1);
      const content = JSON.parse(response.result.content[0].text);
      expect(content.pong).toBe(true);
      server.kill();
      break;
    }
  });

  it("should scan repository and return file count", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(JSON.stringify({ id: 2, method: "tools/call", params: { name: "scan_repository" } }) + "\n");

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(2);
      const content = JSON.parse(response.result.content[0].text);
      expect(content.file_count).toBeGreaterThan(1000);
      expect(content.repository).toContain("chthonic-archive");
      server.kill();
      break;
    }
  });

  it("should validate SSOT with SHA-256 hash", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(
      JSON.stringify({ id: 3, method: "tools/call", params: { name: "validate_ssot_integrity" } }) + "\n"
    );

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(3);
      const content = JSON.parse(response.result.content[0].text);
      expect(content.status).toBe("valid");
      expect(content.hash).toMatch(/^[0-9a-f]{64}$/); // SHA-256 hex
      expect(content.size).toBeGreaterThan(10000);
      server.kill();
      break;
    }
  });

  it("should return stub response for dependency graph query", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(
      JSON.stringify({
        id: 4,
        method: "tools/call",
        params: { name: "query_dependency_graph", arguments: { query: "stats" } },
      }) + "\n"
    );

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(4);
      expect(response.result.content[0].text).toBeDefined();
      server.kill();
      break;
    }
  });

  it("should reject unknown methods with error response", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(
      JSON.stringify({ id: 5, method: "unknown_method" }) + "\n"
    );

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(5);
      expect(response.error).toBeDefined();
      expect(response.error.message).toContain("Method not found");
      server.kill();
      break;
    }
  });
});
