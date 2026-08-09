# Chthonic Archive Assistant

VSCode extension providing MCP-powered chat interface to the ASC Framework.

## Features

- 🔥 **Sidebar Chat Panel** - React 19 interface
- 💀 **MCP Integration** - Connects to the chthonic-v3 server (which absorbed asc-injector 2026-08-09)
- ⚓ **SSOT Context** - Inject Codex Brahmanica Perfectus
- ⚡ **Built with Bun** - Fast, modern tooling

## Installation

1. Build the extension:
   ```bash
   cd chthonic-vscode-extension
   bun install
   bun run build
   ```

2. Install in VSCode:
   ```bash
   code --install-extension chthonic-assistant-0.1.0.vsix
   ```

## Usage

- Click the flame icon (🔥) in the activity bar
- Chat with the Triumvirate via MCP servers
- Use commands:
  - `Chthonic: Inject SSOT Context`
  - `Chthonic: Validate SSOT Hash`

## Development

```bash
bun run dev      # Build and launch in development mode
bun run watch    # Watch mode for live reload
```

## Architecture

- **Extension**: TypeScript → Bun bundler → dist/extension.js
- **Webview**: React 19 → Bun bundler → dist/index.js
- **Backend**: Existing MCP servers (stdio transport)
