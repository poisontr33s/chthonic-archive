# Chthonic Status Bridge

This extension is a compatibility/status bridge for legacy statusbar lanes.

## Role

- Keeps legacy command IDs available.
- Forwards commands to `chthonic-archive` runtime lanes.
- Exposes quick task commands for heavyweight checks.

## Routed Legacy Commands

- `chthonic.verifySSO_T` -> `chthonic.verifySSOT`
- `chthonic.runMetabolicCycle` -> `chthonic.slabHeal`
- `chthonic.showGPUStats` -> `chthonic.reactorSediment`

## Added Task Commands

- `chthonic.runHostVerify` -> runs `bun run verify:host` in `extensions/chthonic-archive`
- `chthonic.runVsAudit` -> runs `bun run audit:vs2026` in `extensions/chthonic-archive`

## Notes

- This bridge does not implement old UV/GPU/status logic directly.
- `chthonic-archive` remains the authoritative extension lane.
- Pre-bridge runtime is preserved at `src/statusbar_runtime_legacy.ts`.
- Legacy validation module is preserved at `src/hedonisticValidation.ts`.
- Snapshot metadata is preserved at `legacy.package.snapshot.json`.
