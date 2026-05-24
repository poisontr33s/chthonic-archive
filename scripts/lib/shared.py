#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: shared.py
# ║ Python module: find_repo_root, configure_utf8_output, setup_logging, add_common_args, add_output_arg, ChthonicConfig...
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: WHITE
# ║ Architectural Role: 🌿 THE GARDEN
# ║ Semantic ID: LIB_CHTHONIC_SHARED_UTILS
# ║ Purpose: shared.py - Common utilities for chthonic CLI tools
# ║ Exports: find_repo_root, configure_utf8_output, setup_logging, add_common_arg
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║ Dependencies (I rely on):
# ║  ├─► scripts/lib/analyze.py
# ║  ├─► scripts/lib/audit.py
# ║  ├─► scripts/lib/compact.py
# ║  ├─► scripts/lib/extract.py
# ║  ├─► scripts/lib/map.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
shared.py - Common utilities for chthonic CLI tools

@SID:           LIB_CHTHONIC_SHARED_UTILS
@Type:          Library Module
@Context:       Infrastructure / Shared Utilities
@SessionOrigin: CONTINUATION_2026_01_27
@Implements:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27

Provides common functionality to eliminate duplication across CLI tools:
- UTF-8 stdout configuration
- Standard argparse patterns
- Consistent logging setup
- Config file loading
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = [
    "find_repo_root",
    "configure_utf8_output",
    "setup_logging",
    "add_common_args",
    "add_output_arg",
    "ChthonicConfig",
]

# =============================================================================
# Repository Root Detection
# =============================================================================

def find_repo_root(start_path: Path | None = None) -> Path:
    """
    Find repository root by looking for markers (.git, Cargo.toml, etc.).

    Walks up from start_path (or CWD) until finding a repo marker.
    Falls back to CWD if no marker found.
    """
    current = Path(start_path or os.getcwd()).resolve()

    # Repo markers (in priority order)
    markers = [".git", "Cargo.toml", "package.json", "pyproject.toml"]

    parents_to_check = ([current] + list(current.parents))[:10]
    for parent in parents_to_check:
        for marker in markers:
            if (parent / marker).exists():
                return parent

    # Fallback to CWD if no marker found (or traversal limit reached)
    return Path.cwd()


# =============================================================================
# UTF-8 Configuration
# =============================================================================

def configure_utf8_output():
    """
    Configure stdout/stderr for UTF-8 encoding on Windows.

    Prevents UnicodeEncodeError on cp1252 console.
    Safe to call multiple times.
    """
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    Configure consistent logging across all tools.

    Args:
        verbose: Enable DEBUG level logging
        quiet: Suppress INFO/DEBUG, show only WARNING+
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    level = logging.WARNING if quiet else (logging.DEBUG if verbose else logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]

    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        handlers=handlers,
        force=True,
    )

    return logging.getLogger("chthonic")


# =============================================================================
# Common Argparse Patterns
# =============================================================================

def add_common_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add standard flags to an argparse parser.

    Adds:
        --verbose: Enable debug logging
        --quiet: Suppress info/debug output
        --json: Output as JSON
        --dry-run: Preview without making changes

    Returns:
        Modified parser (for chaining)
    """
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress info/debug output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing"
    )
    return parser


def add_output_arg(parser: argparse.ArgumentParser, help_text: str = "Output file path") -> argparse.ArgumentParser:
    """Add standard --output/-o argument."""
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help=help_text
    )
    return parser


# =============================================================================
# Config File Support
# =============================================================================

@dataclass
class ChthonicConfig:
    """Runtime configuration loaded from .chthonic.toml or defaults."""
    verbose: bool = False
    quiet: bool = False
    root_dir: Path = Path.cwd()
    sid_index_path: Path = Path("data/indices/sid_index.json")

    @classmethod
    def load(cls, config_file: Path | None = None) -> ChthonicConfig:
        """
        Load config from TOML file.

        Search order:
        1. Explicit config_file argument
        2. .chthonic.toml in current directory
        3. .chthonic.toml in repo root (git rev-parse --show-toplevel)
        4. Defaults
        """
        if config_file and config_file.exists():
            return cls._load_toml(config_file)

        # Try current directory
        local_config = Path.cwd() / ".chthonic.toml"
        if local_config.exists():
            return cls._load_toml(local_config)

        # Try repo root (if in git repo)
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            repo_root = Path(result.stdout.strip()) / ".chthonic.toml"
            if repo_root.exists():
                return cls._load_toml(repo_root)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Return defaults
        return cls()

    @classmethod
    def _load_toml(cls, path: Path) -> ChthonicConfig:
        """Load config from TOML file."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # Fallback for Python 3.10
            except ImportError:
                logging.warning(f"TOML support requires tomllib (3.11+) or tomli. Using defaults.")
                return cls()

        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls(
            verbose=data.get("verbose", False),
            quiet=data.get("quiet", False),
            root_dir=Path(data.get("root_dir", Path.cwd())),
            sid_index_path=Path(data.get("sid_index_path", "data/indices/sid_index.json")),
        )


# =============================================================================
# Output Helpers
# =============================================================================

def print_json(data: Any, indent: int = 2):
    """Print data as formatted JSON with UTF-8 support."""
    configure_utf8_output()
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def print_table(rows: list[list[str]], headers: list[str] | None = None):
    """Print simple aligned table."""
    configure_utf8_output()

    if headers:
        rows = [headers] + rows

    # Calculate column widths
    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]

    for i, row in enumerate(rows):
        print("  ".join(str(cell).ljust(widths[j]) for j, cell in enumerate(row)))
        if i == 0 and headers:
            print("  ".join("-" * widths[j] for j in range(len(row))))


# =============================================================================
# Error Handling
# =============================================================================

class ChthonicError(Exception):
    """Base exception for chthonic CLI tools."""
    pass


class ConfigError(ChthonicError):
    """Configuration-related errors."""
    pass


class ValidationError(ChthonicError):
    """Input validation errors."""
    pass


def handle_errors(func):
    """
    Decorator for main() functions to handle errors gracefully.

    Usage:
        @handle_errors
        def main():
            ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ChthonicError as e:
            logging.error(f"{e.__class__.__name__}: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logging.info("Interrupted by user")
            sys.exit(130)
        except Exception as e:
            logging.exception(f"Unexpected error: {e}")
            sys.exit(1)
    return wrapper
