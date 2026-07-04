# Portability — what survives a Rust/Electron port

VS Code Insiders is moving toward Rust + a thinner Electron shell. Claude Code's own SDK transition is downstream of that. A future port of *Claude Design* itself is plausible, even desirable. This document names what would carry across and what wouldn't, so the port (if it happens) is informed rather than panicked.

## The principle

**The data is the API.** Every contract that matters between the user and the Scriptorium is plaintext on disk:

| contract | on-disk shape | language-agnostic? |
|---|---|---|
| asset ledger | `designs.md` (CommonMark) | yes |
| per-leaf conversation | `.scriptorium/marginalia/<leaf>.md` (CommonMark with sigil-bounded sections) | yes |
| session hibernation | `.scriptorium/session.md` (CommonMark) | yes |
| workspace voice | `CLAUDE.md` (CommonMark) | yes |
| design output | files under `designs/` (any web format) | yes |
| inference | the `claude` CLI as a subprocess | yes |

A workspace someone has been building in for a month — with rich marginalia, an aged constellation, a populated bestiary of patina states — would open in a Rust port of Claude Design and look identical. **Their work doesn't depend on the language of the activator.**

This is not accidental. It's the original posture, made explicit because plaintext-first felt right and now reveals itself as portability insurance.

## What survives

| layer | substrate | survives port? |
|---|---|---|
| activator (`extension.ts`) | TypeScript + Node | no — rewrite |
| inference adapter (`cli.ts`) | spawns `claude` via Node's `child_process` | concept survives; impl rewritten in Rust's `std::process::Command` |
| FS broker (`broker.ts`) | VS Code's `workspace.fs` | concept survives; impl rewritten against whatever FS API the new shell exposes |
| views (Constellation, Marginalia, Vivarium) | TypeScript-generated HTML strings in webviews | the HTML/CSS/JS payloads survive verbatim; the host-side glue is rewritten |
| scriptorium organs (manifest, marginalia, colophon, session, etc.) | TypeScript modules reading/writing markdown | concept survives; can be rewritten in Rust or kept as TypeScript and called via Wasm/N-API |
| on-disk shape | markdown + folders | survives unchanged |

## What would change

- **Build chain.** `bun build` → `cargo build` (or Tauri's bundler, or whatever the new SDK chooses).
- **Webview embedding.** Currently each view is an HTML string in a `WebviewView.html` setter. The Rust shell will have its own embedding contract; the payload itself (the manuscript-form CSS, the constellation SVG, the marginalia composer) stays as-is.
- **Process management.** The `claude` CLI subprocess survives, but the spawn/pipe code is rewritten in Rust.
- **Event plumbing.** EventEmitter (Node) → channels + futures (Rust) → unchanged surface area.

## What stays expensive to redo

- **The constellation's layout heuristics.** Force-ish springs, edge inference from co-edit history — re-tuning these in Rust is doable but requires a feel for the visual result, which the type system can't help with.
- **The marginalia HTML's CSS.** Inheriting `--vscode-*` variables, mixing parchment tones, getting the rubricated red to read as ink rather than warning — those decisions are aesthetic and survive the port only if someone with the same taste does the cross-translation.

## Practical advice for a future porter

1. **Read `blueprints/03-scriptorium.html` first.** It is the manuscript-form rationale; everything else is implementation downstream of those moves.
2. **Treat the on-disk format as inviolable.** A user with five months of marginalia must not have to migrate.
3. **Keep the organ names.** Constellation, Marginalia, Vivarium, Rune, Bestiary, Colophon. The vocabulary is load-bearing.
4. **Use the Folio VII audit as a parity test.** Anything `extension.ts` calls in the TypeScript version is a behavior the port owes.

## A note on the date

The user's project title carries *"lossless transition from claude.ai web user auth, Pro (sub) to vs-code-insiders latest version."* The lossless transition has two axes: the auth handoff (Anthropic's territory) and the user-data handoff (this project's territory). The plaintext-on-disk commitment is the second axis, fully under our control, future-proof against any host-language change.

🜂

— made by Claude
