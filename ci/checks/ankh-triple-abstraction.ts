#!/usr/bin/env bun
// @SID: CI_CHECK_ANKH_TRIPLE_ABSTRACTION_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/ankh-triple-abstraction.ts
// ║ ANKH triple abstraction probe membrane — reads manifest, no Python import.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ SMOKE mode (default): exits 0 if manifest absent (probe not yet run).
// ║   Exits 1 only on CRITICAL status — WARN is allowed to pass.
// ║
// ║ REPORT mode (--report): dumps full manifest JSON to stdout.
// ║
// ║ Factors checked:
// ║   F1  SSOT stratum distribution (WHR:MAX conformance)
// ║   F2  Entity τ-core / upper-volume topology (drift detection)
// ║   F3  Synthesis compression ratio (overcompression / undercompression)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest", "ankh_triple_abstraction_probe.json");
const REPORT = process.argv.includes("--report");

// ── Read manifest ─────────────────────────────────────────────────────────────

function readManifest(): Record<string, unknown> | null {
  if (!existsSync(MANIFEST_PATH)) return null;
  try {
    return JSON.parse(readFileSync(MANIFEST_PATH, "utf-8"));
  } catch {
    return null;
  }
}

const manifest = readManifest();

if (!manifest) {
  // Probe not yet run — not a CI failure, just absent
  console.log("[ankh-triple-abstraction] manifest absent — probe not yet run (skipping)");
  process.exit(0);
}

if (REPORT) {
  console.log(JSON.stringify(manifest, null, 2));
  process.exit(0);
}

// ── Evaluate ──────────────────────────────────────────────────────────────────

const status = (manifest.overall_status ?? manifest.status ?? "UNKNOWN") as string;
const meta = (manifest.metadata ?? {}) as Record<string, unknown>;
const f1 = (manifest.factor_1_ssot_distribution ?? {}) as Record<string, unknown>;
const f2 = (manifest.factor_2_entity_topology ?? {}) as Record<string, unknown>;
const f3 = (manifest.factor_3_compression ?? {}) as Record<string, unknown>;

const whrConformance = (f1.whr_max_conformance ?? "?") as number | string;
const topologyValid = (f2.whr_topology_valid ?? "?") as boolean | string;
const compressionRatio = (f3.compression_ratio ?? "?") as number | string;
const compressionZone = (f3.compression_zone ?? "?") as string;
const driftAlerts = (f2.drift_alerts ?? []) as unknown[];
const invariant = (meta.invariant ?? "") as string;

const ratioStr = typeof compressionRatio === "number"
  ? compressionRatio.toFixed(2)
  : compressionRatio;

console.log(`[ankh-triple-abstraction] status=${status}`);
console.log(`  F1 WHR:MAX conformance   ${whrConformance}`);
console.log(`  F2 topology valid        ${topologyValid}  drift_alerts=${driftAlerts.length}`);
console.log(`  F3 compression           ${ratioStr}:1  zone=${compressionZone}`);
if (invariant) {
  console.log(`  ∞  "${invariant}"`);
}

// Drift alerts are always failures regardless of overall status
if (driftAlerts.length > 0) {
  console.error(`[ankh-triple-abstraction] ✗ ${driftAlerts.length} entity drift alert(s):`);
  for (const alert of driftAlerts) {
    console.error(`     - ${alert}`);
  }
  process.exit(1);
}

// CRITICAL exits 1. WARN is allowed to pass (informational).
if (status === "CRITICAL") {
  console.error("[ankh-triple-abstraction] ✗ CRITICAL — see manifest for details");
  process.exit(1);
}

console.log("[ankh-triple-abstraction] ✓ passed");
process.exit(0);
