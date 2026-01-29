# Harvest Registry

Tracking completed data harvests from PRs, sessions, and other sources.

---

## Completed Harvests

| ID | Date | Source | Input | Output | Compression | Status |
|----|------|--------|-------|--------|-------------|--------|
| `pr-harvest-2026-01-29` | 2026-01-29 | PRs #1, #2, #5 | ~10,000 lines | ~500 lines | 20:1 | Complete |

---

## Harvest Details

### pr-harvest-2026-01-29

**Location:** [intake/pr-harvest-2026-01-29/](./intake/pr-harvest-2026-01-29/)

**Sources:**
- PR #1: Copilot Pro VS Code Setup Research (closed, never merged)
- PR #2: ANKH semantic lineage framework (closed, harvested)
- PR #5: SSOT_Canon.md governance document (closed, harvested)

**Extracted Artifacts:**

| Tier | Artifact | Description |
|------|----------|-------------|
| 1 | [ssot_hash.py](./intake/pr-harvest-2026-01-29/tier-1-direct/ssot_hash.py) | SHA-256 hash verification utility |
| 1 | [COPILOT_PRO_VSCODE_SETUP_REPORT.md](./intake/pr-harvest-2026-01-29/pr1-copilot-research/tier-1-direct/COPILOT_PRO_VSCODE_SETUP_REPORT.md) | Copilot research doc |
| 2 | [translation_matrix.json](./intake/pr-harvest-2026-01-29/tier-2-schemas/translation_matrix.json) | What survives/decays in translations |
| 2 | [entity_template.json](./intake/pr-harvest-2026-01-29/tier-2-schemas/entity_template.json) | Procedural generation scaffold |
| 2 | [tier_hierarchy.json](./intake/pr-harvest-2026-01-29/tier-2-schemas/tier_hierarchy.json) | RBAC/permission model |
| 2 | [copilot_settings_patch.json](./intake/pr-harvest-2026-01-29/pr1-copilot-research/tier-2-configs/copilot_settings_patch.json) | VS Code settings config |
| 3 | [body_system_metaphor.md](./intake/pr-harvest-2026-01-29/tier-3-conceptual/body_system_metaphor.md) | Architecture documentation pattern |
| 3 | [emoji_vocabulary.md](./intake/pr-harvest-2026-01-29/tier-3-conceptual/emoji_vocabulary.md) | Status indicator vocabulary |

**Disposition:** PRs closed with harvest references

**Methodology:** [WET_PAPER_TO_GOLD_METHODOLOGY.md](../claude/WET_PAPER_TO_GOLD_METHODOLOGY.md)

---

## Pending/In-Progress

| Source | Status | Notes |
|--------|--------|-------|
| [sessionDUMP0001.txt](../claude/sessionDUMP0001.txt) | Analyzed | IDE patch patterns, third patch location open |

---

## Registry Format

When adding new harvests:

```markdown
### harvest-id-YYYY-MM-DD

**Location:** `intake/harvest-id-YYYY-MM-DD/`

**Sources:**
- [Source description]

**Extracted Artifacts:**
| Tier | Artifact | Description |
|------|----------|-------------|

**Disposition:** [What happened to sources]
```
