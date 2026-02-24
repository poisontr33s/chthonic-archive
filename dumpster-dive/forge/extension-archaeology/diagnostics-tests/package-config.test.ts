// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: package-config.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_PACKAGE_CONFIG_V1 @Shabti Test Script @Purpose Validates statusbar package.json production config. */

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
  expect(pkg.activationEvents).toEqual(
    expect.arrayContaining([
      "onCommand:chthonic.verifySSO_T",
      "onCommand:chthonic.runMetabolicCycle",
      "onCommand:chthonic.showGPUStats",
      "onCommand:chthonic.runHostVerify",
      "onCommand:chthonic.runVsAudit",
    ])
  );
  // Bridge-era statusbar should not be Python-language activated.
  expect(pkg.activationEvents).not.toContain("onLanguage:python");
});

test("mandala has bridge view container contribution", () => {
  const pkg = JSON.parse(
    readFileSync("extensions/chthonic-mandala/package.json", "utf-8")
  );

  const containers = pkg.contributes?.viewsContainers?.activitybar ?? [];
  expect(containers.length).toBeGreaterThan(0);
  expect(containers.some((entry: { id?: string }) => entry.id === "chthonic-geometry")).toBe(true);

  const bridgeViews = pkg.contributes?.views?.["chthonic-geometry"] ?? [];
  expect(bridgeViews.length).toBeGreaterThanOrEqual(4);
  // Mandala bridge no longer owns theme JSON assets directly.
  expect(pkg.contributes?.themes).toBeUndefined();
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

test("bridge extensions expose Bun cockpit command lanes", () => {
  const statusbarPkg = JSON.parse(
    readFileSync("extensions/chthonic-statusbar/package.json", "utf-8")
  );
  const mandalaPkg = JSON.parse(
    readFileSync("extensions/chthonic-mandala/package.json", "utf-8")
  );

  const statusbarCommands = (statusbarPkg.contributes?.commands ?? []).map(
    (entry: { command?: string }) => entry.command
  );
  const mandalaCommands = (mandalaPkg.contributes?.commands ?? []).map(
    (entry: { command?: string }) => entry.command
  );

  expect(statusbarCommands).toEqual(
    expect.arrayContaining([
      "chthonic.openWebCockpitBridge",
      "chthonic.openBunTrainingDocsBridge",
    ])
  );
  expect(mandalaCommands).toEqual(
    expect.arrayContaining([
      "chthonic.mandalaBridge.openWebCockpit",
      "chthonic.mandalaBridge.openBunDocs",
    ])
  );
});
