"""
SSOT Abbreviation Management System
====================================

A Python-based system for parsing, validating, and managing the abbreviation
conventions in the ASC Framework's Single Source of Truth (copilot-instructions.md).

This module provides:
- Pattern-based extraction of abbreviations from markdown
- Bidirectional lookup (abbrev ↔ full term)
- Consistency validation and issue detection
- Automated audit report generation

Adheres to DC-OD (Section XIV) - All Python operations via `uv run`.

Author: ASC Engine (T³-MΨ assisted)
Date: December 8, 2025
"""

from .models import (
    AbbreviationEntry,
    AuditReport,
    ConsistencyIssue,
    IssueSeverity,
    NotationPattern,
)
from .parser import SSOTParser
from .registry import AbbreviationRegistry
from .reporter import AuditReporter
from .validator import ConsistencyValidator

__version__ = "0.1.0"
__all__ = [
    "AbbreviationEntry",
    "NotationPattern",
    "ConsistencyIssue",
    "IssueSeverity",
    "AuditReport",
    "SSOTParser",
    "AbbreviationRegistry",
    "ConsistencyValidator",
    "AuditReporter",
]
