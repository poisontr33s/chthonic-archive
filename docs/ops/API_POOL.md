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
For this repo, use the local pool so `uv run`, MCP helpers, and agent shells share the same token:
```powershell
.\scripts\api_pool.ps1 -SetHFToken
```

Create the token under **Access Tokens**, not the MCP page. The MCP page login is for browser/OAuth MCP access; `huggingface_hub` model downloads use the API token lane.

Probe (no secrets printed):
```powershell
.\scripts\api_pool.ps1 -VerifyHF
```

## GitHub (Consolidate VS Code/gh into Pool)
If VS Code or `gh` works but `GITHUB_TOKEN` fails, sync the working `gh` keyring token into the local pool:
```powershell
.\scripts\api_pool.ps1 -SyncGitHubFromGh
```

Verify the pool-loaded GitHub lane:
```powershell
.\scripts\api_pool.ps1 -VerifyGitHub
```

This reads the working `gh` keyring token while ignoring stale `GITHUB_TOKEN` process overrides, writes only to `~/.chthonic/api_pool.json`, and does not print the token.

## Hugging Face (Env Var Alternative)
If you need raw env-var based auth outside the pool loader, set a user-level variable:
```powershell
setx HUGGINGFACE_HUB_TOKEN "<your_token>"
```

Notes:
- This is user-profile persistent, not session-only.
- VS Code terminals may require a restart to see updated user env vars.

## Policy
- Do not store tokens in `codex/`, `claude/`, `.codex/`, `.claude/`, `.meta/`, or any repo file.
- Tools should only verify "auth present" and report non-secret identifiers.
