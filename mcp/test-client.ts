// Bun-native spawn for process orchestration
const server = Bun.spawn(["bun", "run", "./server.ts"], {
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  cwd: import.meta.dir,
});

const requests = [
  { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "test-client", version: "1.0" } } },
  { jsonrpc: "2.0", id: 2, method: "tools/list" },
  { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "ping", arguments: {} } },
  { jsonrpc: "2.0", id: 4, method: "tools/call", params: { name: "scan_repository", arguments: {} } },
  { jsonrpc: "2.0", id: 5, method: "tools/call", params: { name: "validate_ssot_integrity", arguments: {} } },
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
