# Toolchain Doctor Report

- Generated: `2026-02-09T17:01:54.215670+00:00`
- bun: `True`
- uv: `True`
- apply: `False`

## Bun

- Audit: PASS (no vulnerabilities)

## uv

- uv sync: executed
```text
Resolved 97 packages in 2ms
Audited 93 packages in 4ms
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
- auth: `False`
```text
fail HfHubHTTPError Invalid user token. The token from HF_TOKEN environment variable is invalid. Note that HF_TOKEN takes precedence over `hf auth login`.
```

### Auth Policy
- Prefer `huggingface-cli login` for durable auth (cached outside VS Code).
- If using env vars, set a user-level `HUGGINGFACE_HUB_TOKEN` (avoid session-only).


