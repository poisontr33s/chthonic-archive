// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: deployment.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_DEPLOYMENT_V1 @Shabti Test Script @Purpose Validates deployment configuration and VSIX readiness. */

import { test, expect } from "bun:test";
import { existsSync } from "fs";
import { join } from "path";

const statusbarRoot = join("extensions", "chthonic-statusbar");
const mandalaRoot = join("extensions", "chthonic-mandala");

test("statusbar extension is deployed", () => {
  const deployPath = join(statusbarRoot, "dist", "extension.js");
  expect(existsSync(deployPath)).toBe(true);
});

test("mandala extension is deployed", () => {
  const deployPath = join(mandalaRoot, "dist", "extension.js");
  expect(existsSync(deployPath)).toBe(true);
});

test("theme file is deployed", () => {
  const themePath = join(mandalaRoot, "themes", "chthonic-mandala-color-theme.json");
  expect(existsSync(themePath)).toBe(true);
});

test("icon is deployed", () => {
  const iconPath = join(mandalaRoot, "icons", "mandala.svg");
  expect(existsSync(iconPath)).toBe(true);
});
