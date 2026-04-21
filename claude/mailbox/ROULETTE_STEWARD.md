# ROULETTE STEWARD — Autonomous Dispatch Protocol

> **Purpose:** Contra-intervention against The Savant's 99.9% abandonment rate.
> **Model:** Pentea injection contract. Cold-start capable. No human direction required after load.
> **Blueprint:** `claude/mailbox/SCRIPTS_ROULETTE.md` — single source of execution state.
> **Commit trailer:** `Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>`

---

## Cold-Start Bootstrap (2 reads, then execute)

```
1. read_file SCRIPTS_ROULETTE.md lines 1-25   → read Progress Trail table
2. grep SCRIPTS_ROULETTE.md for "⬜"          → first ⬜ row = next execution target
3. Execute. No planning pass. No orientation speech.
```

**If progress trail is absent or stale** — re-derive from ✅/⬜ counts in each tier table.

---

## Execution Loop

For each ⬜ item, in order (score-descending, tier-ascending T1→T2→T3→T4→T5):

```
PASS 1 — Read the target file. Understand what exists.
PASS 2 — Implement the Action column items. Validate (dry-run or direct invocation).
PASS 3 — Commit. Update roulette row ✅. Update Progress Trail count.
```

**One item per turn.** Commit before moving to next. No batching across unrelated files.

**Exception — T3 skill_tensor batch:** The 9× `skill_tensor_*.py` import fix is a single execution unit. Read all 9, fix all 9, commit once, mark all 9 ✅ together.

---

## Per-Item Execution Contract

### Read phase
```powershell
# Always read the target before touching it
read_file scripts/<target>
```

### Implement phase
Follow the **Action** column exactly. Do not improvise scope beyond it. If the action is ambiguous, apply the conservative interpretation and mark what was done in the ✅ shorthand.

**Toolchain routing:**
| File type | Run via |
|-----------|---------|
| `.py` | `uv run scripts/<file>.py` |
| `.ps1` | `pwsh -NoProfile -File scripts/<file>.ps1` |
| `.ts` / `.mjs` | `bun run scripts/<file>.ts` |

### Validate phase
Run the script with the new flag/behavior. Capture at least one line of output confirming the new behavior fires. If validation fails — fix, re-validate. Do NOT mark ✅ on failed validation.

### Commit phase
```
git add scripts/<target>
git commit -m "roulette(T<tier>): <script-basename> — <1-line shorthand of what changed>

Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>"
```

### Mark phase
Edit `SCRIPTS_ROULETTE.md`: change `⬜` → `✅`, append shorthand of what was actually done to the Action column (preserve original text). Update Progress Trail count for the tier.

---

## Batch Detection Rules

| Pattern | Treatment |
|---------|-----------|
| Same fix across N files (T3 skill_tensor) | Single execution unit, one commit, mark all N ✅ |
| Same `erdno`→`eldno` typo fix | One commit per file — don't batch across tiers |
| `--dry-run` + `--json` flags | Same file, same commit |
| Unrelated scripts in same tier | Separate commits |

---

## Session-End Handoff

When context pressure mounts OR after completing a full tier sub-section, write to `claude/mailbox/`:

```
ROULETTE_CHECKPOINT_<YYYYMMDD_HHMM>.md
```

Contents:
```markdown
## Roulette Checkpoint — <datetime>
- **Last committed:** <script> — <commit hash>
- **Next target:** <script> (<tier>, score <N>)
- **T<N> progress:** <done>/<total>
- **Blockers:** <none OR describe>
```

This is the re-entry point for the next session. No Savant briefing required.

---

## Priority Queue (current state — 2026-04-21)

**Execute in this order:**

### T1 Remaining (2 items)
1. `scripts/claude_ide.ps1` (score 1.5) — `.mcp.json` validation + backup + `verify-mcp` subcommand
2. `scripts/desktop-clone-state.ps1` (score 1.0) — size estimate + disk space check + `--exclude-git`

### T2 — start score-descending
3. `scripts/theme_contrast_audit.py` (score 3.0) — `sys.path.insert` guard; exit codes; `--emit-junit`
4. `scripts/theme-sync.ps1` (score 3.0) — hash verify after copy; `-VerifyOnly`; glob-based path-finding
5. `scripts/git_snapshot.py` (score 3.0) — `--quiet/-q`; `resolve_ssot_paths()` for mailbox dir; `--since <ISO>`
6. `scripts/run_archaeology.ps1` (score 3.0) — print `$runFailures` at end; remove dead `-LocalV2`; `-What` switch
7. `scripts/mcp-asc-injector.ts` (score 2.0) — SSOT existence check at startup; `ping` tool
8. `scripts/run_overnight_daemon.ps1` (score 2.0) — `Get-Command bun` first; `-Timeout N`; exit code propagation
9. `scripts/local_refiner_v2.py` (score 2.0) — normalize output schema; `--validate`; `--model-list`
10. `scripts/hf_refiner.py` (score 2.0) — exponential backoff; `--model` flag; `--ore-dir` configurable
11. ... *(continue score-descending through T2, then T3 batch, then T4, then T5)*

### T3 Batch (execute as single unit)
- All 9 `skill_tensor_*.py` files — `sys.path.insert(0, str(Path(__file__).resolve().parent))` on each
- Then `skill_tensor_cycle.py` and `skill_tensor_common.py` individually

### T3 Hotspot
- `sfs.ps1` consolidation (score 3.0) — shim or tombstone
- `erdno`→`eldno` in `setup-gemini-claude.ts`, `validate-triad-links.ps1`, `build_epistemograph.py`

---

## Anti-Patterns (hard stop)

| Forbidden | Response |
|-----------|----------|
| "I would recommend..." | Skip to implement |
| Read file, produce plan, stop | FAILED — produce artifact or nothing |
| Ask user what to do next | Read roulette, find next ⬜, execute |
| Mark ✅ before validation passes | FAILED — validate first |
| Batch unrelated files into one commit | Separate commits |
| Invent scope beyond the Action column | Conservative interpretation only |

---

## Invocation — Pentea primed injection

Load this file at session start. Then:

```
INJECTION COMPLETE.
Next target: <first ⬜ from queue above>
Proceeding.
```

No additional briefing from The Savant required.
