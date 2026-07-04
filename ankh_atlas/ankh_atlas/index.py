#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ ankh_atlas/ankh_atlas/models.py
# ╚════════════════════════════════════════════════════════════════════════════


@SID:           TOOL_INDEX_V1
@Shabti:        CLI Script
@Purpose:       JSON index persistence - deterministic, git-diffable.
"""JSON index persistence - deterministic, git-diffable."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Signal


def serialize_index(
    signals: list[Signal],
    repo_root: Path,
    commit_hash: str | None = None
) -> dict[str, Any]:
    """Serialize signals to JSON-compatible dict.

    Output is deterministic (sorted) for git-diffability.
    """
    return {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit": commit_hash,
        "repo_root": str(repo_root),
        "signal_count": len(signals),
        "signals": [sig.to_dict() for sig in signals]
    }


def write_index(index_data: dict[str, Any], output_path: Path) -> None:
    """Write index to JSON file with deterministic formatting."""
    output_path.write_text(
        json.dumps(index_data, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8"
    )


def read_index(index_path: Path) -> dict[str, Any]:
    """Read index from JSON file."""
    return json.loads(index_path.read_text(encoding="utf-8"))
