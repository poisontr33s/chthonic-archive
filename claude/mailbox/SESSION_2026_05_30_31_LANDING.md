# SESSION 2026-05-30/31 LANDING — FLUX shelf + satellite zombie-reap

Read-first re-entry memo for the post-restart session. The interface state is
intended to resume unchanged; this captures what's on the plate so we compound,
not re-derive.

## What's on the plate (live state)

Two work arcs this session, both additive, **nothing deleted** (ethos:
[[no-delete-from-seed]]).

### Arc 1 — FLUX sealed/SHA lane SHELVED (sha × FAF)
- Operator verdict: the sealed lane (`.engine.enc` + `.seal.json`, HKDF-SHA256 /
  AES-256-GCM, hw-bound, master-secret-gated) is overkill for a single operator
  on his own machine — "the SHA-scream." The plain lane (`flux1-dev-sm89.engine.plain`)
  loads + generates; that is the whole requirement.
- **Shelved, not deleted.** Both 22.18 GB engine artifacts, the C++ crypto
  modules, and the forge seal step are ALL retained. The `havePlain ? plain :
  sealed` router in `fluxService.ts` stays as the routing primitive.
- Tidied (references only): plan `~/.claude/plans/challenge-mutable-rabin.md`
  got a STATUS banner + withdrawn "delete the redundant engine" lines. Memory
  `project_flux_cpp_trt_pivot.md` carries the SHELF DECISION block.

### Arc 2 — satellite zombie-reap (the ~6 GB orphan)
Root cause: the bridge spawned the satellite with no Job Object, so a hard death
of the extension host orphaned the python satellite (Windows does not
cascade-kill children); a fresh window's Stop Backend couldn't reap a prior
zombie. Four gates, all code done:

| Gate | Surface | Status |
|------|---------|--------|
| 1 — C++ Job Object | `apps/chthonic-tensor-bridge/src/spawn_satellite.{h,cc}` | DONE + built. `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`; spawn `CREATE_SUSPENDED` → create job → assign → resume; `CloseSatelliteHandles` closes job last (kills survivors, also fixes graceful-stop-timeout leak). |
| 2 — TS startup pid-reap | `extensions/chthonic-archive/src/flux/fluxService.ts` | DONE, typechecks. `reapStaleSatellite()` called first in `register()`; reads `apps/flux-satellite/logs/flux-satellite.pid`, verifies alive + is-a-flux-satellite (CIM cmdline match) before `process.kill`. |
| 3 — compile-verify | both | DONE. `tsc --noEmit` exit 0; `cmake-js rebuild` exit 0; `.node` = 192,000 B (rebuilt 00:20:44), 9 exports load. |
| 4 — runtime smoke | operator | PENDING (needs F5/reload + see below). |

## What's live vs. pending after restart
- **Job Object fix is LIVE on window reload.** `loadBridge()` prefers
  `workspaceRoot/apps/chthonic-tensor-bridge/build/Release/chthonic_tensor_bridge.node`
  — the rebuilt path — over the installed v0.2.9 `native/` copy. The job logic
  lives entirely in the native addon, so even the stale installed JS bundle
  calls the new job-wrapped `startSatellite`. The primary zombie cure works now.
- **TS pid-reap (backstop only) NOT live yet.** Verified 2026-05-31: a plain
  `ext:sync:insiders` run did NOT update the installed bundle — its compile step
  apparently aborted (earlier step failed), AND plain sync has no install/copy
  step (install is gated behind `-Package` in `scripts/insiders-sync.ps1`).
  Source `dist/extension.js` has since been rebuilt (`bun run compile`, reap code
  present, 2 occurrences). To make the backstop live: `bun run
  ext:sync:insiders:package` (packages VSIX + installs), then reload. The
  installed `0.2.9/dist/extension.js` is the staleness check — grep it for
  `reapStaleSatellite`.

## Gate 4 smoke (operator)
1. Reload window (rebuilt bridge + synced TS load).
2. Job test: Start Backend → confirm ~6 GB python → **hard-kill** the host
   (close window / End Task, not graceful Stop) → python should vanish < 1 s.
3. Reap test: Start Backend → kill only python in Task Manager (leaves stale
   pid file) → reload → FLUX output channel shows `cleared stale pid file` or
   `reaped stale satellite`.

## Open trade-off (operator's call)
pid-reap auto-kills a verified-flux-satellite found alive with a stale pid file
on every activation. Only false-positive is the satellite running in TWO
Insiders windows at once (mooted by the `\\.\pipe\chthonic-flux` singleton). If
preferred, switch auto-kill → prompt. Not changed pending decision.

## Resume verification commands
```pwsh
# bridge rebuild (if source touched again)
$env:TENSORRT_ROOT = 'C:\Program Files\NVIDIA\TensorRT-10.16.1.11'
Set-Location 'C:\Users\eldno\chthonic-archive\apps\chthonic-tensor-bridge'; bunx cmake-js rebuild
bun -e "console.log(Object.keys(require('./')).sort().join(','))"   # 9 names
# extension typecheck
Set-Location 'C:\Users\eldno\chthonic-archive\extensions\chthonic-archive'; bunx tsc --noEmit -p .
# make TS pid-reap live
Set-Location 'C:\Users\eldno\chthonic-archive'; bun run ext:sync:insiders
```
