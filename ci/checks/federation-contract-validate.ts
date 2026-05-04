#!/usr/bin/env bun
// @SID: CI_CHECK_FEDERATION_CONTRACT_VALIDATE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/federation-contract-validate.ts
// ║ Validates vampire satellite registration contracts against the live corpus.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Usage:
// ║   bun run ci/checks/federation-contract-validate.ts
// ║     — validates all satellite.json files found in scripts/satellites/
// ║       and any path listed in manifest/corpus-state.json#satellites
// ║
// ║   bun run ci/checks/federation-contract-validate.ts --satellite <id>
// ║     — validates one satellite by id (looks up satellite.json from registry)
// ║
// ║   bun run ci/checks/federation-contract-validate.ts --register <path/satellite.json>
// ║     — validates + registers into corpus-state.json#satellites
// ║
// ║   bun run ci/checks/federation-contract-validate.ts --report
// ║     — full JSON report to stdout (CI machine-parseable)
// ║
// ║ Exit codes:
// ║   0 = all validated satellites pass
// ║   1 = at least one check failed
// ╚════════════════════════════════════════════════════════════════════════════

import { Database } from "bun:sqlite";
import { existsSync, readFileSync, writeFileSync } from "fs";
import { resolve, join } from "path";

const REPO_ROOT    = resolve(import.meta.dir, "../..");
const MANIFEST_DIR = resolve(REPO_ROOT, "manifest");
const CORPUS_PATH  = join(MANIFEST_DIR, "corpus.sqlite");
const STATE_PATH   = join(MANIFEST_DIR, "corpus-state.json");

const REPORT   = process.argv.includes("--report");
const REGISTER = process.argv.includes("--register");
const satArg   = (() => { const i = process.argv.indexOf("--satellite"); return i >= 0 ? process.argv[i + 1] : null; })();
const regArg   = (() => { const i = process.argv.indexOf("--register"); return i >= 0 ? process.argv[i + 1] : null; })();

// ── Satellite contract type ──────────────────────────────────────────────────

interface SatelliteContract {
  satellite_id: string;
  version: string;
  source_contract: {
    host: string;
    platform?: string;
    surfaces: string[];
    poll_interval_ms?: number;
    trigger?: string;
  };
  drain_format: {
    type: string;                // must be "sqlite"
    path: string;                // relative to repo root
    schema_version?: number;
    tables: string[];
  };
  federation_keys: string[];
  outbound_network: boolean;     // MUST be false
  license: string;               // MUST be Apache-2.0
  corpus_schema_min?: number;    // minimum corpus user_version required
}

// ── Check result ─────────────────────────────────────────────────────────────

interface CheckResult {
  satellite_id: string;
  satellite_json_path: string;
  checks: Array<{ name: string; pass: boolean; detail: string }>;
  passed: boolean;
}

// ── Load corpus state ────────────────────────────────────────────────────────

function loadCorpusState(): Record<string, unknown> | null {
  if (!existsSync(STATE_PATH)) return null;
  try { return JSON.parse(readFileSync(STATE_PATH, "utf8")) as Record<string, unknown>; } catch { return null; }
}

function corpusUserVersion(): number {
  if (!existsSync(CORPUS_PATH)) return 0;
  try {
    const db = new Database(CORPUS_PATH, { readonly: true });
    const row = db.prepare("PRAGMA user_version").get() as { user_version: number };
    db.close();
    return row.user_version;
  } catch { return 0; }
}

// ── Validate one satellite.json ──────────────────────────────────────────────

function validate(satPath: string): CheckResult {
  const checks: CheckResult["checks"] = [];
  const addCheck = (name: string, pass: boolean, detail: string) => checks.push({ name, pass, detail });

  // File must exist
  if (!existsSync(satPath)) {
    addCheck("file_exists", false, `satellite.json not found at ${satPath}`);
    return { satellite_id: "<unknown>", satellite_json_path: satPath, checks, passed: false };
  }

  // Must be valid JSON
  let contract: SatelliteContract;
  try {
    contract = JSON.parse(readFileSync(satPath, "utf8")) as SatelliteContract;
  } catch (e) {
    addCheck("json_parse", false, `Invalid JSON: ${e}`);
    return { satellite_id: "<parse_error>", satellite_json_path: satPath, checks, passed: false };
  }

  const id = contract.satellite_id ?? "<missing>";

  // satellite_id: kebab-case, non-empty
  addCheck(
    "satellite_id_format",
    typeof id === "string" && id.length > 0 && /^[a-z][a-z0-9-]*$/.test(id),
    id ? `id="${id}" — must be non-empty kebab-case` : "satellite_id missing"
  );

  // outbound_network MUST be false
  addCheck(
    "no_outbound_network",
    contract.outbound_network === false,
    contract.outbound_network === false
      ? "outbound_network: false ✅"
      : `outbound_network: ${contract.outbound_network} — MUST be false`
  );

  // license MUST be Apache-2.0
  addCheck(
    "license_apache2",
    contract.license === "Apache-2.0",
    contract.license === "Apache-2.0"
      ? "license: Apache-2.0 ✅"
      : `license: ${contract.license ?? "(missing)"} — must be Apache-2.0`
  );

  // drain_format.type MUST be "sqlite"
  addCheck(
    "drain_type_sqlite",
    contract.drain_format?.type === "sqlite",
    contract.drain_format?.type === "sqlite"
      ? "drain_format.type: sqlite ✅"
      : `drain_format.type: ${contract.drain_format?.type ?? "(missing)"} — must be sqlite`
  );

  // tables list must be non-empty
  const tables = contract.drain_format?.tables ?? [];
  addCheck(
    "drain_tables_nonempty",
    tables.length > 0,
    tables.length > 0 ? `tables: [${tables.join(", ")}]` : "drain_format.tables is empty"
  );

  // federation_keys must be non-empty
  const fkeys = contract.federation_keys ?? [];
  addCheck(
    "federation_keys_nonempty",
    fkeys.length > 0,
    fkeys.length > 0 ? `federation_keys: [${fkeys.join(", ")}]` : "federation_keys is empty"
  );

  // corpus_schema_min: if set, must be <= actual corpus user_version
  if (contract.corpus_schema_min !== undefined) {
    const actual = corpusUserVersion();
    const compatible = actual >= contract.corpus_schema_min;
    addCheck(
      "corpus_schema_compat",
      compatible,
      compatible
        ? `corpus user_version=${actual} >= min=${contract.corpus_schema_min} ✅`
        : `corpus user_version=${actual} < required min=${contract.corpus_schema_min} — run corpus gates first`
    );
  } else {
    addCheck("corpus_schema_compat", true, "corpus_schema_min not declared (unconstrained)");
  }

  // drain DB exists (informational — not a hard failure; satellite may not have run yet)
  if (contract.drain_format?.path) {
    const drainPath = resolve(REPO_ROOT, contract.drain_format.path);
    const drainExists = existsSync(drainPath);
    addCheck(
      "drain_db_exists",
      drainExists,
      drainExists ? `drain DB found: ${contract.drain_format.path}` : `drain DB not yet created: ${contract.drain_format.path} (ok if satellite hasn't run)`
    );
  }

  const passed = checks.filter(c => c.name !== "drain_db_exists").every(c => c.pass);
  return { satellite_id: id, satellite_json_path: satPath, checks, passed };
}

// ── Discover satellite.json files ────────────────────────────────────────────

function discoverSatellites(): string[] {
  const paths: string[] = [];

  // From corpus-state.json#satellites (registered paths)
  const state = loadCorpusState();
  if (state && Array.isArray(state.satellites)) {
    for (const p of state.satellites as string[]) {
      const resolved = resolve(REPO_ROOT, p);
      if (!paths.includes(resolved)) paths.push(resolved);
    }
  }

  // From scripts/satellites/ if it exists
  const satDir = join(REPO_ROOT, "scripts", "satellites");
  if (existsSync(satDir)) {
    const { readdirSync } = require("fs") as typeof import("fs");
    for (const entry of readdirSync(satDir, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        const p = join(satDir, entry.name, "satellite.json");
        if (existsSync(p) && !paths.includes(p)) paths.push(p);
      } else if (entry.name === "satellite.json") {
        const p = join(satDir, entry.name);
        if (!paths.includes(p)) paths.push(p);
      }
    }
  }

  return paths;
}

// ── Register satellite into corpus-state.json ────────────────────────────────

function registerSatellite(satPath: string, satelliteId: string): void {
  const state = loadCorpusState() ?? {};
  const sats  = (state.satellites as string[]) ?? [];
  const rel   = satPath.replace(REPO_ROOT + "\\", "").replace(REPO_ROOT + "/", "").replace(/\\/g, "/");
  if (!sats.includes(rel)) {
    sats.push(rel);
    state.satellites = sats;
    writeFileSync(STATE_PATH, JSON.stringify(state, null, 2) + "\n");
    console.log(`📎  Registered ${satelliteId} → corpus-state.json#satellites`);
  } else {
    console.log(`ℹ️   ${satelliteId} already registered`);
  }
}

// ── Main ─────────────────────────────────────────────────────────────────────

const results: CheckResult[] = [];

if (regArg) {
  // --register mode: validate + register one satellite
  const satPath = resolve(REPO_ROOT, regArg);
  const result  = validate(satPath);
  results.push(result);
  if (result.passed && REGISTER) registerSatellite(satPath, result.satellite_id);
} else if (satArg) {
  // --satellite mode: find by id in known paths
  const discovered = discoverSatellites();
  const found = discovered.find(p => {
    try {
      const c = JSON.parse(readFileSync(p, "utf8")) as SatelliteContract;
      return c.satellite_id === satArg;
    } catch { return false; }
  });
  if (!found) {
    console.error(`Satellite not found: ${satArg}`);
    process.exit(1);
  }
  results.push(validate(found));
} else {
  // Default: validate all discovered
  const paths = discoverSatellites();
  if (paths.length === 0) {
    console.log("ℹ️   No satellites registered. Use --register <path/satellite.json> to add one.");
    process.exit(0);
  }
  for (const p of paths) results.push(validate(p));
}

// ── Output ───────────────────────────────────────────────────────────────────

if (REPORT) {
  console.log(JSON.stringify({ results, corpus_user_version: corpusUserVersion() }, null, 2));
} else {
  const corpusVer = corpusUserVersion();
  console.log(`\n🛸 FEDERATION CONTRACT VALIDATE  (corpus schema_version=${corpusVer})\n`);
  for (const r of results) {
    const badge = r.passed ? "✅" : "❌";
    console.log(`  ${badge}  ${r.satellite_id}  (${r.satellite_json_path.replace(REPO_ROOT, ".")})`);
    for (const c of r.checks) {
      const icon = c.pass ? "    ✓" : "    ✗";
      console.log(`${icon}  ${c.name.padEnd(28)} ${c.detail}`);
    }
    console.log();
  }
}

const anyFailed = results.some(r => !r.passed);
process.exit(anyFailed ? 1 : 0);
