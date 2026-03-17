---
sid: SESSION_PREAMBLE_2026_03_11
title: Session Preamble — 2026-03-11 Cross-Reference Summary
type: session-preamble
status: ACTIVE
created: 2026-03-11
scope: local-ai-stack · oxidized-toolchain · ankh-gaps · oxidized-index · lora-pipeline
feeds: STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md · TASK_SCHEDULE_2026_03_11.md
---

<!--
@SID:    SESSION_PREAMBLE_2026_03_11
@Type:   Session Preamble / Resumption Index
@Context: Full cross-reference for 2026-03-11 session. Read this first.
@AutoFix: uv run scripts/link_audit.py check claude/mailbox/SESSION_PREAMBLE_2026_03_11.md --fix
-->

# Session Preamble — 2026-03-11

> Single-file entry point for resuming from this session. All work cross-referenced. Read left-to-right: what we did → what we made → what's pending → known gaps.

---

## Session Summary

Three major tracks were designed and delegated:

| Track | Goal | Status |
|-------|------|--------|
| **A — Infrastructure** | mistralrs serving local model on port 8080; overnight daemon consuming it | Spec complete, delegated to Codex (C1–C7) + User (U1–U3) |
| **B — OxidizedIndex** | Rust CLI registry of Rust-native toolchain managers with Win11 probe | Spec+data tasks assigned to Claude (B1–B3), implementation to Codex (B4–B6) |
| **C — ANKH / Lore** | Close 7 declared gaps in ANKH framework; prerequisite chain for LoRA fine-tune | CA1–CA5 + L2–L6 assigned to Claude; LF1–LF2 to User |

All three converge at LoRA fine-tune (LF1).

---

## Files Created This Session

| File | Purpose | Ready? |
|------|---------|--------|
| [STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md](STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md) | Master plan: model pool, engine strategy, execution sequence, Codex prompt, Horse-Market concept | ✅ `CLOSED — READY_FOR_DELEGATION` |
| [TASK_SCHEDULE_2026_03_11.md](TASK_SCHEDULE_2026_03_11.md) | Three-track schedule: prerequisites, agent assignments, signal thresholds, convergence diagram | ✅ Active |
| [docs/OXIDIZED_TOOLCHAIN_REFERENCE.md](../../docs/OXIDIZED_TOOLCHAIN_REFERENCE.md) | Rust-native toolchain manager ecosystem reference: uv, rv, goup, bun, cargo, brush, fnm, Volta, mise, proto, pixi, rig, zv + Horse-Market analysis + OxidizedIndex concept | ✅ Complete |
| [docs/OXIDIZED_CHEATSHEET.md](../../docs/OXIDIZED_CHEATSHEET.md) | Cross-tool pattern map (42 tasks), per-tool quick reference (9 tools), OxidizedIndex seed table | ✅ Complete |

---

## Files Modified This Session

| File | Change |
|------|--------|
| [AGENT_COMMON.md (repo-root)](../../AGENT_COMMON.md) | Added `brush` to toolchain line; added links to OXIDIZED_TOOLCHAIN_REFERENCE + OXIDIZED_CHEATSHEET; updated Architecture blurb |
| [docs/PWSH_RULES.md](../../docs/PWSH_RULES.md) | `7.4.0` → `7.5.x` in policy statement and verification comment |

---

## Key Concepts Established

### Horse-Market
Named pattern for any domain where surface signals (GitHub stars, download counts, "Win11 support" badges) are systematically decoupled from actual quality/substance. ANKH placement: a **HUCHA accumulator** — the entropy pattern that AD02 (Tinku), AD04 (Ammit), AD06 (Despacho) were designed to counter. NOT a new Alpha Directive.

**Fix:** OxidizedIndex v2 probe layer — `cargo install <crate>` + smoke test = `win11_verified: true` regardless of badge. Ground truth over surface signal.

### OxidizedIndex
Rust CLI tool (Track B). Two-phase design:
- **v1:** Crawl GitHub Search API + crates.io API + endoflife.date → classify + enrich → `output/index.json`
- **v2:** Compilation probe layer → `cargo install` + smoke test per tool → `output/verified.json`

Data sources: `github.com/search?q=topic:version-manager+language:rust`, `crates.io/api/v1/crates/<name>`, `endoflife.date/api/<product>.json`

### Three-Body Problem
The core architectural gap: SSOT lore authoring ↔ overnight daemon (stateless, no memory) ↔ local inference (binary compiled, no model, not in PATH). Track A closes the inference + daemon gap.

### Abliteration (for RTX 4090 Laptop 16GB VRAM)
Weight-level refusal removal via orthogonal projection. Tools: ErisForge, DECCP, Heretic pipeline. GGUF is inference format. Best practical fits for 16GB: 8B Q4_K_M (~5.5GB), 14B Q4_K_M (~9.5GB), 20B Q4_K_M (~12GB), 35B-A3B MoE (~7GB active, but full weight matrix ~18GB — caution).

### Codex Identity
Codex 5.4 — GPT-5 coding agent (Codex Pro subscription). Full autonomous repo engineer lane. Terminal + patch tools, multi-file execution, no practical token ceiling, Extra High thinking. Access via GitHub Copilot Pro+.

---

## Pending Work — Unblocked Now

Ordered by unblocked + highest leverage:

```
1. [User]   U1  — Download GGUF model to dev/models/
                  Command in STRATEGIC_PLAN §Model Download
2. [Codex]  C1–C7 — Paste §Codex Prompt from STRATEGIC_PLAN into a Codex session
3. [Claude] B1  — Draft OxidizedIndex_SPEC.md
                  Sources: docs/OXIDIZED_TOOLCHAIN_REFERENCE.md + docs/OXIDIZED_CHEATSHEET.md
4. [Claude] CA1 — ANKH_FOUNDATIONAL_AXIOMS.md (FA¹–FA⁵ formal specs)
                  Source: docs/frameworks/ankh/ANKH_SYNTHESIS_META.md
5. [Claude] L5  — §10.3.11 Curatrix Mortuorum profile
                  Standalone, no blockers
```

---

## Full Pending Task List

### Track A — Infrastructure

| ID | Task | Agent | Blocker |
|----|------|-------|---------|
| U1 | Download GGUF model → `dev/models/` | User | None |
| U2 | Confirm file integrity | User | U1 |
| C1 | PATH fix: `~/.cargo/bin` + goup + rv hook in pwsh `$PROFILE` + `~/.bashrc` | Codex | None |
| C2 | `scripts/start_mistralrs.ps1` | Codex | None |
| C3 | `dev/local-inference/pyproject.toml` (Python 3.13, torch cu124) | Codex | None |
| C4 | `overnight_daemon.ts` — seen-set state file | Codex | None |
| C5 | `overnight_daemon.ts` — task queue routing | Codex | C4 |
| C6 | `overnight_daemon.ts` — local model probe (port 8080 first, HF fallback) | Codex | C2 |
| C7 | Validate: dry-run daemon, confirm outputs | Codex | C4, C5, C6 |
| U3 | Run `start_mistralrs.ps1`, verify `curl localhost:8080/health` | User | U1, U2, C2 |
| U4 | Reload VS Code Insiders (picks up PATH changes) | User | C1 |
| U5 | Manual daemon run → confirm local model classifies | User | U3, C7 |

### Track B — OxidizedIndex

| ID | Task | Agent | Blocker |
|----|------|-------|---------|
| B1 | `OxidizedIndex_SPEC.md` | Claude | None |
| B2 | `data/known.toml` — 14-tool seed file | Claude | B1 |
| B3 | `data/probes.toml` — per-tool smoke tests | Claude | B1, B2 |
| B4 | OxidizedIndex v1 Rust CLI (`output/index.json`) | Codex | B1–B3 |
| B5 | v2 probe layer (`probe.rs`) | Codex | B4 |
| B6 | `output/verified.json` | Codex | B5 |
| B7 | Nightly refresh scheduled via Gemini/daemon | Gemini | B4 |
| B8 | Wire toolchain feed into overnight daemon | Codex | B7, A-track |

### Track C — ANKH / Lore

| ID | Task | Agent | Blocker | Severity |
|----|------|-------|---------|----------|
| CA1 | `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` — FA¹–FA⁵ formal specs | Claude | None | HIGH |
| CA2 | `docs/frameworks/ankh/ANKH_INVOCATION_PROTOCOL.md` — invocation syntax | Claude | CA1 | MEDIUM |
| CA3 | `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md` — MSP-RSG + SoulCycle | Claude | CA1 | MEDIUM |
| CA4 | DAFP (Dynamic Altitude Focal Point) — fold into CA3 or standalone | Claude | CA1 | MEDIUM |
| CA5 | `docs/frameworks/ankh/ANKH_ANTI_PATTERNS.md` — Horse-Market as HUCHA accumulator | Claude | CA1, CA2 | LOW→MEDIUM |
| L2 | `dev/ankh-dsl-spec.md` — ANKH DSL prototype grammar | Claude | CA1–CA3 | — |
| L3 | Character extraction — 15 entity sheets → `game/lore/characters/` | Claude | None | — |
| L4 | Pen-and-paper game mechanic validation | Claude | L3 | — |
| L5 | §10.3.11 Curatrix Mortuorum profile | Claude | None | — |
| L6 | FA⁵ skin tag schema decision + backfill across 10 profiles | Claude | CA1 | — |
| L1 | Gemini DR brief: SSOT corpus extraction + dataset cleaning | Claude drafts → Gemini | L3, L5, A-track | — |
| LF1 | Unsloth LoRA fine-tune run | User | L1, U3, C3 | — |
| LF2 | Deploy LoRA → TabbyAPI `loras/` | User | LF1 | — |

---

## Signal Thresholds

| Signal | Unlocks |
|--------|---------|
| `dev/models/<model>.gguf` exists | U3, C6 viable |
| `curl localhost:8080/health` responds | U5, daemon local probe active |
| Daemon writes `DAEMON_TASK_QUEUE.md` entry | A-track complete |
| `ANKH_FOUNDATIONAL_AXIOMS.md` exists | CA2, CA3, CA4, L6 unblocked |
| CA1–CA3 all exist | L2 (ANKH DSL spec) unblocked |
| L3 + L5 complete | L1 (Gemini DR brief) can be drafted |
| `output/index.json` exists | B7, B8 viable |
| L1 brief delivered + Gemini responds | LF1 (LoRA training) unblocked |

---

## Known Gaps — No Rust-Native Solution Yet

| Language | Status | Notes |
|----------|--------|-------|
| **Lua** | ❌ No Rust version manager | Manual install only. LuaRocks exists for packages. No EOL API coverage. |
| **PHP** | ❌ `phpup` abandoned/WIP on Windows | `cargo install phpup` compiles but Windows support incomplete. No viable alternative. |
| **Elixir / Erlang** | ❌ None | `asdf` plugin is the community standard (non-Rust). `kiex` (Elixir only) is Bash. EOL API covers Elixir + Erlang. |
| **Crystal** | ❌ None | No version manager exists at all. No EOL API coverage. |
| **Java / JVM** | ❌ None | SDKMan (Bash), jenv (shell script). `mise` supports Java via plugin but mise is TOML-config not Rust-native. |
| **.NET** | ❌ None | `dotnet-install.sh` is official, Bash. No Rust-native alternative. |
| **R** | ⚠️ Tracked via `rig` (Rust, r-lib) | `rig` = R version manager (Rust). `A2-ai/rv` = R package manager (also "rv"). Both exist. EOL API does NOT cover R. |
| **Zig** | ⚠️ `zv` — partial | `cargo install zv` compiles. Win11 not advertised but pure Rust binary. Experimental. |

---

## Toolchain Corrections Applied This Session

| Wrong | Correct | Where Fixed |
|-------|---------|-------------|
| `glam` (shell) | `brush` (`reubeno/brush`) | AGENT_COMMON, STRATEGIC_PLAN, TOOLCHAIN_REFERENCE |
| rv shim path `~/.local/share/rv/shims` | pre-exec hook `eval "$(rv shell init bash)"` | STRATEGIC_PLAN |
| `rv list` / `rv use` / `rv install` | `rv ruby list` / `rv ruby pin` / `rv ruby install` | STRATEGIC_PLAN, TOOLCHAIN_REFERENCE |
| `goup list` / `goup use` / `goup self update` | `goup ls` / `goup set` / `goup upgrade` | STRATEGIC_PLAN, TOOLCHAIN_REFERENCE |
| `rvw` alias (Remove-Variable workaround) | `rv` directly (alias already removed in profile) | STRATEGIC_PLAN |
| pwsh 7.4.0 | pwsh 7.5.x | docs/PWSH_RULES.md (both copies) |

---

## WIP Tooling

**`scripts/link_audit.py`** — Auto-fix markdown links. Run after editing any doc with links:
```powershell
uv run scripts/link_audit.py check claude/mailbox/SESSION_PREAMBLE_2026_03_11.md --fix
uv run scripts/link_audit.py backticks claude/mailbox/SESSION_PREAMBLE_2026_03_11.md --fix
```

---

## Source Files (SSOT for Pending Claude Tasks)

| Task | Primary Source |
|------|---------------|
| B1–B3 (OxidizedIndex spec + data) | [docs/OXIDIZED_TOOLCHAIN_REFERENCE.md](../../docs/OXIDIZED_TOOLCHAIN_REFERENCE.md), [docs/OXIDIZED_CHEATSHEET.md](../../docs/OXIDIZED_CHEATSHEET.md) |
| CA1–CA5 (ANKH axioms + protocols) | [docs/frameworks/ankh/ANKH_SYNTHESIS_META.md](../../docs/frameworks/ankh/ANKH_SYNTHESIS_META.md), [docs/frameworks/ankh/ANKH.md](../../docs/frameworks/ankh/ANKH.md) |
| L3 (character extraction) | `.github/copilot-instructions.md` (SSOT — §10.x entity profiles) |
| L5 (Curatrix Mortuorum) | `.github/copilot-instructions.md` §10.3.11 |
| L1 (Gemini DR brief) | Entire SSOT corpus post L3 + L5 completion |

---

*Authored: 2026-03-11. Synthesizes: STRATEGIC_PLAN_2026_03_10, TASK_SCHEDULE_2026_03_11, OXIDIZED_TOOLCHAIN_REFERENCE, OXIDIZED_CHEATSHEET, ANKH_SYNTHESIS_META.*
