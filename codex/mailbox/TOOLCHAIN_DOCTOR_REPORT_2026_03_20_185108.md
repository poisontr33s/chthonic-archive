# Toolchain Doctor Report

- Generated: `2026-03-20T18:51:08.358398+00:00`
- bun: `True`
- uv: `True`
- apply: `False`

## Bun

- Audit: PASS (no vulnerabilities)

## uv

- uv sync: executed
```text
Resolved 125 packages in 1ms
Uninstalled 4 packages in 1.88s
 - mas-mcp==0.2.0 (from file:///C:/Users/eldno/chthonic-archive/mas_mcp)
 - ml-dtypes==0.5.4
 - onnx==1.20.1
 - protobuf==7.34.0
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


