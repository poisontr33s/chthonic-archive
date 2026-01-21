// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: scanRepository.ts                             ║
// ║  MCP client integration - Observatory communication layer                   ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║  Dependencies (I rely on):                                               ║
// ║    ├─► mcp\server.ts                                                     ║
// ║    ├─► mcp\smoke-suite.ts                                                ║
// ╚════════════════════════════════════════════════════════════════════════════╝

import { readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";

export async function scanRepository() {
  // Find repository root (parent of mcp/)
  const repoRoot = resolve(import.meta.dir, "..", "..");
  const files: { path: string; size: number }[] = [];

  async function walk(dir: string) {
    const entries = await readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = join(dir, entry.name);

      if (entry.name === "node_modules" || entry.name === ".git" || entry.name === "target") continue;

      if (entry.isDirectory()) {
        await walk(fullPath);
      } else {
        const stats = await stat(fullPath);
        files.push({ path: fullPath, size: stats.size });
      }
    }
  }

  await walk(repoRoot);

  return {
    repository: repoRoot,
    file_count: files.length,
    files: files.slice(0, 50), // Limit to 50 for brevity
  };
}
