#!/usr/bin/env bun
// @SID: CI_CHECK_CLAUDINE_LORA_SMOKE_V1

// ╔════════════════════════════════════════════════════════════════════════════
// ║ ci/checks/claudine-lora-smoke.ts
// ║ Gate ladder reader for Claudine LoRA adapter pipeline.
// ╠════════════════════════════════════════════════════════════════════════════
// ║ SMOKE mode (default): reads manifest/*.json only — no Python import,
// ║   no GPU probe. Fast (<1s). Exits 1 if any required gate is not admitted.
// ║
// ║ REPORT mode (--report): dumps full gate ladder JSON to stdout.
// ║
// ║ Gates:
// ║   C-G1  corpus_embed      manifest/claudine_corpus_meta.json
// ║   C-G2  cluster_analyze   manifest/claudine_clusters.json
// ║   C-G3  dataset_format    manifest/claudine_dataset_meta.json
// ║   C-G4  lora_train        manifest/claudine_train_run.json
// ║   C-G5  unsloth_stack     manifest/claudine_unsloth_probe.json
// ║   C-G6  adapter_inference manifest/claudine_inference_probe.json  (optional until run)
// ║   C-G4v2 lora_train_v2   manifest/claudine_train_run_v2.json  (optional)
// ╚════════════════════════════════════════════════════════════════════════════

import { existsSync, readFileSync } from "fs";
import { resolve } from "path";

const REPO_ROOT = resolve(import.meta.dir, "../..");
const MANIFEST_DIR = resolve(REPO_ROOT, "manifest");
const REPORT = process.argv.includes("--report");

// ── Types ─────────────────────────────────────────────────────────────────────

type GateStatus = "admitted" | "not_probed" | "failed";

interface GateResult {
  gate: string;
  description: string;
  status: GateStatus;
  proof: string;
  key_metrics?: Record<string, unknown>;
  notes?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function readJson(path: string): Record<string, unknown> | null {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, "utf-8"));
  } catch {
    return null;
  }
}

// ── Gate probers ──────────────────────────────────────────────────────────────

function probeCG1(): GateResult {
  const meta = readJson(resolve(MANIFEST_DIR, "claudine_corpus_meta.json"));
  if (!meta) {
    return {
      gate: "C-G1",
      description: "corpus_embed — nomic-embed-text-v1.5 over PNK .md corpus",
      status: "not_probed",
      proof: "manifest/claudine_corpus_meta.json missing",
    };
  }
  const admitted = meta.gate === "C-G1" && meta.status === "admitted";
  const shape = meta.embed_shape as number[] | undefined;
  return {
    gate: "C-G1",
    description: "corpus_embed — nomic-embed-text-v1.5 over PNK .md corpus",
    status: admitted ? "admitted" : "failed",
    proof: "manifest/claudine_corpus_meta.json",
    key_metrics: {
      num_files: meta.num_files,
      num_chunks: meta.num_chunks,
      embed_dim: shape ? shape[1] : undefined,
      elapsed_s: meta.elapsed_s,
    },
  };
}

function probeCG2(): GateResult {
  const clusters = readJson(resolve(MANIFEST_DIR, "claudine_clusters.json"));
  if (!clusters) {
    return {
      gate: "C-G2",
      description: "cluster_analyze — UMAP + HDBSCAN semantic clusters",
      status: "not_probed",
      proof: "manifest/claudine_clusters.json missing",
    };
  }
  const admitted = clusters.gate === "C-G2" && clusters.status === "admitted";
  return {
    gate: "C-G2",
    description: "cluster_analyze — UMAP + HDBSCAN semantic clusters",
    status: admitted ? "admitted" : "failed",
    proof: "manifest/claudine_clusters.json",
    key_metrics: {
      num_clusters: clusters.num_clusters,
      noise_chunks: clusters.noise_chunks,
      num_chunks: clusters.num_chunks,
      elapsed_s: clusters.elapsed_s,
    },
  };
}

function probeCG3(): GateResult {
  const meta = readJson(resolve(MANIFEST_DIR, "claudine_dataset_meta.json"));
  if (!meta) {
    return {
      gate: "C-G3",
      description: "dataset_format — completion-style JSONL training set",
      status: "not_probed",
      proof: "manifest/claudine_dataset_meta.json missing",
    };
  }
  const admitted = meta.gate === "C-G3" && meta.status === "admitted";
  return {
    gate: "C-G3",
    description: "dataset_format — completion-style JSONL training set",
    status: admitted ? "admitted" : "failed",
    proof: "manifest/claudine_dataset_meta.json",
    key_metrics: {
      num_examples: meta.num_examples,
      total_chars: meta.total_chars,
      avg_chars: meta.avg_chars,
      elapsed_s: meta.elapsed_s,
    },
  };
}

function probeCG4(): GateResult {
  const run = readJson(resolve(MANIFEST_DIR, "claudine_train_run.json"));
  if (!run) {
    return {
      gate: "C-G4",
      description: "lora_train — LoRA adapter trained on Mistral-7B-v0.3",
      status: "not_probed",
      proof: "manifest/claudine_train_run.json missing (training not yet complete)",
    };
  }
  const isDryRun = Boolean(run.dry_run);
  // admitted = gate field present with status, or status=completed + adapter_path + not dry-run
  const admitted =
    (run.gate === "C-G4" && run.status === "admitted") ||
    (run.status === "completed" && Boolean(run.adapter_path) && !isDryRun);
  return {
    gate: "C-G4",
    description: "lora_train — LoRA adapter trained on Mistral-7B-v0.3",
    status: isDryRun ? "not_probed" : (admitted ? "admitted" : "failed"),
    proof: "manifest/claudine_train_run.json",
    key_metrics: {
      steps: run.steps,
      final_loss: run.final_loss,
      elapsed_s: run.elapsed_s,
      adapter_path: run.adapter_path,
      dry_run: isDryRun,
    },
    notes: isDryRun ? "DRY-RUN only — full training not yet complete" : undefined,
  };
}

function probeCG4v2(): GateResult {
  const run = readJson(resolve(MANIFEST_DIR, "claudine_train_run_v2.json"));
  if (!run) {
    return {
      gate: "C-G4v2",
      description: "lora_train_v2 — FA2 + DoRA + RSLoRA + SFTTrainer packing (claudine-v2)",
      status: "not_probed",
      proof: "manifest/claudine_train_run_v2.json missing (optional — v2 not yet run)",
    };
  }
  const isDryRun = Boolean(run.dry_run);
  const admitted = run.gate === "C-G4v2" && run.status === "admitted" && !isDryRun;
  return {
    gate: "C-G4v2",
    description: "lora_train_v2 — FA2 + DoRA + RSLoRA + SFTTrainer packing (claudine-v2)",
    status: isDryRun ? "not_probed" : (admitted ? "admitted" : "failed"),
    proof: "manifest/claudine_train_run_v2.json",
    key_metrics: {
      steps: run.steps,
      train_loss: run.train_loss,
      elapsed_s: run.elapsed_s,
      use_dora: run.use_dora,
      use_rslora: run.use_rslora,
      packing: run.packing,
      attn_impl: run.attn_impl,
      dry_run: isDryRun,
    },
    notes: isDryRun
      ? "DRY-RUN only — full v2 training not yet complete"
      : run.resumed_from
      ? `resumed from ${run.resumed_from}`
      : undefined,
  };
}

function probeCG5(): GateResult {
  const probe = readJson(resolve(MANIFEST_DIR, "claudine_unsloth_probe.json"));
  if (!probe) {
    return {
      gate: "C-G5",
      description: "unsloth_stack — torch+triton+flash_attn+Unsloth+trl on Win/Python 3.14",
      status: "not_probed",
      proof: "manifest/claudine_unsloth_probe.json missing",
    };
  }
  const admitted = probe.gate === "C-G5" && probe.status === "admitted";
  const checks = probe.checks as Record<string, Record<string, unknown>> | undefined;
  return {
    gate: "C-G5",
    description: "unsloth_stack — torch+triton+flash_attn+Unsloth+trl on Win/Python 3.14",
    status: admitted ? "admitted" : "failed",
    proof: "manifest/claudine_unsloth_probe.json",
    key_metrics: {
      torch: checks?.torch?.version,
      triton: checks?.triton?.version,
      flash_attn: checks?.flash_attn?.version ?? checks?.flash_attn?.error,
      unsloth: checks?.unsloth?.version,
      trl: checks?.trl?.version,
    },
  };
}



function probeCG6(): GateResult {
  const probe = readJson(resolve(MANIFEST_DIR, "claudine_inference_probe.json"));
  if (!probe) {
    return {
      gate: "C-G6",
      description: "adapter_inference — prototype run, base vs. claudine-v1 side-by-side",
      status: "not_probed",
      proof: "manifest/claudine_inference_probe.json missing (run P-06 after C-G4 full run)",
    };
  }
  const admitted = probe.gate === "C-G6" && probe.status === "admitted";
  const perf = probe.performance as Record<string, unknown> | undefined;
  const samples = (probe.adapter_samples as unknown[]) ?? [];
  return {
    gate: "C-G6",
    description: "adapter_inference — prototype run, base vs. claudine-v1 side-by-side",
    status: admitted ? "admitted" : "failed",
    proof: "manifest/claudine_inference_probe.json",
    key_metrics: {
      num_prompts: samples.length,
      base_avg_tps: perf?.base_avg_tps,
      adapter_avg_tps: perf?.adapter_avg_tps,
      vram_after_adapter_gb: perf?.vram_after_adapter_gb,
      adapter_path: probe.adapter_path,
    },
  };
}

// C-G1..G5 are required. C-G6 is optional until adapter run completes. C-G4v2 is optional (v2 upgrade).
const REQUIRED_GATES = ["C-G1", "C-G2", "C-G3", "C-G4", "C-G5"];

const gates: GateResult[] = [probeCG1(), probeCG2(), probeCG3(), probeCG4(), probeCG5(), probeCG6(), probeCG4v2()];

const required = gates.filter((g) => REQUIRED_GATES.includes(g.gate));
const allAdmitted = required.every((g) => g.status === "admitted");
const notProbed = gates.filter((g) => g.status === "not_probed");
const failed = gates.filter((g) => g.status === "failed");

if (REPORT) {
  const report = {
    checked_at: new Date().toISOString(),
    gates,
    summary: {
      total: gates.length,
      admitted: gates.filter((g) => g.status === "admitted").length,
      not_probed: notProbed.length,
      failed: failed.length,
      all_admitted: allAdmitted,
    },
  };
  console.log(JSON.stringify(report, null, 2));
} else {
  // Smoke summary
  for (const g of gates) {
    const icon =
      g.status === "admitted" ? "✅" : g.status === "not_probed" ? "⏳" : "❌";
    const note = g.notes ? ` (${g.notes})` : "";
    console.log(`${icon} ${g.gate}  ${g.description}${note}`);
  }
  console.log("");
  if (allAdmitted) {
    console.log("✅ All Claudine LoRA gates admitted.");
  } else if (notProbed.length > 0) {
    const gates_str = notProbed.map((g) => g.gate).join(", ");
    console.log(`⏳ Gates pending: ${gates_str}`);
  } else {
    console.log(`❌ Gates failed: ${failed.map((g) => g.gate).join(", ")}`);
  }
}

process.exit(allAdmitted ? 0 : 1);
