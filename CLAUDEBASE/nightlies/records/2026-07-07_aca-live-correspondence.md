---
schema_version: 2
date: 2026-07-07
run_id: 2026-07-07_aca-live-correspondence
trigger: claude-autonomous
mode: default
lane: aca-live-correspondence
atlas_source: "predates frontier-atlas.md's first commit that same night — user-named directly"
outcome: shipped
verification: pass
commits: [670499a8]
landing_doc: claude/mailbox/SESSION_2026_07_07_ACA_AUTONOMOUS_NIGHT.md
self_improvement:
  found: false
  summary: "predates SKILL.md §7 (skill was scaffolded later the same night, after this run finished) — not applicable"
duration:
  start: not recorded
  end: not recorded
  elapsed: not recorded
---

Second hand-run nightly, the other precedent `/nightly` formalized from. Found the
A-C-A engine's fully-verified triad (`zodiac.rs` + `cosmos.rs`) was wired to a
frozen verification epoch and a write-only struct field nothing read — applied the
engine's own "forced vs ornamental" criterion to its own integration, not just its
math. Fixed via `cosmos::julian_day_now()`, wired into the correspondence-socket
reading only; the celestial-field mesh stayed pinned for the smoke-test baseline
(verified byte-identical, 163308 bytes). Left the per-frame-recompute question as a
named, undecided fork rather than resolving it alone. Full account: the landing
doc linked above.
