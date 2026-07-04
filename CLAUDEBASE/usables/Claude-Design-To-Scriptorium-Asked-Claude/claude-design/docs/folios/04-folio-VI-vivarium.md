# Folio VI — The Vivarium

The preview surface as illuminated plate. The third organ of the Scriptorium.

## What this sitting plants

| File | Role |
|---|---|
| `src/views/vivarium.ts` | Preview webview. Watches the active editor; when it's an `.html` or `.svg` leaf under `designs/`, renders it in a sandboxed iframe. Reloads on save. Three plate frames: bare, parchment, device. |
| `docs/folio-VI-vivarium.md` | This file. |

## Behavior

- **Activation.** When `vscode.window.activeTextEditor` lands on an `.html` or `.svg` file under `designs/`, the leaf is loaded as the specimen.
- **Reload.** `workspace.onDidSaveTextDocument` watches the active leaf. On save, the iframe `src` is rewritten with the new mtime as a cache-bust so the rendering refreshes immediately.
- **Sandbox.** Iframe is `sandbox="allow-scripts"`. No `allow-same-origin`. The specimen cannot read parent state, cannot reach VS Code APIs, cannot escape its enclosure.
- **Resource scope.** `localResourceRoots` is `designs/` + `assets/`. Anything the leaf references outside that scope fails to load. The vivarium is enclosed by design.
- **Plate frames.**
  - `bare` — no mat, no shadow. The specimen alone.
  - `parchment` — tinted mat, soft shadow, single hairline. The default. Reads as an illuminated plate.
  - `device` — dark bezel with a top notch, portrait aspect. Quick mobile-shape check.
  - Frame choice persists per workspace via `workspaceState`.
- **Theme inheritance.** Mat tone is `--vscode-editor-background` mixed toward a faint parchment. The plate's halo uses `--vscode-charts-orange` with a `--vscode-textLink-foreground` fallback. Persona theme switches recolor the room around the specimen live.

## What it doesn't yet do

- **Tweaks panel.** The `__edit_mode_*` postMessage protocol from claude.ai is not yet bridged. A leaf that posts `__edit_mode_available` should reveal a Tweaks affordance in the vivarium footer; flipping it on should pass `__activate_edit_mode` into the iframe, and `__edit_mode_set_keys` from the leaf should be merged into the `/*EDITMODE-BEGIN*/…/*EDITMODE-END*/` block on disk. This is the next stitch.
- **Viewport pinning.** A leaf with `viewport: { width: 1440 }` in the manifest should pin the specimen-shell to that width. Trivial — one read from the manifest at load.
- **Screenshot capture.** A footer button that snapshots the iframe to `.scriptorium/plates/<leaf>-<stamp>.png`. Useful for the bestiary sightings.

## How to register

In `package.json`, add to `contributes.views.claudeDesign`:

```json
{
  "id": "claudeDesign.vivarium",
  "name": "Vivarium",
  "type": "webview",
  "contextualTitle": "Vivarium"
}
```

In `extension.ts`:

```ts
import { VivariumView } from './views/vivarium';

context.subscriptions.push(
  vscode.window.registerWebviewViewProvider(
    VivariumView.viewType,
    new VivariumView(context)
  )
);
```

## The triptych

With this sitting the three organs are planted in source:

- **Constellation** — the field. What leaves exist, how they relate, which are youngest.
- **Marginalia** — the conversation. Per-leaf rubrics and gloss, on disk, diffable.
- **Vivarium** — the rendered specimen. The leaf as it appears when alive.

The Scriptorium now has shape. The remaining Folio VI courses (colophon stitching, selection coupling, hand toggle, Constellation↔Marginalia focus) are connective tissue between organs already alive.

🜂

— made by Claude
