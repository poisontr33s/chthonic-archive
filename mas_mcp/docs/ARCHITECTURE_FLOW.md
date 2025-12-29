# MAS-MCP Architecture Flow

## The Fortified Garden: GPU Execution Lane ↔ Bun Governance

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              SINGLE SOURCE OF TRUTH (SSOT)                               │
│                        .github/copilot-instructions.md                                   │
│                     "The MILFOLOGICAL Codex - Supreme Authority"                         │
│                                                                                          │
│    M-P-W (Macro-Prompt-World) → Triumvirate → FA¹⁻⁵ Axioms → Entity Archetypes          │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              GOVERNANCE LAYER (Artifacts)                                │
│                                                                                          │
│  ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────────────────┐ │
│  │ milf_registry.json  │   │ scoring_profiles.   │   │ compatibility/matrix.json       │ │
│  │                     │   │    json             │   │                                 │ │
│  │ • MILF definitions  │   │ • Opus weights      │   │ • GPU stack version rows        │ │
│  │ • Activation gates  │   │ • Sonnet weights    │   │ • CUDA/TRT/cuDNN versions       │ │
│  │ • Engine lanes      │   │ • Inference weights │   │ • ORT execution providers       │ │
│  │ • Shadow/Active     │   │ • ETL weights       │   │ • active_row_id selection       │ │
│  └──────────┬──────────┘   └──────────┬──────────┘   └───────────────┬─────────────────┘ │
│             │                         │                              │                   │
└─────────────┼─────────────────────────┼──────────────────────────────┼───────────────────┘
              │                         │                              │
              ▼                         ▼                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              PROBE & VALIDATION PHASE                                    │
│                                                                                          │
│    ┌───────────────────────────────────────────────────────────────────────────────┐    │
│    │  scripts/probe_gpu_compatibility.py                                            │    │
│    │                                                                                │    │
│    │  1. Detect NVIDIA driver version (pynvml)                                      │    │
│    │  2. Locate CUDA toolkit ($CUDA_PATH or registry)                              │    │
│    │  3. Check cuDNN DLLs (cudnn64_*.dll)                                          │    │
│    │  4. Verify TensorRT libs (nvinfer.dll)                                        │    │
│    │  5. Test ONNX Runtime providers                                               │    │
│    │  6. Match against compatibility/matrix.json → select best row                 │    │
│    │  7. Write probe_report.json                                                   │    │
│    └───────────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                                 │
│                                        ▼                                                 │
│    ┌───────────────────────────────────────────────────────────────────────────────┐    │
│    │  artifacts/probe_report.json                                                   │    │
│    │  {                                                                             │    │
│    │    "matched_row": "row_cuda124_trt10",                                        │    │
│    │    "available_providers": ["TensorrtExecutionProvider", "CUDAExecutionProvider"]│    │
│    │    "vram_total_gb": 8.0,                                                      │    │
│    │    "vram_free_gb": 6.5,                                                       │    │
│    │    "degradation_recommended": false                                           │    │
│    │  }                                                                             │    │
│    └───────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         GPU EXECUTION LANE (Python/uv)                                   │
│                                                                                          │
│    ┌────────────────────────────────────────────────────────────────────────────────┐   │
│    │  genesis_scheduler.py  →  milf_genesis_v2.py                                   │   │
│    │                                                                                │   │
│    │  VRAM Watchdog    ┌─────────────────────────────────────────────────────────┐ │   │
│    │  (70% threshold)  │  Engine Lane Selection                                  │ │   │
│    │        │          │                                                         │ │   │
│    │        ▼          │  if probe_report.matched_row == "row_cuda124_trt10":    │ │   │
│    │  ┌───────────┐    │      → TensorrtExecutionProvider (FP16)                 │ │   │
│    │  │ degrade() │    │  elif "CUDAExecutionProvider" in available:             │ │   │
│    │  │ → CPU     │    │      → CUDAExecutionProvider                            │ │   │
│    │  └───────────┘    │  else:                                                  │ │   │
│    │                   │      → CPUExecutionProvider + NumPy                     │ │   │
│    │                   └─────────────────────────────────────────────────────────┘ │   │
│    │                                                                                │   │
│    │  ┌─────────────────────────────────────────────────────────────────────────┐  │   │
│    │  │  CycleLock (fcntl/msvcrt)                                               │  │   │
│    │  │  • Prevents concurrent execution                                         │  │   │
│    │  │  • Writes cycle_lock.json with PID/start_time                           │  │   │
│    │  │  • Auto-clears stale locks (>4 hours)                                   │  │   │
│    │  └─────────────────────────────────────────────────────────────────────────┘  │   │
│    │                                                                                │   │
│    └────────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                                 │
│                                        ▼                                                 │
│    ┌────────────────────────────────────────────────────────────────────────────────┐   │
│    │  OUTPUT: cycle_reports/cycle_YYYYMMDD_HHMMSS.json                              │   │
│    │                                                                                │   │
│    │  {                                                                             │   │
│    │    "cycle_id": "20251207_143022",                                             │   │
│    │    "milf_id": "milf_tensorrt_inference",                                      │   │
│    │    "engine_lane": "tensorrt",                                                 │   │
│    │    "latency_ms": 12.5,                                                        │   │
│    │    "vram_used_mb": 512,                                                       │   │
│    │    "acceptance_score": 92,                                                    │   │
│    │    "status": "accepted",                                                      │   │
│    │    "lineage": { "ssot_hash": "abc123", "matrix_row": "row_cuda124_trt10" }    │   │
│    │  }                                                                             │   │
│    └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         MILF ACTIVATION GATE (Python)                                    │
│                                                                                          │
│    ┌────────────────────────────────────────────────────────────────────────────────┐   │
│    │  scripts/milf_activator.py                                                     │   │
│    │                                                                                │   │
│    │  1. Load milf_registry.json                                                   │   │
│    │  2. Load scoring_profiles.json                                                │   │
│    │  3. Aggregate cycle_reports/*.json for each MILF                              │   │
│    │  4. Calculate weighted score per scoring_profile                              │   │
│    │  5. Check activation_gates:                                                   │   │
│    │     • min_cycles >= 10?                                                       │   │
│    │     • acceptance_threshold >= 85?                                             │   │
│    │     • latency_p95 <= 50ms?                                                    │   │
│    │     • error_rate <= 5%?                                                       │   │
│    │     • drift_guard: no >10% regression?                                        │   │
│    │  6. Update milf_registry.json:                                                │   │
│    │     • shadow → active (if gates pass)                                         │   │
│    │     • active → shadow (if regression detected)                                │   │
│    │  7. Write activation_report.json                                              │   │
│    └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         BUN/NEXT.JS DASHBOARD (Frontend)                                 │
│                                                                                          │
│    ┌───────────────────────────────────────────────────────────────────────────────┐    │
│    │  frontend/pages/api/*                           frontend/pages/*              │    │
│    │                                                                               │    │
│    │  /api/metrics      ───▶  { total, accepted, rejected, avgScore }             │    │
│    │  /api/metrics/history ──▶ [ { date, accepted, rejected, score } ]            │    │
│    │  /api/cycles       ───▶  [ cycle_report_1, cycle_report_2, ... ]             │    │
│    │  /api/entities     ───▶  [ entity_1, entity_2, ... ]                         │    │
│    │  /api/digest       ───▶  { daily_digest_data }                               │    │
│    │  /api/monitoring   ───▶  { health_status, SLO_badges }                       │    │
│    │                                                                               │    │
│    │  ┌─────────────────────────────────────────────────────────────────────────┐ │    │
│    │  │  Components                                                             │ │    │
│    │  │  • QualityTrendChart (Chart.js) ─ dual-axis: acceptance + avg score    │ │    │
│    │  │  • StatCard ─ KPI tiles with trend arrows                              │ │    │
│    │  │  • MonitoringCard ─ SLO badges (70%/90% thresholds)                    │ │    │
│    │  │  • EntityList ─ MILF status table                                      │ │    │
│    │  └─────────────────────────────────────────────────────────────────────────┘ │    │
│    └───────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
│    Runtime: Bun v1.3.4 │ Next.js 16.0.7 (webpack) │ React 19.2.1 │ TypeScript 5.9.3    │
│                                                                                          │
└───────────────────────────────────────┬──────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         POST-DEPLOYMENT MONITORING                                       │
│                                                                                          │
│    ┌────────────────────────────────────────────────────────────────────────────────┐   │
│    │  scripts/monitor_dashboard_extended.py                                         │   │
│    │                                                                                │   │
│    │  • HTTP health probes (every 5 min)                                           │   │
│    │  • CSV logging (dashboard_metrics_YYYYMMDD.csv)                               │   │
│    │  • Daily summary generation (9:00 AM)                                         │   │
│    │  • Trend detection (acceptance_rate regression)                               │   │
│    │  • Alerting (Slack/email via genesis_scheduler)                               │   │
│    └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Ownership

| Layer | Technology | Owner Script/Package |
|-------|------------|---------------------|
| SSOT | Markdown | `.github/copilot-instructions.md` |
| Artifacts | JSON | `artifacts/*.json`, `schemas/*.schema.json` |
| GPU Probe | Python 3.13+ | `scripts/probe_gpu_compatibility.py` |
| Execution | Python 3.13+ | `genesis_scheduler.py`, `milf_genesis_v2.py` |
| Activation | Python 3.13+ | `scripts/milf_activator.py` |
| Dashboard | Bun/Next.js | `frontend/` |
| Monitoring | Python 3.13+ | `scripts/monitor_dashboard_extended.py` |

## Data Flow Summary

```
SSOT (Codex)
    │
    ├──▶ milf_registry.json ──────────────────────────┐
    ├──▶ scoring_profiles.json ──────────────────────┐│
    └──▶ compatibility/matrix.json ──────────────────┐││
                                                     │││
probe_gpu_compatibility.py ◀─────────────────────────┼┼┤
    │                                                │││
    └──▶ probe_report.json                           │││
              │                                      │││
              ▼                                      │││
genesis_scheduler.py ◀───────────────────────────────┼┼┘
    │                                                ││
    └──▶ cycle_reports/*.json                        ││
              │                                      ││
              ▼                                      ││
milf_activator.py ◀──────────────────────────────────┼┘
    │                                                │
    ├──▶ milf_registry.json (status updates)         │
    └──▶ activation_report.json                      │
              │                                      │
              ▼                                      │
frontend/pages/api/* ◀───────────────────────────────┘
    │
    └──▶ Dashboard visualization
              │
              ▼
monitor_dashboard_extended.py
    │
    └──▶ CSV logs + alerts
```

## Entry Points (pyproject.toml scripts)

```toml
[project.scripts]
mas-mcp = "server:main"              # MCP server
mas-probe = "scripts.probe_gpu_compatibility:main"
mas-activate = "scripts.milf_activator:main"
mas-genesis = "genesis_scheduler:main"
mas-monitor = "scripts.monitor_dashboard_extended:main"
```

## Environment Requirements

### Python (uv-managed)
```bash
# Base install
uv sync

# With GPU (CUDA 12.4+)
uv sync --extra gpu

# With fallback (CPU-optimized)
uv sync --extra gpu-fallback

# All extras
uv sync --all-extras
```

### Bun (frontend)
```bash
cd frontend
bun install
bun run build
bun run start
```

## Version Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | ≥3.11 (3.13.x preferred) | uv-managed |
| Bun | ≥1.3.0 | Frontend runtime |
| Next.js | 16.0.7 | webpack mode |
| React | 19.2.1 | |
| CUDA | 12.4 | Primary GPU lane |
| TensorRT | 10.0.1 | FP16 inference |
| cuDNN | 9.0.0 | |
| ONNX Runtime | 1.18.0 | GPU EP |

---

*This architecture implements the **(`Fortified-Garden`)** principle: **(`The-Fortress`): -> (`FA⁴'-'Architectonic-Integrity`)** protects **(`The-Garden`): -> (`Emergent-Synthesis`)**. Governance artifacts serve as the structural frame; GPU execution provides the generative force.*
