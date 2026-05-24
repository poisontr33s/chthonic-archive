#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
kcp_header_classifier.py - Classify KCP header state for source files.

@SID:           TOOL_KCP_HEADER_CLASSIFIER_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_KCP_MIGRATION_AUDIT
@Ankh-Tinku:    STATE_KCP_AUDIT_CLASSIFIED
@Purpose:       Scans source files and classifies header state as
                LEGACY, KCP-COMPLIANT, HYBRID, or NONE using the
                canonical regex patterns from KCP_PROTOCOL_ONTOLOGY.md §8.
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


# KCP canonical regex patterns from docs/standards/KCP_PROTOCOL_ONTOLOGY.md §8.
CARTOUCHE_TOP = re.compile(r"^[#/]+\s*╔═{10,}", re.MULTILINE)
ARTIFACT_NAME = re.compile(r"║\s+THE DECORATOR'S BLESSING:\s+(.+)")
SPECTRUM = re.compile(r"║\s+Wedjat-Quipu Spectrum:\s+(\S+)")
ZONE = re.compile(r"║\s+Temple-Ayllu Zone:\s+(.+)")
RADIANCE = re.compile(r"║\s+└─◄\s+(.+)")
CARTOUCHE_BOTTOM = re.compile(r"^[#/]+\s*╚═{10,}", re.MULTILINE)

SID = re.compile(r"@SID:\s+(\S+)")
SHABTI = re.compile(r"@Shabti:\s+(.+?)(?:\n|$)")
HEKA_AYNI = re.compile(r"@Heka-Ayni:\s+(\S+)")
ANKH_TINKU = re.compile(r"@Ankh-Tinku:\s+(\S+)")
PURPOSE = re.compile(r"@Purpose:\s+(.+(?:\n\s{16}.+)*)", re.MULTILINE)

LEGACY_ENVELOPE_SID = re.compile(r"║\s+Semantic ID:\s+")
LEGACY_ENVELOPE_PURPOSE = re.compile(r"║\s+Purpose:\s+")
LEGACY_ENVELOPE_MODULE = re.compile(r"║\s+Module:\s+")
LEGACY_ENVELOPE_EXPORTS = re.compile(r"║\s+Exports:\s+")
LEGACY_SPECTRAL_FREQ = re.compile(r"║\s+Spectral Frequency:\s+")
LEGACY_ARCH_ROLE = re.compile(r"║\s+Architectural Role:\s+")


KCP_DETECTORS = {
    "cartouche_top": CARTOUCHE_TOP,
    "artifact_name": ARTIFACT_NAME,
    "spectrum": SPECTRUM,
    "zone": ZONE,
    "radiance": RADIANCE,
    "cartouche_bottom": CARTOUCHE_BOTTOM,
    "sid": SID,
    "shabti": SHABTI,
    "heka_ayni": HEKA_AYNI,
    "ankh_tinku": ANKH_TINKU,
    "purpose": PURPOSE,
}

LEGACY_DETECTORS = {
    "legacy_envelope_sid": LEGACY_ENVELOPE_SID,
    "legacy_envelope_purpose": LEGACY_ENVELOPE_PURPOSE,
    "legacy_envelope_module": LEGACY_ENVELOPE_MODULE,
    "legacy_envelope_exports": LEGACY_ENVELOPE_EXPORTS,
    "legacy_spectral_frequency": LEGACY_SPECTRAL_FREQ,
    "legacy_architectural_role": LEGACY_ARCH_ROLE,
}

REQUIRED_KCP_FIELDS = (
    "cartouche_top",
    "artifact_name",
    "spectrum",
    "zone",
    "cartouche_bottom",
    "sid",
    "shabti",
    "purpose",
)

CLASSIFICATIONS = ("LEGACY", "KCP-COMPLIANT", "HYBRID", "NONE")
DEFAULT_EXTENSIONS = (".py", ".ts", ".tsx", ".ps1", ".rs")
IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "target",
}


def _relative_display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _matches(pattern: re.Pattern[str], text: str) -> bool:
    return pattern.search(text) is not None


def classify_text(file_path: Path, text: str) -> dict[str, object]:
    detected = {
        name: _matches(pattern, text) for name, pattern in {**KCP_DETECTORS, **LEGACY_DETECTORS}.items()
    }

    detected_fields = sorted(name for name, matched in detected.items() if matched)
    missing_fields = [field for field in REQUIRED_KCP_FIELDS if not detected[field]]

    has_kcp_signals = any(detected[name] for name in KCP_DETECTORS)
    # @SID appears in both legacy PMS-v3 and KCP. Use KCP-distinctive fields
    # (new cartouche names or renamed Khipu tags) for state separation.
    has_kcp_distinctive_signals = any(
        detected[name]
        for name in (
            "spectrum",
            "zone",
            "radiance",
            "shabti",
            "heka_ayni",
            "ankh_tinku",
            "purpose",
        )
    )
    has_legacy_signals = any(detected[name] for name in LEGACY_DETECTORS)
    is_kcp_compliant = not has_legacy_signals and all(detected[field] for field in REQUIRED_KCP_FIELDS)

    sid_occurrences = len(SID.findall(text))
    dual_sid = detected["legacy_envelope_sid"] and sid_occurrences >= 1

    if is_kcp_compliant:
        classification = "KCP-COMPLIANT"
    elif has_legacy_signals and not has_kcp_distinctive_signals:
        classification = "LEGACY"
    elif has_kcp_signals or has_legacy_signals:
        classification = "HYBRID"
    else:
        classification = "NONE"

    return {
        "file_path": _relative_display_path(file_path),
        "classification": classification,
        "detected_fields": detected_fields,
        "missing_fields": missing_fields,
        "dual_sid": bool(dual_sid),
    }


def _iter_files_git_tracked(target: Path, extensions: tuple[str, ...]) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    root = Path.cwd().resolve()
    target_resolved = target.resolve()

    files: list[Path] = []
    for raw_item in result.stdout.split(b"\x00"):
        if not raw_item:
            continue
        rel_path = Path(raw_item.decode("utf-8", errors="replace"))
        full_path = (root / rel_path).resolve()
        if full_path.is_dir():
            continue
        if full_path.suffix.lower() not in extensions:
            continue
        if target_resolved == full_path or target_resolved in full_path.parents:
            files.append(full_path)

    return sorted(files)


def _iter_files_filesystem(target: Path, extensions: tuple[str, ...]) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() in extensions else []

    files: list[Path] = []
    for path in target.rglob("*"):
        if path.is_dir():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in extensions:
            files.append(path)
    return sorted(files)


def _iter_target_files(target: Path, extensions: tuple[str, ...], git_tracked_only: bool) -> list[Path]:
    if git_tracked_only:
        files = _iter_files_git_tracked(target, extensions)
        if files:
            return files
    return _iter_files_filesystem(target, extensions)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_report(target: Path, extensions: tuple[str, ...], git_tracked_only: bool) -> dict[str, object]:
    files = _iter_target_files(target, extensions, git_tracked_only)
    results = [classify_text(path, _read_text(path)) for path in files]

    counts = {name: 0 for name in CLASSIFICATIONS}
    for item in results:
        counts[item["classification"]] += 1

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "target": _relative_display_path(target),
        "extensions": list(extensions),
        "scan_mode": "git-tracked-only" if git_tracked_only else "filesystem-recursive",
        "totals": {
            "files_scanned": len(results),
            "by_classification": counts,
        },
        "results": results,
    }


def _selftest() -> int:
    kcp_sample = """
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: example.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ docs/ref.md
# ╚════════════════════════════════════════════════════════════════════════════
\"\"\"
@SID:           TOOL_EXAMPLE_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_SAMPLE
@Ankh-Tinku:    STATE_SAMPLE
@Purpose:       Sample content
\"\"\"
"""

    legacy_sample = """
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: legacy.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_LEGACY_V1
# ║ Purpose: Legacy purpose
# ║ Module: something
# ║ Exports: a, b
# ╚════════════════════════════════════════════════════════════════════════════
\"\"\"
@SID:           TOOL_LEGACY_V1
@Type:          Utility Script
\"\"\"
"""

    hybrid_sample = """
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: hybrid.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Semantic ID: TOOL_HYBRID_V1
# ╚════════════════════════════════════════════════════════════════════════════
\"\"\"
@SID:           TOOL_HYBRID_V1
@Shabti:        CLI Script
\"\"\"
"""

    none_sample = "print('hello')\n"

    kcp_result = classify_text(Path("kcp.py"), kcp_sample)
    legacy_result = classify_text(Path("legacy.py"), legacy_sample)
    hybrid_result = classify_text(Path("hybrid.py"), hybrid_sample)
    none_result = classify_text(Path("none.py"), none_sample)

    assert kcp_result["classification"] == "KCP-COMPLIANT"
    assert legacy_result["classification"] == "LEGACY"
    assert hybrid_result["classification"] == "HYBRID"
    assert none_result["classification"] == "NONE"
    assert legacy_result["dual_sid"] is True
    assert "sid" in kcp_result["detected_fields"]
    assert "purpose" in kcp_result["detected_fields"]
    assert "purpose" in hybrid_result["missing_fields"]

    print("selftest: OK")
    return 0


def _parse_extensions(raw_values: list[str]) -> tuple[str, ...]:
    normalized = []
    for item in raw_values:
        part = item.strip().lower()
        if not part:
            continue
        if not part.startswith("."):
            part = f".{part}"
        normalized.append(part)
    if not normalized:
        raise ValueError("No extensions provided.")
    return tuple(dict.fromkeys(normalized))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify source file headers as LEGACY, KCP-COMPLIANT, HYBRID, or NONE "
            "using canonical KCP regex patterns (§8)."
        )
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="File or directory to classify (default: current directory).",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=list(DEFAULT_EXTENSIONS),
        help="Extensions to include (default: .py .ts .tsx .ps1 .rs).",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write JSON report to this file path instead of stdout.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in classifier tests and exit.",
    )
    parser.add_argument(
        "--git-tracked-only",
        action="store_true",
        help="Scan only files reported by git ls-files (falls back to filesystem scan if unavailable).",
    )

    args = parser.parse_args()

    if args.selftest:
        return _selftest()

    try:
        extensions = _parse_extensions(args.extensions)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    target = Path(args.target)
    if not target.exists():
        print(f"error: target does not exist: {args.target}", file=sys.stderr)
        return 2

    report = build_report(target, extensions, args.git_tracked_only)
    payload = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
