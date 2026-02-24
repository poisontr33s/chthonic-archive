// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: source-code.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_SOURCE_CODE_V1 @Shabti Test Script @Purpose Validates statusbar extension legacy bridge routes mapping. */

import { test, expect } from "bun:test";
import { readFileSync } from "fs";

test("statusbar extension maps legacy bridge routes", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );
  expect(src).toContain("const ROUTES: RouteSpec[]");
  expect(src).toContain("chthonic.verifySSO_T");
  expect(src).toContain("chthonic.verifySSOT");
});

test("statusbar bridge dispatches bun host tasks", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );

  expect(src).toContain("terminal.sendText(`bun run ${taskName}`)");
  expect(src).toContain("runArchiveTask('verify:host', output)");
  expect(src).toContain("runArchiveTask('audit:vs2026', output)");
  // Legacy Python/version-detection lane should remain absent in bridge runtime.
  expect(src).not.toContain("PYTHONIOENCODING");
  expect(src).not.toContain("/Python\\s+");
});

test("dead hedonisticValidation import is removed", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );
  expect(src).not.toContain("hedonisticValidation");
});
