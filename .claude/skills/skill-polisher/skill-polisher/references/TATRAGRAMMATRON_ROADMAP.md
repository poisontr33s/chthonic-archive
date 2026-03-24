---
type: roadmap
skill: skill-polisher
codename: TATRAGRAMMATRON
created: 2026-02-06
status: ready
---

# TATRAGRAMMATRON Roadmap

## Objective
Upgrade `skill-polisher` from static structural checks to deterministic multi-pass intelligence while preserving repo policy and UV-first execution.

## Constraints
- `uv run <script.py>` default.
- No `cmd /c`, no raw `python`, no raw `pip` in skill workflows.
- Deterministic outputs; no non-reproducible behavior.

## Scope (Meta-Skill Only)
- Modify only `skill-polisher` lane.
- No cross-skill refactors in this phase.

## Phase Gates
1. `STAMP_SCHEMA_V1`
- Add machine schema for stamps.
- Required fields: `stamp`, `severity`, `domain`, `file`, `line`, `message`, `remedy`, `confidence`.

2. `SCORING_ENGINE_V1`
- Domain weights:
- `structure=30`
- `policy=25`
- `semantics=25`
- `maintainability=20`
- Deterministic total score + per-domain score.

3. `RECURSION_PROTOCOL_V1`
- Passes:
- detect
- plan
- apply (explicit flag only)
- verify
- No mutation in detect/plan/verify.

4. `ARTIFACT_EMIT_V1`
- `--emit-stamps-json <path>`
- `--emit-summary-md <path>`
- `--emit-trend-json <path>`

5. `FIXTURE_EVAL_V1`
- Add fixture sets:
- `fixtures/clean`
- `fixtures/drift`
- `fixtures/broken`
- Snapshot expected outputs for regression.

## Acceptance
- All existing `skill-polisher` commands remain backward-compatible.
- `uv run .codex/skills/skill-polisher/scripts/polish_skill.py .codex/skills --all` remains stable.
- New artifacts are generated deterministically.

## Immediate Build Order
1. Implement `STAMP_SCHEMA_V1`.
2. Implement `SCORING_ENGINE_V1`.
3. Run baseline on `.codex/skills --all`.
4. Lock baseline outputs in mailbox artifacts.
