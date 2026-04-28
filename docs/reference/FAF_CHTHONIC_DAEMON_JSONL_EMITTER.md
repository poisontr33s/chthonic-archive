<!--
@SID:           REF_FAF_CHTHONIC_DAEMON_JSONL_EMITTER_V1
@Type:          FAF Application - Gate H next-pass frame
@Context:       Follow-on to Chthonic Archive Extension Phase 3 modularization
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF.md
@Filed:         2026-04-28
-->

# FAF Application: Chthonic Daemon JSONL Emitter

**Version:** v0.2
**Status:** Frame issued - execution pending Codex 5.5 pass
**Primary challenge:** Close Gate H by making `transport=jsonl` a real SynapseBridge fallback, not a disabled branch.

---

## 0a. Current State Anchor (read first)

Phase 3 modularization closed cleanly in the prior pass. The relevant ground truth Codex 5.5 must accept without re-derivation:

- `extensions/chthonic-archive/src/extension.ts` is now 130 lines; `activate()` body is 38 lines.
- `src/activation/{activateViews,activateCommands,activateSidecars,activateStatus,activateCockpit,types}.ts` exist and own their respective lanes.
- `LaneRegistry` publishes `chthonicDaemon`, `synapseShm`, `entropyLedgerHost`, `entropyWorker` (among others) and writes `${globalStorage}/lane-state.json`.
- `apps/chthonic-next/app/api/lane-state/route.ts` and `apps/chthonic-next/app/page.tsx` consume the snapshot.
- `manifest/extension_phase3_*.json` (gate ledger) and `manifest/failures.jsonl` (Gate H entry) are already written.
- `bun run compile`, `bun run test:e2e`, `bun run web:typecheck`, `bun run web:build` all pass. `bunx tsc --noEmit` has one pre-existing baseline error in `src/entropy/entropyWorkerClient.ts:155`; this is out of scope.
- Gate H is the only `impossible_currently_boundary` left from the Phase 3 ledger.

This pass narrows to closing Gate H. Nothing else in the extension is in scope.

---

## 0. Retargeting Declaration

The Phase 3 extension FAF left Gate H as an `impossible_currently_boundary`.
This application narrows the next pass to one membrane:

> `chthonic-daemon --transport=jsonl` must emit sediment data over stdout JSONL, and `SynapseBridge` must parse that stream into the same `onChunk` callback used by shared memory.

No UI redesign, no reactor re-architecture, no tensor runtime wiring, and no ACP/SDK chat lane work is in scope.

---

## 1. Challenge Statement

Current state:

- `extensions/chthonic-archive/src/reactor/synapseBridge.ts` returns early for `transport=jsonl`.
- `extensions/chthonic-archive/native/chthonic-daemon/src/main.rs` has `ReactorTransportMode::Jsonl`, but selection is env-driven and `reactor/sediment_synapse` writes zero chunks when shared memory is absent.
- `reactor/sediment_stream` already proves stdout JSONL sediment chunk notifications can exist, but the Synapse fallback path does not use them.

Required closure:

- Add a daemon CLI flag: `--transport=auto|shared_memory|jsonl`.
- When JSONL is selected, `reactor/sediment_synapse` must emit one JSONL sediment-slot payload per chunk to stdout.
- The payload must preserve the existing sediment binary contract through the `chthonic-synapse-schema` header/body shape, or a documented JSON envelope that round-trips to the same bytes.
- `SynapseBridge` must replace the disabled `jsonl` branch with a real child-process reader and deliver parsed chunks via `onChunk`.

---

## 2. False Success Ban

Gate H is not admitted because:

- `--transport=jsonl` is accepted by clap.
- `SynapseBridge.isReady()` returns true.
- The daemon prints any JSON line.
- `reactor/sediment_stream` still works.
- A unit test stubs `stdout` without spawning the real daemon.
- Shared memory still passes.

Success is admitted only when a smoke probe spawns the real daemon with `--transport=jsonl`, requests sediment through the fallback path, parses at least one emitted payload, and verifies that `SynapseBridge.drain(..., onChunk)` receives the same chunk count reported by the daemon.

---

## 3. Capability Ladder

| Level | Name | Meaning |
|-------|------|---------|
| L0 | Identified | Boundary exists in `manifest/failures.jsonl`. |
| L1 | Daemon flag | `chthonic-daemon --transport=jsonl` selects JSONL without env vars. |
| L2 | Daemon emits | `reactor/sediment_synapse` emits one JSONL sediment payload per chunk. |
| L3 | Bridge drains | `SynapseBridge` spawns/reads/parses JSONL and calls `onChunk`. |
| L4 | Smoke-clean | Native daemon smoke plus extension e2e pass with JSONL fallback enabled. |

No level may be skipped. If L2 cannot emit real chunks, keep the boundary open.

### Execution Order (load-bearing)

The four gates below are not interchangeable. Execute strictly in order:

1. **H1 first** — daemon CLI flag. Smallest, no behavior change to the existing shared-memory path. Lands as one Rust commit. Verifies clap parsing + mode reporting. The `CHTHONIC_REACTOR_TRANSPORT` env var must remain functional as a fallback so existing call sites do not regress.
2. **H2 second** — daemon-side JSONL emitter. Touches `reactor/sediment_synapse` only. Cannot proceed without H1 (no flag = no isolated test surface). Must preserve the binary contract from `chthonic-synapse-schema`: either re-emit the same bytes base64-encoded inside a JSON envelope, or document a JSON schema that round-trips losslessly to the same `PackedSedimentVertex` field set.
3. **H3 third** — TypeScript bridge reader. Replaces the disabled branch at `synapseBridge.ts:33-35`. Spawns the daemon as a child process, reads stdout line-by-line via `readline.createInterface`, parses each line, and feeds chunks into the existing `onChunk` callback. Must mark `LaneRegistry.set({name:'synapseShm', state:'DEGRADED', reason:'transport=jsonl fallback'})` when the JSONL path is active so the snapshot reflects degraded mode.
4. **H4 last** — end-to-end smoke. Native daemon smoke script (Rust or shell, lives under the native workspace) plus `bun run test:e2e` with `chthonic.reactor.transport=jsonl` set in the test config. Shared-memory path must remain preferred for `auto` and must remain green.

If H1 fails: stop. If H2 cannot emit real chunks: stop and keep the boundary open. Do not advance H3 against a stub.

---

## 4. Gate Ledger

### Gate H1 - Daemon CLI Transport

Question: Can `main.rs` expose `--transport=auto|shared_memory|jsonl` while preserving the existing `CHTHONIC_REACTOR_TRANSPORT` env fallback?

Probe: `chthonic-daemon --workspace <fixture> --transport=jsonl` starts and reports `reactor/synapse` mode `jsonl`.

### Gate H2 - JSONL Sediment Emitter

Question: Can `reactor/sediment_synapse` emit chunk payloads over stdout when shared memory is unavailable or explicitly bypassed?

Probe: send a JSON-RPC `reactor/sediment_synapse` request and assert stdout includes one payload line per reported chunk.

### Gate H3 - SynapseBridge Reader

Question: Can `SynapseBridge` replace the disabled branch with a child-process JSONL reader that feeds `onChunk`?

Probe: configure `chthonic.reactor.transport=jsonl`, execute `chthonic.reactorSediment`, and assert received chunk count is nonzero for a fixture workspace with sediment vertices.

### Gate H4 - End-to-End Smoke

Question: Does the fallback work without weakening shared-memory behavior?

Probe: run `bun run compile`, `bun run test:e2e`, and a native daemon JSONL smoke script. Shared memory remains preferred for `auto`.

---

## 5. Required Artifacts

- Rust: `extensions/chthonic-archive/native/chthonic-daemon/src/main.rs` CLI flag and emitter path.
- TypeScript: `extensions/chthonic-archive/src/reactor/synapseBridge.ts` JSONL reader.
- Smoke: daemon JSONL probe under `extensions/chthonic-archive/scripts/` or native workspace test tooling.
- Manifest: update `manifest/extension_phase3_gate_h_jsonl_boundary.json` from blocked to admitted only after L4.

---

## 6. Impossible-Currently Boundary

Current boundary remains valid until H2 exists:

```json
{
  "artifact_type": "impossible_currently_boundary",
  "gate": "synapse/jsonl_fallback",
  "claim": "SynapseBridge can drain sediment via JSONL stdio when shared-memory is unavailable",
  "observed_failure": "chthonic-daemon has no CLI --transport=jsonl flag and reactor/sediment_synapse emits zero chunks when shared memory is absent",
  "minimum_condition_to_reopen": "daemon emits one JSONL sediment payload per chunk when invoked with --transport=jsonl",
  "status": "blocked_not_closed"
}
```

When the minimum condition is met, reopen Gate H and run the ladder from L1 to L4.

---

## 7. What This Is Not

```
This handoff does not authorize daemon re-architecture beyond adding a CLI
  flag and a JSONL emit path inside reactor/sediment_synapse.
This handoff does not extend SynapseBridge beyond replacing the disabled
  jsonl branch with a real reader.
This handoff does not modify the chthonic-synapse-schema binary header.
This handoff does not touch the activation modules, LaneRegistry, or
  cockpit fetch landed in the Phase 3 pass.
This handoff does not weaken shared-memory as the preferred transport.
This handoff does not introduce a new Rust crate, a new TS package, or
  a new build tool.
```

What this handoff claims:

> Gate H can be closed by adding one CLI flag, one stdout JSONL emitter, one TypeScript child-process reader, and one end-to-end smoke. Each gate (H1, H2, H3, H4) admits at L4 only when its probe succeeds against the real daemon. The boundary stays open if H2 cannot emit real chunks against a real fixture workspace.

The boundary ledger is the artifact. The probe is the smoke run. The membrane is the LaneRegistry `synapseShm` lane reflecting `LIVE` (shared memory) or `DEGRADED` (jsonl). The impossible-currently boundary closes only when H4 admits.

No false success. No decoration. No mythology.

---

## 8. Codex 5.5 Invocation Frame

When the user pastes this document into a Codex 5.5 task prompt, the expected operating posture is:

- Treat `docs/reference/FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF.md` as the prior pass and §0a above as the current state. Do not re-derive.
- Pre-execution: emit `manifest/daemon_jsonl_baseline.json` recording (a) `chthonic-daemon --help` current output, (b) current `synapseBridge.ts` line range for the disabled branch, (c) snapshot lane state for `synapseShm` from `lane-state.json`. This is the rollback anchor.
- Per gate (H1, H2, H3, H4): emit `manifest/daemon_jsonl_<gate>.json` with `{gate, level_reached, status, evidence_files, smoke_evidence}`.
- Per gate: do not advance past L3 without a real-daemon spawn. Do not advance past L4 without `bun run test:e2e` green AND the native smoke script green.
- On H2 failure (cannot emit real chunks against fixture): rewrite the impossible-currently boundary in `manifest/failures.jsonl` with the new specific failure mode and STOP. Do not improvise an emit path.
- On H4 admission: update `manifest/extension_phase3_gate_h_jsonl_boundary.json` from `blocked_not_closed` to `admitted` with the H4 evidence files. Append the corresponding `admitted` entry to `manifest/failures.jsonl` (the ledger is append-only; do not edit prior entries).
- Produce one PR with four commits — one per gate. Commit messages: `feat(daemon): H1 add --transport CLI flag`, `feat(daemon): H2 emit JSONL sediment chunks to stdout`, `feat(synapse): H3 child-process JSONL reader`, `test(synapse): H4 end-to-end JSONL smoke`.
- Do not touch the activation modules, the cockpit route, the lane registry implementation, or `LANE_TEMPLATE.md`. Those are sealed by the prior pass.
- If the work expands beyond the four gates above (e.g. the schema needs to change, or the daemon needs a new dependency), STOP and add a new section §9 to this document describing the unforeseen requirement, then return for human review.

