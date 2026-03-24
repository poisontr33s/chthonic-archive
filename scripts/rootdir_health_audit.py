#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: rootdir_health_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
rootdir_health_audit.py — Root Directory Health & Hygiene Auditor

@SID:           TOOL_ROOT_AUDIT_V1
@Shabti:          Script
@Context:       Hygiene / Codebase Analysis
@Implements:    CONCEPT_DIRECTORY_HEALTH_AUDIT
@Emits:         STATE_ROOTDIR_HEALTH
@Related:       TOOL_CODEBASE_MAPPER_V1
@Purpose:       rootdir_health_audit.py — Root Directory Health & Hygiene Auditor
FILE METADATA
Created:        2026-01-17
Session Doc:    docs/SESSION_2026-01-17_CLEANUP.md
Related Files:  @SID:TOOL_SESSION_EXTRACTOR_V1, @SID:TOOL_CODEBASE_MAPPER_V1
Output:         docs/ROOTDIR_HEALTH.md

Scans the root directory to assess file hygiene, identify redundancy,
versioning issues, and potential cleanup candidates.

Usage:
    uv run scripts/rootdir_health_audit.py [--output report.md] [--json]
    # Defaults to docs/ROOTDIR_HEALTH.md if no output specified
"""

from __future__ import annotations

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    name: str
    extension: str
    size: int
    modified: datetime
    content_hash: str = ""
    first_lines: str = ""
    version_pattern: str = ""
    has_metadata_header: bool = False


@dataclass
class AuditReport:
    """Complete audit report."""
    scan_time: str = ""
    root_path: str = ""
    total_files: int = 0
    total_size: int = 0
    by_extension: dict[str, list[FileInfo]] = field(default_factory=dict)
    versioned_files: list[tuple[str, list[FileInfo]]] = field(default_factory=list)
    potential_duplicates: list[tuple[FileInfo, FileInfo, float]] = field(default_factory=list)
    merge_candidates: list[tuple[str, list[FileInfo]]] = field(default_factory=list)
    missing_metadata: list[FileInfo] = field(default_factory=list)
    large_files: list[FileInfo] = field(default_factory=list)
    empty_files: list[FileInfo] = field(default_factory=list)
    stray_patterns: list[tuple[str, list[FileInfo]]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


def compute_hash(filepath: Path, sample_size: int = 4096) -> str:
    """Compute hash of file start for similarity detection."""
    try:
        with open(filepath, "rb") as f:
            content = f.read(sample_size)
            return hashlib.md5(content).hexdigest()[:12]
    except:
        return ""


def get_first_lines(filepath: Path, num_lines: int = 10) -> str:
    """Get first N lines for content preview."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                lines.append(line.rstrip())
            return "\n".join(lines)
    except:
        return ""


def detect_version_pattern(filename: str) -> str:
    """Detect versioning patterns in filename."""
    patterns = [
        (r"_v(\d+(?:\.\d+)?)", "underscore_version"),  # _v1, _v1.1
        (r"_(\d+)$", "numeric_suffix"),                 # _1, _2
        (r"[-_](\d{4}-\d{2}-\d{2})", "date_suffix"),   # -2026-01-17
        (r"[-_](old|new|backup|copy)", "backup_suffix"),
        (r"[-_](final|draft|wip)", "status_suffix"),
    ]
    for pattern, name in patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return name
    return ""


def has_metadata_header(content: str, extension: str) -> bool:
    """Check if file has proper metadata header."""
    if extension == ".py":
        return "FILE METADATA" in content or "Created:" in content
    if extension == ".md":
        return "Session Doc:" in content or "Created:" in content or "## File Registry" in content
    if extension in (".ps1", ".sh"):
        return "Created:" in content or ".SYNOPSIS" in content
    return False


def compute_similarity(text1: str, text2: str) -> float:
    """Compute text similarity ratio."""
    return SequenceMatcher(None, text1[:2000], text2[:2000]).ratio()


def find_base_name(filename: str) -> str:
    """Extract base name without version suffixes."""
    # Remove common suffixes
    base = re.sub(r"_v\d+(?:\.\d+)?", "", filename)
    base = re.sub(r"_\d+$", "", base)
    base = re.sub(r"[-_](old|new|backup|copy|final|draft|wip)$", "", base, flags=re.IGNORECASE)
    base = re.sub(r"[-_]\d{4}-\d{2}-\d{2}", "", base)
    return base


def scan_directory(root: Path) -> list[FileInfo]:
    """Scan root directory for all files."""
    files = []

    # Only scan immediate children (root dir), not subdirectories
    for item in root.iterdir():
        if item.is_file() and not item.name.startswith("."):
            try:
                stat = item.stat()
                ext = item.suffix.lower() or "(no extension)"
                first_lines = get_first_lines(item)

                info = FileInfo(
                    path=item,
                    name=item.name,
                    extension=ext,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    content_hash=compute_hash(item),
                    first_lines=first_lines,
                    version_pattern=detect_version_pattern(item.stem),
                    has_metadata_header=has_metadata_header(first_lines, ext),
                )
                files.append(info)
            except Exception as e:
                print(f"Warning: Could not scan {item}: {e}")

    return files


def analyze_files(files: list[FileInfo]) -> AuditReport:
    """Analyze files and generate audit report."""
    report = AuditReport(
        scan_time=datetime.now().isoformat(),
        total_files=len(files),
        total_size=sum(f.size for f in files),
    )

    # Group by extension
    for f in files:
        if f.extension not in report.by_extension:
            report.by_extension[f.extension] = []
        report.by_extension[f.extension].append(f)

    # Find versioned files (group by base name)
    base_name_groups: dict[str, list[FileInfo]] = defaultdict(list)
    for f in files:
        if f.version_pattern:
            base = find_base_name(f.name)
            base_name_groups[base].append(f)

    for base, group in base_name_groups.items():
        if len(group) > 1:
            report.versioned_files.append((base, sorted(group, key=lambda x: x.modified)))

    # Find potential duplicates (same hash)
    hash_groups: dict[str, list[FileInfo]] = defaultdict(list)
    for f in files:
        if f.content_hash:
            hash_groups[f.content_hash].append(f)

    for hash_val, group in hash_groups.items():
        if len(group) > 1:
            for i, f1 in enumerate(group):
                for f2 in group[i+1:]:
                    # Verify with text similarity
                    sim = compute_similarity(f1.first_lines, f2.first_lines)
                    if sim > 0.8:
                        report.potential_duplicates.append((f1, f2, sim))

    # Find merge candidates (similar names, same extension)
    ext_groups: dict[str, list[FileInfo]] = defaultdict(list)
    for f in files:
        ext_groups[f.extension].append(f)

    for ext, group in ext_groups.items():
        if len(group) > 1 and ext in (".md", ".py", ".json"):
            # Group by similar base names
            name_clusters: dict[str, list[FileInfo]] = defaultdict(list)
            for f in group:
                # Simplify name for clustering
                simple = re.sub(r"[-_\d]+", "_", f.name.lower())
                simple = re.sub(r"_+", "_", simple)
                name_clusters[simple].append(f)

            for cluster_key, cluster in name_clusters.items():
                if len(cluster) > 1:
                    report.merge_candidates.append((cluster_key, cluster))

    # Find files missing metadata headers
    code_extensions = {".py", ".ps1", ".sh", ".ts", ".js"}
    for f in files:
        if f.extension in code_extensions and not f.has_metadata_header:
            report.missing_metadata.append(f)

    # Find large files (>500KB)
    for f in files:
        if f.size > 500_000:
            report.large_files.append(f)

    # Find empty files
    for f in files:
        if f.size == 0:
            report.empty_files.append(f)

    # Detect stray patterns (files that look out of place)
    stray_patterns = {
        "session_artifacts": r"SESSION.*\d{4}",
        "temp_files": r"(temp|tmp|test)[-_]",
        "backup_files": r"(backup|bak|old)[-_.]",
        "numbered_versions": r"_\d+\.(py|md|json)$",
    }

    for pattern_name, pattern in stray_patterns.items():
        matches = [f for f in files if re.search(pattern, f.name, re.IGNORECASE)]
        if matches:
            report.stray_patterns.append((pattern_name, matches))

    # Generate recommendations
    if report.versioned_files:
        report.recommendations.append(
            f"MERGE: {len(report.versioned_files)} file groups have multiple versions. "
            "Consider consolidating to single authoritative version."
        )

    if report.potential_duplicates:
        report.recommendations.append(
            f"DELETE: {len(report.potential_duplicates)} potential duplicate file pairs detected. "
            "Review and remove redundant copies."
        )

    if report.missing_metadata:
        report.recommendations.append(
            f"UPDATE: {len(report.missing_metadata)} code files lack metadata headers. "
            "Add FILE METADATA blocks for traceability."
        )

    if report.empty_files:
        report.recommendations.append(
            f"DELETE: {len(report.empty_files)} empty files found. "
            "Remove or populate with content."
        )

    if report.large_files:
        report.recommendations.append(
            f"REVIEW: {len(report.large_files)} files exceed 500KB. "
            "Consider compression or moving to separate storage."
        )

    py_in_root = [f for f in files if f.extension == ".py"]
    if py_in_root:
        report.recommendations.append(
            f"RELOCATE: {len(py_in_root)} Python files in root directory. "
            "Move to scripts/ for better organization."
        )

    return report


def format_size(size: int) -> str:
    """Format file size for display."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def generate_markdown_report(report: AuditReport, root_path: Path) -> str:
    """Generate markdown report."""
    lines = [
        "<!--",
        "================================================================================",
        "SEMANTIC IDENTITY (Anchor & Signal Protocol)",
        "================================================================================",
        "@SID:           STATE_ROOTDIR_HEALTH",
        "@Type:          State",
        "@Context:       Health / Audit",
        "@UpdateFrequency: On-Demand",
        "@SessionOrigin: SESSION_DOC_2026_01_17_CLEANUP",
        "================================================================================",
        "-->",
        "",
        "# Root Directory Health Audit",
        "",
        f"> **Scanned:** {root_path}",
        f"> **Time:** {report.scan_time}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Files | {report.total_files} |",
        f"| Total Size | {format_size(report.total_size)} |",
        f"| File Types | {len(report.by_extension)} |",
        f"| Versioned Groups | {len(report.versioned_files)} |",
        f"| Potential Duplicates | {len(report.potential_duplicates)} |",
        f"| Missing Metadata | {len(report.missing_metadata)} |",
        f"| Empty Files | {len(report.empty_files)} |",
        "",
    ]

    # Health score
    issues = (
        len(report.versioned_files) * 2 +
        len(report.potential_duplicates) * 3 +
        len(report.missing_metadata) +
        len(report.empty_files) * 2 +
        len(report.large_files)
    )
    health_score = max(0, 100 - issues)
    health_status = "[OK] Good" if health_score >= 80 else "[~] Fair" if health_score >= 50 else "[!] Needs Attention"

    lines.extend([
        f"**Health Score:** {health_score}/100 ({health_status})",
        "",
        "---",
        "",
        "## Files by Extension",
        "",
        "| Extension | Count | Total Size |",
        "|-----------|-------|------------|",
    ])

    for ext in sorted(report.by_extension.keys(), key=lambda x: -len(report.by_extension[x])):
        files = report.by_extension[ext]
        total_size = sum(f.size for f in files)
        lines.append(f"| `{ext}` | {len(files)} | {format_size(total_size)} |")

    lines.append("")

    # Versioned files
    if report.versioned_files:
        lines.extend([
            "---",
            "",
            "## Versioned Files (Merge Candidates)",
            "",
            "Files with version suffixes that could be consolidated:",
            "",
        ])
        for base, group in report.versioned_files:
            lines.append(f"### `{base}`")
            lines.append("")
            lines.append("| File | Modified | Size |")
            lines.append("|------|----------|------|")
            for f in group:
                lines.append(f"| `{f.name}` | {f.modified.strftime('%Y-%m-%d')} | {format_size(f.size)} |")
            lines.append("")

    # Potential duplicates
    if report.potential_duplicates:
        lines.extend([
            "---",
            "",
            "## Potential Duplicates",
            "",
            "| File 1 | File 2 | Similarity |",
            "|--------|--------|------------|",
        ])
        for f1, f2, sim in report.potential_duplicates:
            lines.append(f"| `{f1.name}` | `{f2.name}` | {sim*100:.0f}% |")
        lines.append("")

    # Missing metadata
    if report.missing_metadata:
        lines.extend([
            "---",
            "",
            "## Missing Metadata Headers",
            "",
            "Code files without FILE METADATA block:",
            "",
        ])
        for f in report.missing_metadata[:20]:  # Limit display
            lines.append(f"- `{f.name}`")
        if len(report.missing_metadata) > 20:
            lines.append(f"- ... and {len(report.missing_metadata) - 20} more")
        lines.append("")

    # Large files
    if report.large_files:
        lines.extend([
            "---",
            "",
            "## Large Files (>500KB)",
            "",
            "| File | Size |",
            "|------|------|",
        ])
        for f in sorted(report.large_files, key=lambda x: -x.size):
            lines.append(f"| `{f.name}` | {format_size(f.size)} |")
        lines.append("")

    # Empty files
    if report.empty_files:
        lines.extend([
            "---",
            "",
            "## Empty Files",
            "",
        ])
        for f in report.empty_files:
            lines.append(f"- `{f.name}`")
        lines.append("")

    # Stray patterns
    if report.stray_patterns:
        lines.extend([
            "---",
            "",
            "## Stray File Patterns",
            "",
        ])
        for pattern_name, files in report.stray_patterns:
            lines.append(f"### {pattern_name.replace('_', ' ').title()}")
            lines.append("")
            for f in files[:10]:
                lines.append(f"- `{f.name}`")
            if len(files) > 10:
                lines.append(f"- ... and {len(files) - 10} more")
            lines.append("")

    # Recommendations
    if report.recommendations:
        lines.extend([
            "---",
            "",
            "## Recommendations",
            "",
        ])
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. **{rec.split(':')[0]}:** {rec.split(':', 1)[1].strip()}")
        lines.append("")

    # Python files in root (specific call-out)
    py_files = report.by_extension.get(".py", [])
    if py_files:
        lines.extend([
            "---",
            "",
            "## Python Files in Root (Should Move to scripts/)",
            "",
            "| File | Size | Has Metadata |",
            "|------|------|--------------|",
        ])
        for f in sorted(py_files, key=lambda x: x.name):
            has_meta = "✓" if f.has_metadata_header else "✗"
            lines.append(f"| `{f.name}` | {format_size(f.size)} | {has_meta} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        f"*Generated by rootdir_health_audit.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ])

    return "\n".join(lines)


def generate_json_report(report: AuditReport) -> str:
    """Generate JSON report."""
    def file_to_dict(f: FileInfo) -> dict:
        return {
            "name": f.name,
            "extension": f.extension,
            "size": f.size,
            "modified": f.modified.isoformat(),
            "has_metadata": f.has_metadata_header,
            "version_pattern": f.version_pattern,
        }

    output = {
        "scan_time": report.scan_time,
        "summary": {
            "total_files": report.total_files,
            "total_size": report.total_size,
            "extension_counts": {ext: len(files) for ext, files in report.by_extension.items()},
        },
        "versioned_files": [
            {"base": base, "files": [file_to_dict(f) for f in group]}
            for base, group in report.versioned_files
        ],
        "potential_duplicates": [
            {"file1": f1.name, "file2": f2.name, "similarity": sim}
            for f1, f2, sim in report.potential_duplicates
        ],
        "missing_metadata": [f.name for f in report.missing_metadata],
        "empty_files": [f.name for f in report.empty_files],
        "large_files": [file_to_dict(f) for f in report.large_files],
        "recommendations": report.recommendations,
    }
    return json.dumps(output, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Audit root directory health and hygiene."
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."),
        help="Root directory to scan (default: current)"
    )
    parser.add_argument(
        "--output", "-o", type=Path,
        help="Output file path (default: Auto-resolves @SID: STATE_ROOTDIR_HEALTH)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of markdown"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print report to console without saving"
    )

    args = parser.parse_args()

    root = args.root.resolve()
    print(f"Scanning: {root}")

    files = scan_directory(root)
    print(f"Found {len(files)} files")

    report = analyze_files(files)
    report.root_path = str(root)

    if args.json:
        output = generate_json_report(report)
    else:
        output = generate_markdown_report(report, root)

    if args.dry_run:
        print("\n[DRY RUN] Report Output:")
        print("-" * 40)
        print(output)
        print("-" * 40)
        return

    # Dynamic Output Path Resolution (Anchor & Signal Protocol)
    # 1. Scan for existing file with target @SID: STATE_ROOTDIR_HEALTH
    # 2. If found, overwrite that file (breaking entropy loop)
    # 3. If not found, use default docs/ROOTDIR_HEALTH.md

    output_path = args.output
    if not output_path:
        target_sid = "STATE_ROOTDIR_HEALTH"
        default_path = Path("docs/ROOTDIR_HEALTH.md")

        # Simple scan of docs/ directory for .md file with the SID
        found_path = None
        docs_dir = Path("docs")
        if docs_dir.exists():
            try:
                for md_file in docs_dir.glob("*.md"):
                    try:
                        content = md_file.read_text(encoding="utf-8", errors="ignore")
                        if f"@SID:           {target_sid}" in content or f"@SID: {target_sid}" in content:
                            found_path = md_file
                            break
                    except OSError:
                        continue
            except OSError:
                pass

        if found_path:
            print(f"Resolving output to existing State File: {found_path}")
            output_path = found_path
        else:
            print(f"State File not found. Creating default: {default_path}")
            output_path = default_path

    # Ensure parent directory exists
    try:
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Report written to: {output_path}")
    except OSError as e:
        print(f"Error writing report: {e}")


if __name__ == "__main__":
    main()
