#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: detectors.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ ankh_atlas/ankh_atlas/models.py
# ╚════════════════════════════════════════════════════════════════════════════

"""Tier 1 detectors - structurally unambiguous patterns only.

Each detector:
- Takes (line, line_no, path)
- Returns Signal | None
- Has zero state
- Detects structure, not meaning

@SID:           TOOL_DETECTORS_V1
@Shabti:        CLI Script
@Purpose:       Tier 1 detectors - structurally unambiguous patterns only.
"""

import re
from pathlib import Path
from .models import Signal


def detect_heading(line: str, line_no: int, path: Path) -> Signal | None:
    """Detect Markdown headings (lines starting with #)."""
    if line.startswith("#"):
        # Extract heading text without leading # and whitespace
        heading_text = line.lstrip("#").strip()
        return Signal(
            artifact=str(path),
            line=line_no,
            signal_type="heading-def",
            token=None,  # Headings don't need token extraction
            context=line.strip()
        )
    return None


def detect_abbrev_def(line: str, line_no: int, path: Path, known_abbrevs: set[str]) -> Signal | None:
    """Detect first use of (ABBREV) or `ABBREV` patterns.

    Abbreviations are:
    - All caps (A-Z), numbers (0-9), hyphens, underscores
    - Minimum 2 characters
    - In parens () or backticks ``
    """
    # Pattern: (CAPS-ABBREV) or `CAPS-ABBREV`
    patterns = [
        r'\(([A-Z0-9_-]{2,})\)',           # (ABBREV)
        r'`([A-Z0-9_-]{2,})`',             # `ABBREV`
        r'\(\`([A-Z0-9_-]{2,})\`\)',       # (`ABBREV`)
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, line):
            token = match.group(1)
            if token not in known_abbrevs:
                known_abbrevs.add(token)
                return Signal(
                    artifact=str(path),
                    line=line_no,
                    signal_type="abbrev-def",
                    token=token,
                    context=line.strip()
                )
    return None


def detect_abbrev_use(line: str, line_no: int, path: Path, known_abbrevs: set[str]) -> list[Signal]:
    """Detect subsequent uses of known abbreviations.

    Returns list because one line may contain multiple uses.
    """
    signals = []
    patterns = [
        r'\(([A-Z0-9_-]{2,})\)',
        r'`([A-Z0-9_-]{2,})`',
        r'\(\`([A-Z0-9_-]{2,})\`\)',
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, line):
            token = match.group(1)
            if token in known_abbrevs:
                signals.append(Signal(
                    artifact=str(path),
                    line=line_no,
                    signal_type="abbrev-use",
                    token=token,
                    context=line.strip()
                ))
    return signals


def detect_invariant_tag(line: str, line_no: int, path: Path) -> list[Signal]:
    """Detect invariant tags like (FA⁴), (SSOT-L-H), (ET-S).

    Pattern: Parenthetical with caps, numbers, hyphens, underscores.
    Includes special chars like ⁴ for superscripts.

    Returns list because one line may contain multiple invariants.
    """
    signals = []
    # More permissive pattern for invariant tags (allows Unicode superscripts, etc.)
    # Matches (FA⁴), (SSOT-L-H), (ET-S), etc.
    pattern = r'\(([A-Z0-9_\-⁰¹²³⁴⁵⁶⁷⁸⁹]+)\)'

    for match in re.finditer(pattern, line):
        token = match.group(1)
        # Filter out common false positives
        if len(token) >= 2:  # Minimum 2 chars
            signals.append(Signal(
                artifact=str(path),
                line=line_no,
                signal_type="invariant-tag",
                token=token,
                context=line.strip()
            ))
    return signals


def detect_crossref(line: str, line_no: int, path: Path) -> list[Signal]:
    """Detect cross-references: Section X, See §Y, (Prt.Z).

    Patterns:
    - "Section X.Y.Z" or "Section X"
    - "See Section X"
    - "§X.Y" or "§X"
    - "(Prt.X)" or "(Section X)"

    Returns list because one line may contain multiple crossrefs.
    """
    signals = []

    patterns = [
        (r'Section\s+([IVX\d]+(?:\.\d+)*)', 'section-ref'),
        (r'See\s+Section\s+([IVX\d]+(?:\.\d+)*)', 'section-ref'),
        (r'§([IVX\d]+(?:\.\d+)*)', 'section-ref'),
        (r'\(Prt\.([IVX\d]+(?:\.\d+)*)\)', 'protocol-ref'),
        (r'\(Section\s+([IVX\d]+(?:\.\d+)*)\)', 'section-ref'),
    ]

    for pattern, ref_type in patterns:
        for match in re.finditer(pattern, line):
            token = match.group(1)
            signals.append(Signal(
                artifact=str(path),
                line=line_no,
                signal_type=f"crossref-{ref_type}",
                token=token,
                context=line.strip()
            ))
    return signals


# Detector registry - order matters for abbrev tracking
TIER_1_DETECTORS = [
    detect_heading,
    detect_invariant_tag,
    detect_crossref,
    # abbrev detectors handled separately due to state requirements
]
