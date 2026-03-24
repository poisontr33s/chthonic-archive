#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: resonance.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LOGIC_RESONANCE_V1
@Shabti: Domain Logic (Persistence)
@Context: Resonance: Liturgical Memory & Imperial Truths
@Purpose:       Script logic for resonance.py.
"""

import json
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict

logger = logging.getLogger("mas-mcp.resonance")

@dataclass
class Impulse:
    """A detected signal/impulse in the field."""
    name: str
    signal_type: str
    file_path: str
    line_number: int
    confidence: float = 0.5
    raw_match: str = ""
    whr: Optional[float] = None
    tier: Optional[float] = None
    cup: Optional[str] = None
    measurements: Optional[str] = None

class ArchiveVault:
    """
    Persistent storage for canonical truths, fractures, and resonance history.
    The Sacerdotal memory of the system.
    """
    
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "canonical_truths": {},      # entity -> confirmed metrics
            "fractures": [],              # list of {entity, expected, got, file, line, timestamp}
            "resonance_history": [],     # historical resonance detections
            "filter_evolution": [],       # how LexiconFilters have changed
            "session_count": 0
        }
        self._load()
    
    def _load(self):
        """Load the Archive from disk."""
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
                logger.info(f"Archive Vault synchronized: {len(self.data['canonical_truths'])} truths, {len(self.data['fractures'])} fractures")
            except Exception as e:
                logger.warning(f"Could not synchronize Archive: {e}")
    
    def _save(self):
        """Commune Archive state to disk."""
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not save Archive state: {e}")
    
    def seal_truth(self, entity: str, metrics: dict):
        """Seal a validated truth into the Archive."""
        self.data["canonical_truths"][entity] = {
            "metrics": metrics,
            "sealed_at": datetime.now().isoformat()
        }
        self._save()
    
    def record_fracture(self, entity: str, expected: dict, got: dict, source: dict):
        """Record a fracture (discrepancy) between code and canon."""
        self.data["fractures"].append({
            "entity": entity,
            "expected": expected,
            "got": got,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        })
        # Keep only last 100 fractures
        self.data["fractures"] = self.data["fractures"][-100:]
        self._save()
    
    def record_resonance(self, entity: str, metrics: dict):
        """Log a resonance event (extraction) for lineage tracking."""
        self.data["resonance_history"].append({
            "entity": entity,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 50 events
        self.data["resonance_history"] = self.data["resonance_history"][-50:]
        self._save()
    
    def track_filter_hit(self, filter_name: str, category: str, detected: bool):
        """Track filter efficacy - which patterns are operational."""
        if "filter_efficacy" not in self.data:
            self.data["filter_efficacy"] = {}
        
        key = f"{category}/{filter_name}"
        if key not in self.data["filter_efficacy"]:
            self.data["filter_efficacy"][key] = {"hits": 0, "misses": 0}
        
        if detected:
            self.data["filter_efficacy"][key]["hits"] += 1
        else:
            self.data["filter_efficacy"][key]["misses"] += 1
    
    def get_filter_report(self) -> dict:
        """Generate efficacy report for the LexiconFilter."""
        efficacy = self.data.get("filter_efficacy", {})
        report = {}
        for key, stats in efficacy.items():
            total = stats["hits"] + stats["misses"]
            if total > 0:
                report[key] = {
                    "hits": stats["hits"],
                    "misses": stats["misses"],
                    "detection_rate": f"{stats['hits'] / total * 100:.1f}%"
                }
        return report
    
    def get_canonical_truth(self, entity: str) -> dict | None:
        """Retrieve the sealed truth for an entity."""
        return self.data["canonical_truths"].get(entity)
    
    def get_active_fractures(self, limit: int = 10) -> list:
        """Get most recent unresolved fractures."""
        unresolved = [d for d in self.data["fractures"] if not d.get("resolved")]
        return unresolved[-limit:]
    
    def increment_session(self):
        """Track liturgical session count."""
        self.data["session_count"] += 1
        self._save()
        return self.data["session_count"]

class LexiconFilter:
    """
    The interpretive lens (formerly PatternRegistry) used to detect ASC meaning.
    """
    
    def __init__(self):
        self.filters: dict[str, list[dict]] = {
            "METRIC": [],
            "ENTITY": [],
            "FACTION": [],
            "AXIOM": [],
            "PROTOCOL": [],
            "STRUCTURAL": [],
            "CUSTOM": []
        }
        self._load_defaults()
        self.evolution_history: list[dict] = []
    
    def _load_defaults(self):
        """Load the default detection filters."""
        self.filters["METRIC"] = [
            {"name": "WHR", "regex": r'WHR[:\s]*[`\*]*~?(0\.\d{2,4})', "confidence": 0.95, "extractor": "whr"},
            {"name": "WHR_INLINE", "regex": r'\*\*\(?WHR\)?\*\*[:\s]*[`\*]*~?(0\.\d{2,4})', "confidence": 0.95, "extractor": "whr"},
            {"name": "TIER", "regex": r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', "confidence": 0.9, "extractor": "tier"},
            {"name": "CUP", "regex": r'\b([A-L])-?cup\b', "confidence": 0.85, "extractor": "cup"},
            {"name": "MEASUREMENTS", "regex": r'\b[BW][\s-]*(\d{2,3})\s*/\s*[WH][\s-]*(\d{2,3})\s*/\s*[H][\s-]*(\d{2,3})', "confidence": 0.9, "extractor": "measurements"},
        ]
        
        self.filters["ENTITY"] = [
            {"name": "The Decorator", "regex": r'\bThe Decorator\b', "confidence": 0.98, "tier": 0.5},
            {"name": "Orackla Nocticula", "regex": r'\bOrackla Nocticula\b', "confidence": 0.98, "tier": 1},
            {"name": "Madam Umeko Ketsuraku", "regex": r'\bMadam Umeko Ketsuraku\b', "confidence": 0.98, "tier": 1},
            {"name": "Dr. Lysandra Thorne", "regex": r'\bDr\.?\s*Lysandra Thorne\b', "confidence": 0.98, "tier": 1},
            {"name": "Lysandra Thorne", "regex": r'\bLysandra Thorne\b', "confidence": 0.95, "tier": 1},
            {"name": "Claudine Sin\'claire", "regex": r"Claudine Sin'claire", "confidence": 0.98, "tier": 1},
            {"name": "Kali Nyx Ravenscar", "regex": r'\bKali Nyx Ravenscar\b', "confidence": 0.98, "tier": 2},
            {"name": "Vesper Mnemosyne Lockhart", "regex": r'\bVesper Mnemosyne Lockhart\b', "confidence": 0.98, "tier": 2},
            {"name": "Seraphine Kore Ashenhelm", "regex": r'\bSeraphine Kore Ashenhelm\b', "confidence": 0.98, "tier": 2},
            {"name": "Sister Ferrum Scoriae", "regex": r'\bSister Ferrum Scoriae\b', "confidence": 0.98, "tier": 3},
            {"name": "SFS", "regex": r'\bSFS\b', "confidence": 0.85, "tier": 3},
            {"name": "Spectra Chroma Excavatus", "regex": r'\bSpectra Chroma Excavatus\b', "confidence": 0.98, "tier": 3},
            {"name": "Dame Schrödinger's Paradox", "regex": r"(?:Dame|Sir) Schrödinger'?s (?:Paradox|Bastard)", "confidence": 0.95, "tier": 4},
            {"name": "DM-SCRS-P", "regex": r'\b(?:DM-SCRS-P|SR-SCRS-B)\b', "confidence": 0.9, "tier": 4},
            {"name": "Alabaster Voyde", "regex": r'\bAlabaster Voyde\b', "confidence": 0.98, "tier": 0.01},
            {"name": "The Null Matriarch", "regex": r'\bThe Null Matriarch\b', "confidence": 0.98, "tier": 0.01},
        ]
        
        self.filters["FACTION"] = [
            {"name": "faction_codes", "regex": r'\b(TMO|TTG|TDPC|TRM-VRT|TL-FNS|TP-FNS|OMCA|SDBH|BOS|AAA|TWOUMC|SBSGYB|TNKW-RIAT|TDAPCFLN|POAFPSG|TR-VRT|ASC)\b', "confidence": 0.95},
        ]
        
        self.filters["AXIOM"] = [
            {"name": "axioms", "regex": r'\b(FA[¹²³⁴⁵1-5]|FA⁵|FA⁴|FA³|FA²|FA¹)\b', "confidence": 0.95},
        ]
        
        self.filters["PROTOCOL"] = [
            {"name": "protocols", "regex": r'\b(DAFP|PRISM|TPEF|TSRP|MMPS|MAS|UMRE|MSP-RSG|PEE|EULP-AA|LIPAA|LUPLR|DULSS|EDFA|ET-S|MURI|CRC|CDA)\b', "confidence": 0.9},
        ]
    
    def add_filter(self, category: str, name: str, regex: str, confidence: float = 0.8, **kwargs) -> bool:
        """Evolve the Lexicon with a new filter."""
        if category not in self.filters:
            self.filters[category] = []
        
        try:
            re.compile(regex)
        except re.error as e:
            logger.error(f"Invalid regex filter: {e}")
            return False
        
        lex_filter = {"name": name, "regex": regex, "confidence": confidence, **kwargs}
        self.filters[category].append(lex_filter)
        
        self.evolution_history.append({
            "action": "add",
            "category": category,
            "filter": lex_filter,
            "timestamp": datetime.now().isoformat()
        })
        return True
    
    def remove_filter(self, category: str, name: str) -> bool:
        """Excise a filter from the Lexicon."""
        if category not in self.filters:
            return False
        
        original_len = len(self.filters[category])
        self.filters[category] = [p for p in self.filters[category] if p["name"] != name]
        
        if len(self.filters[category]) < original_len:
            self.evolution_history.append({
                "action": "excise",
                "category": category,
                "name": name,
                "timestamp": datetime.now().isoformat()
            })
            return True
        return False
    
    def get_all_filters(self) -> dict:
        """Get all currently operational filters."""
        return self.filters
    
    def get_evolution(self) -> list:
        """Get filter evolution history."""
        return self.evolution_history
