#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: tools.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LOGIC_TOOLS_V1
@Shabti: Domain Logic (Tools)
@Context: MCP Tool Logic Implementation
@Purpose:       Script logic for tools.py.
"""

import re
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from collections import defaultdict
from dataclasses import asdict

from mas_mcp.logic.resonance import Impulse, ArchiveVault, LexiconFilter
from mas_mcp.logic.scanner import (
    should_skip_path, extract_impulses_from_line, scan_file_for_impulses, 
    proximity_extract, quick_entity_extract, get_mpw_fingerprint
)
from mas_mcp.logic.governance import (
    GOVERNANCE_CONFIG, policy_check_logic, 
    seal_promotion_in_lineage, queue_for_liturgical_grace
)
from mas_mcp.logic.reflections import (
    compute_file_hash, compute_directory_fingerprint,
    generate_arc_metaphor, generate_arc_recommendation
)
from mas_mcp.logic.narrative import NarrativeScanner
from mas_mcp.logic.qualia import check_qualia_drift, scan_target_qualia

logger = logging.getLogger("mas-mcp")

def mas_qualia_check_logic(target: str, root_path: Path) -> dict:
    """Core logic for mas_qualia_check."""
    path = root_path / target
    if path.exists():
        return scan_target_qualia(target, root_path)
    return check_qualia_drift(target)

def mas_narrative_scan_logic(target: str, root_path: Path, ssot_path: Path) -> dict:
    """Core logic for mas_narrative_scan."""
    scanner = NarrativeScanner(root_path, ssot_path)
    scanner.load_ssot()
    
    root = root_path / target if target != "." else root_path
    if not root.exists():
        return {"error": f"Target path does not exist: {root}"}
        
    target_files = []
    for p in root.rglob("*"):
        if p.is_file() and not should_skip_path(p):
            # Skip the SSOT itself and other instructions to avoid self-reinforcement
            if ".github/instructions" in str(p) or "copilot-instructions" in str(p):
                continue
            # Only scan relevant files for narrative
            if p.suffix in {".py", ".rs", ".md", ".ts"}:
                target_files.append(p)
                
    results = scanner.calculate_drift(target_files)
    results["target"] = target
    results["timestamp"] = datetime.now().isoformat()
    results["lexicon_size"] = len(scanner.lexicon)
    
    return results

def mas_scan_logic(target: str, root_path: Path, lexicon: LexiconFilter) -> dict:
    """Core logic for mas_scan."""
    root = root_path / target if target != "." else root_path
    
    if not root.exists():
        return {"error": f"Target path does not exist: {root}"}
    
    all_impulses = []
    files_scanned = 0
    files_skipped = 0
    bytes_processed = 0
    
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if should_skip_path(file_path):
            files_skipped += 1
            continue
        
        try:
            bytes_processed += file_path.stat().st_size
        except:
            pass
        
        impulses = scan_file_for_impulses(file_path, root_path, lexicon)
        all_impulses.extend(impulses)
        files_scanned += 1
    
    by_type = defaultdict(list)
    for imp in all_impulses:
        by_type[imp.signal_type].append(imp)
    
    entities = {}
    for imp in all_impulses:
        if imp.signal_type == "ENTITY":
            if imp.name not in entities:
                entities[imp.name] = {
                    "name": imp.name,
                    "files": set(),
                    "occurrences": 0,
                    "known_tier": imp.tier
                }
            entities[imp.name]["files"].add(imp.file_path)
            entities[imp.name]["occurrences"] += 1
    
    for e in entities.values():
        e["files"] = sorted(list(e["files"]))
    
    return {
        "scan_metadata": {
            "timestamp": datetime.now().isoformat(),
            "root": str(root),
            "files_scanned": files_scanned,
            "files_skipped": files_skipped,
            "bytes_processed": bytes_processed,
            "total_impulses": len(all_impulses)
        },
        "signal_counts": {k: len(v) for k, v in by_type.items()},
        "entities": entities,
        "unique_values": {
            "factions": sorted(set(s.raw_match.split()[-1] if s.raw_match else s.name for s in by_type.get("FACTION", []))),
            "protocols": sorted(set(s.name for s in by_type.get("PROTOCOL", []))),
        }
    }

def mas_entity_deep_logic(entity_name: str, context_lines: int, root_path: Path) -> dict:
    """Core logic for mas_entity_deep."""
    results = {
        "entity": entity_name,
        "context_lines": context_lines,
        "files_analyzed": [],
        "consolidated_metrics": {},
        "all_mentions": 0
    }
    
    metric_votes = defaultdict(list)
    
    for file_path in root_path.rglob("*"):
        if not file_path.is_file() or should_skip_path(file_path):
            continue
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if entity_name.lower() not in content.lower():
                continue
        except:
            continue
        
        file_result = proximity_extract(file_path, entity_name, context_lines)
        
        if file_result.get("mentions"):
            results["files_analyzed"].append(file_result)
            results["all_mentions"] += len(file_result["mentions"])
            
            for m in file_result.get("associated_metrics", []):
                for key in ["whr", "tier", "cup", "measurements"]:
                    if key in m:
                        metric_votes[key].append(m[key])
    
    from collections import Counter
    for key, values in metric_votes.items():
        if values:
            counter = Counter(values)
            results["consolidated_metrics"][key] = counter.most_common(1)[0][0]
                
    return results

def mas_validate_entity_logic(entity_name: str, expected_whr, expected_tier, expected_cup, root_path, vault: ArchiveVault) -> dict:
    """Core logic for mas_validate_entity."""
    extracted = mas_entity_deep_logic(entity_name, 30, root_path)
    metrics = extracted.get("consolidated_metrics", {})
    
    source_locations = {}
    for file_result in extracted.get("files_analyzed", []):
        for metric in file_result.get("associated_metrics", []):
            for key in ["whr", "tier", "cup", "measurements"]:
                if key in metric and key not in source_locations:
                    source_locations[key] = {
                        "file": file_result.get("file", "unknown"),
                        "line": metric.get("line", 0),
                        "value": metric[key]
                    }
    
    validation = {
        "entity": entity_name,
        "extracted": metrics,
        "expected": {"whr": expected_whr, "tier": expected_tier, "cup": expected_cup},
        "matches": [], "mismatches": [], "missing": [],
        "source_locations": source_locations
    }
    
    # Validation comparisons...
    if expected_whr is not None:
        if "whr" in metrics:
            if abs(metrics["whr"] - expected_whr) < 0.001:
                validation["matches"].append(f"WHR: {metrics['whr']}")
            else:
                validation["mismatches"].append(f"WHR: expected {expected_whr}, got {metrics['whr']}")
                vault.record_fracture(entity_name, {"whr": expected_whr}, {"whr": metrics["whr"]}, source_locations.get("whr", {}))
        else:
            validation["missing"].append(f"WHR: expected {expected_whr}, not found")
    
    # ... similarly for others ...
    
    validation["score"] = len(validation["matches"]) / max(1, len(validation["matches"]) + len(validation["mismatches"]) + len(validation["missing"]))
    vault.record_resonance(entity_name, metrics)
    
    if validation["score"] >= 0.99 and expected_whr and expected_tier and expected_cup:
        vault.seal_truth(entity_name, {"whr": expected_whr, "tier": expected_tier, "cup": expected_cup})
    
    return validation

def mas_pulse_logic(vault: ArchiveVault, mpw_source: Path, lexicon: LexiconFilter) -> dict:
    """Core logic for mas_pulse."""
    pulse = {
        "timestamp": datetime.now().isoformat(),
        "session": vault.data["session_count"],
        "mpw_status": get_mpw_fingerprint(mpw_source),
        "key_entities": {},
        "drift_alerts": [],
        "memory_summary": {
            "truths": len(vault.data["canonical_truths"]),
            "unresolved_fractures": len([d for d in vault.data["fractures"] if not d.get("resolved")])
        },
        "recommendations": []
    }
    
    if pulse["mpw_status"]["exists"]:
        content = mpw_source.read_text(encoding="utf-8", errors="ignore")
        entity_patterns = {p["name"]: p for p in lexicon.filters["ENTITY"]}
        
        key_entities = ["The Decorator", "Orackla Nocticula", "Madam Umeko Ketsuraku", "Dr. Lysandra Thorne", "Claudine Sin'claire"]
        
        for name in key_entities:
            extracted = quick_entity_extract(content, name)
            if extracted:
                canonical_tier = entity_patterns.get(name, {}).get("tier")
                if canonical_tier is not None:
                    extracted["tier_canonical"] = canonical_tier
                    if extracted["tier"] != canonical_tier:
                        extracted["tier_note"] = f"Extracted {extracted['tier']}, canonical is {canonical_tier}"
                        extracted["tier"] = canonical_tier
                pulse["key_entities"][name] = extracted
    
    recent = vault.get_active_fractures(3)
    if recent: pulse["recommendations"].append(f"⚠️ {len(recent)} unresolved fractures - review with mas_memory()")
    
    return pulse
