---
type: human-reference
scope: functional priming system
generated: 2026-04-15
---

# Functional Priming System

## Purpose

This is the live path.

Only these pieces matter:

- `codex/artifacts/PRIMING_REFERENCE_REGISTRY.toml`
- `codex/artifacts/FUNCTIONAL_ARTIFACT_REGISTRY.toml`
- `codex/artifacts/ANKH_LOGICAL_RESIDUE_REFERENCE.toml`
- `codex/artifacts/INVARIANT_EQUIVALENCE_REGISTRY.toml`
- `scripts/render_priming_packet.py`
- `scripts/build_delegation_packet.py`
- `scripts/benchmark_delegation_lanes.py`
- `scripts/validate_functional_artifacts.py`

## Canonical Outputs

- `codex/artifacts/COMPILED_PRIMING_PACKET_CHIMERA_LOCAL_SINGULARITY.json`
- `codex/artifacts/DELEGATION_PACKET_CANONICAL.json`
- `codex/artifacts/DELEGATION_BENCHMARK_CANONICAL.json`

Human-readable mirrors exist only when explicitly requested.

## Commands

Compile the priming packet:

```powershell
uv run scripts/render_priming_packet.py --packet chimera_local_singularity --write-md
```

Build the delegation packet:

```powershell
uv run scripts/build_delegation_packet.py --preset gemma4-local-delegation --write-md
```

Run the delegation benchmark:

```powershell
uv run scripts/benchmark_delegation_lanes.py --lanes qwen25_14b_baseline --write-md
```

Validate the system:

```powershell
uv run scripts/validate_functional_artifacts.py --json
```

## Rule

If a file has no declared consumer path, it is residue.
If a script emits timestamped duplicates by default, it is adding entropy.
If a human-readable mirror exists, it should mirror a canonical JSON artifact rather than replace it.
