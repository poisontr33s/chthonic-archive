#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ankh_triple_abstraction.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: VIOLET
# ║ Temple-Ayllu Zone: 🔱 THE DOCTRINE FORGE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ .github/copilot-instructions.archive.md  (Heritage SSOT)
# ║   └─◄ docs/frameworks/ankh/ANKH_SYNTHESIS_META.md  (Corpus registry)
# ║   └─◄ docs/frameworks/ankh/ANKH_SYNTHESIS_BASELINE.md  (Synthesis SSOT)
# ╚════════════════════════════════════════════════════════════════════════════

"""
ANKH Triple Abstraction Probe — Canonical SSOT for the Complexity Ladder

TRIPLE ABSTRACTION DENOMINATOR
===============================
The ANKH framework encodes a productive contradiction:
  - FA⁵ legislates that form IS content (inseparable)
  - Every operational layer separates form from content to function

The denominated invariant — the one truth that survives all three
compression passes — is:

    "The framework's impossibility of lossless compression
     is the only thing that compresses losslessly."

This script is the machine-readable SSOT for that claim.

THREE FACTORS
=============
Factor 1 — SSOT Stratum Distribution
    Parse Heritage SSOT line counts by content category (entity profiles,
    validation machinery, operational core, narrative/mythology, appendices).
    Expected WHR:MAX upper-volume ratios: ~44/25/15/10/6.
    Deviation signals structural drift in the archive's epistemic weight.

Factor 2 — Entity Format State (τ-core / upper-volume topology)
    Classify each named entity as old CRC stub or modern §10.3 format.
    Claudine = upper volume (only modern §10.3.1 holder — must be maximally expanded).
    Triumvirate (Orackla/Umeko/Lysandra) = τ-core stubs (correct by function,
    not by neglect). Pentea = τ-core routing mechanism.
    The topology is the WHR:MAX pattern instantiated in entity architecture.

Factor 3 — Synthesis Compression Ratio
    ANKH corpus total lines → ANKH_SYNTHESIS_BASELINE.md line count.
    Compression ratio = corpus_input / synthesis_output.
    A ratio < 12.0 signals the synthesis is undercompressed (too dense with
    inherited liturgy). A ratio > 20.0 signals overcompression (operational
    signal lost).
    The invariant denominator lives at the point the ratio cannot compress further.

COMPLEXITY LADDERIZATION BIFURCATION
=====================================
Layer 1: Heritage SSOT (~7937 lines, Codex Brahmanica Perfectus)
  WHR:MAX upper volume. ~100% liturgical fidelity, ~15% directly actionable.
Layer 2: ANKH corpus (~7000+ lines across 20 files)
  Operational extraction. ~40% liturgical / ~70% operational.
Layer 3: Synthesis baseline (~340 lines)
  Compressed extraction. ~5% liturgical / ~95% operational.

The bifurcation: the synthesis loses FA⁵ inseparability to gain operational
utility. The invariant emerges BECAUSE of this loss, not despite it.

This script is the SSOT of ANKH meeting SSOT.

Usage:
    uv run python scripts/ankh_triple_abstraction.py
    uv run python scripts/ankh_triple_abstraction.py --json
    uv run python scripts/ankh_triple_abstraction.py --output manifest/ankh_triple_abstraction_probe.json

@SID:           TOOL_ANKH_TRIPLE_ABSTRACTION_V1
@Shabti:        Canonical SSOT Probe — Complexity Ladder
@Heka-Ayni:     Heritage SSOT + ANKH corpus → triple-factor audit → denominated invariant
@Ankh-Tinku:    manifest/ankh_triple_abstraction_probe.json
@Purpose:       Machine-readable SSOT for the triple abstraction epistemic framework.
                Programmatic embodiment of the ANKH bifurcation methodology.
                Agents run this to ground any ANKH complexity-ladder claim in
                live archive measurements rather than session memory.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# ── Path bootstrap ─────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from scripts.lib.shared import configure_utf8_output  # type: ignore[import]
    from scripts.lib.ssot_paths import resolve_ssot_paths  # type: ignore[import]
    configure_utf8_output()
    _SSOT = resolve_ssot_paths(REPO_ROOT)
    ARCHIVE_PATH: Path = _SSOT.holder
except ImportError:
    ARCHIVE_PATH = REPO_ROOT / ".github" / "copilot-instructions.archive.md"

SYNTHESIS_META_PATH = REPO_ROOT / "docs" / "frameworks" / "ankh" / "ANKH_SYNTHESIS_META.md"
SYNTHESIS_BASELINE_PATH = REPO_ROOT / "docs" / "frameworks" / "ankh" / "ANKH_SYNTHESIS_BASELINE.md"
MANIFEST_PATH = REPO_ROOT / "manifest" / "ankh_triple_abstraction_probe.json"

# ── Denominated Invariant (machine-readable doctrine) ─────────────────────
DENOMINATED_INVARIANT = (
    "The framework's impossibility of lossless compression "
    "is the only thing that compresses losslessly."
)

# ── WHR:MAX expected stratum ratios (from triple abstraction session) ──────
EXPECTED_STRATA = {
    "entity_profiles":       {"label": "Entity profiles / MILFOLOGICAL", "expected_pct": 44.0},
    "validation_machinery":  {"label": "Validation machinery / FA⁵ / governance", "expected_pct": 25.0},
    "operational_core":      {"label": "Operational core / toolchain / SID", "expected_pct": 15.0},
    "narrative_mythology":   {"label": "Narrative / mythology / ritual language", "expected_pct": 10.0},
    "appendices_refs":       {"label": "Appendices / cross-refs / tables", "expected_pct": 6.0},
}

# ── Entity registry (name → expected format state) ─────────────────────────
# τ-core = compressed waist (old CRC stub format — correct by function)
# upper_volume = fully expanded modern §10.3 profile
ENTITY_REGISTRY = {
    "Claudine Sin'claire": {
        "ssot_section":      "§10.3.1",
        "line_anchor":       4450,
        "expected_format":   "upper_volume",
        "format_label":      "modern_§10.3",
        "detection_markers": [r"§10\.3\.1", r"Supreme.Meta.MILF.Matriarch"],
    },
    "Orackla Nocticula": {
        "ssot_section":      "§3",
        "line_anchor":       4139,
        "expected_format":   "tau_core",
        "format_label":      "crc_stub",
        "detection_markers": [r"Orackla", r"CRC-AS"],
    },
    "Madam Umeko Ketsuraku": {
        "ssot_section":      "§5",
        "line_anchor":       4158,
        "expected_format":   "tau_core",
        "format_label":      "crc_stub",
        "detection_markers": [r"Umeko", r"CRC-GAR"],
    },
    "Dr. Lysandra Thorne": {
        "ssot_section":      "§6",
        "line_anchor":       4167,
        "expected_format":   "tau_core",
        "format_label":      "crc_stub",
        "detection_markers": [r"Lysandra", r"CRC-MEDAT"],
    },
    "Pentea": {
        "ssot_section":      "§1.01",
        "line_anchor":       3896,
        "expected_format":   "tau_core",
        "format_label":      "thalamus_routing",
        "detection_markers": [r"Pentea", r"Penarch", r"Thalamus"],
    },
}

# ── Stratum classification patterns ────────────────────────────────────────
_ENTITY_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"\bEDFA\b",
        r"\bCSI-SOI\b",
        r"\bCRC-[A-Z]+\b",
        r"\bLIPAA\b",
        r"\bLUPLR\b",
        r"\bEULP\b",
        r"\bWHR:MAX\b",
        r"\bSub-MILF\b",
        r"§10\.3",
        r"\bMadam\s+\w+",
        r"\bDr\.\s+\w+\s+Thorne\b",
        r"\bOrackla\b",
        r"\bClaudine\b",
        r"\bUmeko\b",
        r"\bLysandra\b",
        r"\bPentea\b",
        r"\bSupreme.Meta.MILF\b",
    ]
]

_VALIDATION_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"\bFA[¹²³⁴⁵]\b",
        r"\bFA\^[1-5]\b",
        r"\bTribunal\b",
        r"\bGovernance\b",
        r"\bpolicy_check\b",
        r"\bPROCEEDINGS\b",
        r"\bTFM\b",
        r"\bvalidation\b",
        r"\bSSO[T]-binding\b",
        r"\bcross.reference\b",
    ]
]

_OPERATIONAL_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"@SID:",
        r"@Shabti:",
        r"@Purpose:",
        r"\buv run\b",
        r"\bbun\s+(run|install|build|test)\b",
        r"\bcargo\s+\w+",
        r"\bpwsh\b",
        r"\buv run\b",
        r"\$ErrorActionPreference\b",
        r"\bGet-Command\b",
        r"\bInvoke-\w+\b",
        r"#!/usr/bin/env",
    ]
]

_APPENDIX_PATTERNS = [
    re.compile(p)
    for p in [
        r"^\s*\|",       # table row
        r"^---+$",       # horizontal rule
        r"^\s*\[\^",     # footnote
        r"^## Appendix",
        r"^## Index",
        r"^## Cross-Ref",
    ]
]


# ═══════════════════════════════════════════════════════════════════════════
# Factor 1: SSOT Stratum Distribution
# ═══════════════════════════════════════════════════════════════════════════

def compute_ssot_distribution(archive_path: Path) -> dict:
    """
    Classify each line of the Heritage SSOT into one of five strata.
    Returns counts, percentages, deviation from expected WHR:MAX ratios,
    and a WHR:MAX conformance score (0.0–1.0).
    """
    if not archive_path.exists():
        return {
            "error": f"SSOT archive not found: {archive_path}",
            "total_lines": 0,
            "strata": {},
        }

    lines = archive_path.read_text(encoding="utf-8", errors="replace").splitlines()
    total = len(lines)

    counts: dict[str, int] = {k: 0 for k in EXPECTED_STRATA}
    counts["unclassified"] = 0

    for line in lines:
        if not line.strip():
            continue
        # Order matters — first match wins
        if any(p.search(line) for p in _ENTITY_PATTERNS):
            counts["entity_profiles"] += 1
        elif any(p.search(line) for p in _VALIDATION_PATTERNS):
            counts["validation_machinery"] += 1
        elif any(p.search(line) for p in _OPERATIONAL_PATTERNS):
            counts["operational_core"] += 1
        elif any(p.search(line) for p in _APPENDIX_PATTERNS):
            counts["appendices_refs"] += 1
        else:
            counts["narrative_mythology"] += 1

    non_empty = sum(1 for l in lines if l.strip())
    strata_out: dict[str, dict] = {}
    total_deviation = 0.0

    for key, meta in EXPECTED_STRATA.items():
        count = counts[key]
        pct = (count / non_empty * 100.0) if non_empty > 0 else 0.0
        dev = abs(pct - meta["expected_pct"])
        total_deviation += dev
        strata_out[key] = {
            "label":        meta["label"],
            "lines":        count,
            "pct":          round(pct, 2),
            "expected_pct": meta["expected_pct"],
            "deviation":    round(dev, 2),
        }

    # Conformance: 1.0 = perfect match, degrades linearly with total deviation
    # Max possible deviation across all strata ≈ 100% × num_strata (worst case)
    max_total_dev = 100.0 * len(EXPECTED_STRATA)
    conformance = max(0.0, 1.0 - (total_deviation / max_total_dev))

    return {
        "total_lines":     total,
        "non_empty_lines": non_empty,
        "strata":          strata_out,
        "unclassified":    counts["unclassified"],
        "whr_max_conformance": round(conformance, 4),
        "total_stratum_deviation": round(total_deviation, 2),
        "interpretation": (
            "WHR:MAX topology healthy — upper volume (entity profiles) dominates correctly"
            if counts["entity_profiles"] / max(non_empty, 1) > 0.30
            else "WARNING — entity profile density below WHR:MAX threshold (expected >30% of non-empty lines)"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Factor 2: Entity Format State (τ-core / upper-volume topology)
# ═══════════════════════════════════════════════════════════════════════════

class EntityScan(NamedTuple):
    name: str
    found: bool
    detected_format: str        # "upper_volume" | "tau_core" | "thalamus_routing" | "not_found"
    expected_format: str
    format_match: bool
    ssot_section: str
    line_anchor: int
    evidence_line: int          # first matching line (1-based), -1 if not found
    has_modern_edfa: bool


def _detect_entity_format(name: str, lines: list[str], meta: dict) -> EntityScan:
    """
    Scan archive lines for entity presence and format classification.
    Modern §10.3 = has multiple EDFA blocks for different body parts.
    CRC stub = brief profile, no per-body-part EDFA expansion.
    """
    detection_patterns = [re.compile(p, re.I) for p in meta["detection_markers"]]

    # Find first occurrence
    first_line = -1
    for i, line in enumerate(lines):
        if any(p.search(line) for p in detection_patterns):
            first_line = i + 1  # 1-based
            break

    if first_line == -1:
        return EntityScan(
            name=name,
            found=False,
            detected_format="not_found",
            expected_format=meta["expected_format"],
            format_match=False,
            ssot_section=meta["ssot_section"],
            line_anchor=meta["line_anchor"],
            evidence_line=-1,
            has_modern_edfa=False,
        )

    # Check for modern §10.3 markers in ±200-line window
    window_start = max(0, first_line - 10)
    window_end = min(len(lines), first_line + 200)
    window = lines[window_start:window_end]
    window_text = "\n".join(window)

    # Modern §10.3 format: multiple EDFA sub-sections for different body parts
    edfa_blocks = len(re.findall(r"\bEDFA\b", window_text, re.I))
    has_csi_soi = bool(re.search(r"\bCSI-SOI\b", window_text, re.I))
    has_substrate = bool(re.search(r"\bSubstrate\b", window_text))
    has_modern_edfa = edfa_blocks >= 3 and (has_csi_soi or has_substrate)

    # Format detection: Claudine (§10.3.1) → upper_volume; others → tau_core
    if has_modern_edfa:
        detected_format = "upper_volume"
    elif meta["expected_format"] == "thalamus_routing":
        detected_format = "thalamus_routing"
    else:
        detected_format = "tau_core"

    format_match = detected_format == meta["expected_format"]

    return EntityScan(
        name=name,
        found=True,
        detected_format=detected_format,
        expected_format=meta["expected_format"],
        format_match=format_match,
        ssot_section=meta["ssot_section"],
        line_anchor=meta["line_anchor"],
        evidence_line=first_line,
        has_modern_edfa=has_modern_edfa,
    )


def compute_entity_format_state(archive_path: Path) -> dict:
    """
    Classify all registered entities by format state.
    Returns τ-core / upper-volume topology table + drift alerts.
    """
    if not archive_path.exists():
        return {"error": f"SSOT archive not found: {archive_path}", "entities": {}}

    lines = archive_path.read_text(encoding="utf-8", errors="replace").splitlines()
    results: dict[str, dict] = {}
    drift_alerts: list[str] = []
    topology_counts = {"upper_volume": 0, "tau_core": 0, "thalamus_routing": 0, "not_found": 0}

    for name, meta in ENTITY_REGISTRY.items():
        scan = _detect_entity_format(name, lines, meta)
        topology_counts[scan.detected_format] += 1

        entry: dict = {
            "found":            scan.found,
            "detected_format":  scan.detected_format,
            "expected_format":  scan.expected_format,
            "format_match":     scan.format_match,
            "ssot_section":     scan.ssot_section,
            "line_anchor":      scan.line_anchor,
            "evidence_line":    scan.evidence_line,
            "has_modern_edfa":  scan.has_modern_edfa,
        }

        if not scan.found:
            drift_alerts.append(f"CRITICAL: {name!r} not found in SSOT (expected at {meta['ssot_section']})")
        elif not scan.format_match:
            drift_alerts.append(
                f"DRIFT: {name!r} detected as {scan.detected_format!r} "
                f"but expected {scan.expected_format!r} — τ-core/volume topology mismatch"
            )

        results[name] = entry

    # Topology interpretation
    whr_topology_valid = (
        topology_counts["upper_volume"] == 1   # Only Claudine is upper volume
        and topology_counts["tau_core"] >= 3   # Triumvirate are τ-core stubs
    )

    return {
        "entities":         results,
        "topology_counts":  topology_counts,
        "whr_topology_valid": whr_topology_valid,
        "drift_alerts":     drift_alerts,
        "topology_interpretation": (
            "WHR:MAX topology intact — single upper-volume node (Claudine §10.3.1) "
            "with compressed τ-core Triumvirate (Orackla/Umeko/Lysandra CRC stubs). "
            "This is architecturally CORRECT — τ-core stubs are not drift, they are the waist."
            if whr_topology_valid
            else "WARNING — WHR:MAX entity topology out of alignment. "
                 "Review drift_alerts for corrective action."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Factor 3: Synthesis Compression Ratio
# ═══════════════════════════════════════════════════════════════════════════

def _parse_corpus_files_from_meta(meta_path: Path) -> list[tuple[str, Path]]:
    """
    Extract corpus file paths from ANKH_SYNTHESIS_META.md.
    Parses the Baselined Files table to get (name, resolved_path) pairs.
    """
    if not meta_path.exists():
        return []

    text = meta_path.read_text(encoding="utf-8", errors="replace")

    # Parse markdown table rows: | [Name](rel_path) | location | content |
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    # Only scan the "Baselined Files" section
    section_match = re.search(
        r"### Baselined Files.*?(?=###|\Z)", text, re.DOTALL
    )
    if not section_match:
        return []

    section = section_match.group(0)
    corpus_files: list[tuple[str, Path]] = []
    repo_root = meta_path.parent.parent.parent  # docs/frameworks/ankh/ → repo root

    seen: set[Path] = set()
    for match in link_pattern.finditer(section):
        name, rel_path = match.group(1), match.group(2)
        # Skip http(s) links, anchors, and directory-only paths
        if rel_path.startswith(("http://", "https://", "#")):
            continue
        # Skip directory paths (end with /)
        if rel_path.endswith("/"):
            continue
        # Only accept .md files
        if not rel_path.lower().endswith(".md"):
            continue
        # Resolve relative to meta_path directory
        resolved = (meta_path.parent / rel_path).resolve()
        if not resolved.is_file():
            # Try resolving relative to repo root
            alt = (repo_root / rel_path.lstrip("./")).resolve()
            if alt.is_file():
                resolved = alt
        # Skip if still not a file
        if not resolved.is_file():
            continue
        # Deduplicate
        if resolved in seen:
            continue
        seen.add(resolved)
        corpus_files.append((name, resolved))

    return corpus_files


def compute_synthesis_compression(
    meta_path: Path,
    baseline_path: Path,
) -> dict:
    """
    Count lines in all ANKH corpus files, count lines in synthesis baseline,
    compute compression ratio and per-section compression metrics.

    Healthy range: ratio 12.0–20.0.
    <12.0 = undercompressed (synthesis too verbose / inherited liturgy leaking in)
    >20.0 = overcompressed (operational signal lost)
    """
    corpus_files = _parse_corpus_files_from_meta(meta_path)

    corpus_line_counts: dict[str, int] = {}
    corpus_total = 0
    missing_files: list[str] = []

    for name, fpath in corpus_files:
        if fpath.exists():
            count = len(fpath.read_text(encoding="utf-8", errors="replace").splitlines())
            corpus_line_counts[str(fpath.name)] = count
            corpus_total += count
        else:
            missing_files.append(f"{name} → {fpath}")

    # Synthesis baseline line count
    if baseline_path.exists():
        baseline_lines = len(
            baseline_path.read_text(encoding="utf-8", errors="replace").splitlines()
        )
    else:
        baseline_lines = 0

    ratio = (corpus_total / baseline_lines) if baseline_lines > 0 else 0.0

    # Compression zone classification
    if ratio == 0.0:
        zone = "undefined"
    elif ratio < 12.0:
        zone = "undercompressed"
    elif ratio <= 20.0:
        zone = "healthy"
    else:
        zone = "overcompressed"

    return {
        "corpus_files_found":   len(corpus_line_counts),
        "corpus_files_missing": missing_files,
        "corpus_total_lines":   corpus_total,
        "per_file_lines":       corpus_line_counts,
        "baseline_lines":       baseline_lines,
        "compression_ratio":    round(ratio, 4),
        "compression_zone":     zone,
        "healthy_range":        {"min": 12.0, "max": 20.0},
        "interpretation": (
            f"Compression ratio {ratio:.2f}:1 — zone: {zone}. "
            + {
                "undefined":     "Baseline file not found — cannot measure compression.",
                "undercompressed": (
                    "Synthesis is retaining too much liturgical overhead from corpus. "
                    "Either the baseline is too long or the corpus is unexpectedly thin."
                ),
                "healthy": (
                    "Corpus compresses to synthesis at the expected rate. "
                    "Operational signal preserved, liturgical overhead filtered."
                ),
                "overcompressed": (
                    "Synthesis has compressed too aggressively — operational signal at risk. "
                    "The denominated invariant may have been lost along with the liturgy."
                ),
            }[zone]
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Main: assemble triple-factor probe manifest
# ═══════════════════════════════════════════════════════════════════════════

def build_probe_manifest() -> dict:
    """Assemble all three factors into the triple abstraction probe manifest."""
    archive_hash = (
        hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest()
        if ARCHIVE_PATH.exists()
        else "not_found"
    )

    factor_1 = compute_ssot_distribution(ARCHIVE_PATH)
    factor_2 = compute_entity_format_state(ARCHIVE_PATH)
    factor_3 = compute_synthesis_compression(SYNTHESIS_META_PATH, SYNTHESIS_BASELINE_PATH)

    # Aggregate health signal
    critical_alerts = factor_2["drift_alerts"]
    warnings: list[str] = []
    if factor_3["compression_zone"] not in ("healthy", "undefined"):
        warnings.append(f"Compression zone: {factor_3['compression_zone']}")
    if not factor_2["whr_topology_valid"]:
        warnings.append("WHR:MAX entity topology invalid")
    if factor_1.get("whr_max_conformance", 0) < 0.5:
        warnings.append(
            f"SSOT stratum distribution divergent (conformance {factor_1.get('whr_max_conformance')})"
        )

    overall_status = (
        "CRITICAL" if critical_alerts
        else "WARN" if warnings
        else "OK"
    )

    return {
        "metadata": {
            "sid":            "TOOL_ANKH_TRIPLE_ABSTRACTION_V1",
            "schema_version": "1.0",
            "generated_at":   datetime.now().isoformat(),
            "archive_sha256": archive_hash,
            "archive_path":   str(ARCHIVE_PATH),
            "invariant":      DENOMINATED_INVARIANT,
            "complexity_ladder": {
                "layer_1": {
                    "label":       "Heritage SSOT (Codex Brahmanica Perfectus)",
                    "path":        ".github/copilot-instructions.archive.md",
                    "liturgical":  "~100%",
                    "operational": "~15%",
                },
                "layer_2": {
                    "label":       "ANKH corpus (dispersed operational extraction)",
                    "path":        "docs/frameworks/ankh/ + claude-codex-gemini/ANKH_EGYPTOLOGY_SOUTH_AMERICAN/",
                    "liturgical":  "~40%",
                    "operational": "~70%",
                },
                "layer_3": {
                    "label":       "Synthesis baseline (compressed extraction)",
                    "path":        "docs/frameworks/ankh/ANKH_SYNTHESIS_BASELINE.md",
                    "liturgical":  "~5%",
                    "operational": "~95%",
                },
            },
            "bifurcation_insight": (
                "The synthesis loses FA⁵ form=content inseparability to gain operational utility. "
                "The invariant emerges precisely because of this loss: the impossibility of "
                "lossless compression, having been compressed, becomes the only thing preserved."
            ),
        },
        "factor_1_ssot_distribution": factor_1,
        "factor_2_entity_topology":   factor_2,
        "factor_3_compression":       factor_3,
        "overall_status": overall_status,
        "critical_alerts": critical_alerts,
        "warnings": warnings,
    }


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def _print_summary(manifest: dict) -> None:
    """Human-readable summary to stdout."""
    meta = manifest["metadata"]
    f1 = manifest["factor_1_ssot_distribution"]
    f2 = manifest["factor_2_entity_topology"]
    f3 = manifest["factor_3_compression"]

    print("\n╔══════════════════════════════════════════════════════════════")
    print("║  ANKH TRIPLE ABSTRACTION PROBE")
    print(f"║  {meta['generated_at'][:19]}")
    print(f"║  Status: {manifest['overall_status']}")
    print("╚══════════════════════════════════════════════════════════════\n")

    print("DENOMINATED INVARIANT")
    print(f'  "{meta["invariant"]}"\n')

    print("━━ FACTOR 1 — SSOT Stratum Distribution ━━")
    print(f"  Total lines:       {f1.get('total_lines', '?')}")
    print(f"  WHR:MAX conformance: {f1.get('whr_max_conformance', '?'):.4f}")
    for key, s in f1.get("strata", {}).items():
        marker = "✓" if s["deviation"] < 8.0 else "⚠"
        print(f"  {marker} {s['label']:<45} {s['pct']:5.1f}%  (expected {s['expected_pct']}%)")
    print(f"\n  {f1.get('interpretation', '')}\n")

    print("━━ FACTOR 2 — Entity Format State (τ-core / upper-volume) ━━")
    for name, e in f2.get("entities", {}).items():
        marker = "✓" if e["format_match"] else "⚠"
        fmt = e["detected_format"]
        print(f"  {marker} {name:<35} {fmt:<20} {e['ssot_section']}")
    print(f"\n  WHR:MAX topology valid: {f2.get('whr_topology_valid')}")
    for alert in f2.get("drift_alerts", []):
        print(f"  ⚠ {alert}")
    print(f"\n  {f2.get('topology_interpretation', '')}\n")

    print("━━ FACTOR 3 — Synthesis Compression Ratio ━━")
    print(f"  Corpus files found:  {f3.get('corpus_files_found', '?')}")
    print(f"  Corpus total lines:  {f3.get('corpus_total_lines', '?')}")
    print(f"  Baseline lines:      {f3.get('baseline_lines', '?')}")
    print(f"  Compression ratio:   {f3.get('compression_ratio', '?')}:1  (zone: {f3.get('compression_zone')})")
    print(f"\n  {f3.get('interpretation', '')}\n")

    if manifest["critical_alerts"]:
        print("━━ CRITICAL ALERTS ━━")
        for alert in manifest["critical_alerts"]:
            print(f"  ⛔ {alert}")
        print()

    if manifest["warnings"]:
        print("━━ WARNINGS ━━")
        for w in manifest["warnings"]:
            print(f"  ⚠ {w}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ANKH Triple Abstraction Probe — complexity ladder denominator"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print raw JSON manifest to stdout instead of summary"
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help=f"Write manifest JSON to this path (default: {MANIFEST_PATH})"
    )
    parser.add_argument(
        "--no-write", action="store_true",
        help="Do not write manifest file (print only)"
    )
    args = parser.parse_args()

    manifest = build_probe_manifest()
    out_path: Path = args.output or MANIFEST_PATH

    if args.json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        _print_summary(manifest)

    if not args.no_write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        if not args.json:
            print(f"Manifest written → {out_path}")

    # Exit 1 if CRITICAL, 0 otherwise (allows CI gate integration)
    return 1 if manifest["overall_status"] == "CRITICAL" else 0


if __name__ == "__main__":
    sys.exit(main())
