# PR Harvest Manifest — 2026-01-29

## Source Material

| PR | Title | Status | Lines | Origin |
|----|-------|--------|-------|--------|
| #1 | Copilot Pro VS Code Setup Research | Closed | +444 | copilot-swe-agent |
| #2 | ANKH semantic lineage framework | Draft | +1,227 | copilot-swe-agent |
| #5 | SSOT_Canon.md governance document | Open | +8,380 | GPT-5.2 posturing |

## Context

PRs #2 and #5 encoded a fundamental misunderstanding: treating "ANKH" (intended as Egyptological ☥ symbol) as an acronym for a governance framework. PR #1 contains valuable Copilot research that was closed without merge. Rather than discard, we transmute.

**Wet-Paper-to-Gold Principle:** Nothing is waste if you see the extractable value.

---

## PR #1 Harvest (Copilot Research)

High-value research that was closed without merge. **Tier-1 directly usable.**

### Extracted Files

| File | Description | Target |
|------|-------------|--------|
| `COPILOT_PRO_VSCODE_SETUP_REPORT.md` | Full research report | Reference documentation |
| `copilot_settings_patch.json` | Optimal settings + YOLO mode | `.vscode/settings.json` integration |

### Key Value

- Multi-model support matrix (Claude, Gemini, GPT)
- YOLO mode configuration (auto-approve patterns)
- Tier comparison (Free/Pro/Pro+/Business/Enterprise)
- Extension recommendations
- Agent (@workspace, @terminal, @vscode) documentation

---

## Extraction Tiers

### Tier 1: Direct Use (Immediate Value)

| File | Source | Target | Notes |
|------|--------|--------|-------|
| `ssot_hash.py` | PR #2 | `scripts/ssot_hash.py` | SHA-256 hash verification for drift detection. Clean utility, no mythology. |

**Action:** Copy to `scripts/` and use directly.

### Tier 2: Schema Definitions (Structured Data)

| File | Source | Description |
|------|--------|-------------|
| `translation_matrix.json` | PR #2 ankh.md | What survives/decays/prohibited in translations. Useful for validation schemas. |
| `entity_template.json` | PR #2 entity files | Template structure for procedural entity generation. |
| `tier_hierarchy.json` | PR #5 SSOT_Canon.md | Hierarchical authority model. Maps to RBAC, microservice tiers, agent orchestration. |

**Action:** Use as schema templates, test fixtures, or procedural generation inputs.

### Tier 3: Conceptual Salvage (Repurposed Metaphors)

| File | Source | Repurpose |
|------|--------|-----------|
| `body_system_metaphor.md` | PR #5 body system mapping | Microservice architecture documentation metaphor. |
| `emoji_vocabulary.md` | PR #5 emoji semantic layer | Consistent status indicators for commits, logs, dashboards. |

**Action:** Reference for documentation patterns, not mythology.

### Raw (Unprocessed Source)

| File | Source | Notes |
|------|--------|-------|
| `pr2_patches.json` | All PR #2 file patches | Complete (42KB) |
| `pr5_patches.json` | PR #5 metadata | Patch null - file too large for API |

**Note:** Full SSOT_Canon.md (8,380 lines) available via `gh pr diff 5` or branch checkout.

**Action:** Mine for additional patterns as needed.

---

## PR Disposition

### PR #2 — Recommend: Close (Draft)
- Core concept (ANKH as framework) is mislabeled
- Useful pieces extracted (ssot_hash.py, entity templates)
- No merge value remaining

### PR #5 — Recommend: Close
- Massive redundancy with existing SSOT
- GPT-5.2 "posturing" without practical utility
- Useful structures extracted (tier hierarchy, emoji vocab)
- 8,380 lines is unmaintainable

---

## Transmutation Summary

```
Input:  ~9,600 lines of mislabeled mythology
Output:
  - 1 working utility script (182 lines)
  - 3 JSON schemas (~180 lines total)
  - 2 documentation patterns (~100 lines total)
  - Raw material for future mining

Compression ratio: ~20:1
Value extraction: High
Mythology residue: Sanitized
```

---

## Next Steps

1. [ ] Copy `ssot_hash.py` to `scripts/` if hash verification desired
2. [ ] Validate schemas against actual use cases
3. [ ] Close PR #2 and #5 with note pointing to this harvest
4. [ ] Consider renaming `ankh_atlas/` to reflect actual intent (Egyptological, not acronym)

---

---

## Session Meta-Learning

### Error Pattern Corrections

See [SESSION_ERROR_LEARNINGS.md](./SESSION_ERROR_LEARNINGS.md) for detailed analysis.

| Error Type | Root Cause | Correction |
|------------|------------|------------|
| Shell nesting | Bash→pwsh pipe | Use pure pwsh or pure gh |
| String formatting | Bash brace expansion | Write to .ps1 file first |
| find/ls usage | Bash-first habit | Use Get-ChildItem |

**[PWSH_RULES.md](../../../docs/PWSH_RULES.md) Lines Violated:** 35, 38, 154

### Sub-Agent Delegation Patterns (Emerging)

Based on this session, patterns for effective sub-agent use:

| Task Type | Agent | Notes |
|-----------|-------|-------|
| Codebase exploration | `Explore` | Use for open-ended searches |
| File operations | Direct tools | Glob, Read, Write — avoid Task overhead |
| GitHub API | Direct `gh` | Don't pipe to pwsh |
| Complex extraction | `.ps1` script | Write script, then execute |

**Iterative Refinement:** Each session should capture error patterns and update learnings for future use.

---

**Harvested:** 2026-01-29
**Harvester:** Claude Opus 4.5 + The Savant
**Methodology:** Wet-paper-to-gold selective uptake + error pattern learning
