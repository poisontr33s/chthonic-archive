# Lane Template

## Lane Shape
Export one `register<LaneName>(context, deps)` or `activate<LaneName>(context, deps)` function.
Pass every dependency explicitly; do not read cross-cutting config inside handlers unless the lane owns that timing.
Use the paste lane as the baseline: `src/markdownPaste/register.ts`.

## Lane State Contract
Publish every state transition to `LaneRegistry` with a stable `name`, `state`, and useful `reason`.
Bind snapshot output through `src/runtime/laneState.ts`; do not write ad hoc JSON elsewhere.
Use `src/runtime/statusReport.ts` when runtimeStatus must summarize the lane.

## Test Contract
Add contributed commands to `scripts/e2e-extension-host.ts` `expectedCommands`.
Add smoke commands when execution is side-effect-safe and non-interactive.
For lifecycle lanes, assert the snapshot lane state after `chthonic.runtimeStatus`.

## What Not To Do
No module-level mutable state for activation dependencies.
No polling when VS Code or the lane already exposes an event source.
No silent native process start outside `chthonic.security.allowNativeSidecars`.
No bypass of `src/runtime/devAutoReload.ts` for reload behavior.
