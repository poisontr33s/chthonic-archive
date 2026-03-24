---
name: toolchain-doctor
description: Diagnose and remediate common Bun + uv drift in this repo (audit vulnerabilities, lockfile inconsistencies, uv sync health) with an opt-in apply mode that only performs safe fixes.
metadata:
  short-description: "Bun + uv health checks and safe remediation"
  triggers:
    - "bun audit"
    - "uv sync"
    - "toolchain drift"
    - "dependencies broken"
---

# Toolchain Doctor (Bun + uv)

This skill is a deterministic health-check and repair loop for the two package lanes in this repo:
- JavaScript: `bun` (lockfile + `bun audit`)
- Python: `uv` (lockfile + `uv sync`)

It produces a single report in `codex/mailbox/` and can optionally apply conservative fixes.

## Commands

Audit only (no writes):
```powershell
uv run .codex/skills/toolchain-doctor/scripts/toolchain_doctor.py --bun --uv
```

Bun audit with safe auto-remediation:
```powershell
uv run .codex/skills/toolchain-doctor/scripts/toolchain_doctor.py --bun --apply
```

## Output
- `codex/mailbox/TOOLCHAIN_DOCTOR_LATEST.md`
- timestamped report (referenced from latest)

## Safety Contract
- Never writes secrets.
- `--apply` only performs safe edits:
  - Updates vulnerable direct deps when a safe `bun update <pkg>` is available.
  - Removes known-problematic dev deps only if they are unused (no ripgrep hits outside manifests/lockfiles).

## Auth Notes (Hugging Face)
- This skill now includes a Hugging Face auth probe (no secrets printed).
- Preferred durable auth: `huggingface-cli login` (cached outside VS Code).
- See `docs/ops/API_POOL.md` for the repo policy and options.
