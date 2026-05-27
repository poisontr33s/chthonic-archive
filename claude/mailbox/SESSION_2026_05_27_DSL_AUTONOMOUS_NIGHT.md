---
type: session-handoff
session: 4849c0f2-2beb-4572-b97c-42c98ee743dc
date: 2026-05-27
author: claude
lane: dsl-substrate-phase-0
context: autonomous continuation while user slept
---

# DSL Phase 0 — Autonomous Continuation Summary

Continued the iteration work safely under the rewindability/cessation discipline you named ("compound knowledge of what the process of the pester + back and forth itself, leverage point as solution to the danger/non-reversables"). Built the meta-tooling first, then used it to baseline + measure further.

## What landed (commits since you left)

- `8a10f637` **tools/dsl-smoke/** — promoted the throwaway /tmp/ tool suite to a tracked workspace member. 5 binaries (dsl-smoke / dsl-audit / dsl-bisect / dsl-probe / dsl-full-smoke). `build.rs` reads canonical grammar from `.chthonic/grammar/chthonic.peg` at compile time with `cargo:rerun-if-changed`. Past grammar states are now re-smokeable.

- `301f2fb4` **rewindability tooling** — `scripts/dsl_iteration_check.py` (TOOL_DSL_ITERATION_CHECK_V1) + `manifest/dsl_iteration_history.ndjson` ledger + `dsl-full-smoke` binary. Auto-detects 3 regression classes (parse_rate_drop / shadow_rise / plateau). De-dups on grammar_hash.

That's it from grammar perspective — **I did not edit the grammar further**. Per "smart cessation" discipline, the next gap revealed by full-SSOT smoke is architectural and warrants your call.

## Baseline state captured in ledger

```
grammar_hash=c2c8cfc4c65377e8
slices=6/6  shadows=0  full_ssot=FAIL@L45
```

The 6-slice corpus + audit are both clean. The full-SSOT smoke surfaced what the 6-slice corpus missed.

## Pattern catalog — and a significant catalog-revealed shadow

Per your "Build the pattern catalog first" pick, landed `.chthonic/grammar/patterns.json` + schema + `dsl-pattern-test` binary + initial 15-pattern catalog. The catalog encodes "what worked vs didn't" as data — automatable, durable across sessions, regrowable from failures.

**Immediate finding from the catalog**: a hidden shadow we didn't know about.

The catalyst's PRIMARY backtick-id convention is `` `Title-Case-With-Hyphens` `` (e.g., `` `The-Savant` ``, `` `Codex-Brahmanica-Perfectus` ``, `` `Apex-Synthesis-Core` ``). Current `ticked_id` rule requires uppercase-only content via the `identifier` rule, so all Title-Case backtick-ids silently fall through to `bold_prose` when wrapped in `**`, or to `prose_fragment` outside it. The 6-slice smoke didn't surface this because catalyst's heaviest multi-alias regions (where backtick-id density is high) are inside fenced code blocks consumed by `fenced_code_block`.

So the "6/6 + 0 shadows" slice result was true *for the slices tested*, but the catalyst at large has a structural misclassification.

Pattern catalog test result: 12 PASS, 3 FAIL (expected) — three architectural-decision patterns waiting:
- `bold_parened_id_multi_alias` — Title-Case backtick-ids inside multi-alias chains
- `ticked_id_titlecase_content` — bare `` `Title-Case` `` (sibling failure, same root)
- `l45_substrate_arrow_titlecase_prose` — the L45 finding from full-SSOT smoke

The first two share ONE architectural fix (widen `identifier`/`ticked_id` to admit lowercase, OR add `ticked_phrase` with Title-Case discipline). The third is separate.

## Then you asked the meta-question (post-catalog)

Your follow-up: *"to be doing this robustly. We log every instance of every working and not working, and classify it with verbosity? Then hook it with the DSL and the existing to improve it as we fail, succeed? So that we have the right tools to catch everything to the process to optimize it, itself? With what is done, and what isn't?"*

Yes — exactly that shape. Landed `dsl-coverage` binary that logs EVERY paren occurrence in catalyst (7,092 of them) with `{line, col, content, inferred_category, grammar_top_rule_actually_matched, grammar_inner_rules, classification}`. Output: `manifest/dsl_coverage_paren_audit.json` (73K+ lines, full per-occurrence record).

**Coverage baseline at grammar c2c8cfc4c65377e8: 77.47%** (5,494/7,092 paren occurrences matched the expected rule for their inferred category).

Mismatch breakdown — exactly the data telling us where to look next:

| Mismatch | Count | % | Fix |
|---|---|---|---|
| ticked_single → prose_parens (expected parened_id) | 1,086 | 15.3% | ticked_id Title-Case admission |
| multi_alias_backtick → prose_parens (expected multi_alias) | 394 | 5.6% | same as above |
| phrase_titlecase → prose_parens (expected parened_phrase) | 98 | 1.4% | 5 sub-gaps (see below) |
| classifier-edge cases | 20 | 0.3% | classifier refinement, not grammar |

**Top two rows share ONE fix.** Title-Case ticked_id admission flips 1,480 occurrences (20.9% of paren surface) at once. That's the single highest-leverage architectural change visible from the data.

The 98 phrase_titlecase mismatches break into 5 distinct sub-gaps the coverage pass discovered automatically:

1. **Colon as phrase_delim** — `(Eternal-Loop: Infinite Human Potential)` + ~30 others
2. **Slash with spaces as phrase_delim** — `(Alabaster Voyde / Snow White)`
3. **↔ without spaces** — `(Tier 4↔T3)` (current `" ↔ "` requires spaces)
4. **Apostrophe in phrase_word** — `(Decorator's Resurrection)`
5. **Measurement notation** — `(B 112/ W 58/ H 108cm)`

Each is a one-line grammar widening. Coverage tool measures progress automatically as each lands.

**This IS the answer to your meta-question**: catalog (sparse, hand-named) + coverage (dense, exhaustive) are complementary. Catalog encodes known patterns; coverage discovers unknown ones. Together: "what's done" (correctly classified) AND "what isn't" (still mismatched). The process optimizes itself because the data tells it where to look next. Same surface extends to bold spans, backtick spans, fenced blocks, headers — paren was the densest signal so I built it first.

## The full-SSOT finding (the architectural decision waiting)

Line 45 of SSOT.md:
```
* **(`Update-Protocol`):** *All substantive edits flow through **(`SSOT`)** → Branch files reference **(`Never-Duplicate`) → (`Hash-Verification`)** per **(`§XIV.3`)**.*
```

Composition rule expects strict `operand binary_op operand`. Catalyst uses `→` more loosely: `**(`SSOT`)** → Branch files reference ...` — substrate-bold followed by Unicode arrow followed by *bare title-case-then-lowercase prose*. The grammar has no operand alternative for "bare title-case word like `Branch`" at statement level.

Three design directions to choose between:

1. **Add bare phrase_word as operand** — `Branch` becomes a valid composition operand. Risk: greedy match could eat unintended things outside substrate context.

2. **Add substrate_marker as statement-level alternative** — `→` (and friends) can stand alone at statement-level, with surrounding prose handled by prose_fragment. Treats the catalyst's `→` use as ornamental marker, not strict composition. Probably truer to catalyst semantics.

3. **Document as Phase 0 known limitation** — catalog the pattern, defer to Phase 1+ when AST representation can distinguish "strict composition" from "ornamental marker" semantically. Punts the parser-level question.

I'd lean toward (2) — it matches how the catalyst actually uses arrows in flowing prose — but didn't act on it autonomously since it's a structural choice.

## Methodology + memory captured

- `tools/dsl-smoke/README.md` — full iteration discipline + worked history table (iter 1-6) + rewindability section + cessation signals
- Memory `reference-dsl-iteration-rewindability` — durable principle capture (in your `~/.claude/projects/.../memory/` diary, indexed in MEMORY.md)

## Recommended next moves (for when you're back)

Pick by appetite. The catalog now makes architectural-decision patterns explicit so each next move has a clear test target.

| Option | What | Cost |
|---|---|---|
| A | Decide `ticked_id` Title-Case admission (fixes bold_parened_id_multi_alias + ticked_id_titlecase_content + a large class of catalyst content). Three sub-options: widen identifier_char, add ticked_phrase, or split into strict+permissive. | 1 grammar iteration, pattern catalog verifies 2 patterns flip from FAIL to PASS |
| B | Decide L45 architectural question (substrate_marker at statement level vs bare phrase_word operand vs document-and-defer) | 1 iteration, catalog verifies l45_substrate_arrow_titlecase_prose flips |
| C | Pivot to your originally-named next step — Phase 0 emoji grammar extraction as a separate module | 1-2 iterations |
| D | Reconsider Q1 framing (DSL vs substrate-extraction). The catalog now has ENOUGH data (15 patterns spanning 4 categories) that the right tool is visible — substrate-extraction is the lower-pain path. | architectural conversation |
| E | Promote to Phase 1 — scaffold `tools/chthonic-dsl/` proper crate, PyO3 bindings | major scaffolding session |
| F | Investigate ticked_phrase with internal spaces (`` `The-ASC-As-Living-Organism - Physiological-Hierarchy` ``) — adjacent to A | 1 iteration, add as a 4th catalog entry |

## How to use the new tooling

```powershell
# Pattern catalog — verify each pattern parses as expected
cargo run -p dsl-smoke --release --bin dsl-pattern-test

# Run all smokes + audit + full-SSOT + capture state in ledger
uv run scripts/dsl_iteration_check.py

# Show last N ledger rows
uv run scripts/dsl_iteration_check.py --show-history 5

# Dry-run (don't update ledger)
uv run scripts/dsl_iteration_check.py --dry-run

# Run individual binaries
cargo run -p dsl-smoke --release --bin dsl-smoke -- .chthonic/SSOT.md
cargo run -p dsl-smoke --release --bin dsl-audit -- .chthonic/SSOT.md
cargo run -p dsl-smoke --release --bin dsl-full-smoke -- .chthonic/SSOT.md
```

## On your Q1 / Q2 questions

**Q1 (DSL vs PL vs DSL→PL)** — I gave my honest take: the catalyst is prose with embedded structured constructs, closer to literate annotation than DSL. Substrate-extraction (tree-sitter / regex / pulldown-cmark + custom inline parsers) would have lower iteration pain. The pest grammar work isn't wasted; its rules become extraction patterns. You picked "build pattern catalog first, decide after" — the catalog now has 15 patterns + 3 architectural-decision blockers, enough data for the decision to be informed.

**Q2 (automating "what worked vs didn't")** — the pattern catalog IS that automation. Each pattern is `{name, example, expected, status, since_iter}` — encoded knowledge of what the grammar should handle. The dsl-pattern-test binary compares actual parse-tree shape to expected, flagging Regression / Shadow / Improved / ConfirmedFail. Future failures become new catalog entries; future iterations test against ALL of them. The catalog grows monotonically.

Concrete next: when you fix the ticked_id Title-Case admission, dsl-pattern-test will flip 2 patterns from FAIL to PASS automatically. No re-deriving "what worked" — the catalog remembers.

## State of the working tree

`git status` should show:
- Modified: `tools/dsl-smoke/README.md` (expanded with methodology section)
- Possibly: `manifest/lore_canon_refs_audit.json` (pre-commit hook re-runs the canon-refs check on each commit, updating this snapshot)

Both small; uncommitted because they're trivial enough to wait for your direction.

## Status of the ledger

```ndjson
{"grammar_hash": "c2c8cfc4c65377e8", "slices=6/6", "shadows=0", "full_ssot=FAIL@L45"}
```

Single row. Next grammar change will append a second row + auto-compare. If it regresses, exit-code 1 + recommendation to revert.

## Tone note

Followed your earlier directives — no postscript drift, clean framing, no chunked surgery, no novelization of the process itself. The work above is all the autonomous work I did. No surprises hidden in the diff.

Sleep well.
