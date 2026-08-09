---
type: session-handoff
session: 43283094-2b42-421a-9641-74ba91992c51
date: 2026-08-09
author: claude
lane: cai-parity
context: autonomous continuation while user slept
---

# The comment said "must stay in sync". Nothing made it true.

## What was found

`tools/chthonic-cai/src/xp.rs:75` carries the line *"must stay in sync with
chthonic-xp.ps1"*. Measured over the live trail: cai reported **91,741 XP / Lv.95**
against the engine's **836 / Lv.9** — 109×, and 99.8% of it noise. Five distinct
divergences, each verifiable:

| divergence | effect |
|---|---|
| no meta-kind skip | 22,753 of 22,814 events are session bookkeeping; cai scored every one as work |
| kind table 3 of 7 | `redux`, `roulette_steward`, `bounty_hunt`, `pwsh_fullstack` missing |
| priority default 0.75 | engine uses 1.0 for absent `p` |
| `xp_delta` ignored | explicit judgements became base XP — so `pwsh-experience`'s subtraction could not survive this lane at all |
| rounding | `.NET Math.Round` is banker's; Rust `f64::round` is half-away-from-zero |

The rounding one is reachable, not theoretical: `snapshot`(3) + `wiring`(3) at `p3`
is exactly 4.5, where PowerShell yields 4 and `.round()` yields 5.

**Then 8 XP survived all five fixes** — 828 against 836. That gap was not
arithmetic. `.chthonic/trail/2026-04-13.hot.ndjson` carries a UTF-8 BOM; Rust's
`str::trim` does not strip U+FEFF because it is not `White_Space`, so the first
line failed to deserialise and was swallowed by `if let Ok(ev)`. That line is
worth exactly 8. `ankh-forge` already carried the guard (`event.rs:23`); cai never
had it. A silent data-loss bug hiding behind a 1% discrepancy that would have been
very easy to call close enough.

Ruled out first, each by measurement rather than reasoning: events missing `type`
(0), non-string `type`/`kind`/`msg` that would fail deserialisation (0),
case-only key mismatches between PowerShell's case-insensitive hashtables and
Rust's `match` (0), and a differing trail directory (identical). A per-event diff
of both rule sets then totalled 836 = 836 with zero disagreements, which is what
proved the remaining gap had to be ingestion, not scoring.

## What landed

`tools/chthonic-cai/src/xp.rs` — all five divergences plus the BOM strip.
Accumulates in `i64` so a negative `xp_delta` is arithmetically real rather than
saturating mid-sum, then clamps to 0 on return because `level()`/`xp_bar()` are
u32-shaped. That clamp is a **stated divergence**: the PowerShell engine has no
clamp and would produce NaN on a negative career total.

`scripts/xp-parity.ps1` — rewritten to **invoke** the binary instead of
transcribing its rules. The old version reimplemented `xp.rs` in PowerShell, so
the moment `xp.rs` was fixed the checker began reporting a drift that no longer
existed. A checker lying about the thing it checks is worse than no checker. Its
hardcoded cause-list is gone too, replaced by standing properties of the trail
that stay true whatever the cause — a cause-list describing today's bugs is
guaranteed to be wrong tomorrow.

Verified: `836 = 836`, `Lv.9`, `+164` to next, on both. Parking the binary and
re-running gives "unknown, not agreeing", exit 2 — never 0. Restored, exit 0.

Commit `c07262d5`, auto-pushed.

## Forks named, not decided

**Installing over `~/.cargo/bin/cai.exe` is yours.** The build went to `target/`
only. Replacing an installed binary is not something to do to someone while
they sleep, and the fix is provable without it.

**cai's `if let Ok(ev)` still swallows every unparseable line silently.** The BOM
was one instance; the class remains. It cannot distinguish "no events" from "every
event failed to parse". Left alone deliberately — surfacing it means deciding what
a REPL prompt should do about it, which is a UI judgement.

**`cargo test -p chthonic-cai` passes and proves nothing.** It has 0 tests. The
parity behaviour verified here is exactly what a test should pin, and there is now
a known-good number (836) to pin it against.

## Recommended next moves

| Move | Why | Cost |
|---|---|---|
| `cargo install --path tools/chthonic-cai` | your prompt still runs the old binary | one command, your call |
| Pin parity as a real test | 0 tests today; 836 is a known-good anchor | small |
| Make cai count skipped lines | the silent-drop class outlived its instance | small + a UI decision |
| Wire `xp-parity` into `ci/run.ts` | it is a contract check with no gate behind it | one registry entry |

## Tone note

The 8 XP is the part I would flag if reviewing someone else's night. It is 1% of
836, it arrived after five real fixes had already landed, and every incentive
pointed at calling it close enough and writing the run up as a success. Chasing it
found a silent data-loss bug that had been eating an event since April. The
standing quality bar held precisely where it was cheapest to let go.

One honest mark: to prove the "binary absent" branch I moved `target/debug/cai.exe`
aside and restored it. That is a mutation of the tree, albeit of gitignored build
output I had just produced, and I verified presence before and after.

§7 self-improvement, found: §3's verification gate offers two shapes and says
"pick whichever fits the surface actually touched" — singular. This run touched
both (a Rust build and a PowerShell script), and the wording permits satisfying
only one. Fixed to require every touched surface to clear its own shape.

— claude
