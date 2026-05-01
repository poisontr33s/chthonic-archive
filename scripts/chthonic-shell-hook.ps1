#!/usr/bin/env pwsh
# @SID: CHTHONIC_SHELL_HOOK_V1
#
# chthonic-shell-hook.ps1 — Terminal session logger for chthonic-archive.
#
# PURPOSE:
#   Instruments the current pwsh session to emit structured JSONL entries
#   for every command executed. Fills the gap between agent terminal tools
#   (which only see the last command) and the full session buffer.
#
# OUTPUTS:
#   manifest/terminal_session.jsonl   — per-command JSONL entries
#   manifest/terminal_pids.json       — PID registry updated on each shell start
#
# USAGE (source from $PROFILE or the local profile):
#   . "$env:USERPROFILE\chthonic-archive\scripts\chthonic-shell-hook.ps1"
#
# QUERY:
#   bun run scripts/terminal_session_query.ts --list-pids
#   bun run scripts/terminal_session_query.ts --pid 70336 --last 20
#   bun run scripts/terminal_session_query.ts --grep "python" --minutes 60
#
# GUARD: CHTHONIC_SHELL_HOOK_LOADED prevents double-registration in nested shells.

if ($env:CHTHONIC_SHELL_HOOK_LOADED -eq '1') { return }

# ── Paths ─────────────────────────────────────────────────────────────────────

$_hookRepoRoot = Join-Path $env:USERPROFILE 'chthonic-archive'
$_hookManifest = Join-Path $_hookRepoRoot 'manifest'
$_hookSessionLog = Join-Path $_hookManifest 'terminal_session.jsonl'
$_hookPidRegistry = Join-Path $_hookManifest 'terminal_pids.json'

if (-not (Test-Path $_hookManifest)) {
    New-Item -ItemType Directory -Path $_hookManifest -Force | Out-Null
}

# ── PID registry — register this shell on load ────────────────────────────────

$_hookSessionId = [System.Guid]::NewGuid().ToString('N').Substring(0, 8)
$_hookStartTs   = (Get-Date -Format 'o')
$_hookPid       = $PID

function _chthonic_update_pid_registry {
    $existing = @{}
    if (Test-Path $_hookPidRegistry) {
        try {
            $existing = (Get-Content $_hookPidRegistry -Raw | ConvertFrom-Json -AsHashtable)
        } catch {}
    }
    # Prune dead PIDs
    $live = @{}
    foreach ($key in $existing.Keys) {
        try {
            $proc = Get-Process -Id ([int]$key) -ErrorAction SilentlyContinue
            if ($proc) { $live[$key] = $existing[$key] }
        } catch {}
    }
    # Register current PID
    $live["$_hookPid"] = @{
        pid         = $_hookPid
        session_id  = $_hookSessionId
        start_ts    = $_hookStartTs
        cwd         = $PWD.Path
        title       = $Host.UI.RawUI.WindowTitle
        term        = $env:TERM_PROGRAM ?? $env:WT_SESSION ?? 'unknown'
        vscode_pid  = $env:VSCODE_PID ?? $null
    }
    $live | ConvertTo-Json -Depth 4 | Set-Content $_hookPidRegistry -Encoding UTF8
}

_chthonic_update_pid_registry

# ── PSReadLine history handler — emit command metadata on every Enter ─────────
# NOTE: This fires BEFORE the command runs. We capture what we can here.
# Exit code is captured via the prompt function AFTER command completes.

Set-PSReadLineOption -AddToHistoryHandler {
    param([string]$cmd)
    # AGENT-INJECTION MEMBRANE: VS Code run_in_terminal prepends \x15 (Ctrl+U / clear-line)
    # before injected commands. Strip leading terminal control sequences so the logged
    # command is clean and $var = ... assignments don't parse as command invocations.
    $cmd = [regex]::Replace($cmd, '^[\x00-\x1F\x7F]+', '')
    $cmd = $cmd.TrimStart()
    if ([string]::IsNullOrWhiteSpace($cmd)) { return $true }
    $entry = [ordered]@{
        ts          = (Get-Date -Format 'o')
        pid         = $_hookPid
        sid         = $_hookSessionId
        cwd         = $PWD.Path
        command     = $cmd
        exit_code   = $null    # filled by prompt hook below
        duration_ms = $null    # filled by prompt hook below
        seq         = ($global:_cthSeq = ($global:_cthSeq ?? 0) + 1)
    }
    $global:_cthLastEntry = $entry
    $global:_cthCmdStart  = [System.Diagnostics.Stopwatch]::StartNew()
    Add-Content -Path $_hookSessionLog -Value ($entry | ConvertTo-Json -Compress) -Encoding UTF8
    return $true
}

# ── Prompt hook — patch exit code + duration into last entry ──────────────────
# We wrap the existing prompt function rather than replacing it.

$_hookOriginalPrompt = if (Test-Path Function:\prompt) { Get-Content Function:\prompt } else { '"PS $($PWD.Path)> "' }

function global:prompt {
    # Capture exit state FIRST before anything can clobber it
    $ec  = $LASTEXITCODE
    $ok  = $?

    # HOOK-SAFETY MEMBRANE: wrap all logging in try/catch so the hook never
    # crashes the shell or corrupts $LASTEXITCODE for the calling session.
    try {
        if ($null -ne $global:_cthLastEntry -and $null -ne $global:_cthCmdStart) {
            $global:_cthCmdStart.Stop()
            $patch = [ordered]@{
                ts          = $global:_cthLastEntry.ts
                pid         = $global:_cthLastEntry.pid
                sid         = $global:_cthLastEntry.sid
                cwd         = $global:_cthLastEntry.cwd
                command     = $global:_cthLastEntry.command
                exit_code   = $ec
                success     = $ok
                duration_ms = $global:_cthCmdStart.ElapsedMilliseconds
                seq         = $global:_cthLastEntry.seq
            }
            # Append a corrected entry with _patch=true so the query tool can use the latest
            Add-Content -Path $_hookSessionLog -Value ($patch | ConvertTo-Json -Compress -AsArray:$false | ForEach-Object { $_ -replace '^{', '{"_patch":true,' }) -Encoding UTF8
            $global:_cthLastEntry = $null
            $global:_cthCmdStart  = $null
        }
    } catch {
        # Hook logging failed — absorb silently. Never propagate into the shell.
    }

    # Restore LASTEXITCODE so prompt doesn't interfere with $?
    $global:LASTEXITCODE = $ec

    # Call original prompt
    $promptResult = & ([scriptblock]::Create($_hookOriginalPrompt))

    # CTRL+U DRAIN: VS Code run_in_terminal queues \x15 (Ctrl+U) in the PTY while the
    # previous command runs. Draining here — after prompt output, before PSReadLine
    # starts ReadLine() — prevents the \x15 from being echoed as ^U in the terminal.
    # Only consumes \x15 bytes; stops immediately on any other key to preserve input.
    try {
        while ([Console]::KeyAvailable) {
            $k = [Console]::ReadKey($true)  # intercept without echo
            if ($k.KeyChar -ne [char]0x15) { break }
        }
    } catch {}

    $promptResult
}

$env:CHTHONIC_SHELL_HOOK_LOADED = '1'

# Explicit PSReadLine Ctrl+U binding — ensures \x15 is handled silently when
# PSReadLine IS in input mode (belt-and-suspenders alongside the prompt drain above).
if (Get-Module PSReadLine -ErrorAction SilentlyContinue) {
    Set-PSReadLineKeyHandler -Key Ctrl+u -Function BackwardDeleteLine -ErrorAction SilentlyContinue
}

Write-Host "[chthonic-hook] Session $($_hookSessionId) PID $($_hookPid) → manifest/terminal_session.jsonl" -ForegroundColor DarkGray
