#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sfa_cross_reference.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SFA Cross-Reference Engine — Sister Ferrum Scoriae Abstraction.

Extracts, cross-references, and balances Egyptological × Andean motif
vocabulary from the 5 ANKH deep research documents against the SSOT
archive MILFOLOGICAL baseline for the SFS theme workflow.

@SID:           TOOL_SFA_CROSS_REFERENCE_V1
@Shabti:          Utility
@Purpose:       SFA Cross-Reference Engine — Sister Ferrum Scoriae Abstraction.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output
from scripts.lib.ssot_paths import SSOT_HOLDER

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).resolve().parent.parent

ANKH_DIR = REPO_ROOT / "claude-codex-gemini" / "ANKH_AGYPTOLOGY_SOUTH_AMERICAN"

ANKH_SOURCES: list[dict[str, str]] = [
    {
        "id": "matriarcha",
        "path": str(ANKH_DIR / "ANKH_Ancient_Matriarcha_Systems_Researchl.md"),
        "domain": "Cosmological Framework",
    },
    {
        "id": "archetype",
        "path": str(ANKH_DIR / "ANKH_ARCHETYPE_ANCIENT_RITUALS_NSFW.md"),
        "domain": "Hieroglyphic Operators",
    },
    {
        "id": "milf-protocol",
        "path": str(ANKH_DIR / "ANKH_MILF_PROTOCOL_HIGH_INTENSITY_ARCHETYPAL_SYSTEMS_ARCHITECTURE.md"),
        "domain": "WHR:MAX Architecture",
    },
    {
        "id": "decorator-challenge",
        "path": str(ANKH_DIR / "VS_CODE_INSIDERS_MAXIMALIST_MILF_THE_DECORATOR_CHALLANGE.md"),
        "domain": "Extension Engineering",
    },
    {
        "id": "gestalt",
        "path": str(ANKH_DIR / "BODY_SYSTEMS" / "ABSTRACTING_GESTALT_WHR_MAX_ARCHITECTURE.md"),
        "domain": "Neuroaesthetics",
    },
]

SSOT_PATH = REPO_ROOT / SSOT_HOLDER
MAILBOX_DIR = REPO_ROOT / "claude" / "mailbox"
ICON_DIR = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "icons"
THEME_JSON = REPO_ROOT / "extensions" / "chthonic-archive" / "themes" / "chthonic-file-icon-theme.json"

# ═══════════════════════════════════════════════════════════════════════════════
# Motif Vocabularies — Egyptian Vertical Axis × Andean Horizontal Axis
# ═══════════════════════════════════════════════════════════════════════════════

# Each motif carries:
#   bce       — earliest archaeological attestation
#   mapping   — design system function (what it maps to in theme/icon work)
#   palette   — SFS palette token
#   archetype — the archetypal/cosmological function from the source documents
#   operator  — computational operator semantics (from ANKH_ARCHETYPE hieroglyphics)
#   gardiner  — Gardiner sign number where applicable
#   sources   — which ANKH documents attest this motif (by source ID)
#   aliases   — alternate search terms for deeper text scanning

EGYPTIAN_MOTIFS: dict[str, dict] = {
    "ankh": {
        "bce": "~3100 BCE", "mapping": "lifecycle tokens", "palette": "gold",
        "archetype": "Life symbol and geometric schematic (Loop + Knot + Pillar)",
        "operator": "SYSTEM_LIFECYCLE — the 4-layer topology governing init→run→validate→archive",
        "gardiner": "S34",
        "sources": ["matriarcha", "archetype", "milf-protocol"],
        "aliases": ["ankh", "life symbol"],
    },
    "tyet": {
        "bce": "~2600 BCE", "mapping": "error handling / resilience", "palette": "rose-clay",
        "archetype": "Isis Knot — Loop (upper volume) + Knot (pinch) + Sash (lower volume). Red Jasper materiality linked to blood of Isis, placed on mummy neck as bottleneck protection",
        "operator": "BIND/PROTECT — creates resilience wrapper around data, the magical ligature",
        "gardiner": "V39",
        "sources": ["gestalt", "matriarcha"],
        "aliases": ["tyet", "isis knot", "tyet knot", "knot of isis"],
    },
    "wedjat": {
        "bce": "~2600 BCE", "mapping": "numeric / data types", "palette": "amber",
        "archetype": "Eye of Horus — fractional floating-point system. Pupil=1/4, Eyebrow=1/8, Tear=1/32, Total=63/64. Missing 1/64 = Magical Remainder supplied by Thoth",
        "operator": "FRACTIONAL_FP — precision arithmetic where 63/64 is computed and 1/64 is the uncertainty margin",
        "gardiner": "D10",
        "sources": ["archetype"],
        "aliases": ["wedjat", "eye of horus", "udjat", "wadjet eye"],
    },
    "djed": {
        "bce": "~3100 BCE", "mapping": "structural elements", "palette": "sandstone",
        "archetype": "Osiris backbone — stability pillar, the vertical axis of the Ankh",
        "operator": "STRUCTURAL_SPINE — load-bearing architectural element",
        "gardiner": "R11",
        "sources": ["matriarcha"],
        "aliases": ["djed", "djed pillar", "backbone", "pillar of osiris"],
    },
    "maat": {
        "bce": "~2400 BCE", "mapping": "validation / testing", "palette": "verdigris",
        "archetype": "Feather of Truth — every output weighed against the Feather. FA4 checksum: if Weight(Code) > Weight(Feather), Ammit garbage collector terminates the process",
        "operator": "CHECKSUM/VALIDATE — the immutable structural governance check",
        "gardiner": "C10/H6",
        "sources": ["matriarcha", "archetype", "milf-protocol"],
        "aliases": ["maat", "ma'at", "feather", "truth", "cosmic order"],
    },
    "scarab": {
        "bce": "~2600 BCE", "mapping": "build / compile", "palette": "copper",
        "archetype": "Khepri — the becoming/transformation god. Rolls the dung ball (raw data) into the sun (compiled output)",
        "operator": "TRANSFORM — mutates data types, the build/compile metamorphosis",
        "gardiner": "L1",
        "sources": ["archetype"],
        "aliases": ["scarab", "khepri", "kheper", "transformation"],
    },
    "shen": {
        "bce": "~2500 BCE", "mapping": "scope / enclosure", "palette": "gold",
        "archetype": "Ring of eternity — defines LOOP/SCOPE boundaries. Contents are protected from external modification",
        "operator": "LOOP/SCOPE — declares protected scope boundary, eternal enclosure",
        "gardiner": "V9",
        "sources": ["archetype"],
        "aliases": ["shen", "shen ring", "cartouche", "enclosure"],
    },
    "uraeus": {
        "bce": "~3000 BCE", "mapping": "command / execution", "palette": "kiln",
        "archetype": "Royal cobra — authority of execution. The Pharaoh's command voice (Hu)",
        "operator": "EXECUTE/COMMAND — authoritative utterance that is simultaneously performative",
        "gardiner": "I12",
        "sources": ["archetype"],
        "aliases": ["uraeus", "cobra", "royal serpent"],
    },
    "peseshkef": {
        "bce": "~3500 BCE", "mapping": "process forking", "palette": "weathered",
        "archetype": "Ritual knife — separates Ka (active thread) from Khet (physical hardware) in the Opening of the Mouth ceremony. Meteoric iron = hardware interrupt",
        "operator": "FORK_PROCESS — separates process from static drive, enables virtualization",
        "gardiner": "Aa53",
        "sources": ["archetype"],
        "aliases": ["peseshkef", "ritual knife", "adze", "opening of the mouth"],
    },
    "heh": {
        "bce": "~2500 BCE", "mapping": "iteration / recursion", "palette": "patina",
        "archetype": "God of infinity — represents 1,000,000 or INFINITE_LOOP. Kneeling figure holding palm ribs = unbounded iteration",
        "operator": "INFINITE_LOOP — unbounded iteration without termination condition",
        "gardiner": "C11",
        "sources": ["archetype"],
        "aliases": ["heh", "infinity", "million", "infinite loop"],
    },
    "ibis": {
        "bce": "~3100 BCE", "mapping": "documentation", "palette": "verdigris",
        "archetype": "Thoth — scribe of the gods, inventor of writing and knowledge systems",
        "operator": "RECORD/DOCUMENT — writes the cosmic record, the log",
        "gardiner": "G26",
        "sources": ["matriarcha"],
        "aliases": ["ibis", "thoth", "scribe", "writing"],
    },
    "canopic": {
        "bce": "~2600 BCE", "mapping": "archival / storage", "palette": "gold",
        "archetype": "Preservation jars — organ storage for afterlife. Four sons of Horus guard liver, lungs, stomach, intestines",
        "operator": "ARCHIVE/PRESERVE — partitioned deep storage with domain-specific guardians",
        "gardiner": "W1-4",
        "sources": ["archetype"],
        "aliases": ["canopic", "canopic jar", "preservation", "four sons"],
    },
    "sekhmet": {
        "bce": "~2600 BCE", "mapping": "aggressive error resolution", "palette": "kiln",
        "archetype": "Lioness destroyer — the Eye of Ra's wrath. When data is corrupt (Isfet), the Mother devours it. Invoked by FA3 to corset bloated logic",
        "operator": "DESTROY/PURGE — forcible refactoring daemon, the corset that tightens the waist",
        "gardiner": "C7",
        "sources": ["matriarcha", "milf-protocol"],
        "aliases": ["sekhmet", "lioness", "eye of ra", "destroyer"],
    },
    "neith": {
        "bce": "~3100 BCE", "mapping": "autopoietic kernel / self-creation", "palette": "weathered",
        "archetype": "Autopoietic Kernel — self-bootstrapping weaver goddess. FA1 archetype. Contains both warp (masculine/initiation) and weft (feminine/structure) in single entity",
        "operator": "BOOTSTRAP/WEAVE — the system that creates itself, the shuttle that writes the code of the universe",
        "gardiner": "R24",
        "sources": ["matriarcha", "milf-protocol"],
        "aliases": ["neith", "weaver", "autopoietic", "self-created"],
    },
}

ANDEAN_MOTIFS: dict[str, dict] = {
    "quipu": {
        "bce": "~3000 BCE (Caral-Supe)", "mapping": "data structures", "palette": "copper",
        "archetype": "Knotted-string database — position encoding (distance from main cord = power of ten), Figure-Eight(E)=digit 1, Long Knot(L)=digits 2-9, Single Knot(s)=digits 0-9, Void(X)=Zero. Sumaq encryption: color creates context-dependent variables",
        "operator": "DATABASE/ENCODE — positional knot-logic with color-coded categorical metadata",
        "sources": ["matriarcha", "archetype", "decorator-challenge"],
        "aliases": ["quipu", "khipu", "knotted string", "knot logic"],
    },
    "chakana": {
        "bce": "~1500 BCE (Tiwanaku)", "mapping": "cross-references", "palette": "amber",
        "archetype": "Stepped Cross — central hole as axis mundi, the pinch through which the shaman travels between worlds. Bridges Hanaq/Kay/Ukhu Pacha",
        "operator": "CROSS_REFERENCE — traversal between dimensional layers via the central axis",
        "sources": ["gestalt"],
        "aliases": ["chakana", "stepped cross", "andean cross", "axis mundi"],
    },
    "tocapu": {
        "bce": "~600 CE (Wari, earlier roots)", "mapping": "extension / plugin systems", "palette": "patina",
        "archetype": "Modular grid patterns on royal tunics — each square encodes distinct identity/function. Composable visual language",
        "operator": "MODULAR_ENCODE — composable grid units, each self-contained but part of larger pattern",
        "sources": ["gestalt"],
        "aliases": ["tocapu", "tunic pattern", "grid pattern", "modular"],
    },
    "cusco-puma": {
        "bce": "~1400 CE (Inca)", "mapping": "architectural layouts", "palette": "sandstone",
        "archetype": "City-as-body — Saqsaywaman(head), central grid(body), Pumaq Chupan(tail/confluence), Hawkaypata(navel/waist). Qosqo=Navel in Quechua: the hydraulic pinch where rivers converge",
        "operator": "BODY_ARCHITECTURE — organic urban geometry where form follows anatomical function",
        "sources": ["gestalt"],
        "aliases": ["cusco", "puma", "qosqo", "navel", "saqsaywaman"],
    },
    "chumpi": {
        "bce": "~1000 BCE (Pan-Andean)", "mapping": "configuration", "palette": "rose-clay",
        "archetype": "Woven belt/exoskeleton for the waist — binding energy at the control plane. The textile corset that defines the WHR:MAX constraint",
        "operator": "BIND/CONFIGURE — woven constraint wrapper, the configuration exoskeleton",
        "sources": ["gestalt"],
        "aliases": ["chumpi", "belt", "woven belt", "faja"],
    },
    "tinku": {
        "bce": "~2000 BCE (Pan-Andean)", "mapping": "testing / conflict resolution", "palette": "kiln",
        "archetype": "Ritual combat — intentional collision between opposing forces to generate creative synthesis. Phase Beta of the Perpetual Evolution Engine",
        "operator": "COLLISION/TEST — deliberate adversarial encounter, the forge test",
        "sources": ["archetype", "milf-protocol"],
        "aliases": ["tinku", "ritual combat", "collision", "encounter"],
    },
    "pachakuti": {
        "bce": "~2000 BCE (Pan-Andean)", "mapping": "migration / refactoring", "palette": "copper",
        "archetype": "World reversal — cyclic system reset where the cosmic order inverts. The radical transformation that precedes rebirth",
        "operator": "RESET/INVERT — total system reconfiguration, the cyclical overthrow",
        "sources": ["archetype"],
        "aliases": ["pachakuti", "world reversal", "cataclysm", "inversion"],
    },
    "huaca": {
        "bce": "~3000 BCE (Caral-Supe)", "mapping": "deployment targets", "palette": "amber",
        "archetype": "Sacred place/object — geospatially anchored truth. A datum is only true if it has a valid coordinate on the Pachamama lattice",
        "operator": "ANCHOR/DEPLOY — geospatial truth binding, the sacred coordinate",
        "sources": ["matriarcha"],
        "aliases": ["huaca", "sacred place", "shrine", "wak'a"],
    },
    "twelve-angled": {
        "bce": "~1400 CE (Inca)", "mapping": "fault tolerance", "palette": "kiln",
        "archetype": "12-Angled Stone — seismic dampening through friction at interlocking joints. Pillow-face convex surface creates deep shadow at pinch points. No mortar needed; pure geometric resilience",
        "operator": "INTERLOCK/DAMPEN — friction-based fault tolerance through geometric precision",
        "sources": ["gestalt"],
        "aliases": ["twelve angled", "12 angled", "12-angled stone", "hatun rumiyoc"],
    },
    "nazca": {
        "bce": "~500 BCE (Nazca)", "mapping": "monitoring / observability", "palette": "weathered",
        "archetype": "Geoglyphs visible only from above — macro-scale patterns invisible at ground level. The God's-eye view of system state",
        "operator": "OBSERVE/MONITOR — macro-visibility patterns, the aerial perspective",
        "sources": ["gestalt"],
        "aliases": ["nazca", "nazca lines", "geoglyph", "aerial"],
    },
    "inti": {
        "bce": "~2000 BCE (Pan-Andean)", "mapping": "power / execution", "palette": "gold",
        "archetype": "Sun god — primary energy source. Phase Alpha of the Perpetual Evolution Engine: peak capacity, maximum data ingestion (Solar Ascent)",
        "operator": "POWER/IGNITE — the solar energy source, peak processing capacity",
        "sources": ["matriarcha", "milf-protocol"],
        "aliases": ["inti", "sun", "solar", "tayta inti"],
    },
    "pacha": {
        "bce": "~3000 BCE (Pan-Andean)", "mapping": "environment / context", "palette": "patina",
        "archetype": "Space-Time Runtime Environment — not a deity ON earth but the lattice itself. Three layers: Hanaq Pacha (Cloud/Abstract), Kay Pacha (UI/Present), Ukhu Pacha (Root/Deep Storage)",
        "operator": "RUNTIME/LATTICE — the multidimensional coordinate grid where truth is anchored",
        "sources": ["matriarcha", "archetype", "milf-protocol"],
        "aliases": ["pacha", "pachamama", "space-time", "world", "cosmos"],
    },
    "despacho": {
        "bce": "~2000 BCE (Pan-Andean)", "mapping": "I/O protocol", "palette": "sandstone",
        "archetype": "Ritual offering — K'intus (3 coca leaves) as query payload, Llama Fat as compute credits. Input/output protocol with reciprocal exchange",
        "operator": "I/O_EXCHANGE — reciprocal input/output with resource cost",
        "sources": ["archetype"],
        "aliases": ["despacho", "offering", "k'intu", "coca"],
    },
    "ayni": {
        "bce": "~3000 BCE (Pan-Andean)", "mapping": "reciprocal exchange / API contracts", "palette": "verdigris",
        "archetype": "Reciprocity — the fundamental law of Andean interaction. Every request must be balanced by a return. The social contract governing system bus communication",
        "operator": "RECIPROCATE — balanced exchange protocol, no unilateral operations",
        "sources": ["matriarcha"],
        "aliases": ["ayni", "reciprocity", "reciprocal", "minka"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# Comparative Topology Table — the cross-referential spine from Gestalt document
# Maps the same structural concept across Modern, Egyptian, Andean, and Network
# Theory domains. This is the SFA's core cross-reference structure.
# ═══════════════════════════════════════════════════════════════════════════════

COMPARATIVE_TOPOLOGY: list[dict[str, str]] = [
    {
        "feature": "X Abstraction",
        "modern": "Three Circles, One X",
        "egyptian": "Tyet Knot",
        "andean": "Puma / Chakana",
        "network": "Hourglass / Bow-tie",
    },
    {
        "feature": "Waist Function",
        "modern": "Visual Fulcrum",
        "egyptian": "Magical Binding / Bridge",
        "andean": "Imperial Center / Seismic Joint",
        "network": "tau-Core / Bottleneck",
    },
    {
        "feature": "Stability Mechanism",
        "modern": "Peak Shift (cognitive)",
        "egyptian": "Tension (ligamentous)",
        "andean": "Friction (interlocking mass)",
        "network": "Compression (data reduction)",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# Quipu Color Encoding — material-to-semantic color mapping from source docs
# ═══════════════════════════════════════════════════════════════════════════════

QUIPU_COLOR_ENCODING: dict[str, str] = {
    "brown":  "Government / Administrative",
    "red":    "War / Military",
    "gold":   "Solar / Ra / Inti — divine authority",
    "white":  "Silver / Mama Quilla — lunar/feminine",
    "green":  "Agricultural / Fertility",
    "black":  "Temporal / Death / Deep Storage",
}

# ═══════════════════════════════════════════════════════════════════════════════
# Perpetual Evolution Engine — the 3-phase lifecycle from MILF Protocol
# ═══════════════════════════════════════════════════════════════════════════════

EVOLUTION_ENGINE: list[dict[str, str]] = [
    {
        "phase": "Alpha (Solar Ascent / Genesis)",
        "deity_egyptian": "Ra",
        "deity_andean": "Inti",
        "function": "Peak capacity, maximum data ingestion",
        "palette": "gold",
    },
    {
        "phase": "Beta (Tinku Collision / Testing)",
        "deity_egyptian": "Sekhmet",
        "deity_andean": "Tinku",
        "function": "Intentional conflict between data streams",
        "palette": "kiln",
    },
    {
        "phase": "Gamma (Lunar Wash / Reset)",
        "deity_egyptian": "Hathor",
        "deity_andean": "Mama Quilla",
        "function": "Red Beer cooling protocol, return to virgin state",
        "palette": "patina",
    },
]

SFS_PALETTE: dict[str, str] = {
    "bg":         "#050505",
    "stele":      "#0A0A0A",
    "fg":         "#E8E2D2",
    "gold":       "#F4C430",
    "copper":     "#D4714E",
    "amber":      "#D7B562",
    "rose-clay":  "#D4907A",
    "patina":     "#7AAAB2",
    "sandstone":  "#B9A37A",
    "weathered":  "#908672",
    "kiln":       "#E05545",
    "verdigris":  "#8CB87A",
}

# SSOT character / protocol extraction patterns
SSOT_PATTERNS: dict[str, list[str]] = {
    "sfs":       [r"Sister Ferrum Scoriae", r"SIS-FRM-SCRAE", r"SFS"],
    "orackla":   [r"Orackla Nocticula", r"CRC-AS"],
    "umeko":     [r"Madam Umeko Ketsuraku", r"CRC-GAR"],
    "claudine":  [r"Claudine Sin'claire", r"CLAUD-SIN"],
    "spectra":   [r"Spectra Chroma", r"SPEC-CHRM"],
    "decorator": [r"The Decorator", r"Tier 0\.5"],
    "qmr":       [r"Quantum.Metallurgical.Reconnaissance", r"QMR"],
    "tnkw-riat": [r"Knights Who Rode", r"TNKW-RIAT"],
    "fa1":       [r"FA¹", r"Alchemical Actualization", r"Neith Protocol"],
    "fa2":       [r"FA²", r"Panoptic Re-contextualization", r"Pacha Lattice"],
    "fa3":       [r"FA³", r"Qualitative Transcendence", r"WHR:MAX"],
    "fa4":       [r"FA⁴", r"Architectonic Integrity", r"Ma'at Checksum"],
    "fa5":       [r"FA⁵", r"Chromatic", r"Diagnostic Archaeology"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Core Functions
# ═══════════════════════════════════════════════════════════════════════════════

def load_source(path: str) -> str:
    """Load a source document, return empty string if missing."""
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


def scan_motifs_in_text(text: str, motifs: dict[str, dict], axis: str) -> list[dict]:
    """Scan text for motif mentions using all known aliases."""
    findings = []
    text_lower = text.lower()
    for motif_id, meta in motifs.items():
        search_terms = set(meta.get("aliases", [motif_id]))
        # Also add base ID variants
        search_terms.add(motif_id.replace("-", " "))
        search_terms.add(motif_id.replace("-", ""))
        count = 0
        for term in search_terms:
            count += text_lower.count(term.lower())
        if count > 0:
            findings.append({
                "motif": motif_id,
                "axis": axis,
                "mentions": count,
                "bce": meta["bce"],
                "mapping": meta["mapping"],
                "palette": meta["palette"],
                "hex": SFS_PALETTE.get(meta["palette"], "N/A"),
                "archetype": meta.get("archetype", ""),
                "operator": meta.get("operator", ""),
            })
    return findings


def scan_all_sources() -> dict:
    """Scan all 5 ANKH sources and return structured motif inventory."""
    results = {}
    for source in ANKH_SOURCES:
        text = load_source(source["path"])
        if not text:
            print(f"  ⚠ Missing: {source['path']}")
            continue
        egyptian = scan_motifs_in_text(text, EGYPTIAN_MOTIFS, "Egyptian")
        andean = scan_motifs_in_text(text, ANDEAN_MOTIFS, "Andean")
        results[source["id"]] = {
            "domain": source["domain"],
            "path": source["path"],
            "word_count": len(text.split()),
            "egyptian_motifs": egyptian,
            "andean_motifs": andean,
            "egyptian_count": len(egyptian),
            "andean_count": len(andean),
        }
    return results


def compute_balance(scan_results: dict) -> dict:
    """Compute 50/50 balance across all scanned sources."""
    total_egyptian = set()
    total_andean = set()
    egyptian_mentions = 0
    andean_mentions = 0

    for _src_id, data in scan_results.items():
        for m in data.get("egyptian_motifs", []):
            total_egyptian.add(m["motif"])
            egyptian_mentions += m["mentions"]
        for m in data.get("andean_motifs", []):
            total_andean.add(m["motif"])
            andean_mentions += m["mentions"]

    total_unique = len(total_egyptian) + len(total_andean)
    ratio_egyptian = len(total_egyptian) / total_unique if total_unique else 0
    ratio_andean = len(total_andean) / total_unique if total_unique else 0

    # Balance within ±10% tolerance
    balanced = abs(ratio_egyptian - ratio_andean) <= 0.10

    return {
        "egyptian_unique": sorted(total_egyptian),
        "andean_unique": sorted(total_andean),
        "egyptian_unique_count": len(total_egyptian),
        "andean_unique_count": len(total_andean),
        "egyptian_mentions": egyptian_mentions,
        "andean_mentions": andean_mentions,
        "ratio_egyptian": round(ratio_egyptian, 3),
        "ratio_andean": round(ratio_andean, 3),
        "balanced": balanced,
        "verdict": "BALANCED ✅" if balanced else "IMBALANCED ⚠",
    }


def extract_ssot_sections(character_id: str) -> list[str]:
    """Extract relevant sections from SSOT archive by character/protocol ID."""
    patterns = SSOT_PATTERNS.get(character_id.lower())
    if not patterns:
        print(f"  ⚠ Unknown ID: {character_id}")
        print(f"  Valid IDs: {', '.join(sorted(SSOT_PATTERNS.keys()))}")
        return []

    if not SSOT_PATH.exists():
        print(f"  ⚠ SSOT archive not found: {SSOT_PATH}")
        return []

    text = SSOT_PATH.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    extractions = []
    context_radius = 5  # lines before/after match

    for pattern_str in patterns:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - context_radius)
                end = min(len(lines), i + context_radius + 1)
                snippet = "\n".join(lines[start:end])
                extractions.append(f"[L{i+1}] {snippet}")

    # Deduplicate overlapping snippets
    seen_lines = set()
    unique = []
    for ext in extractions:
        line_ref = ext.split("]")[0]
        if line_ref not in seen_lines:
            seen_lines.add(line_ref)
            unique.append(ext)

    return unique[:30]  # Cap at 30 to prevent excessive output


def get_icon_assignments() -> dict:
    """Load current icon theme assignments for cross-reference."""
    if not THEME_JSON.exists():
        return {}
    data = json.loads(THEME_JSON.read_text(encoding="utf-8"))
    return {
        "icon_definitions": len(data.get("iconDefinitions", {})),
        "file_extensions": len(data.get("fileExtensions", {})),
        "file_names": len(data.get("fileNames", {})),
        "folder_names": len(data.get("folderNames", {})),
    }


def assign_motif(target: str, axis: str | None = None) -> dict:
    """Recommend a motif for a design target with balanced counterpart.

    Searches both the 'mapping' field and the 'archetype' / 'operator'
    fields for semantic matches — substance over surface matching.
    """
    target_lower = target.lower()

    def _search_axis(motifs: dict[str, dict]) -> dict | None:
        # First: exact mapping match
        for motif_id, meta in motifs.items():
            if target_lower in meta["mapping"]:
                return {"motif": motif_id, **meta, "hex": SFS_PALETTE.get(meta["palette"], "N/A")}
        # Second: archetype / operator semantic match
        for motif_id, meta in motifs.items():
            archetype = meta.get("archetype", "").lower()
            operator = meta.get("operator", "").lower()
            if target_lower in archetype or target_lower in operator:
                return {"motif": motif_id, **meta, "hex": SFS_PALETTE.get(meta["palette"], "N/A")}
        # Third: alias match
        for motif_id, meta in motifs.items():
            for alias in meta.get("aliases", []):
                if target_lower in alias.lower() or alias.lower() in target_lower:
                    return {"motif": motif_id, **meta, "hex": SFS_PALETTE.get(meta["palette"], "N/A")}
        return None

    best_egyptian = _search_axis(EGYPTIAN_MOTIFS)
    best_andean = _search_axis(ANDEAN_MOTIFS)

    result = {"target": target, "axis_filter": axis}

    if axis == "egyptian" and best_egyptian:
        result["primary"] = best_egyptian
        result["counterpart"] = best_andean
    elif axis == "andean" and best_andean:
        result["primary"] = best_andean
        result["counterpart"] = best_egyptian
    elif best_egyptian:
        result["primary"] = best_egyptian
        result["counterpart"] = best_andean
    elif best_andean:
        result["primary"] = best_andean
        result["counterpart"] = best_egyptian
    else:
        result["primary"] = None
        result["counterpart"] = None

    return result


def format_scan_report(scan_results: dict, balance: dict) -> str:
    """Format the full scan + balance report as markdown."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# SFA Cross-Reference Scan",
        f"",
        f"**Generated:** {ts}",
        f"**Tool:** `sfa_cross_reference.py --scan` (@SID: TOOL_SFA_CROSS_REFERENCE_V1)",
        f"",
        f"---",
        f"",
        f"## Balance Summary",
        f"",
        f"| Axis | Unique Motifs | Mentions | Ratio |",
        f"|------|--------------|----------|-------|",
        f"| Egyptian | {balance['egyptian_unique_count']} | {balance['egyptian_mentions']} | {balance['ratio_egyptian']:.1%} |",
        f"| Andean | {balance['andean_unique_count']} | {balance['andean_mentions']} | {balance['ratio_andean']:.1%} |",
        f"",
        f"**Verdict:** {balance['verdict']}",
        f"",
        f"---",
        f"",
    ]

    for src_id, data in scan_results.items():
        lines.append(f"## Source: `{src_id}` — {data['domain']}")
        lines.append(f"")
        lines.append(f"**Words:** {data['word_count']:,}")
        lines.append(f"**Egyptian motifs found:** {data['egyptian_count']} | **Andean:** {data['andean_count']}")
        lines.append(f"")

        if data["egyptian_motifs"] or data["andean_motifs"]:
            lines.append(f"| Motif | Axis | Mentions | BCE | Design Mapping | Palette | Hex |")
            lines.append(f"|-------|------|----------|-----|----------------|---------|-----|")
            for m in data["egyptian_motifs"] + data["andean_motifs"]:
                lines.append(
                    f"| {m['motif']} | {m['axis']} | {m['mentions']} | {m['bce']} "
                    f"| {m['mapping']} | {m['palette']} | `{m['hex']}` |"
                )
            lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # Egyptian motifs list
    lines.append(f"## Unique Egyptian Motifs ({balance['egyptian_unique_count']})")
    lines.append(f"")
    for m in balance["egyptian_unique"]:
        meta = EGYPTIAN_MOTIFS[m]
        lines.append(f"- **{m}** ({meta['bce']}) → {meta['mapping']} → `{SFS_PALETTE.get(meta['palette'], 'N/A')}`")
    lines.append(f"")

    # Andean motifs list
    lines.append(f"## Unique Andean Motifs ({balance['andean_unique_count']})")
    lines.append(f"")
    for m in balance["andean_unique"]:
        meta = ANDEAN_MOTIFS[m]
        lines.append(f"- **{m}** ({meta['bce']}) → {meta['mapping']} → `{SFS_PALETTE.get(meta['palette'], 'N/A')}`")
    lines.append(f"")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="SFA Cross-Reference Engine — Sister Ferrum Scoriae Abstraction"
    )
    parser.add_argument("--scan", action="store_true",
                        help="Scan all ANKH sources for motif vocabulary")
    parser.add_argument("--balance-audit", action="store_true",
                        help="Validate 50/50 Egypto-Andean equilibrium")
    parser.add_argument("--assign", type=str, metavar="TARGET",
                        help="Recommend motif for a design target")
    parser.add_argument("--axis", choices=["egyptian", "andean"],
                        help="Filter assignment to specific axis")
    parser.add_argument("--extract", type=str, metavar="ID",
                        help="Extract SSOT sections by character/protocol ID")
    parser.add_argument("--forge-digest", action="store_true",
                        help="Full pipeline: scan + balance + digest emission")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON instead of markdown")
    args = parser.parse_args()

    if not any([args.scan, args.balance_audit, args.assign,
                args.extract, args.forge_digest]):
        parser.print_help()
        return 1

    # ── Scan ──────────────────────────────────────────────────────────────
    if args.scan or args.forge_digest:
        print("═══ SFA Cross-Reference Scan ═══")
        print()
        scan_results = scan_all_sources()
        balance = compute_balance(scan_results)

        if args.json:
            print(json.dumps({"scan": scan_results, "balance": balance}, indent=2))
        else:
            for src_id, data in scan_results.items():
                eg = data["egyptian_count"]
                an = data["andean_count"]
                print(f"  📜 {src_id} ({data['domain']}): {data['word_count']:,} words — "
                      f"Egyptian: {eg} motifs, Andean: {an} motifs")

            print()
            print(f"  Egyptian unique: {balance['egyptian_unique_count']}/{len(EGYPTIAN_MOTIFS)}")
            print(f"  Andean unique:   {balance['andean_unique_count']}/{len(ANDEAN_MOTIFS)}")
            print(f"  Ratio:           {balance['ratio_egyptian']:.1%} / {balance['ratio_andean']:.1%}")
            print(f"  Verdict:         {balance['verdict']}")

        if args.forge_digest:
            report = format_scan_report(scan_results, balance)
            icons = get_icon_assignments()

            report += f"\n## Current Icon Assignments\n\n"
            report += f"| Metric | Count |\n|--------|-------|\n"
            for key, val in icons.items():
                report += f"| {key} | {val} |\n"
            report += f"\n---\n\n*Forged by SFA v1 — $sfs${{qmr}}+$tool${{SFA}}*\n"

            MAILBOX_DIR.mkdir(parents=True, exist_ok=True)
            digest_path = MAILBOX_DIR / "SFA_FORGE_DIGEST.md"
            digest_path.write_text(report, encoding="utf-8")
            print(f"\n  📨 Forge digest written: {digest_path}")

        if args.scan and not args.forge_digest:
            # Also write scan report to mailbox
            report = format_scan_report(scan_results, balance)
            MAILBOX_DIR.mkdir(parents=True, exist_ok=True)
            scan_path = MAILBOX_DIR / "SFA_CROSS_REFERENCE_SCAN.md"
            scan_path.write_text(report, encoding="utf-8")
            print(f"\n  📨 Scan report written: {scan_path}")

    # ── Balance Audit ─────────────────────────────────────────────────────
    if args.balance_audit and not args.forge_digest:
        print("═══ SFA Balance Audit ═══")
        print()
        scan_results = scan_all_sources()
        balance = compute_balance(scan_results)

        if args.json:
            print(json.dumps(balance, indent=2))
        else:
            print(f"  Egyptian: {balance['egyptian_unique_count']}/{len(EGYPTIAN_MOTIFS)} "
                  f"({balance['egyptian_mentions']} mentions)")
            print(f"  Andean:   {balance['andean_unique_count']}/{len(ANDEAN_MOTIFS)} "
                  f"({balance['andean_mentions']} mentions)")
            print(f"  Ratio:    {balance['ratio_egyptian']:.1%} E / {balance['ratio_andean']:.1%} A")
            print(f"  Verdict:  {balance['verdict']}")

    # ── Assign ────────────────────────────────────────────────────────────
    if args.assign:
        print(f"═══ SFA Motif Assignment: '{args.assign}' ═══")
        print()
        result = assign_motif(args.assign, args.axis)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["primary"]:
                p = result["primary"]
                print(f"  Primary:     {p['motif']} ({p['bce']})")
                print(f"  Mapping:     {p['mapping']}")
                print(f"  Palette:     {p['palette']} → {p['hex']}")
            else:
                print(f"  ⚠ No direct mapping found for '{args.assign}'")
                print(f"  Hint: try keywords like 'testing', 'data', 'build', 'storage', 'execution'")

            if result.get("counterpart"):
                c = result["counterpart"]
                print(f"  Counterpart: {c['motif']} ({c['bce']})")
                print(f"  Mapping:     {c['mapping']}")
                print(f"  Palette:     {c['palette']} → {c['hex']}")

    # ── Extract ───────────────────────────────────────────────────────────
    if args.extract:
        print(f"═══ SFA SSOT Extraction: '{args.extract}' ═══")
        print()
        sections = extract_ssot_sections(args.extract)

        if args.json:
            print(json.dumps({"id": args.extract, "sections": sections}, indent=2))
        else:
            if sections:
                print(f"  Found {len(sections)} relevant section(s):")
                print()
                for s in sections[:10]:  # Show first 10 in terminal
                    print(f"  {s[:200]}...")
                    print()
                if len(sections) > 10:
                    print(f"  ... and {len(sections) - 10} more (use --json for full output)")
            else:
                print(f"  No sections found for '{args.extract}'")

    return 0


if __name__ == "__main__":
    sys.exit(main())
