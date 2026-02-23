// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: source-code.test.ts                           ║
// ║ TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE                                                 ║
// ║ Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):                                      ║
// ║   (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════

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
