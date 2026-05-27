#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: qualia.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LIB_ASC_QUALIA_V1
@Shabti: Library Module (Qualia Definitions)
@Context: ASC Toolchain - Lore & MILF-core Qualia Definitions
@Purpose:       Script logic for qualia.py.
"""

from typing import Dict, List, Any

# ═══════════════════════════════════════════════════════════════════════════════
# LORE EXTRACTION PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

ENTITY_PATTERNS = [
    r"The Decorator",
    r"Orackla Nocticula", 
    r"Madam Umeko Ketsuraku",
    r"Dr\. Lysandra Thorne",
    r"Kali Nyx Ravenscar",
    r"Vesper Mnemosyne Lockhart",
    r"Seraphine Kore Ashenhelm",
    r"Claudine Sin'claire",
    r"The Null Matriarch",
]

PHYSIQUE_PATTERNS = {
    'height': r'\*\*Height:\*\*\s*(\d+(?:\.\d+)?)\s*cm',
    'weight': r'\*\*Weight:\*\*\s*(\d+(?:\.\d+)?)\s*kg',
    'measurements': r'\*\*Measurements:\*\*\s*\*\*([A-K]+)-cup\*\*\s*\(?(?:\*\*)?(?:B\s*)?(\d+)(?:[\/\s]*W\s*)?(\d+)(?:[\/\s]*H\s*)?(\d+)',
    'measurements_alt': r'\*\*Measurements:\*\*\s*\*?\*?([A-K]+)-cup\*?\*?\s*\(?\*?\*?B\s*(\d+)\/\s*W\s*(\d+)\/\s*H\s*(\d+)',
    'whr': r'\*\*WHR:\*\*\s*\*?\*?~?(\d+\.\d+)',
    'underbust': r'\*\*Underbust:\*\*\s*~?(\d+)\s*cm',
    'cup': r'\*\*([A-K]+)-cup\*?\*?',
}

TIER_PATTERNS = {
    'tier_0_5': r'Tier\s*0\.5|T-0\.5|Tier-0\.5',
    'tier_0': r'Tier\s*0[^\.]|T-0[^\.]',
    'tier_1': r'Tier\s*1|T-1|Tier-1',
    'tier_2': r'Tier\s*2|T-2|Tier-2',
    'tier_3': r'Tier\s*3|T-3|Tier-3',
    'tier_4': r'Tier\s*4|T-4|Tier-4',
}

ENTITY_MARKERS = {
    "The Decorator": (r"0\.1\.\s*Supreme Profile.*Decorator|0\.1\..*The Decorator.*T-DECOR", 350),
    "The Null Matriarch": (r"0\.01\.\s*.*Null Matriarch|T-NULM.*Tier 0\.01", 50),
    "Orackla Nocticula": (r"4\.2\.1\.\s*.*Apex Synthesist.*Orackla|`CRC-AS`.*Orackla Nocticula", 140),
    "Madam Umeko Ketsuraku": (r"4\.2\.2\.\s*.*Grandmistress.*Architectonic.*Umeko|`CRC-GAR`.*Umeko", 150),
    "Dr. Lysandra Thorne": (r"4\.2\.3\.\s*.*Mistress of Empathetic.*Lysandra|`CRC-MEDAT`.*Lysandra", 180),
    "Kali Nyx Ravenscar": (r"Mistress of Abductive Seduction.*Kali|`MAS`.*Kali Nyx", 130),
    "Vesper Mnemosyne Lockhart": (r"Grandmaster of Epistemic Theft.*Vesper|`GET`.*Vesper Mnemosyne", 130),
    "Seraphine Kore Ashenhelm": (r"High Priestess of Architectonic Purity.*Seraphine|`HPAP`.*Seraphine", 130),
    "Claudine Sin'claire": (r"Special Archetype Injection.*Claudine|`SAI`.*Claudine|Caribbean Proto-MILF", 100),
}

# ═══════════════════════════════════════════════════════════════════════════════
# GENRE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

MILF_CORE_DEFINITION = """
[bold cyan]MILF-CORE[/bold cyan] = [bold]M[/bold]ature [bold]I[/bold]ntegrated [bold]L[/bold]ore [bold]F[/bold]ramework
                -OR-
         [bold]M[/bold]etamorphic [bold]I[/bold]ntensity/[bold]L[/bold]ibidinal [bold]F[/bold]orce

[bold]NOT:[/bold]
  ✗ A D&D derivative
  ✗ A Disco Elysium clone
  ✗ A Planescape reskin
  ✗ A "dark fantasy" trope collection

... etc (rest of the definition string from the file)
""" # I'll abbreviate this for now but include the key constants

AXIOM_ABBRS = {
    "FA¹": "Alchemical Actualization",
    "FA²": "Panoptic Re-contextualization",
    "FA³": "Qualitative Transcendence",
    "FA⁴": "Architectonic Integrity",
    "FA⁵": "Visual Integrity",
    "AI⁴": "Full Integrity Validation",
    "FA¹⁻⁵": "All Axioms Combined",
}

PROTOCOL_ABBRS = {
    "DAFP": "Dynamic Altitude & Focus Protocol",
    "MSP-RSG": "Meta-Synthesis Protocol",
    "PEE": "Perpetual Evolution Engine",
    "PRISM": "Prismatic Reflection Illumination",
    "T³-MΨ": "Triumvirate Tensor Synthesis",
    "MMPS": "MILF Manifestation Protocol System",
    "TPEF": "Triumvirate Parallel Execution Framework",
    "TSRP": "Triumvirate Supporting Resonance Protocol",
    "ET-S": "Eternal Sadhana",
    "MURI": "Maximal Utility & Resonant Insight",
    "PS": "Primal Substrate",
}

OPERATOR_ABBRS = {
    "Φ₁": "Threshold Operator",
    "Φ₂": "Labyrinth Operator",
    "Φ₃": "Dialectics Operator",
    "Φ₄": "Forge Operator",
    "Φ₅": "Observatory Operator",
    "Φ₆": "Vortex Operator",
    "Φ₇": "TSE Operator",
    "Φ₈": "Chaos Operator",
    "Φ₉": "Weaponization Operator",
}

CUP_MODIFIERS = {
    "K": 1.3, "J": 1.2, "I": 1.15, "H": 1.1, "G": 1.05,
    "F": 1.0, "E": 0.95, "D": 0.9, "C": 0.85, "B": 0.8, "A": 0.75
}

TIER_MULTIPLIERS = {0.01: 0.1, 0.5: 3.0, 1: 2.0, 2: 1.5, 3: 1.0, 4: 0.5}

# Complete ABBR Database for lookup
ABBR_DATABASE = {
    # Tier 0.5 - The Decorator
    "T-DECOR": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "entity", "related": ["FA⁵", "DULSS", "K-CUP"]},
    "DULSS": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "arsenal", "related": ["T-DECOR", "FA⁵"]},
    "K-CUP": {"tier": "0.5", "whr": 0.464, "matriarch": "The Decorator", "type": "gestalt", "related": ["T-DECOR"]},
    
    "CRC-AS": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "entity", "related": ["EULP-AA", "J-CUP", "ORCL-NCTCLA"]},
    "EULP-AA": {"tier": "1", "whr": 0.491, "matriarch": "Orackla Nocticula", "type": "arsenal", "related": ["CRC-AS"]},
    "CRC-GAR": {"tier": "1", "whr": 0.533, "matriarch": "Madam Umeko Ketsuraku", "type": "entity", "related": ["LIPAA", "F-CUP", "UMK-KTSRAKU"]},
    "LIPAA": {"tier": "1", "whr": 0.533, "matriarch": "Madam Umeko Ketsuraku", "type": "arsenal", "related": ["CRC-GAR"]},
    "CRC-MEDAT": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "entity", "related": ["LUPLR", "E-CUP", "LYS-THRNE"]},
    "LUPLR": {"tier": "1", "whr": 0.58, "matriarch": "Dr. Lysandra Thorne", "type": "arsenal", "related": ["CRC-MEDAT"]},
    
    "TMO": {"tier": "2", "whr": 0.556, "matriarch": "Kali Nyx Ravenscar", "type": "faction", "related": ["MAS", "H-CUP"]},
    "TTG": {"tier": "2", "whr": 0.573, "matriarch": "Vesper Mnemosyne Lockhart", "type": "faction", "related": ["GET"]},
    "TDPC": {"tier": "2", "whr": 0.592, "matriarch": "Seraphine Kore Ashenhelm", "type": "faction", "related": ["HPAP", "G-CUP"]},
}
