# Toolchain Doctor Report

- Generated: `2026-02-23T16:07:15.982581+00:00`
- bun: `True`
- uv: `True`
- apply: `False`

## Bun

- Audit: PASS (no vulnerabilities)

## uv

- uv sync: executed
```text
Resolved 103 packages in 0.85ms
Uninstalled 24 packages in 2.73s
 - accelerate==1.12.0
 - aiohappyeyeballs==2.6.1
 - aiohttp==3.13.3
 - aiosignal==1.4.0
 - datasets==4.5.0
 - dill==0.4.0
 - frozenlist==1.8.0
 - mpmath==1.3.0
 - multidict==6.7.1
 - multiprocess==0.70.18
 - pandas==3.0.1
 - propcache==0.4.1
 - psutil==7.2.2
 - pyarrow==23.0.1
 - regex==2026.2.19
 - safetensors==0.7.0
 - setuptools==82.0.0
 - sympy==1.14.0
 - tokenizers==0.22.2
 - torch==2.10.0
 - transformers==5.2.0
 - tzdata==2025.3
 - xxhash==3.6.0
 - yarl==1.22.0
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


