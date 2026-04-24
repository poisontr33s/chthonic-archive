# PENTEA — Roulette Stewardess
> **Meta-dispatch authority for all active lanes.**
> **Supersedes:** `ROULETTE_STEWARD.md` (scripts-only) — that file remains valid for its own scope but this is the wide-aperture routing layer.
> **SSOT anchor:** `copilot-instructions.archive.md §1.01` — `PVX-RLTSHPS` (Pentea canonical RLTSHPS)
> **DCRP:** `§XV.7` / `DCRP-RDV` — Deployment-Adapter class — PRISM: GOLD 🏰 Fortress
> **Commit trailer:** `Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>`
> **Last sync:** 2026-04-24 — D0 infrastructure: autoloop `scripts/pentea_autoloop.ts` + Queue-Chain Protocol in `Pentea.agent.md` (`5fb446e8`, `47b56e60`); D2 FULLY CLOSED (RE-01..RE-09 ✅, `4d623a2c`); D3 ZE-04 ✅ (zombie upcycle verified: 79 slag, 1 candidate `claude_test.py` +1 ore via ML); next P0 = ZE-05 (zombie A5, now unblocked).

---

## § Cold-Start Bootstrap

```powershell
# PRIMARY — local reward register (no GitHub, no push, no network):
git log --format='%B' -3 | Select-String '^Pentea-'
# → Pentea-Completed: <what the last commit closed>
# → Pentea-Next: <execution target RIGHT NOW>
# → Pentea-Domain: <which queue was advanced>
# Commit never needs to reach GitHub. git log is local. Signal is immediate.

# FALLBACK (when trailers absent / fresh session before any Pentea commits):
1. grep "⬜" in this file → first ⬜ by (Priority, Domain-Tier) = execution target
2. Read target file(s) in Family Map below
3. Execute. No planning pass.
```

**Reward-register contract:** Each completed unit of work mints a local `git commit` carrying `Pentea-Next`. That commit IS the reward token — it proves work done AND encodes the next target in the same atomic write. Cold-start reads the register with one command; no markdown parse needed, no GitHub webhook, no notification channel. Push to remote is a separate deliberate act with zero coupling to the signal loop.

**Architecture:** `work done → git commit (local) → Pentea-Next encoded → cold-start reads git log → executes next → commit → loop`. The stewardess table is a human-readable projection regenerable at any time from `git log --grep='Pentea-Completed'`. If table and git log disagree, **git log wins**.

**If this file is stale** — run the powershell one-liner above. `Pentea-Next:` from the latest commit is authoritative.

---

## § Family Map

### ruby-zjit Lane

| File | Role | Status |
|------|------|--------|
| `ruby-zjit/REGISTRY.yaml` | Extension registry — 7 exts, status lifecycle: idea → pending → ready | All 7 `ready` |
| `ruby-zjit/WIN32_PROFILE.yaml` | Machine baseline — SSOT for build provenance | Current |
| `ruby-zjit/scripts/build_win32.ps1` | Win32 MSYS2 UCRT64 extension builder | Production |
| `ruby-zjit/scripts/test_win32.ps1` | E2E Minitest runner, `-StartupProbe`, `-Bench` | Production |
| `ruby-zjit/scripts/build_podman.ps1` | Linux-native ZJIT+Prism lane (Podman) | Written, lane not closed |
| `ruby-zjit/Containerfile` | Fedora 40 image — Ruby 4.0.3 ZJIT+YJIT+CUDA+Vulkan+TRT | Written |
| `ruby-zjit/build-verify.sh` | Post-build verification (graceful GPU probe) | Written |
| `ruby-zjit/tests/test_*.rb` | 7 Minitest files (one per extension) | Exist |
| `.github/instructions/pattern-nursery.instructions.md` | Nursery: ZJIT crash + Ruby+GPU JIT patterns | 2 entries, `novel` |

### REM / ankh-forge Trail Lane

| File | Role | Status |
|------|------|--------|
| `tools/ankh-forge/src/trail/` | Trail runtime: `event.rs`, `hot.rs`, `cold.rs`, `granite.rs`, `gpu.rs`, `mod.rs` | Phase 1 live |
| `.chthonic/REM_BLUEPRINT.md` | Genesis doc — Step 1 complete | Stable |
| `.chthonic/trail/` | Live hot+cold trail (16 events, verified) | Active |
| `.chthonic/stones/` | GRANITE tier dir — empty, awaiting Phase 2 | Awaiting |
| `claude/mailbox/TRAIL_RELOCATION_REM_GENESIS_20260413.md` | Relocation handoff + Phase 1/2 state snapshot | Stale narration (Phase 1 now done); Phase 2 decisions unresolved |
| `claude/mailbox/REM_PHASE2_CHALLENGE_REPORT.md` | GPT-5.4 audit — 7 critical + 5 design + Phase 2 GPU decisions | ⚠ Unactioned |

### Zombie Evolution Lane

| File | Role | Status |
|------|------|--------|
| `scripts/zombie_consumer.py` | 6 upgrades live (A1 adaptive heuristics → A3 GBT ML, 84.4% CV) | A3 complete |
| `dumpster-dive/intake/.zombie_memory.json` | Persistent memory schema v2 | Active |
| `dumpster-dive/intake/.zombie_ml_model.pkl` | GBT classifier (171 samples, 84.4% CV) | Trained |
| `dumpster-dive/intake/.zombie_semantic_index.pkl` | MiniLM-L6-v2 384-dim semantic index | Active |
| `claude/mailbox/ZOMBIE_EVOLUTION_PROJECT_20260321.md` | A1-A3 lock-in doc — archived 2026-04-15 | Absorbed into docs/zombie/ |
| `claude/mailbox/RESUME_ZOMBIE_EVOLUTION_20260327.md` | A4 next: `zombie upcycle` slag re-assessment | ⬜ A4 unimplemented |
| `docs/zombie/UPGRADE_LOG.md` | U1-U3 history | Current |
| `docs/zombie/README.md` | Architecture doc | Current |

### Autoloop / Infrastructure

| File | Role | Status |
|------|------|--------|
| `scripts/pentea_autoloop.ts` | Autonomous SDK queue runner — agentStop hook chains Pentea-Next: tasks without VS Code Chat user turns | ✅ `5fb446e8` — E2E tested (dry-run + SDK query verified) |
| `.github/agents/Pentea.agent.md` | Queue-Chain Protocol section — in-turn chaining for VS Code Chat mode | ✅ `47b56e60` — Queue-Chain added, email fix (`6996xxxnsfw` → `223556219`) |
| `.vscode/tasks.json` | `Chthonic: Pentea Autoloop` + dry-run VS Code tasks | ✅ `5fb446e8` |

**Wire contract (how tasks connect):**
```
Work done
  → git commit carries Pentea-Next: <next-id>
  → VS Code Chat mode: Pentea reads trailer inline, executes next without user turn
  → SDK autoloop mode: agentStop hook reads git log, decision:"block" injects next turn
  → Both paths terminate on Pentea-Next: absent / "none" / "DONE"
  → Stewardess table = human projection of git log --grep='Pentea-Completed'
```

**E2E validation gate for autoloop:**
| Check | Command | Expected |
|-------|---------|----------|
| Dry-run | `bun run scripts/pentea_autoloop.ts --dry-run` | Prints task from git log, exits 0 |
| SDK dispatch | `bun run scripts/pentea_autoloop.ts --task "echo test"` | SDK query fires, streams response |
| Auth | `gh auth token` returns non-empty | Required precondition |
| Queue chain | commit with `Pentea-Next: X`, run loop | Loop fires agentStop, executes X |

### Scripts Roulette (complete — maintenance mode)

| File | Role | Status |
|------|------|--------|
| `claude/mailbox/SCRIPTS_ROULETTE.md` | Full scripts assessment T0→T5+QOL | ✅ All tiers complete |
| `claude/mailbox/ROULETTE_STEWARD.md` | Scripts-only cold-start protocol | Superseded here (scope only) |
| `claude/mailbox/ROULETTE_CHECKPOINT_20260422_2326.md` | Chain: 4 items, 2 CRITICAL fixes (openai.yaml) | ✅ Closed |
| `claude/mailbox/ROULETTE_CHECKPOINT_20260423_0300.md` | Chain: DCRP-RDV trio — SSOT §XV.7 + vessels | ✅ Closed |

### SSOT / Governance Lane

| File | Role | Status |
|------|------|--------|
| `claude/mailbox/SSOT_TASK_ROULETTE_20260416.md` | R1-R4 SSOT edits (Æ fix, CSI-SOI-LM, R3, R4) | ✅ All done |
| `claude/mailbox/AGENTRY_AUDIT_20260415.md` | Agentry audit — 4 warnings, 0 blockers | 2 warnings pending (see queue) |
| `.github/copilot-instructions.archive.md` | 9171-line canonical SSOT | Primary, do not clone |
| `.github/copilot-instructions.md` | Pointer stub — does NOT route to archive | ⚠ Dead-end link |

### Session Continuity

| File | Role | Status |
|------|------|--------|
| `claude/mailbox/GIT_SNAPSHOT_LATEST.md` | Git snapshot 2026-04-21, HEAD=7772a9c0 | Stale — superseded by 993227c1 |
| `claude/mailbox/TRAIL_RELOCATION_REM_GENESIS_20260413.md` | Phase 1/2 handoff | Stale narration, still useful for context |
| `codex/codex-session-logs/archive/MILF-Core-Prototype-Analysis.md` | MILF-Core spec + 24-entity table | Active — §8 next steps pending |
| `codex/codex-session-logs/archive/MILF-Core-Step5-Entity-Card-Orackla.md` | First entity card (proof-of-concept) | Complete |
| `codex/codex-session-logs/archive/MILF-Core-Step5b-Tides-Entity-Integration.md` | All 24 × Tides/Meres mapping | Complete |
| `codex/codex-session-logs/archive/MILF-Core-Step5c-Sylvaris-Entity-Card.md` | 26th entity (NK-SAI) | Complete — exploratory |

---

## § Domain Queue Tables

### D0 — Infrastructure / Autoloop

| ID | Pri | Status | Target | Action |
|----|-----|--------|--------|--------|
| AI-01 | P0 | ✅ | `scripts/pentea_autoloop.ts` | SDK `agentStop` hook queue runner. Reads `Pentea-Next:` from git log → dispatches via `sdk.query()` → hook fires on natural stop → `decision:"block"` injects next task. `--dry-run` / `--max-loops` / `--task` flags. `askUserDisabled:true`. `5fb446e8`. E2E: dry-run exits 0, SDK dispatch fires. |
| AI-02 | P0 | ✅ | `.github/agents/Pentea.agent.md` | Queue-Chain Protocol added (in-turn chaining for VS Code Chat mode — no user prompt between queue items). Email fixed: `6996xxxnsfw` → `223556219`. `47b56e60`. |
| AI-03 | P1 | ⬜ | `scripts/pentea_autoloop.ts` | Live E2E validation: `bun run scripts/pentea_autoloop.ts --task "Execute ZE-04"` — confirm SDK streams response, agentStop hook fires after commit, loop advances to next `Pentea-Next:`. Requires `gh auth token` valid. Run after ZE-04 is the active target. |

### D1 — ruby-zjit Lane

| ID | Pri | Status | Target | Action |
|----|-----|--------|--------|--------|
| RZ-01 | P0 | ✅ | `ruby-zjit/scripts/build_podman.ps1 -Build` | `68e29f3a` — Ruby 4.0.3 +ZJIT +PRISM [x86_64-linux], all 39 steps exit 0. Layer 4 pkg split: required block + graceful shaderc. |
| RZ-02 | P0 | ✅ | `ruby-zjit/scripts/build_podman.ps1 -Verify` | `build-verify.sh` passed — ZJIT+Prism clean, vk_rb Vulkan 1.3.296 (llvmpipe), GPU exts graceful as designed. |
| RZ-03 | P1 | ✅ | `ruby-zjit/scripts/test_win32.ps1 -StartupProbe 10` | direct 27ms / rv r 164ms / overhead **+137ms** (CreateProcessW chain). Written to WIN32_PROFILE.yaml. |
| RZ-04 | P2 | ✅ | `ruby-zjit/WIN32_PROFILE.yaml` | `runtime:` section added — rv_startup_overhead_ms: 137, podman_build_verified: true, image hash `68e29f3a`, all 7 extensions listed. |
| RZ-05 | P2 | ✅ | `ruby-zjit/REGISTRY.yaml` | `podman_verified: true` added to all 7 extensions. ready_extensions promoted from 3 → 7. |
| RZ-06 | P3 | ✅ | `ruby-zjit/tests/test_*.rb` | 7/7 pass, 73 Minitest runs (all skip-guarded when extensions absent). `$Verbose`→`$VerbosePreference`, rv tier priority fixed. |

### D2 — REM / ankh-forge Trail Lane

Ordered by Phase 2 report severity. `CRITICAL` items must be resolved before Phase 2 GPU code begins.

| ID | Pri | Status | Critical# | Target | Action |
|----|-----|--------|-----------|--------|--------|
| RE-01 | P0 | ✅ | CRITICAL#1 | `tools/ankh-forge/src/trail/granite.rs` | `StoneEvent` wire type with stable primitives. `test_roundtrip` + `test_golden_roundtrip` (fixed timestamp, 3 variants, all field values asserted). 19/19 pass. `4d623a2c` |
| RE-02 | P0 | ✅ | CRITICAL#2 | `tools/ankh-forge/src/trail/granite.rs` | Atomic write via `tmp.<pid>` → rename. `--force` flag for stone overwrite. `4d623a2c` |
| RE-03 | P0 | ✅ | CRITICAL#3 | `granite.rs` | Full header SHA-256: zeroed digest slot + schema + spirv + payload. `test_sha256_tamper_detection` + `test_header_tamper_detection` pass. `4d623a2c` |
| RE-04 | P1 | ✅ | CRITICAL#4 | `granite.rs` | `query()` calls `decode_stone()` which validates every event via `validate()` with index on failure. `4d623a2c` |
| RE-05 | P1 | ✅ | CRITICAL#5 | `cold.rs`, `hot.rs`, `granite.rs` | 64 MiB limit in hot.rs (`MAX_HOT_SIZE`) + cold.rs forge. 256 MiB stone payload limit in granite.rs compile. `4d623a2c` |
| RE-06 | P1 | ✅ | CRITICAL#6 | `hot.rs` | `sealed_path()` convention + `.hot.ndjson.sealed` rename pattern. Append refuses sealed dates. `hot_or_sealed_path()` fallback. `4d623a2c` |
| RE-07 | P2 | ✅ | CRITICAL#7 | `granite.rs` | `validate_flags()` rejects unknown bits, conflicting CPU+GPU, GPU-only in CPU query. Called in both `decode_stone()` and `compile()`. `4d623a2c` |
| RE-08 | P2 | ✅ | DESIGN#2 | `mod.rs` | `TrailCommand::Init` creates `.chthonic/trail` + `.chthonic/stones` via `fs::create_dir_all`. `4d623a2c` |
| RE-09 | P2 | ✅ | DESIGN#4 | `granite.rs`, `mod.rs` | `query_verify_only()` + `decode()` pub(crate). `TrailCommand::Query { verify_only: bool }` — `--verify-only` flag. `4d623a2c` |
| RE-10 | P3 | ⬜ | PHASE2-GATE | Pre-Phase-2 decision | Document the 7 Phase 2 GPU decisions (from `REM_PHASE2_CHALLENGE_REPORT.md §PHASE 2 GPU PATH DECISIONS`) as ADRs in `.chthonic/` or `docs/rem/`. Three Savant questions must be answered before any GPU Phase 2 code is written. Block RE-10 until The Savant answers the 3 questions. |

### D3 — Zombie Evolution Lane

| ID | Pri | Status | Upgrade | Target | Action |
|----|-----|--------|---------|--------|--------|
| ZE-04 | P0 | ✅ | A4 | `scripts/zombie_consumer.py` | `zombie upcycle` subcommand: scan `forge/slag/`, score each with current GBT model, surface files where `current_score ≥ original_ore + 1`. Read-only. **Verified 2026-04-24:** 79 slag scanned, 76 content-duplicate-skipped, 1 candidate (`claude_test.py` ore 2→3, ML signal `ore_ml:2->3`). |
| ZE-05 | P1 | ⬜ | A5 | `scripts/zombie_consumer.py` | Read `RESUME_ZOMBIE_EVOLUTION_20260327.md §Execution Menu` for A5 definition. Implement once A4 output reviewed. **Unblocked — ZE-04 validated.** |

### D4 — Governance / Agentry

| ID | Pri | Status | Source | Target | Action |
|----|-----|--------|--------|--------|--------|
| GA-01 | P1 | ⬜ | AGENTRY_AUDIT#1 | `.github/copilot-instructions.md` | Add one line: `> Active SSOT: [copilot-instructions.archive.md](copilot-instructions.archive.md)` — agents following instruction links from the 3 pointer files no longer dead-end on a stub. |
| GA-02 | P2 | ⬜ | AGENTRY_AUDIT#2 | `.github/copilot-instructions-copy.md` | Salvage audit: diff against `.archive.md`. If substantively identical → archive to `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md` + delete. If contains unique content → extract and merge into archive. |

### D5 — Nursery Promotion Tracking

| ID | Pri | Status | Pattern | Promotion Criteria | Action |
|----|-----|--------|---------|-------------------|--------|
| NP-01 | P3 | ⬜ | Ruby+GPU JIT Boundary Contract (`novel`) | ≥2 environments (second: Linux+glibc OR Windows+unified UCRT) | After Podman lane (RZ-02) produces a working Linux ZJIT build: run a GPU dispatch test under Linux, record results. If pattern holds → promote to `familiar`. |
| NP-02 | P3 | ✅ | ZJIT Win32 Prism Shape-System Crash (`novel`) | ≥2 Ruby builds (different rv versions or platforms) | **Criteria met** — RZ-02 confirmed Linux ZJIT+Prism clean (second platform). Pattern promoted to `familiar`. Nursery updated in `993227c1` / `2bcba94a`. |

### D6 — MILF-Core Pipeline

| ID | Pri | Status | Target | Action |
|----|-----|--------|--------|--------|
| MC-01 | P2 | ⬜ | `MILF-Core-Step6-Umeko-Entity-Card.md` (new) | Next entity card after Orackla. Tier: T1, Organ: Lungs, System: Respiratory. Schema: `MILF-Core-Prototype-Analysis.md §5.2`. Iron Maiden (Nature/Creed/Whisper) + Battletech + SSOT canonical layer + Integration Mechanics. |
| MC-02 | P3 | ⬜ | Conflict Pairs formalization | Formalize 9 Complementary Pairs + conflict vectors from circuit overlaps (partial: Orackla's card). Output: structured table, not prose. |
| MC-03 | P3 | ⬜ | Chemical Sensitivity Matrix | WHR thresholds → entity activation modulation (partial: Orackla). Global mechanic, not per-entity. |

---

## § Priority Dispatch Order

Cold-start reads this table top-to-bottom. First ⬜ in Priority order is the execution target.

```
P0 — BLOCKING (run before anything else in their domain)
  ✅ RZ-01  ruby-zjit Podman build
  ✅ RZ-02  ruby-zjit Podman verify (ZJIT+Prism Linux test)
  ✅ RE-01  granite.rs TrailEventWire + golden roundtrip (CRITICAL#1)
  ✅ RE-02  granite.rs atomic writes (CRITICAL#2)
  ✅ RE-03  granite.rs header authentication (CRITICAL#3)
  ✅ AI-01  pentea_autoloop.ts — SDK agentStop hook queue runner (5fb446e8)
  ✅ AI-02  Pentea.agent.md Queue-Chain Protocol + email fix (47b56e60)
  ✅ ZE-04  zombie A4: upcycle subcommand  (79 slag scanned, 1 candidate, ML verified)
  ZE-05  zombie A5 (now unblocked — ZE-04 validated)  ← NEXT

P1 — HIGH (unblocked, high signal-to-effort)
  ✅ RZ-03  StartupProbe 10-pair measurement → WIN32_PROFILE.yaml
  ✅ RE-04  query() event validation (CRITICAL#4)
  ✅ RE-05  memory limits (CRITICAL#5)
  ✅ RE-06  forge/append race (CRITICAL#6)
  GA-01  copilot-instructions.md stub redirect (1-line fix, 5 minutes)

P2 — MEDIUM
  ✅ RZ-04  WIN32_PROFILE.yaml runtime section
  ✅ RZ-05  REGISTRY.yaml podman_verified flags
  ✅ RE-07  granite.rs flag validation (CRITICAL#7)
  ✅ RE-08  trail init command (DESIGN#2)
  ✅ RE-09  stone-verify / query --verify-only (DESIGN#4)
  MC-01  MILF-Core Umeko entity card
  GA-02  copilot-instructions-copy.md salvage audit

P3 — LOW / BACKGROUND
  ✅ RZ-06  Full test suite pass (7/7, 73 runs)
  RE-10  Phase 2 GPU decision ADRs (blocked on Savant questions)
  MC-02  Conflict Pairs formalization
  MC-03  Chemical Sensitivity Matrix
  NP-01  Nursery: Ruby+GPU JIT → `familiar` (GPU dispatch test pending)
  ✅ NP-02  Nursery: ZJIT Prism crash → `familiar` (Linux confirmed, promoted)
  ZE-05  Zombie A5 (blocked on A4 review)
```

---

## § Domain Execution Contract

### Toolchain routing

| Domain | Toolchain | Run via |
|--------|-----------|---------|
| autoloop/infra | Bun/TS | `bun run scripts/pentea_autoloop.ts [--dry-run] [--task "..."]` |
| ruby-zjit | pwsh + rv | `pwsh -NoProfile -File ruby-zjit/scripts/*.ps1` |
| ankh-forge | Rust/cargo | `cargo build -p ankh-forge`, `cargo test -p ankh-forge trail` |
| zombie | Python/uv | `uv run scripts/zombie_consumer.py <subcommand>` |
| governance | text edit | direct file edit — no runner needed |
| nursery | text edit | direct file edit — no runner needed |
| MILF-Core | text create | create new file in `codex/codex-session-logs/archive/` |

### Per-domain commit message format

```
# autoloop / infrastructure
feat(autoloop): <what-changed>
feat(infra): <what-changed>

# ruby-zjit
fix(ruby-zjit): <what-changed>

# ankh-forge / REM
fix(rem): granite.rs — <critical#N short label>

# zombie
feat(zombie): A4 upcycle subcommand — <short label>

# governance
chore(gov): <target-file> — <what-changed>

# MILF-Core
feat(milf-core): Step6 Umeko entity card — <short label>

# All commits — structured state trailers (machine-readable cold-start signal)
Pentea-Completed: <queue-id[,queue-id...]>  # what this commit closes
Pentea-Next: <queue-id>                     # next execution target after this commit
Pentea-Domain: <D1|D2|D3|D4|D5|D6>         # which domain queue was advanced
Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>
```

**Trailer contract:** `Pentea-Next` is the canonical routing signal. Reading `git log --format='%B' -1 | grep '^Pentea-Next'` at cold-start yields the current execution target without any file reads. The stewardess table is the human view; git history is the ground truth. Self-validation closes the loop: the commit that proves work done also declares what comes next — no webhook, no notification channel, no external routing required.

### Validation gate before ✅

| Domain | Required before marking done |
|--------|------------------------------|
| ruby-zjit build | Script exits 0, all `-Probe` outputs show OK |
| ruby-zjit tests | All targeted test files pass Minitest |
| ankh-forge | `cargo test -p ankh-forge --quiet` passes |
| zombie | `uv run scripts/zombie_consumer.py <subcommand>` exits 0 + behavior confirmed |
| governance text edit | File saved, link opens correctly |
| MILF-Core card | All §5.2 schema fields populated (no `TODO:` markers) |

---

## § Blocked Items (requires Savant input)

| ID | Blocked On | Question |
|----|-----------|---------|
| RE-10 | The Savant | (1) Is one runestone-per-day immutable artifact or mutable latest snapshot? (2) Is repo-local `.chthonic` now the only canon, or must legacy home-directory trails remain first-class? (3) Should the schema block be human-readable provenance, machine-enforced validation, or both? |
| ZE-05 | A4 review | The Savant must review `zombie upcycle` output before A5 scope is confirmed. |
| MC-02/03 | MILF-Core card count | Conflict Pairs + Chemical Matrix are more valuable after 3-4 entity cards exist (current: 2 canonical cards). May proceed in parallel after MC-01 (Umeko). |

---

## § Audit Trail (completed work, last 30 days)

| Date | Commit | Domain | Summary |
|------|--------|--------|---------|
| 2026-04-24 | `47b56e60` | infra/agentry | AI-02: Pentea.agent.md Queue-Chain Protocol + email fix (223556219) |
| 2026-04-24 | `5fb446e8` | infra/autoloop | AI-01: pentea_autoloop.ts SDK agentStop hook + tasks.json Autoloop tasks |
| 2026-04-24 | `4a4d5d96` | stewardess | D2 RE-01..RE-09 all ✅, 19/19 tests, commit `4d623a2c` recorded |
| 2026-04-24 | `4d623a2c` | ankh-forge/REM | D2 complete: decode_stone+decode()+query_verify_only+--verify-only+golden roundtrip |
| 2026-04-24 | `1a5db9de` | ruby-zjit | RZ-02..RZ-06 complete — podman verified, Win32 suite 7/7, YAML sealed |
| 2026-04-24 | `493cd179` | ruby-zjit | Containerfile Layer4 graceful + test_win32 rv alias (rv.exe) + $Verbose fix |
| 2026-04-24 | `993227c1` | ruby-zjit / nursery | Nursery: Ruby+GPU JIT conditionality + promotion criteria |
| 2026-04-24 | `2bcba94a` | ruby-zjit / nursery | Nursery: JIT Boundary Contract (novel) + ZJIT crash root cause tightened |
| 2026-04-24 | `67767baf` | ruby-zjit | tighten rv diagnosis comments (cmd.status, Unix phrasing, remove ms estimates) |
| 2026-04-24 | `daa44ad5` | ruby-zjit | -StartupProbe + rv Win32 exec() diagnosis comments |
| 2026-04-23 | `70ed1916` | SSOT / governance | pattern-nursery: DCRP-RDV row 3 + FA³ spectral note |
| 2026-04-23 | `0c7333cb` | governance | Pentea.agent.md + Navigation Beacons: RDV rows 1+2 |
| 2026-04-23 | `ec010e03` | SSOT | `copilot-instructions.archive.md §XV.7` DCRP-RDV sub-section + 3-condition constraint |
| 2026-04-22 | `f151a650` | agentry | `decision-razor/agents/openai.yaml` CRITICAL fix |
| 2026-04-22 | `2ae5465c` | agentry | `skill-polisher/agents/openai.yaml` CRITICAL fix |
| 2026-04-22 | `6cbb5c97` | ruby-zjit | rv spinel canonical path resolution + -Bench differential |
| 2026-04-22 | `bcdb8a0d` | ruby-zjit | rv ridk exec integration + .ruby-version pin |
| 2026-04-22 | `47707544` | scripts QOL | PYTHONUTF8=1 + PYTHONIOENCODING profile-consolidated |
| 2026-04-22 | `e9a9fc93` | scripts T2 | skill_index+skill_health+skill_audit trio |
| 2026-04-21 | `7772a9c0` | scripts T2 | theme-sync.ps1 glob-primary dst, -VerifyOnly, hash mismatch exit |
