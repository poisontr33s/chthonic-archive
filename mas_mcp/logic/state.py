#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: state.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""Compatibility layer for legacy logic.state imports.

The newer code split PatternRegistry into LexiconFilter and the persistence
layer into ArchiveVault. Keep the old names available so older tests and
callers continue to work during the migration.

@SID:           TOOL_STATE_V1
@Shabti:        CLI Script
@Purpose:       Compatibility layer for legacy logic.state imports.
"""

from __future__ import annotations

from pathlib import Path

from .resonance import ArchiveVault, LexiconFilter


class PatternRegistry(LexiconFilter):
    """Legacy alias for the current lexicon filter."""

    def get_all_patterns(self):
        return self.get_all_filters()


class MemoryBank(ArchiveVault):
    """Legacy alias with the historical truth-recording API."""

    def __init__(self, path: Path):
        super().__init__(path)

    def record_truth(self, entity: str, truth: dict) -> None:
        self.seal_truth(entity, truth)

    def get_known_truth(self, entity: str) -> dict | None:
        return self.get_canonical_truth(entity)
