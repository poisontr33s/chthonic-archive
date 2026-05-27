# dsl-iteration-toolkit

Generalized methodology layer for PEG-based DSL development. Library + CLI.

## What this is

A reusable toolkit that encodes the iteration discipline we developed against
the chthonic-archive catalyst grammar — extracted into a project-agnostic
form so any future PEG DSL development benefits from the same methodology.

**Specialized + generalized split:**

- `tools/dsl-smoke/` — chthonic-specific binaries (compile-time grammar binding via pest_derive). Stay as the reference instance.
- `tools/dsl-iteration-toolkit/` (this crate) — generalized library + CLI (runtime grammar loading via pest_vm). Works on any DSL project.

## The principle

The tool ENCODES the project's accumulated decisions. Every "this pattern is
classified as X" becomes catalog data; every "we decided to handle this gap
with rule Y" becomes a catalog entry; every iteration's diff sharpens the
recommendations for the next. The catalog grows; the methodology refines;
the measurement surface widens.

**Three layers that compound:**

1. **Sparse, curated** — `patterns.json` (hand-named patterns with expected outcomes)
2. **Dense, exhaustive** — coverage pass per surface (paren / bold / backtick / fenced / header)
3. **Time-series** — ledger of iteration results with regression detection

Together they catch what's done (correctly classified) AND what isn't (still mismatched).

## CLI

```powershell
# Initialize a config in current directory
dsl-iter init my-project

# Edit dsl-iter.toml to point at your grammar + corpus + catalog

# Run a check (catalog test + coverage + ledger append)
dsl-iter --config dsl-iter.toml check

# Show recent ledger entries
dsl-iter --config dsl-iter.toml history --last 5

# List known coverage surfaces
dsl-iter surfaces
```

## Config schema (dsl-iter.toml)

```toml
project_name = "my-dsl"
grammar_path = "grammar.pest"           # path to pest grammar file
corpus_path  = "corpus.md"              # path to the document parsed by the grammar
catalog_path = "patterns.json"          # path to the pattern catalog
manifest_dir = "manifest"               # output directory for ledger + coverage reports
coverage_surfaces = ["paren"]           # which surfaces to scan
```

Paths are resolved relative to the config file's directory.

## Library API

```rust
use dsl_iteration_toolkit::*;

// Load grammar at runtime
let grammar = Grammar::load(".chthonic/grammar/chthonic.peg")?;

// Test pattern catalog
let catalog = Catalog::load(".chthonic/grammar/patterns.json")?;
let results = catalog.test_all(|p| {
    let summary = grammar.parse_at("program", &p.example).unwrap();
    (summary.ok, summary.inner_rules)
});

// Run coverage on the paren surface
let surface = ParenSurface::default();
let corpus = std::fs::read_to_string(".chthonic/SSOT.md")?;
let report = run_coverage(&surface, &corpus, "SSOT.md", &grammar)?;
println!("Paren coverage: {:.2}%", report.coverage_pct);

// Or use the orchestrator
let checker = IterationChecker::from_config_path(".chthonic/dsl-iter.toml")?;
let report = checker.check()?;
```

## Pattern catalog schema

See `.chthonic/grammar/patterns.json` for the chthonic reference instance.
Each entry:

```json
{
  "name": "snake_case_unique_id",
  "description": "What this pattern represents.",
  "example": "the actual catalyst text",
  "expected_top_rule": "bold_parened_id",
  "expected_inner_rules": ["multi_alias"],
  "status": "working | failing | deferred",
  "since_iter": 1,
  "source_line_ssot": 73,
  "category": "substrate-wrapper"
}
```

## Coverage surfaces (extensible)

Each surface defines: how to enumerate occurrences from corpus, how to
classify each occurrence, what grammar rule SHOULD match each category.

Current:
- **paren** — non-nested `(...)` constructs

Pending (PRs welcome):
- **bold** — `**...**` markdown emphasis
- **backtick** — `` `...` `` inline code
- **fenced** — ` ```lang ... ``` ` code blocks
- **header** — `## ...` markdown headings

## Iteration discipline (recommended)

For any grammar change:

1. **Before**: `dsl-iter check` (baseline)
2. **Edit** grammar (one focused change at a time)
3. **After**: `dsl-iter check` (delta)
4. If regression flagged: **`git revert HEAD`** is the default move
5. If plateau (same fail position 2+ runs): step back, rethink

The ledger is the audit trail. Past grammar states are re-checkable by
checking out the grammar from any commit and running the toolkit — pest_vm
loads it at runtime, no recompile needed.

## Reference: the chthonic instance

See `.chthonic/dsl-iter.toml` for the chthonic-archive catalyst configuration:

```toml
project_name = "chthonic"
grammar_path = "grammar/chthonic.peg"
corpus_path  = "SSOT.md"
catalog_path = "grammar/patterns.json"
manifest_dir = "../manifest"
coverage_surfaces = ["paren"]
```

Baseline at first check (2026-05-27): 12/15 patterns + 77.47% paren coverage.
The mismatch breakdown is the data telling us where the next highest-leverage
grammar fix is.
