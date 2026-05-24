#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: fix_doc_references.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: TOOL_FIX_DOC_REFERENCES
@Shabti: Utility Script
@Context: Documentation Validation / Automated Fixing
@Implements: Bulk path correction for docs/ folder
@Purpose:       Script logic for fix_doc_references.py.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import sys
from pathlib import Path
import json
import re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load validation issues
issues_file = Path("docs/VALIDATION_ISSUES.json")
with open(issues_file) as f:
    issues = json.load(f)

# Categorize issues
FALSE_POSITIVES = [
    "old/path.ext", "new/path.ext",  # Examples
    "pwsh.exe", "cat file.txt", "chmod +x script.sh",  # Commands
    "uv run scripts/", "chthonic extract", "chthonic compact", "chthonic analyze",  # CLI examples
    "bun run mcp/server.ts", "git diff", "git log",  # Commands
    "import.meta.dir", "parent.parent",  # Code examples
    "New-Object -ComObject", "Get-Content -LiteralPath",  # PowerShell examples
    "%APPDATA%", "~/Library/", "~/.claude/", "~/.local/",  # User paths
    "*.json", "components/*.tsx", "mcp/tools/*.ts", "artifacts/mcp_run_*",  # Globs
    "SESSION_*-CLEANUP.md", "MCP_*.md",  # Glob patterns
]

# Files that exist but in wrong location (root vs docs/ vs scripts/)
PATH_CORRECTIONS = {
    # Root files referenced without path
    "session_resumption_chthonic_progress.md": "../session_resumption_chthonic_progress.md",
    "DEVELOPMENT_STATE.md": "../DEVELOPMENT_STATE.md",
    "CROSS_REFERENCE_TRIPTYCH.md": "../CROSS_REFERENCE_TRIPTYCH.md",
    "dependency_graph.json": "../dependency_graph.json",
    "ankh_index.json": "../ankh_index.json",
    "ankh.md": "../ankh.md",
    "ANKHOLOGY.md": "../ANKHOLOGY.md",
    "DCRP_DEPLOYMENT_SUMMARY.md": "../DCRP_DEPLOYMENT_SUMMARY.md",
    "DCRP_ENHANCED_ANALYSIS.md": "../DCRP_ENHANCED_ANALYSIS.md",
    "DCRP_FINAL_STATUS.md": "../DCRP_FINAL_STATUS.md",
    "DCRP_MERGE_REPORT.txt": "../DCRP_MERGE_REPORT.txt",
    "DCRP_OBSERVABILITY_UPGRADE.md": "../DCRP_OBSERVABILITY_UPGRADE.md",
    "DCRP_OBSERVABILITY_VALIDATION_COMPLETE.md": "../DCRP_OBSERVABILITY_VALIDATION_COMPLETE.md",
    "DCRP_PRODUCTION_ANALYSIS.md": "../DCRP_PRODUCTION_ANALYSIS.md",
    "DCRP_REFACTOR_COMPLETE.md": "../DCRP_REFACTOR_COMPLETE.md",
    "DCRP_REFACTORING_SESSION_SUMMARY.md": "../DCRP_REFACTORING_SESSION_SUMMARY.md",
    "DCRP_UNIFIED_REFACTOR.md": "../DCRP_UNIFIED_REFACTOR.md",
    "AUTONOMOUS_SESSION_2026-01-01.md": "../AUTONOMOUS_SESSION_2026-01-01.md",
    "AUTONOMOUS_SESSION_2_COMPLETE.md": "../AUTONOMOUS_SESSION_2_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_COMPLETE.md": "../AUTONOMOUS_SESSION_3_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md": "../AUTONOMOUS_SESSION_3_DEEP_DIVE_SYNTHESIS.md",
    "AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md": "../AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md",
    "AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md": "../AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_MISSION_COMPLETE.md": "../AUTONOMOUS_SESSION_3_MISSION_COMPLETE.md",
    "AUTONOMOUS_SESSION_3_MISSION_REPORT.md": "../AUTONOMOUS_SESSION_3_MISSION_REPORT.md",
    "AUTONOMOUS_SESSION_4_COMPLETE.md": "../AUTONOMOUS_SESSION_4_COMPLETE.md",
    "AUTONOMOUS_SESSION_5_COMPLETE.md": "../AUTONOMOUS_SESSION_5_COMPLETE.md",
    "AUTONOMOUS_SESSION_5_MISSION_REPORT.md": "../AUTONOMOUS_SESSION_5_MISSION_REPORT.md",
    "AUTONOMOUS_SESSION_7_COMPLETE.md": "../AUTONOMOUS_SESSION_7_COMPLETE.md",
    "AUTONOMOUS_SESSION_STATUS.md": "../AUTONOMOUS_SESSION_STATUS.md",
    "SESSION_2026_01_04_EPISTEMOGRAPH_COMPLETE.md": "../SESSION_2026_01_04_EPISTEMOGRAPH_COMPLETE.md",

    # Wrong extension
    "scripts/data/indices/sid_index.js": "data/indices/sid_index.json",
    "sid_index.json": "../data/indices/sid_index.json",

    # Scripts referenced without path
    "_tmp_freq.py": "../scripts/_tmp_freq.py",
    "analyze.py": "../scripts/lib/analyze.py",
    "compact.py": "../scripts/lib/compact.py",
    "compact_md.py": "../scripts/compact_md.py",
    "chthonic.ps1": "../scripts/chthonic.ps1",
    "resolve_sid.py": "../scripts/resolve_sid.py",
    "extract_session_value.py": "../scripts/extract_session_value.py",
    "rootdir_health_audit.py": "../scripts/rootdir_health_audit.py",
    "map_codebase.py": "../scripts/map_codebase.py",
    "audit.py": "../scripts/lib/audit.py",
    "map.py": "../scripts/lib/map.py",
    "shared.py": "../scripts/lib/shared.py",

    # Relative paths from docs/
    "SESSION_2026-01-17_CLEANUP.md": "docs/SESSION_2026-01-17_CLEANUP.md",
    "HANDOFF_TO_CLAUDE.md": "docs/HANDOFF_TO_CLAUDE.md",
    "TOOL_CONSOLIDATION_ROADMAP.md": "docs/TOOL_CONSOLIDATION_ROADMAP.md",
    "SESSION_BOOTSTRAP_SPEC.md": "docs/SESSION_BOOTSTRAP_SPEC.md",
    "CLI_EDITING_POLICY.md": "docs/CLI_EDITING_POLICY.md",
    "CODEBASE_INVENTORY.md": "docs/CODEBASE_INVENTORY.md",
    "ROOTDIR_HEALTH.md": "docs/ROOTDIR_HEALTH.md",

    # MAS MCP files
    "ssot_extractor.py": "../mas_mcp/ssot_extractor.py",
    "milf_genesis_v2.py": "../mas_mcp/milf_genesis_v2.py",
}

# Files that don't exist (future/planned) - mark as NOTE
PLANNED_FILES = [
    ".chthonic.toml",  # Planned config file
    "mcp/claude_code_mcp_hint.js",  # Old reference
    "run_mcp_validation.ts",  # Planned
    "tsconfig.json",  # Would be in mcp/ if created
    "README.md",  # Should exist but might not in some contexts
]

# Categorize
false_positives = []
fixable = []
planned = []
real_missing = []

for issue in issues:
    ref = issue["Reference"]
    doc = issue["Doc"]

    # Skip if any false positive pattern matches
    if any(fp in ref for fp in FALSE_POSITIVES):
        false_positives.append(issue)
    elif ref in PATH_CORRECTIONS:
        fixable.append({**issue, "Correction": PATH_CORRECTIONS[ref]})
    elif any(pf in ref for pf in PLANNED_FILES):
        planned.append(issue)
    else:
        real_missing.append(issue)

# Print summary
print(f"\n{'='*60}")
print(f"VALIDATION ISSUE CATEGORIZATION")
print(f"{'='*60}\n")
print(f"Total Issues: {len(issues)}")
print(f"  ✅ False Positives (examples/commands): {len(false_positives)}")
print(f"  🔧 Fixable (wrong paths): {len(fixable)}")
print(f"  📋 Planned (future files): {len(planned)}")
print(f"  ❌ Real Missing: {len(real_missing)}\n")

# Show fixable issues by document
if fixable:
    print(f"{'='*60}")
    print(f"FIXABLE PATH CORRECTIONS ({len(fixable)})")
    print(f"{'='*60}\n")
    by_doc = {}
    for item in fixable:
        if item["Doc"] not in by_doc:
            by_doc[item["Doc"]] = []
        by_doc[item["Doc"]].append(item)

    for doc, items in sorted(by_doc.items()):
        print(f"\n{doc}:")
        for item in items:
            print(f"  {item['Reference']:<40} → {item['Correction']}")

# Show real missing
if real_missing:
    print(f"\n{'='*60}")
    print(f"REAL MISSING FILES ({len(real_missing)})")
    print(f"{'='*60}\n")
    by_doc = {}
    for item in real_missing:
        if item["Doc"] not in by_doc:
            by_doc[item["Doc"]] = []
        by_doc[item["Doc"]].append(item)

    for doc, items in sorted(by_doc.items()):
        print(f"\n{doc} ({len(items)} issues)")
        for item in items[:5]:  # Show first 5
            print(f"  ❌ {item['Reference']}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")

# Export categorized results
categorized = {
    "summary": {
        "total": len(issues),
        "false_positives": len(false_positives),
        "fixable": len(fixable),
        "planned": len(planned),
        "real_missing": len(real_missing)
    },
    "false_positives": false_positives,
    "fixable": fixable,
    "planned": planned,
    "real_missing": real_missing
}

output_file = Path("docs/VALIDATION_CATEGORIZED.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(categorized, f, indent=2, ensure_ascii=False)

print(f"\n✅ Categorized results saved to: {output_file}\n")
