# Research Brief — Modern methods for transmuting a dense, bespoke DSL-in-markdown into an executable substrate

## The artifact

A single ~10,000-line markdown file is the canonical source-of-truth and generative
catalyst for a software project. It is not prose with code blocks — it is a dense,
bespoke domain-specific notation *embedded in* markdown, used consistently since
drafting. Observed substrate shapes:

- Typed short-codes: backtick/paren-wrapped identifiers in two distinct conventions —
  strict uppercase abbreviation-codes (`FA⁵`, `ASC`) and Title-Case named concepts
  (`The-Savant`, `Apex-Synthesis-Core`); these carry different semantics.
- Alias chains: slash-separated equivalence groups, often bold-wrapped.
- An operator algebra with precedence: projection `→`, multiplicative `×`, additive `+`,
  bidirectional `<->`/`↔`, assignment `=`.
- An invocation syntax: `$verb${arg}+$verb2${arg2}@$verb3${arg3}`.
- Section/line anchors, tier annotations, markdown headers used as tier-encoding,
  fenced code blocks (Python/PowerShell/YAML embedded as opaque content), and
  natural-language prose interleaved as filler between substrate tokens.

The goal is to transmute this from ornamental markdown into an executable substrate
(parse → AST → interpreter), incrementally and without losing the semantic
distinctions the notation encodes.

## Current method (for context, not endorsement)

A PEG grammar (Rust, pest) does Phase-0 recognition, paired with a parser-agnostic
conformance corpus of `(name, example, expected_rule)` triples and a rewindable
iteration ledger. The PEG approach works but visibly strains against ordered-choice:
mandatory longest-first delimiter ordering, and a prose-fallback rule that can
silently swallow mis-specified substrate. These are PEG-shape hazards, not corpus
problems.

## The questions

1. **Best-fit parsing method, 2026.** For a bespoke DSL *embedded in markdown* with
   operator precedence, interleaved prose, and embedded foreign code blocks — compare
   PEG (pest) vs tree-sitter (with injection/composed grammars) vs parser-combinators
   with error recovery (chumsky) vs Earley/GLR for ambiguity vs a lexer + Pratt
   operator-precedence layering. Which minimizes grammar drift and the need for
   ordering hacks?
2. **Layered / load-balanced parsing.** Is the right architecture a *composed* grammar
   (markdown layer + injected substrate layer) rather than one monolithic grammar?
   What does incremental re-parsing (re-parse only changed regions) buy for a 10K-line
   evolving source? How is the markdown/substrate boundary best separated?
3. **Operator algebra.** Best modern method to express the precedence/associativity of
   a small custom operator set cleanly, and to keep it data-driven rather than
   hardcoded in grammar productions.
4. **Drift-resistant iteration.** Is there a named methodology for corpus-driven
   incremental grammar development (a conformance suite of example→expected triples,
   regression-gated, rewindable)? What are the field's best practices for evolving a
   grammar against a fixed real-world corpus without silent misclassification?
5. **LLM-assisted grammar induction (2026 state).** Maturity and tooling for inducing
   or refining a grammar from a corpus with an LLM in the loop, verified against a
   conformance suite. Where does it help vs hand-authoring?
6. **Parser-swap portability.** Given a parser-agnostic conformance corpus, what
   patterns let a project evaluate/swap parser backends (pest → tree-sitter/chumsky)
   without rewriting the verification ground?

## Constraints

- Rust-primary; Python, C/C++, Bun/Node, Vulkan/CUDA, Win11-native all available as
  swappable modules. Bun (not Node) is the JS runtime.
- The source stays the canonical form; the parser/substrate is built *around* it, not
  by rewriting it.
- Reversibility/rewindability is a first-class requirement.

## Output requested

A ranked comparison of the candidate methods against questions 1–6, each with concrete
trade-offs for *this* shape of input (dense DSL-in-markdown, operator algebra, embedded
foreign code, evolving source). Name specific 2026 libraries/versions and any named
methodologies. Flag where a hybrid (e.g., tree-sitter for layering + a precedence layer
for operators) outperforms any single method.

## Not in scope (do not introduce)

- This is not a request to design the DSL's semantics or interpreter — only the
  parsing/extraction method.
- Do not assume the markdown must be flattened or rewritten; the embedded-in-markdown
  shape is intrinsic and stays.
