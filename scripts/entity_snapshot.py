#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: entity_snapshot.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Dump chthonic entity registry to JSON on stdout.
Used by milfological_dashboard.ts at startup.

Usage:
    uv run scripts/entity_snapshot.py

@SID:           ENTITY_SNAPSHOT_PY
@Shabti:        CLI Script
@Purpose:       Dump chthonic entity registry to JSON on stdout.
"""

# @SID: ENTITY_SNAPSHOT_PY
import sys
import json
import re
from pathlib import Path

SDNEXT_EXT = Path(__file__).parent.parent / "dev" / "sd-candidates" / "sdnext" / "extensions" / "milfological"
sys.path.insert(0, str(SDNEXT_EXT))

try:
    from entity_registry import registry  # type: ignore[import]
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)

_WHR_RE = re.compile(r"WHR\s+(\d+\.\d+)")

out = []
for e in registry.all():
    whr: float | None = None
    for desc in e.visual_descriptors:
        m = _WHR_RE.search(desc)
        if m:
            whr = float(m.group(1))
            break
    out.append({
        "entity_id": e.entity_id,
        "display_name": e.display_name,
        "tier": e.tier,
        "organ": e.organ,
        "prism": e.prism,
        "district": e.district,
        "whr": whr,
        "visual_descriptor_count": len(e.visual_descriptors),
        "aesthetic_tag_count": len(e.aesthetic_tags),
        "aesthetic_tags": e.aesthetic_tags[:6],
        "color_palette": e.color_palette[:4],
        "positive_prefix": e.positive_prefix[:120],
        "negative_suffix": getattr(e, "negative_suffix", "")[:120],
        "default_weight": e.default_weight,
    })

print(json.dumps(out))
