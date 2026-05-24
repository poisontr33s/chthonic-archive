<!--
================================================================================
SEMANTIC IDENTITY (Anchor & Signal Protocol)
================================================================================
@SID:           DOC_SCRIPTS_README
@Type:          Documentation
@Context:       Tooling
@UpdateFrequency: Medium
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
================================================================================
-->

# Directory: scripts/

## Purpose
Production-ready tools for repository governance, environment detection, session extraction, and code health analysis.

**Primary Interface:** Unified `chthonic` CLI tool (see [Chthonic CLI](#chthonic-cli) below)

## Contents
- `chthonic`, `chthonic.ps1`, `chthonic.py`: Unified CLI routers
- `lib/*.py`: Core CLI tools (audit, compact, extract, resolve, map, analyze)
- `*.ps1`: PowerShell probes (Shell Capabilities, Environment)
- `*.ts`: TypeScript/MCP tools

## Ownership
- **Steward:** `TOOL_CODEBASE_MAPPER_V1`
- **Maintainer:** Core Engine Team

---

# Chthonic CLI

**@SID:** TOOL_CHTHONIC_ROUTER_PYTHON (and variants)  
**Version:** 1.0.0  
**Documentation:** Phase 3 complete, production-ready

## Quick Start

```powershell
# Show available commands
.\scripts\chthonic.ps1 --help

# Resolve a Semantic ID to its file path
.\scripts\chthonic.ps1 resolve --resolve DOC_CLAUDE_MD_ROOT

# Analyze line patterns in markdown
.\scripts\chthonic.ps1 analyze file.md --top 10

# Compact markdown files (remove noise)
.\scripts\chthonic.ps1 compact file.md --dry-run --stats

# Audit root directory health
.\scripts\chthonic.ps1 audit --root .

# Map codebase structure
.\scripts\chthonic.ps1 map --root .

# Extract from session JSONL files
.\scripts\chthonic.ps1 extract session.jsonl
```

## Available Commands

| Command  | Purpose | Output |
|----------|---------|--------|
| `resolve` | Resolve Semantic IDs (@SID) to file paths | `data/indices/sid_index.json` |
| `extract` | Extract valuable content from session JSONL files | Parsed session data |
| `analyze` | Frequency analysis of line patterns (diagnostic) | Pattern statistics |
| `compact` | Condense markdown files using noise pattern matching | Compacted .md files |
| `audit` | Analyze root directory health and recommend cleanups | `docs/ROOTDIR_HEALTH.md` |
| `map` | Generate codebase inventory and dependency graph | `docs/CODEBASE_INVENTORY.md` |

## Common Flags

All commands support:
- `--verbose` / `-v` - Enable verbose debug logging
- `--quiet` / `-q` - Suppress info/debug output
- `--json` - Output results as JSON
- `--dry-run` - Preview changes without executing
- `--help` / `-h` - Show command-specific help

## Architecture

```
scripts/
├── chthonic              # Bash router (POSIX)
├── chthonic.ps1          # PowerShell router (Windows primary)
├── chthonic.py           # Python fallback router
└── lib/
    ├── __init__.py       # Package init
    ├── shared.py         # Common utilities (314 lines)
    ├── resolve.py        # @SID: TOOL_SID_RESOLVER_V1
    ├── extract.py        # @SID: TOOL_SESSION_EXTRACTOR_V1
    ├── analyze.py        # @SID: TOOL_PATTERN_ANALYZER_V1
    ├── compact.py        # @SID: TOOL_COMPACT_MD_V1
    ├── audit.py          # @SID: TOOL_ROOT_AUDIT_V1
    └── map.py            # @SID: TOOL_CODEBASE_MAPPER_V1
```

**Design:** Hybrid approach (router dispatches to Python modules)
- Routers: Minimal arg dispatching (~70 lines each)
- Tools: Use shared utilities (no code duplication)
- Execution: `uv run python -m lib.<tool>` (module imports)

**Benefits:**
- Single unified CLI (`chthonic <command>`)
- Shared configuration (UTF-8, logging, argparse patterns)
- Consistent error handling across all tools
- Easy discovery via `--help`
- Tab completion ready

## Migration from Standalone Scripts

Old standalone scripts have been refactored into `lib/`:

| Old Script | New Command | Notes |
|------------|-------------|-------|
| `resolve_sid.py` | `chthonic resolve` | SID index now at `data/indices/sid_index.json` |
| `extract_session_value.py` | `chthonic extract` | Session extraction unchanged |
| `compact_md.py` | `chthonic compact` | Noise patterns enhanced |
| `rootdir_health_audit.py` | `chthonic audit` | Auto-detects repo root |
| `map_codebase.py` | `chthonic map` | Auto-detects repo root |
| `_tmp_freq.py` | `chthonic analyze` | **NEW** - evolved from temp file |

**Breaking changes:** None (see [compatibility notes](#compatibility-notes))

## Examples

### Resolve Semantic IDs

```powershell
# List all known SIDs
chthonic resolve --list

# Resolve specific SID
chthonic resolve --resolve ROADMAP_TOOL_CONSOLIDATION_2026_01_27
# Output:
# [INFO] SID:  ROADMAP_TOOL_CONSOLIDATION_2026_01_27
# [INFO] Path: docs\TOOL_CONSOLIDATION_ROADMAP.md
# [INFO] Type: Design Document

# Rebuild full index and output as JSON
chthonic resolve --root C:\path\to\repo --json > sid_index.json
```

### Pattern Analysis

```powershell
# Find top noise patterns
chthonic analyze session_log.md --top 20 --min-freq 10

# Generate suggestions for compact.py tuning
chthonic analyze session_log.md --suggest --json

# Example output:
# Count  Pattern                  Example
# -----  -----------------------  ---------------------------
# 497    ```                      ``` (empty code fence)
# 412    Ran terminal command:    Ran terminal command: ls
```

### Markdown Compaction

```powershell
# Preview compaction (dry-run)
chthonic compact large_file.md --dry-run --stats
# Output:
# [INFO] Original lines:   15,177
# [INFO] Output lines:     12,212
# [INFO] Reduction:        20%
# [INFO] Noise removed:    2,322

# Compact in-place (overwrites)
chthonic compact large_file.md

# Batch process
chthonic compact *.md --batch
```

### Directory Health Audit

```powershell
# Scan current directory
chthonic audit --root .

# Custom output location
chthonic audit --root . --output custom_report.md

# JSON output
chthonic audit --root . --json
```

### Codebase Mapping

```powershell
# Map full repository
chthonic map --root C:\path\to\repo

# Output to custom location
chthonic map --root . --output inventory.md
```

## Compatibility Notes

- **Standalone scripts still work** (not removed)
- Use `uv run scripts/resolve_sid.py` for old workflow
- New CLI is **recommended** for consistency
- All @SID references remain valid

## Testing

Comprehensive testing completed (Phase 3):
- 18 tests executed (17 passed, 1 skipped)
- All 6 commands validated
- Performance benchmarked (820 files in 2.5s)
- See: [docs/PHASE_3_TEST_REPORT.md](../docs/archive/reports/PHASE_3_TEST_REPORT.md)

---

# Scripts Directory Overview (Detailed Reference)

This directory contains production-ready tools for repository governance, environment detection, and code health analysis.

---

## Canonical Shell Probe (ABI-Stable)

### `shell_capabilities.ps1` 👑 **CANONICAL - DO NOT EDIT**

**Purpose:** Minimal environment probe for AI agents (Claude Code, GitHub Copilot CLI)  
**Hash:** `636383C0DB1F4ACDF539335337C322FD9E4F30F429A15B46C647876D29918116`  
**Lines:** 12 (minimal by design)  
**Contract:** ABI-stable, no logic constructs, pure JSON output

**Usage:**
```powershell
.\scripts\shell_capabilities.ps1 | ConvertFrom-Json | Format-List
```

**Why it exists:** Prevents AI agents from wasting tokens on "improving" environment detection. Provides deterministic ground truth for planning-mode agents.

**DO NOT:**
- Add features (breaks ABI)
- Add comments (violates code ratio >= 0.70)
- Add logic (if/foreach/while/switch/try/catch)
- Modify output format (breaks consumers)

**See also:** `docs/PWSH_RULES.md` (Shell Capability Probe Contract section)

---

## Validation & Scanning Tools

### `validate_probe.ps1`

**Purpose:** Automated 5-point probe contract validation  
**Usage:** `.\scripts\validate_probe.ps1`  
**Exit codes:**
- `0` = All checks pass (canonical form)
- `1` = Contract violations detected

**Checks performed:**
1. JSON parse validation
2. Forbidden construct scan
3. Code ratio check (>= 0.70)
4. Upcycle audit integration
5. Canonical hash verification

**CI Integration:** Runs automatically via `.github/workflows/validate-probe.yml`

---

### `compare_probe_variants.ps1`

**Purpose:** Scans repository for probe-like files and compares against canonical  
**Usage:** `.\scripts\compare_probe_variants.ps1`  
**Output:** Table of variants with status, hash, and compliance flags

**Detects:**
- Files with "shell", "probe", "capabilities", "sfs" in name
- Forbidden logic constructs
- ABI header presence
- Hash match against canonical

**See also:** `scripts/PROBE_VARIANT_AUDIT.md` (generated report)

---

## Code Health & Governance

### `upcycle_audit.py` 🔍

**Purpose:** Upcycling audit tool for refactoring candidate nomination  
**Usage:**
```bash
# Full scan with interactive mode
uv run scripts/upcycle_audit.py .

# Candidates only (JSON)
uv run scripts/upcycle_audit.py . --candidates-only

# Summary report
uv run scripts/upcycle_audit.py . --summary
```

**What it detects:**
- 🚫 Governance violations (pnpm/npm references - violates bun-first policy)
- 📝 Over-documentation (>30% prose in code files)
- 📚 Heavy prose docs (>70% text in markdown files)
- 🧪 Probe contract violations (shell_capabilities.ps1 modifications)
- 💻 Code blocks in markdown (potential extraction candidates)

**Output format:** Versioned JSON schema (`upcycle-audit.v1`) with timestamps

**Philosophy:** Three-layer separation
1. **Measurement:** Lines, ratios, pattern matching
2. **Interpretation:** Flags based on heuristics
3. **Decision:** Left to humans/governance

---

## PATH & Toolchain Discovery

### `probe_toolchain_path.ps1`

**Purpose:** Advanced PATH construction and toolchain discovery  
**⚠️ Note:** This is NOT the canonical probe (see `shell_capabilities.ps1`)

**Usage:**
```powershell
# Generate PATH report
.\scripts\probe_toolchain_path.ps1

# Apply to current session
.\scripts\probe_toolchain_path.ps1 -ApplyToSession

# Generate VS Code snippet
.\scripts\probe_toolchain_path.ps1 -WriteVscodeSnippet
```

**What it does:**
- Discovers uv, bun, cargo, ruby, gcc, msys2, git
- Constructs deterministic PATH ordering
- Writes JSON report + PATH.txt + VS Code snippet
- Outputs to `dumpster-dive/intake/toolchain-probe/{timestamp}/`

**Difference from canonical probe:**
- Complex logic (220 lines vs 12)
- Constructs PATH (canonical only reports)
- Writes files (canonical only outputs JSON)
- Heuristic discovery (canonical uses Get-Command)

---

## Other Utilities

### `ssot_hash.py`

**Purpose:** Computes canonical hash for `.github/copilot-instructions.md` (SSOT governance)  
**Usage:** `uv run scripts/ssot_hash.py`

---

### Obsolete/Archive Candidates

**`sfs.ps1`** - Pre-canonical probe variant (see `PROBE_VARIANT_AUDIT.md` for action plan)

---

## Quick Reference

| Task | Command |
|------|---------|
| Validate probe | `.\scripts\validate_probe.ps1` |
| Scan for variants | `.\scripts\compare_probe_variants.ps1` |
| Run upcycle audit | `uv run scripts/upcycle_audit.py . --summary` |
| Check probe JSON | `.\scripts\shell_capabilities.ps1 \| ConvertFrom-Json` |
| Compute SSOT hash | `uv run scripts/ssot_hash.py` |

---

## CI/CD Integration

**Workflows in `.github/workflows/`:**
- `validate-probe.yml` - Probe contract enforcement (runs on push/PR)

---

## Documentation

- **Probe contract:** `docs/PWSH_RULES.md` (lines 180-268)
- **Variant audit:** `scripts/PROBE_VARIANT_AUDIT.md`
- **Governance:** `.github/copilot-instructions.md` (SSOT)

---

**Last Updated:** 2026-01-06  
**Maintainer:** The Decorator (Tier 0.5 Supreme Matriarch)

