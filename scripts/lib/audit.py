#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: audit.py
# ║ Python module: FileInfo, AuditReport, compute_hash, detect_version_pattern, scan_directory, analyze_files...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_ROOT_AUDIT_V1
# ║ Purpose: audit.py — Root Directory Health & Hygiene Auditor
# ║ Exports: FileInfo, AuditReport, compute_hash, detect_version_pattern, scan_di
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependents (Rely on me):
# ║   └─◄ scripts/lib/shared.py
# ╚════════════════════════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""
audit.py — Root Directory Health & Hygiene Auditor

@SID:           TOOL_ROOT_AUDIT_V1
@Type:          CLI Tool
@Context:       Hygiene / Codebase Analysis
@Implements:    CONCEPT_DIRECTORY_HEALTH_AUDIT, ROADMAP_TOOL_CONSOLIDATION_2026_01_27
@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP
@Emits:         STATE_ROOTDIR_HEALTH

Scans the root directory to assess file hygiene, identify redundancy,
versioning issues, and potential cleanup candidates.

Usage:
    chthonic audit                         # Scan current directory
    chthonic audit --root DIR             # Scan specific directory
    chthonic audit --json                  # Output as JSON
    chthonic audit --output report.md      # Custom output location
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



import argparse
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    name: str
    extension: str
    size: int
    modified: datetime
    content_hash: str = ""
    version_pattern: str = ""


@dataclass
class AuditReport:
    """Complete audit report."""
    scan_time: str = ""
    root_path: str = ""
    total_files: int = 0
    total_size: int = 0
    by_extension: dict[str, int] = field(default_factory=dict)
    versioned_files: list[tuple[str, int]] = field(default_factory=list)
    large_files: list[tuple[str, int]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def compute_hash(filepath: Path, sample_size: int = 4096) -> str:
    """Compute hash of file start for similarity detection."""
    try:
        with open(filepath, "rb") as f:
            content = f.read(sample_size)
            return hashlib.md5(content).hexdigest()[:12]
    except:
        return ""


def detect_version_pattern(filename: str) -> str:
    """Detect versioning patterns in filename."""
    patterns = [
        r"_v(\d+(?:\.\d+)?)",
        r"_(\d+)$",
        r"[-_](\d{4}-\d{2}-\d{2})",
        r"[-_](old|new|backup|copy)",
        r"[-_](final|draft|wip)",
    ]
    for pattern in patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return pattern
    return ""


def scan_directory(root: Path, logger) -> list[FileInfo]:
    """Scan root directory for all files."""
    files = []

    for item in root.iterdir():
        if item.is_file() and not item.name.startswith("."):
            try:
                stat = item.stat()
                ext = item.suffix.lower() or "(no extension)"

                info = FileInfo(
                    path=item,
                    name=item.name,
                    extension=ext,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    content_hash=compute_hash(item),
                    version_pattern=detect_version_pattern(item.stem),
                )
                files.append(info)
            except Exception as e:
                logger.warning(f"Could not scan {item}: {e}")

    return files


def analyze_files(files: list[FileInfo], logger) -> AuditReport:
    """Analyze files and generate audit report."""
    report = AuditReport(
        scan_time=datetime.now().isoformat(),
        total_files=len(files),
        total_size=sum(f.size for f in files),
    )

    # Group by extension
    ext_counts = defaultdict(int)
    for f in files:
        ext_counts[f.extension] += 1
    report.by_extension = dict(ext_counts)

    # Find versioned files
    versioned = [(f.name, f.size) for f in files if f.version_pattern]
    report.versioned_files = sorted(versioned)

    # Find large files (> 1MB)
    large = [(f.name, f.size) for f in files if f.size > 1024 * 1024]
    report.large_files = sorted(large, key=lambda x: x[1], reverse=True)

    # Generate recommendations
    if report.versioned_files:
        report.recommendations.append(
            f"Found {len(report.versioned_files)} versioned files - consider consolidation"
        )
    if report.large_files:
        report.recommendations.append(
            f"Found {len(report.large_files)} large files (>1MB) - review for archival"
        )

    logger.info(f"Analysis complete: {report.total_files} files, {len(report.by_extension)} types")

    return report


def generate_markdown_report(report: AuditReport) -> str:
    """Generate markdown report."""
    lines = [
        f"# Root Directory Health Audit",
        f"",
        f"**@SID:** STATE_ROOTDIR_HEALTH",
        f"",
        f"## Scan Summary",
        f"",
        f"- **Scan Time:** {report.scan_time}",
        f"- **Root Path:** `{report.root_path}`",
        f"- **Total Files:** {report.total_files}",
        f"- **Total Size:** {report.total_size / (1024 * 1024):.2f} MB",
        f"",
        f"## File Types",
        f""
    ]

    for ext, count in sorted(report.by_extension.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- `{ext}`: {count} files")

    if report.versioned_files:
        lines.extend([
            "",
            f"## Versioned Files ({len(report.versioned_files)})",
            ""
        ])
        for name, size in report.versioned_files[:10]:
            lines.append(f"- {name} ({size} bytes)")

    if report.large_files:
        lines.extend([
            "",
            f"## Large Files (>1MB)",
            ""
        ])
        for name, size in report.large_files[:10]:
            lines.append(f"- {name} ({size / (1024 * 1024):.2f} MB)")

    if report.recommendations:
        lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        for rec in report.recommendations:
            lines.append(f"- {rec}")

    return "\n".join(lines)


@handle_errors
def main():
    parser = argparse.ArgumentParser(
        description="Audit root directory health and hygiene.",
        prog="chthonic audit"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."),
        help="Root directory to scan (default: current)"
    )

    add_common_args(parser)
    add_output_arg(parser, "Output file path (auto-resolves @SID by default)")

    args = parser.parse_args()
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)

    root = args.root.resolve()
    logger.info(f"Scanning: {root}")

    files = scan_directory(root, logger)
    logger.info(f"Found {len(files)} files")

    report = analyze_files(files, logger)
    report.root_path = str(root)

    if args.dry_run:
        logger.info("\n[DRY RUN] Report Preview:")
        if args.json:
            print_json({
                "scan_time": report.scan_time,
                "root_path": report.root_path,
                "total_files": report.total_files,
                "total_size": report.total_size,
                "by_extension": report.by_extension,
                "versioned_files": report.versioned_files[:10],
                "large_files": report.large_files[:10],
                "recommendations": report.recommendations
            })
        else:
            print(generate_markdown_report(report)[:500] + "...")
        return

    # Determine output path
    output_path = args.output
    if not output_path:
        repo_root = find_repo_root()
        output_path = repo_root / "docs" / "ROOTDIR_HEALTH.md"
        logger.info(f"Using default output: {output_path}")

    # Generate text output
    if args.json:
        output_text = {
            "scan_time": report.scan_time,
            "root_path": report.root_path,
            "total_files": report.total_files,
            "total_size": report.total_size,
            "by_extension": report.by_extension,
            "versioned_files": report.versioned_files,
            "large_files": report.large_files,
            "recommendations": report.recommendations
        }
        if args.output:
            import json
            output_path.write_text(json.dumps(output_text, indent=2), encoding="utf-8")
        else:
            print_json(output_text)
    else:
        output_text = generate_markdown_report(report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        logger.info(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
