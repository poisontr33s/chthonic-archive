# /nightly Ledger

Append-only. Newest row at the bottom. See `README.md` for the schema and
`records/<date>_<lane>.md` for the full structured record behind each row.

**Scope limit, honest and load-bearing:** this ledger only tracks commits produced
*by* a `/nightly` invocation itself — not the surrounding conversation about the
skill, even in the same night. Between the `zombie-b3` and `zombie-c1` rows below,
6 real commits (`801e9438`, `51fd78ff`, `30cb14e4`, `13f35e08`, `e0729a10`,
`0d003e08`) landed in direct response to the user's own follow-up questions about
`/nightly`'s design — none of them belong to either invocation's own scope, so
neither row claims them. That's a real gap in what this ledger can see, not a
rounding error: most of that night's actual commit volume is invisible here. See
`project_nightly_skill_idea.md` (memory) or `git log` on `SKILL.md` directly for
that history.

| Date | Lane | Trigger | Mode | Duration | Outcome | Skill improved? | Record |
|---|---|---|---|---|---|---|---|
| 2026-05-27 | dsl-phase0 | claude-autonomous | default | not recorded | shipped | n/a (pre-dates §7) | [records/2026-05-27_dsl-phase0.md](records/2026-05-27_dsl-phase0.md) |
| 2026-07-07 | aca-live-correspondence | claude-autonomous | default | not recorded | shipped | n/a (pre-dates §7) | [records/2026-07-07_aca-live-correspondence.md](records/2026-07-07_aca-live-correspondence.md) |
| 2026-07-08 | zombie-b3 | claude-autonomous | default | not recorded (ledger built same night, after the run) | shipped | yes — §1 mixed-status atlas entries; pre-existing-staged-files near-miss | [records/2026-07-08_zombie-b3.md](records/2026-07-08_zombie-b3.md) |
| 2026-07-08 | zombie-c1 | **user-invoked** | default | **14m 3s** (first real value — start/end both captured live) | shipped | yes — §3's verification gate read renderer-only, both B3+C1 silently improvised the CLI-shaped equivalent | [records/2026-07-08_zombie-c1.md](records/2026-07-08_zombie-c1.md) |
