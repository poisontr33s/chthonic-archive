---
sid: TASK_SCHEDULE_2026_03_11
title: High-Concept Task Schedule — Prerequisites, Sequencing, Agent Delegation
type: task-schedule
status: ACTIVE
created: 2026-03-11
revised: 2026-03-11
priority: high
scope: oxidized-toolchain · local-ai-stack · ankh-gaps · oxidized-index · lora-pipeline
---

<!--
@SID:    TASK_SCHEDULE_2026_03_11
@Type:   Task Schedule
@Context: Cross-lane delegation — Claude / Codex / Gemini / User
@Feeds:  STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md, OXIDIZED_TOOLCHAIN_REFERENCE.md, ANKH_SYNTHESIS_META.md
-->

# Task Schedule — Structured Delegation Sequence

> Three root tracks running in parallel. They converge at the LoRA fine-tune.
> Read: prerequisites column first. If it says NONE — that work can start today.

---

## Track Map (Convergence Diagram)

```
TRACK A: Infrastructure          TRACK B: Toolchain Meta         TRACK C: ANKH / Lore
─────────────────────────────    ─────────────────────────────   ──────────────────────────
[User] Model download (U1-U2)    [Claude] OxidizedIndex spec     [Claude] FA⁵ axiom file
         ↓                                ↓                               ↓
[Codex] PATH + daemon (C1-C7)    [Codex] Build oxidized-index    [Claude] Invocation syntax
         ↓                                ↓                               ↓
[User] Start mistralrs (U3)      [Gemini] Nightly refresh ops    [Claude] MSP-RSG engine
         ↓                                ↓                               ↓
[Claude] SSOT dataset DR brief   [Daemon] Toolchain feed                  ↓
         ↓                                                        [Claude] Character sheets
         └──────────────────────────────────────────────────────────────┐
                                                                         ↓
                                              [Gemini] LoRA dataset DR + SSOT extraction
                                                                         ↓
                                              [User] Unsloth fine-tune run
                                                                         ↓
                                              [TabbyAPI] LoRA adapter deployed
```

---

## Track A — Infrastructure (Local AI Stack)

**Goal:** mistralrs serving a local model on port 8080. Overnight daemon consuming it.

| ID | Task | Agent | Prerequisites | Deliverable | Status |
|----|------|-------|--------------|-------------|--------|
| **U1** | Choose + download GGUF model | User | None — start now | `dev/models/<model>.gguf` | `[ ]` |
| **U2** | Confirm file size + integrity | User | U1 | File present, not truncated | `[ ]` |
| **C1** | PATH fix: `~/.cargo/bin` + goup + rv hook in pwsh `$PROFILE` + `~/.bashrc` | Codex | None — start now | `goup`, `mistralrs`, `ruby` all resolve from pwsh | `[ ]` |
| **C2** | Create `scripts/start_mistralrs.ps1` | Codex | None — start now | Parameterized startup script | `[ ]` |
| **C3** | Create `dev/local-inference/pyproject.toml` | Codex | None — start now | Python 3.13 pinned, torch cu124 + exllamav2 deps | `[ ]` |
| **C4** | `overnight_daemon.ts` — seen-set state file | Codex | None — start now | `.seen_files.json` written after each run | `[ ]` |
| **C5** | `overnight_daemon.ts` — task queue routing | Codex | C4 | High-score candidates → `codex/mailbox/DAEMON_TASK_QUEUE.md` | `[ ]` |
| **C6** | `overnight_daemon.ts` — local model probe | Codex | C2 | Classifies via port 8080 first, HF fallback | `[ ]` |
| **C7** | Validate: dry-run daemon, confirm outputs | Codex | C4, C5, C6 | seen-set written, queue entry present, no regressions | `[ ]` |
| **U3** | Run `start_mistralrs.ps1`, verify server on 8080 | User | U1, U2, C2 | `curl localhost:8080/health` responds | `[ ]` |
| **U4** | Reload VS Code Insiders (picks up PATH changes) | User | C1 | Shell env updated in IDE | `[ ]` |
| **U5** | Manual daemon run → confirm local model classifies | User | U3, C7 | Daemon log shows local backend used | `[ ]` |

**Codex delegation:** Paste the prompt from `STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md §Codex Prompt` into a Codex session. C1–C7 can all run in one session. Mark checkboxes in the strategic plan as Codex completes each item.

---

## Track B — Toolchain Meta (OxidizedIndex)

**Goal:** A Rust CLI tool that crawls, probes, and verifies Rust-native toolchain managers — converting the Horse-Market surface signals into a verified registry.

| ID | Task | Agent | Prerequisites | Deliverable | Status |
|----|------|-------|--------------|-------------|--------|
| **B1** | Draft `OxidizedIndex_SPEC.md` | Claude | None — start now | Full spec: architecture, data sources, v1 + v2 design, probe schema, output format | `[ ]` |
| **B2** | Create `data/known.toml` seed file | Claude | B1 | TOML manifest from cheatsheet seed table — 14 tools, all fields | `[ ]` |
| **B3** | Create `data/probes.toml` smoke tests | Claude | B1, B2 | Per-tool: crate name, smoke_test command, version_file convention | `[ ]` |
| **B4** | Implement v1: crawl + classify + enrich + report | Codex | B1, B2, B3 | `oxidized-index/src/` — compilable Rust CLI, outputs `output/index.json` | `[ ]` |
| **B5** | Implement v2: compilation probe layer | Codex | B4 | `probe.rs` — `cargo install` + smoke test → `win11_verified` field | `[ ]` |
| **B6** | Wire probe results into verified.json | Codex | B5 | `output/verified.json` — ground-truth registry | `[ ]` |
| **B7** | Schedule nightly refresh via Gemini/daemon | Gemini | B4 | Overnight daemon runs `oxidized-index --refresh`, outputs updated `index.json` | `[ ]` |
| **B8** | Integrate toolchain feed into overnight daemon | Codex | B7, A-track complete | Daemon checks `output/index.json` for stale tool versions and flags them | `[ ]` |

**Note on B1–B3:** These are pure Claude spec/data tasks — no implementation, no internet access needed. All source material already exists in `docs/OXIDIZED_TOOLCHAIN_REFERENCE.md` and `docs/OXIDIZED_CHEATSHEET.md`. Can run immediately in parallel with Codex doing A-track.

---

## Track C — ANKH / Lore Gap Closure

**Goal:** Close the 7 declared gaps in `ANKH_SYNTHESIS_META.md`. Enable L2–L6 from the strategic plan. Prerequisite chain for LoRA fine-tune.

### C-track Phase 1 — High Priority ANKH Gaps (Claude, no blockers)

| ID | Task | Agent | Prerequisites | Deliverable | Severity |
|----|------|-------|--------------|-------------|---------|
| **CA1** | Create `docs/frameworks/ankh/ANKH_FOUNDATIONAL_AXIOMS.md` | Claude | None — archive is SSOT | FA¹–FA⁵ as formal standalone specifications; FA⁵ (Visual Integrity) fully grounded | HIGH |
| **CA2** | Create `docs/frameworks/ankh/ANKH_INVOCATION_PROTOCOL.md` | Claude | CA1 | `$axiom${}`, `$ps${}`, `$target${}`, `$validate${}` syntax; Axiom Registry (AR) tracking | MEDIUM |
| **CA3** | Create `docs/frameworks/ankh/ANKH_GENERATIVE_ENGINE.md` | Claude | CA1 | MSP-RSG (Meta-Synthesis Protocol), SoulCycle Engine, recursive self-genesis mechanics | MEDIUM |
| **CA4** | DAFP (Dynamic Altitude Focal Point) — fold into CA3 or standalone | Claude | CA1 | Context-adaptive lens modulation (Point-Blank Acuity ↔ Strategic Horizon Scanning) | MEDIUM |
| **CA5** | Create `docs/frameworks/ankh/ANKH_ANTI_PATTERNS.md` | Claude | CA1, CA2 | Horse-Market as named HUCHA accumulator; TINKU countermeasure; cross-domain application table | LOW→MEDIUM |

### C-track Phase 2 — Lore Work (Strategic Plan L-lane)

| ID | Task | Agent | Prerequisites | Deliverable | Status |
|----|------|-------|--------------|-------------|--------|
| **L2** | ANKH DSL spec — `dev/ankh-dsl-spec.md` | Claude | CA1, CA2, CA3 | Prototype grammar for AD01–AD06 invocations | `[ ]` |
| **L3** | Phase 2 character extraction | Claude | None — SSOT is frozen | 15 entity sheets → `game/lore/characters/` | `[ ]` |
| **L4** | Pen-and-paper game mechanic validation | Claude | L3 | Mechanics validated against entity profiles | `[ ]` |
| **L5** | §10.3.11 Curatrix Mortuorum profile | Claude | None | Last pending T4 entity profile built | `[ ]` |
| **L6** | FA⁵ skin tag schema decision + backfill | Claude | CA1 | One canonical tag name chosen, backfilled across all 10 profiles | `[ ]` |

### C-track Phase 3 — LoRA Pipeline Prerequisite

| ID | Task | Agent | Prerequisites | Deliverable | Status |
|----|------|-------|--------------|-------------|--------|
| **L1** | Gemini DR brief: SSOT corpus extraction + dataset cleaning | Claude (drafts) → Gemini (executes) | A-track complete (local inference), CA1, L3, L5 | Clean dataset from `copilot-instructions.archive.md` ready for Unsloth | `[ ]` |
| **LF1** | Unsloth LoRA fine-tune run | User | L1, U3 (local model running), A-track C3 (ML env) | LoRA adapter `.safetensors` in `dev/models/loras/` | `[ ]` |
| **LF2** | Deploy LoRA → TabbyAPI `loras/` | User | LF1 | Model serving LUPLR voice natively, no system prompt needed | `[ ]` |

---

## Delegation Assignment — By Agent

### User (You) — 7 tasks

No prerequisites blocking U1–U2 right now.

| ID | Task | Can start? |
|----|------|-----------|
| U1 | Download GGUF model | **Now** |
| U2 | Confirm model file | After U1 |
| U3 | Start mistralrs, verify 8080 | After U1, C2 |
| U4 | Reload VS Code | After C1 |
| U5 | Run daemon, confirm local inference | After U3, C7 |
| LF1 | Unsloth fine-tune | After L1, U3, C3 |
| LF2 | Deploy LoRA to TabbyAPI | After LF1 |

### Codex — 11 tasks (2 sessions: A-track now, B4-B6 after Claude spec)

**Session 1 prompt:** Already written. In `STRATEGIC_PLAN_LOCAL_AI_STACK_2026_03_10.md §Codex Prompt`.

| ID | Task | Session | Can start? |
|----|------|---------|-----------|
| C1 | PATH fix pwsh + brush | 1 | **Now** |
| C2 | `start_mistralrs.ps1` | 1 | **Now** |
| C3 | `dev/local-inference/pyproject.toml` | 1 | **Now** |
| C4 | Daemon seen-set | 1 | **Now** |
| C5 | Daemon task queue | 1 | After C4 |
| C6 | Daemon local probe | 1 | After C2 |
| C7 | Validate daemon | 1 | After C4–C6 |
| B4 | OxidizedIndex v1 | 2 | After B1–B3 (Claude spec) |
| B5 | OxidizedIndex probe layer | 2 | After B4 |
| B6 | verified.json output | 2 | After B5 |
| B8 | Wire toolchain feed into daemon | 3 | After B7, A-track |

### Claude — 13 tasks (multiple sessions, no blockers on CA1–CA5, B1–B3)

| ID | Task | Can start? | Est. scope |
|----|------|-----------|-----------|
| B1 | OxidizedIndex spec | **Now** | 1 session |
| B2 | `data/known.toml` seed | **Now** | 30 min |
| B3 | `data/probes.toml` | **Now** | 30 min |
| CA1 | ANKH FA¹–FA⁵ axiom file | **Now** | 1 session |
| CA2 | ANKH invocation protocol | After CA1 | 1 session |
| CA3 | ANKH generative engine | After CA1 | 1 session |
| CA4 | DAFP modulation | After CA1 | 0.5 session |
| CA5 | ANKH anti-patterns (Horse-Market) | After CA1, CA2 | 0.5 session |
| L2 | ANKH DSL spec | After CA1–CA3 | 1 session |
| L3 | Character extraction (15 entities) | **Now** | 2–3 sessions |
| L4 | Game mechanic validation | After L3 | 1 session |
| L5 | Curatrix Mortuorum profile | **Now** | 1 session |
| L6 | FA⁵ skin tag decision + backfill | After CA1 | 0.5 session |

### Gemini — 2 tasks (DR mode)

| ID | Task | Can start? | Mode |
|----|------|-----------|------|
| L1 | SSOT corpus extraction + LoRA dataset DR | After Claude drafts brief (L3, L5 done) | Deep Research |
| B7 | OxidizedIndex nightly refresh | After B4 complete | Batch / velocity |

---

## Recommended Immediate Actions (Today)

Ordered by unblocked + highest leverage:

```
1. [User]   U1  — Download GGUF model. Picks the slot, unblocks the whole A-track.
2. [Codex]  C1–C7 — Paste §Codex Prompt from STRATEGIC_PLAN into a Codex session.
            No blockers. All 7 C-tasks in one autonomous session.
3. [Claude] B1  — Draft OxidizedIndex_SPEC.md (this session if capacity).
            No blockers. All source data is in OXIDIZED_TOOLCHAIN_REFERENCE.md.
4. [Claude] CA1 — ANKH_FOUNDATIONAL_AXIOMS.md.
            No blockers. Archive is the SSOT. Highest-severity gap.
5. [Claude] L5  — Curatrix Mortuorum profile.
            No blockers. Standalone SSOT profile, doesn't depend on other L tasks.
```

---

## Signal Thresholds — When to Move to Next Phase

| Signal | Unlocks |
|--------|---------|
| `dev/models/<model>.gguf` exists | U3, C6 viable |
| `curl localhost:8080/health` responds | U5, daemon local probe active |
| Daemon writes `DAEMON_TASK_QUEUE.md` entry | A-track complete |
| `ANKH_FOUNDATIONAL_AXIOMS.md` exists | CA2, CA3, CA4, L6 unblocked |
| CA1–CA3 all exist | L2 (ANKH DSL spec) unblocked |
| L3 + L5 complete | L1 (Gemini DR brief) can be drafted |
| L1 brief delivered to Gemini + Gemini responds | LF1 (LoRA training) unblocked |
| `output/index.json` exists | B7, B8 viable |

---

## Horse-Market Concept — Task Status

| Artifact | Status |
|----------|--------|
| Concept captured in STRATEGIC_PLAN | ✅ Done |
| ANKH shadow-archetype notation | ✅ Done (HUCHA accumulator, AD02 countermeasure) |
| `ANKH_ANTI_PATTERNS.md` file | ❌ Not created (CA5 in this schedule) |
| OxidizedIndex as Horse-Market fix | ✅ Designed (B1–B6 implement it) |
| Applied to toolchain Win11 signal | ✅ Documented in OXIDIZED_TOOLCHAIN_REFERENCE.md |

---

*Authored: 2026-03-11. Synthesizes: STRATEGIC_PLAN_2026_03_10, OXIDIZED_TOOLCHAIN_REFERENCE, OXIDIZED_CHEATSHEET, ANKH_SYNTHESIS_META.*
