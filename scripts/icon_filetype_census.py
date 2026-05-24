#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: icon_filetype_census.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Icon Filetype Census — Discover every file extension and filename pattern
present in the workspace, cross-reference against the current icon theme
coverage, and emit a WPTG Stage/Phase sequencing plan for icon refinement.

The current Egyptological stele icons are treated as Stage 0.0 Phase 0.0
(baseline wet-paper). This script structures the path from 0.0 → gold.

@SID:           TOOL_ICON_FILETYPE_CENSUS_V1
@Shabti:          Utility
@Purpose:       Icon Filetype Census — Discover every file extension and filename pattern
"""


import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scripts.lib.shared import configure_utf8_output

# ═══════════════════════════════════════════════════════════════════════════════
# Directories to skip during filesystem walk (build artifacts, deps, VCS)
# ═══════════════════════════════════════════════════════════════════════════════
SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "target",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "dist",
    "build",
    "book",
    ".DS_Store",
    ".cache",
}

# ═══════════════════════════════════════════════════════════════════════════════
# WPTG Phase/Stage taxonomy for icon refinement
# ═══════════════════════════════════════════════════════════════════════════════
WPTG_STAGES: list[dict[str, str]] = [
    {
        "id": "0.0",
        "name": "Baseline Wet-Paper",
        "desc": "Initial Egyptological stele motifs. Archaeologically sourced. "
                "No rendering optimisation. No accessibility audit.",
    },
    {
        "id": "0.1",
        "name": "Coverage Audit",
        "desc": "Identify every file type in the workspace. Map coverage gaps. "
                "Decide which uncovered types warrant bespoke icons vs. default.",
    },
    {
        "id": "0.2",
        "name": "Gap Fill — Bespoke Motifs",
        "desc": "Design and implement Egyptological stele SVGs for high-frequency "
                "uncovered types. Each new icon must source from the archaeo vocabulary.",
    },
    {
        "id": "1.0",
        "name": "Rendering Validation",
        "desc": "Verify every SVG renders correctly at 16×16, 24×24, and 32×32. "
                "Check stroke clarity, fill legibility, and motif recognisability at small sizes.",
    },
    {
        "id": "1.1",
        "name": "WCAG / Contrast Audit",
        "desc": "Validate colour contrast ratios against WCAG 2.1 AA at minimum. "
                "Ensure motifs are distinguishable on SFS dark backgrounds (#050505, #0A0A0A).",
    },
    {
        "id": "1.2",
        "name": "Palette Coherence",
        "desc": "Cross-check SVG fill/stroke colours against the canonical SFS palette. "
                "Eliminate drift. Lock colour tokens.",
    },
    {
        "id": "2.0",
        "name": "Structural Refinement",
        "desc": "Optimise SVG path data. Remove redundant groups. Minimise file size. "
                "Run SVGO or equivalent. Ensure viewBox consistency (0 0 16 16).",
    },
    {
        "id": "2.1",
        "name": "Motif Distinctiveness",
        "desc": "Side-by-side comparison of all icons at 16px. Ensure each glyph is "
                "visually unique and file types are not confused at a glance.",
    },
    {
        "id": "3.0",
        "name": "Gold Standard",
        "desc": "Final polish. All coverage gaps filled. All SVGs pass rendering, "
                "contrast, palette, and distinctiveness gates. Ready for packaging.",
    },
]


def find_repo_root() -> Path:
    """Walk up from this script's location to find the repo root (has Cargo.toml)."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "Cargo.toml").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parent.parent


def load_icon_theme(repo: Path) -> dict:
    """Load chthonic-file-icon-theme.json and return parsed dict."""
    theme_path = repo / "extensions" / "chthonic-archive" / "themes" / "chthonic-file-icon-theme.json"
    with open(theme_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_coverage(theme: dict) -> tuple[set[str], set[str], set[str]]:
    """
    Extract the sets of covered extensions, filenames, and language IDs
    from the icon theme JSON.

    Returns:
        (covered_extensions, covered_filenames, covered_language_ids)
    """
    ext_set = set(theme.get("fileExtensions", {}).keys())
    name_set = set(theme.get("fileNames", {}).keys())
    lang_set = set(theme.get("languageIds", {}).keys())
    return ext_set, name_set, lang_set


def walk_repo(repo: Path) -> tuple[Counter, Counter, int]:
    """
    Walk the repo tree collecting file extension counts and filename counts.

    Returns:
        (extension_counter, filename_counter, total_files)
    """
    ext_counter: Counter = Counter()
    name_counter: Counter = Counter()
    total = 0

    for dirpath, dirnames, filenames in os.walk(repo):
        # Prune skipped directories in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            total += 1
            name_counter[fname] += 1

            # Extract extension (without leading dot, lowercased)
            _, ext = os.path.splitext(fname)
            if ext:
                ext_lower = ext[1:].lower()  # strip the dot
                ext_counter[ext_lower] += 1
            else:
                ext_counter["(no extension)"] += 1

    return ext_counter, name_counter, total


def classify_extensions(
    ext_counts: Counter,
    covered_exts: set[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Split extensions into covered (have icon mapping) and uncovered (use default).

    Returns:
        (covered_dict, uncovered_dict) — each maps ext → count, sorted by count desc.
    """
    covered: dict[str, int] = {}
    uncovered: dict[str, int] = {}

    for ext, count in ext_counts.most_common():
        if ext in covered_exts:
            covered[ext] = count
        else:
            uncovered[ext] = count

    return covered, uncovered


def classify_filenames(
    name_counts: Counter,
    covered_names: set[str],
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Split filenames into covered (have icon mapping) and uncovered.
    """
    covered: dict[str, int] = {}
    uncovered: dict[str, int] = {}

    for name, count in name_counts.most_common():
        if name in covered_names:
            covered[name] = count
        else:
            uncovered[name] = count

    return covered, uncovered


def build_phase_plan(
    uncovered_exts: dict[str, int],
    uncovered_names: dict[str, int],
    covered_exts: dict[str, int],
    covered_names: dict[str, int],
) -> list[dict]:
    """
    Build the WPTG phase/stage plan with census data embedded.
    """
    plan = []
    for stage in WPTG_STAGES:
        entry = {
            "stage": stage["id"],
            "name": stage["name"],
            "description": stage["desc"],
        }
        # Stage 0.0 — embed current coverage summary
        if stage["id"] == "0.0":
            entry["coverage"] = {
                "covered_extensions": len(covered_exts),
                "uncovered_extensions": len(uncovered_exts),
                "covered_filenames": len(covered_names),
            }
        # Stage 0.1 — embed the actual gap data
        if stage["id"] == "0.1":
            # Sort uncovered by frequency (already sorted via Counter)
            entry["uncovered_extensions"] = uncovered_exts
            entry["uncovered_filenames"] = {
                k: v for k, v in uncovered_names.items()
                if v >= 2  # only surface filenames with 2+ occurrences
            }
        # Stage 0.2 — surface high-frequency gaps as candidates
        if stage["id"] == "0.2":
            # Top-N uncovered by frequency — candidates for bespoke icons
            candidates = {
                ext: count
                for ext, count in uncovered_exts.items()
                if count >= 3 and ext != "(no extension)"
            }
            entry["bespoke_candidates"] = candidates
            entry["candidate_count"] = len(candidates)

        plan.append(entry)

    return plan


def print_report(
    ext_counts: Counter,
    name_counts: Counter,
    total_files: int,
    covered_exts: dict[str, int],
    uncovered_exts: dict[str, int],
    covered_names: dict[str, int],
    uncovered_names: dict[str, int],
    plan: list[dict],
    output_json: Path | None,
) -> None:
    """Print the census report to stdout."""

    print("=" * 72)
    print(" ☥ ICON FILETYPE CENSUS — WPTG Stage 0.0 → 0.1 Bridge")
    print("=" * 72)
    print()
    print(f"  Total files scanned:      {total_files:,}")
    print(f"  Unique extensions:         {len(ext_counts):,}")
    print(f"  Unique filenames:          {len(name_counts):,}")
    print()

    # ── Coverage Summary ─────────────────────────────────────────────────
    total_ext = len(ext_counts)
    n_covered = len(covered_exts)
    n_uncovered = len(uncovered_exts)
    pct = (n_covered / total_ext * 100) if total_ext else 0
    print("─" * 72)
    print(f" EXTENSION COVERAGE: {n_covered}/{total_ext}  ({pct:.1f}%)")
    print("─" * 72)
    print()

    # ── Covered Extensions ───────────────────────────────────────────────
    print("  ✅ COVERED EXTENSIONS (have bespoke icon):")
    for ext, count in sorted(covered_exts.items(), key=lambda x: -x[1]):
        print(f"     .{ext:<12s}  {count:>6,} files")
    print()

    # ── Uncovered Extensions ─────────────────────────────────────────────
    print("  ❌ UNCOVERED EXTENSIONS (fall back to default):")
    for ext, count in sorted(uncovered_exts.items(), key=lambda x: -x[1]):
        label = ext if ext != "(no extension)" else "(no ext)"
        print(f"     .{label:<12s}  {count:>6,} files")
    print()

    # ── Covered Filenames ────────────────────────────────────────────────
    print("  ✅ COVERED FILENAMES (have bespoke icon):")
    for name, count in sorted(covered_names.items(), key=lambda x: -x[1]):
        print(f"     {name:<28s}  {count:>4} occurrences")
    print()

    # ── High-Frequency Uncovered Filenames ───────────────────────────────
    hi_freq = {k: v for k, v in uncovered_names.items() if v >= 2}
    if hi_freq:
        print("  ❌ UNCOVERED FILENAMES (2+ occurrences):")
        for name, count in sorted(hi_freq.items(), key=lambda x: -x[1]):
            print(f"     {name:<28s}  {count:>4} occurrences")
        print()

    # ── WPTG Phase/Stage Plan ────────────────────────────────────────────
    print("═" * 72)
    print(" WPTG PHASE/STAGE PLAN — Icon Refinement Sequence")
    print("═" * 72)
    print()
    for stage in plan:
        sid = stage["stage"]
        name = stage["name"]
        desc = stage["description"]
        marker = "◆" if sid == "0.0" else "◇"
        print(f"  {marker} Stage {sid} — {name}")
        print(f"    {desc}")

        if "coverage" in stage:
            c = stage["coverage"]
            print(f"    ├─ Covered extensions:   {c['covered_extensions']}")
            print(f"    ├─ Uncovered extensions: {c['uncovered_extensions']}")
            print(f"    └─ Covered filenames:    {c['covered_filenames']}")

        if "uncovered_extensions" in stage:
            ue = stage["uncovered_extensions"]
            print(f"    └─ {len(ue)} uncovered extension(s) to evaluate")

        if "bespoke_candidates" in stage:
            bc = stage["bespoke_candidates"]
            print(f"    └─ {stage['candidate_count']} bespoke candidate(s) (≥3 files):")
            for ext, cnt in sorted(bc.items(), key=lambda x: -x[1]):
                print(f"       .{ext:<10s}  ({cnt:,} files)")

        print()

    # ── JSON output ──────────────────────────────────────────────────────
    if output_json:
        report = {
            "census": {
                "total_files": total_files,
                "unique_extensions": len(ext_counts),
                "unique_filenames": len(name_counts),
            },
            "covered_extensions": covered_exts,
            "uncovered_extensions": uncovered_exts,
            "covered_filenames": covered_names,
            "uncovered_filenames_hi_freq": hi_freq,
            "wptg_plan": plan,
        }
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  ✏️  JSON report written to: {output_json}")
        print()


def main() -> None:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Icon Filetype Census — discover all file types and plan icon refinement."
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Write structured JSON report to this path.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root (auto-detected if omitted).",
    )
    args = parser.parse_args()

    repo = args.repo or find_repo_root()

    # Load icon theme and extract coverage
    theme = load_icon_theme(repo)
    cov_exts, cov_names, cov_langs = extract_coverage(theme)

    # Walk the repo
    ext_counts, name_counts, total_files = walk_repo(repo)

    # Classify
    covered_exts, uncovered_exts = classify_extensions(ext_counts, cov_exts)
    covered_names, uncovered_names = classify_filenames(name_counts, cov_names)

    # Build WPTG plan
    plan = build_phase_plan(uncovered_exts, uncovered_names, covered_exts, covered_names)

    # Print report
    print_report(
        ext_counts,
        name_counts,
        total_files,
        covered_exts,
        uncovered_exts,
        covered_names,
        uncovered_names,
        plan,
        args.json,
    )


if __name__ == "__main__":
    main()
