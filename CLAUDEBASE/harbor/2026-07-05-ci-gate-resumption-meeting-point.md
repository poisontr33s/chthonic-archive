---
date: 2026-07-05
agent: Codex
substrate: CLAUDEBASE
status: resumption-meeting-point
pairs-with:
  - CLAUDEBASE/harbor/2026-07-04-ci-gate-architecture-fable-handoff.md
  - CLAUDEBASE/harbor/2026-07-04-ci-gate-trainstop-bridge.md
  - CLAUDEBASE/The-Savant-Free-Agency-Logging.md
purpose: stateless pickup surface after Fable/Codex/GHCP-Gemini relay
---

# CI Gate Resumption Meeting Point

This is the current pickup surface. It does not replace the Fable packet or the
trainstop bridge. It gives the next session the order of operations without
forcing it to re-read the whole relay.

## Sequence

1. **Fable executed first.** The CI gate architecture ruling landed and executed
   the three batches plus capstone. Treat the Fable handoff as the canonical
   strategic ruling and execution ledger.
2. **Codex followed.** The deferred extension rebuild/redeploy path was closed,
   then the Solana/Agave preflight contradicted its own color surface. Codex
   wrote the trainstop bridge and added detector-law hardening, including
   `pin-truth`.
3. **GHCP/Gemini 3 Flash followed.** It picked up as a free-agent lane and ran a
   broad `erdno` -> `eldno` migration plus CLAUDEBASE navigation consolidation.
   The user confirms the live-machine intent: after robocopy migration, `eldno`
   is the correct current Windows user on this machine.
4. **The current stop is not the username swap.** The stop is the truth surface:
   broad replacement also touched historical/provenance/law text where `erdno`
   was evidence, not a live path. Those need targeted repair, not another broad
   sweep.

## Trusted Now

- Active Solana CLI is Agave `4.1.1`:
  `Get-Command solana` resolves to
  `C:\Users\eldno\AppData\Local\solana\install\releases\v4.1.1\solana-release\bin\solana.exe`,
  and `solana --version` prints `solana-cli 4.1.1 (src:19e19df5; ... client:Agave)`.
- Both local release directories exist:
  `...\releases\v3.1.9` and `...\releases\v4.1.1`.
- The Solana installer config is not a clean source of active truth by itself:
  `~/.config/solana/install/config.yml` has `explicit_release: 4.1.1`, but its
  `releases_dir` points at `C:\Users\eldno\.local\share\solana\install\releases`
  while PATH uses `C:\Users\eldno\AppData\Local\solana\install\releases`.
- Current CI registry surface lists 26 checks. Any report saying 15/15 or 25/25
  is a dated/local claim, not the current roster.
- `homepath-portability --staged` currently fails, reporting 699 current-user
  path smells, mostly in `.vscode/audit_*.json`. That is not "green"; it is the
  gate doing its job against the staged state.
- The visible `game/` lane does not currently declare a Solana/Agave/Anchor
  dependency. `game/core/Cargo.toml` depends on `serde`, `serde_json`, and
  `serde_yaml_ng`; `game/core/Cargo.lock` contains no Solana/Agave/Anchor/SPL
  packages; `game/cocos-iso/package.json` only records Cocos Creator metadata.
  Therefore the Solana work so far is host CLI/toolchain work, not game-code
  SDK integration. This is not a closure; it is the gap. If the game lane is
  meant to be Solana-aware, the next move is an explicit integration batch, not
  a silent version bump.
- Current Solana-family stable surfaces are not one number:
  - Agave validator/CLI release surface: `v4.1.1` (GitHub latest, 2026-07-02).
  - Local active CLI: `solana-cli 4.1.1`.
  - Rust client crate surface from Cargo registry: `solana-client = 4.1.1`.
  - Rust SDK/program crate surface from Cargo registry: `solana-sdk = 4.0.1`,
    `solana-program = 4.0.0`.
  - Frankendancer mainnet-ready release surface: `v0.913.40003`.
  - Firedancer full validator release surface: Testnet `v1.0.0`, not Mainnet
    Beta.
- The extension already has a Solana lane outside `game/`: entropy settings in
  `extensions/chthonic-archive/package.json` plus the native
  `entropy-ledger-host` sidecar. This is the older Loom/Entropy/sidecar lane the
  user is pointing at. It is not random; it was a prior functional experiment
  with polyglot sidecars and Solana settlement.
- First Solana Rust-lane modernization is now executed in
  `extensions/chthonic-archive/native/Cargo.lock`: latest compatible granular
  Solana crates inside the existing architecture, no reintroduction of Anchor
  or `solana-rpc-client`.
  - `solana-hash 4.2.0 -> 4.4.0`
  - `solana-transaction 4.0.0 -> 4.1.5`
  - `solana-message 4.0.0 -> 4.2.4`
  - `solana-pubkey` consolidated from dual `3.0.0` + `4.1.0` to single `4.2.0`
  - `solana-instruction 3.3.0 -> 3.4.0`
  - `solana-signature 3.3.0 -> 3.4.1`
  - `solana-signer 3.0.0 -> 3.0.1`
  - `solana-system-interface 3.1.0 -> 3.2.0`
  Verified by `cargo check -p entropy-ledger-host --target x86_64-pc-windows-msvc`
  and `cargo tree -p entropy-ledger-host -i solana-pubkey`, which now shows one
  `solana-pubkey v4.2.0` shared by the host, instruction, signer, and
  transaction stack.
- The extension Solana/entropy runtime settings are now emigrated to the local
  toolchain surface without making a VSIX lane. `activateSidecars.ts` still
  honors the contributed VS Code settings as fallback, but first reads
  `process.env`, then `extensions/chthonic-archive/.chthonic/mise.toml [env]`
  through `src/runtime/localLaneConfig.ts`. The live migrated values match the
  current workspace intent: native lanes allowed, entropy off, polyglot/Solana
  settlement off, ledger mode `bankrun`, RPC `http://127.0.0.1:8899`.
  Verified by direct helper load plus TypeScript 6.0.3 `--noEmit` and Bun
  bundle smoke against temp output, not by writing `dist/` or packaging VSIX.

## Do Not Re-Argue First

- Do not spend the next batch proving that active live paths should use `eldno`.
  The user has already supplied the migration fact.
- Do not run another global `erdno`/`eldno` replacement.
- Do not invent a game Solana dependency silently. Do create the game Solana
  lane explicitly if that is the intended trajectory: pick the crate surface
  (`solana-client`/`solana-sdk`/`solana-program`/SPL/Anchor), runtime target
  (read-only RPC probe, wallet/signing, program interface, or validator-adjacent
  tooling), and acceptance tests.
- Do not commit the current staged tree as one batch. The index contains a
  mixed lane: CI code, generated/audit surfaces, CLAUDEBASE routing, historical
  text rewrites, deleted handoff files, binary/probe outputs, and untracked
  files referenced by staged files.

## Clearance Batch

Before resuming Fable modernization, do this narrow clearance:

1. **Repair law/provenance text only.** In the Fable handoff, restore `erdno`
   where it is historical evidence: prior account, stale migration event,
   `erdno` -> `eldno` warning, and direct scan wording. Leave live-path
   replacements alone.
2. **Resolve staged/untracked dependency edges.** If `ci/checks/common_bloat_and_vendored.ts`
   remains imported by staged CI files, it must be staged and validated with the
   same SID/envelope standard as the other CI checks. If `MANIFEST.md` points to
   `The-Savant-Free-Agency-Logging.md`, that file must be tracked or the pointer
   must not land yet.
3. **Classify `.vscode/audit_*.json`.** Decide whether those audit files are
   generated output and belong in the common exemption list, or source-like
   config that must be repaired. Do not silence them by hiding the whole
   `.vscode/` directory.
4. **Update Solana detector truth.** The runtime setting bridge is in place;
   detector truth is still separate. `verify-host.ts` may say the active CLI is
   OK when PATH proves v4.1.1, but it should report the install-root mismatch as
   WARN and keep installer usability separate from CLI usability.
5. **Run staged CI after the above, not before.** The target is not "all green";
   it is no contradictory green: every OK/WARN/INFO must disclose what evidence
   it used.

## Resume Gate

Only resume the larger modernization lane when a fresh pass can state, without
contradiction:

- what is committed versus only staged versus only untracked;
- which live paths are current-machine truth;
- which historical paths are preserved as history;
- which generated outputs are exempt and why;
- which Solana/Agave path is active, which config root is stale/mismatched, and
  which installer/update lane is actually usable.

Until then, this state is a trainstop clearance state, not a Fable continuation
state.
