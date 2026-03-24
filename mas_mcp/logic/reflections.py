#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: reflections.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏰 THE FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
reflections.py — Script logic for reflections.py.

@SID:           TOOL_REFLECTIONS_V1
@Shabti:        CLI Script
@Purpose:       Script logic for reflections.py.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from .scanner import should_skip_path

def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file's contents."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return "unreadable"

def compute_directory_fingerprint(root: Path, extensions: set = None) -> dict:
    """Compute a fingerprint of a directory tree."""
    if extensions is None:
        extensions = {".md", ".rs", ".toml", ".py", ".json", ".frag", ".vert"}
    
    fingerprint = {
        "root": str(root),
        "computed_at": datetime.now().isoformat(),
        "files": {},
        "summary": {"total_files": 0, "total_size": 0, "by_extension": {}}
    }
    
    try:
        for path in root.rglob("*"):
            if path.is_file():
                skip_dirs = {"target", ".git", "__pycache__", "node_modules", ".uv", "venv"}
                if any(skip in path.parts for skip in skip_dirs):
                    continue
                
                ext = path.suffix.lower()
                if ext in extensions or not extensions:
                    rel_path = str(path.relative_to(root))
                    file_hash = compute_file_hash(path)
                    file_size = path.stat().st_size
                    
                    fingerprint["files"][rel_path] = {"hash": file_hash, "size": file_size, "ext": ext}
                    fingerprint["summary"]["total_files"] += 1
                    fingerprint["summary"]["total_size"] += file_size
                    fingerprint["summary"]["by_extension"][ext] = fingerprint["summary"]["by_extension"].get(ext, 0) + 1
    except Exception as e:
        fingerprint["error"] = str(e)
    
    return fingerprint

def generate_arc_metaphor(arc: str) -> str:
    """Generate a metaphor for the current arc."""
    metaphors = {
        "flourish": "The carpet billows with new threads, each one glowing.",
        "growth": "The carpet weaves steadily, pattern by pattern.",
        "dormant": "The carpet hovers still, conserving energy for the next flight.",
        "ordeal": "The carpet mends a tear, stronger where it healed.",
        "consolidation": "The carpet settles, its new patterns integrating."
    }
    return metaphors.get(arc, "The carpet observes its own reflection.")

def generate_arc_recommendation(arc: str) -> str:
    """Generate a recommendation based on current arc."""
    recommendations = {
        "flourish": "Excellent health. Consider taking a flourish snapshot.",
        "growth": "Healthy progress. Continue current trajectory.",
        "dormant": "Consider injecting new candidates or extensions to stimulate growth.",
        "ordeal": "Focus on stability. Run mas_check_invariants() frequently.",
        "consolidation": "Good time to document and tag recent snapshots."
    }
    return recommendations.get(arc, "Observe and adapt.")
