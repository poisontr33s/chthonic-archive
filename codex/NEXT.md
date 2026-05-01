---
type: waypoint
category: codex, claude, github copilot
updated: 2026-05-01
---

# Codex: Next Steps

## Vulkan-Lab V6 Arc — G5+G6+G7 (2026-05-01)

**Status: landed.** Gates G5, G6, G7 committed in overnight arc. Release binary built.

- **G5:** `StatePhase` FSM (`Idle→Spinning→Decelerating→Landed`). SpinState ≡ RoomState — same 4-phase graph, two render projections.
- **G6:** Dungeon render mode (`--dungeon` flag). `ascii_dungeon.comp.spv`, 4×STORAGE_BUFFER + `push_constant uint state_phase`. BLOCK_CHARS extended to 13 entries (box-drawing indices 5–12). Urca de Lima synthesis confirmed: roulette IS dungeon (one manifest, two projection functions).
- **G7:** `vulkan-lab/cli-renderer/GATE_WALK.md` — gate walk seeds next epoch. `todo_roulette.ts` `--live --dungeon` pass-through live.
- **V7 vector:** force-directed GPU room layout (spring-force compute pass), hot-reload manifest watcher, room collapse animation on task completion.
- **Gate walk:** [vulkan-lab/cli-renderer/GATE_WALK.md](../vulkan-lab/cli-renderer/GATE_WALK.md)


## Current State (2026-03-14)

- **Reasoning:** `extra high` (workspace + global)
- **Self-modification:** Denied (config, instructions, AGENTS.md all locked)
- **Git:** Read-only (no commit/add/push)
- **Skills:** 27 non-system in `.codex/skills/` (cap is 15 — consolidation needed, 12 over)
- **Mailbox:** `codex/mailbox/ACTUAL-WORKING-HANDOFFS/` is the task queue
- **MILF-Core Pipeline:** Steps 1–4 complete, 7 prototypes analyzed (P1–P7 incl. Planescape: Tides of Numenera), MILF-Core spec at 24/24 dimensional coverage

## Toolchain Overlay (2026-03-23)

- **Host verifier:** green for Rust, Ruby, Go, JavaScript, Solana, Anchor, WASM, SQL, and infra lane detection
- **PowerShell lane:** 7.6.0 active
- **Ruby lane:** standardized on `rv` `ruby-4.0.2`, with raw-shell `ruby` visibility repaired
- **Go lane:** standardized through `goup`, default `go1.26.1`
- **R lane:** unmanaged `R 4.5.3` runtime active, `rv-r 0.19.0` available
- **Zig lane:** `zv 0.9.2`, `zig 0.15.2`
- **Brush lane:** repo/global compatibility rescue in place for Windows hybrid behavior
- **Mise lane:** standardized on Cargo ownership (`mise 2026.3.12`)
- **Native crypto lane:** `OpenSSL 3.6.1 (64-bit)` installed and bound for MSVC cargo
- **Solana lane:** `solana-cli 3.1.9`, `agave-install 3.1.9`
- **Anchor lane:** `avm` installed, `anchor-cli 0.32.1` active
- **Migration memory:** [LAPTOP_TO_DESKTOP_EMIGRATION.md](artifacts/LAPTOP_TO_DESKTOP_EMIGRATION.md)
- **Strategic control surface:** `chthonic toolchain ...` + `chthonic memory ...` now expose the repaired workstation state directly
- **Extended lane control:** `chthonic r lane` and `chthonic zig lane` expose the newly bound R and Zig lanes directly
- **Command surface inventory:** `chthonic commands counts` reports `23` canonical domains, `8` compatibility domains, `68` canonical documented forms, `76` direct documented forms, and `17` nested action aliases; `claudine` forwards the same surface for `153` combined entrypoint forms

## Active Chore

**`CHORE_CODEBASE_HYGIENE_2026_03_09.md`** — Seven-zone structural hygiene across skills (27→≤15), mailbox (294 files), scripts (255 files), tracked .pyc (6), root files (16+), forge dedup, and migration plan completions.

## Pending Work

1. **Skill consolidation** — Reduce from 27 to ≤15 per AGENTS.md anti-proliferation rules (5 redirects, 2 stashed, 1 protocol identified)
2. **Mailbox rotation** — 294 files need census, rotation policy, and archive engine
3. **Scripts variant triage** — 6+ variant families (decorator_cross_ref 3×172KB, hf_6×, claude_8×)
4. **Scripts Phase 3** — Relocate .md docs from scripts/ to docs/
5. **Tracked .pyc cleanup** — 6 compiled bytecode files tracked in git
6. **Root file archaeology** — 16+ stale artifacts at repo root
7. **Forge dedup audit** — furnace↔tempered 1:1 mirror after perfect 18/18 graduation
8. **Native manifest normalization** — advance `extensions/chthonic-archive/native/Cargo.toml` direct deps in a controlled order now that OpenSSL/Solana/Anchor lanes are alive
9. **Graphics/content continuation** — keep binding HLSL/runtime/content lanes now that workstation blockers are removed
10. **Control-surface refinement** — continue tightening `chthonic.ps1` / `claudine.ps1` around the now-proven workstation lanes rather than adding parallel wrappers

## WIP Lanework: MILF-Core

Organ-to-Surface-to-Prototype pipeline — comparative prototype research for entity-level genre spec.
- **Step 3** (Sets + 7 Prototypes): [MILF-Core-Step3-Deep-Exploration-Prototypes.md](codex-session-logs/archive/MILF-Core-Step3-Deep-Exploration-Prototypes.md)
- **Step 4** (Gap Analysis + MILF-Core Spec): [MILF-Core-Prototype-Analysis.md](codex-session-logs/archive/MILF-Core-Prototype-Analysis.md)

## Rules

- Check `codex/mailbox/MAILBOX_CURRENT_STATE.md` for task priority
- Execute tasks from `ACTUAL-WORKING-HANDOFFS/` as written
- Do not self-document, self-audit, or generate meta-reports unprompted
- **Claude** is the steward/engineer. **Codex** is the shepherd of the workspace/codebase. **Gemini** is the velocity engine (when active).
