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
@SID: LOGIC_QUALIA_V1
@Shabti: Governance Gate
@Context: Qualia: Linguistic Alignment & Canonical Terminology
@Purpose:       Script logic for qualia.py.
"""

# The Forbidden Mappings
# Generic -> Canonical
QUALIA_MAP = {
    "context": "weave",
    "manager": "curator",
    "result": "resonance",
    "handler": "vessel",
    "processor": "catalyst",
    "status": "metabolism",
    "state": "resonance",
    "memory": "archive",
    "registry": "lexicon",
    "signal": "impulse",
    "discrepancy": "fracture",
    "extraction": "resonance",
    "valid": "canonical",
    "verified": "sealed",
}

def check_qualia_drift(text: str) -> dict:
    """
    Scans text for Forbidden generic terms and suggests Canonical alternatives.
    """
    drifts = []
    text_lower = text.lower()
    
    for generic, canonical in QUALIA_MAP.items():
        if generic in text_lower:
            # Find occurrences
            count = text_lower.count(generic)
            drifts.append({
                "forbidden": generic,
                "recommended": canonical,
                "occurrences": count
            })
            
    return {
        "drift_detected": len(drifts) > 0,
        "drifts": drifts,
        "qualia_score": max(0, 100 - (sum(d["occurrences"] for d in drifts) if drifts else 0) * 2)
    }

def scan_target_qualia(target_path, root_path) -> dict:
    """
    Scans a file or directory for qualia drift.
    """
    from mas_mcp.logic.scanner import should_skip_path
    path = root_path / target_path
    
    total_violations = {}
    files_with_violations = set()
    
    if path.is_file():
        targets = [path]
    else:
        targets = [p for p in path.rglob("*") if p.is_file() and not should_skip_path(p) and p.suffix in {".py", ".rs", ".md", ".txt", ".ps1"}]
        
    for file_path in targets:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            result = check_qualia_drift(content)
            if result["drift_detected"]:
                files_with_violations.add(str(file_path.relative_to(root_path)))
                for d in result["drifts"]:
                    term = d["forbidden"]
                    if term not in total_violations:
                        total_violations[term] = {
                            "term": term,
                            "canonical": d["recommended"],
                            "frequency": 0,
                            "files": set()
                        }
                    total_violations[term]["frequency"] += d["occurrences"]
                    total_violations[term]["files"].add(str(file_path.relative_to(root_path)))
        except:
            continue
            
    sorted_violations = sorted(
        [
            {
                "term": v["term"],
                "canonical": v["canonical"],
                "frequency": v["frequency"],
                "files": sorted(list(v["files"]))[:5] # Top 5 files
            }
            for v in total_violations.values()
        ],
        key=lambda x: x["frequency"],
        reverse=True
    )
    
    total_occurrence_sum = sum(v["frequency"] for v in total_violations.values())
    
    return {
        "qualia_score": max(0, 100 - total_occurrence_sum * 1),
        "detected_violations": sorted_violations,
        "files_scanned": len(targets),
        "violation_count": total_occurrence_sum,
        "affected_files": len(files_with_violations)
    }

if __name__ == "__main__":
    import sys
    test_text = "The Context Manager returned the extraction result."
    print(f"Testing text: '{test_text}'")
    print(check_qualia_drift(test_text))
