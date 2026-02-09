# Claude Code Challenge Task: Session Sync (Chthonic Archive)

**Date:** 2026-02-09  
**Owner:** Claude Code (assistant)  
**Goal:** Catch up to the repository’s *current* reality end-to-end by reconstructing a faithful progression narrative from raw session logs to the present implementation state, then produce a concise “what exists / how to run it / what’s next” packet suitable for continuing work without re-litigating history.

This task is explicitly *not* asking for new features first. It is asking for **accurate synchronization**.

## Non-Negotiables

- Do not invent tools, scripts, or capabilities that don’t exist on disk.
- Prefer repo artifacts as truth: read the files, quote file paths, include exact commands.
- Keep secrets out of outputs. Never print tokens; never ask to commit them.
- Windows + PowerShell is the primary execution lane.

## Current State Snapshot (What Already Exists)

These are the “load-bearing” parts of the current system. Confirm each one by reading the file and/or running the command.

### Trainstop Orchestrator (Config-Driven Runner)

- Runner: `.codex/skills/trainstop-orchestrator/scripts/orchestrate.py`
- Lane config: `.codex/skills/trainstop-orchestrator/lane_config.v1.json`
- Latest run report: `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json`

Key behaviors to verify from code/config:

- Lane nesting (lanes can reference other lanes).
- `command` vs `command_template` (templates use `{input_path}`).
- `timeout_s` supported per step.
- Artifact validation supports globs and “fresh artifact” detection (pre/post snapshot).

### HF Auth + Dependency Prep (uv + Python 3.13)

- Token loader (SSOT for process env): `scripts/api_pool.ps1` (reads `C:\\Users\\erdno\\.chthonic\\api_pool.json`)
- HF auth probe: `scripts/hf_probe.py`
- HF dependency prep (verify/apply): `scripts/hf_prep.py`
- Latest readiness artifacts:
  - `codex/mailbox/HF_PREP_LATEST.md`
  - `codex/mailbox/HF_PREP_LATEST.json`

### HF MCP (Real MCP HTTP Inventory via huggingface_hub MCPClient)

- MCP inventory emitter: `scripts/mcp_client_emitter.py`
- Latest inventory artifact: `codex/mailbox/HF_MCP_TOOLS_LATEST.json`
- Timestamped inventory artifacts: `artifacts/hf_mcp_tools_*.json`

### MCP Validation (Local)

- MCP validator: `scripts/run_mcp_validation.ts`
- Timestamped validation artifacts: `artifacts/mcp_run_validation_*.json`

### HF Discovery (Hub API, Not MCP)

- Discovery script: `scripts/hf_discovery.py`
- Timestamped discovery artifacts: `artifacts/hf_discovery_*`

### Legacy/Support: HTML Registry Generator (Narrative-Injected)

- HTML-driven registry generator: `scripts/hf_mcp_service_registry.py`
- Generated outputs:
  - `artifacts/hf_mcp_service_registry.generated.py`
  - `artifacts/hf_mcp_service_registry.generated.*.registry.json`

## What You Must Produce (Artifacts For “Sync”)

Write these into `claude/mailbox/`:

1. `SESSION_CONTEXT_CHRONICLE_2026_02_09.md`
   - A chronological reconstruction (nascency -> now) of:
     - Why trainstop-orchestrator exists (deterministic “lanes” over ad-hoc runs).
     - How HF MCP was added/validated.
     - Why tokens are loaded via `scripts/api_pool.ps1` (and what drift occurred with `HF_TOKEN` precedence).
     - How/why `hf_prep.py` and `uv_autofix` gating works (explicit opt-in).
     - What artifacts are now authoritative.
   - Use explicit dates/timestamps where the repo already recorded them (mailbox JSON timestamps, artifact filenames).

2. `SESSION_SYNC_PACKET_2026_02_09.md`
   - “How to run the system now” in the smallest possible checklist.
   - Include exact commands (PowerShell) and expected artifacts.
   - Include a “failure triage” section with the 3 most common breakpoints (token drift, missing deps, MCP tool surface drift).

Optional (only if it materially helps accuracy):

3. `SESSION_SYNC_INDEX_2026_02_09.json`
   - A machine-readable index of key files you used with categories:
     - `logs`, `artifacts`, `scripts`, `configs`, `mailbox_reports`.

## Required Source Material (Read These, Don’t Guess)

At minimum, read and cite (by path) the following:

- `.codex/skills/trainstop-orchestrator/scripts/orchestrate.py`
- `.codex/skills/trainstop-orchestrator/lane_config.v1.json`
- `codex/mailbox/TRAINSTOP_ORCHESTRATOR_LATEST.json`
- `scripts/api_pool.ps1`
- `scripts/hf_probe.py`
- `scripts/hf_prep.py`
- `codex/mailbox/HF_PREP_LATEST.md`
- `scripts/mcp_client_emitter.py`
- `codex/mailbox/HF_MCP_TOOLS_LATEST.json`
- `scripts/run_mcp_validation.ts`
- A representative MCP validation artifact in `artifacts/` (newest timestamp)

Additionally, for “nascency” context:

- `codex/codex-session-logs/SESSION_TRAIL_00001.md`
- `codex/codex-session-logs/*resume*.md` (if present)
- `codex/codex-session-logs/*structured*.json` (if present)
- Any “SSOT” doc the user was iterating on (example: `codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md`)

## End-to-End Verification (Do This Before Writing Conclusions)

Run these commands and record outcomes (success/failure + which artifact was created).

1. MCP/Auth lane:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-auth --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

2. HF prep lane:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-prep --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

3. MCP client emitter lane:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-client-emitter --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

4. Optional: HF discovery lane:

```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-discovery --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

## Specific Questions You Must Answer In The Packet

- What is the single “truth lane” for HF auth, and where does it read tokens from?
- What is “uv pip”, and does it imply “two package repositories”?
  - Provide a short explanation grounded in this repo’s usage patterns (how scripts call `uv pip install` vs `uv run`).
- Which outputs are the authoritative “latest state” vs timestamped artifacts?
- What are the next 1-3 concrete, repo-native improvements that reduce user cognitive load (no “homework mode”)?

## Style Constraints

- Keep outputs technical and grounded.
- Avoid roleplay tone in these Claude outputs; this is operational documentation.

