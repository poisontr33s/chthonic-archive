#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: gold_signal.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Gold Signal Scanner — Wet-Paper-to-Gold file-type affordance classifier.

Walks the repository and classifies every tracked file by its gold grade
(Operational / Structural / Conceptual / Sentinel) and detects ambulant
signals: files in motion (recently modified, untracked, conflict markers).

Outputs structured JSON for consumption by other tools, or a human-readable
summary to stdout.

Usage:
    uv run scripts/gold_signal.py                # human summary
    uv run scripts/gold_signal.py --json         # structured JSON
    uv run scripts/gold_signal.py --ambulant     # only files in motion

@SID:           TOOL_GOLD_SIGNAL_V1
@Shabti:          Utility
@Purpose:       Gold Signal Scanner — Wet-Paper-to-Gold file-type affordance classifier.
"""

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root


# ── Gold Grade Taxonomy ──────────────────────────────────────────────────────

OPERATIONAL_GOLD = {
    ".py", ".ps1", ".ts", ".tsx", ".rs", ".js", ".jsx", ".bat", ".sh",
    ".css", ".html", ".env",
}

STRUCTURAL_GOLD = {
    ".json", ".jsonl", ".yml", ".yaml", ".toml", ".lock", ".csv",
    ".log", ".bak", ".pyc", ".tsbuildinfo",
}

CONCEPTUAL_GOLD = {
    ".md", ".txt", ".rst",
}

SENTINEL = {
    ".gitkeep", ".keep", ".gitignore", ".copilotignore",
    ".gitattributes", ".geminiignore", ".python-version",
}

VISUAL = {
    ".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp",
}

SHADER = {
    ".vert", ".frag", ".comp", ".glsl", ".wgsl",
}

# Disabled/suspended config (e.g. .yml.off)
DORMANT_PATTERNS = {".off"}


def classify_extension(ext: str) -> str:
    """Classify a file extension into a gold grade."""
    ext = ext.lower()
    if ext in OPERATIONAL_GOLD:
        return "operational"
    if ext in STRUCTURAL_GOLD:
        return "structural"
    if ext in CONCEPTUAL_GOLD:
        return "conceptual"
    if ext in SENTINEL:
        return "sentinel"
    if ext in VISUAL:
        return "visual"
    if ext in SHADER:
        return "shader"
    if ext in DORMANT_PATTERNS:
        return "dormant"
    return "unclassified"


def classify_file(filepath: str) -> str:
    """Classify a file, handling compound extensions and extensionless files."""
    p = Path(filepath)
    name = p.name
    ext = p.suffix.lower()

    # Sentinel by full name
    if name in (".gitkeep", ".keep", ".gitignore", ".copilotignore",
                ".gitattributes", ".geminiignore", ".python-version",
                ".env"):
        return "sentinel"

    # Dormant: .yml.off, .yaml.off
    if ext == ".off":
        return "dormant"

    # Extensionless files — classify by context
    if not ext:
        return "conceptual"  # session dumps, logs without extension

    return classify_extension(ext)


# ── Naming Pattern Signals ───────────────────────────────────────────────────

NAMING_PATTERNS = [
    (re.compile(r"^[A-Z][A-Z_]+\.md$"), "governance",
     "UPPERCASE.md — governance, methodology, or protocol"),
    (re.compile(r"_v\d+\.\w+$"), "evolution",
     "Versioned file — someone iterated"),
    (re.compile(r" - Copy\.\w+$"), "fork",
     "Copy — someone forked a thought"),
    (re.compile(r"\.bak[_.]"), "backup",
     "Explicit backup — delta is the gold"),
    (re.compile(r"^_tmp_|\.tmp$"), "transient",
     "Transient computation — algorithm may be reusable"),
    (re.compile(r"\.meta\.json$"), "generated",
     "Auto-generated metadata — trace the generator"),
    (re.compile(r"^SKILL\.md$"), "skill",
     "Codified agent capability"),
    (re.compile(r"\.reference\.md$"), "tier2",
     "Tier 2 deep reference — on-demand, not demoted"),
    (re.compile(r"\.instructions\.md$"), "tier1",
     "Tier 1 active governance — auto-loaded"),
]


def detect_naming_signals(filename: str) -> list[dict]:
    """Detect gold signals embedded in the filename itself."""
    signals = []
    for pattern, signal_type, description in NAMING_PATTERNS:
        if pattern.search(filename):
            signals.append({"type": signal_type, "description": description})
    return signals


# ── Ambulant Detection (Files in Motion) ─────────────────────────────────────

def get_ambulant_files(repo_root: Path) -> dict[str, list[str]]:
    """Detect files that are in motion — recently changed, untracked, conflicted."""
    ambulant: dict[str, list[str]] = defaultdict(list)

    try:
        # Modified (unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, cwd=repo_root,
        )
        for f in result.stdout.strip().splitlines():
            if f:
                ambulant["modified"].append(f)

        # Staged
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=repo_root,
        )
        for f in result.stdout.strip().splitlines():
            if f:
                ambulant["staged"].append(f)

        # Untracked
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, cwd=repo_root,
        )
        for f in result.stdout.strip().splitlines():
            if f:
                ambulant["untracked"].append(f)

        # Conflict markers (check modified files for <<<<<<)
        for f in ambulant["modified"]:
            fpath = repo_root / f
            if fpath.exists() and fpath.stat().st_size < 500_000:
                try:
                    content = fpath.read_text(encoding="utf-8", errors="replace")
                    if "<<<<<<" in content:
                        ambulant["conflicted"].append(f)
                except OSError:
                    pass

    except FileNotFoundError:
        pass  # git not available

    return dict(ambulant)


# ── Full Repository Scan ─────────────────────────────────────────────────────

def scan_repository(repo_root: Path) -> dict:
    """Classify every tracked file in the repository."""
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True, text=True, cwd=repo_root,
    )
    files = [f for f in result.stdout.strip().splitlines() if f]

    grade_counts: Counter = Counter()
    signal_counts: Counter = Counter()
    classified: list[dict] = []
    by_grade: dict[str, list[str]] = defaultdict(list)

    for filepath in files:
        name = Path(filepath).name
        ext = Path(filepath).suffix.lower()

        # Sentinel files may not have meaningful extensions
        if name in (".gitkeep", ".keep", ".gitignore", ".copilotignore",
                    ".gitattributes", ".geminiignore", ".python-version"):
            grade = "sentinel"
        else:
            grade = classify_file(filepath)

        naming_signals = detect_naming_signals(name)
        grade_counts[grade] += 1
        by_grade[grade].append(filepath)

        for sig in naming_signals:
            signal_counts[sig["type"]] += 1

        classified.append({
            "path": filepath,
            "grade": grade,
            "extension": ext,
            "naming_signals": naming_signals,
        })

    ambulant = get_ambulant_files(repo_root)

    return {
        "total_files": len(files),
        "grade_summary": dict(grade_counts.most_common()),
        "signal_summary": dict(signal_counts.most_common()),
        "ambulant": ambulant,
        "ambulant_count": sum(len(v) for v in ambulant.values()),
        "files": classified,
        "by_grade": {k: sorted(v) for k, v in by_grade.items()},
    }


# ── Output Formatters ────────────────────────────────────────────────────────

GRADE_ICONS = {
    "operational": "⚙️",
    "structural": "🏗️",
    "conceptual": "📜",
    "sentinel": "🛡️",
    "visual": "🎨",
    "shader": "✨",
    "dormant": "💤",
    "unclassified": "❓",
}

AMBULANT_ICONS = {
    "modified": "📝",
    "staged": "📦",
    "untracked": "🆕",
    "conflicted": "⚡",
}


def print_human_summary(data: dict) -> None:
    """Print a human-readable gold signal report."""
    print("=" * 72)
    print("  GOLD SIGNAL REPORT — Wet-Paper-to-Gold Affordance Classification")
    print(f"  Total files: {data['total_files']}")
    print("=" * 72)

    print("\n  Gold Grades:")
    for grade, count in data["grade_summary"].items():
        icon = GRADE_ICONS.get(grade, "?")
        pct = count / data["total_files"] * 100
        print(f"    {icon} {grade:<15} {count:>5}  ({pct:5.1f}%)")

    if data["signal_summary"]:
        print("\n  Naming Signals (filename-embedded gold markers):")
        for signal, count in data["signal_summary"].items():
            print(f"    🔖 {signal:<15} {count:>5}")

    if data["ambulant_count"] > 0:
        print(f"\n  Ambulant Files ({data['ambulant_count']} in motion):")
        for category, files in data["ambulant"].items():
            icon = AMBULANT_ICONS.get(category, "?")
            print(f"    {icon} {category} ({len(files)}):")
            for f in files[:5]:
                print(f"       {f}")
            if len(files) > 5:
                print(f"       ... and {len(files) - 5} more")
    else:
        print("\n  Ambulant: None — repository is at rest ✅")

    print("\n" + "=" * 72)


def print_ambulant_only(data: dict) -> None:
    """Print only ambulant (in-motion) files."""
    if data["ambulant_count"] == 0:
        print("No ambulant files — repository is at rest.")
        return

    print(f"Ambulant files: {data['ambulant_count']}")
    for category, files in data["ambulant"].items():
        icon = AMBULANT_ICONS.get(category, "?")
        for f in files:
            ext = Path(f).suffix.lower()
            grade = classify_extension(ext)
            gicon = GRADE_ICONS.get(grade, "?")
            print(f"  {icon} {category:<12} {gicon} {grade:<13} {f}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    configure_utf8_output()

    repo_root = find_repo_root()
    if not repo_root:
        print("ERROR: Not inside a git repository.", file=sys.stderr)
        sys.exit(1)

    args = sys.argv[1:]
    as_json = "--json" in args
    ambulant_only = "--ambulant" in args

    data = scan_repository(repo_root)

    if as_json:
        # Strip the full file list for JSON brevity unless --verbose
        if "--verbose" not in args:
            data.pop("files", None)
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        print()
    elif ambulant_only:
        print_ambulant_only(data)
    else:
        print_human_summary(data)


if __name__ == "__main__":
    main()
