---
date: 2026-06-30
agent: Codex
source: Gemini Deep Research returns
status: ingested-with-corrections
plan: CLAUDEBASE/harbor/wide-sweeps-inventory-management-plan-2026-06-30.md
---

# Wide Sweeps Boomerang Return Digest

Two Gemini extended research returns were ingested:

| Source | Role |
|---|---|
| `CLAUDEBASE/sub-surface-skinny-dipping/sub-terranean-refreshed-returns/gemini-dr/boomerang-sweep-skills-false-positives.md` | long-form epistemic / structural audit |
| `CLAUDEBASE/sub-surface-skinny-dipping/sub-terranean-refreshed-returns/gemini-dr/hardening.infra.audit-eval-wide-sweeps.md` | more compact hardening / execution audit |

Both returns are useful. Both also hallucinate or overfit in places. Research informs the plan; it does not become the plan.

## Findings

| Severity | Finding | Verdict | Action |
|---|---|---|---|
| Critical | Both reports say the plan is truncated at Section 1.1 | Rejected as local-file false positive | local plan has 617 lines and reaches Section 8 |
| High | Separate stable invariants from local facts | Accepted | patched plan with `Invariants Versus Local Facts` |
| High | Agency Surface must remain first | Accepted | plan already reordered; retained |
| High | Skill auditors cannot bootstrap-audit skills | Accepted | retained contamination rule; `skill-polisher` remains specimen |
| High | MCP declaration needs boot/usefulness proof | Accepted | patched MCP section with unresolved handshake probe requirement |
| High | Raw duplicate counts can become false progress | Accepted | patched routing queues: Quarantine, Rehabilitation, Promotion, Historical sediment |
| High | Bare `rv` is dangerous | Accepted, refined | plan now says bare `rv` is forbidden in repo automation; use `rvw` / `rv-r.ps1` |
| Medium | Ruby-scoped MSYS/RIDK should not be globalized casually | Accepted | plan now warns not to add Ruby MSYS to global PATH casually |
| Medium | Static version values can overfit | Accepted | plan now labels local versions as evidence, not law |
| Medium | Visual/VS Code checksum warning is an expected mutation proof | Rejected as over-broad | Chthonic target state is owned patch + reconciled checksum, not permanent warning |
| Medium | Need output schema for future runs | Accepted | digest records schema direction; plan has first-run required tables |

## Decisions

| Decision | Options | Recommendation |
|---|---|---|
| First wide sweep | Toolchain first / Agency first / Movement first | Agency first, because stale agency surfaces poison all later tool use |
| Skill audit method | use `skill-polisher` / manual static bootstrap / skip skills | manual static bootstrap first; skill tools only after rehabilitation |
| MCP promotion | declared / entrypoint-reachable / boot-proven / useful | do not promote beyond entrypoint-reachable until handshake/client-visible proof exists |
| Version handling | freeze observed versions / record as local facts / omit versions | record as local facts, rerun proof before acting |
| VS Code substrate warnings | treat warning as success / reinstall / reconcile owned patch | reconcile owned patch; never reinstall reflexively |
| Ruby MSYS/RIDK | globalize PATH / treat as missing / private wrapper policy | treat as private Ruby/RIDK lane unless a wrapper policy is deliberately created |

## Accepted Invariants

| Invariant | Why it matters |
|---|---|
| Declared does not mean reachable; reachable does not mean bootable; bootable does not mean useful; useful does not mean authoritative. | prevents MCP and tool-config hallucinations |
| The first audit of an audit system must not use the audit system. | prevents recursive skill-polisher style false positives |
| Missing global command does not prove missing capability. | catches Ruby-scoped MSYS/RIDK and other private toolchains |
| Local inventory facts are evidence, not law. | prevents version and file-count overfitting |
| Counts must route into queues. | prevents inventory theater |
| Visual substrate proof has layers. | separates main-process proof, renderer proof, checksum proof, and human-eye calibration |
| Bare ambiguous commands are forbidden in automation. | prevents `rv`/PowerShell/R/Ruby collision damage |

## Rejected Or Downgraded Claims

| Claim | Why rejected or downgraded |
|---|---|
| The plan is physically truncated at Section 1.1. | local file has 617 lines and includes Sections 5, 6, and 8; the research likely saw an excerpt |
| Checksum failure is definitive proof of success. | too Vibrancy-generic; Chthonic reconciles checksum after owned patching |
| Agents should check VS Code Developer Tools for Vibrancy running. | wrong target; Vibrancy is a reference source, not the active dependency |
| Use hooks/pre-commit to block dot/non-dot writes immediately. | plausible later; premature until Agency Surface bootstrap maps actual write flows |
| Add global MSYS/PATH wrappers now. | premature; first classify Ruby/RIDK-private use and wrapper boundary |
| Use a specific MCP inspector command now. | useful direction, but no local in-house probe has been selected or proven |

## Plan Amendments Applied

| Plan area | Applied change |
|---|---|
| `0.1 Current Toolchain Surface` | bare `rv` is now forbidden in repo automation; Ruby MSYS/RIDK should not be globalized casually |
| `0.8.1 Invariants Versus Local Facts` | added invariant/local fact/hypothesis/stale-risk/style distinction |
| `1.5 Routing Queues` | added Quarantine, Rehabilitation, Promotion, Historical sediment |
| MCP section | added unresolved handshake probe note |
| False-positive kill switches | GUI unchanged now requires main-process, renderer, checksum, and human-eye proof separation |
| Movement 1 C0 | added Chthonic-specific checksum nuance |

## Actionable Checklist

| Route | Action | Status |
|---|---|---|
| `[codex]` | Preserve the current plan as corrected draft, not final canon | done |
| `[codex]` | Patch plan with accepted research invariants | done |
| `[codex]` | Reject truncation finding explicitly | done |
| `[chthonic]` | Next run: Agency Surface bootstrap with no skill invocation | queued |
| `[chthonic]` | Convert skill duplicate counts into queues | queued |
| `[chthonic]` | Design in-house MCP handshake probe | queued |
| `[chthonic]` | Design private Ruby/RIDK MSYS wrapper policy | queued |
| `[manual]` | Keep coffee lane separate from execution lane | ongoing |

## Dependencies And Install Vectors

No new dependency is approved by this digest.

| Candidate | Vector | Status |
|---|---|---|
| MCP handshake probe | likely `uv` or Bun, in-house | design only |
| static skill parser | likely `uv run` PowerShell/Python hybrid | design only |
| Ruby/RIDK MSYS wrapper | PowerShell script | design only |
| `mise.toml` | root policy manifest or actual manager config | design only |

## Conflicts

CONFLICT: The reports request completion of a supposedly truncated plan section. Local file proof rejects this.

CONFLICT: The reports recommend treating checksum warnings as expected success. That applies to generic Vibrancy-style patching, not the current Chthonic target state.

CONFLICT: The reports recommend stronger execution machinery, but the current plan is intentionally a challenge/routing artifact. Do not turn it into a monolithic maintenance script.

## Next Move

Do not open Toolchain yet.

Open **Agency Surface Bootstrap** next:

1. no skills invoked;
2. static file reads only;
3. classify dot/non-dot roots;
4. classify skills into queues;
5. classify MCP declarations into proof levels;
6. write `CLAUDEBASE/harbor/agency-surface-bootstrap-2026-06-30.md`;
7. only then decide whether Toolchain or Movement 1 gets the next batch.

