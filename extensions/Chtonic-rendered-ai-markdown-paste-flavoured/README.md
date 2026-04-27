# Chtonic Rendered AI Markdown Paste Flavoured

Minimal VS Code Insiders extension for Chthonic Archive Markdown paste fidelity.

When a paste into a Markdown editor includes `text/html`, the extension converts that rendered HTML into Markdown with Turndown and inserts the Markdown instead of degraded plain text.

## Scope

- TypeScript VS Code extension.
- No React, webview, hooks, daemon, DOM scraping, Claude-specific code, or Vite stack.
- Targets `{ language: "markdown" }`.
- Primary paste provider uses `pasteMimeTypes: ["text/html"]`.
- Uses the Chthonic Archive mandala icon so the package sits beside the unfinished archive theme, file icon, and product icon work without absorbing that larger extension.

## Preserved Shapes

- ATX headings
- Bullet lists
- Numbered lists
- Fenced code blocks with language tags where available
- GFM Markdown tables
- Blockquotes
- Links
- Inline code

The converter also trims trailing whitespace and collapses excessive blank lines.

## Commands

- `Rendered AI Markdown Paste: Paste as Markdown`
- Command id: `renderedAiMarkdownPaste.pasteAsMarkdown`

The command invokes VS Code's normal paste action, allowing the registered paste provider to handle `text/html` when the clipboard exposes it.

## Manual Test

1. Open this folder in VS Code Insiders.
2. Run `bun install` if dependencies are not installed.
3. Run `bun run compile`.
4. Run `code-insiders --extensionDevelopmentPath=.` from this folder.
5. In the extension development host, open a `.md` file.
6. Copy rendered AI output that contains headings, lists, a fenced code block, a table, links, inline code, and a blockquote.
7. Paste into the Markdown file.
8. Confirm the inserted text is valid Markdown and preserves the rendered structure.

If a paste operation reaches the fallback provider without `text/html`, the extension shows:

`Clipboard did not include text/html; pasted source may only provide plain text.`

VS Code only invokes a provider for matching clipboard MIME types, so the fallback diagnostic listens for `text/plain` while the conversion provider remains scoped to `text/html`.

## Fixture Test

```powershell
bun install
bun run test
```

The Bun test runner converts `fixtures/rendered-sample.html` and compares it byte-for-byte with `fixtures/rendered-sample.md`.
