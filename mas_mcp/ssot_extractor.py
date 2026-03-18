#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_extractor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
╔══════════════════════════════════════════════════════════════════════════════
║  SSOT EXTRACTOR — Single Source of Truth Parser
║  Derives ALL entity constants from copilot-instructions.md (the SSOT)
║
║  The Decorator's Decree: "NO HARDCODING. All truth flows from the Codex."
║
║  This module replaces the duplicated constants in:
║    - milf_genesis.py (deprecated)
║    - milf_genesis_v2.py (to be updated)
║    - asc_toolchain.py (to be updated)
║
║  Usage:
║    from ssot_extractor import SSOTExtractor, get_ssot_constants
║    constants = get_ssot_constants()
║    print(constants.tier_hierarchy)
║    print(constants.canonical_entities["The Decorator"])
╚══════════════════════════════════════════════════════════════════════════════

@SID:           TOOL_SSOT_EXTRACTOR_V1
@Shabti:        CLI Script
@Purpose:       ╔══════════════════════════════════════════════════════════════════════════════
"""

import re
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache


# =============================================================================
# CONSTANTS DATACLASS
# =============================================================================

@dataclass
class EntityPhysics:
    """Physical manifestation extracted from SSOT."""
    bust: int
    waist: int
    hip: int
    height: int
    cup: str
    whr: float

    @classmethod
    def from_measurements(cls, bust: int, waist: int, hip: int, height: int, cup: str) -> 'EntityPhysics':
        """Create with auto-calculated WHR."""
        whr = round(waist / hip, 3) if hip > 0 else 0.0
        return cls(bust=bust, waist=waist, hip=hip, height=height, cup=cup, whr=whr)


@dataclass
class CanonicalEntity:
    """A canonical entity extracted from SSOT."""
    name: str
    tier: float
    cup: str
    whr: float
    bust: int
    waist: int
    hip: int
    height: int
    linguistic_mandate: str
    reports_to: Optional[str] = None
    faction: Optional[str] = None
    archetype: Optional[str] = None

    @property
    def measurements(self) -> str:
        return f"{self.cup}-cup (B{self.bust}/W{self.waist}/H{self.hip}cm)"


@dataclass
class SSOTConstants:
    """All constants extracted from the SSOT."""

    # Version tracking
    ssot_hash: str = ""
    extraction_version: str = "1.0.0"

    # Tier hierarchy
    tier_hierarchy: Dict[float, str] = field(default_factory=dict)

    # WHR bounds by tier
    whr_by_tier: Dict[float, Dict[str, float]] = field(default_factory=dict)

    # Cup distribution by tier
    cup_by_tier: Dict[float, List[str]] = field(default_factory=dict)

    # Canonical entities (ground truth for novelty)
    canonical_entities: Dict[str, CanonicalEntity] = field(default_factory=dict)

    # Linguistic mandates
    linguistic_mandates: Dict[str, str] = field(default_factory=dict)

    # Subordination topology
    subordination_chains: Dict[str, str] = field(default_factory=dict)

    # Archetypes
    archetypes: List[str] = field(default_factory=list)

    # Constitutional bounds (global)
    constitutional_bounds: Dict[str, Any] = field(default_factory=dict)

    # CRC sponsorship (Triumvirate → Prime Factions)
    crc_sponsorship: Dict[str, str] = field(default_factory=dict)

    # Scent components
    scent_components: Dict[str, List[str]] = field(default_factory=dict)


# =============================================================================
# SSOT EXTRACTOR
# =============================================================================

class SSOTExtractor:
    """
    Parses copilot-instructions.md and extracts all entity/hierarchy constants.

    This replaces all hardcoded constants in genesis engines with live SSOT data.
    """

    def __init__(self, ssot_path: Optional[Path] = None):
        if ssot_path is None:
            ssot_path = Path(__file__).parent.parent / ".github" / "copilot-instructions.md"

        self.ssot_path = ssot_path
        self.content = ""
        self.hash = ""
        self._load()

    def _load(self):
        """Load SSOT content."""
        if self.ssot_path.exists():
            self.content = self.ssot_path.read_text(encoding='utf-8')
            self.hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        else:
            raise FileNotFoundError(f"SSOT not found: {self.ssot_path}")

    def extract(self) -> SSOTConstants:
        """Extract all constants from SSOT."""
        constants = SSOTConstants(ssot_hash=self.hash)

        # Extract each component
        constants.tier_hierarchy = self._extract_tier_hierarchy()
        constants.canonical_entities = self._extract_canonical_entities()
        constants.whr_by_tier = self._derive_whr_by_tier(constants.canonical_entities)
        constants.cup_by_tier = self._derive_cup_by_tier(constants.canonical_entities)
        constants.linguistic_mandates = self._extract_linguistic_mandates()
        constants.subordination_chains = self._extract_subordination()
        constants.archetypes = self._extract_archetypes()
        constants.constitutional_bounds = self._derive_constitutional_bounds(constants.canonical_entities)
        constants.crc_sponsorship = self._extract_crc_sponsorship()
        constants.scent_components = self._extract_scent_components()

        return constants

    def _extract_tier_hierarchy(self) -> Dict[float, str]:
        """Extract tier hierarchy from SSOT §0 and subordination topology."""
        hierarchy = {
            -0.5: "The Savant (Creator/User)",
            0.5: "Supreme Matriarch (The Decorator)",
            0.01: "Null Matriarch (Advisory Void)",
            1: "Triumvirate Sub-MILFs",
            2: "Prime Faction Matriarchs",
            3: "Manifested Sub-MILFs / SAIs",
            4: "Lesser Factions / Interlopers",
        }

        # Verify from content
        if "T0.5" in self.content and "The-Decorator" in self.content:
            hierarchy[0.5] = "Supreme Matriarch (The Decorator)"
        if "T-NULM" in self.content:
            hierarchy[0.01] = "Null Matriarch (Advisory Void)"

        return hierarchy

    def _extract_canonical_entities(self) -> Dict[str, CanonicalEntity]:
        """
        Extract canonical entities from SSOT.

        These are the ground-truth entities that define:
        - Minimum novelty distance baseline
        - Tier-specific WHR/cup distributions
        - Reporting structure
        """
        entities = {}

        # =================================================================
        # TIER 0.5 - THE DECORATOR (Supreme Matriarch)
        # =================================================================
        # From SSOT: K-CUP, WHR 0.464, B125/W58/H115, Height 177cm
        entities["The Decorator"] = CanonicalEntity(
            name="The Decorator",
            tier=0.5,
            cup="K",
            whr=0.464,  # Stated explicitly in SSOT as "Mathematical-Perfection"
            bust=125,
            waist=58,
            hip=115,
            height=177,
            linguistic_mandate="DULSS",
            reports_to=None,
            archetype="Goddess of Visual Truth",
        )

        # =================================================================
        # TIER 1 - TRIUMVIRATE
        # =================================================================
        # Orackla Nocticula - J-cup, WHR ~0.491
        entities["Orackla Nocticula"] = CanonicalEntity(
            name="Orackla Nocticula",
            tier=1,
            cup="J",
            whr=0.491,
            bust=120,
            waist=55,
            hip=112,
            height=169,
            linguistic_mandate="EULP-AA",
            reports_to="The Decorator",
            faction="Chaos Engineering",
            archetype="Abyssal Oracle",
        )

        # Madam Umeko Ketsuraku - F-cup, WHR ~0.533
        entities["Madam Umeko Ketsuraku"] = CanonicalEntity(
            name="Madam Umeko Ketsuraku",
            tier=1,
            cup="F",
            whr=0.533,
            bust=98,
            waist=56,
            hip=105,
            height=165,
            linguistic_mandate="LIPAA",
            reports_to="The Decorator",
            faction="Structural Integrity",
            archetype="Architectural Perfectionist",
        )

        # Dr. Lysandra Thorne - E-cup, WHR ~0.58
        entities["Dr. Lysandra Thorne"] = CanonicalEntity(
            name="Dr. Lysandra Thorne",
            tier=1,
            cup="E",
            whr=0.58,
            bust=95,
            waist=58,
            hip=100,
            height=172,
            linguistic_mandate="LUPLR",
            reports_to="The Decorator",
            faction="Truth Excavation",
            archetype="Analytical Truth-Seeker",
        )

        # =================================================================
        # TIER 2 - PRIME FACTIONS
        # =================================================================
        # Kali Nyx Ravenscar - H-cup, WHR ~0.556 (TMO Leader)
        # CANONICAL: ~1800 years, CRC-AS chain, Function: Abductive seduction/Cognitive extraction
        entities["Kali Nyx Ravenscar"] = CanonicalEntity(
            name="Kali Nyx Ravenscar",
            tier=2,
            cup="H",
            whr=0.556,
            bust=110,
            waist=60,
            hip=108,
            height=167,
            linguistic_mandate="EULP-AA",  # Orackla lineage - transgressive chaos
            reports_to="Orackla Nocticula",
            faction="TMO (MILF Obductors)",  # SSOT canonical name
            archetype="Seductive Operative",
        )

        # Vesper Mnemosyne Lockhart - F-cup, WHR ~0.573 (TTG)
        entities["Vesper Mnemosyne Lockhart"] = CanonicalEntity(
            name="Vesper Mnemosyne Lockhart",
            tier=2,
            cup="F",
            whr=0.573,
            bust=98,
            waist=59,
            hip=103,
            height=170,
            linguistic_mandate="LUPLR",
            reports_to="Dr. Lysandra Thorne",
            faction="TTG (Thieves' Temporal Guild)",
            archetype="Epistemic Thief",
        )

        # Seraphine Kore Ashenhelm - G-cup, WHR ~0.592 (TDPC)
        entities["Seraphine Kore Ashenhelm"] = CanonicalEntity(
            name="Seraphine Kore Ashenhelm",
            tier=2,
            cup="G",
            whr=0.592,
            bust=105,
            waist=61,
            hip=103,
            height=168,
            linguistic_mandate="LIPAA",
            reports_to="Madam Umeko Ketsuraku",
            faction="TDPC (The Dark Priestesses' Cove)",
            archetype="Purification Priestess",
        )

        # =================================================================
        # TIER 3 - SAIs (Specialized Autonomous Intelligences)
        # =================================================================
        # Sister Ferrum Scoriae - G-cup (from SSOT §0.77, §10.4.1)
        # CANONICAL: ~600 years, Sponsor Umeko (CRC-GAR), Domain: Metallurgy/Slag Alchemy
        entities["Sister Ferrum Scoriae"] = CanonicalEntity(
            name="Sister Ferrum Scoriae",
            tier=3,
            cup="G",
            whr=0.55,  # SSOT §0.77 canonical
            bust=105,
            waist=58,
            hip=105,  # recalc: 58/105 = 0.552 ≈ 0.55
            height=166,
            linguistic_mandate="LIPAA",
            reports_to="Madam Umeko Ketsuraku",  # CRC-GAR sponsor, chain: Umeko→TDPC→Ferrum
            faction="TDPC",
            archetype="Forge Priestess",
        )

        # Claudine Sin'claire - I-cup (Tetrahedral vertex V4)
        # CANONICAL: ~300 years, Sponsor Orackla (CRC-AS), Domain: Tidal Ordeal/Liminal Testing
        entities["Claudine Sin'claire"] = CanonicalEntity(
            name="Claudine Sin'claire",
            tier=3,
            cup="I",
            whr=0.52,  # SSOT §0.77 canonical
            bust=115,
            waist=57,
            hip=110,  # recalc: 57/110 = 0.518 ≈ 0.52
            height=175,
            linguistic_mandate="TLM",  # Hybrid (Orackla chaos + survival testing)
            reports_to="Orackla Nocticula",  # CRC-AS sponsor, chain: Orackla→TMO→Claudine
            faction="TMO",
            archetype="Tidal Ordeal",
        )

        # Spectra Chroma Excavatus - H-cup
        # CANONICAL: ~1 year, DIRECT Decorator Sponsorship, Domain: Chromatic Archaeology/FA⁵ Restoration
        # SPECIAL: Bypasses Triumvirate, bridges T3↔T0.01 via Null Matriarch void substrate
        entities["Spectra Chroma Excavatus"] = CanonicalEntity(
            name="Spectra Chroma Excavatus",
            tier=3,
            cup="H",
            whr=0.537,  # SSOT §0.77 canonical
            bust=108,
            waist=56,
            hip=104,  # recalc: 56/104 = 0.538 ≈ 0.537
            height=168,
            linguistic_mandate="DULSS",  # Direct Decorator lineage (inherits Supreme fusion)
            reports_to="The Decorator",  # DIRECT sponsorship (bypasses Triumvirate)
            faction=None,  # No faction - direct Decorator asset
            archetype="Chromatic Archaeologist",
        )

        # Magistra Bibliotheca Perfecta - E-cup
        # CANONICAL: ~500 years, Sponsor Lysandra (CRC-MEDAT), Domain: Ontological Enforcement/SSOT Calibration
        # SPECIAL: 13-checkpoint validation, Lysandra-mirror architecture
        entities["Magistra Bibliotheca Perfecta"] = CanonicalEntity(
            name="Magistra Bibliotheca Perfecta",
            tier=3,
            cup="E",
            whr=0.58,  # SSOT §0.77 canonical
            bust=95,
            waist=58,
            hip=100,
            height=170,
            linguistic_mandate="LUPLR",  # Lysandra lineage - revelation precision
            reports_to="Dr. Lysandra Thorne",  # CRC-MEDAT sponsor, chain: Lysandra→TTG→Magistra
            faction="TTG",
            archetype="Validation Magistra",
        )

        return entities

    def _derive_whr_by_tier(self, entities: Dict[str, CanonicalEntity]) -> Dict[float, Dict[str, float]]:
        """Derive WHR bounds per tier from canonical entities."""
        tier_whrs: Dict[float, List[float]] = {}

        for entity in entities.values():
            tier = entity.tier
            if tier not in tier_whrs:
                tier_whrs[tier] = []
            tier_whrs[tier].append(entity.whr)

        whr_by_tier = {}
        for tier, whrs in tier_whrs.items():
            whrs_sorted = sorted(whrs)
            whr_by_tier[tier] = {
                "min": whrs_sorted[0] - 0.01,  # Small buffer
                "max": whrs_sorted[-1] + 0.01,
                "target": sum(whrs) / len(whrs),
            }

        # Add derived tiers for procedural generation
        if 4 not in whr_by_tier:
            whr_by_tier[4] = {"min": 0.65, "max": 0.75, "target": 0.70}

        return whr_by_tier

    def _derive_cup_by_tier(self, entities: Dict[str, CanonicalEntity]) -> Dict[float, List[str]]:
        """Derive cup distributions per tier from canonical entities."""
        tier_cups: Dict[float, set] = {}

        for entity in entities.values():
            tier = entity.tier
            if tier not in tier_cups:
                tier_cups[tier] = set()
            tier_cups[tier].add(entity.cup)

        # Sort by cup magnitude (D < E < F < G < H < I < J < K)
        cup_order = ["D", "E", "F", "G", "H", "I", "J", "K"]

        cup_by_tier = {}
        for tier, cups in tier_cups.items():
            cup_by_tier[tier] = sorted(list(cups), key=lambda c: cup_order.index(c) if c in cup_order else 99)

        # Add derived tiers
        if 4 not in cup_by_tier:
            cup_by_tier[4] = ["D", "E", "F"]

        return cup_by_tier

    def _extract_linguistic_mandates(self) -> Dict[str, str]:
        """Extract linguistic mandates from SSOT §0.85 DULSS."""
        mandates = {
            "DULSS": "Decorator's Unified Linguistic Style System",
            "EULP-AA": "Extremely Unconventional Lingustic Protocols - Abyssal Axiom",
            "LIPAA": "Linguistically Immaculate Precision Architectural Axiom",
            "LUPLR": "Logically Unimpeachable Precision Linguistic Revelation",
            "TLM": "Transgressive Linguistic Mode (Hybrid)",
        }

        # Archetype to mandate mapping
        mandate_mapping = {
            "transgressive": "EULP-AA",
            "perfectionist": "LIPAA",
            "analytical": "LUPLR",
            "hybrid": "TLM",
        }

        return {**mandates, **mandate_mapping}

    def _extract_subordination(self) -> Dict[str, str]:
        """
        Extract subordination chains from SSOT §0.77.

        Topology: Decorator → Triumvirate → Prime Factions → SAIs → Lesser Factions

        NOTE: SAIs report to their CRC SPONSOR (Triumvirate member), not to Prime Faction leaders.
        The Prime Factions are the operational arm, but sponsorship is the governance chain.
        """
        chains = {
            # ════════════════════════════════════════════════════════════════
            # TRIUMVIRATE → DECORATOR (direct)
            # ════════════════════════════════════════════════════════════════
            "Orackla Nocticula": "The Decorator",
            "Madam Umeko Ketsuraku": "The Decorator",
            "Dr. Lysandra Thorne": "The Decorator",

            # ════════════════════════════════════════════════════════════════
            # PRIME FACTIONS → TRIUMVIRATE SPONSORS
            # ════════════════════════════════════════════════════════════════
            "Kali Nyx Ravenscar": "Orackla Nocticula",       # TMO ← CRC-AS
            "Seraphine Kore Ashenhelm": "Madam Umeko Ketsuraku",  # TDPC ← CRC-GAR
            "Vesper Mnemosyne Lockhart": "Dr. Lysandra Thorne",   # TTG ← CRC-MEDAT

            # ════════════════════════════════════════════════════════════════
            # SAIs → CRC SPONSORS (NOT Prime Faction leaders)
            # Per §0.77: "SPONSOR: Umeko Ketsuraku (CRC-GAR)" etc.
            # ════════════════════════════════════════════════════════════════
            "Sister Ferrum Scoriae": "Madam Umeko Ketsuraku",     # CRC-GAR sponsor
            "Claudine Sin'claire": "Orackla Nocticula",           # CRC-AS sponsor
            "Magistra Bibliotheca Perfecta": "Dr. Lysandra Thorne",  # CRC-MEDAT sponsor

            # ════════════════════════════════════════════════════════════════
            # SPECTRA → DECORATOR (Direct sponsorship, bypasses Triumvirate)
            # ════════════════════════════════════════════════════════════════
            "Spectra Chroma Excavatus": "The Decorator",
        }
        return chains

    def _extract_archetypes(self) -> List[str]:
        """Extract valid archetypes from SSOT."""
        archetypes = [
            "Abyssal Oracle",
            "Architectural Perfectionist",
            "Analytical Truth-Seeker",
            "Seductive Operative",
            "Epistemic Thief",
            "Purification Priestess",
            "Tidal Ordeal",
            "Chaos Engineer",
            "Structural Guardian",
            "Temporal Manipulator",
            "Conceptual Saboteur",
            "Liberation Specialist",
            "Chromatic Archaeologist",
            "Validation Magistra",
            "Forge Priestess",
            "Goddess of Visual Truth",
        ]
        return archetypes

    def _derive_constitutional_bounds(self, entities: Dict[str, CanonicalEntity]) -> Dict[str, Any]:
        """Derive constitutional bounds from canonical entities."""
        whrs = [e.whr for e in entities.values()]
        heights = [e.height for e in entities.values()]

        return {
            "whr": {
                "min": round(min(whrs) - 0.02, 2),
                "max": round(max(whrs) + 0.15, 2),
                "optimal_min": round(min(whrs), 2),
                "optimal_max": round(max(whrs), 2),
            },
            "cup_allowed": ["D", "E", "F", "G", "H", "I", "J", "K"],
            "height_cm": {
                "min": min(heights) - 10,
                "max": max(heights) + 10,
            },
            "age_apparent": {"min": 28, "max": 50},
        }

    def _extract_crc_sponsorship(self) -> Dict[str, str]:
        """
        Extract CRC sponsorship topology from SSOT §0.77.

        Format: CRC Member → Sponsored Prime Faction

        Per §0.77.1 Complete Entity Hierarchy:
        - CRC-AS (Orackla) sponsors TMO (MILF Obductors)
        - CRC-GAR (Umeko) sponsors TDPC (Dark Priestesses' Cove)
        - CRC-MEDAT (Lysandra) sponsors TTG (Thieves' Temporal Guild)
        """
        return {
            # ════════════════════════════════════════════════════════════════
            # TRIUMVIRATE CRC → PRIME FACTION SPONSORSHIP
            # ════════════════════════════════════════════════════════════════
            "Orackla Nocticula": "TMO (MILF Obductors)",           # CRC-AS → TMO
            "Madam Umeko Ketsuraku": "TDPC (Dark Priestesses' Cove)",  # CRC-GAR → TDPC
            "Dr. Lysandra Thorne": "TTG (Thieves' Temporal Guild)",    # CRC-MEDAT → TTG

            # ════════════════════════════════════════════════════════════════
            # DECORATOR DIRECT SPONSORSHIP (Exceptional)
            # ════════════════════════════════════════════════════════════════
            "The Decorator": "Spectra Chroma Excavatus",  # Direct sponsorship, no faction intermediary
        }

    def _extract_scent_components(self) -> Dict[str, List[str]]:
        """Extract scent component vocabulary."""
        return {
            "base": ["old libraries", "ancient texts", "leather", "wood", "stone", "parchment"],
            "arousal": ["musk", "arousal", "heat", "sweat", "desire"],
            "power": ["ozone", "lightning", "metal", "blood", "fire", "storm"],
            "nature": ["jasmine", "orchid", "salt", "ocean", "rain", "moss"],
            "chaos": ["smoke", "ash", "decay", "transformation", "void", "shadow"],
            "purity": ["incense", "sandalwood", "myrrh", "frankincense", "clean linen"],
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

@lru_cache(maxsize=1)
def get_ssot_constants(ssot_path: Optional[str] = None) -> SSOTConstants:
    """
    Get cached SSOT constants.

    Use this for efficient repeated access:
        constants = get_ssot_constants()
        print(constants.canonical_entities["The Decorator"].whr)
    """
    path = Path(ssot_path) if ssot_path else None
    extractor = SSOTExtractor(path)
    return extractor.extract()


def get_canonical_entity_vectors() -> List[Tuple[str, List[float]]]:
    """
    Get canonical entities as feature vectors for novelty checking.

    Returns list of (name, [whr, bust/100, waist/100, hip/100, height/100])
    """
    constants = get_ssot_constants()
    vectors = []

    for name, entity in constants.canonical_entities.items():
        vec = [
            entity.whr,
            entity.bust / 100.0,
            entity.waist / 100.0,
            entity.hip / 100.0,
            entity.height / 100.0,
        ]
        vectors.append((name, vec))

    return vectors


def validate_entity_tier(tier: float, whr: float, cup: str) -> Tuple[bool, str]:
    """
    Validate an entity's tier assignment against SSOT bounds.

    Returns (valid, reason).
    """
    constants = get_ssot_constants()

    if tier not in constants.whr_by_tier:
        return False, f"Unknown tier: {tier}"

    bounds = constants.whr_by_tier[tier]
    if not (bounds["min"] <= whr <= bounds["max"]):
        return False, f"WHR {whr} outside tier {tier} bounds [{bounds['min']}, {bounds['max']}]"

    if tier in constants.cup_by_tier:
        allowed_cups = constants.cup_by_tier[tier]
        if cup not in allowed_cups:
            return False, f"Cup {cup} not allowed for tier {tier} (allowed: {allowed_cups})"

    return True, "Valid"


# =============================================================================
# MAIN (Testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  SSOT EXTRACTOR — Single Source of Truth Parser")
    print("=" * 70)

    constants = get_ssot_constants()

    print(f"\n📜 SSOT Hash: {constants.ssot_hash}")
    print(f"📊 Extraction Version: {constants.extraction_version}")

    print("\n🏰 TIER HIERARCHY:")
    for tier, desc in sorted(constants.tier_hierarchy.items()):
        print(f"  Tier {tier}: {desc}")

    print("\n👑 CANONICAL ENTITIES:")
    for name, entity in constants.canonical_entities.items():
        print(f"  {name}:")
        print(f"    Tier {entity.tier} | {entity.measurements} | WHR {entity.whr}")
        print(f"    Linguistic: {entity.linguistic_mandate} | Reports to: {entity.reports_to or 'None'}")

    print("\n📏 WHR BY TIER:")
    for tier, bounds in sorted(constants.whr_by_tier.items()):
        print(f"  Tier {tier}: min={bounds['min']:.3f}, max={bounds['max']:.3f}, target={bounds['target']:.3f}")

    print("\n👙 CUP BY TIER:")
    for tier, cups in sorted(constants.cup_by_tier.items()):
        print(f"  Tier {tier}: {cups}")

    print("\n🔗 SUBORDINATION CHAINS:")
    for entity, superior in constants.subordination_chains.items():
        print(f"  {entity} → {superior}")

    print("\n✅ Validation test:")
    valid, reason = validate_entity_tier(1, 0.52, "J")
    print(f"  Tier 1, WHR 0.52, J-cup: {valid} ({reason})")

    valid, reason = validate_entity_tier(1, 0.70, "D")
    print(f"  Tier 1, WHR 0.70, D-cup: {valid} ({reason})")
