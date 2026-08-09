#!/usr/bin/env bun

// @SID: CI_CHECK_SSOT_SEAL_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: ci/checks/ssot-seal.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: GOLD
// ║ Temple-Ayllu Zone: ⚖️ THE SCALE
// ║ Ogdoad-Ceque Radiance:
// ║   └─◄ (Guards the sidecar seals AxiomVerifier reads at runtime;
// ║       writes manifest/ssot_seal_audit.json)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * ci/checks/ssot-seal.ts — Does each sealed canon still match its seal?
 *
 * `src/data/verifier.rs` (AxiomVerifier) compares a frozen canon file against a
 * sidecar `<canon>.sha256` at runtime. Two properties of that design make it
 * unguardable from inside itself:
 *
 *   1. It runs only under `#[cfg(debug_assertions)]`, so a release binary never
 *      checks at all.
 *   2. A MISSING seal takes the `return Ok(())` branch (verifier.rs:61-67). That
 *      is correct for first-run bootstrapping and wrong as a steady state: once a
 *      seal has been committed, its later absence means "the check no longer
 *      runs," not "the canon is fine." Silence and success look identical.
 *
 * Both were live on 2026-08-09: `.chthonic/SSOT.md.sha256` was deleted in the
 * working tree, and the copy in HEAD (1d484686…) did not match the SSOT.md in
 * the same commit (6808095b…) — the seal was written by 3f19e50a on 2026-07-07
 * and the canon moved again in fadba2e4 on 2026-07-08 with no reseal.
 *
 * WHY THE CANON LIST IS EXPLICIT, NOT DISCOVERED. Enumerating `*.sha256` files
 * would reproduce the exact bug this check exists to catch: delete the seal and
 * the scan finds nothing to check, so the run goes green. An absent seal has to
 * be a finding, which means the thing being sealed must be named up front.
 *
 * Read-only by default (exit 0), same shape as spread-freshness: it reports, it
 * does not hijack the pre-commit flow. `--strict` opts into gating.
 *
 * Usage:
 *   bun run ci/checks/ssot-seal.ts
 *   bun run ci/checks/ssot-seal.ts --strict     # exit 1 on any finding
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from "fs";
import { dirname, resolve } from "path";
import { createHash } from "crypto";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_PATH = resolve(REPO_ROOT, "manifest/ssot_seal_audit.json");
const STRICT = process.argv.includes("--strict");

// Explicit by design — see the header note. Add a row when a new canon file gets
// a sidecar seal that AxiomVerifier (or anything else) is expected to read.
const SEALED_CANON: Array<{ canon: string; note: string }> = [
  {
    canon: ".chthonic/SSOT.md",
    note: "read by AxiomVerifier::new() in src/main.rs (debug builds only)",
  },
];

type Status = "ok" | "drift" | "seal_missing" | "canon_missing";

type Result = {
  canon: string;
  seal: string;
  status: Status;
  actual_hash: string | null;
  sealed_hash: string | null;
  note: string;
};

function sha256OfFile(absPath: string): string {
  const h = createHash("sha256");
  h.update(readFileSync(absPath));
  return h.digest("hex");
}

const results: Result[] = [];

for (const entry of SEALED_CANON) {
  const sealRel = `${entry.canon}.sha256`;
  const canonAbs = resolve(REPO_ROOT, entry.canon);
  const sealAbs = resolve(REPO_ROOT, sealRel);

  if (!existsSync(canonAbs)) {
    results.push({
      canon: entry.canon, seal: sealRel, status: "canon_missing",
      actual_hash: null, sealed_hash: null, note: entry.note,
    });
    continue;
  }

  const actual = sha256OfFile(canonAbs);

  if (!existsSync(sealAbs)) {
    results.push({
      canon: entry.canon, seal: sealRel, status: "seal_missing",
      actual_hash: actual, sealed_hash: null, note: entry.note,
    });
    continue;
  }

  const sealed = readFileSync(sealAbs, "utf8").trim();
  results.push({
    canon: entry.canon, seal: sealRel,
    status: sealed === actual ? "ok" : "drift",
    actual_hash: actual, sealed_hash: sealed, note: entry.note,
  });
}

const findings = results.filter((r) => r.status !== "ok");

const manifest = {
  tool: "CI_CHECK_SSOT_SEAL_V1",
  generated_at: new Date().toISOString(),
  strict: STRICT,
  sealed_count: results.length,
  ok_count: results.length - findings.length,
  finding_count: findings.length,
  results,
};
mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + "\n", "utf8");

for (const r of results) {
  if (r.status === "ok") {
    console.log(`[ssot-seal] OK       ${r.canon} matches ${r.seal}`);
    continue;
  }
  if (r.status === "canon_missing") {
    console.error(`[ssot-seal] MISSING  ${r.canon} does not exist — nothing to verify`);
    continue;
  }
  if (r.status === "seal_missing") {
    const size = statSync(resolve(REPO_ROOT, r.canon)).size;
    console.error(`[ssot-seal] NO SEAL  ${r.seal} is absent`);
    console.error(`             ${r.note}`);
    console.error(`             AxiomVerifier returns Ok() when the seal is missing, so runtime`);
    console.error(`             drift detection is currently OFF for this canon, not passing.`);
    console.error(`             canon is ${size} bytes, sha256 ${r.actual_hash}`);
    console.error(`             restore the committed seal:  git checkout -- ${r.seal}`);
    continue;
  }
  console.error(`[ssot-seal] DRIFT    ${r.canon} has moved since its last seal`);
  console.error(`             sealed:  ${r.sealed_hash}`);
  console.error(`             current: ${r.actual_hash}`);
  console.error(`             ${r.note}`);
  console.error(`             Resealing accepts current content as frozen canon — an authorship`);
  console.error(`             decision, not a mechanical fix. To reseal deliberately:`);
  console.error(`             (Get-FileHash -LiteralPath ${r.canon} -Algorithm SHA256).Hash.ToLower() | Set-Content ${r.seal} -NoNewline`);
}

console.log(
  `[ssot-seal] ${results.length - findings.length}/${results.length} sealed canon file(s) verified` +
    (findings.length > 0 ? `, ${findings.length} finding(s)` : "") +
    (STRICT ? " [strict]" : " [read-only — pass --strict to gate]")
);

process.exit(STRICT && findings.length > 0 ? 1 : 0);
