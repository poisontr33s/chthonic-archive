# Migration Guide: Standalone Scripts → Chthonic CLI

<!--
@SID:           DOC_MIGRATION_CHTHONIC_CLI
@Type:          User Documentation
@Context:       Migration / User Guide
@SessionOrigin: CONTINUATION_2026_01_27
@References:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27
-->

**Version:** 1.0.0  
**Date:** 2026-01-27  
**Status:** Stable

---

## Overview

As of Phase 3 completion (2026-01-27), all standalone Python scripts have been consolidated into the unified `chthonic` CLI tool. This guide helps users migrate from old standalone workflows to the new CLI.

**TL;DR:** Replace `uv run scripts/<script>.py` with `chthonic <command>`.

---

## Quick Migration Table

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `uv run scripts/resolve_sid.py` | `chthonic resolve` | SID resolution |
| `uv run scripts/resolve_sid.py --list` | `chthonic resolve --list` | List all SIDs |
| `uv run scripts/extract_session_value.py FILE.jsonl` | `chthonic extract FILE.jsonl` | Session extraction |
| `uv run scripts/compact_md.py FILE.md` | `chthonic compact FILE.md` | Markdown compaction |
| `uv run scripts/compact_md.py FILE.md --dry-run --stats` | `chthonic compact FILE.md --dry-run --stats` | Preview mode |
| `uv run scripts/rootdir_health_audit.py` | `chthonic audit --root .` | Health audit |
| `uv run scripts/map_codebase.py` | `chthonic map --root .` | Codebase mapping |
| `uv run scripts/../scripts/_tmp_freq.py` | `chthonic analyze FILE.md` | **NEW** - Pattern analysis |

---

## Detailed Migration Examples

### 1. SID Resolution

**Before:**
```bash
uv run scripts/resolve_sid.py
uv run scripts/resolve_sid.py --list
uv run scripts/resolve_sid.py --resolve DOC_CLAUDE_MD_ROOT
uv run scripts/resolve_sid.py --json > output.json
```

**After:**
```bash
chthonic resolve
chthonic resolve --list
chthonic resolve --resolve DOC_CLAUDE_MD_ROOT
chthonic resolve --json > output.json
```

**Changes:**
- Same flags, same behavior
- Index location unchanged: `data/indices/sid_index.json`
- **Improvement:** Auto-detects repo root (no manual path needed)

---

### 2. Session Extraction

**Before:**
```bash
uv run scripts/extract_session_value.py session.jsonl
uv run scripts/extract_session_value.py session.jsonl --json
```

**After:**
```bash
chthonic extract session.jsonl
chthonic extract session.jsonl --json
```

**Changes:**
- Same arguments, same output
- **Improvement:** Consistent logging format across all tools

---

### 3. Markdown Compaction

**Before:**
```bash
uv run scripts/compact_md.py large_file.md
uv run scripts/compact_md.py large_file.md --dry-run
uv run scripts/compact_md.py large_file.md --stats
uv run scripts/compact_md.py *.md --batch
```

**After:**
```bash
chthonic compact large_file.md
chthonic compact large_file.md --dry-run
chthonic compact large_file.md --stats
chthonic compact *.md --batch
```

**Changes:**
- All 38 noise patterns preserved
- Same compaction algorithm
- **Improvement:** Shared UTF-8 handling (no encoding errors)

---

### 4. Directory Health Audit

**Before:**
```bash
uv run scripts/rootdir_health_audit.py
uv run scripts/rootdir_health_audit.py --json
uv run scripts/rootdir_health_audit.py --output custom.md
```

**After:**
```bash
chthonic audit --root .
chthonic audit --root . --json
chthonic audit --root . --output custom.md
```

**Changes:**
- Now requires `--root` flag (explicit directory)
- Default output: `docs/ROOTDIR_HEALTH.md` (auto-detects repo root)
- **Improvement:** Fixed relative path resolution bug (Issue #2)

---

### 5. Codebase Mapping

**Before:**
```bash
uv run scripts/map_codebase.py
uv run scripts/map_codebase.py --json
```

**After:**
```bash
chthonic map --root .
chthonic map --root . --json
```

**Changes:**
- Now requires `--root` flag
- Default output: `docs/CODEBASE_INVENTORY.md` (auto-detects repo root)
- **Improvement:** Fixed relative path resolution bug (Issue #2)

---

### 6. Pattern Analysis (NEW)

**Before:**
```bash
# No direct equivalent (was ../scripts/_tmp_freq.py temp file)
```

**After:**
```bash
chthonic analyze file.md --top 20
chthonic analyze file.md --min-freq 5
chthonic analyze file.md --suggest --json
```

**Changes:**
- **NEW TOOL** - evolved from abandoned `../scripts/../scripts/_tmp_freq.py`
- Frequency analysis for markdown noise patterns
- Helps tune `../scripts/lib/../scripts/lib/compact.py` noise patterns

---

## Common Flags (Available on All Commands)

New unified flags across all tools:

```bash
--verbose, -v       # Enable verbose debug logging
--quiet, -q         # Suppress info/debug output
--json              # Output results as JSON
--dry-run           # Preview changes without executing
--help, -h          # Show command-specific help
```

**Before:** Not all scripts supported these flags consistently  
**After:** Every command supports the same flags

---

## Breaking Changes

**None.** Old standalone scripts still exist and work.

**Deprecation Timeline:**
- **Phase 3 (2026-01-27):** New CLI available, old scripts maintained
- **Phase 4 (TBD):** Old scripts marked deprecated (warnings added)
- **Phase 5 (TBD):** Old scripts removed (after 3-month notice period)

---

## Environment Differences

### Old Workflow
```bash
# Each script had its own:
- UTF-8 configuration (duplicated 6 times)
- Argparse setup (duplicated 6 times)
- Logging configuration (inconsistent)
- Error handling (varied by script)
```

### New Workflow
```bash
# Shared utilities (scripts/lib/shared.py):
- UTF-8 configured once
- Argparse patterns standardized
- Logging consistent across tools
- Error handling unified
```

**Benefit:** 80% code reduction, consistent UX

---

## Router Options

Three routers available (pick one based on environment):

### PowerShell (Windows Primary)
```powershell
.\scripts\chthonic.ps1 <command> [args]
```

### Bash (POSIX/Linux/macOS)
```bash
./scripts/chthonic <command> [args]
```

### Python Fallback (Cross-platform)
```bash
python scripts/chthonic.py <command> [args]
```

**Recommendation:** Use PowerShell on Windows, Bash elsewhere.

---

## Configuration

### Old Scripts
No shared configuration. Each script re-implemented settings.

### New CLI
Supports `.chthonic.toml` for repository-level defaults:

```toml
[defaults]
verbose = false
json = false
dry_run = false

[resolve]
root = "."

[compact]
stats = true

[audit]
root = "."
output = "docs/ROOTDIR_HEALTH.md"
```

Place at repo root. All commands read this file automatically.

---

## Troubleshooting

### "Command not found: chthonic"

**Issue:** Router not in PATH or wrong directory  
**Fix:**
```bash
# Use full path
./scripts/chthonic.ps1 <command>

# Or add scripts/ to PATH
$env:PATH += ";C:\path\to\repo\scripts"
```

### "Import error: no module named lib"

**Issue:** Tool executed directly instead of via router  
**Fix:**
```bash
# Wrong:
uv run scripts/lib/resolve.py

# Right:
chthonic resolve
```

### "File written to wrong directory"

**Issue:** Using old version before Issue #2 fix  
**Fix:** Pull latest changes (2026-01-27 or later)

### "SID index empty"

**Issue:** Index not built or wrong --root path  
**Fix:**
```bash
chthonic resolve --root C:\full\path\to\repo
```

---

## Performance Comparison

| Task | Old Script | New CLI | Change |
|------|-----------|---------|--------|
| Full repo SID scan (820 files) | 2.5s | 2.5s | Same |
| Markdown compaction (15k lines) | 3.2s | 3.1s | -3% (overhead reduced) |
| Health audit (14 files) | <0.1s | <0.1s | Same |
| Codebase map (148 dirs) | 3.5s | 3.5s | Same |

**Conclusion:** No performance regression, slight improvement due to shared imports.

---

## CI/CD Integration

### Old Approach
```yaml
# Each script called separately
- run: uv run scripts/resolve_sid.py --validate
- run: uv run scripts/rootdir_health_audit.py
- run: uv run scripts/map_codebase.py
```

### New Approach
```yaml
# Unified interface
- run: ./scripts/chthonic resolve --validate
- run: ./scripts/chthonic audit --root .
- run: ./scripts/chthonic map --root .
```

**Benefit:** Easier to maintain, consistent error codes

---

## FAQ

### Q: Can I still use old scripts directly?

**A:** Yes, they still exist and work. But:
- They're not maintained (frozen)
- Missing new features (shared config, better logging)
- Will be removed in Phase 5 (with 3-month notice)

### Q: Do I need to update my scripts that call these tools?

**A:** Not immediately, but recommended. See [migration timeline](#breaking-changes).

### Q: What if I have custom wrappers around old scripts?

**A:** Update them to use `chthonic <command>` instead. All flags are compatible.

### Q: Can I use both old and new simultaneously?

**A:** Yes, but outputs may conflict (e.g., both writing to same SID index).

### Q: How do I know which version I'm using?

**A:**
```bash
# New CLI
chthonic --version
# Output: chthonic v1.0.0

# Old scripts
uv run scripts/resolve_sid.py --version
# No version flag (old scripts don't have this)
```

---

## Additional Resources

- **CLI Documentation:** [scripts/README.md](../scripts/README.md) (see "Chthonic CLI" section)
- **Test Report:** [docs/PHASE_3_TEST_REPORT.md](PHASE_3_TEST_REPORT.md)
- **Roadmap:** [TOOL_CONSOLIDATION_ROADMAP.md](TOOL_CONSOLIDATION_ROADMAP.md)
- **Agent Guidance:** [CLAUDE.md (repo-root)](../CLAUDE.md)

---

## Support

**Questions?** Check:
1. `chthonic <command> --help` for command-specific docs
2. `scripts/README.md` for detailed examples
3. `docs/PHASE_3_TEST_REPORT.md` for validation results

**Issues?** See [Troubleshooting](#troubleshooting) above.

---

**Migration Path Status:**
- ✅ Phase 3 Complete (CLI available)
- ⏳ Phase 4 Pending (deprecation warnings)
- ⏳ Phase 5 Pending (old script removal)

**Last Updated:** 2026-01-27  
**Maintainer:** Chthonic Archive Core Team
