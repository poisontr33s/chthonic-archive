# Warmstart — AHA boundary layer

**Left 2026-08-10 ~02:45.** Written for whoever picks up next, most likely a
`/nightly`. Tree is clean apart from two items named at the bottom, both of which
are deliberately out of a nightly's scope.

## Where the arc got to

`CLAUDEBASE/dev/null/salt-trial/AHA_MANIFEST.md` is a prose specification, and
five of its eight laws turned out to already have mechanisms in this repo — not
because anyone wired them to the document, but because the document was
describing work that had happened.

| law | mechanism | state |
|---|---|---|
| Last-Call | `scripts/last-call.ps1` | built 2026-08-10, `ec195925` |
| The-Barrel-Roll | `HistoryLake::rotate` (capture.rs, 64 MB) · `logSonicEvent` (mcp-sonic.ts, 8 MB) | built |
| The-Housewarming | `tools/chthonic-mcp-server/src/canon.rs` — 3 bun servers → 1 Rust hull | built |
| Strategic-Amnesia | `.gitignore` + `git rm --cached`; generator tracked, output not | built |
| The-Sobriety-Clause | `mcp_handshake_probe.py --boot`, fleet sounding | **practice only — no gate** |
| The-Audience-Tax | — | unbuilt |
| The-Vagueness-Shield | — | unbuilt |

Every built law governs the cove's inside. Both unbuilt ones govern what crosses
out of it. They are one missing organ, and the manifest already named it:
**channel-mouth**. The repo gates at write (linters) and at commit (pre-commit
CI); it gates nothing at publish, and `post-commit` pushes to a public remote
with no inspection of what is leaving. That gap has drawn blood twice on record
— a 67 MB listening-history lake one commit from public on 2026-08-09, and a
full-admin Sentry token public for six weeks.

## Next move, already scoped

**The Audience-Tax scanner.** *If a gesture requires a public gallery to exist,
the procession sheds it.* Measurable as: an artifact written by code and read by
nothing.

- Build the write-set — `Add-Content`, `writeFileSync`, `fs::write`, `json.dump`,
  `--out` — and the read-set, and diff them.
- Known true positive to verify against: `manifest/sonic_session.jsonl` is
  written by exactly one function in `scripts/mcp-sonic.ts` and read by nothing
  in the repo. If the scanner does not flag that, it is wrong.
- It should charge, not just report: negative XP per write-only artifact.
  `pwsh-experience.ps1` is the precedent for a scorer that subtracts.
- Report and charge; never delete. Shedding is the procession's move, not the
  linter's — see the no-delete-from-seed ladder.

After it: the Vagueness-Shield is dither on what crosses out, never on what
stays. The trail holds 11,477 `session_start` / 11,274 `session_end` events at
millisecond resolution and pushes to a public remote — that reads as a diary, not
as telemetry. Hot exact and local, cold dithered, runestone downstream; aggregates
(XP sums, counts, intra-session order) survive, point queries do not.

## Out of scope for a nightly

- **`.chthonic/SSOT.md.sha256` is deleted, and the committed seal was already
  stale**: HEAD's seal reads `1d484686`, HEAD's `SSOT.md` hashes to `6808095b`,
  and it is not an EOL artifact. Deleting it flipped `AxiomVerifier` to the
  silent `return Ok(())` branch. Reseal or restore-and-fail-loudly is a canon
  decision belonging to the user. Do not decide it autonomously.
- **`apps/flux-lane-archive/`** untracked. Belongs to the FLUX / Sol-Forge lane,
  which the user has queued as priority 2 behind this one.
