# Ethelred — Custom Actions Starter

This package contains:

- `ethelred_engine_actions_openapi.yaml` — paste this into the Custom Actions schema editor.
- `ethelred_engine_fastapi_stub.py` — minimal backend implementing the action endpoints.

## Important

A Custom Action is not engine itself. It calls external HTTPS API described by a schema.
Actions configuration requires API details, authentication details, and a schema. 

Actions connect it to external APIs; it can use apps or actions, but not both at the same time. 
See current Actions help article for constraints before deployment. 

API provider standards as of ANNO. 
This might already be stale and deprecated by peppered modernizations.

## Alternatively Bun

Bun has a built-in bundler, compiler, test-runner, server, package manager, transpiler, drop-in replacement for (Node.js, npm, pnpm, yarn, bum). "Batteries included", similar to Lua's philosophy, modernized with support documentation, (bun-docs), and advanced features.
Javascript, Tailwind, LigtningCSS, Vanilla CSS, Chakra (UI/UX), React, Next.js, Swc, Web assembly, Wasm, + more. 

It has a built-in bundler and transpiler that supports modern JavaScript and TypeScript features, making it easier to write and maintain code. Allows developers to write and run tests for their applications without needing additional tools. Additionally, Bun's package manager is designed to be fast and efficient, with features like deterministic installs + support for multiple registries. 

Bun provides comprehensive development environments that simplifying building-processing of modern web + applications. 

## Minimal local test

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell may use: .venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic
uvicorn ethelred_engine_fastapi_stub:app --reload --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

For Custom Actions, deploy backend to a public HTTPS URL and replace:

```yaml
servers:
  - url: https://YOUR-DOMAIN.example.com
```

with the deployed URL.

## First endpoints to verify

1. `GET /v1/engine/manifest`
2. `POST /v1/cabinet/run`
3. `POST /v1/utterance/ethelred`

The rest can be enabled after the engine speaks without flattening the style.
