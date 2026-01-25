// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: bundle-size.test.ts                           ║
// ║  TypeScript module: frontend utility                                        ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Spectral Frequency: ORANGE                                                 ║
// ║  Architectural Role: 🔭 THE OBSERVATORY                                      ║
// ╠════════════════════════════════════════════════════════════════════════════╣
// ║  Cross-References (Bidirectional):                                      ║
// ║    (Standalone file - no detected dependencies)                          ║
// ╚════════════════════════════════════════════════════════════════════════════╝

import { test, expect } from "bun:test";
import { statSync } from "fs";

const SIZE_THRESHOLDS = {
  statusbar: 10 * 1024, // 10 KB max
  mandala: 18 * 1024,   // 18 KB max
} as const;

test("statusbar bundle stays under size threshold", () => {
  const size = statSync("extensions/chthonic-statusbar/dist/extension.js").size;
  expect(size).toBeLessThan(SIZE_THRESHOLDS.statusbar);
});

test("mandala bundle stays under size threshold", () => {
  const size = statSync("extensions/chthonic-mandala/dist/extension.js").size;
  expect(size).toBeLessThan(SIZE_THRESHOLDS.mandala);
});

test("combined bundle size is production-acceptable", () => {
  const statusbarSize = statSync("extensions/chthonic-statusbar/dist/extension.js").size;
  const mandalaSize = statSync("extensions/chthonic-mandala/dist/extension.js").size;
  const combined = statusbarSize + mandalaSize;

  expect(combined).toBeLessThan(30 * 1024); // 30 KB combined max
});
