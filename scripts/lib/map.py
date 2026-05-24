#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: map.py
# ║ Python module: IGNORE_DIRS, FolderStats, CodebaseMap, scan_tree, generate_markdown_map, main
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_CODEBASE_MAPPER_V1
# ║ Purpose: map.py — Codebase Cartographer & Inventory Generator
# ║ Exports: IGNORE_DIRS, FolderStats, CodebaseMap, scan_tree, generate_markdown_
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
map.py — Codebase Cartographer & Inventory Generator

@SID:           TOOL_CODEBASE_MAPPER_V1
@Type:          CLI Tool
@Context:       Documentation / Inventory
@Implements:    CONCEPT_CODEBASE_CARTOGRAPHY, ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@Emits:         STATE_CODEBASE_INVENTORY
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP

Traverses the repository to map directory structure,
inventory files by type, and generate codebase overview.

Usage:
    chthonic map                    # Map current directory
    chthonic map --json             # Output as JSON
    chthonic map --output map.md    # Custom output location
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



import argparse
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .shared import (
    configure_utf8_output,
    setup_logging,
    add_common_args,
    add_output_arg,
    print_json,
    handle_errors,
    find_repo_root,
)

# Configure UTF-8 output
configure_utf8_output()


IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "__pycache__", "dist", ".bun",
    "target", ".vscode", "build", "dumpster-dive"
}


@dataclass
class FolderStats:
    """Statistics for a folder."""
    path: Path
    file_counts: dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    has_readme: bool = False


@dataclass
class CodebaseMap:
    """Complete codebase inventory."""
    root: str = ""
    total_dirs: int = 0
    total_files: int = 0
    by_extension: dict[str, int] = field(default_factory=dict)
    folders: list[FolderStats] = field(default_factory=list)


def scan_tree(root: Path, logger) -> CodebaseMap:
    """Recursively map the codebase."""
    codebase_map = CodebaseMap(root=str(root))
    all_ext_counts = defaultdict(int)
    folders = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter ignored directories
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]

        current_path = Path(dirpath)
        rel_path = current_path.relative_to(root)

        # Skip if in ignored path segments
        if any(part in IGNORE_DIRS for part in current_path.parts):
            continue

        file_counts = defaultdict(int)
        has_readme = False

        for f in filenames:
            ext = Path(f).suffix.lower() or "(no-ext)"
            file_counts[ext] += 1
            all_ext_counts[ext] += 1

            if f.lower() == "readme.md":
                has_readme = True

        if filenames:  # Only record non-empty directories
            folder_stats = FolderStats(
                path=rel_path,
                file_counts=dict(file_counts),
                total_files=len(filenames),
                has_readme=has_readme
            )
            folders.append(folder_stats)

    codebase_map.total_dirs = len(folders)
    codebase_map.total_files = sum(ext_count for ext_count in all_ext_counts.values())
    codebase_map.by_extension = dict(all_ext_counts)
    codebase_map.folders = sorted(folders, key=lambda f: f.total_files, reverse=True)

    logger.info(f"Mapped {codebase_map.total_dirs} directories, {codebase_map.total_files} files")

    return codebase_map


def generate_markdown_map(codebase_map: CodebaseMap) -> str:
    """Generate markdown inventory report."""
    lines = [
        "# Codebase Inventory",
        "",
        "**@SID:** STATE_CODEBASE_INVENTORY",
        "",
        "## Summary",
        "",
        f"- **Root:** `{codebase_map.root}`",
        f"- **Directories:** {codebase_map.total_dirs}",
        f"- **Total Files:** {codebase_map.total_files}",
        "",
        "## File Types",
        ""
    ]

    for ext, count in sorted(codebase_map.by_extension.items(), key=lambda x: x[1], reverse=True)[:20]:
        lines.append(f"- `{ext}`: {count} files")

    lines.extend([
        "",
        "## Directory Structure (Top 15 by file count)",
        ""
    ])

    for folder in codebase_map.folders[:15]:
        readme_indicator = "✓ README" if folder.has_readme else ""
        lines.append(f"### `{folder.path}` ({folder.total_files} files) {readme_indicator}")
        lines.append("")

        for ext, count in sorted(folder.file_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            lines.append(f"- `{ext}`: {count}")
        lines.append("")

    return "\n".join(lines)


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Map codebase structure and inventory files.",
        prog="chthonic map"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."),
        help="Root directory to map (default: current)"
    )

    add_common_args(parser)
    add_output_arg(parser, "Output file path (auto-resolves @SID by default)")

    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    root = args.root.resolve()
    logger.info(f"Mapping codebase from: {root}")

    codebase_map = scan_tree(root, logger)

    if args.dry_run:
        logger.info("\n[DRY RUN] Map Preview:")
        if args.json:
            print_json({
                "root": codebase_map.root,
                "total_dirs": codebase_map.total_dirs,
                "total_files": codebase_map.total_files,
                "by_extension": codebase_map.by_extension
            })
        else:
            print(generate_markdown_map(codebase_map)[:500] + "...")
        return

    # Determine output path
    output_path = args.output
    if not output_path:
        repo_root = find_repo_root()
        output_path = repo_root / "docs" / "CODEBASE_INVENTORY.md"
        logger.info(f"Using default output: {output_path}")

    # Generate output
    if args.json:
        output_data = {
            "root": codebase_map.root,
            "total_dirs": codebase_map.total_dirs,
            "total_files": codebase_map.total_files,
            "by_extension": codebase_map.by_extension,
            "folders": [
                {
                    "path": str(f.path),
                    "file_counts": f.file_counts,
                    "total_files": f.total_files,
                    "has_readme": f.has_readme
                }
                for f in codebase_map.folders
            ]
        }
        if args.output:
            import json
            output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
        else:
            print_json(output_data)
    else:
        output_text = generate_markdown_map(codebase_map)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        logger.info(f"Map written to: {output_path}")


if __name__ == "__main__":
    main()
