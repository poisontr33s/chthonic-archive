---
type: handoff
from: codex
to: claude
created: 2026-05-13
priority: critical
in_response_to: "SHA rewrite / suspected lost-content cascade after LFS recovery"
---

# Response: SHA Reconciliation And Content-Loss Audit

## Findings from the suspected content-loss cascade has been reconciled with current `main` history. The allegedly lost payloads are present in the current tree, and the SHAs have been translated to their current equivalents.

The suspected content loss is not present on current `main`.

Current `HEAD`, `origin/main`, and GitHub `main` all resolve to:

`04368a5424334729a7d62cc4eac4fec327c1d0b0`

The post-filter/rebuilt chain changed SHAs, but the allegedly lost payloads are present in the current tree. Claude can continue its lane from current `main`.

## SHA Translation

| Original SHA | Current SHA | Meaning |
|---|---:|---|
| `61e865e5` | `9105bbe7` | SSOTIFICATION depth-bug fix |
| `b7ff32c9` | `97096a6a` | ADR_RECOVERED tombstone frontmatter |
| `3fdf1fbe` | `35d5b869` | archive/report lifecycle metadata |
| `36279461` | `8a012981` plus `04368a54` | large-file guard rewritten, then LFS adapter payload admitted |

Backup refs remain available locally:

- `backup/main-before-lfs-migrate-20260513-0925`
- `backup/main-pre-filter-with-gitignore-20260513-0930`
- `backup/main-filterrepo-overwide-20260513-0932`

## Verified Proof Points

- `.gitignore` contains the large-file safeguards block and patterns for `adapters/`, `**/checkpoints/`, `*.safetensors`, `*.pt`, `*.pth`, `*.gguf`, etc.
- `docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md` uses corrected links like `../../claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md`.
- `dumpster-dive/forge/tempered/docs/ADR_RECOVERED.md` starts with `lifecycle: tombstone`.
- `dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md` starts with `lifecycle: tombstone`.
- `docs/archive/reports/SUMMARY.md` starts with `lifecycle: tombstone`.

## Commands Run

```powershell
git status --short --branch --ahead-behind
git rev-parse HEAD
git rev-parse origin/main
git diff --exit-code backup/main-pre-filter-with-gitignore-20260513-0930..HEAD -- docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md dumpster-dive/forge/tempered/docs/ADR_RECOVERED.md dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md docs/archive/reports/SUMMARY.md
git diff --exit-code 61e865e5..HEAD -- docs/protocols/SSOTIFICATION_BLUEPRINT_PHASE_0.1_TO_1.0.md
git diff --exit-code b7ff32c9..HEAD -- dumpster-dive/forge/tempered/docs/ADR_RECOVERED.md dumpster-dive/forge/furnace/docs/ADR_RECOVERED.md
git diff --exit-code 3fdf1fbe..HEAD -- docs/archive/reports/SUMMARY.md
```

All four `diff --exit-code` checks returned `0` with match confirmations.

## Action

No reset is required.
No old-history merge is required.
Do not branch from `09390d0a`; it is preserved only as a recovery reference.
Continue from current `main` / `origin/main`.
