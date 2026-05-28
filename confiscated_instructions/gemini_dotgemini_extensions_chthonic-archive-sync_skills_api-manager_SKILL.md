---
name: api-manager
description: Local API/token manager for this repo (no secrets in git). Diagnoses auth drift and loads tokens into the current shell from the user API pool.
metadata:
  short-description: "Load + diagnose API tokens (HF/OpenAI/etc) without committing secrets"
  argument-hint: "pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Doctor"
tags:
  - api management
  - local secrets
  - auth diagnostics
  - powershell
  - environment variables
  - api tokens
---
# API Manager (Local Tokens + Drift Doctor)

This skill eliminates the “where do I put the token / why did it break after an update” loop by centralizing:
- local token storage (outside git): `C:\Users\<you>\.chthonic\api_pool.json`
- deterministic loading into the current PowerShell process
- auth diagnostics (no secrets printed)

## Commands

Doctor mode (prints what signals are present and what is overriding what):
```powershell
pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Doctor
```

Load tokens into current shell (process-only env vars):
```powershell
pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -Load
```

Fix Hugging Face precedence issues (clear `HF_TOKEN` in current shell):
```powershell
pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -FixHF
```

Verify Hugging Face auth (no secrets printed):
```powershell
pwsh -NoProfile -File .codex/skills/api-manager/scripts/api_manager.ps1 -VerifyHF
```

## Safety Contract
- Never prints tokens.
- Never writes secrets into the repo.
- Only creates/edits the user-profile file: `~/.chthonic/api_pool.json` (local machine only).

## Cross-Flavor Compatibility
- Canonical implementation lives here: `.codex/skills/api-manager/scripts/api_manager.ps1`
- Claude wrapper skill: `.claude/skills/api-manager/SKILL.md`
- Gemini wrapper skill: `.gemini/skills/api-manager/SKILL.md`
- Shared local secret store: `C:\Users\<you>\.chthonic\api_pool.json`
- Recommended keys: `HUGGINGFACE_HUB_TOKEN`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `POE_API_KEY`, `POE_API_KEY_1`, `POE_API_KEY_2`
