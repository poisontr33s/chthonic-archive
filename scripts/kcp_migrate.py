#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: kcp_migrate.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ docs/standards/KCP_PROTOCOL_ONTOLOGY.md
# ╚════════════════════════════════════════════════════════════════════════════

"""
kcp_migrate.py - Lossless KCP header migration (Phase 1: .ps1 dual-SID block).

@SID:           TOOL_KCP_MIGRATE_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_KCP_MIGRATION
@Ankh-Tinku:    STATE_KCP_DUAL_SID_DEDUPED
@Purpose:       Performs ONLY the lossless slice of the KCP migration for the
                .ps1 dual-SID block. Two transforms, both reversible and value-
                preserving: (1) relabel legacy 'Spectral Frequency' to canonical
                'Wedjat-Quipu Spectrum' (identical colour value space); (2) drop
                the duplicate legacy ID line WHERE its value agrees with the
                modern @SID tag. Disagreements are FLAGGED, never auto-resolved.
                Semantic fields (Temple-Ayllu Zone, @Shabti, .NOTES restructuring)
                are deliberately out of scope - they require judgement.
                Verifier: scripts/kcp_header_classifier.py (dual_sid count drops).
"""

from __future__ import annotations


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "manifest" / "kcp_rot_queue.json"

# Box char built from codepoint so this tool never trips its own classifier.
BOX = "║"
SID_TAG = re.compile(r"@SID:\s+(\S+)")
LEGACY_ID_LINE = re.compile(rf"^.*{BOX}\s+Semantic ID:\s*(\S+).*$\n?", re.MULTILINE)
LEGACY_SPECTRUM_LABEL = "Spectral Frequency:"
CANON_SPECTRUM_LABEL = "Wedjat-Quipu Spectrum:"


def targets() -> list[Path]:
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    out: list[Path] = []
    for rel in data.get("dual_sid", []):
        if not rel.endswith(".ps1"):
            continue
        if "dumpster-dive/" in rel or "/intake/" in rel:
            continue  # quarantine stays as-is
        p = ROOT / rel
        if p.exists():
            out.append(p)
    return out


def migrate_text(text: str, relabel_spectrum: bool = False) -> tuple[str, list[str]]:
    actions: list[str] = []
    new = text

    # (1) spectrum relabel - OPT-IN. Legacy 'Spectral Frequency' is referenced by
    # canonize_blessing.py and decorator_cross_ref_*.py; relabeling is deferred
    # until those readers are confirmed label-agnostic. Not part of dual-SID.
    if relabel_spectrum and LEGACY_SPECTRUM_LABEL in new:
        new = new.replace(LEGACY_SPECTRUM_LABEL, CANON_SPECTRUM_LABEL)
        actions.append("relabel_spectrum")

    # (2) dual-SID dedup - proven safe (sid-envelope + stamp_sid read only @SID).
    # Only when modern @SID and legacy ID agree; disagreements are flagged.
    sids = set(SID_TAG.findall(new))
    legacy_vals = set(LEGACY_ID_LINE.findall(new))
    if legacy_vals:
        if sids and legacy_vals <= sids:
            new = LEGACY_ID_LINE.sub("", new)
            actions.append("dedup_sid")
        else:
            actions.append(f"FLAG_disagree(@SID={sorted(sids)} vs legacy={sorted(legacy_vals)})")

    return new, actions


def main() -> int:
    ap = argparse.ArgumentParser(description="Lossless KCP .ps1 dual-SID migration")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--relabel-spectrum", action="store_true",
                    help="ALSO relabel legacy 'Spectral Frequency' (opt-in; verify readers first)")
    args = ap.parse_args()

    files = targets()
    changed = flagged = 0
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"KCP migrate (Phase 1) - {len(files)} .ps1 dual-SID targets  [{mode}]\n")
    for p in files:
        text = p.read_text(encoding="utf-8")
        new, actions = migrate_text(text, relabel_spectrum=args.relabel_spectrum)
        if not actions:
            continue
        rel = p.relative_to(ROOT).as_posix()
        has_flag = any(a.startswith("FLAG") for a in actions)
        tag = "FLAG " if has_flag else ("would" if not args.apply else "done ")
        print(f"  [{tag}] {rel}\n           {', '.join(actions)}")
        if has_flag:
            flagged += 1
        if new != text:
            if args.apply:
                p.write_text(new, encoding="utf-8")
            changed += 1

    verb = "Changed" if args.apply else "Would change"
    print(f"\n{verb}: {changed}  |  Flagged disagreements: {flagged}  |  Scanned: {len(files)}")
    if not args.apply:
        print("Apply with: uv run scripts/kcp_migrate.py --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
