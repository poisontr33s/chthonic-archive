# Extension Non-Regression Checklist

## Diagnostic Commands

### Quick Health Check
```powershell
bun run doctor
# Human-facing narrative output
# Shows bundle sizes, Python/GPU status, deployment, config
```

### Enforceable Invariants
```powershell
bun test extensions/__diagnostics__
# Structured test suite (22 tests across 7 files)
# CI-ready: fails on threshold violations
```

### Selective Diagnostics
```powershell
# Run specific test files
bun test extensions/__diagnostics__/bundle-size.test.ts
bun test extensions/__diagnostics__/python-detection.test.ts
bun test extensions/__diagnostics__/deployment.test.ts
```

---

## System Health Invariants

### Bundle Size (Critical - Monitor Regressions)
```powershell
# Verify bundle sizes remain predictably small
cd extensions
Get-ChildItem -Recurse -Filter "extension.js" | ForEach-Object {
    $size = ($_.Length / 1KB).ToString('F1')
    $name = $_.Directory.Parent.Name
    Write-Host "$name: $size KB"
}

# Expected values (2026-01-09):
# chthonic-statusbar: 6.5-7.0 KB (was 20.6 KB)
# chthonic-mandala: 13.8-14.5 KB (was 16.9 KB)
# Combined: <22 KB

# Regression threshold: If statusbar >10KB or mandala >18KB, investigate.
```

### Runtime Activation (Must Pass)
```powershell
# After reload, verify both extensions activated
code-insiders --list-extensions | Select-String 'chthonic'
# Expected: 2 matches (statusbar + mandala)

# Check Extension Host logs for activation
# F1 → "Developer: Show Running Extensions" → both listed as "Activated"
```

### Python Detection (Must Not Fail Silently)
```powershell
# Dry-run test
$output = & uv run python --version 2>&1
$version = if ($output -match 'Python\s+(\d+\.\d+(?:\.\d+)?)') { $matches[1] } else { 'FAILED' }
Write-Host "Python detection: $version"

# Expected: "3.13.11" or similar (NOT "FAILED" or "???")
# If fails: Check regex in extension.ts line ~204
```

### UTF-8 Encoding (Windows-Specific)
```powershell
# Verify PYTHONIOENCODING is set in spawned processes
$env:PYTHONIOENCODING = 'utf-8'
uv run python ssot_immunity.py --quiet

# Expected: No UnicodeEncodeError
# If fails: Check process.env.PYTHONIOENCODING in activate() function
```

### Theme Integrity
```powershell
# Verify theme file exists and is valid JSON
$themePath = 'extensions\chthonic-mandala\themes\chthonic-mandala-color-theme.json'
if (Test-Path $themePath) {
    $theme = Get-Content $themePath | ConvertFrom-Json
    Write-Host "Theme: $($theme.name) ($($theme.type))"
    Write-Host "Colors: $($theme.colors.Count)"
    Write-Host "Token scopes: $($theme.tokenColors.Count)"
} else {
    Write-Host "❌ Theme file missing" -ForegroundColor Red
}

# Expected: 33 colors, 14 token scopes
```

### Icon Visibility
```powershell
# Verify SVG uses currentColor (theme-adaptive)
$iconPath = 'extensions\chthonic-mandala\icons\mandala.svg'
$svg = Get-Content $iconPath -Raw
if ($svg -match 'currentColor') {
    Write-Host "✓ Icon uses currentColor"
} else {
    Write-Host "❌ Icon missing theme adaptation"
}

# Expected: At least one occurrence of 'currentColor'
```

---

## Bun Build Invariants

### Production Optimization Locked
```powershell
# Verify package.json has Bun production config
cd extensions\chthonic-statusbar
$pkg = Get-Content package.json | ConvertFrom-Json
Write-Host "sideEffects: $($pkg.sideEffects)"
Write-Host "treeShaking: $($pkg.bun.treeShaking)"
Write-Host "minify: $($pkg.bun.minify)"
Write-Host "NODE_ENV: $($pkg.bun.define.'process.env.NODE_ENV')"

# Expected:
# sideEffects: False
# treeShaking: True
# minify: True
# NODE_ENV: "production"
```

### Compile Script Minification
```powershell
# Verify --minify flag in compile scripts
Get-Content extensions\*/package.json | Select-String '"compile".*--minify'

# Expected: 2 matches (statusbar + mandala)
# If missing: Add --minify to compile script
```

### No Legacy Tooling
```powershell
# Verify no Jest/Node test artifacts remain
Get-ChildItem extensions -Recurse -Include @(
    'jest.config.*',
    '*.test.ts',
    '*.spec.ts',
    'webpack.config.*',
    'rollup.config.*'
) | Select-Object FullName

# Expected: No files found
# If found: Remove legacy test/build configs
```

---

## VSCode Compatibility

### Engine Version
```powershell
# Verify VSCode engine requirement is not too restrictive
Get-Content extensions\*/package.json | Select-String '"vscode":'

# Expected: "^1.90.0" or similar (not pinned to exact version)
# Allows compatibility with future VSCode releases
```

### Activation Events Coverage
```json
// Both extensions must have:
"activationEvents": [
  "onStartupFinished",    // Ensures activation on reload
  "onCommand:chthonic.*", // Explicit command triggers
  "onLanguage:python"     // Python file context
]
```

### Extension Host Logs (No Errors)
```
After reload:
1. Help → Toggle Developer Tools → Console
2. Filter: "chthonic"
3. Expected:
   - "🔥 Chthonic Archive Status Bar extension activated"
   - "🌀 Chthonic Mandala Viewer activated"
   - "Detected Python: 3.13.11" (or version)
4. No red errors or unhandled rejections
```

---

## Deployment Workflow (Repeatable)

### Rebuild + Deploy (Standard)
```powershell
# From workspace root
cd extensions\chthonic-statusbar
bun run compile  # Should be <15ms, output 6-7 KB

cd ..\chthonic-mandala
bun run compile  # Should be <15ms, output 13-14 KB

# Deploy
cd ..\..
$extDir = "$env:USERPROFILE\.vscode-insiders\extensions"
@('chthonic-statusbar', 'chthonic-mandala') | ForEach-Object {
    Remove-Item "$extDir\$_" -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item "extensions\$_" "$extDir\$_" -Recurse -Force
    Write-Host "✓ $_"
}

# Reload VSCode: Ctrl+Shift+P → "Developer: Reload Window"
```

### Watch Mode (Development)
```powershell
# Auto-rebuild on save
cd extensions\chthonic-statusbar
bun run watch

# In separate terminal for mandala
cd extensions\chthonic-mandala
bun run watch
```

### Validation (After Changes)
```powershell
# Run comprehensive diagnostic test suite
bun test extensions/__diagnostics__

# Expected: 22/22 tests pass across 7 files
# Fails if: bundle size regressed, config broken, deployment missing

# Human-readable summary
bun run doctor
```

---

## Regression Detection

### Size Increase Threshold
- **StatusBar**: If >10 KB → Dead code reintroduced or unused dependency added
- **Mandala**: If >18 KB → WebView HTML bloat or unnecessary imports

### Python Detection Failure Modes
1. **Returns `null`**: Regex broken (check backslash escaping)
2. **Returns `"???"`**: execSync timeout or uv not in PATH
3. **UnicodeEncodeError**: PYTHONIOENCODING not set in activate()

### Theme Not Showing
1. **File missing**: Check `themes/chthonic-mandala-color-theme.json` exists
2. **Not in list**: Verify `contributes.themes` in package.json
3. **Breaks on reload**: Check JSON syntax (no trailing commas)

### Icon Not Visible
1. **Wrong path**: Verify `"icon": "icons/mandala.svg"` in package.json
2. **Not theme-adaptive**: Check SVG contains `currentColor`
3. **Pixelated**: Ensure SVG viewBox is 64x64 or higher

---

## Future-Proofing

### When Adding Features
1. Run `bun run compile` and verify bundle size increase is justified
2. Run `bun test` to ensure no invariant violations
3. Check Extension Host logs for new activation errors
4. Update diagnostic tests if new behavior needs monitoring

### When VSCode Updates
1. Re-run diagnostics: `bun test extensions/__diagnostics__`
2. Test in both VSCode stable and Insiders
3. Verify theme colors still render correctly
4. Check activation events still trigger

### When Dependencies Update
1. Run `bun install` in each extension folder
2. Verify `bun run compile` still produces <15 KB bundles
3. Run `bun test` to check no regressions
4. Check no new warnings in build output

---

## Emergency Rollback

### If Extensions Break After Update
```powershell
# Quick rollback to last known good state
cd extensions\chthonic-statusbar
git checkout HEAD~1 -- src/ package.json
bun run compile

cd ..\chthonic-mandala
git checkout HEAD~1 -- src/ package.json
bun run compile

# Redeploy
cd ..\..
# Run deploy script (see above)
```

### Nuclear Option: Clean Rebuild
```powershell
# Remove all build artifacts and reinstall
cd extensions\chthonic-statusbar
Remove-Item -Recurse -Force node_modules, dist
bun install
bun run compile

cd ..\chthonic-mandala
Remove-Item -Recurse -Force node_modules, dist
bun install
bun run compile
```

---

## Metrics to Track

| Metric | Current | Threshold | Action if Exceeded |
|--------|---------|-----------|-------------------|
| StatusBar bundle | 6.7 KB | 10 KB | Audit imports, check for dead code |
| Mandala bundle | 14.1 KB | 18 KB | Review WebView HTML size |
| Combined size | 20.8 KB | 30 KB | Consider splitting features |
| Compile time | ~15ms | 100ms | Check for unnecessary transpilation |
| Activation time | <50ms | 200ms | Profile with Extension Host devtools |
| Python regex match rate | 100% | <95% | Investigate edge cases |

---

## Sign-Off Checklist (Before Committing)

- [ ] `bun test extensions/__diagnostics__` passes all 22 tests
- [ ] `bun run doctor` shows all ✓ green
- [ ] Bundle sizes within thresholds (statusbar <10KB, mandala <18KB)
- [ ] Extension Host logs show no errors
- [ ] Python version displays in status bar (not "???")
- [ ] Theme selectable in `Ctrl+K Ctrl+T`
- [ ] Icon visible in Extensions view and Activity Bar
- [ ] All activation events tested (reload, command palette, Python file open)
- [ ] No ad-hoc `.js` diagnostic scripts in extensions/
- [ ] `package.json` has `"sideEffects": false` and `bun.minify: true`
- [ ] Compile scripts include `--minify` flag

---

## Diagnostic Test Suite Structure

```
extensions/
├─ __diagnostics__/           # Bun test suite (enforceable)
│  ├─ bundle-size.test.ts     # Size thresholds (3 tests)
│  ├─ python-detection.test.ts # Regex validation (2 tests)
│  ├─ gpu-parsing.test.ts     # VRAM parsing (2 tests)
│  ├─ deployment.test.ts      # File deployment (4 tests)
│  ├─ source-code.test.ts     # Code quality (3 tests)
│  ├─ package-config.test.ts  # Build config (6 tests)
│  └─ assets.test.ts          # Theme/icon (3 tests)
├─ doctor.ts                  # Human diagnostics (narrative)
└─ NON_REGRESSION_CHECKLIST.md # This file
```

**Total: 22 enforceable tests + 1 narrative script**

---

*Last validated: 2026-01-09*
*Bundle sizes: StatusBar 6.7KB, Mandala 14.1KB (68% reduction from original)*
*Tooling: 100% Bun-native, zero npm/Jest/webpack dependencies*
*Test coverage: 22 diagnostic tests, <1s execution time*
