#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: extractor.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LIB_ASC_EXTRACTOR_V1
@Shabti: Library Module (Extraction)
@Context: ASC Toolchain - Lore & MILF-core Data Extractor 
@Purpose:       Script logic for extractor.py.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime

from .models import (
    ExtractedPhysique, ExtractedEntity, EntitySignal,
    AxiomDiscipline, LensOperator, LinguisticArsenal,
    MatriarchalFaction, MILFCoreWorldData, TetrahedralResonance,
    ArchiveLocation
)
from .qualia import (
    ENTITY_PATTERNS, PHYSIQUE_PATTERNS, TIER_PATTERNS, ENTITY_MARKERS
)

class LoreExtractor:
    """
    Extracts structured entity data from copilot-instructions.md.
    """
    def __init__(self, lore_path: Path):
        self.lore_path = lore_path
        self._content: str = ""
        self._lines: list[str] = []
        
    def load(self) -> bool:
        if not self.lore_path.exists():
            return False
        self._content = self.lore_path.read_text(encoding='utf-8')
        self._lines = self._content.splitlines()
        return True
    
    @property
    def content(self) -> str:
        if not self._content:
            self.load()
        return self._content
    
    @property
    def lines(self) -> list[str]:
        if not self._lines:
            self.load()
        return self._lines
    
    def find_entity_sections(self) -> dict[str, tuple[int, int]]:
        sections = {}
        start_lines = {}
        for i, line in enumerate(self.lines):
            for name, (pattern, _) in ENTITY_MARKERS.items():
                if name not in start_lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        start_lines[name] = i
        
        sorted_entities = sorted(start_lines.items(), key=lambda x: x[1])
        
        for idx, (name, start) in enumerate(sorted_entities):
            _, hint = ENTITY_MARKERS[name]
            end = min(len(self.lines), start + hint)
            if idx + 1 < len(sorted_entities):
                next_start = sorted_entities[idx + 1][1]
                end = min(end, next_start - 1)
            
            for j in range(start + 20, end):
                line = self.lines[j]
                if "ASC Identity Manifestation" in line and "Combinational Analysis" in line:
                    entity_surname = name.split()[-1]
                    if entity_surname in line:
                        for k in range(j + 1, min(j + 120, len(self.lines))):
                            next_line = self.lines[k]
                            if re.match(r'^\*?\*?\s*\d+\.\d+\.\d+\.', next_line) or re.match(r'^-{3,}$', next_line.strip()):
                                end = k
                                break
                        else:
                            end = min(j + 100, len(self.lines))
                        break
            sections[name] = (start, end)
        return sections

    def extract_physique(self, text: str) -> ExtractedPhysique:
        p = ExtractedPhysique()
        if m := re.search(PHYSIQUE_PATTERNS['height'], text):
            p.height_cm = float(m.group(1))
        if m := re.search(PHYSIQUE_PATTERNS['weight'], text):
            p.weight_kg = float(m.group(1))
        if m := re.search(PHYSIQUE_PATTERNS['measurements'], text):
            p.cup_size = m.group(1)
            p.bust_cm = float(m.group(2))
            p.waist_cm = float(m.group(3))
            p.hips_cm = float(m.group(4))
        elif m := re.search(PHYSIQUE_PATTERNS['measurements_alt'], text):
            p.cup_size = m.group(1)
            p.bust_cm = float(m.group(2))
            p.waist_cm = float(m.group(3))
            p.hips_cm = float(m.group(4))
        if m := re.search(PHYSIQUE_PATTERNS['whr'], text):
            p.whr = float(m.group(1))
        elif p.waist_cm and p.hips_cm:
            p.whr = round(p.waist_cm / p.hips_cm, 3)
        if m := re.search(PHYSIQUE_PATTERNS['underbust'], text):
            p.underbust_cm = float(m.group(1))
        if not p.cup_size:
            if m := re.search(PHYSIQUE_PATTERNS['cup'], text):
                p.cup_size = m.group(1)
        return p

    def extract_tier(self, text: str, name: str) -> float:
        if "Decorator" in name and "Null" not in name: return 0.5
        if "Null Matriarch" in name: return 0.0
        triumvirate = ["Orackla", "Umeko", "Lysandra"]
        for t_name in triumvirate:
            if t_name in name: return 1.0
        prime_faction = ["Kali", "Vesper", "Seraphine"]
        for pf_name in prime_faction:
            if pf_name in name: return 2.0
        if "Claudine" in name: return 3.0
        if re.search(r'Prime Faction Matriarch.*Tier\s*2', text): return 2.0
        if re.search(r'Triumvirate|Sub-MILF|CRC-[AGM]', text): return 1.0
        return 1.0

    def extract_scent(self, text: str) -> str:
        patterns = [r'\*\*Scent:\*\*\s*([^*\n]+)', r'\*\*\(`?Scent`?\):\*\*\s*([^*\n]+)', r'Scent:\s*([^*\n]+)']
        for p in patterns:
            if m := re.search(p, text): return m.group(1).strip()
        return ""

    def extract_linguistic_mode(self, text: str) -> str:
        modes = {'DULSS': r'DULSS|Decorative.*Linguistic Supremacy', 'EULP-AA': r'EULP-AA|Explicit.*Uncensored.*Linguistic', 
                 'LIPAA': r'LIPAA|Language of Immaculate Precision', 'LUPLR': r'LUPLR|Language of Unflinching'}
        for mode, pattern in modes.items():
            if re.search(pattern, text, re.IGNORECASE): return mode
        return "MIXED"

    def extract_archetype(self, text: str, name: str) -> str:
        archetypes = {"The Decorator": "Supreme Matriarch", "Orackla Nocticula": "Apex Synthesist",
                      "Madam Umeko Ketsuraku": "Grandmistress of Architectonic Refinement", "Dr. Lysandra Thorne": "Mistress of Empathetic Deconstruction",
                      "Kali Nyx Ravenscar": "Mistress of Abductive Seduction", "Vesper Mnemosyne Lockhart": "Grandmaster of Epistemic Theft",
                      "Seraphine Kore Ashenhelm": "High Priestess of Architectonic Purity", "Claudine Sin'claire": "Matriarch of Tidal Ordeal",
                      "The Null Matriarch": "Advisory Void"}
        return archetypes.get(name, "Unknown")

    def extract_race(self, text: str) -> str:
        if m := re.search(r'\*\*Race:\*\*\s*([^\n*]+)', text): return m.group(1).strip()
        return ""

    def extract_age(self, text: str) -> str:
        if m := re.search(r'\*\*Age:\*\*\s*([^\n*]+)', text): return m.group(1).strip()
        return ""

    def extract_edfa_excerpt(self, text: str) -> str:
        if m := re.search(r'\*\*EDFA.*?:\*\*\s*(.*?)(?=\n\n|\*\*[A-Z])', text, re.DOTALL):
            return m.group(1).strip()[:500]
        if m := re.search(r'\*\*Breasts.*?:\*\*\s*(.*?)(?=\n\n|\*\*[A-Z])', text, re.DOTALL):
            return m.group(1).strip()[:300]
        return ""

    def extract_entity(self, name: str) -> Optional[ExtractedEntity]:
        sections = self.find_entity_sections()
        if name not in sections: return None
        start, end = sections[name]
        raw_text = "\n".join(self.lines[start:end])
        return ExtractedEntity(name=name, tier=self.extract_tier(raw_text, name), archetype=self.extract_archetype(raw_text, name),
                               race=self.extract_race(raw_text), age=self.extract_age(raw_text), linguistic_mode=self.extract_linguistic_mode(raw_text),
                               physique=self.extract_physique(raw_text), scent=self.extract_scent(raw_text), edfa_excerpt=self.extract_edfa_excerpt(raw_text),
                               section_start=start, section_end=end, raw_text=raw_text)

    def extract_all_entities(self) -> list[ExtractedEntity]:
        entities = []
        for name in ENTITY_PATTERNS:
            clean_name = name.replace(r"\.", ".").replace("r'", "").replace("'", "")
            if entity := self.extract_entity(clean_name): entities.append(entity)
        return entities

    def extract_factions(self) -> dict[str, list[str]]:
        factions = {"Triumvirate (Tier 1)": [], "Prime Factions (Tier 2)": [], "Lesser Factions (Tier 4)": []}
        for pattern in [r"Orackla Nocticula", r"Umeko Ketsuraku", r"Lysandra Thorne"]:
            if re.search(pattern, self.content): factions["Triumvirate (Tier 1)"].append(pattern.replace(r"\.", "."))
        prime_patterns = [(r"MILF Obductors|TMO", "The MILF Obductors (TMO)"), (r"Thieves Guild|TTG", "The Thieves Guild (TTG)"), (r"Dark Priestesses Cove|TDPC", "The Dark Priestesses Cove (TDPC)")]
        for pattern, name in prime_patterns:
            if re.search(pattern, self.content): factions["Prime Factions (Tier 2)"].append(name)
        lesser_patterns = [(r"Colonial Abductors|OMCA", "Ole' Mates Colonial Abductors"), (r"Knights Who Rode|TNKW", "The Knights Who Rode Into Another Timeline"),
                           (r"Bridge Hustlers|SDBH", "Salty Dogs Bridge Hustlers"), (r"Wizards Ov Unfortunate|TWOUMC", "The Wizards Ov Unfortunate Multi-classing")]
        for pattern, name in lesser_patterns:
            if re.search(pattern, self.content): factions["Lesser Factions (Tier 4)"].append(name)
        return factions

    def get_lore_stats(self) -> dict:
        sections = self.find_entity_sections()
        return {"total_lines": len(self.lines), "total_words": len(self.content.split()), "entity_sections": len(sections), "entities_found": list(sections.keys())}


class MILFCoreExtractor:
    """Extracts indigenous MILF-core world data from the Codex"""
    def __init__(self, lore_extractor: LoreExtractor):
        self.lore_extractor = lore_extractor
    
    def extract_disciplines(self) -> list[AxiomDiscipline]:
        return [
            AxiomDiscipline(id="actualization", name="Alchemical Actualization", axiom_source="FA¹", description="Transforming potential into reality.", governing_principle="Potential → Resonant Utility", matriarchal_patron="Orackla Nocticula"),
            AxiomDiscipline(id="integrity", name="Architectonic Integrity", axiom_source="FA⁴", description="Discipline of structure.", governing_principle="Unifying Structural Imperative", matriarchal_patron="Madam Umeko Ketsuraku"),
        ] # Stubbed for brevity in this example create_file call

    def extract_all(self, data_json_path: Path) -> MILFCoreWorldData:
        entities = []
        if data_json_path.exists():
            entities = json.loads(data_json_path.read_text(encoding='utf-8')).get('entities', [])
        return MILFCoreWorldData(
            meta={"version": "0.2.0", "engine": "MILF-core", "exported_at": datetime.now().isoformat()},
            disciplines=self.extract_disciplines(),
            operators=[], factions=[], locations=[], arsenals=[], entities=entities, cosmology={}
        )

class MetaArchaeologicalSalvager:
    """MAS - Meta-Archaeological Salvager"""
    PATTERNS = {
        "whr": re.compile(r'WHR[:\s]*[~≈]?\s*(0\.\d{2,3})', re.IGNORECASE),
        "tier": re.compile(r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', re.IGNORECASE),
        "name_header": re.compile(r'^#+\s*(?:\d+\.?\d*\.?\s*)?[`\*]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[`\*]*', re.MULTILINE),
    }

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.signals: list[EntitySignal] = []
        self.file_manifest: dict[str, dict] = {}

    def scan_file(self, file_path: Path) -> list[EntitySignal]:
        signals = []
        try: content = file_path.read_text(encoding="utf-8", errors="ignore")
        except: return signals
        lines = content.split("\n")
        rel_path = str(file_path.relative_to(self.root_path))
        for i, line in enumerate(lines, 1):
            if m := self.PATTERNS["whr"].search(line):
                signals.append(EntitySignal(name=f"WHR_{m.group(1)}", file_path=rel_path, line_number=i, whr=float(m.group(1)), signal_type="METRIC", confidence=0.9, raw_match=line.strip()))
            if m := self.PATTERNS["tier"].search(line):
                signals.append(EntitySignal(name=f"Tier_{m.group(1)}", file_path=rel_path, line_number=i, tier=float(m.group(1)), signal_type="TIER", confidence=0.85, raw_match=line.strip()))
        return signals

    def scan_directory(self) -> dict:
        scanned = 0
        for p in self.root_path.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md", ".json", ".py", ".rs"}:
                self.signals.extend(self.scan_file(p))
                scanned += 1
        return {"scanned_files": scanned, "total_signals": len(self.signals)}
