# spec-enforcer

Neural Bus event loop service for Chthonic.

## Purpose

Watches `.chthonic/specs/*.md` and executes the local feedback loop:
1. Detect spec create/modify.
2. Extract `Intent` / `Objective`.
3. Trigger context refresh through `context-compressor`.
4. Emit `handoff_signal.json` for downstream implementation agents.

## Run

```powershell
bun run src/index.ts
```

One-shot mode for the latest spec:

```powershell
bun run src/index.ts --once
```

One-shot mode for an explicit spec file:

```powershell
bun run src/index.ts --once --spec .chthonic/specs/my_spec.md
```

## Outputs

- `extensions/spec-enforcer/handoff_signal.json`
- `.chthonic/cache/neural-bus/handoff_signal.json`
- `.chthonic/cache/neural-bus/latest_context.md`

