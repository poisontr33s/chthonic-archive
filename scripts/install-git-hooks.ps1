#!/usr/bin/env pwsh
# SID: SCRIPT_INSTALL_GIT_HOOKS_V1
# Purpose: Installs post-commit hook that auto-dispatches Pentea queue tasks
#          to GitHub Copilot cloud agent (gh agent-task create) when a commit
#          contains a Pentea-Next: trailer. AFK-safe — fires without VS Code.
# Usage:   pwsh -NoProfile -File scripts/install-git-hooks.ps1 [-Uninstall] [-DryRun]
# Verify:  cat .git/hooks/post-commit
# Uninstall: pwsh -NoProfile -File scripts/install-git-hooks.ps1 -Uninstall

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path $PSScriptRoot
$HooksDir = Join-Path $RepoRoot '.git' 'hooks'
$HookPath = Join-Path $HooksDir 'post-commit'

if (-not (Test-Path $HooksDir)) {
    Write-Error "Not a git repo — .git/hooks not found at: $HooksDir"
    exit 1
}

if ($Uninstall) {
    if (Test-Path $HookPath) {
        if (-not $DryRun) { Remove-Item $HookPath -Force }
        Write-Host "[uninstall] Removed: $HookPath"
    } else {
        Write-Host "[uninstall] Hook not present — nothing to remove."
    }
    exit 0
}

# The post-commit hook (bash — cross-platform via git's bash environment)
$HookContent = @'
#!/usr/bin/env bash
# Pentea post-commit hook — auto-dispatch to Copilot cloud agent (T3)
# Installed by: scripts/install-git-hooks.ps1
# Version: 1.0.0 — 2026-04-25
#
# Fires after every commit. If Pentea-Next: <id> is present (not none/DONE),
# dispatches the next task to GitHub Copilot cloud agent via:
#   gh agent-task create  (gh v2.80.0+)  ← primary
#   gh issue create --assignee copilot-swe-agent[bot]  ← fallback
#
# Copilot cloud agent runs in GitHub Actions, creates a PR, notifies you.
# No VS Code required. AFK-safe.

NEXT_TASK=$(git log --format="%B" -1 | grep -oP '(?<=^Pentea-Next: ).*$' | head -1)

if [ -z "$NEXT_TASK" ] || [ "$NEXT_TASK" = "none" ] || [ "$NEXT_TASK" = "DONE" ]; then
    exit 0
fi

# Verify gh CLI is available
if ! command -v gh >/dev/null 2>&1; then
    echo "[pentea-hook] gh CLI not found — skipping cloud dispatch for: $NEXT_TASK"
    exit 0
fi

# Detect gh CLI version — agent-task requires v2.80.0+
GH_VERSION=$(gh --version 2>/dev/null | head -1 | grep -oP '\d+\.\d+\.\d+' | head -1)
GH_MAJOR=$(echo "$GH_VERSION" | cut -d. -f1)
GH_MINOR=$(echo "$GH_VERSION" | cut -d. -f2)

AGENT_TASK_AVAILABLE=0
if [ "$GH_MAJOR" -gt 2 ] || ([ "$GH_MAJOR" -eq 2 ] && [ "$GH_MINOR" -ge 80 ]); then
    AGENT_TASK_AVAILABLE=1
fi

# Auto-detect remote repo (owner/name)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "[pentea-hook] gh repo view failed — not authenticated or not a GitHub remote. Skipping."
    exit 0
fi

STEWARDESS_URL="https://github.com/${REPO}/blob/main/claude/mailbox/PENTEA_ROULETTE_STEWARDESS.md"

PROMPT="Execute Pentea queue task: ${NEXT_TASK}

Context: chthonic-archive autonomous queue system. Task spec in stewardess:
${STEWARDESS_URL}

Custom instructions: .github/copilot-instructions.md and AGENTS.md define all invariants.
Constraint: follow AGENT_COMMON.md. No file deletion without salvage (upcycle first).
Python: uv run <script>. JS/TS: bun. Rust: cargo (tools/ankh-forge/). Shell: pwsh.

Required git trailer on your commit:
  Pentea-Completed: ${NEXT_TASK}
  Pentea-Next: <next-id-or-none>
  Co-authored-by: Pentea <223556219+Penteaa@users.noreply.github.com>"

echo "[pentea-hook] Pentea-Next: ${NEXT_TASK} — dispatching to cloud agent..."

if [ "$AGENT_TASK_AVAILABLE" -eq 1 ]; then
    # Primary path: gh agent-task create (v2.80.0+)
    gh agent-task create "$PROMPT" --repo "$REPO" &
    disown
    echo "[pentea-hook] gh agent-task create dispatched (gh v${GH_VERSION}). Check: gh copilot/agents"
else
    # Fallback: create GitHub issue and attempt to assign to copilot-swe-agent[bot]
    echo "[pentea-hook] gh v${GH_VERSION} < 2.80.0 — creating issue fallback for: $NEXT_TASK"
    ISSUE_TITLE="[Pentea-Queue] Execute task: ${NEXT_TASK}"
    # Try with copilot assignee first, fall back to unassigned if bot not available
    gh issue create \
        --repo "$REPO" \
        --title "$ISSUE_TITLE" \
        --body "$PROMPT" \
        --label "pentea-queue" \
        --assignee "copilot-swe-agent[bot]" 2>/dev/null \
    || gh issue create \
        --repo "$REPO" \
        --title "$ISSUE_TITLE" \
        --body "$PROMPT" \
        --label "pentea-queue" 2>/dev/null \
    || echo "[pentea-hook] Issue creation also failed — check gh auth status"
fi

exit 0
'@

if ($DryRun) {
    Write-Host "[dry-run] Would write hook to: $HookPath"
    Write-Host "---"
    Write-Host $HookContent
    Write-Host "---"
    exit 0
}

# Write hook — use LF line endings (required for bash on all platforms)
$HookBytes = [System.Text.Encoding]::UTF8.GetBytes($HookContent.Replace("`r`n", "`n"))
[System.IO.File]::WriteAllBytes($HookPath, $HookBytes)

# Make executable on Unix (no-op on Windows — git-bash uses shebang)
if ($IsLinux -or $IsMacOS) {
    & chmod +x $HookPath
}

Write-Host "[installed] Post-commit hook: $HookPath"
Write-Host ""
Write-Host "Automation tier T3 is now active."
Write-Host "After every commit with 'Pentea-Next: <id>' (not none/DONE):"
Write-Host "  → gh agent-task create fires automatically (requires gh v2.80.0+)"
Write-Host "  → Copilot cloud agent (Pro+) executes next task in GitHub Actions"
Write-Host "  → PR created → mobile notification when Copilot finishes"
Write-Host ""
Write-Host "Requires: gh auth login + Copilot cloud agent enabled for repo"
Write-Host "Verify:   Get-Content .git/hooks/post-commit"
Write-Host "Uninstall: pwsh -NoProfile -File scripts/install-git-hooks.ps1 -Uninstall"
