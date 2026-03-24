#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: scanner.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
@SID: LOGIC_SCANNER_V1
@Shabti: Domain Logic (Extraction)
@Context: Field Impulse Scanner & Proximity Extractor
@Purpose:       Script logic for scanner.py.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from .resonance import Impulse, LexiconFilter

logger = logging.getLogger("mas-mcp.scanner")

# Directories to skip
SKIP_DIRS = {
    ".git", "target", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache", ".pytest_cache", ".mypy_cache",
    "incremental", "deps", "examples", "dumpster-dive"
}

# Binary extensions to skip
SKIP_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".lib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".doc", ".docx",
    ".rlib", ".rmeta", ".d"
}

def should_skip_path(path: Path) -> bool:
    """Determine if path should be skipped."""
    for part in path.parts:
        if part in SKIP_DIRS or part.startswith(".venv"):
            return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return False

def extract_impulses_from_line(line: str, file_path: str, line_num: int, lexicon: LexiconFilter) -> list[Impulse]:
    """Extract all impulses from a single line using the LexiconFilter."""
    impulses = []
    
    for category, filters in lexicon.filters.items():
        for filter_def in filters:
            regex = filter_def["regex"]
            confidence = filter_def.get("confidence", 0.8)
            
            try:
                for match in re.finditer(regex, line, re.IGNORECASE):
                    impulse = Impulse(
                        name=filter_def.get("name", match.group(0)),
                        signal_type=category,
                        file_path=file_path,
                        line_number=line_num,
                        confidence=confidence,
                        raw_match=line.strip()[:150]
                    )
                    
                    extractor = filter_def.get("extractor")
                    if extractor == "whr" and match.lastindex:
                        impulse.whr = float(match.group(1))
                        impulse.name = f"WHR_{impulse.whr}"
                    elif extractor == "tier" and match.lastindex:
                        impulse.tier = float(match.group(1))
                        impulse.name = f"Tier_{impulse.tier}"
                    elif extractor == "cup" and match.lastindex:
                        impulse.cup = match.group(1).upper()
                        impulse.name = f"{impulse.cup}-cup"
                    elif extractor == "measurements" and match.lastindex and match.lastindex >= 3:
                        impulse.measurements = f"B{match.group(1)}/W{match.group(2)}/H{match.group(3)}"
                        impulse.name = f"Measurements_{impulse.measurements}"
                    
                    if "tier" in filter_def and category == "ENTITY":
                        impulse.tier = filter_def["tier"]
                    
                    impulses.append(impulse)
            except re.error:
                continue
    
    return impulses

def scan_file_for_impulses(file_path: Path, root: Path, lexicon: LexiconFilter) -> list[Impulse]:
    """Scan a single file for impulses."""
    impulses = []
    
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return impulses
    
    rel_path = str(file_path.relative_to(root))
    lines = content.split("\n")
    
    for line_num, line in enumerate(lines, 1):
        line_impulses = extract_impulses_from_line(line, rel_path, line_num, lexicon)
        impulses.extend(line_impulses)
    
    return impulses

def proximity_extract(file_path: Path, entity_name: str, context_lines: int = 20) -> dict:
    """Extract metrics that appear within N lines of an entity mention."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"error": f"Could not read {file_path}"}
    
    lines = content.split("\n")
    entity_regex = re.compile(re.escape(entity_name), re.IGNORECASE)
    
    results = {
        "entity": entity_name,
        "file": str(file_path),
        "mentions": [],
        "associated_metrics": []
    }
    
    for line_num, line in enumerate(lines, 1):
        if entity_regex.search(line):
            results["mentions"].append({"line": line_num, "text": line.strip()[:100]})
            
            start = max(0, line_num - context_lines - 1)
            end = min(len(lines), line_num + context_lines)
            context = "\n".join(lines[start:end])
            
            whr_match = re.search(r'WHR[:\s]*[`\*]*(0\.\d{2,4})', context, re.IGNORECASE)
            tier_match = re.search(r'Tier[:\s]*[`\*]*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
            cup_match = re.search(r'\b([A-L])-?cup\b', context, re.IGNORECASE)
            meas_match = re.search(r'\b[BW][\s-]*(\d{2,3})\s*/\s*[WH][\s-]*(\d{2,3})\s*/\s*[H][\s-]*(\d{2,3})', context)
            
            metrics = {}
            if whr_match: metrics["whr"] = float(whr_match.group(1))
            if tier_match: metrics["tier"] = float(tier_match.group(1))
            if cup_match: metrics["cup"] = cup_match.group(1).upper()
            if meas_match: metrics["measurements"] = f"B{meas_match.group(1)}/W{meas_match.group(2)}/H{meas_match.group(3)}"
            
            if metrics:
                metrics["source_line"] = line_num
                metrics["context_window"] = f"lines {start+1}-{end}"
                results["associated_metrics"].append(metrics)
    
    return results

def get_mpw_fingerprint(mpw_source: Path) -> dict:
    """Get a fingerprint of the M-P-W source file for drift detection."""
    if not mpw_source.exists():
        return {"exists": False}
    
    stat = mpw_source.stat()
    content = mpw_source.read_text(encoding="utf-8", errors="ignore")
    
    # Count key structural elements
    entity_mentions = len(re.findall(r'\b(The Decorator|Orackla Nocticula|Madam Umeko|Dr\. Lysandra|Claudine Sin)', content))
    tier_mentions = len(re.findall(r'Tier[:\s]*[0-9]', content))
    whr_mentions = len(re.findall(r'WHR[:\s]*0\.\d+', content))
    section_count = len(re.findall(r'^###?\s+[IVXLCDM]+\.', content, re.MULTILINE))
    
    return {
        "exists": True,
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "line_count": content.count("\n"),
        "entity_mentions": entity_mentions,
        "tier_mentions": tier_mentions,
        "whr_mentions": whr_mentions,
        "section_count": section_count
    }

def quick_entity_extract(content: str, entity_name: str, context_lines: int = 50) -> dict | None:
    """Quick extraction of an entity's metrics from content."""
    lines = content.split("\n")
    entity_regex = re.compile(re.escape(entity_name), re.IGNORECASE)
    
    profile_patterns = [
        rf'^\s*#+.*Profile.*{re.escape(entity_name)}',
        rf'^\s*#+.*{re.escape(entity_name)}.*Profile',
        rf'^\s*#+.*{re.escape(entity_name)}.*\(CRC',
        rf'^\*\*\(`?{re.escape(entity_name)}`?\)\*\*',
    ]
    
    best_result = None
    best_score = 0
    
    for i, line in enumerate(lines):
        if entity_regex.search(line):
            is_profile_section = any(re.search(pat, line, re.IGNORECASE) for pat in profile_patterns)
            ctx_size = context_lines if is_profile_section else 30
            start = max(0, i - 5)
            end = min(len(lines), i + ctx_size)
            context = "\n".join(lines[start:end])
            
            has_physique = bool(re.search(r'Physique|EDFA|Measurements.*cup', context, re.IGNORECASE))
            has_measurements = bool(re.search(r'\*\*\(`?Measurements\)?:?\*\*|\bB[-\s]*\d{2,3}\s*/\s*W', context))
            
            whr = re.search(r'WHR[:\s\)\*`]*[`\*]*~?(0\.\d{2,4})', context, re.IGNORECASE)
            tier = re.search(r'Tier[:\s\)\*`]*[`\*]*([0-9]+\.?[0-9]*)', context, re.IGNORECASE)
            cup = re.search(r'\*\*\(`?Measurements\)?:?\*\*.*?([A-L])-?cup|([A-L])-?cup.*\*\*\s*\(?\s*\*?\*?B', context, re.IGNORECASE | re.DOTALL)
            
            if not cup:
                cup = re.search(r'\b([A-L])-?cup\b', context, re.IGNORECASE)
            
            if whr or tier or cup:
                score = 0
                if is_profile_section: score += 100
                if has_physique: score += 50
                if has_measurements: score += 30
                if whr: score += 10
                if tier: score += 5
                if cup: score += 5
                
                if score > best_score:
                    best_score = score
                    cup_val = (cup.group(1) or cup.group(2)).upper() if cup else None
                    best_result = {
                        "entity": entity_name,
                        "source_line": i + 1,
                        "whr": float(whr.group(1)) if whr else None,
                        "tier": float(tier.group(1)) if tier else None,
                        "cup": cup_val,
                    }
    
    return best_result
