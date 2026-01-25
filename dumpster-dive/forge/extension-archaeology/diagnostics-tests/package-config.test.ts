// ╔════════════════════════════════════════════════════════════════════════════╗
// ║  THE DECORATOR'S BLESSING: package-config.test.ts                        ║
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

test("statusbar package.json has production config", () => {
  const pkg = JSON.parse(
    readFileSync("extensions/chthonic-statusbar/package.json", "utf-8")
  );

  expect(pkg.sideEffects).toBe(false);
  expect(pkg.bun?.treeShaking).toBe(true);
  expect(pkg.bun?.minify).toBe(true);
  expect(pkg.bun?.define?.["process.env.NODE_ENV"]).toBe('"production"');
});

test("mandala package.json has production config", () => {
  const pkg = JSON.parse(
    readFileSync("extensions/chthonic-mandala/package.json", "utf-8")
  );

  expect(pkg.sideEffects).toBe(false);
  expect(pkg.bun?.treeShaking).toBe(true);
  expect(pkg.bun?.minify).toBe(true);
});

test("statusbar has proper activation events", () => {
  const pkg = JSON.parse(
    readFileSync("extensions/chthonic-statusbar/package.json", "utf-8")
  );

  expect(pkg.activationEvents).toContain("onStartupFinished");
  expect(pkg.activationEvents).toContain("onLanguage:python");
  expect(pkg.activationEvents.length).toBeGreaterThan(2);
});

test("mandala has theme contribution", () => {
  const pkg = JSON.parse(
    readFileSync("extensions/chthonic-mandala/package.json", "utf-8")
  );

  expect(pkg.contributes?.themes).toBeDefined();
  expect(pkg.contributes.themes.length).toBeGreaterThan(0);
});

test("compile scripts use minification", () => {
  const statusbarPkg = JSON.parse(
    readFileSync("extensions/chthonic-statusbar/package.json", "utf-8")
  );
  const mandalaPkg = JSON.parse(
    readFileSync("extensions/chthonic-mandala/package.json", "utf-8")
  );

  expect(statusbarPkg.scripts.compile).toContain("--minify");
  expect(mandalaPkg.scripts.compile).toContain("--minify");
});
