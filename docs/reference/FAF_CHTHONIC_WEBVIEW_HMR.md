<!--
@SID:           REF_FAF_CHTHONIC_WEBVIEW_HMR_V1
@Type:          FAF Application - Phase 4 webview HMR closure
@Context:       Closes the deferred half of Phase 4 from high-level-strategical-deep-book.md
@References:    FAF_FRAMING_AS_FUNCTION_METHODOLOGY.md, FAF_CHTHONIC_EXTENSION_PHASE3_HANDOFF.md, FAF_CHTHONIC_DAEMON_JSONL_EMITTER.md
@Filed:         2026-04-29
-->

# FAF Application: Chthonic Webview HMR

**Version:** v0.1
**Status:** Frame issued - execution pending Codex 5.5 pass
**Primary challenge:** Move the four webview HTML payloads out of TS string templates into `media/views/<surface>/{index.html,view.js}` and add a file-watcher → `postMessage({type:'reload'})` → `location.reload()` HMR loop, so iterating on webview UI no longer requires `Developer: Reload Window`.

---

## 0a. Current State Anchor (read first)

The daemon JSONL pass closed cleanly. Main as of `f5822ffe` contains:

- Phase 1-6 + Gates G/H/I shipped. Five honestly-parked items remain in `~/.claude/plans/high-level-strategical-deep-book.md` "Consolidation Status".
- `chthonic.dev.autoReload` (default `false`) already does **extension-host** reload-on-rebuild via `dist/extension.js` `fs.watch` → `workbench.action.reloadWindow`. This pass adds the **webview** half — granular reload of webview JS/HTML without window reload.
- `media/**` is already allowlisted in `.vscodeignore`.
- `media/` already contains `abyssalPane.js` and `wasm/` — Abyssal is partially externalized. Use this precedent for the new `media/views/<surface>/` shape; do not invent a different layout.
- Webview file sizes (TS lines, includes baked HTML/CSS/JS): `ankhReferenceView.ts` 535, `archiveAbyssalView.ts` 290, `loomView.ts` 286, `stylusInputView.ts` 379. Total 1490 lines, the bulk of which is HTML/CSS/JS payload that should leave the .ts files.
- All four webviews use the same CSP shape: `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}'`. Preserve this shape exactly when externalizing.
- `LaneRegistry` has lanes for views; the HMR watcher must publish a new lane (`webviewHmr`) reflecting `LIVE` (watcher active) / `PARKED` (autoReload disabled) / `DEGRADED` (watcher init failed).
- The pre-existing `entropyWorkerClient.ts:155` baseline tsc error is out of scope.

---

## 0. Retargeting Declaration

The original FAF proving challenge:
> Ruby 4.0.3 on Windows 11 must be forced into a verified foreign-capability host.

This application retargets FAF to:
> **Webview HTML payloads must be relocated to disk under `media/views/<surface>/` and reloaded in-place when their source files change, without breaking the existing CSP nonce model and without forcing a window reload.**

The host language stays TypeScript. The foreign capability is the VS Code webview host's reload model. The membrane is the CSP nonce contract + the file-system watcher debounce. The False Success Ban, Capability Ladder, and Impossible-Currently Boundary schema are unchanged.

---

## 1. Challenge Statement

```
The chthonic-archive extension must complete:

  - Per-webview HTML/JS/CSS extraction to media/views/<surface>/.
  - A reload watcher gated on chthonic.dev.autoReload (already-existing config key),
    no new opt-in flag required.
  - A reload postMessage protocol that triggers location.reload() inside each
    live webview when its media/views/ source file changes.
  - One e2e smoke that mutates a media/views/ file and asserts the webview
    re-renders within a debounce window.

The starting state already has:

  - Extension-host hot-reload via chthonic.dev.autoReload + fs.watch on dist/
    (Phase 4 first half, already shipped).
  - media/abyssalPane.js + media/wasm/ as precedent for externalized assets.
  - LaneRegistry + RuntimeLaneState as the telemetry contract.

The challenge is NOT:

  - Migrate webviews to a UI framework (React, Svelte, Solid).
  - Introduce a webview bundler distinct from the existing bun pipeline.
  - Change the CSP shape or relax the nonce requirement.
  - Touch the activation modules sealed by the Phase 3 pass.
  - Externalize the markdown paste lane (no webview).
  - Add a new opt-in flag — chthonic.dev.autoReload already covers both
    extension-host and webview reload semantics.
  - Reload the window when a media/views/ file changes; the whole point of
    this pass is webview-only reload.

The actual challenge is:

  Move HTML/CSS/JS to disk. Read it back at resolveWebviewView time with
  the same nonce/CSP substitution. Watch the directory. On change, ask each
  live webview to reload itself. Each surface passes the smoke gate before
  the next is extracted.
```

---

## 2. False Success Ban

A webview HMR closure is **not** admitted because:

- `media/views/stylus/index.html` exists.
- `bun run compile` returned 0.
- `bunx tsc --noEmit` returned 0 (modulo the baseline error).
- The webview opens and renders.
- The CSP header in the rendered HTML looks identical.
- A unit test mocks `webview.postMessage` and asserts it was called.
- The watcher fires when a file changes.
- `chthonic.dev.autoReload=false` and the watcher is silent.

Those facts may create candidate gates. They do not admit HMR.

A successful HMR closure is admitted only when, with `chthonic.dev.autoReload=true`, mutating `media/views/stylus/index.html` (or any `media/views/**` file) causes the live Stylus webview to call `location.reload()` and re-render with the new content within ≤ 1000 ms, **without** triggering `workbench.action.reloadWindow`. The same probe must pass for all four webviews.

---

## 3. Capability Ladder (per webview + per HMR step)

| Level | Name | Meaning |
|-------|------|---------|
| L0 | Identified | Surface is named in this FAF (Stylus, Loom, ANKH, Abyssal). |
| L1 | Externalized | HTML/CSS/JS payload now lives at `media/views/<surface>/` and provider reads from disk. |
| L2 | Renders | Webview opens and matches the pre-extraction render byte-for-byte (modulo nonce). |
| L3 | Watched | File change in `media/views/<surface>/` causes provider to detect (debounced) and `postMessage({type:'reload'})`. |
| L4 | Reloads | Webview-side JS receives the message and calls `location.reload()`; new content visible without `workbench.action.reloadWindow`. |

**No level may be skipped.** If L2 fails byte-for-byte (real visual regression, not just nonce diff), the surface stays L1; HMR cannot be wired against a surface that doesn't render correctly first.

### Execution Order (load-bearing)

1. **W1 first — Stylus.** Smallest, simplest webview (379 lines of TS, no external dependencies, no WASM). The pattern-setter. Land L1→L4 for Stylus alone before touching any other surface. Stylus proves the externalization shape, the nonce substitution helper, and the postMessage protocol in isolation.
2. **W2 second — Loom + ANKH.** Same shape as Stylus, no external assets. Batch as one gate because both are pure HTML/CSS/inline-JS payloads. Land both at L4.
3. **W3 third — Abyssal.** Last because it already loads `media/abyssalPane.js` + `media/wasm/` via `localResourceRoots`. The HMR watcher must include `media/abyssalPane.js` in its watch set without double-firing for `media/views/abyssal/`. Care required; do not push this earlier in the order to avoid debugging the WASM load path while also debugging the HMR protocol.
4. **W4 fourth — End-to-end smoke.** New script `scripts/webview-hmr-smoke.ts` (or extension to e2e-extension-host) that opens each webview, mutates its `media/views/<surface>/index.html`, and asserts reload-without-window-reload within the debounce window.

If W1 cannot reach L4: stop. Do not extract W2 against an unproven pattern. If W3 fires the watcher twice for the same change: stop and fix the watcher glob before declaring W3 admitted.

---

## 4. Gate Ledger

### Gate W1 - Stylus extraction + HMR pattern-setter

**Question:** Can the Stylus webview's HTML/CSS/JS payload be moved to `media/views/stylus/{index.html,view.js}` (or `view.css` if separation helps), with the provider reading from disk, the CSP nonce substitution preserved, and a file-watcher → postMessage → location.reload() loop completing within 1000 ms?

**Targets:**
- `extensions/chthonic-archive/src/monolith/stylusInputView.ts` — `_getHtml(webview)` at line 100, currently returns a tagged-template HTML string.
- `extensions/chthonic-archive/media/views/stylus/index.html` (new) — the externalized HTML, with `{{nonce}}`, `{{cspSource}}`, and `{{viewScriptUri}}` placeholders.
- `extensions/chthonic-archive/media/views/stylus/view.js` (new) — the inline `<script nonce="...">` body, plus a tiny shim that listens for `window.addEventListener('message', e => e.data?.type === 'reload' && location.reload())`.

**Required artifacts:**
- **Probe (L2):** Open Stylus webview pre-extraction; capture `webview.html`. Open Stylus webview post-extraction; capture `webview.html`. Diff: only the nonce value differs. Anything else fails the gate.
- **Probe (L4):** With `chthonic.dev.autoReload=true`, run `fs.appendFile('media/views/stylus/index.html', '<!-- hmr-test -->')`. Within ≤ 1000 ms, the webview's `document.documentElement.outerHTML` includes the new comment. `workbench.action.reloadWindow` was NOT called (assert via spy or by checking that the test-electron window survives the reload).
- **Binding:** A small reusable helper `loadWebviewHtml(webview, mediaUri, surface, substitutions)` lives at `src/runtime/webviewLoader.ts` (new) and is shared by W1, W2, W3.
- **Membrane:** CSP shape is preserved exactly: `default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';`. The `{{cspSource}}` placeholder MUST resolve to `webview.cspSource` so any future asset references remain CSP-compliant. The watcher fires only when `chthonic.dev.autoReload=true`.

**Failure handling:** If the externalized file fails to load (missing, parse error), provider marks `LaneRegistry.set({name:'webviewHmr', state:'DEGRADED', reason:'media/views/stylus/index.html unreadable'})` and falls back to a minimal hardcoded "view unavailable" placeholder. Never throw past `resolveWebviewView`.

**Closure condition:** L4 reached. `manifest/webview_hmr_w1.json` written.

---

### Gate W2 - Loom + ANKH batch extraction

**Question:** Can Loom and ANKH webviews be externalized using the same `loadWebviewHtml` helper proven in W1, with their identical CSP shapes preserved?

**Targets:**
- `extensions/chthonic-archive/src/monolith/loomView.ts` (286 lines)
- `extensions/chthonic-archive/src/monolith/ankhReferenceView.ts` (535 lines — includes ANKH section parsing logic that must remain in TS; only the HTML chrome moves to disk)
- `extensions/chthonic-archive/media/views/loom/{index.html,view.js}` (new)
- `extensions/chthonic-archive/media/views/ankh/{index.html,view.js}` (new)

**Required artifacts:**
- **Probe (L2):** Same byte-for-byte rendered HTML diff as W1, for each surface.
- **Probe (L4):** Same 1000 ms reload probe as W1, for each surface.
- **ANKH-specific membrane:** ANKH's `_getHtml` interpolates parsed `sections` data into the HTML. The on-disk template must use a placeholder like `{{sectionsJsonInlined}}`; the provider serializes the sections array to a JSON literal and substitutes. Do NOT move the section-parsing logic to disk. Do NOT replace this with a fetch — the data is computed at resolve time and must inline.

**Closure condition:** L4 reached for both surfaces. `manifest/webview_hmr_w2.json` written.

---

### Gate W3 - Abyssal extraction (with existing external assets)

**Question:** Can the Abyssal webview be externalized to `media/views/abyssal/{index.html,view.js}` while continuing to load `media/abyssalPane.js` and `media/wasm/` correctly, and without the file-watcher firing twice for any single change?

**Targets:**
- `extensions/chthonic-archive/src/entropy/archiveAbyssalView.ts` (290 lines)
- `extensions/chthonic-archive/media/views/abyssal/{index.html,view.js}` (new)
- The existing `media/abyssalPane.js` and `media/wasm/` are NOT moved. They continue to live where they are. The watch glob must be `media/views/**` (NOT `media/**`) to avoid double-firing on changes to the existing assets.

**Required artifacts:**
- **Probe (L2):** Byte-for-byte HTML diff. WASM still loads (assert the WASM lane in `LaneRegistry` reaches its current state — `LIVE` if it was `LIVE` pre-extraction).
- **Probe (L4):** Mutate `media/views/abyssal/index.html` → reload within 1000 ms. Mutate `media/abyssalPane.js` → assert NO reload fires (it's not in the watch glob; this is intentional separation). Mutate `media/wasm/<file>` → assert NO reload fires.
- **Membrane:** `localResourceRoots` must include both `media/views/abyssal/` and the existing `media/` for the assets. The watcher glob is strictly `media/views/**`.

**Closure condition:** L4 reached. `manifest/webview_hmr_w3.json` written. `LaneRegistry.get('webviewHmr').state === 'LIVE'` after activation when `chthonic.dev.autoReload=true`.

---

### Gate W4 - End-to-end smoke

**Question:** Does a single smoke script exercise all four surfaces' HMR loops back-to-back without window reload?

**Targets:**
- `extensions/chthonic-archive/scripts/webview-hmr-smoke.ts` (new), or a new `webviewHmrCases` block inside `scripts/e2e-extension-host.ts`.
- The probe iterates over the four surfaces. For each: open the webview, mutate the corresponding `media/views/<surface>/index.html` (append a unique HMR test comment), wait up to 1500 ms (debounce + reload margin), assert the rendered DOM includes the new comment.
- The probe also asserts `vscode.commands.executeCommand` was NOT called with `workbench.action.reloadWindow` during the run (via spy or by checking the window UUID is unchanged).

**Required artifacts:**
- **Probe:** `bun run test:webview-hmr` (new package.json script) passes locally and in CI. All four surfaces reach L4. The lane registry snapshot at end of run shows `webviewHmr=LIVE`.
- **Membrane:** This is a strict superset of the W1-W3 per-surface probes. If any per-surface probe regresses, W4 fails — do not lower the per-surface bar to make W4 pass.

**Closure condition:** L4 reached. `manifest/webview_hmr_w4.json` written.

---

## 5. Required Artifacts

- TypeScript: `src/runtime/webviewLoader.ts` (new) with `loadWebviewHtml(webview, mediaUri, surface, substitutions)`.
- TypeScript: `src/runtime/webviewHmrWatcher.ts` (new) — registers `vscode.workspace.createFileSystemWatcher('**/media/views/**')`, gated on `chthonic.dev.autoReload`, publishes to `LaneRegistry` as the `webviewHmr` lane, debounces 250 ms (matches `LaneRegistry`'s flush cadence), tracks live webviews via the providers' returned `WebviewView` references and broadcasts `postMessage({type:'reload'})` on change.
- TypeScript: each provider's `_getHtml` / `getHtml` is replaced by a call to `loadWebviewHtml`. The TS file shrinks substantially.
- HTML/JS: `media/views/{stylus,loom,ankh,abyssal}/{index.html,view.js}` (8 new files).
- Smoke: `scripts/webview-hmr-smoke.ts` OR new block in `e2e-extension-host.ts`.
- Manifest: `manifest/webview_hmr_w{1..4}.json` per gate, plus `manifest/webview_hmr_baseline.json` recorded pre-execution (captures pre-extraction `webview.html` for each surface, used as the L2 byte-diff baseline).
- Package.json: add `"test:webview-hmr": "bun run scripts/webview-hmr-smoke.ts"` if a standalone script.

---

## 6. Impossible-Currently Boundaries (none expected)

This pass should not produce new impossible-currently entries. Possible exceptions:

- If the VS Code webview API does not deliver `postMessage` to a webview that has just received a CSP-violation, document the boundary and pin the affected surface at L3 with a reopen condition.
- If `vscode.workspace.createFileSystemWatcher` does not fire on `media/views/**` paths inside `extensions/chthonic-archive/` because of how the workspace root is resolved during e2e tests, document the boundary at W4 and ship W1-W3 admitted while W4 stays open.

If neither exception fires, this pass closes with no new boundaries.

---

## 7. What This Is Not

```
This handoff does not authorize a UI framework migration (React, Svelte, Solid).
This handoff does not introduce a new bundler or build tool for webview JS.
This handoff does not change the CSP shape or relax the nonce requirement.
This handoff does not touch the activation modules from the Phase 3 pass.
This handoff does not externalize the markdown paste lane (it has no webview).
This handoff does not add a new opt-in flag — chthonic.dev.autoReload covers both halves of Phase 4.
This handoff does not move media/abyssalPane.js or media/wasm/ — they stay where they are.
This handoff does not reload the window when a media/views/ file changes.
```

What this handoff claims:

> Phase 4's deferred webview HMR half can be closed by externalizing four webview payloads to `media/views/<surface>/`, adding one shared loader helper, one watcher module, and one e2e smoke. Each surface admits at L4 only when its mutation triggers `location.reload()` within 1000 ms without a window reload. The pattern is set by Stylus alone before any other surface is touched.

The boundary ledger is the artifact. The probe is the file-mutation reload smoke. The membrane is the CSP nonce contract preserved across the disk roundtrip + the watcher glob restricted to `media/views/**`. The lane is `webviewHmr` published to `LaneRegistry`.

No false success. No decoration. No mythology.

---

## 8. Codex 5.5 Invocation Frame

When the user pastes this document into a Codex 5.5 task prompt, the expected operating posture is:

- Treat `docs/reference/FAF_CHTHONIC_DAEMON_JSONL_EMITTER.md` as the immediately-prior pass shape and §0a above as the current state. Do not re-derive.
- Pre-execution: emit `manifest/webview_hmr_baseline.json` recording (a) `webview.html` content for each of the four surfaces (open them via the test-electron harness), (b) current line counts for the four `*View.ts` files, (c) the current `LaneRegistry` lane set for the four view lanes. This is the rollback anchor.
- Per gate (W1, W2, W3, W4): emit `manifest/webview_hmr_<gate>.json` with `{gate, level_reached, status, evidence_files, html_diff_summary, reload_latency_ms}`.
- Per gate: do not advance past L3 without a real `vscode.workspace.createFileSystemWatcher` fire. Do not advance past L4 without observing `location.reload()` in the rendered DOM AND confirming `workbench.action.reloadWindow` was not invoked.
- On W1 failure (cannot reach L4 for Stylus alone): rewrite the gate as `impossible_currently_boundary` with the specific failure mode and STOP. Do not attempt W2-W4 against an unproven pattern.
- On W4 admission: append `webviewHmr=admitted_L4` to `manifest/failures.jsonl`.
- Produce one PR with four commits — one per gate. Commit message convention: `feat(webview): W1 externalize Stylus + HMR pattern`, `feat(webview): W2 externalize Loom and ANKH`, `feat(webview): W3 externalize Abyssal`, `test(webview): W4 end-to-end HMR smoke`.
- Do not touch the activation modules, the daemon JSONL transport, the cockpit route, the lane registry implementation, or `LANE_TEMPLATE.md`. Those are sealed.
- If the work expands beyond the four gates above (e.g. a webview cannot be externalized cleanly, or the watcher fires unpredictably), STOP and add a §9 to this document describing the unforeseen requirement, then return for human review.
