---
name: trainstop-orchestrator
description: Proxy runner that chains the repo's non-official maintenance skills/tools in a deterministic order (skill freshness gate -> toolchain doctor -> skill polisher -> mailbox polish -> scribe -> manifest checks).
metadata:
  short-description: "Chained maintenance proxy (non-official skills only)"
  argument-hint: "uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both [--apply]"
  triggers:
    - "rewind"
    - "train stop"
    - "orchestrate"
    - "proxy"
---

# Trainstop Orchestrator (Proxy)

This skill is the "rewind to Train Stop" proxy: it runs the maintenance lane in a strict order so each step informs the next.

## Scope
- Included: repo-local maintenance skills and scripts.
- Excluded: official OpenAI skills (do not modify or auto-run): `sora`, `imagegen`, etc.
- Auth loader contract: uses `.codex/skills/api-manager/scripts/api_manager.ps1` for HF/MCP-adjacent lanes.

## Order (Deterministic)
1. Skill freshness gate: stale unsafe pattern + refresh drift checks (`skill_freshness_gate.py`)
2. Toolchain health: Bun + uv
3. Skill integrity: `skill-polisher` (Codex flavor) on `.codex/skills`
4. Optional cross recon: `skill-polisher` (Claude flavor) on `.claude/skills`
5. Mailbox hygiene: archive churn (`scripts/mailbox_polisher.py`)
6. Packet + manifest refresh: `scripts/mailbox_scribe.py`
7. Contract checks: `scripts/check_mailbox_manifest.py`
8. Local-AI pivot gate: runtime/model/overnight readiness artifacts (`local_ai_readiness.py`)

## Commands

Verify-only (no writes except reports emitted by underlying tools):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both
```

MCP + auth validation lane (Codex MCP servers + HF auth probe):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-auth
```

Local AI readiness pivot lane (pre-skill integration gate):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --lane local-ai-readiness
```

Hugging Face discovery lane:
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-discovery
```

Hugging Face MCP client emitter lane:
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-client-emitter
```

Hugging Face prep lane (verify-only by default; add `--apply` to install):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane hf-prep
```

Run using the declarative lane config:
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target codex --lane mcp-auth --lane-config .codex/skills/trainstop-orchestrator/lane_config.v1.json
```

Apply (runs safe apply modes where supported):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --apply
```

Apply with iterative polishing (retries skill-polisher apply until clean or max iterations):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --apply --max-iterations 3
```

Poe smoke lane (validates available Poe account keys, then emits cross-transport audit):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --lane poe-smoke
```

Composite all lane (maintenance + mcp-auth + local-ai-readiness + poe-smoke):
```powershell
uv run .codex/skills/trainstop-orchestrator/scripts/orchestrate.py --target both --lane all
```

## Lane Config Reference

Declarative lane map (reference artifact; the current runner is implemented in `scripts/orchestrate.py`):
- `.codex/skills/trainstop-orchestrator/lane_config.v1.json`

## Outputs
- Updates mailbox artifacts under:
  - `codex/mailbox/`
  - `claude/mailbox/`
