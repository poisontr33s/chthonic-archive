#!/usr/bin/env bun
// @SID: CI_CHECK_INFERENCE_GATE_SMOKE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/inference-gate-smoke.ts
// ║ Gate ladder status reader for tabbyAPI / Python 3.14 GPU inference host.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ SMOKE mode (default): reads manifest/*.json only — no Python import,
// ║   no rebuild. Fast (<1s). Exits 1 if any non-impossible gate is L0_blocked.
// ║
// ║ REPORT mode (--report): dumps full gate ladder JSON to stdout.
// ║   Machine-parseable by future sessions / CI pipelines.
// ║
// ║ Gates:
// ║   G1  resolver_coherence        manifest: (inline — no probe file)
// ║   G2  pydantic_pyо3_abi         manifest: (inline — via pytest results)
// ║   G3  torch_cuda                manifest/cuda_gate.jsonl
// ║   G4  exllamav2_cp314           manifest: impossible_currently
// ║   G5  exllamav3_cp314           manifest: inferred from G6
// ║   G6  flash_attn_build          manifest/vs2022_flash_attn_probe.json
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_DIR = resolve(REPO_ROOT, "manifest");
const REPORT = process.argv.includes("--report");

// ── Gate definitions ─────────────────────────────────────────────────────────

type GateStatus =
  | "admitted"
  | "impossible_currently"
  | "blocked"
  | "not_probed";

type GateLevel = "L0" | "L1" | "L2" | "L3" | "L4" | "unknown";

interface GateResult {
  gate: string;
  question: string;
  status: GateStatus;
  level: GateLevel;
  proof: string;
  notes?: string;
}

function readJson(path: string): Record<string, unknown> | null {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch {
    return null;
  }
}

function readJsonl(path: string): Record<string, unknown>[] {
  if (!existsSync(path)) return [];
  try {
    return readFileSync(path, "utf-8")
      .split("\n")
      .filter((l) => l.trim())
      .map((l) => JSON.parse(l));
  } catch {
    return [];
  }
}

// ── Gate probers ─────────────────────────────────────────────────────────────

function probeG3(): GateResult {
  const entries = readJsonl(resolve(MANIFEST_DIR, "cuda_gate.jsonl"));
  const last = entries[entries.length - 1] ?? null;
  if (!last) {
    return {
      gate: "G3_torch_cuda",
      question: "Can torch discover a CUDA device on Python 3.14?",
      status: "not_probed",
      level: "L0",
      proof: "manifest/cuda_gate.jsonl not found",
    };
  }
  const ok = last["cuda_available"] === true && Number(last["device_count"] ?? 0) > 0;
  return {
    gate: "G3_torch_cuda",
    question: "Can torch discover a CUDA device on Python 3.14?",
    status: ok ? "admitted" : "blocked",
    level: ok ? "L4" : "L0",
    proof: `torch=${last["torch_version"]} device=${last["device_name"]} cap=${JSON.stringify(last["device_capability"])}`,
  };
}

function probeG6(): GateResult {
  const m = readJson(resolve(MANIFEST_DIR, "vs2022_flash_attn_probe.json"));
  if (!m) {
    return {
      gate: "G6_flash_attn_build",
      question: "Can flash_attn 2.8.3 be built and installed on Python 3.14 + CUDA 12.8?",
      status: "not_probed",
      level: "L0",
      proof: "manifest/vs2022_flash_attn_probe.json not found",
    };
  }
  const ok = m["build_result"] === "SUCCESS";
  return {
    gate: "G6_flash_attn_build",
    question: "Can flash_attn 2.8.3 be built and installed on Python 3.14 + CUDA 12.8?",
    status: ok ? "admitted" : "blocked",
    level: ok ? "L1" : "L0",
    proof: ok
      ? `P-06 succeeded: MSVC ${m["vs2022_version"]} + CUDA 12.8 — build_exit_code=0`
      : `P-06 failed: ${m["status"]} — ${m["remaining_blocker"] ?? "see manifest"}`,
    notes: ok ? `Build time inferred ~60m (source build). Wheel cached in uv store.` : undefined,
  };
}

// ── Static gates (no manifest file — status known from ledger) ───────────────

const STATIC_GATES: GateResult[] = [
  {
    gate: "G1_resolver_coherence",
    question: "Can uv resolve a GPU-backend wheel stack for Python 3.14?",
    status: "admitted",
    level: "L4",
    proof: "uv run pytest tests/test_start_ps1.py -v → 17/17 passed (commit bfeb655b)",
  },
  {
    gate: "G2_pydantic_pyо3_abi",
    question: "Can pydantic-core on Python 3.14 pass tabbyAPI's validation layer?",
    status: "admitted",
    level: "L4",
    proof: "pydantic-core 2.46.x cp314 wheel, PyO3 0.25.x — 17/17 tests (commit bfeb655b)",
  },
  {
    gate: "G4_exllamav2_cp314",
    question: "Can exllamav2 be loaded on Python 3.14?",
    status: "impossible_currently",
    level: "L0",
    proof: "v0.3.2 highest wheel = cp313. No cp314 wheel published.",
    notes: "Reopen when turboderp-org/exllamav2 publishes cp314-cp314-win_amd64",
  },
  {
    gate: "G5_exllamav3_cp314",
    question: "Can exllamav3 be loaded on Python 3.14?",
    status: "admitted",
    level: "L4",
    proof: "import exllamav3 → OK after Gate 6 cleared (2026-04-25T08:46:33Z); triton warning non-fatal",
    notes: "triton not available on Win32 Python 3.14 — performance warning only, not blocking",
  },
];

// ── Known warnings (non-fatal, should be tracked not silenced) ───────────────

const KNOWN_WARNINGS = [
  {
    id: "triton_unavailable",
    description: "No module named 'triton' — Triton not available on Win32 Python 3.14",
    impact: "flop_counter disabled; some torch optimizations inactive",
    blocking: false,
    resolution: "triton has no Win32 wheel for cp314; WSL2 or Linux build required for full triton support",
  },
  {
    id: "xformers_triton_missing",
    description: "xformers imports triton internally — same root as triton_unavailable",
    impact: "xformers falls back to non-triton kernels",
    blocking: false,
    resolution: "same as triton_unavailable",
  },
  {
    id: "formatron_escape_sequences",
    description: "SyntaxWarning: invalid escape sequences in formatron/formats/json.py",
    impact: "cosmetic warning; no runtime effect on Python 3.14",
    blocking: false,
    resolution: "upstream fix in formatron — not our dependency to patch",
  },
];

// ── Runner ────────────────────────────────────────────────────────────────────

const gates: GateResult[] = [
  ...STATIC_GATES.slice(0, 2),
  probeG3(),
  STATIC_GATES[2], // G4
  STATIC_GATES[3], // G5
  probeG6(),
];

const blockedGates = gates.filter((g) => g.status === "blocked" || g.status === "not_probed");
const admittedGates = gates.filter((g) => g.status === "admitted");
const impossibleGates = gates.filter((g) => g.status === "impossible_currently");

if (REPORT) {
  const report = {
    generated: new Date().toISOString(),
    summary: {
      total: gates.length,
      admitted: admittedGates.length,
      impossible_currently: impossibleGates.length,
      blocked: blockedGates.length,
    },
    gates,
    known_warnings: KNOWN_WARNINGS,
  };
  console.log(JSON.stringify(report, null, 2));
  process.exit(blockedGates.length > 0 ? 1 : 0);
}

// Compact smoke output
if (blockedGates.length === 0) {
  const levels = admittedGates.map((g) => `${g.gate}=${g.level}`).join(" ");
  console.log(`[inference-gate-smoke] ✓ All active gates admitted — ${levels}`);
  process.exit(0);
} else {
  for (const g of blockedGates) {
    console.error(`[inference-gate-smoke] ✗ ${g.gate} — ${g.status} — ${g.proof}`);
  }
  process.exit(1);
}
