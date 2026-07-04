# Phase 1 — chat + write loop

What lands in this phase:

- **Chat panel** as a panel-area webview view (`designChat`). Streams from the `claude` CLI, renders user / Claude / tool lines, inherits VS Code theme through `--vscode-*` variables, no hard-coded colors.
- **FS broker** (`src/fs/broker.ts`) — every model write goes through one chokepoint. Workspace-relative allowlist: `designs/`, `assets/`, `.claude-design/`. Anything outside triggers a modal confirm. Per-path 200ms debounce against concurrent writers.
- **Streaming parser** stays in `src/inference/cli.ts` — line-buffered JSON over CLI stdout. `tool_use` events with `name=write_file` route through the broker; the preview redraws on the resulting URI.

### Wiring

`package.json` contributes:

```jsonc
"views": {
  "panel": [{ "type": "webview", "id": "designChat", "name": "Design Chat" }]
}
```

This sits next to TERMINAL / OUTPUT in the bottom drawer, the same posture as Terminal — one keystroke away, never the focus.

### What's deliberately deferred

- **No manifest writes yet.** Asset review still reads only. Phase 2.
- **No `__edit_mode_*` write-back.** The toggle fires the iframe message, but persistence to `/*EDITMODE-BEGIN*/` blocks is Phase 3.
- **No mention attachments** (dragging a workspace file into chat). Phase 3.

### Sanity check after install

1. Reload window.
2. Open the panel; the **Design Chat** tab is there.
3. Type "make a hello world page in designs/Hello.html"; on send, the CLI spawns, tokens stream, and `Hello.html` materializes in the tree.
4. Save the file — preview redraws.

If step 3 errors with "claude whoami failed", Claude Code isn't signed in.
