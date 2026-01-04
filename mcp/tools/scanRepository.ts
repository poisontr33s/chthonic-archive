import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";

export async function scanRepository() {
  const files: { path: string; size: number }[] = [];

  async function walk(dir: string) {
    const entries = await readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = join(dir, entry.name);

      if (entry.name === "node_modules" || entry.name === ".git") continue;

      if (entry.isDirectory()) {
        await walk(fullPath);
      } else {
        const stats = await stat(fullPath);
        files.push({ path: fullPath, size: stats.size });
      }
    }
  }

  await walk(process.cwd());

  return {
    repository: process.cwd(),
    file_count: files.length,
    files: files.slice(0, 50), // Limit to 50 for brevity
  };
}
