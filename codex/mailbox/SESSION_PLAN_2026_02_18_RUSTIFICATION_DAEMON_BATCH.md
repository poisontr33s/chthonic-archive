---
type: session-plan
created: 2026-02-18
owner: codex
scope: TEMPLE
status: actionable
---

# Session Batch Plan: Rustification + Overnight Daemon

## Inputs Used
- Research source: `claude-codex-gemini/engineering_agentic_deep_research_candidates/gemini-deep-research-2026-02/ANNO_RUSTIFICATION_ENDO_DOT_LIFE.md`
- Daemon log (current): `dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-02-18_030002.log`
- Daemon log (stale failure): `dumpster-dive/intake/overnight-daemon/nightly-scheduled-2026-02-17_030002.log`
- Readiness baseline (refreshed): `codex/mailbox/LOCAL_AI_READINESS_LATEST.md`

## State Reassessment (2026-02-18)

### What was failing
- `2026-02-17` run failed in local refiner with:
  - `ModuleNotFoundError: No module named 'llama_cpp'`

### What is now true
- `2026-02-18` run completed without traceback.
- Local AI readiness refreshed and now reports:
  - `Scheduler log clean: True`
  - `Ready for skill integration: True`

### Remaining non-blocker
- `module:exllamav2` is still missing.
- This only affects legacy `local_refiner_v1`; primary `local_refiner_v2` is ready.

## Research Distillation (Curated)

### Core architectural claims to keep
- Rustified manager stack (`uv`, `rv`/`rvw`, `goup`, `bun`, `rustup`) is viable on Win11.
- Keep VS 2026 Insiders shell + stable build lane behavior for native toolchain consistency.
- Use `endoflife.date` lifecycle polling as update signal input, not direct blind auto-upgrade.
- Build Chthonic Archive around three panes:
  - Gate (state/compliance)
  - Lens (observability/debug)
  - Loom (build/dependency flow)

### Claims to treat as advisory only
- Any recommendation sourced from non-primary or weak references should not become policy until re-verified.
- Generated sample snippets in the research doc are conceptual; they need implementation-specific hardening before adoption.

## Hierarchical Execution Plan (Next Session)

## Phase 0: Stabilize Truth Sources
- [codex] Add a "source confidence" column to research digests (primary docs vs community/blog references).
- [codex] Patch `scripts/ingest_research.py` to normalize escaped markdown artifacts (`\*`, `\#`, escaped tables) before extraction.
- [manual] Decide whether `mise` is policy SSOT or optional overlay above existing `chthonic` manager lanes.

## Phase 1: Rustification Contract in Chthonic
- [chthonic] Encode canonical manager mapping:
  - Python=`uv`
  - Ruby=`rvw` (with `rv` collision guard)
  - Go=`goup`
  - JS=`bun`
  - Rust=`rustup/cargo`
- [chthonic] Add explicit status field for legacy/fallback lanes (`local_refiner_v1`).
- [chthonic] Add strict "no stale log" check: scheduler health must bind to newest nightly log timestamp.

## Phase 2: Overnight Daemon Hardening
- [codex] In daemon summary, split:
  - Runtime errors (tracebacks/module errors)
  - Content debt signals (TODO/FIXME/HACK hits)
- [codex] Ensure TODO scanner ignores literal regex/examples where TODO tokens are part of parser code.
- [codex] Add "run health verdict" to `report.json` so pipeline consumers avoid ambiguous status.

## Phase 3: Skill Integration Rollout
- [codex] Gate all local-LLM-consuming skills on `ready_for_skill_integration == true`.
- [codex] Add compatibility note in relevant skills: `local_refiner_v2` is primary, `v1` optional.
- [claude] Update mailbox protocol to reference latest readiness artifact path directly in handoff headers.

## Phase 4: Chthonic Archive Extension Track
- [codex] Convert research "Gate/Lens/Loom" into implementation tickets against existing extension paths.
- [chthonic] Add machine-readable toolchain state export for extension UI consumption.
- [manual] Confirm proposed API usage policy for VS Code Insiders before coding dynamic layout behavior.

## Immediate Session-Start Checklist (Next Run)
1. `uv run .codex/skills/trainstop-orchestrator/scripts/local_ai_readiness.py`
2. Confirm `codex/mailbox/LOCAL_AI_READINESS_LATEST.md` shows `Ready for skill integration: True`.
3. Run overnight daemon once and verify no traceback in newest `nightly-scheduled-*.log`.
4. Only then execute skill-chain orchestration.

## Decisions Needed
| Decision | Options | Recommendation |
|---|---|---|
| Canonical orchestrator model | `chthonic-only` vs `mise+chthonic` hybrid | Keep `chthonic` as runtime SSOT, allow `mise` as optional integration lane |
| Legacy lane support | Keep `local_refiner_v1` vs deprecate | Keep as optional fallback, do not gate pipeline on it |
| Auto-heal policy | Full auto-update vs review-gated | Use review-gated updates with explicit compatibility checks |

