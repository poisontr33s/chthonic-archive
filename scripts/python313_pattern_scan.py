#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: python313_pattern_scan.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: COMPLIANCE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Python 3.13 Pattern Scan (Crude Estimate)

Scans repository from root and reports coarse usage patterns:
- uv run python
- raw python invocations
- pip usage
- venv/virtualenv mentions

This is a crude estimate for audit calibration, not a compliance gate.

@SID:           TOOL_PYTHON313_PATTERN_SCAN_V1
@Shabti:        CLI Script
@Purpose:       Python 3.13 Pattern Scan (Crude Estimate)
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
from pathlib import Path
from typing import Iterable


PATTERNS = {
    "uv_run_python": re.compile(r"\buv\s+run\s+python\b"),
    "raw_python": re.compile(r"\bpython(\d+(?:\.\d+)*)?\b"),
    "pip": re.compile(r"\bpip(3(?:\.\d+)*)?\b"),
    "venv": re.compile(r"\bvenv\b|\bvirtualenv\b|\.venv"),
}

CODE_EXTENSIONS = {
    ".py",
    ".ps1",
    ".psm1",
    ".ts",
    ".js",
    ".tsx",
    ".jsx",
    ".mjs",
    ".cjs",
    ".rs",
    ".sh",
    ".cmd",
    ".bat",
    ".toml",
    ".yml",
    ".yaml",
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".cache",
    ".venv",
    "__pycache__",
    "dumpster-dive",
}


@dataclass
class PatternScanResult:
    uv_run_python: int = 0
    raw_python: int = 0
    pip: int = 0
    venv: int = 0
    files_scanned: int = 0
    files_matched: int = 0


class PatternScanner:
    def __init__(self, root: Path, verbose: bool = False):
        self.root = root
        self.verbose = verbose
        self.result = PatternScanResult()
        self.samples: list[str] = []

    def _should_skip(self, path: Path) -> bool:
        parts = {p.lower() for p in path.parts}
        return any(skip in parts for skip in SKIP_DIRS)

    def _iter_files(self) -> Iterable[Path]:
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix.lower() in CODE_EXTENSIONS:
                if not self._should_skip(path):
                    yield path

    def scan(self, max_samples: int = 20):
        for file_path in self._iter_files():
            self.result.files_scanned += 1
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            matched = False
            for label, pattern in PATTERNS.items():
                count = len(pattern.findall(content))
                if count:
                    matched = True
                    setattr(self.result, label, getattr(self.result, label) + count)

            if matched:
                self.result.files_matched += 1
                if len(self.samples) < max_samples:
                    self.samples.append(str(file_path.relative_to(self.root)))

    def report(self) -> str:
        lines = [
            "Python 3.13 Pattern Scan (Crude Estimate)",
            "-" * 60,
            f"Root: {self.root}",
            f"Files scanned: {self.result.files_scanned}",
            f"Files matched: {self.result.files_matched}",
            "",
            f"uv_run_python: {self.result.uv_run_python}",
            f"raw_python:    {self.result.raw_python}",
            f"pip:           {self.result.pip}",
            f"venv:          {self.result.venv}",
            "",
            "Sample matches:",
        ]
        if self.samples:
            lines.extend([f"  - {p}" for p in self.samples])
        else:
            lines.append("  (none)")
        return "\n".join(lines)


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        data = msg.encode("utf-8", errors="replace") + b"\n"
        sys.stdout.buffer.write(data)
        sys.stdout.flush()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Crude Python 3.13 pattern scan")
    parser.add_argument("--root", type=str, default=".", help="Repo root to scan")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--max-samples", type=int, default=20, help="Max sample paths")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    scanner = PatternScanner(root, verbose=args.verbose)
    scanner.scan(max_samples=args.max_samples)
    safe_print(scanner.report())
    return 0


if __name__ == "__main__":
    sys.exit(main())
