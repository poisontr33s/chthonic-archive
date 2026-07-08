---
name: nightly
description: "Autonomous continuation while the user is away (asleep, out) — picks one bounded task from the frontier atlas's warmest cluster, follows rewindability/cessation discipline, verifies before committing, writes a structured landing doc to claude/mailbox/. Formalizes a pattern proven twice, not invented fresh: SESSION_2026_05_27_DSL_AUTONOMOUS_NIGHT.md and SESSION_2026_07_07_ACA_AUTONOMOUS_NIGHT.md."
allowed-tools: "Read, Grep, Glob, Bash, Edit, Write"
user-invocable: true
---

# /nightly — autonomous continuation

Two nightlies happened before this skill existed, hand-run from precedent: `claude/mailbox/SESSION_2026_05_27_DSL_AUTONOMOUS_NIGHT.md` and `claude/mailbox/SESSION_2026_07_07_ACA_AUTONOMOUS_NIGHT.md`. This skill generalizes what both actually did, not what a nightly *should* do in the abstract. Read both before the first real invocation if their shape isn't already warm in context.

## When to use

The user is stepping away for a real stretch (sleep, out) and wants bounded, verified progress rather than nothing happening. Not a replacement for asking — it exists because the user explicitly asked for it each time so far. Treat an unprompted `/nightly` invocation the same as an explicit ask, not as standing permission to run it whenever convenient.

## 1. Scope selection

Optional argument names a topic or cluster directly (`/nightly aca-engine`, `/nightly dsl`) — both real invocations so far worked this way, the user named the topic. With no argument: read `CLAUDEBASE/charts/frontier-atlas.md`'s Level map section and its §1 ("ready to alchemize now") first. Pick the item that is BOTH gate-met (§1, not §2/§3) AND in a cluster with a recent nearby landing doc — "what cluster am I already warm in" is the atlas's own stated purpose for this. Do not pick from §2 (externally blocked) or §3 (needs foundational work) without the user having named it directly — those are explicitly not nightly-sized.

**§1 is not a pure candidate queue.** First time scope selection actually ran with no topic named (2026-07-08, zombie B3), §1 held a mix: genuinely-open items sitting next to entries kept purely for record-keeping (work logged there the same session it closed). Check each entry's own stated status, not just its presence in §1 — "ready to alchemize" and "already alchemized, logged here" can sit side by side.

**Before acting on anything the atlas or memory claims**: verify it against the current code. Three real nightlies, three different outcomes on this check — the DSL nightly found a hidden grammar shadow the "6/6 clean" baseline had missed (memory wrong); the A-C-A nightly found the whole correspondence engine was write-only despite the philosophy memory describing it as complete (memory wrong); the zombie B3 nightly found a genuine middle case — partially wired, some fields already flowing through, some not, neither fully-done nor fully-untouched. Don't force a verify-before-assume finding into a binary matches/doesn't-match box — read closely enough to say exactly which parts are real.

## 2. The discipline (non-negotiable, not a style choice)

- **Build meta-tooling/baseline before changing behavior**, when a baseline doesn't already exist. The DSL nightly built the coverage tool before touching the grammar; the A-C-A nightly wrote a numeric probe pattern (see this session's atmosphere-shader debugging) before editing shaders.
- **Never decide a genuine architectural fork alone.** If a change has more than one reasonable shape and picking wrong is expensive or hard to reverse, implement the safe/minimal version, and name the fork explicitly in the landing doc's "recommended next moves" table instead of picking for the user. Both real nightlies did this (DSL's L45 substrate-marker question; A-C-A's per-frame-recompute question) — neither was resolved unilaterally.
- **No invented content in the user's own creative/authorship domains** (lore meanings, SSOT.md prose, character/world content). Verifiable, forced-by-substrate work only, unless the user has explicitly opened that domain for this invocation.
- **One well-verified thing beats several padded ones.** Don't stretch scope to look more productive — both landing docs said this explicitly in their tone notes, and it's worth restating here so a future invocation doesn't drift.

## 3. Verification gate — must pass before any commit

- `cargo build` (or the project's equivalent) clean.
- Relevant test suite green — run the narrowest scope that actually covers the change, then confirm nothing wider broke.
- If the change touches anything with a visual/behavioral smoke test (this repo: `scripts/render-smoke.ps1`), run it and check BOTH that it still passes AND that the diff (screenshot bytes, log content) matches what the change should and shouldn't have touched. A byte-identical screenshot alongside a changed log line is a real proof of isolation, not a formality — this is exactly how the A-C-A nightly confirmed its fix reached only the intended surface.
- Do not commit on a failing or unverified gate. Revert cleanly (matching this session's atmosphere-shader revert-and-rescope discipline) rather than leaving a half-working change in the tree.

## 4. The landing doc

Write to `claude/mailbox/SESSION_<YYYY_MM_DD>_<TOPIC>_AUTONOMOUS_NIGHT.md`, frontmatter:

```yaml
---
type: session-handoff
session: <this session's id>
date: <YYYY-MM-DD>
author: claude
lane: <short-topic-slug>
context: autonomous continuation while user slept
---
```

Body sections, in this order, matching both precedents: what was found (including anything memory/planning claimed that the live code didn't back up), what landed (files + why, not a diff dump), the architectural fork(s) named but not decided, a "recommended next moves" table, a short tone note (honest about what was and wasn't done, no padding), and a plain sign-off.

## 5. Commit

Both real nightlies committed autonomously, including through this repo's auto-push-on-commit hook. That's the default here too — but it is a default, not a law: if the verification gate didn't fully pass, or the change touches something the discipline in §2 says name-don't-decide, stop short of committing and say so in the landing doc instead.

**Check the index before staging, every time.** The zombie B3 nightly found the working tree already had ~20 unrelated files staged from earlier in the session (`git status --porcelain` showed `A `/`M ` entries before this invocation touched anything) — a first `git add <this task's files>` landed on top of that existing staged set instead of replacing it, and committing at that point would have swept all of it in under this skill's own authority. Every time: run `git status --porcelain` first; if anything unexpected is already staged, `git reset HEAD --` (unstages everything, working tree untouched) before adding your own files; stage only the exact files this invocation's task touched, by name — never `git add -A`/`git add .`. If the tree has other unrelated uncommitted or staged work, name it in the landing doc for the user's own call on how to batch it — deciding that is not this skill's job.

## 6. Close the loop — retrospective self-improvement (mandatory, not optional)

Every invocation ends with one more pass, after the landing doc and commit (or stopped-short note) are done: review the run itself for any place THIS SKILL's own design — scope selection, the discipline, the verification gate, the commit process — had a blind spot, produced a near-miss, or worked only because of a general habit rather than because this file said to. This is independent of whether the target task succeeded: a fully successful run, like zombie B3, can still expose a real gap in the skill itself (§1's mixed open/closed entries; the near-miss on pre-existing staged files, caught only by a general git-safety habit, not by anything this file said at the time).

If a real gap surfaced: name it precisely, fix it in THIS SAME `SKILL.md`, re-verify with `skill_audit.py`, and note the fix — with which run found it — in the landing doc's tone note. If nothing surfaced: say so explicitly rather than silently skipping the step. "Reviewed, nothing found this run" is a real, valid outcome, not a failure to find something — don't invent a weakness to report just to have filled in this section.

This is nightly's own scoped, immediate cousin of the `self-upcycle` skill's pattern — direct and same-invocation rather than deferred behind a 2+ occurrence promotion threshold, since nightly runs happen too infrequently for "wait for a second occurrence" to be worth the wait. Do this by default, every run, without being asked — that's the whole point: a self-improving skill that only improves when someone thinks to ask isn't actually recursive, it's just responsive.

## What this skill deliberately does not do

- Does not pick §2/§3 atlas items (externally blocked, or genuinely foundational) without the user naming them directly.
- Does not spawn subagents by default — both real nightlies were single-threaded, direct execution; that kept the landing doc's account of "what I did" exhaustive and trustworthy. Only reach for the Agent/Workflow tools if the scope genuinely needs them and that's stated in the landing doc.
- Does not have a Codex-lane counterpart yet (`.codex/skills/` parity is unclaimed for this skill as of 2026-07-07) — flag this if cross-lane parity ever matters here, don't silently assume one exists.
- Does not resolve, by itself: what triggers scope selection when the atlas is stale, how rigid the "when to stop" judgment call should be, or whether landing-doc frontmatter should be schema-validated. These are named in memory (`project_nightly_skill_idea`) as open design questions, not decided by writing this file.
