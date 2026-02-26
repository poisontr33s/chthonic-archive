# Chthonic Golden — Custom VS Code Distribution

> A hardened, ANKH-integrated Visual Studio Code distribution for the Chthonic Archive.

## Directory Structure

```
chthonic-golden/
├── product.json              # Distribution identity (branding, telemetry, update channel)
├── quality.json              # Build quality definitions (stable/insider)
├── electron-main/
│   ├── bootstrap.js          # Hardened Electron entry point (GPU, memory, crash recovery)
│   └── gpu-policy.json       # Baked-in GPU flags (no argv.json dependency)
├── patches/
│   ├── README.md             # Patch strategy documentation
│   ├── 001-product-json.patch     # product.json replacement (generated)
│   ├── 002-telemetry-strip.patch  # Remove/redirect Microsoft telemetry
│   └── 003-gpu-defaults.patch     # Bake GPU acceleration into defaults
├── branding/
│   ├── icon.ico              # Chthonic Golden application icon (placeholder)
│   ├── icon.png              # 512x512 mandala icon
│   └── splash.svg            # Startup splash (optional)
├── extensions/
│   ├── allowlist.json        # Curated extension IDs that ship built-in
│   └── blocklist.json        # Extensions banned from activation
├── scripts/
│   ├── build.ps1             # Full build pipeline (clone → patch → build → package)
│   ├── patch.ps1             # Apply patches to upstream VS Code checkout
│   └── package.ps1           # Package into installer/portable
└── ankh/
    ├── semantic-tokens.json  # Custom semantic token types for @ankh: markers
    └── integration.md        # How ANKH integrates into the fork
```

## Quick Start

```powershell
# 1. Clone upstream VS Code
git clone --depth 1 --branch main https://github.com/microsoft/vscode.git upstream-vscode

# 2. Apply Chthonic Golden patches
.\chthonic-golden\scripts\patch.ps1 -UpstreamPath .\upstream-vscode

# 3. Build
.\chthonic-golden\scripts\build.ps1 -UpstreamPath .\upstream-vscode -Quality stable

# 4. Package
.\chthonic-golden\scripts\package.ps1 -UpstreamPath .\upstream-vscode -Output .\dist
```

## Architecture

- **Shallow patch strategy**: We patch upstream VS Code rather than maintaining a deep fork. This minimizes merge conflict surface when pulling upstream updates.
- **product.json replacement**: The primary differentiation layer — branding, telemetry, marketplace, update channel.
- **GPU hardening baked in**: GPU flags are applied at the Electron bootstrap level, not in user-space argv.json.
- **ANKH integration**: Custom semantic tokens, CodeLens providers, and sidebar panels ship as built-in extensions.

## ANKH Layer

The fork embodies ANKH's Media Projection layer:

```
ANKH Lineage Core (immutable)
  ↓
Interface Vessel: VS Code Fork (translates lineage → editor experience)
  ↓
Media Projections: semantic tokens, commands, panels, themes
```

The fork does NOT define ANKH — it consumes ANKH-descended artifacts.

## Legal

VS Code is MIT-licensed. This distribution:
- Replaces Microsoft trademarks (name, logo, marketplace URLs)
- Keeps MIT license for VS Code upstream code
- ANKH integration layer: proprietary (Chthonic Archive)
