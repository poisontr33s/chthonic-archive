# MPE Install Research — 2026-04-17

## VSIX Sideload Route (No Marketplace Needed)
- **Open VSX** has MPE v0.8.22 with direct VSIX download:
  `https://open-vsx.org/api/shd101wyy/markdown-preview-enhanced/0.8.22/file/shd101wyy.markdown-preview-enhanced-0.8.22.vsix`
- **GitHub Releases** at `shd101wyy/vscode-markdown-preview-enhanced/releases` — latest is v0.8.21 (Mar 15 2026), each release has "Assets 3" (includes VSIX)
- Install via: `code-insiders --install-extension path/to/file.vsix`

## MPE Architecture
- Engine: **Crossnote** (separate npm package `shd101wyy/crossnote`) — the core markdown renderer
- Latest crossnote: v0.9.19
- Diagram engines: Mermaid 11.13.0, KaTeX 0.16.38, PlantUML, WaveDrom, GraphViz (viz.js), Vega/Vega-Lite, Kroki (50+ diagram types)
- Code Chunks: execute Python/JS/Bash inline, render output in preview
- Security: CVE-2025-65716 fixed in 0.8.21 (HTML sanitization via cheerio + DOMPurify)

## Polyglot Rust Connection — CONFIRMED
The repo's polyglot stack (all confirmed from .toml files):

**Rust** (rust-toolchain.toml): channel 1.94.1, targets x86_64-pc-windows-msvc
- Cargo.toml: Vulkan (ash 0.38), GPU (gpu-allocator), ECS (bevy_ecs), math (glam), async (tokio), serde
- Future: Solana blockchain integration
- Tools: ankh-forge CLI (trail subcommand, .runestone format)

**Zig** (zig-toolchain.toml): channel 0.14.0, targets x86_64-windows + x86_64-linux-musl
- Used for: Vulkan pipeline LNK compatibility, cross-compilation

**Python** (pyproject.toml): requires-python >=3.14
- networkx, polars, rich, scikit-learn, numpy, sentence-transformers, torch, fastmcp, huggingface-hub, openai
- UV workspace members: mas_mcp, ankh_atlas
- Build: hatchling

**Bun/Node** (package.json, bunfig.toml, tsconfig.bun-base.json): JS/TS runtime
- Playwright POC, chthonic-next app

**R** (rproject.toml): Present but lightweight

**How MPE connects:**
- Crossnote engine is Node.js/TypeScript — runs IN VS Code's extension host
- Code Chunks can shell out to ANY binary: `cargo run`, `python`, `zig build`, etc.
- MPE could render live output from ankh-forge trail queries, Python polars analysis, etc.
- GraphViz/dot diagrams from Rust-generated .dot files
- Vega-Lite charts from Python/polars data pipelines
- Mermaid for architecture diagrams
- The polyglot .toml stack means every language has a renderer MPE can invoke

## Install Path (No Marketplace)
1. Download VSIX from Open VSX: https://open-vsx.org/api/shd101wyy/markdown-preview-enhanced/0.8.22/file/shd101wyy.markdown-preview-enhanced-0.8.22.vsix
2. Or from GitHub Releases: https://github.com/shd101wyy/vscode-markdown-preview-enhanced/releases (Assets include VSIX)
3. Install: `code-insiders --install-extension shd101wyy.markdown-preview-enhanced-0.8.22.vsix`
4. OR in VS Code: Extensions sidebar → "..." menu → "Install from VSIX..."

## MPE Latest
- v0.8.22 on Open VSX (25 days ago from 2026-04-17 = ~Mar 23)
- v0.8.21 on GitHub Releases (Mar 15 2026)
- Crossnote 0.9.19, Mermaid 11.13.0, KaTeX 0.16.38
- CVE-2025-65716 fixed (HTML sanitization)
