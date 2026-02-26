---
name: conceptualize
description: Perform high-rigor structural and aesthetic audits with findings-first output, actionable remediation, and governance-aware preconditions.
metadata:
  short-description: "Findings-first review and remediation contract."
  refreshed: "2026-02-24"
  archetype: matriarch-refurbished
  prerequisites:
    - "For CDE-KLLR/WPTG/Tribunal work, run codekiller-remediation-gate first."
  triggers:
    - "review"
    - "critique"
    - "refactor"
    - "judge"
    - "audit"
---

# Conceptualize (Refurbished)

Use this skill when the user asks for judgment, review, critique, or refactor quality gates.

## Mandatory Preconditions

1. Classify target domain as `TEMPLE` or `GAME` before judging quality.
2. If request touches Codekiller/CDE-KLLR/WPTG/Tribunal, run:
   - `uv run .codex/skills/codekiller-remediation-gate/scripts/codekiller_remediation_gate.py ...`
3. Use findings-first output. No roleplay blocks, no internal monologue format.

## Output Contract

1. Findings first, ordered by severity (`critical`, `high`, `medium`, `low`).
2. Every finding includes concrete file path and line reference when possible.
3. If no findings exist, explicitly say so and list residual risks/testing gaps.
4. After findings, provide the shortest executable remediation path.
5. When editing, apply patches directly and validate with relevant checks.

## Required Review Shape

1. `Findings`: severity-ordered list with path/line anchors.
2. `Contradiction Map`: where docs, code, and runtime disagree.
3. `Minimal Fix Set`: smallest patch sequence that resolves all `critical/high` findings.
4. `Validation Proof`: commands run and observed pass/fail outcome.
5. `Residual Risk`: what still remains uncertain after fixes.

## Creativity Constraint

- Creativity is required in solution design, not in evidence reporting.
- Inventive refactors must still preserve traceability from finding to fix.
- Never substitute stylistic prose for concrete defect mechanics.

## Review Heuristics

- Structural integrity: correctness, regressions, edge cases, dependency stability.
- Governance integrity: WPTG compliance, no-destroy behavior, reference hygiene.
- Operability: determinism, observability, reproducibility, rollback safety.
- Aesthetic quality: clarity, naming precision, cohesion, unnecessary complexity.

## Guardrails

- Do not use insulting language.
- Do not fabricate hidden chain-of-thought blocks.
- Do not bypass permissions for destructive actions.
- Do not substitute style commentary for concrete engineering findings.

<!-- @REFURBISHED: 2026-02-24 -->

## Cross-Flavor Compatibility
- Codex flavor: requires `agents/openai.yaml` and `assets/` with SVG icons.
- Claude flavor: requires `SKILL.md` with valid frontmatter (`name`, `description`), optional `allowed-tools`.
- For shared audits use: `python scripts/skill_audit.py --flavor codex --root .codex/skills` and `python scripts/skill_audit.py --flavor claude --root .claude/skills`.
