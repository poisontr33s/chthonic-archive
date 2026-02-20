---
type: decision-triage
created: 2026-02-19
owner: codex
source: Gemini 3 Pro deep-research response
status: actionable
---

# Gemini Deep Research Triage (2026-02-19)

## Accepted as implementation-grade

1. Model lane routing should prioritize Qwen3 lanes and demote GPT-OSS from strict JSON paths.
2. Proposed VS Code layout APIs must remain optional/guarded; stable fallback path is mandatory.
3. Native Win11 POSIX shell strategy should standardize on Git Bash (`sh.exe`) for POSIX scripts and `pwsh` for orchestration.
4. Solana/Agave lifecycle governance must not depend on `endoflife.date`; use upstream release polling.

## Requires caution before hard-coding

1. "Force `chat_format=\"chatml\"` for all cases" is too broad:
   - Keep this as a per-model override for failing GPT-OSS variants.
   - Do not assume a single chat format for every future model.
2. "LocalAI native = deprecate" is too absolute:
   - For this repo's native-first lane, direct `llama_cpp.server` is preferred now.
   - Keep LocalAI as optional lane if future Windows support matures.

## Implemented from this triage

1. Added Solana/Agave governance gate:
   - `scripts/check-solana-version.ps1`
   - Policy: fail when local CLI is more than N minor versions behind remote release.
   - Remote fallback order:
     - `anza-xyz/agave`
     - `solana-labs/solana`
2. Validated in this environment:
   - local `solana` = `3.1.8`
   - remote `anza-xyz/agave` latest = `v3.1.8`
   - drift status = OK

## Immediate next execution pass

1. Wire `check-solana-version.ps1` into host verification and nightly governance checks.
2. Add model routing constants for:
   - strict JSON lane: Qwen3 Instruct A3B
   - code lane: Qwen3 Coder A3B
   - GPT-OSS lane: experimental only
3. Add explicit per-model chat template overrides in the llama-cpp serving layer.

