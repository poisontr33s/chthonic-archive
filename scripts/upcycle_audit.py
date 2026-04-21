#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: upcycle_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
upcycle_audit.py — File Upcycling Auditor

@SID:           TOOL_UPCYCLE_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Nominates files for refactor/consolidation based on code
                vs text density. Filetype-aware heuristics, no AI inference.
                Usage: uv run python scripts/upcycle_audit.py <paths...>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# sys.path guard: ensure repo root is importable regardless of invocation CWD
_REPO_ROOT_CANDIDATE = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_CANDIDATE) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_CANDIDATE))

from scripts.lib.shared import find_repo_root as _find_repo_root


# Filetype comment markers for density calculation
COMMENT_MARKERS = {
    ".py": "#",
    ".ps1": "#",
    ".sh": "#",
    ".bash": "#",
    ".js": "//",
    ".ts": "//",
    ".tsx": "//",
    ".jsx": "//",
    ".rs": "//",
    ".c": "//",
    ".cpp": "//",
    ".h": "//",
    ".md": None,  # markdown is prose-first
    ".txt": None,
    ".json": None,
    ".toml": "#",
    ".yaml": "#",
    ".yml": "#",
}

# Files/patterns to skip (governance-critical or binary)
SKIP_PATTERNS = {
    ".git",
    "node_modules",
    ".venv",
    "target",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "*.lock",
    "*.log",
    "*.bin",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.spv",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.ico",
    "*.woff",
    "*.woff2",
    "*.ttf",
    "*.eot",
}

# Exempt files from upcycle nomination (ABI-stable contracts)
# These files are intentionally documented and must not be flagged
EXEMPT_FROM_NOMINATION = {
    "scripts/shell_capabilities.ps1",  # ABI-stable probe - comments allowed
}


def should_skip(path: Path) -> bool:
    """Check if path matches skip patterns."""
    path_str = str(path)
    for pattern in SKIP_PATTERNS:
        if pattern.startswith("*."):
            if path.suffix == pattern[1:]:
                return True
        elif pattern in path_str:
            return True
    return False


def analyze_file(
    path: Path,
    text_ratio_code: float = 0.30,
    text_ratio_md: float = 0.70,
    blank_ratio_min: float = 0.30,
    min_lines_upcycle: int = 30,
    md_min_lines: int = 80,
    md_code_ratio: float = 0.20,
) -> Dict:
    """
    Analyze a single file for code/text density.

    Returns dict with:
        - path, ext, lines, code_lines, text_lines, blank_lines
        - code_ratio, text_ratio
        - flags (list of heuristic signals)
        - upcycle_candidate (bool)
    """
    ext = path.suffix.lower()
    comment = COMMENT_MARKERS.get(ext)

    # Skip files with unknown extensions
    if ext and ext not in COMMENT_MARKERS:
        return None

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {
            "path": str(path),
            "error": str(e),
            "upcycle_candidate": False,
        }

    total = code = text = blank = 0

    for line in content.splitlines():
        stripped = line.strip()
        total += 1

        if not stripped:
            blank += 1
        elif ext == ".md" or ext == ".txt":
            text += 1
        elif comment and stripped.startswith(comment):
            text += 1
        else:
            code += 1

    # Calculate ratios
    text_ratio = text / max(total, 1)
    code_ratio = code / max(total, 1)
    blank_ratio = blank / max(total, 1)

    # Apply heuristics
    flags = []

    # Too small to meaningfully upcycle
    if total < min_lines_upcycle:
        flags.append("too_small_to_upcycle")

    # Code files with high prose ratio (over-documented?)
    if ext in {".ps1", ".py", ".sh", ".bash"} and text_ratio > text_ratio_code:
        flags.append("high_prose_for_code_file")

    # Heavy prose docs (potential consolidation candidates)
    if ext == ".md" and text_ratio > text_ratio_md and total > md_min_lines:
        flags.append("heavy_prose_doc")

    # Probe contract violation (shell_capabilities.ps1 must be probe-only)
    if "shell_capabilities" in path.name and code < total * 0.7:
        flags.append("probe_contract_violation")

    # High blank ratio (formatting bloat?)
    if blank_ratio > blank_ratio_min and total > 50:
        flags.append("high_blank_ratio")

    # Markdown with code blocks (might belong in code file)
    if ext == ".md" and code_ratio > md_code_ratio:
        flags.append("md_with_code_blocks")

    # PNPM references (deprecated per bun-first policy)
    if "pnpm" in content.lower():
        flags.append("contains_pnpm_references")

    # NPM/Yarn references (deprecated per bun-first policy)
    # Note: Checking for legacy package manager usage, not Bun itself
    if "bun " not in content.lower() and ("npm " in content.lower() or "yarn " in content.lower()):
        flags.append("contains_legacy_package_manager_references")

    # Determine if upcycle candidate
    upcycle_flags = {
        "high_prose_for_code_file",
        "heavy_prose_doc",
        "probe_contract_violation",
        "contains_pnpm_references",
        "contains_npm_references",
        "md_with_code_blocks",
    }

    # Check if file is exempt from nomination (ABI-stable contracts)
    try:
        relative_path = str(path.absolute().relative_to(Path.cwd()))
    except ValueError:
        relative_path = str(path.absolute())

    # Normalize path separators for comparison
    normalized_path = relative_path.replace("\\", "/")
    is_exempt = any(normalized_path.endswith(exempt_path.replace("\\", "/")) for exempt_path in EXEMPT_FROM_NOMINATION)

    # Find primary nomination reason (first matching upcycle flag)
    nomination_reason = None
    if not is_exempt:
        for flag in flags:
            if flag in upcycle_flags:
                nomination_reason = flag
                break

    is_candidate = nomination_reason is not None

    # Handle path display - use absolute path, then make relative if possible
    try:
        display_path = str(path.absolute().relative_to(Path.cwd()))
    except ValueError:
        # Path is outside cwd, use absolute path
        display_path = str(path.absolute())

    result = {
        "path": display_path,
        "ext": ext,
        "lines": total,
        "code_lines": code,
        "text_lines": text,
        "blank_lines": blank,
        "code_ratio": round(code_ratio, 2),
        "text_ratio": round(text_ratio, 2),
        "blank_ratio": round(blank_ratio, 2),
        "flags": flags,
        "upcycle_candidate": is_candidate,
    }

    # Add nomination reason if candidate
    if is_candidate:
        result["nomination_reason"] = nomination_reason

    return result


def scan_paths(
    paths: List[str],
    text_ratio_code: float = 0.30,
    text_ratio_md: float = 0.70,
    blank_ratio_min: float = 0.30,
    min_lines_upcycle: int = 30,
    md_min_lines: int = 80,
    md_code_ratio: float = 0.20,
) -> List[Dict]:
    """Scan provided paths and return analysis results."""
    results = []
    thresholds = dict(
        text_ratio_code=text_ratio_code,
        text_ratio_md=text_ratio_md,
        blank_ratio_min=blank_ratio_min,
        min_lines_upcycle=min_lines_upcycle,
        md_min_lines=md_min_lines,
        md_code_ratio=md_code_ratio,
    )

    for p in paths:
        path = Path(p)

        if not path.exists():
            print(f"Warning: {p} does not exist", file=sys.stderr)
            continue

        if path.is_dir():
            for file in path.rglob("*"):
                if file.is_file() and not should_skip(file):
                    result = analyze_file(file, **thresholds)
                    if result:
                        results.append(result)
        else:
            if not should_skip(path):
                result = analyze_file(path, **thresholds)
                if result:
                    results.append(result)

    return results


def prompt_mode_if_ambiguous(args):
    """Interactive mode selection when no explicit flags provided."""
    if args.candidates_only or args.summary:
        return args  # explicit intent already provided

    print(
        "\nSelect upcycle audit mode:\n"
        "  [1] Full JSON report (default)\n"
        "  [2] Candidates only\n"
        "  [3] Summary (human-readable + JSON envelope)\n"
        "  [q] Quit\n",
        file=sys.stderr
    )

    choice = input("Enter choice [1/2/3/q]: ").strip().lower()

    if choice in ("", "1"):
        return args
    if choice == "2":
        args.candidates_only = True
        return args
    if choice == "3":
        args.summary = True
        return args
    if choice == "q":
        raise SystemExit(0)

    print("Invalid choice.", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan codebase for upcycling candidates based on code/text density"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (optional when --dir is used)"
    )
    parser.add_argument(
        "--dir", "-d", type=Path, default=None,
        help="Recursively scan a directory (appended to positional paths; defaults to repo root when neither paths nor --dir are given).",
    )
    parser.add_argument(
        "--candidates-only",
        action="store_true",
        help="Only show upcycle candidates"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics instead of full JSON"
    )
    parser.add_argument(
        "--text-ratio-code", type=float, default=0.30, metavar="FLOAT",
        help="Max text ratio before flagging code file (default: 0.30).",
    )
    parser.add_argument(
        "--text-ratio-md", type=float, default=0.70, metavar="FLOAT",
        help="Min text ratio to flag .md file as heavy prose (default: 0.70).",
    )
    parser.add_argument(
        "--blank-ratio-min", type=float, default=0.30, metavar="FLOAT",
        help="Min blank-line ratio to flag formatting bloat (default: 0.30).",
    )
    parser.add_argument(
        "--min-lines-upcycle", type=int, default=30, metavar="INT",
        help="Skip files with fewer lines than this (default: 30).",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Write JSON output to this file (for zombie pipeline integration).",
    )

    args = parser.parse_args()

    # Build effective path list
    all_paths: List[str] = list(args.paths)
    if args.dir:
        all_paths.append(str(args.dir))
    if not all_paths:
        # Default: repo root
        all_paths = [str(_find_repo_root())]

    # Interactive mode selection if no explicit intent provided
    args = prompt_mode_if_ambiguous(args)

    # Print resolved mode to stderr for audit trail
    mode = 'summary' if args.summary else 'candidates' if args.candidates_only else 'full'
    print(f"[upcycle-audit] mode = {mode}", file=sys.stderr)

    # Scan paths
    thresholds = dict(
        text_ratio_code=args.text_ratio_code,
        text_ratio_md=args.text_ratio_md,
        blank_ratio_min=args.blank_ratio_min,
        min_lines_upcycle=args.min_lines_upcycle,
    )
    results = scan_paths(all_paths, **thresholds)

    # Filter if requested
    if args.candidates_only:
        results = [r for r in results if r.get("upcycle_candidate")]

    # Output format
    if args.summary:
        total_files = len(results)
        candidates = sum(1 for r in results if r.get("upcycle_candidate"))
        total_lines = sum(r.get("lines", 0) for r in results)

        # Build flag distribution
        flag_counts = {}
        for r in results:
            for flag in r.get("flags", []):
                flag_counts[flag] = flag_counts.get(flag, 0) + 1

        # Human-readable summary to stderr, JSON to stdout
        print(f"Total files scanned: {total_files}", file=sys.stderr)
        print(f"Upcycle candidates: {candidates}", file=sys.stderr)
        print(f"Total lines: {total_lines:,}", file=sys.stderr)
        print(f"\nFlag distribution:", file=sys.stderr)

        for flag, count in sorted(flag_counts.items(), key=lambda x: -x[1]):
            print(f"  {flag}: {count}", file=sys.stderr)

        # Build schema envelope for JSON output
        from datetime import datetime, UTC
        output_payload = {
            "schema": "upcycle-audit.v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_files": total_files,
                "candidates": candidates,
                "total_lines": total_lines,
                "flag_distribution": flag_counts,
            },
            "results": results
        }
        _emit(output_payload, args.output)
    else:
        # JSON output (default) - still needs schema envelope
        from datetime import datetime, UTC
        output_payload = {
            "schema": "upcycle-audit.v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "results": results
        }
        _emit(output_payload, args.output)


def _emit(payload: Dict, output_path: "Path | None") -> None:
    """Print JSON to stdout or write to output_path."""
    text = json.dumps(payload, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"[upcycle-audit] written: {output_path}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
