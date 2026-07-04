# Toolchain Doctor Report

- Generated: `2026-06-20T21:29:32.798611+00:00`
- bun: `False`
- uv: `True`
- rv: `False`
- apply: `False`

## uv

- uv sync: executed
```text
Resolved 237 packages in 2ms
Checked 205 packages in 36ms
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


