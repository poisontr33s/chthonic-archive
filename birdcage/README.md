# birdcage

First agentic chamber inside `chthonic-archive`. Bounded, observable, identity-inherited.

## What this is

A minimal probe harness that confirms the auth + routing chain works across three surfaces:

- **Probe A** — Azure-for-GitHub models endpoint (via GHCP Pro+ token)
- **Probe B** — Windows AI Foundry Local (OpenAI-compatible localhost endpoint)
- **Probe C** — VS Code Insiders Copilot Chat (manual, logged into `runs.jsonl`)

Each probe sends the same canary prompt and writes one JSONL line to `runs.jsonl`. That's the bird's tracks.

## What this is not

- Not an agent framework. No tool-calling, no orchestration, no MCP yet.
- Not a satellite. Lives in the hub because it observes the hub.
- Not production. v0 is plumbing verification only.

## Layout

```
birdcage/
├── README.md          # this file
├── pyproject.toml     # uv-managed, Python project
├── cage.toml          # scope walls + endpoint config (no secrets)
├── .env.example       # secrets shape (copy to .env, gitignored)
├── .gitignore
├── probes.py          # all three probes in one file (A, B, C-logger)
└── runs.jsonl         # observability log (created on first run)
```

No subdirs. Six files plus the log. Anything more is premature.

## Identity chain (assumed)

```
GHCP Pro+ token  ──►  Azure-for-GitHub models endpoint   (Probe A)
                 └──► VS Code Insiders Copilot session

(Probe C)

Foundry Local (no token, localhost only)                 (Probe B)
```

If the chain holds, all three probes return `BIRDCAGE-OK` and `runs.jsonl` gets three new lines.

## Bootstrap (Win11 + uv)

```powershell
cd chthonic-archive\birdcage
uv sync
copy .env.example .env
# edit .env — paste GHCP Pro+ token into GITHUB_TOKEN
uv run python probes.py a
uv run python probes.py b
uv run python probes.py c "paste response from Copilot Chat here"
```

## Reading the bird

```powershell
type runs.jsonl
```

Each line: `{ts, probe, surface, model, latency_ms, ok, response_excerpt}`.

## Next chambers (not built yet)

- Grounding probes against `satellites/` content
- Gitological probes — feed git log/diff as context
- Tool-calling cage (Probe D) once A/B/C are green three runs in a row
