# Harvest Registry

Tracking completed data harvests from PRs, sessions, and other sources.

---

## Completed Harvests

| ID | Date | Source | Input | Output | Compression | Status |
|----|------|--------|-------|--------|-------------|--------|
| `pr-harvest-2026-01-29` | 2026-01-29 | PRs #1, #2, #5 | ~10,000 lines | ~500 lines | 20:1 | Complete |
| `overnight-daemon` | 2026-02-03 | Local intake | daemon scripts | curated files | n/a | Complete |
| `sentry-probe` | 2026-02-03 | Local intake | probe scripts | curated files | n/a | Complete |
| `toolchain-probe` | 2026-02-03 | Local intake | probe scripts | curated files | n/a | Complete |
| `claudine-harvest` | 2026-02-03 | Local intake | external scripts | curated files | n/a | Complete |
| `protocols` | 2026-02-03 | Local intake | protocol docs | curated files | n/a | Complete |
| `templates` | 2026-02-03 | Local intake | templates | curated files | n/a | Complete |
| `ore-batch-2025-12-30` | 2025-12-30 | Local intake | ore batch | curated file | n/a | Complete |
| `claude-ide-harden-2026-02-10` | 2026-02-10 | Local intake | patch cascade | canonical entrypoint | n/a | Complete |

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

### claude-ide-harden-2026-02-10

**Location:** [intake/claude-ide-harden-2026-02-10/](./intake/claude-ide-harden-2026-02-10/)

**Sources:**
- Local intake (VS Code Insiders + Claude Code + MCP hardening scripts and logs)

**Extracted Artifacts:**

| Tier | Artifact | Description |
|------|----------|-------------|
| 1 | `tier-1-direct/scripts/claude_ide.ps1` | Canonical Claude IDE entrypoint (`heal|health|write-mcp|persist-env|crossover`) |
| 1 | `tier-1-direct/scripts/claude_process_wrapper.ps1` | VS Code wrapper (loads tokens + heal + healthcheck before spawning) |
| 1 | `tier-1-direct/scripts/claude_process_wrapper.bat` | Wrapper shim for VS Code setting |
| 1 | `tier-1-direct/scripts/claude_healthcheck.ps1` | Writes `codex/mailbox/CLAUDE_IDE_HEALTH_LATEST.json` |
| Raw | `raw/scripts/patch-claude-insiders.ps1` | Historical patch logic kept for mining |

**Disposition:** Canonical path remains in `scripts/` (operational). Historical sources copied here for audit/mining.

**Methodology:** [WET_PAPER_TO_GOLD_METHODOLOGY.md](../claude/WET_PAPER_TO_GOLD_METHODOLOGY.md)

---

### overnight-daemon

**Location:** [intake/overnight-daemon/](./intake/overnight-daemon/)

**Sources:**
- Local intake (daemon scripts)

**Extracted Artifacts:**
- Intake folder contents (see location)

**Disposition:** Archived to intake for review

---

### sentry-probe

**Location:** [intake/sentry-probe/](./intake/sentry-probe/)

**Sources:**
- Local intake (probe scripts)

**Extracted Artifacts:**
- Intake folder contents (see location)

**Disposition:** Archived to intake for review

---

### toolchain-probe

**Location:** [intake/toolchain-probe/](./intake/toolchain-probe/)

**Sources:**
- Local intake (probe scripts)

**Extracted Artifacts:**
- Intake folder contents (see location)

**Disposition:** Archived to intake for review

---

### claudine-harvest

**Location:** [intake/claudine-harvest/](./intake/claudine-harvest/)

**Sources:**
- Local intake (external Claudine scripts)

**Extracted Artifacts:**
- Intake folder contents (see location)

**Disposition:** Archived to intake for review

---

### protocols

**Location:** [protocols/](./protocols/)

**Sources:**
- Local intake (protocol docs)

**Extracted Artifacts:**
- Protocol directory contents (see location)

**Disposition:** Archived to dumpster-dive/protocols

---

### templates

**Location:** [intake/templates/](./intake/templates/)

**Sources:**
- Local intake (templates)

**Extracted Artifacts:**
- Intake folder contents (see location)

**Disposition:** Archived to intake for review

---

### ore-batch-2025-12-30

**Location:** [intake/INSTRUCTIONS_ORE_BATCH_20251230.md](./intake/INSTRUCTIONS_ORE_BATCH_20251230.md)

**Sources:**
- Local intake (ore batch instructions)

**Extracted Artifacts:**
- INSTRUCTIONS_ORE_BATCH_20251230.md

**Disposition:** Archived to intake for review

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
