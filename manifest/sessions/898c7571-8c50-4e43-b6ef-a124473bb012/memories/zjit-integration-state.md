# ZJIT rv Integration Session State

## What's been read
- `scripts/chthonic.ps1` ruby functions: Get-RvRubyExePath (line 74), Get-RvRubyBinDir (91), Get-RubyDevKitRoot (113), Ensure-RvCommandBinding (804), Get-RubyInstalledVersions (4628), Get-RubyCurrentVersion (4683), Invoke-RubyLane (4906-5005), Invoke-RubyDoctor (line ~4770+)
- `Invoke-RubyLane` is at line 4906, ends ~5005. Called from line 5892 for `ruby lane` dispatch.
- `.ruby-version` → `4.0.3-zjit` ✅ already pinned
- `rv ruby list` shows `ruby-4.0.3-zjit` installed at `~\AppData\Roaming\rv\rubies\ruby-4.0.3-zjit\bin\ruby.exe`
- `rv r ruby --zjit -e "puts RubyVM::ZJIT.enabled?"` → `true`
- Known issues: socket.so, bigdecimal, json/parser fail to build → "RubyGems not loaded" warning (expected, non-fatal)

## Integration gaps in Invoke-RubyLane
- No ZJIT/YJIT detection or display in `chthonic ruby lane`
- `Get-RubyCurrentVersion` uses bare `ruby --version` not `rv ruby find` — may miss rv-managed binary
- `Invoke-RubyDoctor` doesn't know about zjit known issues (needs to treat RubyGems/socket/bigdecimal warn as expected not error)
- No `Get-RvZjitExePath` helper for explicitly getting the zjit binary path

## Files to edit
1. `scripts/chthonic.ps1` — Invoke-RubyLane + Get-RubyCurrentVersion + Invoke-RubyDoctor
2. AGENT_COMMON.md — pwsh health check line says `pwsh --version` — check if 7.5.x needs updating to 7.6.x

## Key line numbers
- Invoke-RubyLane: 4906
- Invoke-RubyLane payload block: ~4940-4960
- Invoke-RubyLane display block: starts ~4964
- Invoke-RubyDoctor: need to find exact start
- ruby lane dispatch: line 5892
