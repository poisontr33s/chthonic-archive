# ROULETTE STEWARD — Autonomous Dispatch Protocol

> **(`PRPS`):** Contra-intervention against **The-Savant**'*s*-**99.9%**-*abandonment rate*.
> **(`Milf`/`Tier`):** **Pentea**-*injection*. Cold-start capable. No human direction required after load.
> **(`BLPRT`):** `claude/mailbox/SCRIPTS_ROULETTE.md` — single *source-of-execution* state.
> **(`CTLR`):** `Co-authored-by: Pentea <6996xxxnsfw+Penteaa@users.noreply.github.com>`

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
| Same `eldno`→`eldno` typo fix | One commit per file — don't batch across tiers |
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

## Priority Queue — 2026-04-21 (COMPLETE)

**All tiers T0→T5 are done. No ⬜ items remain.**

| Tier | Completed | Last commit |
|------|-----------|-------------|
| T0 | 9/9 ✅ | prior sessions |
| T1 | 12/12 ✅ | `336f26d1` |
| T2 | ~68/~68 ✅ | `e9a9fc93`, `9e1d70c1` |
| T3 | 16/16 ✅ | prior sessions |
| T4 | 2/2 ✅ | `88a675b4`, `8b40191c` |
| T5 thin-shims | 5/5 ✅ | `798150e1` |
| T5 assess-before-act | 11/11 ✅ | `a01857f0` |
| T5 prototypes + WIP | 5/5 + 1/1 ✅ | `d8912727` |

**Next session:** No roulette work remains. Steward is idle — await new blueprint or The Savant direction.

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

