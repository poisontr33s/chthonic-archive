# Research Digest — DSL parsing modernization (triangulated)

Source: 2 Gemini DR returns triangulated — `G_31_P` (3.1 Pro, dense) + `G_35_F`
(3.5 Flash, verbose). Classification: methodology research. Analysis-only — no
code changes flow from this digest; it informs a migration decision the architect
owns.

## Convergent core (both returns agree — high confidence)

1. **Abandon monolithic PEG.** Both rank pest last; the silent-prose-fallback
   (malformed substrate swallowed as prose) is the central, unfixable-in-PEG hazard.
   Matches what our own grammar is already fighting (longest-first ordering, bold_prose).
2. **Two-layer composed architecture: macro (markdown structure) → micro (substrate).**
   Macro extracts byte-ranges of DSL spans + fenced blocks; prose is skipped, never
   a fallback. This is the load-balancing answer — and it dissolves our fenced_code_block/
   bold_prose hacks structurally.
3. **Micro layer = chumsky with explicit error recovery** (`recover_with` /
   `skip_then_retry_until`). Errors surface instead of degrading to prose — the direct
   cure for silent misclassification.
4. **Operator algebra = Pratt parsing, data-driven binding powers** (`chumsky::pratt`),
   precedence in a config table, not baked into productions. Adding an operator = one
   table row, zero grammar refactor.
5. **Drift-resistant conformance = `insta` snapshot tests of the AST** + `cargo-insta
   review` for interactive, rewindable accept/reject. This is the direct upgrade of our
   `patterns.json` (example→expected) into golden-master AST snapshots.
6. **Parser-swap portability = a parser-agnostic intermediate + adapters.** Pro calls
   it "Universal AST schema + adapters"; Flash calls it "parser-agnostic CST (cstree/
   rowan) + `ParserBackend` trait + inflation layer." Same pattern: conformance corpus
   decoupled from backend, so pest stays usable during migration.
7. **LLM grammar induction = agentic Evaluator-Optimizer / self-healing loop**, the
   `insta` suite as the deterministic evaluator. This is exactly the hand-loop I run now,
   automated. Later-stage; not first.
8. **Incremental re-parse (O(log N))** for the 10K-line evolving source.

## Decisions

| Decision | Options | Recommendation |
| --- | --- | --- |
| Macro/structural layer | tree-sitter (Pro) vs pulldown-cmark (Flash) | **pulldown-cmark** — see CONFLICT below; environment-decided |
| Micro/substrate parser | chumsky vs logos+Pratt vs keep pest | **chumsky** (error recovery + native Pratt) |
| Operator precedence engine | hardcoded climbing vs data-driven Pratt | **data-driven Pratt**, table in `.chthonic/*.toml` (project already uses toml configs, e.g. voice-iter.toml) |
| Syntax tree | plain AST vs Lossless Syntax Tree (cstree/rowan) | **LST (cstree)** — round-trip byte-fidelity serves canonical-source + no-delete; doubles as the swap-portable CST |
| Conformance harness | current dsl-pattern-test vs insta snapshots | **insta snapshots** over the agnostic CST; keep patterns.json as the corpus, snapshot the AST |
| Anti-silent-swallow guarantee | manual patterns only vs + property fuzzing | **add proptest negative-mutation fuzzing** (Flash-only; guarantees malformed never parses-as-prose) |
| Operator precedence/assoc VALUES | (the two returns disagree) | **ARCHITECT'S CALL** — semantic, not a DR decision (see CONFLICT) |

## CONFLICT: macro layer — tree-sitter vs pulldown-cmark

- `G_31_P` recommends **tree-sitter** (GLR, `injections.scm`, best-in-class incremental).
  Acknowledges friction: tree-sitter grammars are authored in a JS DSL compiled to C.
- `G_35_F` recommends **pulldown-cmark** (pure-Rust pull-parser, `.into_offset_iter()`),
  no JS/C/WASM at build.

Resolution (environment-grounded): **pulldown-cmark.** This box has **no node on PATH —
bun-only** (verified this session). tree-sitter's grammar toolchain is Node/JS-authored;
adopting it drags exactly the runtime we've been removing. pulldown-cmark + cstree gives
the same macro→micro split and round-trip in pure Rust, and we build the incremental layer
on cstree rather than inheriting tree-sitter's C build. Revisit tree-sitter only if an
LSP/editor-grade incremental injection becomes the priority AND a node toolchain is
acceptable.

## CONFLICT: operator precedence table — the returns disagree

- `G_31_P`: × > + > ↔ > {= , →}; `→` and `=` right-assoc, low precedence; `↔` non-assoc.
- `G_35_F`: `→` highest (50, right) > × (40, left) > + (30, left) > ↔ (20, none) > = (10, right).

They agree on associativity for ×/+/↔ (left/left/none) and `=` right; they DISAGREE on
`→` precedence and associativity. This is a semantic call about what the catalyst's
operators MEAN (is `→` projection tighter or looser than `×`?). **The Savant decides this**;
the DR can't. Once decided, it's one TOML table either way (data-driven Pratt makes it cheap
to change).

## Actionable items (routing-tagged; sequenced, not yet started)

- [ ] [manual] Architect fixes the operator precedence/associativity table (the one semantic
  decision above). Output: `.chthonic/grammar/operators.toml`.
- [ ] [chthonic] Spike: pulldown-cmark macro extractor → byte-ranges of DSL spans + fenced
  blocks; verify against a slice of SSOT.md. Closable proof.
- [ ] [chthonic] Define the parser-agnostic CST (cstree `RawSyntaxKind`) + `ParserBackend`
  trait; write the pest adapter first (keeps the current grammar usable while migrating).
- [ ] [chthonic] chumsky micro-parser for ticked_id/ticked_phrase/alias_chain/invocation +
  `chumsky::pratt` reading operators.toml; emit into the agnostic CST.
- [ ] [chthonic] Convert patterns.json conformance into `insta` AST snapshots; wire
  `cargo-insta review` as the rewindable gate (supersedes dsl-pattern-test).
- [ ] [chthonic] Add proptest negative-mutation fuzz: every malformed mutant must error,
  never parse-as-prose.
- [ ] [chthonic] (later) Agentic Evaluator-Optimizer loop with the insta suite as evaluator.

## Dependencies (Rust, 2026)

`pulldown-cmark` (macro), `chumsky` 0.13+ with `pratt` feature (micro+operators),
`cstree` or `rowan` (LST + agnostic CST), `insta` + `cargo-insta` (snapshot conformance),
`proptest` (mutation fuzz), `serde` (CST serialization). All pure-Rust; no node. `logos`
optional if a separate lexer is wanted.

## Method note

This stays cheap to adopt incrementally: the agnostic CST + `ParserBackend` trait means
pest, the current pattern corpus, and the just-landed `ticked_phrase` work all remain valid
during migration — each layer (macro extractor → CST → chumsky micro → insta) is a closable
slice, prototyped against the existing patterns before commitment. No big-bang rewrite.
