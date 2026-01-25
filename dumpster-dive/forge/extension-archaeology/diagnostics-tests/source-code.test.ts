// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: source-code.test.ts                           ║
// ║  TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

import { test, expect } from "bun:test";
import { readFileSync } from "fs";

test("statusbar extension has UTF-8 enforcement", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );
  expect(src).toContain("PYTHONIOENCODING");
});

test("python regex is correctly escaped", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );

  // Should NOT have double backslashes
  expect(src).not.toContain("/Python\\\\s+");

  // Should have single backslashes in regex
  expect(src).toContain("/Python\\s+");
});

test("dead hedonisticValidation import is removed", () => {
  const src = readFileSync(
    "extensions/chthonic-statusbar/src/extension.ts",
    "utf-8"
  );
  expect(src).not.toContain("hedonisticValidation");
});
