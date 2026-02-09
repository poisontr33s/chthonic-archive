# Session Context Chronicle (2026-02-09)

This document reconstructs the chronological progression from nascency to the current implementation state of the chthonic-archive repository's automated tooling.

## Phase 0: Purification Chain + Cross-Flavor Skill Parity (Codex Lane ⇄ Claude Lane)

**Period:** 2026-02-05 to 2026-02-06 (ref: `claude/mailbox/SESSION_CONTEXT_CHRONICLE_2026_02_06.md`, `claude/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`)

Before the Hugging Face MCP work, the repo underwent a **structural stabilization pass** to prevent “two agents, two ecosystems, two incompatible skill formats” from fragmenting the toolchain.

### The conceptualize skill as the first “hard standard”

The earliest high-leverage “Codex-side identity” was codified as a **skill** and backed by a **protocol**:

- Codex skill: `.codex/skills/conceptualize/SKILL.md`
- Claude skill (parallel shape): `.claude/skills/conceptualize/SKILL.md`
- Protocol (Matriarch/Umeko): `.temple/protocols/MATRIARCH_PROTOCOL.md`

Key idea: the “Disco Elysium Skills Debate” mechanism (internal monologue structure) became a *repeatable audit template* that could be invoked deterministically (trigger words or explicit `/conceptualize`), instead of relying on vibe-driven reviews.

### Canonical path model (prevents entropy)

Established as non-negotiable:

- Codex skills live in: `.codex/skills`
- Claude skills live in: `.claude/skills`
- Codex mailbox lives in: `codex/mailbox`
- Claude mailbox lives in: `claude/mailbox`
- Hidden mailboxes (`.codex/mailbox`, `.claude/mailbox`) are sentinel-only

This is the foundation that made later “train lanes” viable: the runner can assume where things live.

### Bridge + parity posture (contract parity, not file parity)

The repo adopted a “**contract parity**” approach:

- Codex flavor enforces OpenAI-ish skill expectations (agent yaml, assets).
- Claude flavor uses Claude frontmatter and does not require OpenAI agent scaffolding.
- Bridge policy prevents forcing unnatural equivalence while still supporting cross-audits.

Evidence / artifacts already produced (2026-02-06):

- `claude/mailbox/skills_parity_map_2026_02_06.json`
- `claude/mailbox/SKILLS_PARITY_DISCREPANCY_2026_02_06.md`
- `claude/mailbox/KISS_PARITY_BRIEF_2026_02_06.md`

Operator command used for ongoing verification:

- `scripts/run_cross_audit.ps1`

### “No Task Dumping” (reduce cognitive load)

This is a policy layer added explicitly to stop “homework mode”:

- `.temple/protocols/NO_TASK_DUMPING_PROTOCOL.md`

Later HF/MCP work follows this: verify/apply gating, deterministic lanes, minimal required user actions (only when secrets/UI consent are unavoidable).

## Phase 1: Nascency - The Problem Space

**Period:** Early 2026 sessions (ref: `codex/codex-session-logs/SESSION_TRAIL_00001.md`)

The repository began as a creative writing project (Iron Maiden SSOT, see `codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md`) but accumulated significant technical debt:

- **Context overflow:** Gemini CLI and other agents hit context limits due to broad ingestion patterns.
- **Ad-hoc execution:** No deterministic workflow; each session ran commands manually.
- **Scattered artifacts:** Session logs, manifests, and packets were correct but dispersed across multiple locations.

**Key insight from SESSION_TRAIL_00001.md:**
> "The last actionable intent was to consolidate the session into a single 'large trail' artifact for rapid resumption."

## Phase 2: Trainstop Orchestrator (Deterministic Lanes)

**Why it exists:**

The "Train Stop" metaphor emerged to enforce disciplined maintenance: stop the work, run a fixed chain of checks/polishes, then resume. This replaced ad-hoc command runs with config-driven lanes.

**Implementation:**
- Runner: `.codex/skills/trainstop-orchestrator/scripts/orchestrate.py`
- Config: `.codex/skills/trainstop-orchestrator/lane_config.v1.json`
- Report: `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json`

**Key behaviors verified from code:**
1. **Lane nesting:** Lanes can reference other lanes (e.g., `all` lane includes `maintenance` + `mcp-auth`).
2. **Command templates:** `command_template` uses `{input_path}` for parameterized lanes like `resume`.
3. **Timeout support:** `timeout_s` per step (default varies, up to 1800s for heavy installs).
4. **Artifact validation:** Supports globs (`artifacts/*.json`) and "fresh artifact" detection via pre/post snapshot comparison.

## Phase 3: HF Auth/Prep Layer (Token Precedence Resolution)

**Why tokens are loaded via `scripts/api_pool.ps1`:**

Early sessions encountered token drift where:
- `HF_TOKEN` (from `huggingface-cli login` or other sources) could be stale.
- `HUGGINGFACE_HUB_TOKEN` is the newer canonical variable for `huggingface_hub`.
- Some tools read only one, causing silent auth failures.

**Resolution (ref: `scripts/api_pool.ps1:76-87`):**

The API pool loader reads from `~/.chthonic/api_pool.json` and:
1. Sets each env var for the current process only.
2. If `HUGGINGFACE_HUB_TOKEN` is present, it also sets/overrides `HF_TOKEN` to ensure compatibility.

**Token source of truth:** `C:\Users\erdno\.chthonic\api_pool.json` (never committed to repo).

**hf_probe.py behavior (lines 23-27):**
```python
# Prefer HUGGINGFACE_HUB_TOKEN when present (API pool), and ignore HF_TOKEN for this probe.
if os.getenv("HUGGINGFACE_HUB_TOKEN") and os.getenv("HF_TOKEN"):
    os.environ.pop("HF_TOKEN", None)
```

This ensures the probe tests the API pool's token, not a potentially stale `HF_TOKEN`.

## Phase 4: hf_prep.py and uv_autofix Gating

**Why explicit opt-in (`--apply`):**

The `hf_prep.py` script follows a verify/apply pattern:
- **Default (no flags):** Verify mode - checks deps, reports status, exits 0 (artifacts show what's missing).
- **`--apply`:** Actually installs missing deps via `uv pip install`.
- **`--strict`:** Exits non-zero if any check fails.

**uv_autofix gating (ref: `scripts/uv_autofix.py`):**

Some scripts (like `mcp_client_emitter.py`) call `ensure_deps()` which:
- Does nothing if deps are already installed.
- Raises `RuntimeError` if missing and `CHTHONIC_UV_AUTOFIX != 1`.
- Auto-installs via `uv pip install` only when explicitly enabled.

**Rationale:** Prevents surprise installs during read-only validation runs.

## Phase 5: HF MCP (Real MCP HTTP Inventory)

**What is HF MCP:**

Hugging Face exposes an MCP server at `https://huggingface.co/mcp` that lists tools for searching spaces, datasets, documentation, etc.

**Implementation:**
- Emitter: `scripts/mcp_client_emitter.py`
- Uses `huggingface_hub.inference._mcp.mcp_client.MCPClient` to connect via HTTP.
- Emits:
  - Timestamped: `artifacts/hf_mcp_tools_<timestamp>.json`
  - Latest: `codex/mailbox/HF_MCP_TOOLS_LATEST.json`

**Last verified output (2026-02-09T19:38:02Z):**
- Tool count: 6
- Tools: `space_search`, `hf_whoami`, `hf_doc_search`, `hf_doc_fetch`, `hub_repo_details`, `dataset_search`

## Phase 6: Local MCP Validation (chthonic-polyglot)

**What is chthonic MCP:**

The repository has its own MCP server (`scripts/mcp-chthonic-server.ts`) exposing 24 tools (10 polyglot + 11 archive + 3 meta).

**Validation runner:** `scripts/run_mcp_validation.ts`
- Spawns the server, sends JSON-RPC requests, validates responses.
- Emits: `artifacts/mcp_run_validation_<timestamp>.json`

**Required tool subset (from runner):**
- `chthonic_status`, `chthonic_scan`, `chthonic_validate_ssot`, `polyglot_versions`, `meta_cli`

## Authoritative Artifacts Summary

| Artifact Type | Latest Location | Timestamped Location |
|---------------|-----------------|----------------------|
| Orchestrator report | `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json` | (overwrites) |
| HF Prep | `codex/mailbox/HF_PREP_LATEST.json`, `HF_PREP_LATEST.md` | (overwrites) |
| HF MCP tools | `codex/mailbox/HF_MCP_TOOLS_LATEST.json` | `artifacts/hf_mcp_tools_*.json` |
| Local MCP validation | - | `artifacts/mcp_run_validation_*.json` |
| HF Discovery | - | `artifacts/hf_discovery_*.json`, `*.md` |

## End-to-End Verification (2026-02-09T20:21Z)

All lanes executed successfully:

1. **mcp-auth lane:** `codex mcp list` confirmed HF MCP server enabled; `hf_probe.py` returned `ok: esabbr`.
2. **hf-prep lane:** Verify + apply completed; all deps OK (transformers=5.1.0, datasets=4.5.0, accelerate=1.12.0).
3. **mcp-client-emitter lane:** Wrote `artifacts/hf_mcp_tools_2026-02-09T20-22-05-320Z.json`.

## Timeline Anchors

| Date | Event | Artifact |
|------|-------|----------|
| 2026-02-09 | Session 00001 consolidated | `codex/codex-session-logs/SESSION_TRAIL_00001.md` |
| 2026-02-09T17:44Z | MCP validation artifacts | `artifacts/mcp_run_validation_2026-02-09T17-44-*.json` |
| 2026-02-09T19:38Z | HF MCP tools inventory | `codex/mailbox/HF_MCP_TOOLS_LATEST.json` |
| 2026-02-09T20:03Z | HF Prep latest | `codex/mailbox/HF_PREP_LATEST.json` |
| 2026-02-09T20:22Z | Full sync verification | This chronicle |
