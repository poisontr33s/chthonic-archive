# reflex-guard

Pre-commit scaffold for dependency drift detection in Cargo lanes.

## What it does

- Reads staged changes from `git diff --cached`.
- Detects `Cargo.toml` edits.
- Compares staged dependencies vs `HEAD` dependencies.
- Logs: `Dependency Change Detected`.
- Optionally enforces allowlist with `--strict`.

## Components

- Python guard: `extensions/reflex-guard/.chthonic/reflex_guard.py`
- Pre-commit wrapper: `extensions/reflex-guard/scripts/pre-commit.ps1`
- Hook installer (chains existing guardian): `extensions/reflex-guard/scripts/install-hook.ps1`
- Allowlist file: `extensions/reflex-guard/whitelist.json`

## Manual run

```powershell
uv run extensions/reflex-guard/.chthonic/reflex_guard.py --staged
```

Strict mode:

```powershell
uv run extensions/reflex-guard/.chthonic/reflex_guard.py --staged --strict
```

## Install pre-commit hook shim

```powershell
pwsh -NoProfile -File extensions/reflex-guard/scripts/install-hook.ps1
```

