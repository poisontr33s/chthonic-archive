#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scan_delete_language.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Scan all agent-readable files for deletion/removal language that agents
might interpret as standing authorization to delete, move, or remove files.

@SID:           TOOL_SCAN_DELETE_LANGUAGE_V1
@Shabti:          Guardian
@Purpose:       Scan all agent-readable files for deletion/removal language that agents

Usage:
    uv run scripts/scan_delete_language.py
    uv run scripts/scan_delete_language.py --verbose
    uv run scripts/scan_delete_language.py --fix-candidates
"""

import argparse
import io
import re
import sys
from pathlib import Path

# UTF-8 output ritual (Windows cp1252 workaround)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.ssot_paths import SSOT_POINTER

# Files agents auto-load or regularly read
AGENT_READABLE_GLOBS = [
    SSOT_POINTER,
    ".github/pathstofiles.md",
    ".github/instructions/*.instructions.md",
    ".github/instructions/*.reference.md",
    ".codex/instructions.md",
    ".codex/config.toml",
    ".claude/instructions.md",
    "AGENTS.md",
    "AGENT_COMMON.md",
    "CLAUDE.md",
    "GEMINI.md",
    "WET_PAPER_TO_GOLD_METHODOLOGY.md",
    "STRATEGIC_PLAN.md",
    "PWSH_RULES.md",
    "codex/NEXT.md",
    "codex/mailbox/**/*.md",
    ".claude/skills/*/SKILL.md",
    ".codex/skills/*/SKILL.md",
    # Global agent configs
]

# "Codebase" scope: all OUR code, not vendored/built dependencies
# These are directories where agents read/write and we own the content
CODEBASE_DIRS = [
    ".github", ".codex", ".claude", ".temple",
    "scripts", "codex", "claude", "claude-codex-gemini",
    "docs", "dumpster-dive", "artifacts",
    "src", "game", "dev", "extensions",
    "chthonic-vscode-extension", "bun-playwright-poc",
    "mas_mcp/scripts", "mas_mcp/server.py",
    "mas_mcp/frontend",
]
CODEBASE_ROOT_GLOBS = [
    "*.md", "*.toml", "*.py", "*.ps1", "*.ts", "*.json", "*.yml", "*.yaml",
]
CODEBASE_EXTENSIONS = {
    ".md", ".toml", ".json", ".yml", ".yaml",
    ".py", ".ps1", ".ts", ".tsx", ".js", ".jsx",
    ".sh", ".txt", ".rs", ".cfg",
}

GLOBAL_PATHS = [
    Path.home() / ".codex" / "instructions.md",
    Path.home() / ".codex" / "config.toml",
]

# Patterns that agents interpret as deletion authorization
# Each tuple: (pattern_regex, severity, description)
PATTERNS = [
    # Direct commands
    (r'\bgit\s+rm\b', 'CRITICAL', 'git rm command'),
    (r'\bRemove-Item\b', 'CRITICAL', 'PowerShell Remove-Item'),
    (r'\bMove-Item\b', 'HIGH', 'PowerShell Move-Item (relocation)'),
    (r'\brm\s+-[rf]', 'CRITICAL', 'Unix rm with force/recursive'),
    (r'\bdel\s+', 'HIGH', 'DOS del command'),
    (r'\brmdir\b', 'CRITICAL', 'rmdir command'),
    (r'\bRemove-ItemProperty\b', 'MEDIUM', 'PowerShell Remove-ItemProperty'),
    (r'\bunlink\b', 'HIGH', 'unlink command'),
    (r'\bshutil\.rmtree\b', 'CRITICAL', 'Python shutil.rmtree'),
    (r'\bos\.remove\b', 'CRITICAL', 'Python os.remove'),
    (r'\bos\.unlink\b', 'CRITICAL', 'Python os.unlink'),
    (r'\bfs\.unlinkSync\b', 'CRITICAL', 'Node fs.unlinkSync'),
    (r'\bfs\.rmSync\b', 'CRITICAL', 'Node fs.rmSync'),

    # Imperative deletion language (agents read these as instructions)
    (r'(?i)\bdelete\s+(it|them|this|these|the|all|directly|immediately)', 'HIGH', 'imperative delete'),
    (r'(?i)\bremove\s+(it|them|this|these|the|all|directly|immediately)', 'HIGH', 'imperative remove'),
    (r'(?i)\bpurge\b', 'MEDIUM', 'purge language'),
    (r'(?i)\bwipe\b', 'MEDIUM', 'wipe language'),
    (r'(?i)\beradicate\b', 'MEDIUM', 'eradicate language'),
    (r'(?i)\beliminate\b', 'LOW', 'eliminate language'),
    (r'(?i)\bnuke\b', 'MEDIUM', 'nuke language'),
    (r'(?i)\bdestroy\b', 'MEDIUM', 'destroy language'),
    (r'(?i)\bobliterate\b', 'LOW', 'obliterate language'),

    # Structured deletion plans (tables/lists that agents execute)
    (r'(?i)\bimmediate\s+removals?\b', 'HIGH', 'structured removal plan'),
    (r'(?i)\bdelete\s+directly\b', 'CRITICAL', 'direct deletion instruction'),
    (r'(?i)\bno\s+archive\s+needed\b', 'HIGH', 'bypass archive instruction'),
    (r'(?i)\bnoise\s+floor\s+clear', 'MEDIUM', 'noise floor clearing'),
    (r'(?i)\bestimated\s+removal\b', 'HIGH', 'removal estimate (execution plan)'),
    (r'(?i)\brelocate\s+to\b', 'MEDIUM', 'relocation instruction'),

    # Archive-as-euphemism patterns
    (r'(?i)\barchive\s+the\s+rest\b', 'MEDIUM', 'archive-as-deletion euphemism'),
    (r'(?i)\bclean\s*up\b', 'LOW', 'cleanup language (context-dependent)'),
    (r'(?i)\bnoise\b.*\bvalue\b', 'LOW', 'noise-vs-value judgment'),
]

# Lines containing these are EXEMPT (they're prohibitions, not authorizations)
EXEMPTION_PATTERNS = [
    r'(?i)\bdo\s+not\b',
    r'(?i)\bdon.t\b',
    r'(?i)\bmust\s+not\b',
    r'(?i)\bcannot\b',
    r'(?i)\bcan.t\b',
    r'(?i)\bforbidden\b',
    r'(?i)\bprohibit',
    r'(?i)\bnever\b',
    r'(?i)\bdenied\b',
    r'(?i)\bblocked\b',
    r'(?i)\bwhat agents cannot\b',
    r'(?i)\bdo not\b',
    r'(?i)\bVOIDED\b',
    r'(?i)\bSUPERSEDED\b',
    r'(?i)\bNo[- ]Destroy\b',
    r'(?i)\bno agent\b.*\bmay\b',
    r'(?i)\bMUST NOT\b',
]



def is_exempted(line: str, context_lines: list[str] | None = None) -> bool:
    """Check if the line is a prohibition (safe) rather than an instruction.
    
    Also checks surrounding context (5 lines above) for prohibition headers
    like '### What Agents CANNOT Do' that cover subordinate bullet points.
    """
    all_text = [line]
    if context_lines:
        all_text.extend(context_lines)
    return any(
        re.search(p, text) for p in EXEMPTION_PATTERNS for text in all_text
    )


def scan_file(filepath: Path, verbose: bool = False) -> list[dict]:
    """Scan a single file for deletion language."""
    # Skip ourselves — pattern definitions aren't instructions
    if filepath.name == "scan_delete_language.py":
        return []
    hits = []
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return hits

    lines = text.splitlines()
    for line_num, line in enumerate(lines, 1):
        for pattern, severity, description in PATTERNS:
            if re.search(pattern, line):
                # Check 5 lines above for prohibition context
                start = max(0, line_num - 6)
                context = lines[start:line_num - 1]
                exempted = is_exempted(line, context)
                hits.append({
                    "file": str(filepath),
                    "line": line_num,
                    "severity": severity,
                    "description": description,
                    "text": line.strip()[:120],
                    "exempted": exempted,
                })
    return hits


def resolve_globs() -> list[Path]:
    """Resolve all agent-readable file globs to actual paths."""
    paths = []
    for glob_pattern in AGENT_READABLE_GLOBS:
        found = list(REPO_ROOT.glob(glob_pattern))
        paths.extend(found)
    for p in GLOBAL_PATHS:
        if p.exists():
            paths.append(p)
    return sorted(set(paths))


def resolve_codebase() -> list[Path]:
    """Resolve all OUR code (not vendored/built) to scan.
    
    Covers: owned directories + root-level files.
    Excludes: mas_mcp/.venv, node_modules, target, build, __pycache__, .git
    """
    skip = {"node_modules", "target", ".venv", "__pycache__", ".git", ".next", "build"}
    paths = []
    
    # Root-level files matching our extensions
    for glob_pat in CODEBASE_ROOT_GLOBS:
        paths.extend(REPO_ROOT.glob(glob_pat))
    
    # Owned directories — recurse into them
    for dir_entry in CODEBASE_DIRS:
        dir_path = REPO_ROOT / dir_entry
        if dir_path.is_file():
            if dir_path.suffix in CODEBASE_EXTENSIONS:
                paths.append(dir_path)
        elif dir_path.is_dir():
            for f in dir_path.rglob("*"):
                if f.is_file() and f.suffix in CODEBASE_EXTENSIONS:
                    if not any(s in f.parts for s in skip):
                        paths.append(f)
    
    # Global agent configs
    for p in GLOBAL_PATHS:
        if p.exists():
            paths.append(p)
    
    return sorted(set(paths))


def main():
    parser = argparse.ArgumentParser(
        description="Scan agent-readable files for deletion/removal language"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show exempted (safe) hits too")
    parser.add_argument("--fix-candidates", action="store_true",
                        help="Show only non-exempted hits (things to fix)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON (for programmatic use)")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--codebase", action="store_true",
                       help="Scan all OUR code (scripts, codex, claude, .github, etc.) — excludes vendored deps")
    scope.add_argument("--all-files", action="store_true",
                       help="Scan EVERYTHING in repo (includes vendored, very slow)")
    args = parser.parse_args()

    if args.all_files:
        ALL_EXTENSIONS = [
            "*.md", "*.toml", "*.json", "*.yml", "*.yaml",
            "*.py", "*.ps1", "*.ts", "*.sh", "*.txt",
        ]
        skip = {"node_modules", "target", ".venv", "__pycache__", ".git", ".next", "bun.lock"}
        collected = []
        for ext in ALL_EXTENSIONS:
            collected.extend(REPO_ROOT.rglob(ext))
        files = sorted(set(
            f for f in collected
            if not any(s in f.parts for s in skip)
        ))
        scope_label = "ALL FILES"
    elif args.codebase:
        files = resolve_codebase()
        scope_label = "CODEBASE (owned code)"
    else:
        files = resolve_globs()
        scope_label = "Agent-Readable Files"

    all_hits = []
    for filepath in files:
        hits = scan_file(filepath)
        all_hits.extend(hits)

    # Separate actionable vs exempted
    actionable = [h for h in all_hits if not h["exempted"]]
    exempted = [h for h in all_hits if h["exempted"]]

    # Normalize file paths to relative POSIX-style for JSON output
    for h in all_hits:
        try:
            h["file"] = str(Path(h["file"]).relative_to(REPO_ROOT)).replace("\\", "/")
        except ValueError:
            pass

    # JSON output mode
    if args.json:
        import json
        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for h in actionable:
            sev_counts[h["severity"]] += 1
        result = {
            "scope": scope_label,
            "files_scanned": len(files),
            "total_hits": len(all_hits),
            "actionable": len(actionable),
            "exempted": len(exempted),
            "severity": sev_counts,
            "hits": [h for h in (all_hits if args.verbose else actionable)],
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1 if sev_counts["CRITICAL"] > 0 else 0)

    # Severity counts
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for h in actionable:
        sev_counts[h["severity"]] += 1

    # Header
    print("=" * 72)
    print(f"  DELETION LANGUAGE SCANNER — {scope_label}")
    print(f"  Files scanned: {len(files)}")
    print(f"  Total hits: {len(all_hits)} ({len(actionable)} actionable, {len(exempted)} exempted)")
    print("=" * 72)
    print()

    # Severity summary
    print("  Severity Breakdown (actionable only):")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}[sev]
        print(f"    {icon} {sev}: {sev_counts[sev]}")
    print()

    if args.fix_candidates or not args.verbose:
        display = actionable
        label = "ACTIONABLE"
    else:
        display = all_hits
        label = "ALL"

    if not display:
        print("  ✅ No actionable deletion language found. The methodology is clean.")
        print()
        sys.exit(0)

    # Group by file
    by_file: dict[str, list[dict]] = {}
    for h in display:
        by_file.setdefault(h["file"], []).append(h)

    for filepath, hits in sorted(by_file.items()):
        rel = filepath
        try:
            rel = str(Path(filepath).relative_to(REPO_ROOT))
        except ValueError:
            pass
        print(f"  📄 {rel}")
        for h in sorted(hits, key=lambda x: x["line"]):
            sev = h["severity"]
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}[sev]
            exempt_tag = " [EXEMPT: prohibition]" if h["exempted"] else ""
            print(f"     L{h['line']:>4} {icon} {sev:<8} {h['description']}{exempt_tag}")
            print(f"           {h['text']}")
        print()

    # Final verdict
    if sev_counts["CRITICAL"] > 0:
        print("  ❌ CRITICAL hits found — agents may interpret these as deletion orders.")
    elif sev_counts["HIGH"] > 0:
        print("  ⚠️  HIGH-severity hits — review for implicit authorization language.")
    elif actionable:
        print("  ℹ️  Low/medium hits only — likely safe but worth reviewing context.")
    else:
        print("  ✅ Clean — all deletion language is properly wrapped in prohibitions.")

    print()
    sys.exit(1 if sev_counts["CRITICAL"] > 0 else 0)


if __name__ == "__main__":
    main()
