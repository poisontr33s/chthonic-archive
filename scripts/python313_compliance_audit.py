#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: python313_compliance_audit.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: COMPLIANCE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Python 3.13 Compliance Audit Script

Scans repository for non-uv Python usage and Python <3.13 lane violations.
Aligned with repo policy: use `uv run python` and avoid raw `python`/`pip`.

Usage:
    uv run python scripts/python313_compliance_audit.py               # Full scan
    uv run python scripts/python313_compliance_audit.py --ci          # CI mode
    uv run python scripts/python313_compliance_audit.py --verbose     # Verbose

Exit Codes:
    0 - Compliant
    1 - Violations found (--ci mode)
    2 - Script error

@SID:           TOOL_PYTHON313_COMPLIANCE_AUDIT_V1
@Shabti:        CLI Script
@Purpose:       Python 3.13 Compliance Audit Script
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple


class Severity(Enum):
    """Violation severity levels."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Violation:
    """Represents a Python 3.13 compliance violation."""

    file: Path
    line_num: int
    line_content: str
    pattern: str
    severity: Severity
    suggestion: str
    docs_ref: str


class Python313ComplianceScanner:
    """Scans for non-uv Python usage and <3.13 lane patterns."""

    VIOLATION_PATTERNS: Dict[str, Tuple[Severity, str, str]] = {
        # Raw Python invocation
        r"\bpython(\d+(\.\d+)*)?\b": (
            Severity.CRITICAL,
            "Replace raw 'python' with 'uv run python' per repo policy.",
            "https://docs.astral.sh/uv/guides/scripts/",
        ),
        r"\bpy\b\s+-\d": (
            Severity.CRITICAL,
            "Replace 'py -<ver>' with 'uv run python'.",
            "https://docs.astral.sh/uv/guides/scripts/",
        ),
        # Pip usage
        r"\bpip(3(\.\d+)*)?\b": (
            Severity.CRITICAL,
            "Replace 'pip' with 'uv pip' or 'uv run python -m pip' as needed.",
            "https://docs.astral.sh/uv/reference/cli/#uv-pip",
        ),
        # Virtualenv direct usage
        r"\bvenv\b|\bvirtualenv\b": (
            Severity.WARNING,
            "Prefer uv-managed environments instead of venv/virtualenv.",
            "https://docs.astral.sh/uv/concepts/projects/",
        ),
        # Explicit older Python pin
        r"\bpython\s*==\s*3\.(10|11|12|13)\b": (
            Severity.WARNING,
            "Update Python pin to 3.14+ where compatible.",
            "https://docs.python.org/3.14/whatsnew/3.14.html",
        ),
    }

    EXCLUSIONS = {
        # Documentation that references old commands for historical reasons
        r"(?:DO NOT|❌|INCORRECT|WRONG|AVOID).*(?:python|pip|venv|virtualenv)",
        r"(?:previously|before|migrated from|replaced).*(?:python|pip|venv|virtualenv)",
        r"python3\.14",
        r"uv run python",
        r"uv pip",
        r"\bPython\s+3\.14\b",
        r"\brequires-python\b",
        r"\.python-version\b",
        r"\"python\"\s*:\s*\"?\d",
        r"python\.(?:analysis|lint|format|terminal|defaultInterpreterPath|languageServer)",
        r"meta\.function\.decorator\.python",
        r"entity\.name\.function\.decorator\.python",
        # This script's own patterns
        r"Replace raw 'python' with 'uv run python'",
        r"Replace 'pip' with 'uv pip'",
        # Neutral doc lists
        r"(?:python|pip|venv|virtualenv).*(?:documentation|reference|examples?)",
    }

    SKIP_PATHS = {
        "dist/",
        ".git",
        ".vscode",
        ".dcrp_state.json",
        "node_modules",
        ".venv",
        "__pycache__",
        "target",
        "build",
        ".cache",
        ".cargo",
        "logs",
        "artifacts",
        "dumpster-dive/",
        ".github/ssot_backups",
        "dependency_graph.json",
        "temp_repo_structure.json",
        "meta_cli_test.json",
        "pre_xiv_check.txt",
        "xiv_check.txt",
        "xiv_xv_check.txt",
    }

    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.violations: List[Violation] = []

    def is_excluded_line(self, line: str) -> bool:
        for pattern in self.EXCLUSIONS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def should_skip_path(self, path: Path) -> bool:
        path_str = str(path.relative_to(self.repo_root)).replace("\\", "/")
        for skip in self.SKIP_PATHS:
            if skip in path_str:
                return True
        if path.suffix in {".pyc", ".so", ".dll", ".exe", ".lock", ".sqlite"}:
            return True
        return False

    def scan_file(self, file_path: Path):
        if self.should_skip_path(file_path):
            return

        if file_path.name == "python313_compliance_audit.py":
            return

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            if self.verbose:
                safe_print(f"[WARN] Skipping {file_path}: {exc}")
            return

        for line_num, line in enumerate(content.splitlines(), start=1):
            if self.is_excluded_line(line):
                continue
            for pattern, (severity, suggestion, docs_ref) in self.VIOLATION_PATTERNS.items():
                if re.search(pattern, line):
                    self.violations.append(
                        Violation(
                            file=file_path,
                            line_num=line_num,
                            line_content=line.strip(),
                            pattern=pattern,
                            severity=severity,
                            suggestion=suggestion,
                            docs_ref=docs_ref,
                        )
                    )

    def scan(self):
        text_extensions = {
            ".md",
            ".txt",
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".ts",
            ".js",
            ".tsx",
            ".jsx",
            ".mjs",
            ".cjs",
            ".py",
            ".rs",
            ".sh",
            ".ps1",
            ".psm1",
        }

        for path in self.repo_root.rglob("*"):
            if path.is_file() and path.suffix in text_extensions:
                self.scan_file(path)

    def print_report(self):
        if not self.violations:
            safe_print("[PASS] Python 3.13 compliance: CLEAN (no violations detected)")
            return

        by_severity = {s: [] for s in Severity}
        for v in self.violations:
            by_severity[v.severity].append(v)

        total = len(self.violations)
        critical = len(by_severity[Severity.CRITICAL])
        warning = len(by_severity[Severity.WARNING])
        info = len(by_severity[Severity.INFO])

        safe_print("[FAIL] Python 3.13 compliance: VIOLATIONS DETECTED")
        safe_print(f"   Total: {total} | Critical: {critical} | Warning: {warning} | Info: {info}\n")

        max_sample = 25
        for severity in [Severity.CRITICAL, Severity.WARNING, Severity.INFO]:
            violations = by_severity[severity]
            if not violations:
                continue
            icon = "[!]" if severity == Severity.CRITICAL else "[W]" if severity == Severity.WARNING else "[i]"
            safe_print(f"{icon} {severity.value} ({len(violations)})")
            safe_print("=" * 80)
            for v in violations[:max_sample]:
                rel_path = v.file.relative_to(self.repo_root)
                safe_print(f"\nFile: {rel_path}:{v.line_num}")
                safe_print(f"   Line: {v.line_content[:100]}")
                safe_print(f"   Fix:  {v.suggestion}")
                safe_print(f"   Docs: {v.docs_ref}")
            safe_print("")
            if len(violations) > max_sample:
                safe_print(f"[i] Truncated output: {len(violations) - max_sample} more not shown")
                safe_print("")

    def get_exit_code(self) -> int:
        if not self.violations:
            return 0
        if any(v.severity == Severity.CRITICAL for v in self.violations):
            return 1
        return 0


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        safe_msg = msg.replace("→", "->").replace("✓", "[OK]").replace("✗", "[FAIL]")
        data = safe_msg.encode("utf-8", errors="replace") + b"\n"
        sys.stdout.buffer.write(data)
        sys.stdout.flush()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan repository for Python 3.13 + uv compliance violations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ci", action="store_true", help="CI mode: exit 1 on violations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    if args.verbose:
        safe_print(f"[SCAN] Checking {repo_root} for Python 3.13 compliance violations...")

    scanner = Python313ComplianceScanner(repo_root, verbose=args.verbose)
    scanner.scan()
    scanner.print_report()

    exit_code = scanner.get_exit_code()
    if args.ci and exit_code != 0:
        safe_print("\n[CI FAILURE] Critical Python compliance violations detected")
        safe_print("   Run locally to see details: uv run python scripts/python313_compliance_audit.py")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
