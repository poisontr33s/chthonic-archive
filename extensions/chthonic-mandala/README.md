# Chthonic Mandala Bridge

This extension is a compatibility bridge for legacy Mandala commands and views.

## Role

- Keeps historical command IDs alive.
- Routes interactions to `chthonic-archive` as the authoritative runtime lane.
- Avoids duplicate webview renderers and stale graph logic.

## Routed Commands

- `chthonic.openMandala` -> opens archive container and focuses `chthonic.loomView`
- `chthonic.openDependencyGraph` -> opens archive container and focuses `chthonic.abyssalView`
- `chthonic.openHealthReport` -> opens archive container and focuses `chthonic.statusView`
- `chthonic.mandalaBridge.switchTheme` -> forwards to archive theme command

## Notes

- This bridge intentionally contains no standalone topology renderer.
- Use `extensions/chthonic-archive` for heavyweight UI/runtime features.
- Pre-bridge source is preserved at `src/mandala_viewer_legacy.ts`.
- Snapshot metadata is preserved at `legacy.package.snapshot.json`.
