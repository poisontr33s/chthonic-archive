#!/usr/bin/env bun
// @SID: SCRIPT_SOURCER_SDK_V1

/**
 * sourcer-sdk — The Sourcer's dependency lane.
 *
 * Her canon role generalized: source the repo's pinned SDK versions against upstream latest.
 * `compare` is read-only and safe; the bump itself is a greenlit act, not a silent fix, because
 * the bridges (chthonic-acp-bridge, chthonic-copilot-bridge) are written to these exact APIs.
 *
 * Tracked:
 *   agent-client-protocol  — pin: chthonic-acp-bridge/Cargo.toml      latest: crates.io
 *   copilot-sdk (rust)     — pin: meta-ide vendored clone dir-name    latest: github/copilot-sdk (rust/ tags)
 *
 * Usage:  bun run scripts/sourcer-sdk.ts compare [--json]
 */

import { existsSync, readFileSync } from "fs";
import { join } from "path";

const REPO_ROOT = process.cwd();

// ── version compare (pre-release aware: 1.0.0-beta.9 < 1.0.0) ──────────────────
function parseVer(v: string): { nums: number[]; pre: string } {
  const s = v.replace(/^v/, "");
  const dash = s.indexOf("-");
  const core = dash === -1 ? s : s.slice(0, dash);
  const pre = dash === -1 ? "" : s.slice(dash + 1);
  return { nums: core.split(".").map((n) => parseInt(n, 10) || 0), pre };
}
function cmpVer(a: string, b: string): number {
  const pa = parseVer(a);
  const pb = parseVer(b);
  for (let i = 0; i < Math.max(pa.nums.length, pb.nums.length); i++) {
    const d = (pa.nums[i] ?? 0) - (pb.nums[i] ?? 0);
    if (d !== 0) return d < 0 ? -1 : 1;
  }
  if (pa.pre === pb.pre) return 0;
  if (pa.pre === "") return 1; // a is a release, b is a pre-release -> a is newer
  if (pb.pre === "") return -1;
  return pa.pre < pb.pre ? -1 : 1;
}

// ── resolvers ─────────────────────────────────────────────────────────────────
function cargoPin(cargoRel: string, crate: string): string | null {
  const p = join(REPO_ROOT, cargoRel);
  if (!existsSync(p)) return null;
  const txt = readFileSync(p, "utf8");
  const esc = crate.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const m = txt.match(new RegExp(`${esc}\\s*=\\s*(?:\\{[^}]*?version\\s*=\\s*)?"([^"]+)"`));
  return m ? m[1] : null;
}

async function cratesLatest(crate: string): Promise<string | null> {
  try {
    const r = await fetch(`https://crates.io/api/v1/crates/${crate}`, {
      headers: { "User-Agent": "chthonic-sourcer-sdk (canon dependency check)" },
    });
    if (!r.ok) return null;
    const j = (await r.json()) as { crate?: { max_stable_version?: string; newest_version?: string } };
    return j.crate?.max_stable_version ?? j.crate?.newest_version ?? null;
  } catch {
    return null;
  }
}

// ── the SDK manifest ──────────────────────────────────────────────────────────
type SdkReport = {
  name: string;
  pinned: string | null;
  latest: string | null;
  status: "current" | "behind" | "ahead" | "unknown";
  upstream: string;
  consumer: string;
};

function verdict(pinned: string | null, latest: string | null): SdkReport["status"] {
  if (!pinned || !latest) return "unknown";
  const c = cmpVer(pinned, latest);
  return c < 0 ? "behind" : c > 0 ? "ahead" : "current";
}

async function compare(): Promise<SdkReport[]> {
  const acpPin = cargoPin(
    "extensions/chthonic-archive/native/chthonic-acp-bridge/Cargo.toml",
    "agent-client-protocol",
  );
  const acpLatest = await cratesLatest("agent-client-protocol");

  const cpPin = cargoPin(
    "extensions/chthonic-archive/native/chthonic-copilot-bridge/Cargo.toml",
    "github-copilot-sdk",
  );
  const cpLatest = await cratesLatest("github-copilot-sdk");

  return [
    {
      name: "agent-client-protocol",
      pinned: acpPin,
      latest: acpLatest,
      status: verdict(acpPin, acpLatest),
      upstream: "crates.io",
      consumer: "chthonic-acp-bridge",
    },
    {
      name: "github-copilot-sdk",
      pinned: cpPin,
      latest: cpLatest,
      status: verdict(cpPin, cpLatest),
      upstream: "crates.io",
      consumer: "chthonic-copilot-bridge",
    },
  ];
}

// ── CLI ───────────────────────────────────────────────────────────────────────
const cmd = process.argv[2] ?? "compare";
const asJson = process.argv.includes("--json");

if (cmd !== "compare") {
  console.error(`sourcer-sdk: unknown command '${cmd}' (only 'compare' so far)`);
  process.exit(1);
}

const reps = await compare();
if (asJson) {
  console.log(JSON.stringify({ sdks: reps }, null, 2));
} else {
  console.log("The Sourcer — SDK currency (repo pin vs upstream latest)\n");
  for (const r of reps) {
    const mark =
      r.status === "behind" ? "BEHIND" : r.status === "current" ? "current" : r.status.toUpperCase();
    console.log(`  ${r.name}  [${r.consumer}]`);
    console.log(`    pinned:  ${r.pinned ?? "?"}`);
    console.log(`    latest:  ${r.latest ?? "?"}   (${r.upstream})`);
    console.log(`    status:  ${mark}\n`);
  }
}
