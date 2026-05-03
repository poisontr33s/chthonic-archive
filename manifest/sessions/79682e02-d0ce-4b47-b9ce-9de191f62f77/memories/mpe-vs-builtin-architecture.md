# MPE vs VS Code Built-in Markdown Preview — Architecture Diagnosis

## Key Finding: MPE does NOT extend the built-in preview. It REPLACES it.

MPE uses `customEditors` viewType + `vscode.window.createWebviewPanel()` to create its own webview panel.
The rendering is done by `crossnote` library (standalone npm package, formerly called `mume`).
Crossnote runs its own instance of markdown-it with its own plugin chain.

## VS Code Built-in Preview Extension Points

Three contribution points allow enhancing the BUILT-IN preview:
1. `markdown.markdownItPlugins` — chain markdown-it plugins into the built-in parser
2. `markdown.previewScripts` — inject JS into the built-in preview webview
3. `markdown.previewStyles` — inject CSS into the built-in preview

Reference implementations:
- `bierner.markdown-mermaid` — uses markdownItPlugins + previewScripts for Mermaid in built-in preview
- `bierner.markdown-emoji` — uses markdownItPlugins for emoji in built-in preview

## Why MPE Chose Replacement Over Extension

1. **Full HTML template control**: MPE generates entire HTML via `engine.generateHTMLTemplateForPreview()` — owns `<head>`, `<body>`, all scripts/styles. Built-in preview only lets you inject into its existing template.

2. **Bidirectional webview messaging**: MPE uses `previewPanel.webview.postMessage()` and `onDidReceiveMessage()` for scroll sync, code chunk execution, theme switching, image helper, etc. Built-in preview scripts run in a sandboxed context with limited messaging.

3. **Code Chunk execution**: MPE's `runCodeChunk()` / `runAllCodeChunks()` spawns processes (python, node, etc.) from the extension host and streams results back into the webview. Built-in preview sandbox cannot spawn processes.

4. **Multiple export engines**: Chrome/Puppeteer, Prince, Pandoc, eBook — these need full Node.js process access.

5. **Notebook-per-workspace architecture**: MPE maintains a `Notebook` object per workspace folder with its own configuration, caches, backlinks graph. Built-in preview has no concept of this.

6. **Custom editor mode**: `PreviewsOnly` mode replaces the text editor entirely. Built-in preview is always a side panel.

7. **File protocol rewriting**: `utility.useExternalAddFileProtocolFunction()` hooks into all resource URL generation for webview URI conversion.

## What IS Portable to Built-in Preview

Everything that only needs markdown-it plugins + client-side JS + CSS:
- KaTeX rendering (markdown-it-katex + KaTeX JS/CSS bundle)
- Mermaid diagrams (already proven by bierner.markdown-mermaid)
- Footnotes (markdown-it-footnote)
- Extended tables (markdown-it plugin)
- Emoji (already proven by bierner.markdown-emoji)
- Wiki links (markdown-it plugin)
- Custom theme CSS (markdown.previewStyles)

## What CANNOT Be Ported

- Code Chunks (process spawning from sandbox)
- Pandoc parser (needs subprocess)
- RevealJS presentations (needs full webview control)
- PDF/ePub export (needs Puppeteer/Prince processes)
- Scroll sync (needs bidirectional messaging — limited in built-in)
- Backlinks (needs workspace-wide note graph)
- Custom editor mode (needs customEditors)
