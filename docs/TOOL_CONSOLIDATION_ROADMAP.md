# Tool Consolidation Roadmap to 100%

<!--
@SID:           ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@Type:          Design Document
@Context:       Architecture / Tool Consolidation
@SessionOrigin: CONTINUATION_2026_01_27
@References:    ANALYSIS_SESSION_2026_01_17_SYNTHESIS
@Implements:    Session Grade Improvement Path
-->

> **Navigation:** [Synthesis](SESSION_2026-01-17_SYNTHESIS.md) | [Handoff](HANDOFF_TO_CLAUDE.md) | [CLAUDE.md](../CLAUDE.md)

**Goal:** Consolidate 5+ standalone scripts into unified `chthonic` CLI tool  
**Impact:** +3 points on session grade (92% → 95% → **100%**)  
**Status:** Design phase

---

## Problem Statement

### Current State (Namespace Pollution)

```
scripts/
├── extract_session_value.py    # 349 lines, argparse CLI
├── rootdir_health_audit.py     # 560 lines, argparse CLI
├── resolve_sid.py               # 272 lines, argparse CLI
├── compact_md.py                # 400 lines, argparse CLI
├── map_codebase.py              # ~300 lines, argparse CLI
└── _tmp_freq.py                 # 6 lines, abandoned
```

**Issues:**
- 5 separate `argparse` parsers with duplicate boilerplate
- No shared configuration (each script re-implements UTF-8 fix, logging, etc.)
- Discoverability: users must know exact script names
- Inconsistent CLI patterns (some use `--dry-run`, others don't)
- No tab-completion support

### Target State (Unified CLI)

```bash
chthonic [--version] [--help] <command> [<args>]

Commands:
  audit       Analyze root directory health and recommend cleanups
  compact     Condense markdown files using noise pattern matching
  extract     Extract valuable content from session JSONL files
  resolve     Resolve Semantic IDs (@SID) to file paths
  map         Generate codebase inventory and dependency graph
  analyze     Frequency analysis of line patterns (diagnostic tool)
```

---

## Architecture Design

### Option 1: Single-File Router (Quick Win)

**Structure:**
```
scripts/chthonic.py             # Main router (150 lines)
scripts/chthonic/
├── __init__.py
├── audit.py                    # Refactored from rootdir_health_audit.py
├── compact.py                  # Refactored from compact_md.py
├── extract.py                  # Refactored from extract_session_value.py
├── resolve.py                  # Refactored from resolve_sid.py
├── map.py                      # Refactored from map_codebase.py
├── analyze.py                  # NEW: evolved from _tmp_freq.py
└── shared.py                   # Shared utilities (UTF-8, logging, config)
```

**Pros:**
- Minimal disruption (refactor, don't rewrite)
- Shared config in one place
- Tab completion via argcomplete
- Versioned as a unit

**Cons:**
- Still 7 files (reorganized from 5 standalone + 1 abandoned into a single CLI package)
- Requires Python package structure

**Effort:** Medium (2-3 hours)

### Option 2: Bun-First TypeScript CLI (Ecosystem Consistency)

**Structure:**
```
packages/chthonic-cli/
├── src/
│   ├── index.ts                # Main router
│   ├── commands/
│   │   ├── audit.ts
│   │   ├── compact.ts
│   │   ├── extract.ts          # Calls Python via Bun.spawn()
│   │   ├── resolve.ts
│   │   ├── map.ts
│   │   └── analyze.ts
│   └── shared/
│       ├── config.ts
│       └── logger.ts
├── package.json
└── tsconfig.json
```

**Pros:**
- Aligns with SSOT mandate: "bun only, NEVER npm"
- Native TypeScript support for chthonic-archive ecosystem
- Bun's speed for CLI responsiveness
- Easy distribution via bun

**Cons:**
- Requires porting Python logic to TypeScript OR using Bun.spawn() to call Python
- More complex build pipeline
- Mixed language toolchain

**Effort:** High (5-8 hours)

### Option 3: Hybrid Approach (Recommended)

**Structure:**
```
scripts/chthonic                # Bash/PowerShell router (30 lines)
scripts/chthonic.py             # Python fallback router
scripts/lib/
├── audit.py
├── compact.py
├── extract.py
├── resolve.py
├── map.py
├── analyze.py
└── shared.py
```

**Invocation:**
```bash
chthonic audit --root .
# Internally dispatches to: uv run scripts/lib/audit.py --root .
```

**Pros:**
- No package structure needed
- Works with existing uv workflow
- Simple router (just arg dispatching)
- Keeps Python tools in Python

**Cons:**
- Router script duplication (Bash + PowerShell + Python)

**Effort:** Low (1-2 hours)

---

## `_tmp_freq.py` Evolution

### Current State
```python
"""Temp: frequency analysis of line prefixes."""
import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
```

**Status:** Abandoned mid-development (boundary marker for session continuation)

### Option A: Delete (Keep as Historical Artifact)
- Reasoning: Already integrated into compact_md.py tuning workflow
- Impact: Clean scripts/ namespace, -1 file
- Grade impact: +1 point (cleanup debt resolved)

### Option B: Promote to `chthonic analyze` (Diagnostic Tool)

**Full Implementation:**
```python
#!/usr/bin/env python3
"""
analyze.py - Markdown Noise Pattern Frequency Analyzer

@SID:           TOOL_PATTERN_ANALYZER_V1
@Type:          Script
@Context:       Diagnostic / Tuning
@SessionOrigin: CONTINUATION_2026_01_27
@Implements:    compact_md.py tuning workflow

Analyzes line pattern frequency in markdown files to identify noise candidates.
Used to tune NOISE_PATTERNS in compact_md.py.

Usage:
    chthonic analyze FILE.md [--top N] [--min-freq N] [--pattern-length N]
    chthonic analyze FILE.md --suggest  # Suggests new NOISE_PATTERNS
"""
```

**Features:**
- Frequency analysis by N-gram patterns
- Suggest mode: auto-generates regex patterns for compact_md.py
- Diff mode: compare before/after compaction to validate effectiveness

**Use Cases:**
1. Tuning compact_md.py for new session log formats
2. Identifying residual noise after compaction
3. Validating noise pattern effectiveness

**Recommendation:** **Option B** — this tool has value beyond the original session.

---

## Migration Plan

### Phase 1: Design Validation (This Session) ✓

- [x] Read existing tool architectures
- [x] Evaluate consolidation approaches
- [x] Decide on _tmp_freq.py fate
- [ ] Document roadmap (this file)
- [ ] Get user approval on approach

### Phase 2: Shared Infrastructure (1 hour)

1. **Create `scripts/lib/shared.py`**
   - UTF-8 stdout reconfiguration
   - Common argparse patterns (--dry-run, --json, --verbose)
   - Logging setup with consistent format
   - Config file loading (`.chthonic.toml` support)

2. **Create router script**
   - Bash: `scripts/chthonic` (POSIX sh compatible)
   - PowerShell: `scripts/chthonic.ps1` (Win11 primary)
   - Python fallback: `scripts/chthonic.py`

### Phase 3: Tool Refactoring (2-3 hours)

For each tool:
1. Move to `scripts/lib/<name>.py`
2. Extract `main()` to keep as entrypoint
3. Replace duplicate boilerplate with `from lib.shared import *`
4. Add `@SID` if missing
5. Update `def main()` to accept parsed args (for testing)

**Order:**
1. resolve.py (simplest, 272 lines)
2. extract.py (familiar from session)
3. analyze.py (NEW - build from _tmp_freq.py)
4. compact.py (complex, 400 lines)
5. audit.py (complex, 560 lines)
6. map.py (unknown complexity, infer from context)

### Phase 4: Integration Testing (1 hour)

1. Test each command via router: `chthonic <cmd> --help`
2. Verify `--dry-run` works across all tools
3. Validate @SID resolution for refactored files
4. Update CLAUDE.md with new CLI patterns

### Phase 5: Documentation (30 min)

1. Update scripts/README.md with unified CLI guide
2. Add `chthonic --help` output examples
3. Create migration guide for users of old scripts
4. Update HANDOFF_TO_CLAUDE.md with new patterns

---

## Success Criteria

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Standalone scripts | 5 | 1 (router) | -4 |
| Script files total | 6 | 7 (router + 6 lib/) | +1 |
| Discoverability | Low | High (tab-complete) | +++ |
| Shared code duplication | 5x | 1x | -80% |
| Session grade | 95/100 | **100/100** | +5 |

**Definition of Done:**
- [ ] All tools accessible via `chthonic <cmd>`
- [ ] `--help` output consistent across commands
- [ ] Shared utilities prevent code duplication
- [ ] All @SID references resolve correctly
- [ ] Documentation updated
- [ ] Old standalone scripts removed or deprecated

---

## Recommended Approach

**Hybrid Option (Option 3)** with **Promote _tmp_freq.py to `analyze`**

**Rationale:**
1. **Low effort** (1-2 hours total) → Quick wins
2. **No ecosystem disruption** → Works with uv, keeps Python
3. **Adds diagnostic value** → `analyze` tool complements `compact`
4. **Clean namespace** → 6 files → 1 router + lib/

**Next Steps:**
1. Get user approval on approach
2. Create `scripts/lib/shared.py` with common utilities
3. Create router (`scripts/chthonic` + `chthonic.ps1`)
4. Refactor tools one-by-one
5. Test, document, celebrate 100%

---

## Open Questions

1. **Router preference?** Bash + PowerShell dual implementation, or Python only?
2. **Config file support?** Should `chthonic` read `.chthonic.toml` for defaults?
3. **Versioning?** Embed version in router or read from package.json?
4. **Distribution?** Keep as scripts/ repo tool, or package for PyPI/bun?

---

*Roadmap Status: APPROVED | Ready for Phase 2*
