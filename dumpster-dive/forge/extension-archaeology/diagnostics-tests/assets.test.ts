// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: assets.test.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/** @SID TEST_EXT_ARCH_ASSETS_V1 @Shabti Test Script @Purpose Validates mandala theme file existence and structure. */

import { test, expect } from "bun:test";
import { existsSync, readFileSync } from "fs";

test("mandala theme file exists and is valid", () => {
  const themePath =
    "extensions/chthonic-mandala/themes/chthonic-mandala-color-theme.json";

  expect(existsSync(themePath)).toBe(true);

  const theme = JSON.parse(readFileSync(themePath, "utf-8"));
  expect(theme.name).toContain("Chthonic Mandala");
  expect(theme.type).toBe("dark");
  expect(Object.keys(theme.colors).length).toBeGreaterThan(20);
  expect(theme.tokenColors.length).toBeGreaterThan(10);
});

test("mandala icon is theme-adaptive SVG", () => {
  const iconPath = "extensions/chthonic-mandala/icons/mandala.svg";

  expect(existsSync(iconPath)).toBe(true);

  const svg = readFileSync(iconPath, "utf-8");
  expect(svg).toContain("currentColor");
  expect(svg).toMatch(/viewBox="[^"]+"/);
});

test("icon uses proper FA color bands", () => {
  const svg = readFileSync(
    "extensions/chthonic-mandala/icons/mandala.svg",
    "utf-8"
  );

  // FA¹-⁵ color scheme
  expect(svg).toContain("#FF6B6B"); // FA¹ red
  expect(svg).toContain("#FFB84D"); // FA² orange
  expect(svg).toContain("#FFD700"); // FA³ gold
  expect(svg).toContain("#4ECDC4"); // FA⁴ blue
});
