# WEB BRIDGE

The name collision matters.

`claude.ai/design` is the upstream Claude Design product. It owns the browser or desktop canvas, project list, design-system setup, export surfaces, sharing, and Claude Code handoff.

`Claude Design - Scriptorium` is this local VS Code Insiders extension. It owns the local design leaves, marginalia, vivarium preview, constellation view, bestiary, rune, and plaintext state under the workspace.

They are related by intent, not by a private API.

## Current truth table

| question | answer |
|---|---|
| Does Scriptorium log into `claude.ai/design`? | No. |
| Does it list web Claude Design projects? | No. |
| Does it consume the web product's project quota directly? | No known direct route. |
| Does it use Claude? | Yes, through the configured local `claude` CLI. |
| Where does OAuth happen? | Inside the Claude CLI account flow. |
| Where does local state live? | `designs/`, `designs.md`, `.scriptorium/`, and any files Claude writes into the workspace. |
| Can a web Claude Design export become a Scriptorium leaf? | Yes, once exported or handed off onto disk. |
| Can Scriptorium output be uploaded or imported into web Claude Design? | Yes, as local files/design-system material, subject to the web product's import flow. |

## Intended bridge

The stable bridge is file-first:

1. Claude Design web exports HTML bundles or hands off to Claude Code.
2. Those artifacts land in the workspace under `designs/` and `assets/`.
3. Scriptorium previews, annotates, transforms, and records marginalia beside those leaves.
4. If needed, the updated files can be uploaded or imported back into the web design-system flow.

This avoids pretending there is a secret sync API. When Anthropic exposes a documented Claude Design integration surface, this file becomes the place to describe that transport.

## What not to claim

- Do not claim Scriptorium is the Claude Design web app.
- Do not claim it has direct web project sync.
- Do not claim it has a separate Claude Design meter unless the CLI or official API exposes that explicitly.
- Do not erase the precursor transcript; mark it as precursor history.

## What to preserve

- The Scriptorium vocabulary: Constellation, Marginalia, Vivarium, Bestiary, Rune, Colophon.
- Plaintext on disk as the transition contract.
- Web Claude Design as the upstream creative canvas.
- Claude Code CLI as the current local inference bridge.

Made by Claude. Kept local until the web bridge becomes real.
