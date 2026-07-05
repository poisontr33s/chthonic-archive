---
date: 2026-07-04
agent: Claude Code (Sonnet 5)
substrate: CLAUDEBASE
status: ruled
ruled-by: Fable 5 (main loop, direct dispatch 2026-07-04)
skill-invocation: none
source-session: CLAUDEBASE/last-CLAUDEBASE-session-important.md
addressed-to: sailing-master (Fable 5, max effort)
---

# CI Gate Architecture Session — Handoff to Fable

Paired trainstop bridge:
`CLAUDEBASE/harbor/2026-07-04-ci-gate-trainstop-bridge.md`.

The conductor ran out of context (~1%) mid-thread on a session that built a new
CI gate and then audited the whole gate architecture around it. Rather than let
the thread die uncaptured, this packet exists so the next session — or Fable
directly — can pick it up without re-deriving what was already found. The
conductor's ask is explicit: not just "continue the work," but Fable's *take* —
what this pass missed, and what interactivity should have looked like.

## What landed

`ci/checks/homepath-portability.ts` was built, registered in `ci/run.ts`'s
`CHECKS` array, and verified end-to-end: it catches a synthetic violation in
`--staged` mode (exit 1), passes clean once fixed, and its own SID/envelope pass
the repo's existing governance checks. It is `no_auto_fix: semantic` — the
correct replacement (home-relative vs. repo-relative path) needs the same kind of
tracing a prior `CHTHONIC_NVIDIA_STACK` fix needed, and that doesn't mechanize
safely.

## What the audit corrected

The conductor's starting assumption going in was "3 auto-fix checks, ~10
manual." Verified against live source, that was wrong:

| | Count |
|---|---:|
| Total registered checks (`ci/run.ts`) | 21 |
| `auto_fix` | 6 (shebang, python-headers, sid-envelope, uv-guard, blessing-gate, pathfinder) |
| `no_auto_fix` | 15 |

Two further corrections surfaced while confirming the SID/envelope standard
against every real file (not just the written reference docs):

- **GOLD, not ORANGE.** `.codex/skills/script-envelope/references/envelope-template.md`'s
  generic per-extension table says `.ts → Wedjat-Quipu Spectrum: ORANGE`. True for
  ordinary product/extension TypeScript. False for every `.ts` file under `ci/`
  and the CI-tooling files under `scripts/` — all of those use `GOLD`, with zero
  exceptions found across `ci/run.ts`, `sid-envelope.ts`, `python-headers.ts`,
  `uv-guard.ts`, `bun-audit.ts`, `character-schema.ts`, `fix_envelope.ts`. GOLD is
  the real convention for this directory; the written table is stale for this
  case.
- **`.meta/script-envelope.schema.json` is dormant, not live.** It's a JSON
  Schema for a "universal sidecar" idea referenced in archived mailbox docs
  (`codex/mailbox/archive/2026_02_10_meta_cleanup/TETRAGRAMMATON_PACKET.md`), but
  no executing code path validates against it and nothing generates a matching
  sidecar file. Aspirational scaffolding, not the enforced contract.

## What's open, unforced

Three threads were surfaced and deliberately left undecided — stated here as
options, not a recommendation, because the recommendation is what's being asked
of Fable below.

1. **72 pre-existing drift findings**, surfaced by the new gate but not
   auto-fixed: 28 stale `eldno` references (`extensions/chthonic-archive/src/acp/connection.ts`,
   `mas_mcp/mas_memory.json` ×14, several `scripts/*.ps1`/`.py` files) plus 44
   "smell" findings — hardcoded `eldno` that's correct today but fragile the
   moment this crosses machines again (`.vscode/mcp.json`, `.vscode/settings.json`,
   `scripts/mcp-*.ts`, others).
2. **4 orphaned check scripts** sitting in `ci/checks/` right now with valid
   SIDs and envelopes, but no entry in the `CHECKS` array — so none of them ever
   runs, via `bun run ci`, `--list`, or the pre-commit hook:
   `claudine-lora-smoke.ts`, `federation-contract-validate.ts`,
   `session-truncation-gate.ts`, `theme-icon-validate.ts`.
3. **`SCRIPTS_README.md` documentation-parity gap** — the repo's own convention
   is a hand-written subsection per check under `## Local CI Checks (ci/checks/)`
   (~line 407); the new gate doesn't have one yet. Zero functional effect; pure
   precedent-matching.

## What this session likely didn't catch

Named plainly, not hedged:

- No second-pass adversarial check on the registry recount itself (21 / 6 / 15)
  — it was counted once, carefully, but not cross-verified by a second method or
  a second pass.
- The GOLD-vs-ORANGE correction rests entirely on file-tally precedent (7 files,
  0 exceptions) — that's strong but not a written rule. It's possible this is
  local drift being mistaken for settled convention, not the other way around.
- Whether the 72 findings share a root cause (e.g. one bad rename script, one
  bad find-and-replace pass, one machine-specific config generator) was never
  asked. They were counted and categorized, not traced to origin.
- The session narrated straight through the 72-finding surface event to "want me
  to work through those now, or leave the gate as landed and handle cleanup
  separately?" — a question asked in text, not a structural pause. Whether that
  was the right moment for a harder stop is itself part of the ask below.

## Ask of Fable

Structured to slot into your own four-part output contract (Decision /
Rationale / Rejected alternatives / Next actions):

- **Decision needed:** which of the three open threads — drift cleanup, orphan
  check registration, doc parity — is the right next batch, and why. This is a
  cross-cutting judgment call (which drift is worth fixing now vs. deferred, and
  in what order) that fits the bar you're reserved for: being wrong here is
  expensive in wasted-cleanup-effort terms, not catastrophic, but the batching
  decision compounds across however many future sessions touch this gate layer.
- **Interactivity, explicitly:** should a session shaped like this one — long
  single-thread audit-then-build, discovering an escalating scope (a gate build
  that surfaces 72 pre-existing findings) — have paused for a conductor check-in
  *before* narrating past the discovery, rather than folding the pause into a
  single end-of-turn question? Put differently: is the gap in this session a
  *what-to-do-next* gap, or a *when-should-the-human-have-been-pulled-back-in*
  gap? The conductor named this as important for trajectory, not as an
  afterthought — treat it as a first-class part of the ruling, not a coda.

## Fable's Ruling

Dispatched 2026-07-04, direct to Fable 5 in the main loop — the conductor dropped
the packet and its plan as the dispatch; no sailing-master wrapper in between.
Nothing below is inherited from the transcript: every claim was re-verified this
session against live source, live git history, and live execution.

### Verification of the record

**Confirmed.** The registry recount holds exactly: 21 entries in `CHECKS`, 6 with
`auto_fix` (shebang, python-headers, sid-envelope, uv-guard, blessing-gate,
pathfinder), 15 manual. Cross-checked by set arithmetic rather than re-reading:
`ci/checks/` holds 24 scripts, 20 of them registered, the 21st registered check
(`scripts/shebang-guard.ts`) lives outside the directory, and the remainder is
exactly the four named orphans. The live gate still reports 28 stale / 44 smell —
identical to the session's counts. And the `no_auto_fix: semantic` classification
survives adversarial review: the finding surfaces (VS Code configs, a PowerShell
satellite-repo list, an MCP memory store, extension source) each want a different
replacement primitive, and a blind `eldno`→`eldno` swap would convert visible
wrongness into latent wrongness. The registry entry's reasoning is correct as
written.

**Corrected.** The packet's self-doubt section was right to worry — two of its
premises fail under a second pass:

1. **"GOLD, zero exceptions" is sample bias.** Full tally: `ci/` has 10 GOLD,
   4 AMETHYST (`dsl-conformance`, `lore-canon-paths`, `lore-canon-refs`,
   `organ-canon-citation`), and 11 files with no blessing line at all;
   `scripts/*.ts` splits 7 GOLD / 14 ORANGE. What survives: zero ORANGE anywhere
   in `ci/`, so the envelope-template's `.ts → ORANGE` row is genuinely wrong for
   CI tooling. What does not survive: "GOLD is the convention for this
   directory." GOLD is majority practice in a patchily-decorated directory;
   AMETHYST marks most — not all (`character-schema` and `canon-drift-snapshot`
   are GOLD) — of the lore/DSL membrane family. There is no settled convention
   here to *discover*. If one is wanted, write the rule into
   `envelope-template.md` and let the tally follow the law, not the reverse.
2. **The doc-parity thread rests on a false premise.** `SCRIPTS_README.md`'s
   Local CI Checks section documents two of the 21 registered checks (uv-guard,
   blessing-gate). A per-check subsection convention does not exist; writing 21+
   subsections would be make-work shadowing `--list`. The thread re-frames
   rather than dies: the two existing subsections are true and stay, and the
   section gains one line naming `bun run ci/run.ts --list` / `--autofix-list`
   as the registry's living documentation. If per-check parity is ever wanted
   for real, generate that block from the `CHECKS` array instead of
   hand-writing it — hand-maintained meta-doc is where this repo's false
   positives breed, and the durable cure for a lying doc is a doc that cannot
   lie.

**Traced.** The 72 findings have a shape, and it was recoverable in minutes:

- All 28 stale findings are one username — `eldno`, the prior laptop account —
  i.e. **one migration event** (~Feb 2026; the check's own header dates it via
  the Feb-18 cache snapshot), not 28 independent mistakes. Distribution: 13 sit
  in a single data artifact (`mas_mcp/mas_memory.json`), one more in
  `mas_mcp/data/inventory.json`, two in `scripts/.deprecated/setup_db.py`
  (tombstone lane), and the remaining ~12 spread across ten live files at 1–2
  each (`extensions/.../acp/connection.ts`, `mas_mcp/build_cupy.ps1`, assorted
  `scripts/*.ps1|.py`).
- The 44 smells are all `eldno` and cluster in the cross-repo wiring lane:
  `scripts/mcp_write_local.ps1` ×5 (the satellite-repo directory list — it
  writes the gitignored root `.mcp.json`, so these are its own literals, not a
  writer→output pair with `.vscode/mcp.json`), `.vscode/mcp.json` ×5,
  `scripts/relaunch-vscode-insiders.ps1` ×5, `.vscode/settings.json` ×4,
  `scripts/mcp-{game,sonic,sourcer}.ts` ×11 combined, `polyrepo-runner.ps1` ×4,
  one tracked **build artifact** (`extensions/chthonic-archive/dist/extension.js`
  ×3 — fix in extension source and rebuild, so the artifact regenerates true), and
  a tail of eight files at 1 each.

**Orphans resolved.** `git log -S` across the full history of `ci/run.ts`: none
of the four names ever appeared. They were never deregistered — the wiring never
happened. Three postdate the registry (built 2026-04-19) by weeks; they're
gate-ladder scripts from May 4–10 whose commit messages say "CI gate" but whose
registration was simply missed. The fourth, `theme-icon-validate.ts`, is
**untracked** — no git history at all; it must be committed before it can be
registered. Executed all four this session: **every one exits 0** (LoRA gates
admitted; federation contract valid; G9 admitted, 13 sessions / 23% avg ratio;
99/99 icons). Registration is pure coverage gain with zero new red.

**New, unflagged by either prior session:**

- The gate's exit semantics change the urgency picture. Default mode is
  advisory — always exit 0 — so **nothing is red today**. `--staged` mode is
  strict on any finding in a staged in-scope file, so each of the 72 findings is
  a **commit landmine** that detonates when its carrying file is next touched
  for any reason. Urgency therefore tracks churn probability, and the hottest
  carriers are exactly `.vscode/mcp.json`, `.vscode/settings.json`, and the
  `scripts/mcp-*.ts` lane.
- 11 of 25 `ci/` TypeScript files carry no Decorator's Blessing, and no gate
  checks for one (blessing-gate doesn't scan `ci/*.ts`). By this repo's own
  rule — gates auto-fix or die — an unenforced decoration standard is currently
  vibes. Enforce it or accept it as optional; either is fine, but it's currently
  neither.

### Decision

The three threads as framed are the wrong cut. Restructured, under one
invariant: nothing is deleted or written off — stale work is altered until it
tells the truth. Upcycle outranks exemption; exemption outranks deletion;
deletion doesn't run:

**Batch 1 — erase the migration ghost (the 28 stale).** The only wrong-today
category, and it's three moves, not 28 surgeries: (a) migrate the 14
data-artifact strings in place (`mas_memory.json`, `inventory.json`) — preserves
the records, updates the host path; spot-check two or three referenced paths
resolve afterward; (b) fix the two strings in `scripts/.deprecated/setup_db.py`
as well — no `EXEMPT_PARTS` carve-out for the tombstone lane: a learning record
carrying a false path is a corrupted record, the alteration costs thirty
seconds, and the gate stays maximally watchful over every lane it already
covers; (c) hand-fix the ~10 live files, 1–2 findings each,
home-relative vs repo-relative per the check's own remediation guidance. One
focused session.

**Batch 2 — wire the ready coverage (the 4 orphans).** Commit
`theme-icon-validate.ts` first. Add four registry entries with honest
classifications (the first three are `read_only_health`; theme-icon is a
validator, classify at write time). Measure `session-truncation-gate` runtime
before choosing fast vs slow — it chews 17k turns. Fold in the README pointer
line from the re-framed doc thread. Under an hour, independent of Batch 1.

**Batch 3 — defuse the hot smells; let the tail ratchet.** Deliberately fix the
high-churn cluster (~19 findings: both `.vscode` configs, `mcp_write_local.ps1`,
`relaunch-vscode-insiders.ps1`) — those files will be touched soon, and the
worst time to be forced into five semantic path decisions is mid-commit on
unrelated work. The ~25-finding tail is *not* a batch: the staged gate already
ratchets it, fix-on-touch, at the exact moment someone is in the file.
`dist/extension.js`: fix in extension source and rebuild — the tracked artifact
then regenerates true; untracking it would be write-off, not repair.

Order: 1 → 2 → 3-hot for a full session; 2 alone fits a short one. Not chosen
as batches at all: writing the GOLD rule (one line in `envelope-template.md`
whenever it's next touched — a law decision, not a work item) and blessing
coverage for `ci/` (conductor decides enforce-vs-shrug).

### Rejected alternatives

- **Orphans first as the default.** Defensible — they're cheapest and
  registering them makes future rot visible instead of silent. Edged out
  because the stale set is the only actual wrongness and the hot smells are
  flow-kill mines under the staged gate. If the next session is
  short, invert freely.
- **A dedicated 44-smell sweep.** Surgery-count work. The ratchet does the tail
  for free; only the hot cluster deserves deliberate effort.
- **Building an `eldno`→`eldno` auto-fixer.** The adversarial pass confirms the
  registry's reasoning: surfaces differ (data file vs configs vs source), and a
  mechanical swap converts a visible stale into a latent smell — strictly worse.
  `no_auto_fix: semantic` stands.

### On interactivity — the first-class answer

The gap was **not** a when-to-ask-permission gap. Under the conductor's own
settled contract — in-turn latitude real, anti-steering, infer-and-execute — a
mid-turn "may I continue?" pause at the 72-finding surface event would have been
ceremony, and the ruling here does not prescribe one.

The actual failure was economic. The session reached its decision point with
~1% context left, which means the question it asked — "work through these now,
or handle cleanup separately?" — was one it could no longer execute *either
answer to*. A question you can't act on isn't interactivity; it's a farewell
note. Two structural rules fall out:

1. **Checkpoint on budget, not on drama.** The trigger for stopping is not "a
   big discovery happened" but "discovered work now exceeds remaining execution
   budget." At that threshold, stop narrating and land the smallest
   decision-complete artifact — root cause, batch shape, cost per batch — while
   there is still fuel to write it well. The conductor's answer then costs one
   word and survives session death.
2. **Hand over a shape, not a count.** The session presented "72 findings" when
   five minutes of tracing would have shown "one migration event + one config
   lane + a tail." Errors-as-batch-method is already this repo's law for
   *fixing*; it applies equally to *presenting*. The conductor was pulled back
   in at the right moment — with the wrong artifact.

So: neither a what-next gap nor a when-to-interrupt gap, but a
**handoff-artifact-shape** gap. The proof is this packet itself: the moment a
successor session gave the thread a decision-complete shape, one cold dispatch
produced a ruling. The two-session recovery worked; an earlier-landed shape
would have made it one.

### Next actions

1. Conductor picks: Batch 1 next full session (default), or Batch 2 anytime a
   short window opens. Both fully specified above; no further scoping needed.
   No open data calls remain: `mas_memory.json` migrates in place (records
   preserved, host path updated), and `dist/extension.js` is repaired at its
   source.
2. When `envelope-template.md` is next touched: bless the GOLD-for-CI-tooling
   line (and AMETHYST-for-lore-membrane, if that split is intended) — turning
   tally into law, deliberately.

## Execution log (2026-07-04, same day — conductor's "commence")

Executed by Fable 5 main loop, ruling as dynamic reference. One move inverted
in flight, toward truth:

- **Batch 1** (`1e9a4a4f`): stale 28 → **0**. Inversion: `mas_memory.json`
  records were NOT migrated — the spot-check showed every referent gone on this
  machine (`output.stderr.log`, `.github/abbr-system.json`, `claudine-gpu/`);
  an `eldno`→`eldno` rewrite would have manufactured false records. The gate's
  own outputs-exempt principle was realized instead (`mas_mcp/mas_memory.json`
  + `mas_mcp/data/` → `EXEMPT_PARTS`); the records stand as history. Live
  files fixed as ruled (PSScriptRoot / USERPROFILE / pathlib / PATH-resolution
  primitives; `recover_ide_sessions.ps1` doc lines rephrased — its eldno params
  are its purpose). Bonus finds, both fixed in-flight: mas_mcp README+GPU_ENV
  setup docs carried 6 gate-blind eldno paths (`.md` is outside SCAN_EXTS);
  `validate_docs_content.ps1` had a fantasy `Metadata{}` block and had NEVER
  parsed — converted to comments, validator parses for the first time.
- **Batch 2** (`4035b780`): registry 21 → **25**; `theme-icon-validate.ts`
  first-ever commit; all four orphans verified green through the runner before
  registration (each ~0.1s → fast); README section re-anchored to `--list`.
- **Batch 3-hot** (`71af7f1b`, `a2993e29`): smells 44 → **26**. mcp.json
  satellite roots → `${env:USERPROFILE}` (substitution proven in-file);
  `mcp_write_local.ps1` `$fsRoots` → Join-Path; relaunch script →
  `GetFolderPath('Desktop')` + `$env:LOCALAPPDATA`; terminal-profile pins →
  `${env:LOCALAPPDATA}` (WindowsApps AppExecutionAlias pin preserved — bare
  `pwsh.exe` would have silently switched binaries to Program Files 7.5).
  `settings.json` committed via the sanctioned `--no-verify` escape over its
  two deliberate residuals, documented in `a2993e29`.
- **Capstone** (`60d4155a`): first full fast-suite run at 25 surfaced
  pre-existing envelope drift in `mcp_handshake_probe.py` (July-1 era,
  untracked); fixed via the gate's own registered auto-fix and committed.
  **Full suite: 22/22 fast checks green.**

Root-caused, deferred to one conductor-timed rebuild+redeploy event:
`dist/extension.js` ×3 — bun's CJS bundling inlines build-machine literals for
`__dirname`/`__filename` at `ankhReferenceView.ts:313`, `polyglotBroker.ts:244`,
`synapseBridge.ts:302`; the latter two are latent cross-machine bugs that work
here by directory coincidence. Sequence: fix the trio → rebuild →
`insiders:package` + install → flip `reactor.daemonBinaryPath` to relative
(resolution logic already landed in `71af7f1b`) → commit dist. The rebuilt
dist sits uncommitted in the working tree because the staged-strict gate
correctly refuses the machine-baked artifact — the gate earning its keep
against its own author's session.

Residual ledger (26 smells, all ride the staged-gate ratchet fix-on-touch):
`mcp-{game,sonic,sourcer}.ts` ×10, `polyrepo-runner.ps1` ×4, dist ×3 (above),
`settings.json` ×2 (deliberate: L66 substitution unverifiable, L253 awaiting
redeploy), `package.json` ×1, six singletons. Gate blind spot flagged, not
acted on: 27 `.md` files repo-wide carry `C:\Users` paths — conductor's call
whether the docs lane becomes a lens.

## Codex continuation (2026-07-04 — deferred rebuild/redeploy closed)

Executed by Codex against the deferred event above; two commits pushed:

- **Runtime + dist repair** (`b63b02c4`): removed all bundled
  `__dirname`/`__filename` build-machine literals from the three named source
  sites. ANKH now receives `context.extensionUri`; polyglot sidecar discovery
  receives `context.extensionPath`; synapse native loading anchors
  `createRequire` on the runtime extension package. Rebuilt
  `dist/extension.js`; direct scan found zero `C:\Users`, `eldno`, `eldno`,
  `__dirname`, or `__filename` hits. Updated the extension setting description
  to say absolute or workspace-relative path. Staged gate: **11/11 passed**.
- **Settings flip** (`dceafbe9`): `chthonic.reactor.daemonBinaryPath` now uses
  `extensions/chthonic-archive/native/target/debug/chthonic-daemon.exe`.
  Committed with the sanctioned `--no-verify` lane because staging
  `.vscode/settings.json` still detonates the deliberate L66 residual only;
  verifier output showed no finding for the edited daemon path.

Redeploy completed: `bun run --cwd extensions/chthonic-archive insiders:package`
produced `chthonic-archive-insiders.vsix`, and
`code-insiders --install-extension ... --force` installed it successfully. The
installer emitted only VS Code's own `url.parse()` deprecation warning.

Verification after closure:

- `bun run --cwd extensions/chthonic-archive compile` — pass.
- `bun run ci -- --check homepath-portability` — stale **0**, smell **22**.
- `bun run ci` — **22/22 checks passed**.

Residual ledger is now 22 smells: the prior dist ×3 and settings L253 entries
are gone. Remaining known hot clusters stay on the staged-gate ratchet:
`mcp-{game,sonic,sourcer}.ts` ×10, `polyrepo-runner.ps1` ×4,
`settings.json` L66, `package.json` ×1, and the documented singleton tail.

