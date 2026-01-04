// Bun-native spawn for process orchestration
const server = Bun.spawn(["bun", "run", "mcp/server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
});

const requests = [
  { id: 1, method: "ping" },
  { id: 2, method: "scan_repository" },
  { id: 3, method: "validate_ssot_integrity" },
  { id: 4, method: "query_dependency_graph", params: { query: "test" } },
];

// Write all requests immediately
for (const req of requests) {
  server.stdin.write(JSON.stringify(req) + "\n");
}

// Read stdout synchronously with timeout
const decoder = new TextDecoder();
const timeout = setTimeout(() => {
  server.kill();
  console.log("[Test Client] Server terminated after timeout");
  process.exit(0);
}, 3000);

for await (const chunk of server.stdout) {
  const lines = decoder.decode(chunk).trim().split("\n");
  for (const line of lines) {
    if (line) console.log("[Server Response]", line);
  }
}
