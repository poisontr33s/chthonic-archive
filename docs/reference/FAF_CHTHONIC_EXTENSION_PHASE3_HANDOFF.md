# FAF Application: Chthonic Archive Extension — Phase 3 Modularization + Lane Closure

<!--
@SID:           REF_FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF_V1
@Type:          FAF Application — Codex 5.5 handoff frame
@Context:       Next-pass continuation of high-level-strategical-deep-book.md
@SessionOrigin: PHASE_1_2_4_5_LANDED_PHASE_6_PARTIAL
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, FAF_TABBYAPI_PY314_GPU_INFERENCE_HOST.md, ~/.claude/plans/high-level-strategical-deep-book.md
-->

**Version:** v0.1
**Status:** Frame issued — execution pending Codex 5.5 pass
**Primary challenge:** Modularize `extensions/chthonic-archive/src/extension.ts` activation surface and close the runtime-state telemetry loop without behavior regression.
**Plan source:** `~/.claude/plans/high-level-strategical-deep-book.md`
**FAF source:** [FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md](FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md)
**Filed:** 2026-04-28

---

## 0. Retargeting Declaration

The original FAF proving challenge:
> Ruby 4.0.3 on Windows 11 must be forced into a verified foreign-capability host.

This application retargets FAF to:
> **The chthonic-archive VS Code extension's monolithic `activate()` must be modularized, and its lane-state telemetry must be closed end-to-end, without breaking any of the 19 contributed commands or 6 GUI surfaces.**

The host language changes from Ruby to TypeScript. The foreign-capability stack changes from CUDA-via-Fiddle to the VS Code extension host API + the existing Rust native lane (`synapse-node`, `chthonic-daemon`, `entropy-ledger-host`). The membrane changes from the Windows DLL loader to the VS Code activation contract + `vscode.ExtensionContext.subscriptions` lifecycle. The False Success Ban, Capability Ladder, and Impossible-Currently Boundary schema are unchanged.

---

## 1. Challenge Statement

```
The chthonic-archive extension at extensions/chthonic-archive/ must complete:

  - Phase 3 (5 remaining activation extractions): activateViews,
    activateCommands, activateSidecars, activateStatus, activateCockpit.
  - Cockpit lane-state fetch wiring: apps/chthonic-next must read the
    LaneRegistry snapshot file written by the extension and replace the
    hardcoded "hot/warm/stable" pills.
  - JSONL fallback transport for SynapseBridge: re-enable the disabled
    transport=jsonl path with a real stdio reader against chthonic-daemon.
  - LANE_TEMPLATE.md: capture the paste-lane shape so future lanes follow it.

The starting state already has:

  - Phase 1 (honesty pass) landed: ParkedChatProvider removed.
  - Phase 2 (RuntimeLaneState) landed: LaneRegistry with EventEmitter,
    debounced JSON snapshot to ${globalStorage}/lane-state.json.
  - Phase 4 (hot-reload) landed: chthonic.dev.autoReload (default false)
    + dist/extension.js fs.watch -> reloadWindow.
  - Phase 5 (Rust lane closure) landed: native/dist/synapse-${platform}-${arch}.node
    packaged via .vscodeignore allowlist; bridge lookup order updated;
    build-synapse.ts emits platform-suffixed artifact.
  - Phase 6 (smoke coverage) partially landed: scripts/e2e-extension-host.ts
    asserts all 19 commands incl. chthonic.pasteRenderedAiMarkdown sentinel.
  - Phase 3 first extraction landed: src/runtime/statusReport.ts
    (ReactorReadiness, BridgeLaneStatus, RuntimeStatusInput,
    collectRuntimeLaneStates, collectRuntimeStatusRows, formatBridgeStatus).

The challenge is NOT:

  Re-architect the extension.
  Introduce a state library (Redux, Zustand, MobX).
  Convert the bun bundler to esbuild/webpack/vite.
  Add new Rust crates beyond what is in extensions/chthonic-archive/native/Cargo.toml.
  Wire tensor-runtime-host to actual TensorRT/cuDNN.
  Reactivate the parked ACP/SDK chat lanes.
  Rename chthonic.chatView (consumer churn — explicitly out of scope).
  Touch any file under .temple/ or game/.

The actual challenge is:

  Move code into modules without changing behavior. Close the snapshot
  loop. Re-enable the disabled fallback. Document the pattern. Each
  extraction passes the smoke gate before the next begins.
```

---

## 2. False Success Ban (extension translation)

A Phase 3 extraction is **not** admitted because any of these are true:

```
bun build src/extension.ts produced dist/extension.js without error.
bunx tsc --noEmit returned 0.
extensions/chthonic-archive/src/activation/activateViews.ts now exists.
The new module has the right number of registerWebviewViewProvider calls.
Code review says it looks right.
The 1200-line extension.ts is now 200 lines.
The 6 view providers are imported by the new module.
The lint passes.
A unit test of the new module passes in isolation.
A README says the extraction is complete.
```

Those facts may create candidate gates. They do not admit a successful extraction.

A successful extraction is admitted only when the smoke gate (`bun run test:e2e`) reports the same command set, view-provider activation, and probe-execute results as the pre-extraction baseline, AND the LaneRegistry snapshot file has the same eight named lanes after `chthonic.runtimeStatus` runs.

---

## 3. Capability Ladder (per extraction)

| Level | Name | Meaning |
|-------|------|---------|
| L0 | Identified | The lane to extract is named in `~/.claude/plans/high-level-strategical-deep-book.md` Phase 3. |
| L1 | Moved | Code is physically in `src/activation/<lane>.ts`; old file no longer contains it. |
| L2 | Compiles | `bun run compile` and `bunx tsc --noEmit` both succeed (modulo two pre-existing `stringifyError`/`unknown` errors that pre-date this work). |
| L3 | Smoke-clean | `bun run test:e2e` passes — all 19 commands present; smokeCommands execute without throwing. |
| L4 | Behavior-clean | The `chthonic.runtimeStatus` smoke run produces a `lane-state.json` whose lane set matches the pre-extraction baseline byte-for-byte (modulo `updatedAt` and `emittedAt` timestamps). |

**No gate may skip levels silently.** Each extraction must report its own L0→L4 ladder in the gate ledger.

---

## 4. Gate Ledger

### Gate P3-A — `activateViews` extraction
**Question:** Can the six `registerWebviewViewProvider` / `registerTreeDataProvider` calls be moved to `src/activation/activateViews.ts(context, deps)` without changing the order or arguments of registration?

**Targets in current file:** [extensions/chthonic-archive/src/extension.ts:37](/extensions/chthonic-archive/src/extension.ts#L37) (chatView→AnkhReferenceProvider), [:55](/extensions/chthonic-archive/src/extension.ts#L55) (loomView), [:61](/extensions/chthonic-archive/src/extension.ts#L61) (stylusView), [:126](/extensions/chthonic-archive/src/extension.ts#L126) (abyssalView + EntropyDecorationProvider), [:565](/extensions/chthonic-archive/src/extension.ts#L565) (themeView), [:641](/extensions/chthonic-archive/src/extension.ts#L641) (statusView).

**Required artifacts:**
- **Probe:** `bun run test:e2e` post-extraction — must list all six view types registered.
- **Binding:** `activateViews(context, { workspaceRoot, outputChannel, laneRegistry, loomProvider, ... })` — explicit parameter object; no module-level mutable state.
- **Membrane:** Same registration ORDER as current file; provider constructors receive same arguments. Any change in order or arguments fails the gate.

**Failure handling:** If any provider fails to register, mark the corresponding lane in `RuntimeLaneState` as `DEGRADED` with the thrown reason. Never let a provider error escape the orchestrator.

**Closure condition:** L4 reached.

---

### Gate P3-B — `activateCommands` extraction
**Question:** Can the 18 `vscode.commands.registerCommand` calls (plus the markdown paste command at `register.ts:63`) be partitioned into domain-grouped registrations under `src/activation/activateCommands.ts` without changing command IDs or handler closures?

**Domain groups (suggested):**
- layout: `activateCockpit`, `deepFocus`, `restoreOrder`
- entropy: `entropyRefresh`, `refreshRustification`, `reactorSediment`
- reactor: `annoDetect`
- slab: `slabHeal`
- cockpit: `openWebCockpit`, `startWebCockpit`
- training: `openBunTrainingDocs`
- restart: `postRestartVerify`, `restartGate`
- runtime: `runtimeStatus`
- theme: `switchTheme`
- policy: `verifySSOT`
- status: `refreshStatus`
- stylus: `openStylusInput`

**Required artifacts:**
- **Probe:** `scripts/e2e-extension-host.ts` `expectedCommands` list of 19 entries — already in place. Smoke run must return all 19.
- **Membrane:** Each command's handler closure currently captures `outputChannel`, `chthonicConfig`, `workspaceRoot`, `entropyEnabled`, etc. The extraction MUST pass these via an explicit `CommandDeps` parameter object, not via re-reading config inside each module. Re-reading config is False Success — it changes evaluation timing.

**Closure condition:** L4 reached. Smoke run includes `chthonic.runtimeStatus` (already in `smokeCommands`) which validates the LaneRegistry path through this module.

---

### Gate P3-C — `activateSidecars` extraction
**Question:** Can `EntropyWorkerClient`, `AnnoClient`, `PolyglotEntropyOrchestrator`, `SynapseBridge`, `SelfHealingLoop` be lifecycle-managed under `src/activation/activateSidecars.ts(context, deps)` such that none instantiates when `chthonic.security.allowNativeSidecars=false`?

**Critical predicate:** Read [extensions/chthonic-archive/src/extension.ts:70](/extensions/chthonic-archive/src/extension.ts#L70) (`allowNativeSidecars`) and any nearby `entropyEnabled` / `slabSelfHealingEnabled` gates. The extraction must preserve every `if (allowNativeSidecars)` and `if (entropyEnabled)` guard exactly. **One missing guard = silent activation = security regression.**

**Required artifacts:**
- **Probe:** New `scripts/e2e-extension-host.ts` test case launched with `chthonic.security.allowNativeSidecars=false` (already the default), then probe `LaneRegistry.get('native-sidecars').state === 'DISABLED'` and `LaneRegistry.get('synapseShm').state === 'PARKED'`. Currently the registry only fires lanes after `chthonic.runtimeStatus` runs — extending it to fire on activation is part of this gate.
- **Membrane:** A `SidecarSupervisor` interface that exposes `start()` / `stop()` / `state(): RuntimeLaneState` per sidecar. The supervisor publishes to `LaneRegistry`. No sidecar may construct itself outside the supervisor.
- **Impossible-Currently:** None at this gate. All sidecars exist and have current call sites; this is a relocation, not new capability.

**Closure condition:** L4 reached. Snapshot file shows `synapseShm`, `chthonicDaemon`, `entropyLedgerHost`, `entropyWorker` lanes with correct gated states under both flag values (false→PARKED/DISABLED, true→READY or LIVE).

---

### Gate P3-D — `activateStatus` extraction
**Question:** Can the two status bar items at [extensions/chthonic-archive/src/extension.ts:596](/extensions/chthonic-archive/src/extension.ts#L596) (`showSSOTHash`, fingerprint) and [:614](/extensions/chthonic-archive/src/extension.ts#L614) (`showLineage`, lineage) be moved to `src/activation/activateStatus.ts` while keeping their default-off semantics?

**Required artifacts:**
- **Probe:** With both `chthonic.showSSOTHash` and `chthonic.showLineage` at their defaults (`false`), `vscode.window.statusBarItems` enumeration must contain neither. Toggle each to `true`, fire `onDidChangeConfiguration`, observe item appearance.
- **Membrane:** Both items must subscribe to `LaneRegistry.onDidChange('policyOracle')` (for the fingerprint) and to a new `git-lineage` lane (for the branch label). The current 6-second polling interval at `extension.ts:624` must be either removed (event-driven) or moved to the new module unchanged. Choose one explicitly; do not leave both.

**Closure condition:** L4 reached. New gate sub-test toggles `chthonic.showSSOTHash` and asserts the status bar item appears within 200 ms.

---

### Gate P3-E — `activateCockpit` extraction
**Question:** Can the web cockpit panel builder at [extensions/chthonic-archive/src/extension.ts:741-885](/extensions/chthonic-archive/src/extension.ts#L741-L885) be extracted to `src/activation/activateCockpit.ts` with the iframe CSP and `frame-src` rules preserved?

**Required artifacts:**
- **Probe:** Run `chthonic.openWebCockpit` in the smoke harness. The webview's HTML must contain the same `<iframe>` `src` and CSP `frame-src` directives as today (string-equality check on the generated HTML).
- **Membrane:** The cockpit URL resolver `resolveWebCockpitUrl(chthonicConfig)` must move with the panel; do not duplicate.
- **Coupling note:** This module also owns the `chthonic.startWebCockpit` terminal-spawn command if the activateCommands extraction (Gate B) places it here instead of under `cockpit:`. Choose one; document the choice.

**Closure condition:** L4 reached.

---

### Gate P3-F — Activation orchestrator
**Question:** Can `extension.ts::activate(context)` be reduced to ≤ 60 lines that wire the registry, paste lane, dev-reload, and the five activation modules above, with each module returning its disposables?

**Required artifacts:**
- **Probe:** `wc -l src/extension.ts` — must be ≤ 200 lines (target ≤ 150). Current baseline after Phase 1+2+5+first-extraction: TBD — record the pre-extraction line count in the gate ledger.
- **Binding:** A single `ActivationDeps` type in `src/activation/types.ts` (or in `runtime/laneState.ts`) carrying `context`, `outputChannel`, `workspaceRoot`, `chthonicConfig`, `laneRegistry`, and the cross-cutting providers (`loomProvider`). Each `activateX(context, deps)` returns `void`; disposables are pushed via `context.subscriptions.push(...)` inside the module.
- **Membrane:** `activate()` must wrap each module in `try/catch` — a thrown module marks its lane `DEGRADED` and never propagates. The orchestrator never throws past `activate()`.

**Closure condition:** L4 reached. Smoke gate green, line count met, every module's failure path produces a `DEGRADED` snapshot entry.

---

### Gate G — Cockpit lane-state fetch
**Question:** Can `apps/chthonic-next/app/page.tsx` replace its hardcoded "hot/warm/stable" pills with a live read of the LaneRegistry snapshot?

**Targets:** [apps/chthonic-next/app/page.tsx](/apps/chthonic-next/app/page.tsx) (the Rust Reactor / Solana Stream / Policy Oracle pills); the snapshot file at `${globalStorage}/lane-state.json` (already written by Phase 2).

**Required artifacts:**
- **Probe:** A Next API route at `apps/chthonic-next/app/api/lane-state/route.ts` that reads the snapshot path via an env var (`CHTHONIC_LANE_STATE_PATH`, set by the extension when it spawns `bun run web:dev` in [extension.ts:445](/extensions/chthonic-archive/src/extension.ts#L445)). Returns the snapshot JSON. The page hits `/api/lane-state` with revalidation = 1s.
- **Binding:** Extension's `chthonic.startWebCockpit` command sets `CHTHONIC_LANE_STATE_PATH` in the spawned terminal env. The route reads the file via `node:fs/promises`.
- **Impossible-Currently:** If the Next dev server is launched outside the extension (user runs `bun run web:dev` manually without the extension running), the env var is absent. Record this as `impossible_currently_boundary` with `minimum_condition_to_reopen = "extension is running and has emitted at least one lane-state snapshot"`. The page must render a "no snapshot yet" placeholder rather than crashing.
- **Membrane:** No `fetch('file://...')` from the browser. The Node API route is the only filesystem reader.

**Closure condition:** Page renders three pills whose colors and labels are derived from `lanes['chthonicDaemon']`, `lanes['entropyLedgerHost']`, `lanes['policyOracle']` (or whichever names the snapshot uses; reconcile with the lane set in [src/runtime/statusReport.ts](/extensions/chthonic-archive/src/runtime/statusReport.ts)).

---

### Gate H — JSONL fallback transport
**Question:** Can the disabled `transport=jsonl` branch at [extensions/chthonic-archive/src/reactor/synapseBridge.ts:33-35](/extensions/chthonic-archive/src/reactor/synapseBridge.ts#L33-L35) be replaced with a real stdio JSONL reader against `chthonic-daemon`?

**Current state:** The shared-memory transport is admitted (Phase 5). The JSONL branch is a stub: it logs `[synapse] disabled by transport=jsonl` and returns. There is no daemon-side stdio JSONL emitter.

**Required artifacts:**
- **Probe:** Daemon-side: spawn `chthonic-daemon --transport=jsonl` and assert it emits one JSON line per sediment slot to stdout. Bridge-side: read the spawned process's stdout, parse JSONL, deliver chunks via the same `onChunk` callback that shared-memory uses.
- **Impossible-Currently (current):** The daemon does not yet expose a `--transport=jsonl` mode. This gate cannot be admitted until the daemon is extended.
  ```json
  {
    "artifact_type": "impossible_currently_boundary",
    "gate": "synapse/jsonl_fallback",
    "claim": "SynapseBridge can drain sediment via JSONL stdio when shared-memory is unavailable",
    "observed_failure": "chthonic-daemon has no --transport=jsonl flag; lib.rs only emits to shared memory",
    "proof": "extensions/chthonic-archive/native/chthonic-daemon/src/main.rs",
    "minimum_condition_to_reopen": "chthonic-daemon emits one JSONL line per SedimentSlotHeader to stdout when invoked with --transport=jsonl",
    "upstream_dependency": "chthonic-daemon stdio emitter (Rust)",
    "next_probe": "daemon_jsonl_emit_smoke_inside_native_workspace",
    "status": "blocked_not_closed"
  }
  ```
- **Membrane (TS-side, ready now):** Once the daemon emitter exists, the bridge spawns the daemon as a child process, parses stdout line-by-line, and marks `LaneRegistry.set({name:'synapseShm', state:'DEGRADED', reason:'fallback transport=jsonl'})`.

**Closure condition:** Either (a) admit at L4 once the daemon is extended, or (b) leave as `impossible_currently_boundary` with the reopen condition explicit. Do NOT delete the JSONL branch.

---

### Gate I — `LANE_TEMPLATE.md` (Phase 6 closure)
**Question:** Can the paste-lane shape be captured as a single-page template that future lanes (e.g. a hypothetical `policyOracleLane`) can follow without ceremony?

**Required artifacts:**
- **Binding:** `extensions/chthonic-archive/docs/LANE_TEMPLATE.md` referencing the four existing exemplars: [src/markdownPaste/register.ts](/extensions/chthonic-archive/src/markdownPaste/register.ts) (the gold-standard pattern), [src/runtime/devAutoReload.ts](/extensions/chthonic-archive/src/runtime/devAutoReload.ts), [src/runtime/laneState.ts](/extensions/chthonic-archive/src/runtime/laneState.ts), [src/runtime/statusReport.ts](/extensions/chthonic-archive/src/runtime/statusReport.ts).
- **Required sections:** (1) lane shape (export a `register<LaneName>(context, deps)` function), (2) lane state contract (publish to `LaneRegistry` on every state transition), (3) test contract (smoke-runner expectedCommands entry, plus optional dedicated probe), (4) what NOT to do (no `vscode.workspace.onDidChange*` polling when an event source exists; no module-level mutable state).

**Closure condition:** Doc exists, ≤ 1 page, each section ≤ 5 lines.

---

## 5. Capability Ladder — Current State (handoff baseline)

| Capability | L0 | L1 | L2 | L3 | L4 | Status |
|------------|----|----|----|----|-----|--------|
| Phase 1 honesty pass | ✅ | ✅ | ✅ | ✅ | ✅ | **admitted** — ParkedChatProvider removed |
| Phase 2 LaneRegistry | ✅ | ✅ | ✅ | ✅ | ✅ | **admitted** — runtimeStatus publishes 12 lanes; snapshot writes |
| Phase 4 dev autoReload | ✅ | ✅ | ✅ | ✅ | ✅ | **admitted** — opt-in, default false |
| Phase 5 Rust packaging | ✅ | ✅ | ✅ | ✅ | ✅ | **admitted** — `native/dist/` allowlisted; bridge lookup updated |
| Phase 6 smoke coverage | ✅ | ✅ | ✅ | ✅ | ✅ | **admitted** — 19 commands asserted |
| Phase 3 first extraction (statusReport) | ✅ | ✅ | ✅ | ❓ | ❓ | **L2 admitted** — compiles; smoke not yet rerun against this checkpoint |
| Phase 3 P3-A activateViews | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** — identified, not started |
| Phase 3 P3-B activateCommands | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |
| Phase 3 P3-C activateSidecars | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |
| Phase 3 P3-D activateStatus | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |
| Phase 3 P3-E activateCockpit | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |
| Phase 3 P3-F orchestrator | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** — gated on A–E |
| Gate G cockpit fetch | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |
| Gate H JSONL fallback | ✅ | ❌ | ❌ | ❌ | ❌ | **L0 / impossible_currently** — daemon-side missing |
| Gate I LANE_TEMPLATE.md | ✅ | ❌ | ❌ | ❌ | ❌ | **L0** |

---

## 6. Membrane Inventory (extension translation)

| Membrane | Purpose | Current State |
|----------|---------|---------------|
| `RuntimeLaneState` enum | Single vocabulary for lane status across views, status bar, snapshot | Active — defined in [src/runtime/laneState.ts](/extensions/chthonic-archive/src/runtime/laneState.ts) |
| `LaneRegistry.bindSnapshotFile` | Debounced JSON flush guards against tearing reads | Active — 250 ms debounce |
| `chthonic.security.allowNativeSidecars` default `false` | Master kill-switch; sidecars never auto-start | Active — [package.json:388](/extensions/chthonic-archive/package.json#L388) |
| `.vscodeignore` allowlist for `native/dist/**` | Native artifacts ship deterministically, not by accident | Active — [.vscodeignore](/extensions/chthonic-archive/.vscodeignore) |
| `bun build --watch` + `chthonic.dev.autoReload` | Hot-reload is opt-in; never reloads window for non-developers | Active — default false |
| `e2e-smoke-runner.cjs` `withTimeout` | Smoke commands cannot hang the test harness | Active — 30 s default |
| `ActivationDeps` (Phase 3 P3-F) | No module-level mutable state; everything passes through `activate()` | **Required** — to be created in Phase 3 |
| `SidecarSupervisor` (Phase 3 P3-C) | One owner per native sidecar; LaneRegistry is single source of truth | **Required** |

---

## 7. Failure-to-Artifact Compiler (extension translation)

| Failure | FAF Artifact |
|---------|-------------|
| `vscode.commands.getCommands(true)` missing a chthonic.* entry post-extraction | Smoke gate failure → revert + investigate; do not patch the test |
| `LaneRegistry` missing a lane after extraction | Snapshot drift gate → diff snapshot vs. baseline; missing lane is a real bug |
| Webview registers but `resolveWebviewView` never fires | View-activation probe gate; webview lazy-resolve must be respected |
| Sidecar instantiates with `allowNativeSidecars=false` | Security regression — extraction MUST be reverted |
| `extension.ts` line count grows after a Phase 3 extraction | Wrong direction — gate failure |
| Status bar item appears with `showSSOTHash=false` | `default-off` membrane breached |
| Cockpit page crashes when snapshot file absent | Missing impossible-currently boundary on Gate G |
| `transport=jsonl` deletes the disabled branch | False closure — gate H must remain `impossible_currently` until daemon-side lands |
| `bun run test:e2e` flake | Probe-infrastructure failure (gate test of the test); fix the harness, not the suite |
| Pre-existing `tsc` errors (`stringifyError`, `unknown` catch) regress | Out of scope; do not touch unless your edit caused new ones |

---

## 8. Execution Order (load-bearing)

The five Phase 3 extractions are not interchangeable. The order minimizes regression risk:

1. **P3-D `activateStatus`** first — smallest, cleanly bounded, low coupling. Proves the pattern with negligible blast radius.
2. **P3-A `activateViews`** — view registrations are dispose-safe and have explicit smoke coverage.
3. **P3-E `activateCockpit`** — large but isolated; the panel builder is the single biggest closure block.
4. **P3-B `activateCommands`** — touches every domain; do this only after A/D/E are green so each command lands in a known-stable surrounding.
5. **P3-C `activateSidecars`** — highest risk (security predicate, lane-state coupling); do last when the registry and supervisor pattern are proven by predecessors.
6. **P3-F orchestrator** — once A–E are extracted, `activate()` becomes a wire-up shell. This is the closure step.

After P3-F: **Gate I** (LANE_TEMPLATE.md) — write while the pattern is fresh. Then **Gate G** (cockpit fetch). **Gate H** (JSONL) remains `impossible_currently` until daemon-side work is scheduled.

---

## 9. What This Is Not

```
This handoff does not authorize re-architecture.
This handoff does not deviate from ~/.claude/plans/high-level-strategical-deep-book.md.
This handoff does not extend scope to ACP/SDK chat lanes, tensor-runtime-host,
  cockpit visual redesign, or Codex/Gemini bridges.
This handoff does not weaken the False Success Ban for "looks right" extractions.
```

What this handoff claims:

> The Phase 3 modularization, the cockpit lane-state fetch, the JSONL boundary
> declaration, and LANE_TEMPLATE.md form a closeable, gate-validated work
> package on top of the Phase 1+2+4+5+6-partial baseline.
>
> Each extraction passes L0 → L4 before the next begins. The smoke gate is
> the entry condition for promoting a lane from L2 to L3. The snapshot
> diff is the entry condition for L4. The orchestrator step (P3-F) is
> rejected unless A–E are all L4.

The boundary ledger is the artifact.
The probe is the smoke run.
The membrane is the LaneRegistry + ActivationDeps + SidecarSupervisor.
The impossible-currently boundary is Gate H until the daemon emits JSONL.

No false success. No decoration. No mythology.

---

## 10. Codex 5.5 Invocation Frame

When the user pastes this document into a Codex 5.5 task prompt, the expected operating posture is:

- Treat `~/.claude/plans/high-level-strategical-deep-book.md` as the immutable plan; this **FAF** is the failure-aware framing of that plan's deferred work.
- Pre-execution: emit a baseline snapshot of `extension.ts` line count, `bun run test:e2e` result, and `lane-state.json` lane set. Record under `manifest/extension_phase3_baseline.json` (create the manifest dir if needed).
- Per gate: emit `manifest/extension_phase3_<gate>.json` with `{gate, level_reached, status, evidence_files, smoke_diff}`.
- Per gate: do not advance past L3 without a green smoke run; do not advance past L4 without a snapshot diff equal to the baseline for the lane set.
- On any unexpected failure: append `{artifact_type: "impossible_currently_boundary", ...}` to `manifest/failures.jsonl` with the reopen condition. Do not improvise.
- On completion of P3-F: produce a single PR with one commit per gate (six commits for P3-A through P3-F, plus optional separate commits for Gate G and Gate I).
- Gate H stays open as a tracked impossible-currently entry; do not ship code that pretends to admit it.
