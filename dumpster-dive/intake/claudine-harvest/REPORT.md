# Claudine Harvest Report

## Findings (Outside Sources)

| Source | Role | What it does | Trolling vector |
|---|---|---|---|
| `C:\Users\erdno\OneDrive\Documents\PowerShell\Microsoft.PowerShell_profile.ps1` | Global PowerShell profile | Sets `claudine` alias to `C:\Users\erdno\PsychoNoir-Kontrapunkt\scripts\claudineENV.ps1`; conditionally auto-activates that environment when inside that other repo. | **Always sets the alias**, so any terminal session can resolve `claudine` to the other repo unless this repo’s workspace profile is dot-sourced. |
| `C:\Users\erdno\OneDrive\Documents\PowerShell\profile.ps1` | Global PowerShell profile | Same pattern: sets `claudine` alias + auto-activation block for the other repo. | Same alias hijack behavior. |
| `C:\Users\erdno\PsychoNoir-Kontrapunkt\scripts\claudineENV.ps1` | Other repo activation script | Prepends global toolchain paths, sets env vars, prints a banner; uses `uv run python --version` for Python version output. | Not inherently malicious; it’s the **global alias** that makes it leak into other repos. |
| `C:\Users\erdno\Downloads\CantorForge.ps1` | “Fun” sandbox installer | A large, self-contained “impossible stack” bootstrapper (downloads/installers, uv install, rustup, conda, etc.). | Not a hijack, but **high-impact** if run accidentally; treat as a reference/upcycle source, not an auto-run dependency. |

## Repo-side Mitigations (Chthonic Archive)

| Mechanism | Status | Effect |
|---|---|---|
| `.vscode/profile.ps1` removes `Alias:claudine` and defines `global:claudine` | Implemented | Neutralizes the global alias **when the workspace profile is loaded**. |
| VS Code terminal profile dot-sources `.vscode/profile.ps1` | Implemented | Ensures new integrated terminals start “inside” the repo’s deterministic environment. |
| `scripts/claudine.ps1` entrypoint | Implemented | Explicit repo-local activation that can be run even if a global alias exists. |

## Upcycle Candidates (Safe)

| Candidate | From | Why it might be useful | Keep/Skip default |
|---|---|---|---|
| PATH de-dup + toolchain front-loading | `claudineENV.ps1` | Solid pattern, but this repo already has a deterministic PATH strategy. | Skip by default |
| Job-cap env vars | Global profiles | Might help on thermal stability, but it’s global and not repo-specific. | Skip by default |
| `CLAUDINE_ACTIVATED` marker | `claudineENV.ps1` | Useful for provenance/debugging; this repo now uses `__CHTHONIC_PROFILE_LOADED` marker. | Keep (repo-local marker already) |

## Next Steps (If you want to fully stop the hijack everywhere)

| Option | Change | Impact |
|---|---|---|
| A (recommended) | Make the global `Set-Alias claudine ...` conditional on being inside `PsychoNoir-Kontrapunkt` (or remove it entirely from global profiles). | Prevents cross-repo alias leakage at the source. |
| B | Keep global alias, but always use this repo’s `scripts/claudine.ps1` or ensure integrated terminals dot-source `.vscode/profile.ps1`. | Works in this repo, but leaves the global hijack in place for other contexts. |
