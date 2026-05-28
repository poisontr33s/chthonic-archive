---
sid: WPTG_SKILL_ALIGNMENT_RUBRIC_V1
type: reference
status: active
owner: codex
updated: 2026-02-24
---

# WPTG Skill Alignment Rubric

This rubric maps skills to the 7-stage WPTG transmutation pipeline from:
- `WET_PAPER_TO_GOLD_WIP/chthonic-archive_transmutation_framework_original.html`

## Stage Checks

| Stage | Name | Required evidence in skill artifacts |
|---|---|---|
| `00` | Blind Ingestion | `SKILL.md` frontmatter (`name`, `description`) + explicit usage contract (`When to Use`/`triggers`) |
| `01` | Emergent Taxonomy | Flavor/scope derivation (`target-flavor`, `cross-flavor`, or equivalent scope language) |
| `02` | Cartography | Relationship mapping to other artifacts (links, `references/`, cross-reference notes) |
| `03` | Criterion Genesis | Measurable criteria or gates (`verify`, `validation`, `threshold`, `acceptance`) |
| `04` | Transmutation | Script-backed execution (`scripts/` + runnable command snippets) |
| `05` | Verification | Deterministic verification path (`--mode verify`, fixture eval, selftest, regression checks) |
| `06` | Iteration | Iteration memory (`@POLISHED`, trend output, retrospective/baseline promotion cues) |

## Profiles

- `off`: disable WPTG audit.
- `baseline`: include stage coverage and non-blocking WPTG findings.
- `strict`: enforce stage gaps as blocking findings.

## Scoring

- `wptg_score = met_stages / 7 * 100`
- Coverage is emitted per skill in `emit_wptg_json` output.
