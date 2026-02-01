# Triad Documentation Consolidation Strategy

**Date:** 2026-02-01
**Lead:** Claude Code (Opus 4.5)
**Support:** Gemini 3-Pro, Codex GPT-5.2
**Status:** In Progress

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
4. **Standardize** all cross-references to clickable `[name](path)` format
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

## Phase 3: Cross-Reference Standardization (Claude)

**Assigned to:** Claude Code
**Scope:** Ensure all .md files use clickable cross-references

### Standard Format:
```markdown
[filename.md](relative/path/to/filename.md)
[Directory Name](relative/path/to/directory/)
```

### Tasks:
1. Scan all canonical .md files for bare text references
2. Convert to clickable `[name](path)` format
3. Verify all paths resolve from file location
4. Fix broken links

### Files to prioritize:
- Root `*.md` files (18)
- `AGENT_COMMON.md`
- `codex/NEXT.md`
- `claude-codex-gemini/*.md`

---

## Phase 4: Verification (All)

**Assigned to:** All agents
**Scope:** Validate consolidation

### Tasks:
1. Run link checker across all canonical locations
2. Verify no orphaned files in canonical directories
3. Confirm duplicate directories are removed
4. Update `codex/NEXT.md` with completion status

---

## Success Criteria

- [ ] Total .md files < 200
- [ ] Zero duplicate directories
- [ ] All cross-references use `[name](path)` format
- [ ] All links in canonical files resolve correctly
- [ ] Stale content archived with manifest

---

## Coordination Protocol

1. Each agent updates this file when completing their phase
2. Use `claude-codex-gemini/triadic-session-shared-0003.md` for handoff notes
3. Claude leads architecture decisions
4. Gemini handles bulk file operations
5. Codex handles verification and documentation updates

---

## Next Action

**Gemini:** Begin Phase 1 - audit macro-prompt-world duplicates
**Codex:** Begin Phase 2 - audit health_reports staleness
**Claude:** Begin Phase 3 - cross-reference standardization on root files
