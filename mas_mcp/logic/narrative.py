#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: narrative.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LOGIC_NARRATIVE_V1
@Shabti: Domain Logic (Cultural Analysis)
@Context: Narrative Scanner Logic: Cultural Drift Analysis
@Purpose:       Script logic for narrative.py.
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Any

class NarrativeScanner:
    """
    Analyzes the 'Cultural Drift' between the SSOT (Canon) and the codebase (Field).
    Measures how much of the Chthonic vocabulary has resonated into the implementation.
    """
    def __init__(self, root_path: Path, ssot_path: Path):
        self.root_path = root_path
        self.ssot_path = ssot_path
        self.lexicon: Set[str] = set()
        self.entities: Dict[str, Dict] = {}
        
    def load_ssot(self):
        """Extracts key terminology and entity constraints from SSOT."""
        if not self.ssot_path.exists():
            return
            
        content = self.ssot_path.read_text(encoding='utf-8')
        
        # 1. Extract terms in parentheses like (`Term`)
        terms = re.findall(r'\(`([^`\)]+)`?\)', content)
        self.lexicon.update(terms)
        
        # 2. Extract Tier and WHR patterns for entities
        # Example: (`T1`): → (`TRM-VRT`): → ... → (`Orackla-Nocticula`)
        # Example: (`T-DECOR`/`K-CUP`/`WHR-0.464`/`FA⁵-SUPREME`)
        
        # Simple entity extraction for common names
        entity_names = ["Orackla", "Umeko", "Lysandra", "Kali", "Vesper", "Seraphine", "Claudine"]
        for name in entity_names:
            # Look for WHR near name
            whr_match = re.search(fr'{name}.*?WHR-?(\d\.\d+)', content, re.IGNORECASE | re.DOTALL)
            tier_match = re.search(fr'{name}.*?T(\d(?:\.\d)?)', content, re.IGNORECASE | re.DOTALL)
            
            self.entities[name] = {
                "whr": float(whr_match.group(1)) if whr_match else None,
                "tier": float(tier_match.group(1)) if tier_match else None
            }

    def calculate_drift(self, target_files: List[Path]) -> Dict[str, Any]:
        """Scans target files for lexicon usage and value collisions using word-tokenization (FASTER)."""
        # We use lowercase keys for internal counting
        usage_counts: Dict[str, int] = {term.lower(): 0 for term in self.lexicon}
        # Mapping back to original case for the report
        term_map: Dict[str, str] = {term.lower(): term for term in self.lexicon}
        collisions: List[Dict] = []
        
        # Terms to always ignore (High frequency noise / Generic words)
        ignore_terms = {
            "Update", "Status", "Maintainer", "Creator", "User", "as", "all",
            "Context", "Manager", "Result", "Handler", "Error", "data", "file", "path", "None", 
            "True", "False", "import", "class", "def", "self", "for", "if", "in", "with"
        }
        
        # Savant Standard: Filter out noise but allow specific short Canon terms
        canonical_short = {"I", "K"} 
        lexicon_lower = {}
        for t in self.lexicon:
            tl = t.lower()
            if t in canonical_short:
                lexicon_lower[tl] = t
            elif len(t) > 2 and t not in ignore_terms:
                lexicon_lower[tl] = t

        for file_path in target_files:
            try:
                # Still skip very large files
                if file_path.stat().st_size > 500_000: continue
                # Savant Standard: Binary check (Entropy Filter)
                content_bytes = file_path.read_bytes()
                if b'\x00' in content_bytes: continue
                
                content = content_bytes.decode('utf-8', errors='ignore')
                
                # Tokenize (allow single chars if they're in lexicon_lower)
                words = re.findall(r'\b[A-Za-z0-9\-\.]{1,}\b', content)
                for w in words:
                    wl = w.lower()
                    if wl in lexicon_lower:
                        usage_counts[wl] += 1
                
                # Collisions check (limited to entities found in text)
                lower_content = content.lower()
                for name, expected in self.entities.items():
                    name_lower = name.lower()
                    if f" {name_lower} " in f" {lower_content} ": # Simplified contains
                        # Extract WHR near name if possible
                        pos = lower_content.find(name_lower)
                        snippet = lower_content[max(0, pos-150):min(len(lower_content), pos+150)]
                        found_whr = re.search(r'whr[:\s\-]*(\d\.\d+)', snippet)
                        if found_whr and expected['whr']:
                            actual_whr = float(found_whr.group(1))
                            if abs(actual_whr - expected['whr']) > 0.005:
                                collisions.append({
                                    "file": str(file_path.relative_to(self.root_path)),
                                    "entity": name,
                                    "type": "WHR",
                                    "expected": expected['whr'],
                                    "actual": actual_whr
                                })
            except:
                continue

        # Map back to original names and aggregate
        final_counts = {term_map[l]: c for l, c in usage_counts.items() if c > 0}
        used_terms = list(final_counts.keys())
        
        # Savant Standard: Accurate relevant lexicon calculation
        relevant_lexicon = list(lexicon_lower.values())
        missing_terms = [t for t in relevant_lexicon if t.lower() not in usage_counts or usage_counts[t.lower()] == 0]
        
        vocabulary_coverage = len(used_terms) / len(relevant_lexicon) if relevant_lexicon else 0
        
        return {
            "vocabulary_coverage": round(vocabulary_coverage, 3),
            "used_terms_count": len(used_terms),
            "missing_terms_count": len(missing_terms),
            "top_terms": sorted(final_counts.items(), key=lambda x: x[1], reverse=True)[:15],
            "collisions": collisions,
            "drift_score": self._calculate_final_score(vocabulary_coverage, len(collisions))
        }

    def _calculate_final_score(self, coverage: float, collision_count: int) -> float:
        # High coverage = Low drift
        # High collisions = High drift
        drift = (1.0 - coverage) * 100 + (collision_count * 10)
        return round(max(0, drift), 2)
