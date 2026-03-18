# Toolchain Doctor Report

- Generated: `2026-02-23T16:04:33.796432+00:00`
- bun: `True`
- uv: `True`
- apply: `False`

## Bun

- Audit: PASS (no vulnerabilities)

## uv

- uv sync: executed
```text
Resolved 103 packages in 0.87ms
Audited 99 packages in 3ms
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


