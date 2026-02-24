// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: bundle-size.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_BUNDLE_SIZE_V1 @Shabti Test Script @Purpose Validates extension bundle sizes against thresholds. */

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
