# T1 SCRIPTS_ROULETTE State

## Done (T0 + T1 partial)
- ✅ nightly-scheduled.ps1: erdno→eldno + sentinel file
- ✅ api_pool.ps1: -Verify switch
- ✅ desktop-warmup.ps1: already done
- ✅ mcp-filesystem.ts: chthonic-patch marker + version assertion
- ✅ lib/poe_auth.py: valid property + strict wrapper
- ✅ lib/shared.py: __all__ + 10-level traversal cap
- ✅ lib/ssot-paths.ts: as const + assertSsotExists + imports
- ✅ lib/ssot_paths.py: except ImportError fallback
- ✅ lib/ssot-paths.ps1: remove line-count + AssertExists param
- ✅ claudine.ps1: -NoProfile on all 8 inner invocations

## T1 Remaining (score 2.0, effort 1 each)
### gemini-cli-wrapper.ps1
- Add pre-flight binary check: if bun not found, hint `bun add @google/gemini-cli`
- Add `-Version` flag handler (already has `-Version` alias `v` in params; check if it's handled)

### chthonic-xp.ps1
- Scope `$ErrorActionPreference = 'SilentlyContinue'` to only the Get-Content loop (remove global)
- Derive TrailDir from chthonic config first (check .chthonic/config.json)
- Add `-Debug` switch param

### probe_toolchain_path.ps1
- Use `Get-Command <tool>` as primary probe
- Hardcoded paths as fallback only
- Emit probe-miss log

### polyglot_env.ps1
- Auto-invoke probe if output stale (>24h)
- Print confirmation on -Apply
- Add -Verify that re-runs sfs.ps1

### fortify_terminal.ps1
- Replace reflection hack `$console.GetMethod("set_QuickEdit","NonPublic, Static")` 
  with `[System.Console]::TreatControlCAsInput = $false`
- Also set `[Console]::InputEncoding`

### pause_agents.ps1
- Print backup path clearly (already does this but confirm)
- Add --restore flag
- Validate `operationalMode` key exists before setting

### api_pool_persist_user_env.ps1
- Add drift detection in -Status: compare pool file keys vs User env keys
- Highlight "need -Apply" keys

### api_key_gap_report.ps1
- Compute repo root via PSScriptRoot-relative traversal (currently uses Get-Location)
- Validate RegistryPath exists before reading
- Add -Json flag

## T1 Remaining (score 1.5, effort 2 — do after above)
### chthonic.ps1
- Add $ErrorActionPreference = 'Stop' after param block
- Propagate $LASTEXITCODE
- Add --version from package.json (currently hardcoded "3.3.0")
