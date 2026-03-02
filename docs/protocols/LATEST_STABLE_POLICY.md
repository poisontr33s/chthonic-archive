# Latest stable policy (toolchain lanes)

This repo follows a **latest stable per-lane** policy for toolchains. The goal is predictable upgrades without machine-specific paths.

## Python (uv)
- Primary lane: **CPython 3.14** (latest stable, bugfix phase).
- Legacy lane: **CPython 3.13** (security-only — use only when a dependency lacks 3.14 wheels).
- Repo pin must be portable:
  - `.python-version` should contain `3.14` (lane request), not an absolute path.
- Prefer uv shims:
  - `%USERPROFILE%\\.local\\bin\\python3.14.exe`

### Maintain lanes (PowerShell)
- Upgrade primary lane (downloads latest patch if needed):
  - `uv python upgrade 3.14 --reinstall`
- Ensure shims are on PATH:
  - `uv python update-shell`
- Verify:
  - `uv python list`
  - `py -0p`

### Virtualenv safety rule
Before removing old uv-managed installs, upgrade any venvs that reference them:
- `python3.14.exe -m venv --upgrade --upgrade-deps <venv-dir>`

## Rust
- Workspace uses rust-analyzer + cargo for builds.
- Validate after changes:
  - `cargo build`
  - `cargo test`
  - Optional: `cargo clippy --all-targets --all-features -- -W clippy::pedantic`

## VS Code workspace settings
- Workspace settings should be **portable** (no absolute machine paths when avoidable).
- Prefer per-language formatting and explicit validation steps.
