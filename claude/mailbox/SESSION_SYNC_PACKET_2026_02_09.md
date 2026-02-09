# Session Sync Packet (2026-02-09)

Operational checklist for running the chthonic-archive system.

## How to Run the System Now

### Prerequisites

1. **API Pool configured:**
   ```powershell
   # Check if api_pool.json exists
   Test-Path "$HOME\.chthonic\api_pool.json"

   # If missing, create template:
   .\scripts\api_pool.ps1 -Load
   # Then fill in HUGGINGFACE_HUB_TOKEN with your HF token
   ```

2. **Toolchain present:**
   - `uv` (0.10.0+): `uv --version`
   - `bun` (1.x): `bun --version`
   - `codex` CLI: `codex --version`

### Core Commands

**Load tokens for current shell (run first):**
```powershell
.\scripts\api_pool.ps1 -Load
```

**Run HF auth probe:**
```powershell
.\scripts\api_pool.ps1 -Load | Out-Null; uv run scripts/hf_probe.py
# Expected: ok: <username>
```

**Run mcp-auth lane (full validation):**
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-auth --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```
- Expected artifacts: `artifacts/mcp_run_validation_*.json`

**Run hf-prep lane (verify + install deps):**
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-prep --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```
- Expected artifacts: `codex/mailbox/HF_PREP_LATEST.json`, `HF_PREP_LATEST.md`

**Run mcp-client-emitter lane (HF MCP tool inventory):**
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-client-emitter --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```
- Expected artifacts: `artifacts/hf_mcp_tools_*.json`, `codex/mailbox/HF_MCP_TOOLS_LATEST.json`

**Run local MCP validation (standalone):**
```powershell
bun run scripts/run_mcp_validation.ts
```

### Available Lanes

| Lane | Purpose | Key Artifacts |
|------|---------|---------------|
| `maintenance` | Core repo hygiene (skill polish, mailbox) | `TATRAGRAMMATRON_SUMMARY_LATEST_CODEX.md` |
| `mcp-auth` | MCP + HF auth validation | `mcp_run_validation_*.json` |
| `hf-prep` | Verify/install HF deps | `HF_PREP_LATEST.json`, `HF_PREP_LATEST.md` |
| `mcp-client-emitter` | HF MCP tool inventory | `HF_MCP_TOOLS_LATEST.json` |
| `hf-discovery` | Hub API discovery (spaces/models) | `hf_discovery_*.json` |
| `all` | maintenance + mcp-auth | All above |

---

## Answers to Required Questions

### Q1: What is the single "truth lane" for HF auth?

**Answer:** The `mcp-auth` lane with step `hf_probe_api_pool`.

**Token source:** `C:\Users\erdno\.chthonic\api_pool.json`

**Flow:**
1. `api_pool.ps1 -Load` reads `api_pool.json` and sets `HUGGINGFACE_HUB_TOKEN` (and mirrors to `HF_TOKEN`).
2. `hf_probe.py` calls `HfApi(token=...)` and prints the authenticated username.

### Q2: What is "uv pip", and does it imply two package repositories?

**Answer:** No, `uv pip` is a single package manager operating on PyPI.

- `uv` is a fast Python package manager (Rust-based, compatible with pip commands).
- `uv pip install <pkg>` installs from PyPI into the current environment.
- `uv run <script>` executes Python with automatic dependency resolution from `pyproject.toml`.

**Repo usage pattern:**
- `uv run scripts/hf_prep.py` - runs script using project deps.
- `uv pip install transformers` - explicitly installs a package (used in apply mode).

There is no second package repository; all deps come from PyPI.

### Q3: Which outputs are authoritative "latest state" vs timestamped artifacts?

| Type | Authoritative Latest | Timestamped Historical |
|------|---------------------|------------------------|
| HF MCP Tools | `codex/mailbox/HF_MCP_TOOLS_LATEST.json` | `artifacts/hf_mcp_tools_*.json` |
| HF Prep | `codex/mailbox/HF_PREP_LATEST.json` | (none) |
| MCP Validation | (none) | `artifacts/mcp_run_validation_*.json` |
| Orchestrator | `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json` | (none) |

### Q4: What are the next 1-3 concrete improvements?

1. **Single-command full sync:** Create a `sync` lane that runs `mcp-auth` + `hf-prep` + `mcp-client-emitter` in sequence. Currently requires three separate invocations.

2. **MCP validation latest artifact:** The local MCP validation runner only writes timestamped artifacts. Add a `codex/mailbox/MCP_VALIDATION_LATEST.json` for consistency.

3. **Token expiry detection:** `hf_probe.py` currently only reports success/failure. Add a warning when the authenticated token is near expiry (HF tokens have TTLs).

---

## Failure Triage

### Breakpoint 1: Token Drift

**Symptom:** `hf_probe.py` returns `fail: LocalTokenNotFoundError` or wrong username.

**Diagnosis:**
```powershell
.\scripts\api_pool.ps1 -Load
[System.Environment]::GetEnvironmentVariable("HF_TOKEN", "Process")
[System.Environment]::GetEnvironmentVariable("HUGGINGFACE_HUB_TOKEN", "Process")
```

**Fix:** Update `~/.chthonic/api_pool.json` with a fresh token from https://huggingface.co/settings/tokens.

### Breakpoint 2: Missing Deps

**Symptom:** `RuntimeError: Missing deps: mcp, pydantic-settings...`

**Diagnosis:**
```powershell
uv run scripts/hf_prep.py --with transformers,datasets,accelerate
# Check output for FAIL lines
```

**Fix:**
```powershell
uv run scripts/hf_prep.py --apply --with transformers,datasets,accelerate
```

Or enable autofix:
```powershell
$env:CHTHONIC_UV_AUTOFIX = "1"
uv run scripts/mcp_client_emitter.py
```

### Breakpoint 3: MCP Tool Surface Drift

**Symptom:** `run_mcp_validation.ts` fails "Required tools present" check.

**Diagnosis:** HF or local MCP server changed its tool list.

**Fix:**
1. Run emitter to get fresh inventory: `uv run scripts/mcp_client_emitter.py --url https://huggingface.co/mcp --min-despair 0`
2. Compare `HF_MCP_TOOLS_LATEST.json` with previous version.
3. If local server, check `scripts/mcp-chthonic-server.ts` for tool registration changes.

---

## File Index

| Category | Key Files |
|----------|-----------|
| **Scripts** | `scripts/api_pool.ps1`, `scripts/hf_probe.py`, `scripts/hf_prep.py`, `scripts/mcp_client_emitter.py`, `scripts/run_mcp_validation.ts` |
| **Configs** | `.codex/skills/trainstop-orchestrator/lane_config.v1.json` |
| **Mailbox Reports** | `codex/mailbox/HF_PREP_LATEST.*`, `codex/mailbox/HF_MCP_TOOLS_LATEST.json`, `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json` |
| **Artifacts** | `artifacts/hf_mcp_tools_*.json`, `artifacts/mcp_run_validation_*.json`, `artifacts/hf_discovery_*.json` |
| **Logs** | `codex/codex-session-logs/SESSION_TRAIL_00001.md` |
