#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: doctor.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * Extension archaeology doctor — system health check
 *
 * @SID           TOOL_EXT_ARCH_DOCTOR_V1
 * @Shabti        CLI Script
 * @Purpose       Comprehensive diagnostics: bundle sizes, runtime lanes,
 *                GPU status, deployment, build config, source checks.
 */

import { execSync } from "child_process";
import { existsSync, statSync, readFileSync } from "fs";
import { join } from "path";

console.log("🔍 Chthonic Extension System Health Check\n");

// Bundle sizes
console.log("📦 Bundle Sizes");
const statusbarSize = statSync("extensions/chthonic-statusbar/dist/extension.js").size;
const mandalaSize = statSync("extensions/chthonic-mandala/dist/extension.js").size;
console.log(`  StatusBar: ${(statusbarSize / 1024).toFixed(1)} KB`);
console.log(`  Mandala:   ${(mandalaSize / 1024).toFixed(1)} KB`);
console.log(`  Combined:  ${((statusbarSize + mandalaSize) / 1024).toFixed(1)} KB`);

const statusbarHealth = statusbarSize < 10 * 1024 ? "✓" : "⚠️";
const mandalaHealth = mandalaSize < 18 * 1024 ? "✓" : "⚠️";
console.log(`  Status:    ${statusbarHealth} StatusBar, ${mandalaHealth} Mandala\n`);

// Bun lane detection
console.log("🥟 Bun Runtime Lane");
try {
  const output = execSync("bun --version", { encoding: "utf-8", timeout: 5000 }).trim();
  console.log(`  Version:   ${output || "FAILED"}`);
  console.log(`  Status:    ${output ? "✓" : "❌"}\n`);
} catch (error: any) {
  console.log(`  Status:    ❌ ${error.message}\n`);
}

// GPU stats
console.log("🎮 GPU Status");
try {
  const output = execSync(
    "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits",
    { encoding: "utf-8", timeout: 3000 }
  ).trim();
  const [used, total] = output.split(",").map((s) => parseInt(s.trim()));
  const percent = ((used / total) * 100).toFixed(0);
  console.log(`  VRAM:      ${(used / 1024).toFixed(1)} GB / ${(total / 1024).toFixed(1)} GB (${percent}%)`);
  console.log(`  Status:    ✓\n`);
} catch {
  console.log(`  Status:    ⚠️  nvidia-smi not available\n`);
}

// Deployment
console.log("📍 Deployment Status");
const statusbarDeployed = existsSync(join("extensions", "chthonic-statusbar", "dist", "extension.js"));
const mandalaDeployed = existsSync(join("extensions", "chthonic-mandala", "dist", "extension.js"));
const themeDeployed = existsSync(
  join("extensions", "chthonic-mandala", "themes", "chthonic-mandala-color-theme.json")
);

console.log(`  StatusBar: ${statusbarDeployed ? "✓" : "❌"}`);
console.log(`  Mandala:   ${mandalaDeployed ? "✓" : "❌"}`);
console.log(`  Theme:     ${themeDeployed ? "✓" : "❌"}\n`);

// Production config
console.log("⚙️  Build Configuration");
const statusbarPkg = JSON.parse(readFileSync("extensions/chthonic-statusbar/package.json", "utf-8"));
const mandalaPkg = JSON.parse(readFileSync("extensions/chthonic-mandala/package.json", "utf-8"));

console.log(`  Tree-shaking:  ${statusbarPkg.bun?.treeShaking ? "✓" : "❌"}`);
console.log(`  Minification:  ${statusbarPkg.bun?.minify ? "✓" : "❌"}`);
console.log(`  SideEffects:   ${statusbarPkg.sideEffects === false ? "✓" : "❌"}`);
console.log(`  NODE_ENV:      ${statusbarPkg.bun?.define?.["process.env.NODE_ENV"] || "not set"}\n`);

// Source code checks
console.log("🔬 Source Code Health");
const extensionSrc = readFileSync("extensions/chthonic-statusbar/src/extension.ts", "utf-8");
const hasBridgeRoutes =
  extensionSrc.includes("const ROUTES: RouteSpec[]") &&
  extensionSrc.includes("chthonic.verifySSO_T") &&
  extensionSrc.includes("chthonic.verifySSOT");
const dispatchesBunTasks =
  extensionSrc.includes("terminal.sendText(`bun run ${taskName}`)") &&
  extensionSrc.includes("runArchiveTask('verify:host', output)") &&
  extensionSrc.includes("runArchiveTask('audit:vs2026', output)");
const hasDeadImport = extensionSrc.includes("hedonisticValidation");

console.log(`  Bridge routes mapped:  ${hasBridgeRoutes ? "✓" : "❌"}`);
console.log(`  Bun task dispatch:     ${dispatchesBunTasks ? "✓" : "❌"}`);
console.log(`  Dead imports removed:  ${!hasDeadImport ? "✓" : "❌"}\n`);

// Summary
console.log("═".repeat(60));
const allHealthy =
  statusbarSize < 10 * 1024 &&
  mandalaSize < 18 * 1024 &&
  statusbarDeployed &&
  mandalaDeployed &&
  hasBridgeRoutes &&
  dispatchesBunTasks &&
  !hasDeadImport;

if (allHealthy) {
  console.log("✅ System is healthy - all critical invariants satisfied");
} else {
  console.log("⚠️  System has issues - run `bun test` for details");
}
console.log("═".repeat(60));
