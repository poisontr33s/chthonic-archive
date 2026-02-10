# Toolchain Doctor Report

- Generated: `2026-02-07T18:05:24.074714+00:00`
- bun: `False`
- uv: `True`
- apply: `False`

## uv

- uv sync: executed
```text
Resolved 97 packages in 0.72ms
Audited 93 packages in 3ms
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


