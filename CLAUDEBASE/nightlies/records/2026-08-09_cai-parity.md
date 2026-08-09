---
schema_version: 3
date: 2026-08-09
run_id: 2026-08-09_cai-parity
trigger: user-invoked
mode: default
lane: cai-parity
atlas_source: "session-thread: the XP/trail four-implementation divergence measured earlier the same night; cai was its last unfixed member. Atlas not consulted."
outcome: shipped
verification: pass
commits:
  - hash: c07262d5
    kind: feature
landing_doc: claude/mailbox/SESSION_2026_08_09_CAI_PARITY_AUTONOMOUS_NIGHT.md
self_improvement:
  found: true
  summary: "§3 read as a menu — 'pick whichever shape fits' — but this run touched both a Rust build and a PowerShell script; now every touched surface must clear its own shape"
duration:
  start: 2026-08-09T04:30:15Z
  end: 2026-08-09T04:38:45Z
  elapsed: 8m 30s
---

`xp.rs:75` claimed "must stay in sync with chthonic-xp.ps1" with nothing enforcing
it. Live measurement: cai 91,741 XP / Lv.95 vs the engine's 836 / Lv.9 — 109×,
99.8% of it session bookkeeping cai scored as work. Five divergences fixed
(meta-kind skip, 4 missing kind bonuses, priority default 0.75→1.0, `xp_delta`
ignored, and banker's-vs-half-away rounding, which is reachable at
`snapshot`+`wiring` at p3 = 4.5).

The last 8 XP were not arithmetic. `2026-04-13.hot.ndjson` carries a UTF-8 BOM,
Rust's `str::trim` leaves U+FEFF (not `White_Space`), the line failed to
deserialise, and `if let Ok(ev)` swallowed it. Worth exactly 8. `ankh-forge` had
the guard at `event.rs:23`; cai never did. Found only because a per-event diff of
both rule sets returned 836 = 836 with zero disagreements, which localised the
remainder to ingestion rather than scoring.

`xp-parity.ps1` now invokes the binary instead of transcribing its rules — the old
transcription began reporting a drift that no longer existed the moment `xp.rs`
was fixed. Both branches exercised: binary present → 836 = 836, exit 0; parked →
"unknown, not agreeing", exit 2.

Not decided here: installing over `~/.cargo/bin/cai.exe` (build went to `target/`
only — replacing an installed binary while the user sleeps is not this skill's
call), whether cai should surface its silently-skipped lines, and pinning parity
as a real test (the crate has 0 tests, so `cargo test` passing proves only that it
compiles).

Feature/meta ratio: one feature commit, plus this record and the §7 `SKILL.md`
fix. Meta stayed the exception.

**MATURITY note, against the scorecard's own gate.** `MATURITY.md` says 8/10 needs
"3-5 more real runs with NO new major skill-design in between." This is a real run
and the second tonight — but the night also added session-continuity precedence,
the staleness section, and the readiness gate to `SKILL.md`. By the gate's own
wording those runs do not count cleanly toward the 3-5. Score left at **7/10**;
the honest read is that the counter has not started yet, not that it advanced
twice.
