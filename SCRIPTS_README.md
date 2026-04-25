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
- `claudine.ps1`: Legacy compatibility wrapper that delegates to `chthonic.ps1`
- `lib/*.py`: Core CLI tools (audit, compact, extract, resolve, map, analyze)
- `*.ps1`: PowerShell probes (Shell Capabilities, Environment)
- `*.ts`: TypeScript/MCP tools

## Ownership
- **Steward:** `TOOL_CODEBASE_MAPPER_V1`
- **Maintainer:** Core Engine Team

---

# Chthonic CLI

**@SID:** TOOL_CHTHONIC_ROUTER_PYTHON (and variants)  
**Version:** 3.3.0 (PowerShell router)  
**Documentation:** Multi-domain meta CLI with archive tool dispatch

## Quick Start

```powershell
# Show available commands
chthonic --help

# Show router version
chthonic --version

# Activate polyglot environment
chthonic env

# Compatibility alias (same as env)
chthonic claudine

# Legacy wrapper script (delegates to chthonic)
pwsh -File scripts/claudine.ps1
pwsh -File scripts/claudine.ps1 status --json
pwsh -File scripts/claudine.ps1 build-check        # pre-build sanity: linker shadow + OpenSSL + MSVC effective state
pwsh -File scripts/claudine.ps1 repair --fix       # delegates to chthonic doctor --fix (persists env vars)

# Tool inventory (JSON)
chthonic status --json

# Ruby lane summary
chthonic ruby lane

# Ruby versions / tools
chthonic ruby versions
chthonic ruby tools

# Repair stale rv state / upgrade latest stable Ruby
chthonic ruby doctor
chthonic ruby doctor --fix
chthonic ruby upgrade

# Search/install Ruby tools from RubyGems
chthonic ruby search solargraph
chthonic ruby install solargraph@0.58.3

# EOL/version audit without applying fixes
chthonic doctor --dry-run

# Tool origin audit (path + install methodology)
chthonic doctor --origins

# IDE/runtime context detection
chthonic detect --json

# Service domain
chthonic mcp status --json

# Archive command passthrough
chthonic analyze file.md --top 10
chthonic map --root .
```

## VS Code Insiders PowerShell Registration

To auto-register the full polyglot + VS 2026 + Azure CLI toolchain in every integrated terminal, append this to your PowerShell profile:

```powershell
$repoRoot = Join-Path $env:USERPROFILE "chthonic-archive"
$chthonic = Join-Path $repoRoot "scripts\chthonic.ps1"
if (Test-Path $chthonic) {
  & $chthonic env --quiet | Out-Null
}
```

Open with:

```powershell
notepad $PROFILE
```

### PowerShell `rv` Collision Guard

PowerShell reserves `rv` as an alias for `Remove-Variable`.

When you run `chthonic env` (or `chthonic claudine`), the router applies a safe session-local guard:
- If `rv` is still `Remove-Variable` and `rvw` exists, it remaps `rv -> rvw`.
- It preserves quick access to `Remove-Variable` via `rvar`.
- It does **not** override `rv` if you already mapped it to a non-default command.

You can inspect active bindings with:

```powershell
chthonic status --json
```

## Available Commands

| Domain / Command | Purpose | Output / Behavior |
|----------|---------|--------|
| `env` | Activate polyglot PATH + toolchain env | Process environment mutation |
| `claudine` | Compatibility alias to `env` | Process environment mutation |
| `status` | Show detected tool, manager, and handler-lane versions | Text table or JSON |
| `doctor` | Compare installed vs latest/EOL and optionally remediate; mitigation chain awareness — `effective` + `mitigations[]` arrays per issue (linker shadow, OpenSSL); `--fix` persists env vars | Text report or `--json`, optional fixes (`--fix`) |
| `detect` | Detect IDE/runtime context | Text report or JSON |
| `ruby versions|tools|lane|doctor|search|install|upgrade` | Ruby lane via `rv` + RubyGems | Listing, summary, repair, search, install, stable upgrade |
| `ide launch|detect|reset` | VS Code management helpers | Launch/diagnostics/reset |
| `mcp start|stop|status|logs` | Bridge service lifecycle | Service control/status |
| `config init|show|set` | Manage `~/.chthonic/config.json` | Config bootstrap/display |
| `book [build\|serve\|clean]` | mdBook command wrapper | mdBook output |
| `audit|compact|extract|resolve|map|analyze` | Archive tool suite (`uv run python -m lib.<tool>`) | Tool-specific artifacts |
| `gemini` | Wrapper passthrough (`gemini-cli-wrapper.ps1`) | External CLI execution |

## Common Flags

Shared flags:
- `--help` / `-h` - Show usage/help
- `--version` - Show router version
- `--quiet` / `-q` - Suppress activation chatter (`env`)
- `--json` - JSON mode for commands that support structured output (`status`, `detect`, `mcp status`, etc.)
- `--dry-run` - Preview actions without execution (`doctor`)
- `--fix` - Apply recommended upgrades/installs (`doctor`)
- `--origins` - Show install origins (`doctor`)

## Architecture

```
scripts/
├── chthonic              # Bash router (POSIX)
├── chthonic.ps1          # PowerShell router (Windows primary)
├── chthonic.py           # Python fallback router
├── claudine.ps1          # Legacy wrapper -> chthonic.ps1
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

**Design:** PowerShell-first orchestration + Python module dispatch
- `chthonic.ps1` handles domain/action routing, environment activation, doctor/origins logic, IDE and MCP controls
- `claudine.ps1` preserves legacy entrypoints and forwards to `chthonic.ps1`
- Archive tools are forwarded to Python modules
- Execution path for archive tools remains `uv run python -m lib.<tool>`

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

### Markdown Link Audit

```powershell
# Validate links in a markdown file (dry-run)
uv run scripts/link_audit.py check <file> --dry-run

# Auto-fix broken/disambiguatable links
uv run scripts/link_audit.py check <file> --fix

# Upgrade inert backtick file refs to markdown links
uv run scripts/link_audit.py backticks <file> --fix

# List all basename collisions in the repo
uv run scripts/link_audit.py collisions --filter .md

# Audit markdown links against staged git renames
uv run scripts/link_audit.py renames --staged --dry-run
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

Manual command validation (2026-04-21):
- `chthonic --version` returns `v3.3.0`
- `chthonic --help` shows current domain/action surface
- `chthonic status --json` returns JSON
- `chthonic detect --json` returns JSON
- `chthonic mcp status --json` returns JSON
- `chthonic doctor --origins` reports path + install methodology

---

# Scripts Directory Overview (Detailed Reference)

This directory contains production-ready tools for repository governance, environment detection, and code health analysis.

---

## Canonical Shell Probe (ABI-Stable)

### `shell_capabilities.ps1` 👑 **CANONICAL - DO NOT EDIT**

**Purpose:** Minimal environment probe for AI agents (Claude Code, GitHub Copilot CLI)  
**Hash:** `934B9E30F4C30F65E4229055E2CCE41B99E99E792450D8A6B63EFC5F880B5E82`  
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

**See also:** [PWSH_RULES.md (repo-root)](PWSH_RULES.md) (Shell Capability Probe Contract section)

---

## Archive Maintenance Tools (V2)

### `scripts/pentea_family_relations.py`

**@SID:** `TOOL_PENTEA_FAMILY_V2`  
**Purpose:** Full-archive `.md` × `*META*.md` relational mapper with git authorship classification.

Maps every `.md` file in the archive to META families, extracts `:pentarch` fields, and reports coverage gaps. V2 adds origin classification: each `.md` is tagged `authored` (git-tracked) or `framework` (present on disk but not committed — vendored, auto-generated, or framework scaffolding).

**Usage:**
```powershell
# Default: rich tree report
uv run scripts/pentea_family_relations.py

# Authored files only (exclude framework/vendor .md)
uv run scripts/pentea_family_relations.py --authored-only

# JSON output (CI/scripting)
uv run scripts/pentea_family_relations.py --json

# Write report to file
uv run scripts/pentea_family_relations.py --report docs/family-report.md

# Force cache refresh
uv run scripts/pentea_family_relations.py --no-cache

# Strict mode: exit 1 if unclaimed or :pentarch gaps
uv run scripts/pentea_family_relations.py --strict

# Scope to a sub-tree
uv run scripts/pentea_family_relations.py --domain "codex/**"

# Scope to a single META file
uv run scripts/pentea_family_relations.py --meta codex/MILF-Core-META.md
```

**Origin classification:**
- `authored` — file appears in `git ls-files` (you or an agent committed it)
- `framework` — on disk but not in git index (auto-generated / vendored)
- `unknown` — git oracle unavailable (non-git environment)

**Flags:**

| Flag | Effect |
|------|--------|
| `--authored-only` | Drop framework/untracked `.md` files before building the graph |
| `--json` | Emit JSON (includes `origin_summary` + per-file `origin` in `unclaimed_mds`) |
| `--report FILE` | Write output to FILE instead of stdout |
| `--no-cache` | Force full filesystem walk, refresh `.git/pentea_family_cache.json` |
| `--strict` | Exit 1 if any unclaimed `.md` or `:pentarch` gaps exist |
| `--domain GLOB` | Filter `.md` paths to GLOB pattern |
| `--meta FILE` | Scope to a single META file |

**Cache:** `.git/pentea_family_cache.json` (Cache V2 — dir-mtime + file-mtime coherence, gitignored by location)

---

## Local CI Checks (`ci/checks/`)

### `ci/checks/uv-guard.ts`

**@SID:** `CI_CHECK_UV_GUARD_V1`  
**Purpose:** Block bare `python`/`python3` invocations — enforce the repo-wide `uv run` mandate.

Scans `.py`, `.sh`, `.ps1`, `.ts` files for raw Python calls not prefixed with `uv run`. Registered in `ci/run.ts` as a `staged/fast` check — runs in pre-commit mode automatically.

**Enforcement levels:**
- **Added files (strict):** exit 1 — blocks the commit
- **Modified files (advisory):** warns but does not block
- **Default scan (advisory):** `bun run ci/checks/uv-guard.ts` — advisory over all tracked files (exit 0)

**Detected patterns:**
```shell
python script.py          # bare shell
python3 -m module         # bare module
& python script.py        # PowerShell ampersand call
spawnSync("python3", …)   # Node/Bun spawn
subprocess.run(["python", …])  # Python subprocess
```

**Allowed patterns:**
```shell
uv run script.py          # correct
uv run python3 -c "…"     # correct
#!/usr/bin/env python3    # shebang (allowed)
# python3 foo             # comment (skipped)
```

**Run manually:**
```powershell
# Advisory scan (all tracked files)
bun run ci/checks/uv-guard.ts

# Staged mode (what pre-commit runs)
bun run ci/checks/uv-guard.ts --staged

# Via CI runner
bun run ci/run.ts --check uv-guard
```

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

**See also:** [PROBE_VARIANT_AUDIT.md](scripts/PROBE_VARIANT_AUDIT.md) (generated report)

---

## Code Health & Governance

### `upcycle_audit.py` 🔍

**Purpose:** Upcycling audit tool for refactoring candidate nomination  
**Usage:**
```bash
# Full scan with interactive mode
uv run python scripts/upcycle_audit.py .

# Candidates only (JSON)
uv run python scripts/upcycle_audit.py . --candidates-only

# Summary report
uv run python scripts/upcycle_audit.py . --summary
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
**Usage:** `uv run python scripts/ssot_hash.py`

---

### Obsolete/Archive Candidates

**`sfs.ps1`** - Pre-canonical probe variant (see `PROBE_VARIANT_AUDIT.md` for action plan)

---

## Quick Reference

| Task | Command |
|------|---------|
| Validate probe | `.\scripts\validate_probe.ps1` |
| Scan for variants | `.\scripts\compare_probe_variants.ps1` |
| Run upcycle audit | `uv run python scripts/upcycle_audit.py . --summary` |
| Check probe JSON | `.\scripts\shell_capabilities.ps1 \| ConvertFrom-Json` |
| Compute SSOT hash | `uv run python scripts/ssot_hash.py` |

---

## CI/CD Integration

**Workflows in `.github/workflows/`:**
- `validate-probe.yml` - Probe contract enforcement (runs on push/PR)

---

## Documentation

- **Probe contract:** [PWSH_RULES.md (repo-root)](PWSH_RULES.md) (lines 180-268)
- **Variant audit:** [PROBE_VARIANT_AUDIT.md](scripts/PROBE_VARIANT_AUDIT.md)
- **Governance:** [.github/copilot-instructions.md](.github/copilot-instructions.md) (SSOT)

---

**Last Updated:** 2026-01-06  
**Maintainer:** The Decorator (Tier 0.5 Supreme Matriarch)
