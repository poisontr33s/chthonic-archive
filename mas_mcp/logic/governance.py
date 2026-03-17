#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: governance.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
governance.py — Script logic for governance.py.

@SID:           TOOL_GOVERNANCE_V1
@Shabti:        CLI Script
@Purpose:       Script logic for governance.py.
"""

import re
import hashlib
from datetime import datetime

GOVERNANCE_CONFIG = {
    "promotion_thresholds": {
        "novelty_min": 0.7,
        "redundancy_max": 0.3,
        "safety_min": 0.8,
        "overall_min": 0.6,
    },
    "grace_window": {
        "novelty_range": (0.5, 0.7),
        "redundancy_range": (0.3, 0.5),
        "max_queue_size": 10,
        "retest_after_snapshots": 2,
    },
    "risk_bands": {
        "safe": {"description": "No dangerous operations detected", "action": "auto_approve"},
        "guarded": {"description": "Contains operations requiring review", "action": "require_justification"},
        "prohibited": {"description": "Contains forbidden operations", "action": "auto_reject"}
    },
    "prohibited_patterns": [
        r'\bexec\s*\([^)]*\bopen\b',
        r'\beval\s*\([^)]*\binput\b',
        r'\brm\s+-rf\s+[/~]',
        r'\bos\.system\s*\([^)]*[;&|]',
        r'__import__.*\bos\b.*\bsystem\b',
    ],
    "guarded_patterns": [
        (r'\bexec\s*\(', "Dynamic code execution"),
        (r'\beval\s*\(', "Dynamic evaluation"),
        (r'\bopen\s*\([^)]*["\']w', "File write operation"),
        (r'\bsubprocess\b', "Subprocess execution"),
        (r'\bos\.(remove|unlink|rmdir)\b', "File deletion"),
        (r'\bshutil\.(rmtree|move|copy)\b', "File system modification"),
        (r'\b__import__\b', "Dynamic import"),
        (r'\bglobals\(\)|locals\(\)', "Namespace access"),
    ],
    "core_invariants": {
        "required_entities": ["The Decorator", "Orackla Nocticula", "Madam Umeko Ketsuraku", "Dr. Lysandra Thorne"],
        "max_orphan_rate": 0.3,
        "min_pattern_count": 10,
        "min_tool_count": 15,
    },
    "lineage": {
        "max_snapshots": 50,
        "auto_snapshot_interval": 300,
        "digest_threshold": 20,
    },
    "narrative_tags": {
        "genesis": "First snapshot or major reset",
        "pivot": "Significant direction change",
        "ordeal": "Recovery from error or regression",
        "consolidation": "Stability after growth",
        "flourish": "Period of healthy emergence",
        "dormant": "Extended period of stasis",
    }
}

def policy_check_logic(code: str) -> dict:
    """Core logic for policy checking."""
    result = {
        "timestamp": datetime.now().isoformat(),
        "risk_band": "safe",
        "issues": [],
        "required_actions": [],
        "can_proceed": True
    }
    
    for pattern in GOVERNANCE_CONFIG["prohibited_patterns"]:
        if re.search(pattern, code, re.IGNORECASE):
            result["risk_band"] = "prohibited"
            result["issues"].append({"severity": "critical", "pattern": pattern, "message": "Prohibited pattern detected"})
            result["can_proceed"] = False
    
    if result["risk_band"] == "prohibited":
        result["required_actions"] = ["Code rejected. Prohibited operations detected."]
        return result
    
    for pattern, description in GOVERNANCE_CONFIG["guarded_patterns"]:
        if re.search(pattern, code):
            if result["risk_band"] == "safe": result["risk_band"] = "guarded"
            result["issues"].append({"severity": "warning", "pattern": pattern, "message": description})
    
    if result["risk_band"] == "guarded":
        result["required_actions"] = ["Provide justification memo via mas_promote_candidate()"]
        result["can_proceed"] = True
    
    result["band_info"] = GOVERNANCE_CONFIG["risk_bands"][result["risk_band"]]
    return result

def seal_promotion_in_lineage(vault, function_name, code, justification, result):
    """Seal a successful promotion in the Archive's lineage."""
    if "promotions" not in vault.data:
        vault.data["promotions"] = []
    
    vault.data["promotions"].append({
        "function_name": function_name,
        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
        "justification": justification,
        "scores": result["gate_results"]["test"]["scores"],
        "timestamp": datetime.now().isoformat(),
        "seal": result.get("seal", {}).get("chant")
    })
    vault.data["promotions"] = vault.data["promotions"][-50:]
    vault._save()

def queue_for_liturgical_grace(vault, function_name, code, justification, result):
    """Add a borderline candidate to the grace queue."""
    if "grace_queue" not in vault.data:
        vault.data["grace_queue"] = []
    
    snapshot_count = len(vault.data.get("self_snapshots", []))
    vault.data["grace_queue"].append({
        "function_name": function_name,
        "code": code,
        "justification": justification,
        "scores": result["gate_results"]["test"]["scores"],
        "queued_at": datetime.now().isoformat(),
        "queued_at_snapshot": snapshot_count,
        "retest_at_snapshot": snapshot_count + GOVERNANCE_CONFIG["grace_window"]["retest_after_snapshots"]
    })
    
    max_size = GOVERNANCE_CONFIG["grace_window"]["max_queue_size"]
    vault.data["grace_queue"] = vault.data["grace_queue"][-max_size:]
    vault._save()
