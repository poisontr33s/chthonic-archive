---
type: runbook
category: migration
created: 2026-03-15
status: active
---

# Desktop Clone Next Steps

## Current State

- Laptop export completed to `C:\Users\erdno\Desktop\chthonic-desktop-clone`
- Desktop-side `robocopy` from `\\192.168.1.9\chthonic-clone` is in progress
- Do not interrupt `robocopy` unless it exits with a hard error

## When `robocopy` Finishes

Run these on the **desktop local** machine, not inside the remote laptop session.

### 1. Verify the copied package

```powershell
pwsh -NoProfile -File "C:\Users\eldno\Desktop\chthonic-desktop-clone\desktop-clone-state.ps1" `
  -Mode Verify `
  -PackageRoot "C:\Users\eldno\Desktop\chthonic-desktop-clone"
```

### 2. Simulate restore first

```powershell
pwsh -NoProfile -File "C:\Users\eldno\Desktop\chthonic-desktop-clone\desktop-clone-state.ps1" `
  -Mode Restore `
  -DryRun `
  -PackageRoot "C:\Users\eldno\Desktop\chthonic-desktop-clone" `
  -RestoreRepoRoot "$env:USERPROFILE"
```

### 3. Run the real restore

```powershell
pwsh -NoProfile -File "C:\Users\eldno\Desktop\chthonic-desktop-clone\desktop-clone-state.ps1" `
  -Mode Restore `
  -PackageRoot "C:\Users\eldno\Desktop\chthonic-desktop-clone" `
  -RestoreRepoRoot "$env:USERPROFILE"
```

### 4. Restart and validate locally

- Close the remote VS Code window connected to `laptop-draqgn8a`
- Open **local** VS Code Insiders on the desktop
- Open the local repo at `C:\Users\eldno\chthonic-archive`

Run:

```powershell
hostname
cd $env:USERPROFILE\chthonic-archive
git rev-parse HEAD
git stash list
gh auth status
Test-Path "$env:USERPROFILE\.codex\auth.json"
Test-Path "$env:USERPROFILE\.claude\.credentials.json"
```

Expected:

- `hostname` is the desktop
- `git rev-parse HEAD` is `53228baaa95789e6a59886a78714900063de37ce`
- stash list is present
- both auth files exist

## Cleanup After Success

Run on the **laptop**:

```powershell
Remove-SmbShare -Name "chthonic-clone" -Force -ErrorAction SilentlyContinue
```

If a temporary bridge user was created, also remove it:

```powershell
Remove-LocalUser -Name "clonebridge" -ErrorAction SilentlyContinue
```

## Concept Queue

- Future lane: a functional terminal/process overlay with matrix-like glyph flow
- Target abstraction: language-agnostic execution surface across `pwsh`, terminal, filetype, extension, and content-driven runtime lanes
- Constraint: keep it aesthetic **and** operational, not just ornamental animation
