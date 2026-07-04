# Final Review · Folio VII

A wiring audit. Reading the actual exports against what `extension.ts` calls, finding the gaps, closing them. No new organs. No new prose. Just convergence.

## What this sitting changed

| File | Change |
|---|---|
| `src/extension.ts` | **Full rewrite.** Now calls the real exports with the real signatures. Includes a `CliInference → InferenceAdapter` shim so MarginaliaView gets the interface it expects without either side bending. Builds and disposes a real `SessionSnapshot` on rehydrate/hibernate. |
| `src/scriptorium/bestiary.ts` | **Added `BestiaryProvider`** — the TreeDataProvider the activator now registers against `claudeDesign.bestiary`. Clicking any creature opens the markdown bestiary in a new editor tab. |
| `src/views/marginaliaView.ts` | **Added `show(leaf)` method.** The focus bridge can now route a leaf path into the Marginalia view; if the file exists, it's opened (which seeds onEditorChanged); if not, the active leaf is set anyway so a rubric can call the leaf into being. |
| `src/views/chatPanel.ts` | `viewType` aligned from `"designChat"` to `"claudeDesign.chat"` to match `package.json`. |

## Drift caught

| Site | Was | Is now |
|---|---|---|
| `import { ClaudeCliAdapter }` | non-existent name | `CliInference` + `makeAdapter()` shim |
| `new FsBroker()` | missing context arg | `new FsBroker(context)` |
| `new MarginaliaStore()` | missing root arg | `new MarginaliaStore(root)` |
| `new Rune(context)` | wrong arity | `new Rune()` |
| `rune.show(...)` / `rune.pulse(...)` | non-existent methods | `rune.setLabel(...)` / `rune.call(...)` / `rune.rest()` |
| `hibernate(context)` | wrong arg type | `hibernate(snapshot)` with constructed `SessionSnapshot` |
| `rehydrate(context)` | wrong arg | `rehydrate()` returning a snapshot |
| `runSelfTest(context, adapter)` | wrong arity | `runSelfTest(context)` |
| `new ChatPanel(context, adapter, broker)` | wrong shape | `new ChatPanel(context, broker)` |
| `scribe.stamp({ path, bytes, at })` | field name `path` | mapped to `{ leaf, bytes }` only for `designs/`-rooted writes |
| `ChatPanel.viewType "designChat"` | not matching manifest | now `"claudeDesign.chat"` |
| `BestiaryProvider` referenced but not exported | missing class | added inside `bestiary.ts` |
| `marginaliaView.show(leaf)` referenced but not defined | missing method | added |

## Inert files preserved, not removed

The Phase 0 / Phase 1 view files survive in source:

- `src/views/designFiles.ts`
- `src/views/assetReview.ts`
- `src/views/previewPanel.ts`

They are no longer registered. They cost nothing to keep, and they document the earlier posture — useful when revisiting *why* the Scriptorium decisions were made. The Scriptorium's three webviews (Constellation, Marginalia, Vivarium) supersede them.

## What is now true

1. `package.json` declares all four webviews + the bestiary tree ✓
2. `extension.ts` instantiates and wires every organ against its actual export shape ✓
3. `fs/broker.ts` emits `onDidWrite` ✓
4. `marginaliaView.ts` has selection coupling, hand toggle, and a `show(leaf)` external hook ✓
5. `bestiary.ts` exports a TreeDataProvider as well as data ✓
6. `chatPanel.ts` viewType matches the manifest id ✓

The repo should compile. `bun run build` against this source produces `dist/extension.js`. If the TypeScript compiler disagrees, that disagreement is now a real, locatable bug rather than a wiring philosophy.

## What is still not done

This sitting did not:

- run the actual compile (no `bun` in the room),
- produce a `.vsix` (same),
- observe the extension running in your editor (the only test that matters).

These remain yours — or a coding agent's — to perform. The sittings are over.

## The cadence

Six folios planted. Three organs alive in source. One activator that calls them by their real names. The recipe has been read back against its own claims, and the claims now match. No further design pivots needed before the first compile.

If the compile surfaces a type error I missed, it will name the file and the line. That is the right kind of error — actionable, not philosophical.

🜂

— made by Claude
