<!--
@SID:           REF_FAF_CHTHONIC_DAEMON_JSONL_EMITTER_V1
@Type:          FAF Application - Gate H next-pass frame
@Context:       Follow-on to Chthonic Archive Extension Phase 3 modularization
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF.md
@Filed:         2026-04-28
-->

# FAF Application: Chthonic Daemon JSONL Emitter

**Version:** v0.1  
**Status:** Frame issued - execution pending  
**Primary challenge:** Close Gate H by making `transport=jsonl` a real SynapseBridge fallback, not a disabled branch.

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
