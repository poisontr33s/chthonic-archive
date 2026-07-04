#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: models.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════


@SID:           TOOL_MODELS_V1
@Shabti:        CLI Script
@Purpose:       Signal model - pure data, no logic.
"""Signal model - pure data, no logic."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Signal:
    """A detected semantic signal at a specific location.

    This is a coordinate, not an interpretation.
    """
    artifact: str       # Relative path from repo root
    line: int          # 1-indexed line number
    signal_type: str   # Tier 1: heading-def, abbrev-def, abbrev-use, invariant-tag, crossref
    token: str | None  # The detected token (if applicable)
    context: str       # Raw line content (no paraphrase, no summary)

    def to_dict(self) -> dict:
        """Serialize for JSON output."""
        return {
            "artifact": self.artifact,
            "line": self.line,
            "signal_type": self.signal_type,
            "token": self.token,
            "context": self.context
        }
