# Python lanes (uv)

## Policy
- Primary lane: **CPython 3.14** (latest stable, bugfix phase).
- Legacy lane: **CPython 3.13** (security-only — use only when a dependency lacks 3.14 wheels).
- The repo pins Python via `.python-version` using the lane request (portable): `3.14`.
- Local development should use uv shims (lane-stable): `%USERPROFILE%\.local\bin\python3.14.exe`.

## Maintenance (Windows PowerShell)
- Upgrade primary lane: `uv python upgrade 3.14 --reinstall`
- Refresh shims on PATH: `uv python update-shell`
- Verify: `uv python list` and `py -0p`

## Virtualenv safety
- Before removing old uv-managed installs, upgrade any venvs that reference them:
  - `python3.14.exe -m venv --upgrade --upgrade-deps <venv-dir>`
