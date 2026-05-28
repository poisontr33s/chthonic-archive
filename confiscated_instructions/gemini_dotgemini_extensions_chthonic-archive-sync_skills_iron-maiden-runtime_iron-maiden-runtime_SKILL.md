---
name: iron-maiden-runtime
description: Deterministic runtime harness for The Iron Maiden voicepack (state model, contract schema, scene renderer).
argument-hint: "uv run .codex/skills/iron-maiden-runtime/scripts/render_scene.py --voicepack <voicepack.json> --state <state.json> --prompt <text>"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - exec_command
---

# Iron Maiden Runtime

This skill turns the Iron Maiden SSOT into an executable, deterministic loop:

- A canonical `voicepack.json` (acts, voices, creeds, core rules)
- A deterministic `state.json` (NPCs, inventory, injuries, plot threads)
- A renderer that produces:
  - a scene
  - 3-5 options
  - a voice trace (which voices fired and why)

## Canonical Voicepack

Generate (canonicalizes legacy model handle text to `THE ENGINE`):

```ps1
uv run scripts/extract_voicepack.py codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md --canonical-target "THE ENGINE"
```

Voicepack file:

- `codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json`

## State Model

Schemas:

- `.codex/skills/iron-maiden-runtime/references/runtime_contract.schema.json`
- `.codex/skills/iron-maiden-runtime/references/state.schema.json`

Example state:

- `.codex/skills/iron-maiden-runtime/references/state.example.json`

## Render A Scene

```ps1
uv run .codex/skills/iron-maiden-runtime/scripts/render_scene.py `
  --voicepack codex/codex-session-logs/The-Iron-Maiden-(SSOT)-Copyright-Savant.md.voicepack.json `
  --state .codex/skills/iron-maiden-runtime/references/state.example.json `
  --prompt "You push through the door of The Rusty Tap."
```
