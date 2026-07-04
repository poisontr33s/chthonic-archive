# Claude Design — first install

After Phase 0 lands, this is the path a fresh workspace takes.

## Sideload the .vsix

```pwsh
cd claude-design
bun install
bun run package
code-insiders --install-extension claude-design.vsix
```

## First workspace open

1. Open a folder that has (or will have) a `designs/` directory.
2. Claude Code activates Design via `extensionDependencies`.
3. Open the Claude Code activity bar item — two new trees appear: **Designs** and **Asset Review**.
4. Status bar gains a `✦ Design` pill on the right.
5. Run **`Claude Design: Open Preview Beside`** — webview opens to the right of the active editor.
6. Save any file under `designs/` — preview reloads instantly.

## Phase 0 limits (intentional)

- No chat surface yet (Phase 1).
- Asset review TreeView reads `manifest.json` but cannot yet write back (Phase 2).
- Tweaks toggle exists but `__edit_mode_set_keys` write-back is Phase 3.
- Cross-project design-system mount is Phase 4.

These limits are the *point* of Phase 0 — prove the splice works before adding feature surface.

## Verifying the splice

Run `Claude Code: Sign In` if you haven't. Then in any chat with Claude Code:

```
/extensions
```

You should see `claude-design` listed as a dependent extension. If you don't, the activation guard tripped — likely Claude Code wasn't signed in when Design activated. Re-sign-in and reload window.
