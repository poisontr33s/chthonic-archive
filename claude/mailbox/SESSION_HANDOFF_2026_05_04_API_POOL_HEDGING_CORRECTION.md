---
type: handoff
from: codex
to: claude
created: 2026-05-04
priority: high
subject: api pool verification and hedging correction
---

# API Pool Verification: No Hedging

## What I Did
- Verified local pool presence at `C:\Users\eldno\.chthonic\api_pool.json`; last modified `2026-02-23 17:49:36` local time.
- Generated no-secrets registry reports:
  - `codex/mailbox/API_KEY_GAP_REPORT_20260504T052230Z.md`
  - `codex/mailbox/API_KEY_GAP_REPORT_20260504T052230Z.json`
  - `codex/mailbox/API_KEY_ENV_TEMPLATE_20260504T052230Z.env`
- Ran live Hugging Face auth after clearing `HF_TOKEN`; result: failed with `Invalid user token`.
- Ran live GitHub API auth using the pool `GITHUB_TOKEN`; result: failed with HTTP `401 Bad credentials`.
- Ran Poe direct key plus account 1 and account 2 model-list validation through `scripts/poe_lane.py`; all returned `382` models.
- Fixed `scripts/poe_transport_audit.py` so explicit Poe account IDs stay string-normalized when resolving credentials.
- Reran Poe transport audit and emitted latest audit payloads:
  - `codex/mailbox/POE_TRANSPORT_AUDIT_LATEST.md`
  - `codex/mailbox/POE_TRANSPORT_AUDIT_LATEST.json`
  - `claude/mailbox/POE_TRANSPORT_AUDIT_LATEST.md`
  - `claude/mailbox/POE_TRANSPORT_AUDIT_LATEST.json`

## Current State
- Pool, user env, and process env are aligned for `GITHUB_TOKEN`, `HUGGINGFACE_HUB_TOKEN`, `POE_API_KEY`, `POE_API_KEY_1`, and `POE_API_KEY_2`.
- `HF_TOKEN` is not stored in the pool, but user/process env contain it and it equals `HUGGINGFACE_HUB_TOKEN`.
- Required registry slots are present: `GITHUB_TOKEN`, `POE_API_KEY`, `POE_API_KEY_1`, `POE_API_KEY_2`, `HUGGINGFACE_HUB_TOKEN`.
- Live-valid tools:
  - Poe account 1: key accepted for model listing; control/app-creator probes are subscription-gated.
  - Poe account 2: key accepted and callable for `claude-sonnet-4.5` and `app-creator` over both OpenAI-compatible and SDK probes.
- Live-failing tools:
  - Hugging Face: `HUGGINGFACE_HUB_TOKEN` is invalid as of this check. `HF_TOKEN` also exists in env/user scope and can mask auth, but clearing it did not make HF pass.
  - GitHub: pool `GITHUB_TOKEN` is invalid as of this check; GitHub returned `401 Bad credentials`.
- Missing optional direct API keys in registry include OpenAI, Gemini, Anthropic, OpenRouter, Groq, Together, Fireworks, Replicate, Cohere, Pinecone, Tavily, Mistral, Perplexity, xAI, DeepSeek, Azure OpenAI, Voyage, Exa, Brave Search, SerpAPI, ElevenLabs, AssemblyAI, Cerebras, and LangSmith.

## Claude Instruction
- Do not say "probably", "appears", "should", or "maybe" for this state unless a fresh command was not run.
- Say `passed`, `failed`, `missing`, or `not checked`, and cite the command/artifact.
- Do not imply Hugging Face or GitHub are healthy until their live auth probes pass.
- Use Poe account 2 as the currently verified callable Poe lane; treat account 1 as model-list-valid but subscription-gated for the probed Claude/app-creator calls.

## Claude Correction Addendum
- Do not output visible intent-analysis such as "the user is giving me a status update" or "they are not asking me to do anything specific." That is process narration, not work.
- Do not end with a binary permission question when one path is blocked by secrets and another path is locally executable.
- If token rotation is required, state the blocker once, then continue with the non-secret work that remains available.
- If no work remains available, close with the exact blocker and verification command; do not ask the user to choose between blocked and unblocked lanes.
- For the pasted response pattern, the compliant close is:
  - `Proceeding with the local G7 embed path. HF and GitHub remain blocked pending token rotation; Poe account 2 is the verified callable Poe lane.`
- If the user explicitly asks only for status, give status only. If the user asks to move forward and a verified lane exists, execute it.

## How to Verify
Run:
```powershell
uv run scripts/poe_lane.py --mode models --account 2 --limit 1000 --json --timeout 30
uv run scripts/poe_transport_audit.py --accounts '1,2' --openai-max-tokens 1 --models-limit 400 --json
```

Expected: account 2 callable in transport audit; account 1 subscription-gated for the probed models.

## Blockers
- HF and GitHub require token rotation or correction in the local/user secret pool. No repo secret values were written.
