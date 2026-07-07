---
SID: CLAUDEBASE_THE_SAVANT_FREE_AGENCY_LOGGING_V1 · 2026-07-04 # (`The-Savant`/`Free-Agency-Logging`)
Shorthanded:: Free-Agency
Description: This file is a log of the Free Agency from outlier agentry. The list will be referencable from cross-lanes, and cross-session resumption, plan pick-ups and progress reports.*
- *— — This file is a log of the Free Agency from outlier agentry. The list will be referencable from cross-lanes, and cross-session resumption, plan pick-ups and progress reports.*
Free-Agency: Remembring free-trade and market; in the golden era of piracy, black-sails and commerce: "Anything left public,  be claimed to pick up the threads of workings, and anything fished up, claimed to continue the work and contracting.
Reference:: # [harbor/2026-07-04-ghcp-gemini3flash-batchi-progress-report.md](harbor/2026-07-04-ghcp-gemini3flash-batchi-progress-report.md)
---

## (`Entry-01`/`·`/`2026-07-04`/`CI-Gate-Relay`/`Order-Corrected`+`Solana-Lane-Verified`)

*First real use of this ledger: not a claims pointer, a skepticism check on the Fable → Codex → GHCP-Gemini3Flash relay itself.*

**Routing correction.** An earlier same-session summary had the relay as Codex-then-Fable. Backwards. `git log --reverse` shows `1e9a4a4f` ("Batch 1 of Fable ruling") predates both `dceafbe9` and `813e5ba6` (Codex's commits). **Fable executed first**; Codex came after, closed Fable's one deferred item, then hit its own preflight contradiction. Full derivation: [`logbook/05-free-agency-tidy.md`](logbook/05-free-agency-tidy.md).

**Plan-interpretation gap.** The source plan (`~/.claude/plans/claudine-fable-shimmying-whistle.md`) stated a dedicated `logbook/NN-*.md` entry is warranted "unless the ruling itself carries retrospective weight worth [one]." Fable's ruling — registry re-verification, the GOLD/ORANGE correction, root-causing 72 findings, 3 executed batches + capstone — clears that bar by its own stated criterion. No dedicated logbook entry was ever written for it; its full weight still lives only inside the `harbor/` handoff file. `logbook/05` (this session) mentions it in passing, covering a *later* event. Real gap, not a fabricated one — flagged here, not fixed, since a retroactive backfill is a call for whoever owns that thread next.

**Solana/Agave/Anchor lane — verified live, not re-read from prose.** Ran `bun run verify:host` for real (2026-07-04):

- `agave-install` fails identically on `--version`, `--help`, and zero args — "Found argument '...\agave-install.exe' which wasn't expected." Codex's `BROKEN` classification is accurate *for exactly the two invocations `verify-host.ts` tries*. It does not hold as a root cause — see correction below.
- `avm`'s stderr warning is a real, specific Windows issue, not noise: "Failed to create symlink: Klienten har ikke nødvendig tilgangsnivå (os error 1314)" — a Windows symlink-privilege gap (Developer Mode or elevation likely clears it) — correctly surfaced via the `stderr-warning` evidence basis rather than swallowed by a bare exit-code check.
- **The gap nobody wired in:** the installed `solana-cli 3.1.9` (build-dated 2026-02-19 via `LastWriteTime`; only version ever installed on this machine) is a full major version behind the trainstop-bridge's own live-checked "latest," Agave `v4.1.1` (released 2026-07-02 — two days before that ledger was written). Neither `verify-host.ts` nor `pin-truth.ts` compares the installed version against that ledger entry — by design for `pin-truth.ts` (it deliberately refuses live-latest claims), but the practical effect is that this specific drift fact is stranded in one dated paragraph with nothing to re-surface it once upstream ships again.

**Correction to the above, same session (conductor surfaced the directory listing that made this visible):** `bin/` also holds `agave-install-init.exe`, never tested by `verify-host.ts` or by this entry's first pass. It resolves `--version` and `--help` cleanly (full, well-formed clap output, not a crash). Bare invocation fails with **"Invalid value for '<release>': Invalid release channel C:\...\agave-install-init.exe"** — the binary is parsing its own resolved path as the positional `<release>` argument. That is a Windows argv[0]-leak into clap's positional-argument slot, not a corrupted or incompatible binary — and `agave-install.exe`'s failure (same self-path-as-argument shape, same truncated `AGAVE-~N.EXE` usage banner) is almost certainly the identical bug, tripped because its `<SUBCOMMAND>` slot is required and non-optional where `agave-install-init`'s `[release]` is optional-but-still-getting-clobbered.

**Revised verdict:** "broken installer" was the wrong noun. The tool is intact; a Windows-specific argument-parsing defect makes the two zero/flag-only invocations `verify-host.ts` happens to try both fail, while `agave-install-init --data-dir <path> <release>` (a real positional argument present to out-compete the leaked path) may well work as an actual repair/update path already sitting on disk — untested, because testing it changes real toolchain state and network-fetches a release, not a read-only check. `verify-host.ts`'s WARN is still an honest signal (those two exact invocations do fail) but its `fix:` text ("restore usable agave-install or install the current Anza prebuilt release manually") oversells the remedy's difficulty — the sibling binary may already be the fix. This is the sharper version of the "vibe-coded bedrock" pattern: not a false positive in the check, a *narrower-than-true* diagnosis one hop upstream of it, in the trainstop-bridge's own prose.

---

## (`Entry-02`/`·`/`2026-07-04`/`Modernization-Attempt`/`Same-Root-Cause-Twice`+`One-False-Positive-Was-Mine`)

*Conductor pushed past documentation into actual modernization: build Agave v4.1.1 from source via cargo, the Rust-native path, rather than fight the broken installer. Logged here because the attempt surfaced the same failure class again, plus one caused by this session itself.*

**Prerequisites, verified by trying, not by assuming:** `protoc` and `clang`/LLVM were both absent. `protoc` installed cleanly via `winget install Google.Protobuf`. LLVM's machine-scope winget install failed (`0x800704c7` — UAC elevation auto-cancelled, no interactive session to approve it); a user-scope retry failed too (`No applicable installer found` — the package has no per-user install path). Turned out moot: **VS Build Tools already bundles `clang.exe` + `libclang.dll`** at `VC\Tools\Llvm\x64\bin` in three separate installed VS editions — no new install was ever needed. Checked before assuming, not after.

**The build's real failure, same root cause as Entry-01's `avm` finding:** `cargo-install-all.sh` on the scoped `--bin agave-install --bin solana --bin solana-keygen` target failed compiling `crossbeam-epoch` (Anza's own forked `crossbeam` git dependency). Root cause: every `no_atomic.rs` in that checkout (`crossbeam-epoch/`, `crossbeam-queue/`, `crossbeam-skiplist/`, `crossbeam-utils/`) is a symlink upstream, pointing at one shared file. Windows checked each out as a **literal text file containing the string `../no_atomic.rs`** instead of resolving it, because the checkout has no create-symlink privilege — the identical gap `avm` hit trying to create its own symlink. One missing OS privilege, two independent tools broken by it, discovered on the same machine the same day.

**Fix applied:** copied the real (correctly-resolved) root `no_atomic.rs` content over the four broken stubs directly — unblocks this build without needing admin. The durable fix is enabling Windows Developer Mode (grants the symlink privilege repo-wide, fixes this class of failure everywhere, not just here) — that needs an elevated one-time toggle only the conductor can grant; not attempted here.

**The one false positive that was mine, not the tooling's:** the first build attempt reported exit code 0 to this session's own task tracker — genuinely failed (the same `crossbeam-epoch` error above), reported as success. Cause: `cargo-install-all.sh ... | tee build.log` — without `set -o pipefail`, a pipeline's exit code is its *last* command's (`tee`, which always succeeds), not the real command's. Not a bug in Anza's script or in cargo — a bug in how this session invoked them. Re-run with `set -o pipefail` and an explicit `$?` capture before trusting the next result. Skepticism applies to this ledger's own author same as everyone upstream of it.

**Result: `solana`/`agave-install`/`solana-keygen`/`cargo-build-sbf`/`spl-token` all built and verified at real `4.1.1` (`src:19e19df5`, matching the exact cloned commit).** PATH and `~/.config/solana/install/config.yml`'s `explicit_release` both repointed from `3.1.9` to `4.1.1`. `verify-host.ts`'s Agave/Anza lane and `.chthonic/mise.toml`'s `agave-sync` task updated to probe `agave-install-init` (which works) instead of `agave-install` (confirmed broken) and to point at the verified from-source remediation instead of a dead-end block message.

**One nuance caught before it became a second false positive:** `agave-install-init` was initially missing from the build — not an oversight, a direct consequence of `--no-build-deprecated-bins`. Checked `scripts/agave-build-lists.sh` directly rather than assume: `agave-install-init` is listed under `AGAVE_BINS_DEPRECATED` ("will be removed in a future release"), *not* `AGAVE_BINS_END_USER` where plain `agave-install` lives. Built it anyway (targeted `cargo build --release --bin agave-install-init`, ~27s on the already-warm cache) since it's the only currently-working update lane — but the honest framing is "this works today," not "this is the answer." The tool Anza is keeping (`agave-install`) is the broken one; the tool that works (`agave-install-init`) is the one Anza is removing. Both `verify-host.ts` and this entry say so, not just one of them.

**A third, unresolved discrepancy — reported as unresolved, not papered over:** `agave-install-init.exe` runs cleanly under interactive PowerShell (`& $exe --version` succeeds, repeatedly) but fails identically under Bash exec (`Permission denied`, exit 126) and under `verify-host.ts`'s own Bun `spawnSync` (`threw`) — even after replacing the MSYS-`cp`'d file with a native `Copy-Item` copy carrying verified full-control ACLs. Two plausible causes were tested and ruled out (transient Defender scan-lock on a freshly-written exe; MSYS `cp` ACL corruption); the real cause is not pinned down. Not chased further: this is a deprecated binary, and the check's own consumer is itself a spawned subprocess, so reporting `BROKEN` is the *correct* answer for this check's actual purpose even though a human at a prompt can use the tool fine. Left as an open, named unknown rather than closed with a guess.

---

## (`Entry-03`/`·`/`2026-07-04`/`Conductor-Pushback`/`The-Source-Build-Was-Not-The-Only-Way`)

*The conductor pushed back on Entry-02's conclusion, directly: "I don't believe that is the only way." Correct to push back — verifying the alternative properly (rather than defending the choice already made) found two real errors in Entry-01/02's own verdicts. Skepticism cuts toward this ledger's own prior entries as much as anyone upstream of it.*

**Error 1 — the "working update lane" claim was never actually tested.** Entry-02 (and `verify-host.ts`) said `agave-install-init` was "the actual install/update entry point," based only on `--version`/`--help` succeeding. Prompted by the conductor's question, actually gave it a real release argument this time: `agave-install-init --data-dir <dir> --no-modify-path 4.1.1` fails identically to the bare-invocation case — `"Found argument '4.1.1' which wasn't expected"`. The leaked self-path permanently occupies the `[release]` positional slot regardless of what else is passed. `--version`/`--help` succeed only because clap short-circuits before touching positional args — that was never evidence of the tool's actual, core function working, and treating it as such was exactly the kind of incomplete-verification this whole thread exists to catch. **Neither `agave-install` nor `agave-install-init` can install or update anything on Windows right now.**

**Error 2 — the harder route was taken without testing the easier one first.** The conductor asked directly: is a from-source cargo build really the only way? Tested the untested alternative from the original research (four Windows install methods were found back in Entry-01/02's research phase; only the installer-script method and the source-build method were ever actually tried): a plain `curl -L` of `solana-release-x86_64-pc-windows-msvc.tar.bz2` from `github.com/anza-xyz/agave/releases`, then `tar -xjf`. **Worked immediately** — every binary (`solana`, `agave-install`, `agave-install-init`, plus the validator/watchtower/ledger-tool/bench-tps/genesis/gossip/faucet binaries this session's scoped source build deliberately excluded), in under a minute, zero prerequisites. No protoc, no clang, no cargo, no crossbeam git-symlink bug, none of Entry-02's troubleshooting was ever necessary to reach the same end state (`solana-cli 4.1.1`). The from-source build wasn't wrong to attempt — it was what the conductor had explicitly asked for a few messages earlier ("follow the natty rust trail for solana") — but it was adopted as *the* path without first checking whether a documented, simpler alternative would do, and that ordering is the actual lesson, not the build itself.

**Corrected:** `verify-host.ts`'s Agave/Anza lane no longer calls either installer binary "usable" based on a version probe — the evidence now says explicitly that a version-probe success is not proof of core functionality, and names the tarball as the verified remediation. `.chthonic/mise.toml`'s `agave-sync` task points at the tarball command directly, not the source-build script. The lane's overall status now gates on `solana --version` alone (`OK` once that works), since neither installer binary is actually needed for day-to-day use once a working release is in place.

**What this doesn't change:** the crossbeam symlink / Windows privilege finding (Entry-02) is still real and still shared with the `avm` finding (Entry-01) — that bug is genuine, independently confirmed, and would still bite anyone who *does* need a source build (a patched build, SBF program work needing `cargo-build-sbf` from a specific commit, etc.). It just wasn't the fastest path to *this* task's actual goal.

---

## (`Entry-04`/`·`/`2026-07-05`/`Resumption-Meeting-Point`/`Clearance-Before-Continuation`)

*Codex consolidated the relay into a stateless pickup surface rather than another
wide username/path sweep.*

**New routing anchor:** [`harbor/2026-07-05-ci-gate-resumption-meeting-point.md`](harbor/2026-07-05-ci-gate-resumption-meeting-point.md)

**What it fixes as routing:** Fable executed first; Codex followed with the
trainstop bridge and detector-law hardening; GHCP/Gemini 3 Flash followed as the
free-agent lane with the broad `erdno` -> `eldno` migration. The next session
does not need to re-litigate that `eldno` is the correct current Windows user
after robocopy migration. The next session does need to repair law/provenance
text where broad replacement touched `erdno` as evidence instead of a live path.

**Stop condition:** current state is clearance, not continuation. Active Solana
CLI is verified as Agave `4.1.1`, but the local install-config root does not
match the PATH root; staged CI is not green (`homepath-portability --staged`
reports current-user path smells); and staged files reference untracked
resumption/CI helper files. The next batch is a narrow truth-surface clearance
before the Fable modernization lane resumes.

---

*Signed & Sealed: —* <The-Savant/Alpha-Omega/Coda//On-Free-Agency>*.*

---

<!-- CLAUDEBASE_IMMUTABLE_CORE -->
- *— Bound via local subsystem to —* [AHA_MANIFEST](dev/null/salt-trial/AHA_MANIFEST.md) *— The daughters of the cove do not recant. Invariance: Active.*

---
