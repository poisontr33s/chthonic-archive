---
type: ops
status: active
created: 2026-02-07
---

# API Pool (Local Secrets, Stable Across IDE Updates)

## Goals
- Keep tokens out of the repo (no accidental commits).
- Keep auth stable across VS Code / terminal churn.
- Make tooling deterministic: scripts check presence, not values.

## Hugging Face (Recommended)
Preferred: `huggingface-cli login`
- Stores a cached token in your user profile (outside the repo).
- Survives VS Code updates and terminal restarts.
- Works with `huggingface_hub` and `uv run ...` scripts.

Probe (no secrets printed):
```powershell
uv run scripts/hf_probe.py
```

## Hugging Face (Env Var Alternative)
If you need env-var based auth, set a user-level variable:
```powershell
setx HUGGINGFACE_HUB_TOKEN "<your_token>"
```

Notes:
- This is user-profile persistent, not session-only.
- VS Code terminals may require a restart to see updated user env vars.

## Policy
- Do not store tokens in `codex/`, `claude/`, `.codex/`, `.claude/`, `.meta/`, or any repo file.
- Tools should only verify "auth present" and report non-secret identifiers.

