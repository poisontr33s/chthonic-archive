---
date: 2026-07-04
agent: Codex
substrate: CLAUDEBASE
status: trainstop-bridge
pairs-with: CLAUDEBASE/harbor/2026-07-04-ci-gate-architecture-fable-handoff.md
source-plan: C:/Users/eldno/.claude/plans/claudine-fable-shimmying-whistle.md
stop-reason: colorized preflight claims contradicted host/tool/remediation facts
---

# CI Gate Trainstop Bridge

This is the small bridge paired with the larger Fable handoff. It does not
replace the packet; it marks the mid-plan interception point so resumption does
not sail through a compass known to be partially lying.

## Paired References

- Main packet:
  `CLAUDEBASE/harbor/2026-07-04-ci-gate-architecture-fable-handoff.md`
- Original Claude plan:
  `C:/Users/eldno/.claude/plans/claudine-fable-shimmying-whistle.md`
- Local Codex law now carrying the rule:
  `CLAUDEBASE/Codex.md` (`Win11-Local-Bedrock`,
  `Clearance-Before-Continuation`)

## Trusted So Far

- Fable batches landed and pushed through the commits named in the main packet.
- Codex closed the deferred rebuild/redeploy event:
  `b63b02c4` and `dceafbe9`.
- `homepath-portability` is still useful: stale `0`, smells `22` after the
  deferred closure.
- `bun run ci` passed 22/22 at that moment.

Those facts remain valid as execution facts. They do not prove the host
preflight truth surface is coherent.

## Intercepted Claim Surface

The color-flashing preflight inside
`bun run --cwd extensions/chthonic-archive compile` is now intercepted:

- `verify-host passed` means no hard-fail lane, not "all claims are true."
- Solana/Agave lane wording is false-shaped:
  `agave-install.exe` exists, but its probes fail; `solana-install` is the
  actually missing binary, while the mise repair task still calls
  `solana-install init stable`.
- Anchor green hides an `avm` symlink-permission warning.
- Codex CLI path/version can shift by cwd/env/package surface, so green version
  text is context-bearing rather than absolute.

## Upstream Source Ledger (2026-07-04)

Checked live because "latest stable" is time-bearing cargo:

- Agave latest release is `v4.1.1`, released 2026-07-02:
  `https://github.com/anza-xyz/agave/releases`
- Anza's CLI install docs still contain installer examples pinned to
  `v4.1.0-beta.3`, while also pointing prebuilt-binary users at the GitHub
  `releases/latest` surface:
  `https://docs.anza.xyz/cli/install`
- Firedancer repo says full Firedancer validator is not ready for test or
  production use and has no production release; Frankendancer is the available
  mainnet/testnet lane:
  `https://github.com/firedancer-io/firedancer`
- Firedancer docs say Frankendancer is a hybrid of Firedancer and Agave, and
  full Firedancer remains heavy-development:
  `https://docs.firedancer.io/guide/getting-started.html`
- Firedancer release surface shows Frankendancer Mainnet `v0.913.40003` as the
  latest mainnet-ready release, and a newer Testnet `v0.1004.40101` pre-release:
  `https://github.com/firedancer-io/firedancer/releases`

Decision implication: this repo's Win11 preflight should not collapse Agave CLI,
Anchor/AVM, Frankendancer, and Firedancer into one "Solana lane." They are
different altitude bands with different operating systems, release meanings,
and remediation commands.

## Stabilization Pass (Codex, 2026-07-04)

Implemented the lane split in the local verifier:

- `verify-host.ts` now reports `Agave / Anza CLI`, `Anchor Lane`,
  `Frankendancer Validator Lane`, and `Firedancer C++ Lane` separately.
- `toolpool-scan.ts` now distinguishes `exists` from `usable` for CLI probes.
  Current cache shape: `solana` exists+usable, `agave-install` exists but is
  not usable, `solana-install` is missing.
- `.chthonic/mise.toml` no longer routes `agave-sync` through stale
  `solana-install init stable`; the task is blocked with explicit repair text
  until a usable `agave-install` or manual current Anza prebuilt lane is
  restored.
- `verify-host` no longer ends WARN-bearing runs with a clean all-clear. It now
  says: no hard failures, but clear WARN truth before treating the preflight as
  an all-clear.

Dry verification after patch:

- `bun run --cwd extensions/chthonic-archive verify:host` exits `0`.
- Solana lanes are `WARN` for Agave/Anza installer breakage and AVM symlink
  warning.
- Frankendancer and Firedancer C++ are `INFO`, not Win11 compile blockers.

Evidence hardening after the conductor's false-positive objection:

- `verify-host.ts` now carries an explicit evidence ledger per leaf status.
  Output lines name the basis: `command-exit`, `command-predicate`,
  `path-probe`, `stderr-warning`, `upstream-not-checked`, `remediation-blocked`,
  `manual-check`, `policy-warn`, `policy-info`, or `await-lane`.
- A green/yellow/blue status is therefore not allowed to stand alone. The
  verifier must disclose what it observed, what it inferred, and which policy
  downgraded a failure into `WARN` or `INFO`.
- The Agave/Anza lane now says: `solana` exists and runs; `agave-install`
  exists but throws on probe; `solana-install` is missing and legacy; latest
  upstream is not proven by offline preflight; stale remediation is blocked.
- `bun run --cwd extensions/chthonic-archive compile` dry-runs through the same
  repaired surface: compile exits `0`, but the preflight remains `WARN`, not an
  all-clear.

Pin-truth hardening after the dependency/versioning objection:

- Added `ci/checks/pin-truth.ts` and registered it as `pin-truth`.
- The check does not claim live latest. It distinguishes local declaration
  categories: exact pins, major pins, ranges, floating channels, local specs,
  and unknown specs.
- It now also reads tracked lockfiles as a separate truth surface. Current
  advisory state: 10 tracked lockfiles, 2053 locked package records
  (`cargo=889`, `bun=818`, `uv=346`). `--locks` prints per-lockfile previews;
  `--report` emits full JSON records.
- Output modes are intentionally tiered:
  default = short counts + contradictions only; `--locks` = per-lockfile
  preview; `--history` / `--provenance` = concise `git log -1` date/hash/subject
  for declaration and lock surfaces; `--report` = full JSON.
- Staged mode reads the Git index blob (`git show :path`), not the working-tree
  file, so VS Code partial-staging and index-only additions are checked as they
  will actually commit. UTF-8 BOM is stripped before JSON/TOML-ish parsing.
- E2E staged fixture proved the intended behavior: an index-only
  `package.json` with `"latest 1.2.3"` fails through
  `bun run ci/run.ts --staged --check pin-truth`; a clean `^1.2.3` range passes;
  cleanup leaves no staged files.
- Default mode is advisory and exits `0`; staged mode is strict only when a
  staged in-scope file introduces a contradiction like "latest/current/floating"
  language next to a concrete version literal.
- First advisory pass found five high-signal local contradictions, not a red
  gate: Solana crate comments that say "latest 4.0", ACP/Copilot bridge comments
  that say "track latest stable" beside pinned baselines, and a `pyproject.toml`
  comment saying `typer 0.26.7 is the latest`.
- This is the local equivalent of the Solana trainstop principle: a CI color may
  report pinned/floating/range facts, but it must not pretend a pinned file is
  live-upstream truth.

## Stop Law

- Do not resume Fable modernization by trusting the preflight colors.
- Separate observed host fact, detector logic, remediation text, and live
  upstream/repo law before changing tools.
- If any two contradict, the next batch is `Repair-The-Law` before
  `Obey-The-Lie`.
- Prefer dry-run probes, source inspection, and direct path/version checks over
  installer/update motion until the detector truth surface is repaired.

## Next Batch

Detector hardening is now executed for the intercepted surface:

1. `verify-host.ts` distinguishes installed CLI, broken installer, missing
   legacy installer, upstream-not-checked, and update-lane unavailable.
2. `.chthonic/mise.toml` blocks `agave-sync` instead of calling stale
   `solana-install init stable`.
3. `toolpool-scan.ts` distinguishes command `exists` from command `usable`.
4. `compile` was dry-run after the repair and inherits the evidence-bearing
   WARN surface.
5. `pin-truth` now audits version-declaration law before migration batches use
   "latest" language as evidence.

The remaining decision is not "trust the green" but whether to repair or upgrade
the local Agave/Anza installer lane. Re-check live upstream at that moment:
Agave release, Anza install docs, and Firedancer/Frankendancer release surface.

## Resume Gate

Resume the Fable packet only when the preflight can say, in one pass:

- what is installed;
- what is usable;
- what is stale;
- what repair command is real;
- and which warnings remain advisory rather than contradictory.

Until then, the correct state is trainstop clearance, not execution momentum.
