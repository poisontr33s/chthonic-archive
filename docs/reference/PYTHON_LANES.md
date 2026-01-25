# Python lanes (uv)

## Policy
- Maintain only the latest stable patch releases for the `3.13` and `3.14` CPython lanes via `uv`.
- The repo pins Python via `.python-version` using the lane request (portable): `3.13`.
- Local development should use uv shims (lane-stable): `%USERPROFILE%\.local\bin\python3.13.exe` and `python3.14.exe`.

## Maintenance (Windows PowerShell)
- Upgrade lane installs: `uv python upgrade 3.13 --reinstall` and `uv python upgrade 3.14 --reinstall`
- Refresh shims on PATH: `uv python update-shell`
- Verify: `uv python list` and `py -0p`

## Virtualenv safety
- Before removing old uv-managed installs, upgrade any venvs that reference them:
  - `python3.14.exe -m venv --upgrade --upgrade-deps <venv-dir>`
  - `python3.13.exe -m venv --upgrade --upgrade-deps <venv-dir>`
