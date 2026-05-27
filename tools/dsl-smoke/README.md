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
