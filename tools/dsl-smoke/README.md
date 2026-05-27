# dsl-smoke

Phase 0 grammar iteration tooling for the Chthonic DSL substrate. Reads the
canonical grammar at `.chthonic/grammar/chthonic.peg` (copied to `src/` at
compile time via `build.rs`).

## Binaries

- **`dsl-smoke <ssot.md>`** — parse 6 hand-picked stress-test slices through the
  current grammar; report rule-count distribution + prose fraction per slice.
- **`dsl-audit <ssot.md>`** — deeper inspection; verify no `prose_parens` span
  silently swallows substrate (shadow-failure detection).
- **`dsl-bisect <ssot.md>`** — find the first line N where a prefix [1..N] of a
  given slice fails to parse. Used to locate the failure boundary when slices
  fail beyond the obvious.
- **`dsl-probe <ssot.md>`** — single-line probes for grammar-rule isolation;
  edit `src/probe.rs` to add new probe cases.

## Workflow

```powershell
# Build (recompiles when canonical grammar changes via build.rs)
cargo build -p dsl-smoke --release

# Iteration loop
cargo run -p dsl-smoke --release --bin dsl-smoke -- .chthonic/SSOT.md
cargo run -p dsl-smoke --release --bin dsl-audit -- .chthonic/SSOT.md

# After editing grammar — single rebuild + re-smoke
cargo run -p dsl-smoke --release --bin dsl-smoke -- .chthonic/SSOT.md
```

## Iteration discipline

Each grammar edit should be a single focused change. Re-smoke after every
change. The iteration loop is:

1. `dsl-smoke` — parse pass/fail across 6 slices
2. If 1+ slice fails: read failure position, identify root cause
3. Design one targeted fix
4. Edit `.chthonic/grammar/chthonic.peg`
5. `dsl-smoke` again — observe delta
6. Run `dsl-audit` to confirm no shadow failures introduced
7. Commit when clean

See iter 1-6 commit history for worked examples (2026-05-27).

## Known iteration patterns

- **PEG ordered-choice trap**: longer alternatives must come BEFORE shorter
  ones (e.g., `" ↔ "` before `" "` in `phrase_delim`). Pest does not backtrack
  on alternative-length.
- **Silent atom for choice-rules**: when a rule like `prose_parens_atom` is
  just a priority cascade, mark it `_{...}` (silent) so the matched child
  shows directly under the parent. Otherwise type info is lost behind a
  generic wrapper node.
- **Audit beyond parse OK/FAIL**: shadow failures (substrate silently swallowed
  by a fallback rule) show up only via parse-tree inspection. `dsl-audit`
  surfaces these.
- **Bisect on multi-line slice failures**: when a slice fails at line N, the
  root cause might be at line M < N due to greedy multi-line matches. Use
  `dsl-bisect` to find the boundary.

## Rewindability discipline (2026-05-27)

The grammar iteration loop is forward-only by default: edit grammar →
re-smoke → forward-fix. This has a danger: a misdesigned iteration (e.g. the
iter-5 prose_parens that silently shredded substrate) cascades into the next
iteration's design context, making the regression harder to detect.

The rewindability tooling makes the loop reversible:

1. **Before** any grammar edit, run `dsl-iteration-check`. This captures the
   current state (slice pass count, audit shadow count, full-SSOT result) as
   a row in `manifest/dsl_iteration_history.ndjson`.
2. **Edit** the grammar (one focused change at a time).
3. **After** the edit, run `dsl-iteration-check` again. Three outcomes:
   - **Clean** — no regressions vs prior row. Continue.
   - **Regression detected** — `parse_rate_drop`, `shadow_rise`, or `plateau`
     flag fires. Exit code 1. **Prefer `git revert HEAD`** over chasing the
     regression with a forward-fix. The reverted state is known-good; the
     forward-fix from a bad state risks compounding the problem.
   - **Plateau** — same fail position 2+ runs. The current design is
     trapped; consider a different angle rather than another iteration.

The ledger is the audit trail. Any past grammar state can be re-smoked by
checking out the grammar from a past commit and running the tooling — the
in-repo `build.rs` ensures the past grammar text is what's parsed.

Smart cessation signals (when to stop iterating):

- **Plateau** (same fail position 2x in a row): the rule is genuinely
  contested by the catalyst; iterating won't help. Step back, gather more
  catalyst samples, redesign.
- **Shadow rise** (substrate silently eaten by a new rule): the new rule
  is too greedy. Revert + design with explicit exclusion.
- **Full-SSOT regresses** (was passing on slices, now fails on full): the
  6-slice corpus didn't cover something. Either extend the corpus or
  document the catalyst pattern as out-of-scope.

The methodology compounds (per user 2026-05-27): "compound knowledge of
what the process of the pester + and back and forth itself, this is a
leverage point to oversee as solution to the danger/non-reversables in a
process that we can research."

## Worked iteration history (2026-05-27)

Six iterations took the grammar from 0/6 to 6/6 slices + 0 shadows. Each
iteration was a single focused change:

| Iter | Change | Slices | Shadows | Notes |
|---|---|---|---|---|
| 0 | initial Phase 0 grammar | 0/6 | n/a | all 6 slices fail |
| 1 | bold_parened widening + phrase_id (Design A) | 0/6 | n/a | error messages advance; identifies more gaps |
| 2 | Unicode ↔ + = op + em-dash delim + PEG ordering fix | 0/6 | n/a | LONGEST-FIRST in phrase_delim was the bug |
| 3 | bold_prose fallback | 0/6 | n/a | 5 slices advance substantially |
| 4 | fenced_code_block (code-as-opaque) | 3/6 | n/a | Trinity Formula was in a code block all along |
| 5 | prose_parens fallback (single-level) | 5/6 | 6 | introduced silent substrate-shredding |
| 6 | recursive prose_parens + bare-operator recognition + silent atom | 6/6 | 0 | iter-5 fixed via more-principled design |

Iteration 5 → 6 is the canonical case where rewindability would have helped.
The iter-5 prose_parens passed the slice-count check (5/6 → progress!) but
introduced shadow failures (substrate silently swallowed). Without the audit,
this would have been a silent regression. The audit + rewind discipline now
catches such cases automatically.
