#!/usr/bin/env bun

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
import { readFileSync, writeFileSync } from "fs";

const distDir = resolve(
  import.meta.dir,
  "../node_modules/@modelcontextprotocol/server-filesystem/dist",
);
const rootsUtilsPath = resolve(distDir, "roots-utils.js");

// Ensure the fileURLToPath fix is present (idempotent, survives bun install)
const src = readFileSync(rootsUtilsPath, "utf-8");
if (!src.includes("fileURLToPath")) {
  writeFileSync(
    rootsUtilsPath,
    "import { fileURLToPath } from 'url';\n" +
      src.replace(
        "const rawPath = rootUri.startsWith('file://') ? rootUri.slice(7) : rootUri;",
        "const rawPath = rootUri.startsWith('file://') ? fileURLToPath(rootUri) : rootUri;",
      ),
  );
}

// Forward CLI args and run the actual server
const root = process.argv.slice(2);
const entry = resolve(distDir, "index.js");
process.argv = [process.argv[0], entry, ...root];
await import(entry);
