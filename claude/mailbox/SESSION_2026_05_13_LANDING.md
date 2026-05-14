# Session landing — 2026-05-13

Short. Designed to be re-read in three weeks and still make sense.
Open this first when you come back to this thread.

## What happened today

A drift was caught and dissolved. Codex's pathfinder rewrite (commit
`27a21d7f`, +736 lines) had landed during a prior session with a
broken contract — useful capability bundled with over-strict gating
that blocked your commits. You came back, named the problem, and
switched lanes to Claude Code. From there we worked the redux.

## What's live now (with commit SHAs)

> **2026-05-13 late-session note:** Codex performed a `git filter-repo`
> later in the day to strip three 160MB `.safetensors` files from
> history (they were blocking the push to GitHub). The filter rewrote
> every commit SHA in the chain. The SHAs listed below are the
> ORIGINAL ones; they exist only in local reflog and backup refs now.
> The current `main` chain has different SHAs but the same content.
> Full translation table at
> [CODEX_RESPONSE_SHA_RECONCILIATION_2026_05_13.md](CODEX_RESPONSE_SHA_RECONCILIATION_2026_05_13.md).
> Use `git show <new-sha>` for current chain inspection. `git show <old-sha>`
> still works against the local backup refs until they're pruned.

The work is real and committed; the table below lets you trace what landed when.

| Commit | What landed |
|---|---|
| `04770546` | scripts/session_normalize.py — raw paste → vampire-compatible JSONL |
| `ad5a855d` | `bun run workspace:open` — opens the polyrepo dropdown |
| `ca376fac` | scripts/link_audit_author.py — author-filtered + satellite orchestrator |
| `6365687a` | wrapper batches paths to dodge Windows cmdline cap |
| `b5b7000d` | apply link-rot auto-fixes across 28 markdown files |
| `cbb41515` | AMBIG severity = warning, not error (unblocks commits) |
| `44e6ad03` | git-rot index v2 + scope contract w/ stakes + 3 tombstones |
| `1ab5dfa2` | this landing page + redux addendum (postmortem of hour-to-4s) |
| `d905b8a4` | code-fence skip + 2 more tombstones + git_truth enrichment |
| `b7ff32c9` | ADR_RECOVERED.md tombstones (deletion-cluster fix, -20 refs) |
| `61e865e5` | SSOTIFICATION depth-bug resolved + 2 stub mailbox docs |
| `484f6a49` | suppress ROT-003 false positives by default (161 → 38 entries) |
| `5fa8b97a` | Gitological Ladder taxonomy — L1..L4 depth model |

## How to use what we built

### Want fresh diagnosis of repo rot
```
uv run scripts/git_rot_index.py
# writes manifest/git_rot_index.json + manifest/git_rot_index.md (digest)
# 4.4s end-to-end on this repo
```

### Want to hand off work to Codex / Gemini / another Claude
Copy `claude/mailbox/_contracts/TEMPLATE_scope_contract.md`, fill it in,
send it. Receiving agent must echo the contract back before starting.
No echo, no execution. This is the gate that didn't exist before.

### Want to mark a file as graveyard (acknowledged-dead)
Add to the file's YAML frontmatter:
```yaml
---
lifecycle: tombstone
tombstone_marked_at: YYYY-MM-DD
tombstone_reason: |
  Why it's dead. One paragraph.
---
```
The rot index and the CI pathfinder both honor this. File stays in
the repo; it stops counting against the living signal.

### Want the chronology of today's work
Read `claude/mailbox/REDUX_2026_05_13_PATHFINDER_SEQUENCE.md`.

## What we learned (preserved as durable memory)

- Stakes-language, not rule-language. Agents need consequence to
  internalize architecture. "Be helpful" doesn't land; "or this becomes
  a tombstone" does. Saved at `memory/feedback_stakes_not_rules.md`.
- Declare next, don't ask. "If you want me to..." shifts decision
  burden onto someone who trusts initiative. Saved at
  `memory/feedback_declare_next.md`.
- No more layers in chthonic-archive — prefer navigating existing
  tools to building new. The rot index is the exception: it
  consolidates orientation across multiple existing signals.
- Smoke-test before declaring done. The hour-long indexer hang
  (2026-05-13) happened because I introduced a clever balanced-paren
  regex without running it over the actual corpus. The fix was a
  one-line revert. Real-data test on every new tool before sign-off.

## Session arc — how rot collapsed

The data-led lane the user invoked carried itself, each rung surfacing
the next:

```
[2,151 baseline]   raw session-start rot count
   ↓
[ 463 ]  3 hotspot files marked lifecycle: tombstone
   ↓
[ 196 ]  code-fence skip + 2 more tombstones + git_truth enrichment
   ↓
[ 176 ]  ADR_RECOVERED.md deletion-cluster collapsed via tombstones
   ↓
[ 168 ]  SSOTIFICATION depth-bug: 8 of 15 links fixed
   ↓
[ 161 ]  SSOTIFICATION remaining 7: stub-created the 2 phantom targets
   ↓
[  38 ]  ROT-003 false positives suppressed by default
```

~98% reduction across one session. The remaining 38 are real work-list,
not noise: 12 ROT-001 typos/hallucinations, 16 ROT-002 basename-ambig
broken refs, 10 ROT-008 placeholder literals in skill templates.

## The Gitological Ladder (taxonomy you named)

The ROT codes aren't flat — they describe symptoms at different depths.
The 5fa8b97a commit made this explicit in the schema:

```
L4 LINEAGE   structural / causational (CLUSTER-001/002, ROOT-001)
L3 ANCHOR    positional / semantic (ROT-006, ROT-007)  [detectors pending]
L2 VIRTUAL   namespace / collision (ROT-003, ROT-004)
L1 SURFACE   raw symptoms (ROT-001/002/005/008)    ← where indexer lives now
```

Tombstone lifecycle is orthogonal — cuts across all levels.

## The late-session slugger and its resolution (2026-05-13 PM)

After the morning lane completed, the SCM Graph in VS Code started
running ~3-second `git diff` operations on every panel refresh. Cause:
64 unpushed local commits containing 655MB of binary adapter files
(three 160MB `.safetensors`, two 81MB `optimizer.pt`) committed in
`b02e8243` from 2026-05-11. Every panel refresh recomputed similarity
across all those binaries.

Discovery sequence: user thought they had been auto-pushing to
origin/main all along, hit "fix it" — push got rejected by GitHub's
100MB hard limit. The 64 outgoing commits revealed the actual HODL
state had been operating silently. Two-step fix attempted first
(copy adapters to satellite + gitignore defensive rules) which
addressed prevention but not the existing block. User raised the
"size-based gitignore" question stake-aware to widen prevention.

Codex took the bolder path: created three backup refs first
(`backup/main-before-lfs-migrate-...`, `backup/main-pre-filter-with-gitignore-...`,
`backup/main-filterrepo-overwide-...`), then ran `git filter-repo` to
strip the large files from history, then verified content preservation
via four `git diff --exit-code` checks against the original commit
SHAs. Pushed cleanly. Wrote a handoff note documenting the SHA
translation.

What I (Claude) got right: refusing to run the history rewrite myself
without explicit consent when backup refs didn't yet exist. What I got
wrong: when system-reminder snippets later showed apparently-reverted
content, I raised an alarm based on misread stale snapshots instead of
checking actual disk state first. Codex's all-clear was correct; my
panic was unfounded. Lesson: verify against disk, not against
snapshot streams, when the situation is in flux.

Lesson encoded as durable feedback memory: history-rewrite operations
are only safe when backup refs exist first. With backup refs, bold
action is appropriate; without them, defer until they exist.

## What's burning right now (open threads)

- 38 real entries in the default rot index, all L1 SURFACE. Per-file
  triage when ready. Not urgent.
- L3 detectors (ROT-006 anchor miss, ROT-007 line anchor stale) — slots
  exist in the taxonomy, code doesn't yet.
- L4 detector (ROOT-001 mass-rename ancestry) — slot exists, code
  doesn't yet. Would trace broken-link clusters back to the single
  historical commit that broke them (like `dc42cac8` did with the docs/
  consolidation).
- Two stubs at `claude/mailbox/BOUNTY_00000031_STEWARD_AUDIT.md` and
  `claude/mailbox/FORGE_PIPELINE_DEV_PLAN.md` exist as placeholders.
  Their planned content is still TBD.
- Iron Maiden / Pentea work was alive in WIP at session start; the
  in-flight changes had already landed in `27a21d7f` and `ad2e28a2`.
  No remaining WIP from that lane.
- Claudine adapter POC (655MB of model weights from `b02e8243`) now
  lives in the `git-dump-lfs-holder-we-it-takes` satellite at
  `adapters/claudine-v1/`. Not yet committed/pushed to that satellite
  — when you're ready to commit there, the satellite's
  `.gitattributes` needs `*.safetensors` and `*.pt` filter=lfs lines
  added first so git-lfs catches the big files.
- Repo is fully synced with origin/main as of late session. The HODL
  state ended cleanly: rewrite happened with backup refs as safety
  net, content preserved end-to-end, pushed.

## What I'm carrying forward

Next operational move when you come back: build the L3 and L4 detectors
the ladder has slots for. The L1 indexer is mature; the next ladder
rungs are the natural extensions.

You don't need to remember any of this to re-enter. Just open this file.

The adventure continues.

---

# Continuation — 2026-05-14 (same session, next day)

Written as proactive synthesis before auto-compact fires. Honest 90/10
postmortem so the next session inherits the lessons, not the noise.

## What actually worked (the durable 10%)

- L3 ANCHOR detectors landed in `git_rot_index.py` (ROT-006 anchor_missing,
  ROT-007 line_anchor_stale). Surfaced 28 new entries we couldn't see before
  — mostly stale line anchors into `.github/copilot-instructions.md` which
  shrank from ~6000 lines to 83. GFM duplicate-suffix handling + unified
  `target_structure_cache` shipped as correctness banking.
- L4 LINEAGE detector (ROOT-001 mass-rename ancestry) landed in
  `145254a9`. Single sentinel-stream parser, cluster-grouping driver
  groups L1 ROT-001 by parent dir, single `git log --diff-filter=D`
  subprocess per cluster. Completes the Gitological Ladder L1..L4.
- Dependabot lens (`scripts/dependabot_index.py`) shipped. 68 alerts
  structurized, 94% fixable. Same data-plane / render-plane envelope as
  `git_rot_index`. Compound cross-lens query was demonstrated inline (zero
  intersection — proves the lenses are orthogonal, complementary not
  redundant).
- Lens-refresh wiring: registered in `ci/run.ts` as `scope:always`,
  `scripts/refresh-lenses.ps1` as one-stop orchestrator.
- LFS recovery via Codex's filter-repo: 64 unpushed local commits
  (including 655MB of `.safetensors`) made it to origin/main. Backup
  refs preserved as safety net. Claudine adapter POC moved to satellite.
- Auto-push post-commit hook: tool-agnostic fix for the
  `git.postCommitCommand` flow problem. Every commit (VS Code, Copilot,
  terminal) now pushes automatically. Cloud-agent dispatch stripped from
  the hook explicitly (no SWE-bot coupling — feedback memory saved).

## What was noise (the 90%)

Honest naming so this doesn't repeat:

- Hours of chasing `git.postCommitCommand` workspace setting variations
  in VS Code Insiders. Setting wouldn't fire reliably from the Copilot
  commit path. Multiple attempts at progressively more aggressive
  settings (`postCommitCommand:"sync"`, then also `confirmSync:false`,
  then cold restart) all in the same mechanism class. Should have
  pivoted to git hook after attempt 2; instead pivoted only after
  attempt 3 + user frustration. Lesson saved as
  `feedback_pivot_mechanism_after_2_failures.md`.
- Premature alarm about "lost content" during the LFS-recovery
  reconciliation. Read system-reminder snippets as on-disk state when
  they were intermediate/stale snapshots. Codex's filter-repo had
  actually preserved everything; my alarm was wrong. Should have
  verified against disk before raising. Lesson encoded in
  `feedback_history_rewrite_needs_backup_refs.md`.
- Silently preserving the Pentea cloud-dispatch hook when assembling
  the combined post-commit hook. "It was already there" is not consent;
  should have surfaced the existing behavior and asked. Lesson saved as
  `feedback_no_commit_cloud_coupling.md`.
- The hour-long indexer hang from yesterday (regex catastrophic
  backtracking on adversarial input). Already encoded in the original
  postmortem section above.

## Where the lane drifted

Original lane intent (2026-05-13 morning):
- Build orientation infrastructure (rot index → lens pattern → ladder)
- Apply lens to dependabot signal
- Complete L1..L4 detectors

Drift (2026-05-13 PM → 2026-05-14 AM):
- LFS push block surfaced → recovery (Codex did right thing)
- VS Code SCM panel sluggishness → diagnosed correctly as the 655MB diff
- "VS Code commit flow broken" investigation → spent hours in wrong
  mechanism class (settings) before pivoting to git hook
- Pentea cloud-coupling cleanup → tech debt, removed

The orientation lane completed successfully. The plumbing lane (SCM
flow + LFS + commit hook) consumed disproportionate time. The pivot
from "fix the settings" to "install a hook" was the breakthrough; that
should have happened earlier.

## Anchor commits (current SHAs)

| Commit | What landed |
|---|---|
| `145254a9` | L4 LINEAGE detector (ROOT-001) — Gitological Ladder complete |
| `9d9db598` | Lens automation in ci/run.ts + scripts/refresh-lenses.ps1 |
| `dependabot_index commit` | Dependabot lens shipped |
| `22c1d774` | Combined post-commit hook (later stripped) |
| `eeeb6d11` | Cloud-coupling stripped; post-commit is push-only |

## What's still actually open

- Backlog: 47 open dependabot alerts (lens at `manifest/dependabot_index.md`)
  — user-driven triage, no urgency.
- Backlog: per-file triage of remaining ROT-001/002/008 entries in
  `manifest/git_rot_index.md` — manual judgment, no urgency.
- Optional next: GitHub Actions workflow for cloud-side scheduled lens
  refresh — deferred, needs HODL-aware decision.

## Memory rules saved this session (cross-session inheritance)

- `feedback_lens_pattern.md` — Gitological Noise As Structured Data
- `feedback_no_commit_cloud_coupling.md` — commits stay local-scoped
- `feedback_proactive_session_synthesis.md` — pre-compact synthesis hygiene
- `feedback_pivot_mechanism_after_2_failures.md` — two failures = pivot, not third try
- `feedback_history_rewrite_needs_backup_refs.md` — backups before bold ops

Future-me reads MEMORY.md first when re-entering. These five rules
encode the durable behavior from this session arc.

The lane has converged for real now. Next session opens this file,
checks for new dependabot or rot entries, and decides where the user
wants to spend energy.

---

# Continuation — 2026-05-14 PM (method_index meta-lens + rot triage + SSOT canon)

Written in place; no new SESSION_2026_05_14_*.md file. The substrate
gets fewer files, more compound — per the no-more-layers rule.

## What landed (4 commits, all pushed to origin)

| Commit | What landed |
|---|---|
| `3a6a1350` | activity + method meta-lens — full Gitological 4-lens stack |
| `8bf359ee` | rot triage — 3 tombstones + anchor-correction + ROT-008 suppression |
| `cd2bc1fd` | (later corrected) introduced lifecycle: ssot-canon |
| `a8f9d6f2` | true SSOT canon is .github/copilot-instructions.archive.md; BOM tolerance |
| `9770db8c` | propagate EXCLUDED_LIFECYCLES into the canonical scripts/link_audit.py |

## The 4-lens stack (final shape)

- `git_rot_index` — link rot, L1..L4 depth
- `dependabot_index` — CVE alerts
- `github_activity_index` — PRs/Issues/Branches by actor type
- `method_index` — meta-lens; observes methods that cleared prior lenses

Cross-lens compound query result: 47/47 open dependabot alerts route to a
known method-class. No noise without a method.

Method catalog (11 entries) maps each noise class to its working
invocation: `uv-lock-upgrade`, `python-constraint-bump`, `cargo-update`,
`rust-constraint-bump`, `bun-update`, `npm-constraint-bump`,
`tombstone-mark`, `stub-creation`, `anchor-correction`,
`path-rename-followup`, `code-fence-fix`.

## Rot drop: 66 → 34 (−48%)

- 11 cleared by 2 archive tombstones (`copilot-instructions-copy.archived.md`
  in codex, plus initial-but-corrected mailbox file)
- 6 cleared by FAF Phase 3 handoff tombstone (work is shipped:
  `extensions/chthonic-archive/src/activation/` holds ~1500 lines extracted)
- 5 cleared by anchor-correction on `reference-appendix.reference.md`
  (dropped stale #L6991..#L7331 anchors — target file shrank ~7000 → 56 lines)
- 10 cleared by default-suppressing ROT-008 placeholder_literal (universal
  `[label](path)` doc syntax, not real rot)

## SSOT canon distinction (this is the load-bearing taxonomy update)

Three archive-suffixed files needed different lifecycle markers:

| File | Lifecycle | Reason |
|---|---|---|
| `.github/copilot-instructions.archive.md` | `ssot-canon` | THE 10K-line frozen macro-prompt-world — pool of everything else |
| `claude/mailbox/copilot-instructions.archive.md` | `tombstone` | Drifted variant, bulks rot |
| `codex/codex-session-logs/archive/copilot-instructions-copy.archived.md` | `tombstone` | Drifted variant, bulks rot |

`ssot-canon` is alive-and-frozen; `tombstone` is dead-and-preserved. Both
exclude from active rot/link scanning, but semantically distinct.

## The compounding-method principle (what the user articulated mid-arc)

> Same instances on different tasks that use the same method or lifecycle
> should work — wherever the method travels, the prior "didn't work" data
> compounds back into the method.

Applied: BOM tolerance was added to `is_tombstone()` after the .github SSOT
(saved with BOM) was missed. Then the predicate was propagated from two
sites (rot-index + CI wrapper) into the third (canonical `link_audit.py`)
so every direct invocation, satellite wrapper, and author-filtered wrapper
inherits the exclusion. Now `EXCLUDED_LIFECYCLES = {tombstone, ssot-canon}`
travels with the method.

## What is open (no urgency)

- 34 scattered rot entries — small clusters, top file has 4
- 40 open dependabot alerts — all routed to a method class; user-driven decision on which to act
- (Deferred) automated-review noise siphon — fifth lens candidate, not started

## What is settled (do not re-touch)

The methodology is locked. Future noise of known classes auto-routes via
`manifest/method_index.md`. Re-entry path: this file + `~/.claude/plans/1-i-have-enumerated-plum.md`
+ `MEMORY.md`.
