# DSL Iteration Toolkit — Lifecycle Design

> Status: design doc. Phases 0–1 implemented. Phases 2–4 designed, not built.
> Build trigger for each future phase is documented in §Decision-points.
> Authored 2026-05-27 per user direction ("design doc first, build later;
> use what we have across iterations to validate; compounds better than
> separating them").

## Vision

A unified toolchain for the entire PEG-DSL development lifecycle. The same
config (`dsl-iter.toml`), the same catalog (`patterns.json`), and the same
ledger (`manifest/<project>_iteration_history.ndjson`) flow through every
phase, so methodology compounds rather than restarting at each handoff.

```
NL ──┐
     │ translate (Phase 4)
     ▼
   DSL ──┐
         │ check (Phase 1) — catalog + coverage + ledger
         ▼
   verified-DSL ──┐
                  │ compile (Phase 2) — codegen optimized parser
                  ▼
            compiled-parser ──┐
                              │ interpret (Phase 3) — AST → effects
                              ▼
                          effects (writes to manifest, dispatches, etc.)
```

Each arrow is a phase. Each phase consumes the previous output, validates
against the catalog, and appends to the ledger. The whole chain is observable,
rewindable, and regression-detectable.

## Phase 0 — Grammar extraction

**Status**: not a toolkit phase — manual/semi-manual. Authored as the initial
`.peg` file from observation of the corpus's substrate constructs.

**Discipline**: observation-not-invention. The grammar formalizes existing
notation, not new syntax.

## Phase 1 — Iteration (current scope)

**Status**: built and verified on chthonic. 12/15 patterns + 77.47% paren coverage at baseline.

**Subcommands**:
- `dsl-iter check` — runs catalog test + coverage per surface + ledger append
- `dsl-iter history [--last N]` — recent ledger rows
- `dsl-iter init <project>` — scaffold config
- `dsl-iter surfaces` — list known coverage surfaces

**Loop**: edit grammar → `check` → on regression `git revert HEAD` → repeat.

**Compounds**:
- Catalog grows: new patterns added per iteration (manually or via auto-extract from coverage mismatches)
- Ledger compounds: time-series of state-per-grammar-hash
- Coverage surfaces extend: paren now; bold/backtick/fenced/header pending

## Phase 2 — Compile

**Status**: designed, not built. Build trigger: chthonic graduates to production
parsing (where pest_vm's interpretation cost matters), OR a second DSL project
starts and needs scaffolding from zero.

**Subcommands**:
```
dsl-iter compile [--single-file | --scaffold full-crate] [--output PATH] [--build]
```

**Modes**:
- `--single-file`: emits one `.rs` source with `#[grammar = "..."]` pest_derive
  attribute + Parser struct + minimal harness. Drop into any existing Rust
  project; instant compiled parser.
- `--scaffold full-crate` (default): emits a complete Cargo crate (Cargo.toml +
  build.rs + src/main.rs + src/lib.rs + harness binaries). Equivalent to
  `tools/dsl-smoke/` but auto-generated from the config.
- `--build`: also runs `cargo build --release` on the output and reports
  the binary path.

**Inputs**:
- `grammar_path` from `dsl-iter.toml`
- output directory (default: `tools/<project>-parser/` or `./<project>-parser/`)

**Outputs**:
- generated Rust source(s)
- optionally: compiled binary (when `--build` flag set)

**Verification (cross-phase invariant)**:
- Generated parser MUST produce identical parse trees vs `pest_vm` interpreter.
- Catalog test: every pattern's example must yield same `expected_top_rule` +
  `expected_inner_rules` in both modes.
- Coverage test: per-surface `matched_correctly` count must be identical.
- Implementation: a new `dsl-iter verify-compile` subcommand cross-checks the
  two modes against the catalog + a sample of the corpus.

**Why this matters**:
- Production deployment: compiled parser is 10-100× faster than pest_vm.
- Bootstrap: new DSL projects get a working compiled parser in seconds
  (`init` → `compile --scaffold` → run).
- Cross-validation: divergence between interpreter and compiled output is
  a real bug (in either pest_derive or pest_vm); having both makes such bugs
  visible.

## Phase 3 — Interpret

**Status**: designed, not built. Build trigger: catalyst content needs to be
EXECUTED, not just parsed — e.g., the catalyst's substrate constructs need to
manipulate data, dispatch to agents, or update state.

**Subcommands**:
```
dsl-iter interpret [--input FILE | --stdin] [--effects-allowed] [--dry-run]
```

**Vision (per [reference-dsl-substrate-methodology])**:
- AST → operations on data (a small tree-walking evaluator)
- Catalyst constructs become operations:
  - **Compositions** (`A → B × C`) — function chains; operators are typed combinators
  - **Invocations** (`$verb${args}`) — function calls into the project's runtime registry
  - **References** (`§X.Y`, `L<num>`) — lookups into resolved data
  - **Bold-paren ids** (`**(`X`)**`) — typed identifier resolution against the project's
    entity registry (e.g., chthonic's character JSONs)
- The interpreter walks the parse tree and dispatches each rule to a handler.

**Inputs**:
- AST from `compile` or `pest_vm` parse
- Project's data files (e.g., chthonic's `ankh_seeds.yaml`, character JSONs,
  protocols) — declared in `dsl-iter.toml`'s new `data_sources` field

**Outputs**:
- evaluated results per construct
- side-effects (when `--effects-allowed`): file writes, agent dispatches,
  manifest updates. Default is `--dry-run`: report what WOULD happen.

**Catalog hookup**:
- Each pattern in `patterns.json` can declare `runtime_handler: "fn_name"` —
  the interpreter resolves the name to a registered handler.
- Patterns without handlers are parsed but not evaluated (Phase 0/1 semantics
  preserved).

**Verification**:
- Pure-function patterns: evaluating example produces deterministic output;
  ledger captures the output hash; future runs verify the same output (regression
  detection at the runtime level).
- Effectful patterns: dry-run output captured; effects gated.

**Open questions**:
- Tree-walking evaluator (simple, slow) vs bytecode compilation (faster, more complex)?
  → Tree-walking for v1; revisit if perf matters.
- How does the interpreter handle the catalyst's prose? Currently parsed as
  `prose_parens` or `prose_fragment` — at interpret time, these are no-ops
  (preserved as text, not executed).
- Cross-rule data: how does `op_project` know the right-hand operand's type?
  → Phase 3 introduces a typed-operand discipline; catalog gets a `type` field
  per pattern.

## Phase 4 — Translate

**Status**: designed, not built. Build trigger: NL → DSL bridge becomes
load-bearing — e.g., user wants to author corpus updates in natural language
and have them automatically encoded as substrate constructs.

**Subcommands**:
```
dsl-iter translate <natural-language-input>
              [--model openai-gpt-x | local-llama-x | rule-based]
              [--confidence-threshold 0.7]
              [--bias-audit-log PATH]
```

**Vision (per the bias-quarantined boundary directive)**:
- This is the ONLY phase that uses a pre-trained model (LLM or equivalent).
- The model's bias is named, inspectable, and confined to this layer.
- All other phases operate on substrate (post-translation), bias-free.

**Inputs**:
- natural-language input
- catalog (so translation has KNOWN target patterns to aim at)
- corpus (so translation can ground claims in cited content)

**Outputs**:
- generated DSL construct(s)
- per-construct confidence score
- audit trail: which patterns the model considered, which was selected, why
  (logged to `--bias-audit-log`)

**Discipline**:
- Output is automatically tested against the catalog (does it match an existing
  `working` pattern?) — if yes, accept; if no, flag for human review.
- The catalog ACTS AS the grammar's "known good" surface that translation
  outputs must conform to.
- Bias audit log persists EVERY translation decision so drift can be analyzed.

**Open questions**:
- Which model? OpenAI API (capable, bias-known), local Llama (private, bias-different),
  rule-based (no bias but limited)?
- How is the bias-audit-log analyzed? Manual review per session, OR an automated
  drift detector that flags when the model's pattern selection shifts unexpectedly?
- How does the user override? `--accept` flag for manually-approved outputs
  that don't match an existing pattern (which then becomes a new catalog entry).

## Loop C — Step-level rewindability (checkpoint mechanism)

**Status**: built 2026-05-27, alongside the three-prospects architectural articulation.

Loop C complements the two rewindability resolutions that already exist:

| Resolution | Mechanism | Scope | Use-case |
|---|---|---|---|
| Commit-level | `git revert HEAD` | cross-session, durable | undoing a whole iteration that's been committed |
| Run-level | Ledger regression detection (`dsl-iter check` exit 1) | between runs of the same phase | detecting that the LAST run regressed against the prior one |
| **Step-level** | **Checkpoint snapshot** (Loop C) | individual mutation | **undoing one specific mutation without touching git or unrelated state** |

Three resolutions stack so the conductor can move back at the granularity the situation warrants.

### Mechanism

Each stateful operation (currently: `dsl-iter check`; future: `pattern add`,
`compile --build`, `interpret --effects-allowed`) snapshots the files it's
about to mutate **before** the mutation runs. The snapshot is atomic (write
to a fresh per-timestamp directory; never overwrite mid-write).

State files snapshotted per check:
- `manifest/<project>_iteration_history.ndjson` (the ledger)
- `manifest/<project>_coverage_<surface>_audit.json` per configured surface

When future phases land, they extend the snapshot list:
- Phase 2 (compile): the generated parser source(s), the build cache
- Phase 3 (interpret): the runtime state files declared in dsl-iter.toml's `data_sources`
- Phase 4 (translate): the bias audit log

Each snapshot is described by a `manifest.json` carrying:
- `id` (ISO-timestamp)
- `reason` (`pre-check`, `pre-pattern-add`, etc.)
- `files[]` — list of `{original_path, snapshot_path, was_missing, size_bytes}`
- `git_head`, `grammar_hash`, `project_name`

### Storage

Checkpoints live at `<manifest_dir>/.checkpoints/<id>/`. The `.checkpoints/`
parent stays gitignored by the catch-all `*` rule — checkpoints are runtime
state, not committed artifacts. (git tracks the COMMITTED state; Loop C tracks
the WORKING-TREE state between commits.)

### Retention

Default: keep last 20 checkpoints, prune older. Configurable via dsl-iter.toml's
future `checkpoint_retention` field (currently hardcoded to 20).

### Subcommands

```
dsl-iter checkpoint-list                   # list available checkpoints (newest first)
dsl-iter checkpoint-show <id>              # show one checkpoint's manifest
dsl-iter revert [--to <id> | --last] [-y]  # restore state to checkpoint
```

Without `--to`, `revert` defaults to the most recent checkpoint. Without `-y`,
revert prompts for confirmation (showing what files will be restored or deleted).

### Was-missing semantics

If a file didn't exist at checkpoint time but exists now (e.g., a new
coverage manifest created by the current run), revert will DELETE it. This
preserves the "exact state before the mutation" invariant. The manifest's
`was_missing: true` flag distinguishes "file existed empty" from "file didn't
exist at all" — both restore correctly.

### Verification

After this commit, the chthonic instance produced a 2.4MB checkpoint snapshot
of the coverage manifest + 534-byte snapshot of the ledger, both stored
atomically under `manifest/.checkpoints/<timestamp>/`. The CLI's
`checkpoint-list` reports them; `revert` restores them; round-trip-verified.

### Composition with Loops A and B

The three loops compose by operating at different scopes:

- **Loop A** edits the grammar (`.chthonic/grammar/chthonic.peg`) — git tracks this.
- **Loop B** runs the toolkit (`dsl-iter check`) — modifies state files; Loop C snapshots these.
- **Loop C** preserves and restores those snapshots.

A typical workflow:
1. Grammar edit (Loop A).
2. `dsl-iter check` — Loop B runs; Loop C snapshots state pre-check; ledger appended; coverage manifest written.
3. If results unexpected: `dsl-iter revert --to <previous-checkpoint>` restores prior state.
4. Try a different grammar edit; re-check.

This means individual experiments are cheap — bad ideas are reverted without
polluting the ledger or coverage history. The committed state stays clean;
only confirmed-good iterations get committed (Loop A → git).

## Cross-phase invariants

Regardless of which phase is running, the toolkit enforces:

1. **Same config** — `dsl-iter.toml` defines paths, surfaces, project name.
2. **Same catalog** — `patterns.json` is the shared contract; every phase tests
   against it.
3. **Same ledger** — `manifest/<project>_iteration_history.ndjson` records each
   phase's state per grammar-hash.
4. **Same regression detection** — `parse_rate_drop`, `shadow_rise`,
   `coverage_drop`, `plateau` apply across all phases.
5. **Same rewindability** — every phase's output is reproducible from a past
   commit; past grammar states are re-checkable via `git checkout` + re-run.
6. **Same `--dry-run`** — every phase that writes state has a dry-run mode.

## Decision points

| Phase | Status | Build trigger |
|---|---|---|
| 0 (grammar extraction) | done | n/a — manual |
| 1 (iterate: check / history / coverage) | done | n/a — current scope |
| 2 (compile) | designed — **NO-GO, 2026-07-06** (revisit when the build trigger actually fires) | chthonic graduates to production parsing, OR 2nd DSL project starts and needs scaffold |
| 3 (interpret) | designed | catalyst content needs to be EXECUTED, not just parsed; runtime handlers wanted |
| 4 (translate) | designed | NL → DSL bridge becomes load-bearing; manual authoring is the bottleneck |

## Phase 2 maturation checklist — answered 2026-07-06

Full-SSOT-smoke session (2026-07-06) ran ~10 grammar-affecting iterations (took
the 10,283-line SSOT.md from failing at line 230 to a full clean parse) plus
added the 3 missing coverage surfaces and corrected 1 stale catalog entry —
enough real Phase 1 usage to answer the 5 questions above with actual data
instead of guesses (`manifest/chthonic_iteration_history.ndjson`, 18 rows):

1. **Does the catalog grow naturally as we iterate?** Mixed evidence. Over the
   project's life: yes (15→20 patterns, mostly pre-session). Within this
   session specifically: no new patterns were added — the one catalog change
   was correcting pattern #20's stale `status: failing` to `working` (the
   grammar had already fixed it on 2026-06-05, the catalog just never synced).
   Don't over-read "catalog growth" from a session that happened to only need
   corrections, not additions.
2. **Does coverage move in the right direction?** Yes for `paren`, cleanly:
   77.47% (pre-session baseline) → 98.00% after 3 early fixes → flat at
   exactly 98.00% for the remaining ~15 checks (later fixes targeted
   emphasis/backtick/dollar/hash constructs, not parens — flat is the correct
   result, not stagnation). `bold`/`backtick`/`fenced` have exactly one data
   point each (97.81% / 99.68% / 100%) — a baseline, not a trend. Don't let a
   good first number read as proof the "coverage compounds" hypothesis holds
   for the new surfaces; only `paren`'s multi-iteration history actually
   answers this question.
3. **Are the regression classes catching real issues?** `shadow_rise` — yes,
   directly exercised: 4 real shadow failures found and fixed this session,
   `audit_shadow_total` tracked 0 throughout afterward. `parse_rate_drop` /
   `coverage_drop` / `plateau` — never fired this session because no fix ever
   regressed anything (a discipline outcome, not a detector test). Their
   design is sound and documented (LIFECYCLE.md's own iter-5→6 story), but
   that's inherited trust, not fresh verification under this session's hands.
4. **Is per-surface coverage cost-effective?** Yes on implementation cost
   (all 3 new surfaces built and wired in well under the ~30sec/surface
   estimate once the `Surface` trait scaffolding existed). Mixed on
   bug-discovery value: `paren`'s original 77%→98% arc drove real grammar
   fixes; `bold`/`backtick`/`fenced` came in high (97.81%/99.68%/100%) and
   confirmed robustness rather than surfacing new problems. A clean bill of
   health is real information, just a different kind than paren's original
   run produced.
5. **Does the ledger feel useful for navigation?** Yes, clearly — this
   session's entire fix sequence (grammar-hash changes, pattern-count
   changes, coverage numbers appearing one surface at a time) was
   reconstructable from the ledger alone, cross-checked against git history.

**Verdict: NO-GO on Phase 2 (compile), not because Phase 1 is immature, but
because Phase 2's own documented build trigger hasn't fired.** Neither
condition in the trigger column is true: chthonic isn't in production
parsing (no live system consumes the grammar's output yet — this is still an
iteration/validation tool), and no second DSL project has started needing a
scaffold. Building the compile phase now would be capability added because
it's possible, not because anything needs it — the same discipline this
grammar's own philosophy states ("observation, not invention") applied to
tooling scope rather than grammar rules. Revisit when either trigger actually
occurs.

## Until then — validation discipline (Phase 1 maturation)

Don't build Phase 2+ until you've used Phase 1 enough to know:

1. Does the catalog grow naturally as we iterate? (Each fix should reveal patterns
   we hadn't catalogued yet; the catalog should expand monotonically.)
2. Does coverage move in the right direction? (Each grammar fix should raise
   `matched_correctly` per surface; regressions caught by ledger.)
3. Are the regression classes right? (parse_rate_drop, shadow_rise, plateau —
   are they catching real issues? Adding `coverage_drop` was already a needed
   refinement.)
4. Is the per-surface coverage cost-effective? (paren took ~30 seconds to write;
   bold/backtick/etc would be similar. Worth it if they each surface unique gaps.)
5. Does the ledger feel useful for navigation? (Can you read the last few rows
   and understand where you are? If not, the schema needs refinement.)

After 5-10 iterations on the real chthonic grammar with the toolkit, the
answers will be clear. THEN decide on Phase 2.

## Architectural risks (think before phase-2 build)

- **pest_vm vs pest_derive parse-tree divergence**: pest_vm should produce
  identical trees to pest_derive, but version skew is possible. Cross-validation
  in Phase 2 verifies this.
- **Catalog schema migration**: adding fields per phase (runtime_handler for
  Phase 3, confidence for Phase 4) needs a versioned schema; v1 catalog must
  still parse cleanly under v2 toolkit.
- **Effects discipline**: Phase 3 introduces side effects. The dry-run-by-default
  invariant must hold absolutely — effects only when `--effects-allowed` is
  explicit. Default-safe.
- **Bias confinement**: Phase 4's model contact must be SEPARATE from Phase 1-3
  logic. No model output flows into Phase 1-3 unaudited.

## Open meta-question

When does the toolkit itself need versioning? Today it's `0.1.0`. As phases
2-4 land, semver matters — a `dsl-iter.toml` written for v0.1 should keep
working under v0.2. The catalog schema should likewise version (currently
implicit `version: 1`).

This isn't a now-problem but a future-problem the design should NOT preclude.
