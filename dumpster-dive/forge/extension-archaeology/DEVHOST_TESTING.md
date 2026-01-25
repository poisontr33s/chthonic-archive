# Extension Development Host Testing

## Launch Extension Dev Host

### Method 1: VSCode Command Palette
1. Open `extensions/chthonic-statusbar` or `extensions/chthonic-mandala` in VSCode
2. Press `F5` (or `Ctrl+Shift+D` → Run → "Extension")
3. New VSCode window opens with `[Extension Development Host]` in title

### Method 2: PowerShell (Bun-friendly)
```powershell
# StatusBar extension
code-insiders --extensionDevelopmentPath="$PWD\extensions\chthonic-statusbar"

# Mandala extension
code-insiders --extensionDevelopmentPath="$PWD\extensions\chthonic-mandala"

# Both (if you have multi-root support)
code-insiders --extensionDevelopmentPath="$PWD\extensions\chthonic-statusbar;$PWD\extensions\chthonic-mandala"
```

## Verification Checklist

### 1. Extension Activation
- `F1` → `Developer: Show Running Extensions`
- Look for `chthonic-archive.chthonic-statusbar` and `chthonic-archive.chthonic-mandala`
- Status should be "Activated"

### 2. Check Console Logs
- `Help` → `Toggle Developer Tools` → `Console` tab
- Should see: `🔥 Chthonic Archive Status Bar extension activated`
- Should see: `🌀 Chthonic Mandala Viewer activated`
- Should see: `Detected Python: 3.13.11` (or similar)

### 3. Status Bar Indicators (Right Side)
- `$(pulse) 8d` - Metabolic cycle age
- `$(device-desktop) X.XGB/16.0GB` - GPU VRAM
- `$(symbol-method) 3.13` - Python lane (should show version, not "???")
- `$(git-branch) Ø` - Active lineage
- `$(pass) SSOT` or `$(warning) SSOT` - SSOT verification

### 4. Theme
- `Ctrl+K Ctrl+T` → Select `Chthonic Mandala (Dark)`
- Editor background should be dark (`#0b0b10`)
- Activity bar should have gold foreground
- Status bar should be slightly lighter than editor

### 5. Activity Bar Icon
- Look for Chthonic Geometry icon on left sidebar (colorful mandala)
- Should be visible in both dark and light themes (uses `currentColor`)

### 6. Commands
Test all commands via `F1`:
- `Chthonic: Refresh All Status Indicators`
- `Chthonic: Verify SSOT Integrity` (spawns terminal)
- `Chthonic: Run Metabolic Cycle` (spawns terminal)
- `Chthonic: Show GPU Statistics` (spawns terminal)
- `Chthonic: Open Sacred Mandala` (opens webview)
- `Chthonic: Open Dependency Graph` (opens webview)
- `Chthonic: Open Health Report` (opens webview)

### 7. Extension Host Logs
- `Output` panel → Select `Extension Host` from dropdown
- Look for errors or warnings
- Should see activation messages without errors

## Common Issues

### Extension Doesn't Activate
- Check `activationEvents` in `package.json` includes `onStartupFinished`
- Verify `main` points to `./dist/extension.js`
- Check Extension Host logs for errors

### Status Bar Shows "???" for Python
- Old regex bug - verify fix applied: `/Python\s+(\d+\.\d+(?:\.\d+)?)/`
- Check that `PYTHONIOENCODING=utf-8` is set
- Test manually: `uv run python --version`

### Theme Not Visible
- Verify `themes/chthonic-mandala-color-theme.json` exists
- Check `package.json` has `contributes.themes` array
- Reload window after installing

### Icon Not Showing
- Verify `icons/mandala.svg` exists
- Check `package.json` has `"icon": "icons/mandala.svg"`
- SVG should use `currentColor` for theme adaptation

## Bun-Specific Commands

```powershell
# Rebuild extensions (fast!)
cd extensions\chthonic-statusbar
bun run compile  # ~15ms

cd ..\chthonic-mandala
bun run compile  # ~13ms

# Watch mode (auto-rebuild on save)
bun run watch

# Install dependencies (if needed)
bun install

# Run validation
cd ..\..
bun run extensions/validate_fixes.js
```

## Bundle Size Targets

- **StatusBar**: ~12.6KB (was 20.6KB, 38% reduction)
- **Mandala**: ~16.9KB (stable)
- **Total**: ~29.5KB for both extensions

Achieved via:
- Removed dead `hedonisticValidation` import
- `"sideEffects": false` in package.json
- Bun's aggressive tree-shaking
- Single-file bundle (no chunking)
