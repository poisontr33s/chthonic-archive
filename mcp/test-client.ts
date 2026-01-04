import { spawn } from "node:child_process";

const server = spawn("bun", ["run", "mcp/server.ts"], {
  stdio: ["pipe", "pipe", "inherit"],
});

const requests = [
  { id: 1, method: "ping" },
  { id: 2, method: "scan_repository" },
  { id: 3, method: "validate_ssot_integrity" },
  { id: 4, method: "query_dependency_graph", params: { query: "test" } },
];

server.stdout?.on("data", (data) => {
  console.log("[Server Response]", data.toString().trim());
});

for (const req of requests) {
  server.stdin?.write(JSON.stringify(req) + "\n");
}

setTimeout(() => {
  server.kill();
  console.log("[Test Client] Server terminated");
}, 2000);
