#!/usr/bin/env bun

// @SID: SCRIPT_MCP_FILESYSTEM_V1

/**
 * MCP Filesystem Server launcher — patches upstream Windows file URI bug
 * then runs the server. The patch survives `bun install` because this script
 * re-applies it on every startup before importing the server entry point.
 *
 * Bug: roots-utils.js uses rootUri.slice(7) instead of fileURLToPath(),
 * which fails to decode percent-encoded Windows paths (file:///c%3A/...).
 * This causes VS Code client roots to be rejected, wiping CLI-arg roots.
 */

import { resolve } from "path";
import { existsSync, readFileSync, writeFileSync } from "fs";

const distDir = resolve(
  import.meta.dir,
  "../node_modules/@modelcontextprotocol/server-filesystem/dist",
);
const rootsUtilsPath = resolve(distDir, "roots-utils.js");

if (!existsSync(distDir)) {
  console.error(`[mcp-filesystem] FATAL: server-filesystem not installed. Run: bun install`);
  process.exit(1);
}

// Package version assertion — detects upstream changes that may invalidate the patch
try {
  const pkgJson = JSON.parse(readFileSync(resolve(distDir, "../package.json"), "utf-8"));
  if (pkgJson.name !== "@modelcontextprotocol/server-filesystem") {
    console.warn(`[mcp-filesystem] Warning: unexpected package name '${pkgJson.name}' at server-filesystem location`);
  }
} catch {
  // Non-fatal: version check failure doesn't block server startup
}

// Ensure the fileURLToPath fix is present (idempotent, survives bun install)
try {
  const src = readFileSync(rootsUtilsPath, "utf-8");
  if (!src.includes("// chthonic-patch") && !src.includes("fileURLToPath")) {
    writeFileSync(
      rootsUtilsPath,
      "// chthonic-patch\nimport { fileURLToPath } from 'url';\n" +
        src.replace(
          "const rawPath = rootUri.startsWith('file://') ? rootUri.slice(7) : rootUri;",
          "const rawPath = rootUri.startsWith('file://') ? fileURLToPath(rootUri) : rootUri;",
        ),
    );
  }
} catch (e) {
  console.error(`[mcp-filesystem] Warning: could not apply fileURLToPath patch: ${e instanceof Error ? e.message : String(e)}`);
  // Non-fatal: proceed without patch; Windows paths may fail for percent-encoded URIs
}

// Forward CLI args and run the actual server
const root = process.argv.slice(2);
const entry = resolve(distDir, "index.js");
process.argv = [process.argv[0], entry, ...root];
await import(entry);
