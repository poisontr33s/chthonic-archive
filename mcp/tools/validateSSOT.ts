import { join, resolve } from "node:path";

/**
 * Canonicalize text per Section XIV.3:
 * - CRLF→LF normalization
 * - Trim trailing whitespace per line
 * - NFC Unicode normalization
 * - Strip final newline
 */
function canonicalize(text: string): string {
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = text.split("\n").map((line) => line.trimEnd());
  text = lines.join("\n");
  text = text.normalize("NFC");
  return text.trim();
}

export async function validateSSOT() {
  // Find repository root (parent of mcp/)
  const repoRoot = resolve(import.meta.dir, "..", "..");
  const ssotPath = join(repoRoot, ".github", "copilot-instructions.md");

  try {
    const file = Bun.file(ssotPath);
    const content = await file.text();
    const canonical = canonicalize(content);
    
    // Bun-native SHA-256 hashing
    const hasher = new Bun.CryptoHasher("sha256");
    hasher.update(canonical);
    const digest = hasher.digest("hex");

    return {
      status: "valid",
      path: ssotPath,
      size: file.size,
      lines: content.split("\n").length,
      hash: digest,
    };
  } catch (err: any) {
    return {
      status: "error",
      message: err.message,
    };
  }
}
