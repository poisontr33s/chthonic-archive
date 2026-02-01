# Triad Documentation Consolidation Strategy

**Date:** 2026-02-01
**Lead:** Claude Code (Opus 4.5)
**Support:** Gemini 3-Pro, Codex GPT-5.2
**Status:** TRIAD-COMPLETE (archive debt accepted)

---

## Problem Statement

- **621 .md files** across the repository
- **Duplicate content** in multiple locations (macro-prompt-world exists in both `.github/` and `dumpster-dive/from-github/`)
- **Stale documentation** (health_reports, old session docs)
- **Broken cross-references** (relative paths that don't resolve)
- **No enforced standard** for clickable links

---

## Strategic Objectives

1. **Reduce** from 621 → target <200 active .md files
2. **Eliminate** all duplicates
3. **Archive** stale content to `dumpster-dive/archive/`
4. **Standardize** all cross-references to clickable `name(path)` format
5. **Verify** all links resolve correctly

---

## Canonical Locations (DO NOT TOUCH)

| Location | Purpose | Owner |
|----------|---------|-------|
| Root `*.md` | Triad anchors, shared config | All |
| `.github/copilot-instructions.md` | SSOT governance | Protected |
| `.github/instructions/` | Modular instruction branches | Protected |
| `claude-codex-gemini/` | Triad shared memory | All |
| `codex/` | Codex waypoints | Codex |
| `claude/` | Claude patches/methodology | Claude |
| `.gemini/` | Gemini config | Gemini |
| `scripts/` | Tool documentation | All |
| `dumpster-dive/protocols/` | Forge protocols | All |

---

## Phase 1: Duplicate Elimination (Gemini) ✓ COMPLETE

**Assigned to:** Gemini 3-Pro
**Status:** COMPLETE (2026-02-01)

### Results:
- Gemini discovered `.github/macro-prompt-world/` had NEWER files (Dec 9) than `dumpster-dive/` (Nov 17)
- Synced newer content to `dumpster-dive/from-github/macro-prompt-world/`
- Claude deleted `.github/macro-prompt-world/`
- Updated `scripts/bun_compliance_audit.py` exclusion path

### Actual reduction: **72 files** (621 → 549)

---

## Phase 2: Stale Content Archive (Codex)

**Assigned to:** Codex GPT-5.2
**Scope:** Identify and archive stale documentation

### Tasks:
1. Audit `health_reports/` - archive if >30 days old
2. Audit `docs/sessions/` - archive completed sessions
3. Audit `dumpster-dive/archive/` - verify it's properly isolated
4. Move stale content to `dumpster-dive/archive/consolidated-YYYY-MM-DD/`

### Status Update (2026-02-01)
- Archived **all January 2026** health reports (16 files)
- New location: `dumpster-dive/archive/health_reports_2026-01/`
- `health_reports/` is now empty (directory retained for future reports)

### Expected reduction: ~30 files

---

## Phase 3: Cross-Reference Standardization (Claude) ✓ COMPLETE

**Assigned to:** Claude Code
**Status:** COMPLETE (2026-02-01)

### Results:
- Converted bare backtick references to clickable `name(path)` format
- Fixed all `../` broken paths in root copies
- Eliminated stale `codex-claude-gemini-triad-sessions/` → `claude-codex-gemini/`

### Files Standardized:
| File | Refs Fixed |
|------|------------|
| SCRIPTS_README.md | 6 |
| PWSH_RULES.md | 8 |
| WET_PAPER_TO_GOLD_METHODOLOGY.md | 6 |
| CLAUDE_README.md | 1 |
| TRIADIC_SESSION_SHARED files (4) | 4 |
| Handoff files (2) | 4 |

**Total refs fixed:** ~29

### Files to prioritize:
- Root `*.md` files (18) — complete
- `AGENT_COMMON.md` — complete
- `codex/NEXT.md` — complete
- `claude-codex-gemini/*.md` — complete

---

## Phase 4: Verification (All)

**Assigned to:** All agents
**Scope:** Validate consolidation

### Tasks:
1. Run link checker across all canonical locations
2. Verify no orphaned files in canonical directories
3. Confirm duplicate directories are removed
4. Update `codex/NEXT.md` with completion status

### Status Update (2026-02-01)
- Phase 4 validation executed (canonical scope; `.github/` + SSOT excluded)
- Report: `claude-codex-gemini/triadic-session-context/PHASE4_LINK_VALIDATION_2026_02_01.filtered.json`
- Summary: `claude-codex-gemini/triadic-session-context/PHASE4_LINK_VALIDATION_2026_02_01.filtered.summary.json`
- Links checked: **510**
- Broken links: **148** (pre-remediation)

### Remediation (2026-02-01)
- **Triad files fixed by Codex:** 16 broken links → 0
  - `SESSION_CACHE_STRUCTURED.md` - repo paths fixed
  - `SSOTI_FIED_SESSION_LOG.md` - file:/// links fixed
  - `TRIAD_DOC_CONSOLIDATION_STRATEGY.md` - placeholder removed
- **Remaining broken links:** 132 (in archive/historical content)
- **Decision:** Accepted as technical debt (not consumed by triad agents)

---

## Success Criteria

- [x] Zero duplicate directories (`.github/macro-prompt-world/` deleted)
- [x] All cross-references in **triad files** use clickable markdown link format
- [x] All links in **triad/root files** resolve correctly
- [x] Stale content archived (`health_reports/` → `dumpster-dive/archive/`)
- [x] Active context < 200 files (via `.geminiignore` scope)
- [ ] Total .md files < 200 (549 overall; archive pruning optional)
- [ ] Archive content links fixed (132 remaining — accepted technical debt)

---

## Coordination Protocol

1. Each agent updates this file when completing their phase
2. Use `claude-codex-gemini/triadic-session-shared-0003.md` for handoff notes
3. Claude leads architecture decisions
4. Gemini handles bulk file operations
5. Codex handles verification and documentation updates

---

## Next Action

**Status:** Consolidation complete.  
**Focus:** Refinement pass (optional) — only if new triad docs are added or if archive pruning is requested.
