# Tabby Modernization — Scaffold Decision

<!--
@SID:           REF_TABBY_MODERNIZATION_SCAFFOLD_DECISION_V1
@Type:          Architecture Decision Record
@Context:       tabbyAPI / Python 3.14 GPU inference host — post E2E gate epoch
@SessionOrigin: E2E_GATE_EPOCH_2026_04_25
@References:    FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md, docs/ops/PROBE_CONTRACT.md
-->

**Version:** v0.1  
**Status:** Decision recorded — scaffold path selected, implementation pending  
**Epoch:** E2E gate PASSED (2026-04-25, commit `2241ed22`)  
**Gate foundation:** G1 L4, G2 L4, G3 L4, G4 `impossible_currently`, G5 L4, G6 L1  
**Filed:** 2026-04-25

---

## 0. Decision Summary

> **Path selected: `apps/tabby-modern/` — new Python 3.14-native scaffold with tabbyAPI as library.**

The `dev/tabbyAPI/` force-patch path is rejected. Rationale follows.

---

## 1. Chronology — What Had to Be Built Before This Decision

The scaffold decision is not the start of this lanework — it is the conclusion of a prerequisite infrastructure sprint. The sequence below is the mandatory task hierarchy that had to complete before the scaffold could be responsibly chosen.

### 1.1 — Why Oversight Infrastructure Preceded Everything

VS Code Copilot agent has no PID-based terminal scrollback access. The available surfaces are:

| Surface | Scope |
|---------|-------|
| `terminal_last_command` | Last command + output only |
| `terminal_selection` | User-selected text only |
| `get_terminal_output` | Agent-launched terminals only (UUID required) |

Without persistent output storage, every probe result would be lost at session boundary. The gate ladder could not be verified across sessions. The CI could not read anything. This is the structural constraint that forced the `manifest/*.json` architecture as a prerequisite — not a choice.

### 1.2 — Infrastructure Sprint (chronological)

| Phase | Artifact | Commit | Function |
|-------|----------|--------|----------|
| **PID reader** | `scripts/chthonic-shell-hook.ps1` | `dfb63f02` | PSReadLine instrumentation; every pwsh command → `manifest/terminal_session.jsonl` + `manifest/terminal_pids.json`. Ground truth for session visibility. |
| **Session query** | `scripts/terminal_session_query.ts` | `dfb63f02` | Reads `terminal_session.jsonl`; `--pid`, `--last`, `--grep`, `--failed`, `--sid`. PATCH_FILTER_BYPASS (merge logic preserved `_patch:true` → `applyFilters` excluded all entries → empty output) diagnosed and fixed at line 106: `{ ...entry, _patch: false }`. |
| **Terminal CI gate** | `ci/checks/terminal-hook-smoke.ts` | `9b2a2d70` | PATCH_FILTER_BYPASS regression detector via `stale_patch_entries` field. |
| **Probe ladder G1–G6** | `probes/python/P-0{1..6}.py` | various | Python 3.14 GPU inference stack, each probe → `manifest/*.json`. Gate results: G1 L4, G2 L4, G3 L4, G4 `impossible_currently`, G5 L4, G6 L1. |
| **Inference CI gate** | `ci/checks/inference-gate-smoke.ts` | `f36442eb` | Reads `manifest/` probe outputs → structured exit 0/1. G1-G3,G5=L4, G6=L1. |
| **GH run manifest** | `scripts/gh_run_pull.ts` | `d7ae56ae` | Pulls GitHub Actions run data → `manifest/gh_runs/index.json` + `failures.json`. Upstream extension of CI membrane pattern. |
| **GH run CI gate** | `ci/checks/gh-run-smoke.ts` | `d7ae56ae` | Reads `manifest/gh_runs/`; reports `dispatch_consecutive_fail` signal. |
| **Dispatch workflow fix** | `.github/workflows/pentea-cloud-dispatch.yml` | `d7ae56ae` | YAML corruption root-caused: mid-word linebreak artifacts in base64-decoded content (`Pen↵tea-Next:` bare YAML key) + broken indentation in `.yml.off`. Rewrote from scratch. Run `24934808239` → `conclusion=success`. |
| **E2E sweep** | 19 shebang files + 2 blessing files | `2241ed22` | Pre-existing failures cleared: `# ` → `#` whitespace in encoding lines (shebang-guard canon), blessing-gate envelope drift in 2 scripts. CI 8/8 green. |

### 1.3 — Why the Dispatch Workflow Had to Be Fixed Before Scaffold

`pentea-cloud-dispatch.yml` had been failing on every push (5 consecutive failures). The root cause was YAML corruption — GitHub aborted the run before any job spawned, so `gh run view --json jobs` returned `{"jobs":[]}`. This meant:

1. The `dispatch_consecutive_fail` signal in `gh-run-smoke.ts` would have blocked any CI membrane confidence signal
2. Autonomous agent dispatch on push would remain non-functional
3. The scaffold phase would launch into a broken CI signal environment

The fix was a pre-condition, not optional scope expansion.

---

## 2. Gate Ladder Summary (E2E Gate Epoch)

| Gate | Question | Level | Status |
|------|----------|-------|--------|
| G1 — Python 3.14 Resolver Coherence | Can uv resolve a GPU-backend wheel stack for Python 3.14? | L4 | `admitted` |
| G2 — pydantic-core PyO3 ABI | Can pydantic-core on Python 3.14 pass tabbyAPI's validation? | L4 | `admitted` |
| G3 — torch CUDA Discovery | Can Python 3.14 discover a CUDA device via torch? | L4 | `admitted` — RTX 4090, cuda_available=True, device_count=1, SM 8.9 |
| G4 — exllamav2 cp314 Wheel | Can exllamav2 be loaded on Python 3.14? | L0 | `impossible_currently` — v0.3.2 highest=cp313 |
| G5 — exllamav3 cp314 Wheel | Can exllamav3 be loaded on Python 3.14? | L4 | `admitted` — 0.0.30 imports clean; triton warning non-fatal |
| G6 — flash_attn cp314 Source Build | Can flash_attn be built on Python 3.14? | L1 | `admitted` — P-06: MSVC 14.44.35207, CUDA 12.8, 60m 42s |

**Critical path:** G4 (`impossible_currently`) eliminates the `exllamav2` backend for tabbyAPI on Python 3.14. The `exllamav3` backend path (G5+G6 both admitted) is the functional forward path.

---

## 3. Scaffold Options

### Option A — Force-Patch `dev/tabbyAPI/`

**Approach:** Modify the upstream tabbyAPI submodule in-place to support Python 3.14, exllamav3 backend, and the proven dependency stack.

**Constraints:**
- `dev/tabbyAPI/` is a git submodule tracking `theroyallab/tabbyAPI` upstream
- All force-patches create merge drift with upstream — each upstream update risks undoing patches
- tabbyAPI's default backend assumes `exllamav2`; rewiring to `exllamav3` requires modifying backend dispatch logic in the upstream codebase
- pyproject.toml overrides (pydantic pin bypass, direct-URL wheel entries) are already applied in the submodule — these would require ongoing rebase maintenance
- The upstream project has no Python 3.14 support commitment — patches may need to be re-applied on every upstream tag bump

**Assessment:** High maintenance burden. Every upstream release cycle requires a rebase + patch re-application pass. The exllamav3 backend wiring lives in upstream-owned files with no clean injection point.

### Option B — New Scaffold `apps/tabby-modern/`

**Approach:** Python 3.14-native project scaffold that uses tabbyAPI as a library dependency, not a submodule. Owns the entrypoint, dependency tree, and backend selection layer.

**Architecture:**
```
apps/tabby-modern/
├── pyproject.toml          ← Python 3.14 native, cu12 extras, proven gate stack
├── main.py                 ← entrypoint — wires exllamav3 backend, owns startup sequence
├── backends/
│   ├── exllamav3_host.py   ← exllamav3 inference host (G5 admitted)
│   └── stub.py             ← no-GPU fallback (for CI/test environments)
├── tests/
│   └── test_host_contract.py ← port of 17/17 test_start_ps1 contract to Python
├── .python-version         ← 3.14
└── uv.lock
```

**Key properties:**
- tabbyAPI imported as a library — upstream submodule churn is isolated from this scaffold
- Dependency tree owned here: torch 2.11.0+cu128, exllamav3 0.0.30, flash_attn 2.8.3, pydantic-core 2.46.x — all proven by gate ladder
- Backend dispatch is explicit: `exllamav3_host.py` is the primary backend; no exllamav2 assumption
- G4 (`exllamav2 impossible_currently`) does not block this path — exllamav2 can be added as optional when the cp314 wheel ships
- `pyproject.toml` carries the same `override-dependencies`, `[tool.uv.sources]`, `[[tool.uv.index]]` patterns proven in Gate 1
- CI integration: `ci/checks/inference-gate-smoke.ts` already validates the gate stack; scaffold tests extend that baseline

**Assessment:** Clean separation of concerns. Gate ladder artifacts (probes, manifests, CI gates) transfer directly to this scaffold with zero rework. Upstream submodule is decoupled.

---

## 4. Decision

**`apps/tabby-modern/` — Option B — selected.**

### Rationale

1. **G4 eliminates the exllamav2 baseline.** tabbyAPI's upstream default backend is exllamav2. Force-patching `dev/tabbyAPI/` to use exllamav3 means patching the default dispatch layer in upstream-owned code. Option B owns that dispatch layer natively.

2. **Gate ladder proves the stack, not the submodule.** G1–G6 validated individual capability gates against the Python 3.14 host. They did not validate tabbyAPI-as-a-service end-to-end. The scaffold is where that validation happens — and it should happen in code we own.

3. **Submodule churn cost is real.** `dev/tabbyAPI/` has already accumulated Python version, pydantic override, and test suite patches. Each upstream release requires reconciliation. Option B removes that coupling permanently.

4. **CI membrane is ready.** `ci/run.ts` 8/8 green means the scaffold launches into a clean CI environment. The inference gate smoke check (`ci/checks/inference-gate-smoke.ts`) already validates G1–G3,G5,G6 against `manifest/`. The scaffold just needs to produce probe output in the same manifest format.

5. **flash_attn L1, not L4.** flash_attn is installed (L1) but not yet validated at L3/L4 (call-level usefulness under the exllamav3 dispatch path). The scaffold test suite will be the vehicle for driving that gate to L4 — not a force-patch in an upstream file.

---

## 5. Scaffold Entry Contract

The scaffold is admitted when the following gate opens:

```
apps/tabby-modern/ exists
uv run pytest tests/test_host_contract.py → 0 failures
bun run ci/run.ts → 8/8 (or better) with new tabby-modern check registered
manifest/tabby_modern_host.json emitted by first probe run
```

Impossible-currently boundaries that remain blocked at scaffold time:
- exllamav2 backend (G4) — deferred, no cp314 wheel upstream
- flash_attn L4 call-level gate — deferred to scaffold test suite
- ruff py314 target — advisory, non-blocking

---

## 6. Authority Chain

This decision derives from the gate ladder evidence in:
[FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md](FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md) §3, §4, §9, §11

It does not override SSOT. It records an architectural choice within the proven capability boundary.
