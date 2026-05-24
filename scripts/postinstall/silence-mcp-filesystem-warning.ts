#!/usr/bin/env bun
// @SID: TOOL_POSTINSTALL_SILENCE_MCP_FS_V2
// @Type: Postinstall Patch
// @Status: SUPERSEDED by scripts/mcp-filesystem.ts (fileURLToPath root-cause fix)
//
// Original purpose: suppress cosmetic "No valid root directories" noise.
// The root cause (URI percent-encoding of Windows drive letters) is now fixed
// at startup by mcp-filesystem.ts, so this warning never fires.
// Retained per WPTG — converted from CJS to Bun-compatible ESM.

import { existsSync, readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

const target = resolve(
  import.meta.dir,
  "../../node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
);
if (!existsSync(target)) process.exit(0);

const src = readFileSync(target, "utf8");
const patched = src.replace(
  'console.error("No valid root directories provided by client");',
  "// suppressed: VS Code URI-encoding bug — CLI arg roots remain active",
);
if (src !== patched) {
  writeFileSync(target, patched, "utf8");
  console.log(
    "[postinstall] patched mcp-server-filesystem: suppressed URI-encoding noise",
  );
}
