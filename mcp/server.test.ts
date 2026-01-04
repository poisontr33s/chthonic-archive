import { describe, it, expect } from "bun:test";
import { spawn } from "bun";

describe("MCP Server Integration Tests", () => {
  it("should respond to ping with pong", async () => {
    const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
      stdin: "pipe",
      stdout: "pipe",
      stderr: "inherit",
    });

    server.stdin.write(JSON.stringify({ id: 1, method: "ping" }) + "\n");

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(1);
      expect(response.result.pong).toBe(true);
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

    server.stdin.write(JSON.stringify({ id: 2, method: "scan_repository" }) + "\n");

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(2);
      expect(response.result.file_count).toBeGreaterThan(40000);
      expect(response.result.repository).toContain("chthonic-archive");
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
      JSON.stringify({ id: 3, method: "validate_ssot_integrity" }) + "\n"
    );

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(3);
      expect(response.result.status).toBe("valid");
      expect(response.result.hash).toMatch(/^[0-9a-f]{64}$/); // SHA-256 hex
      expect(response.result.size).toBeGreaterThan(300000);
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
        method: "query_dependency_graph",
        params: { query: "test" },
      }) + "\n"
    );

    const decoder = new TextDecoder();
    for await (const chunk of server.stdout) {
      const response = JSON.parse(decoder.decode(chunk));
      expect(response.id).toBe(4);
      expect(response.result.query).toBe("test");
      expect(response.result.note).toContain("Not yet implemented");
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
      expect(response.error.message).toContain("Unknown method");
      server.kill();
      break;
    }
  });
});
