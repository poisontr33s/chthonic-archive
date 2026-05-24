---
type: policy
created: 2026-02-06
scope: huggingface-auth
---

# Hugging Face Token Policy (Stable Auth)

## Goal
Make Hugging Face auth stable for tools and agents without committing secrets to the repo.

## Rule
- Do not store tokens in git-tracked files.
- Prefer `huggingface-cli login` (token cached outside the repo) or `HUGGINGFACE_HUB_TOKEN` loaded via the local API pool.
- Avoid setting `HF_TOKEN` unless you deliberately want it to override the CLI cache. `HF_TOKEN` takes precedence and can break auth if stale.

## Setup (PowerShell)
### Option A: Hugging Face CLI (Recommended)

```powershell
huggingface-cli login
```

### Option B: API Pool (Recommended for VS Code churn)

Create/update `C:\Users\<you>\.chthonic\api_pool.json` and load:

```powershell
.\scripts\api_pool.ps1 -Load
```

### Option C: Env Var (Use Carefully)

Set for current session:

```powershell
$env:HUGGINGFACE_HUB_TOKEN="hf_...redacted..."
```

Persist for future sessions (user-level):

```powershell
setx HUGGINGFACE_HUB_TOKEN "hf_...redacted..."
```

After `setx`, open a new terminal.

## Verification

```powershell
uv run scripts/hf_probe.py
```

## Notes
- Fine-grained tokens are preferred.
- If a token is ever pasted into chat/logs, rotate it.
- If `uv run scripts/hf_probe.py` says `HF_TOKEN ... is invalid`, unset `HF_TOKEN` (it overrides other auth):

```powershell
pwsh -NoProfile -File .\scripts\hf_auth_doctor.ps1 -UnsetProcessHFToken
```
