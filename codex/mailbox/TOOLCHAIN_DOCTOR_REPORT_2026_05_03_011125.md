# Toolchain Doctor Report

- Generated: `2026-05-03T01:11:25.757796+00:00`
- bun: `True`
- uv: `True`
- rv: `True`
- apply: `False`

## Bun

- Audit: PASS (no vulnerabilities)

## uv

- uv sync: executed
```text
warning: Found both a `uv.toml` file and a `[tool.uv]` section in an adjacent `pyproject.toml`. The following fields from `[tool.uv]` will be ignored in favor of the `uv.toml` file:
- index
Resolved 157 packages in 2ms
Checked 129 packages in 11ms
```

### Import Probes
- `idna`: `True`
```text
idna ok
```
- `huggingface_hub`: `True`
```text
huggingface_hub ok
```

### Hugging Face Auth Probe
- auth: `True`
```text
ok esabbr
```

### Auth Policy
- Prefer `huggingface-cli login` for durable auth (cached outside VS Code).
- If using env vars, set a user-level `HUGGINGFACE_HUB_TOKEN` (avoid session-only).


## rv (Ruby version manager)

- active ruby: `ruby-4.0.3`
- rv ruby list: `ok`
```text
┌───────────────┬─────────────────────────────────────────────────────┐
│ Version       │ Installed                                           │
├───────────────┼─────────────────────────────────────────────────────┤
│   ruby-2.4.10 │ [available]                                         │
│   ruby-2.5.9  │ [available]                                         │
│   ruby-2.6.10 │ [available]                                         │
│   ruby-2.7.8  │ [available]                                         │
│   ruby-3.0.7  │ [available]                                         │
│   ruby-3.1.7  │ [available]                                         │
│   ruby-3.2.11 │ [available]                                         │
│   ruby-3.3.11 │ [available]                                         │
│   ruby-3.4.9  │ [available]                                         │
│ * ruby-4.0.3  │ ~\AppData\Roaming\rv\rubies\ruby-4.0.3\bin\ruby.exe │
├───────────────┴─────────────────────────────────────────────────────┤
│ * Default version pinned by .ruby-version                           │
└─────────────────────────────────────────────────────────────────────┘
```
- stale installer dirs: none

### rv upgrade workflow
`rv ruby upgrade` does not exist. Correct flow:
```powershell
rv ruby install <new-version>   # e.g. ruby-4.0.3
rv ruby pin <new-version>
```
> **Windows PowerShell note:** `rv` may resolve to the built-in `Remove-Variable` alias.
> Use `rvw` if `rv` commands fail, or set up shell integration: `rv shell powershell`.

