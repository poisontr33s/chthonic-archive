#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Artifact-Upcycle automation with intelligence.
Implements Policy: references/POLICY.md
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Any

# --- Configuration Loader ---

def load_rules(skill_root: Path) -> Dict[str, Any]:
    rules_path = skill_root / "references" / "ruleset.json"
    if not rules_path.exists():
        # Fallback defaults if json missing
        return {
            "potency_map": {".py": 100, ".md": 80, ".log": 10},
            "thresholds": {"archive": 20},
            "action_priority": ["archive", "normalize_name", "add_header"],
            "safe_filenames": ["README.md", "LICENSE", "SKILL.md"]
        }
    return json.loads(rules_path.read_text(encoding="utf-8"))

# --- 1. Potency Scoring ---

def calculate_potency(path: Path, content: str, rules: Dict[str, Any]) -> int:
    """Calculate score based on ruleset."""
    score = rules["potency_map"].get(path.suffix.lower(), 30)
    
    modifiers = rules.get("content_modifiers", {})
    
    # structural boosts
    for marker in modifiers.get("structural", []):
        if marker in content:
            if marker in ["# SSOT", "@SID"]:
                score += modifiers.get("critical_bonus", 0)
            else:
                score += modifiers.get("structural_bonus", 0)
            
    # noise penalties
    for noise in modifiers.get("noise", []):
        if noise.lower() in content.lower():
            score += modifiers.get("noise_penalty", 0)
            
    if "TODO" in content:
        score += modifiers.get("todo_penalty", 0)
        
    return max(0, score)

# --- 2. Classification & Action Selection ---

def determine_action(path: Path, potency: int, content: str, rules: Dict[str, Any]) -> str:
    """Decide the HIGHEST PRIORITY action needed."""
    
    # Priority 1: Archival (Low Value)
    if potency < rules["thresholds"]["archive"]:
        return "archive"
        
    # Priority 2: Normalization (Filenames)
    if path.name not in rules["safe_filenames"]:
        if " " in path.name or (not path.name.islower() and path.suffix not in [".md", ".txt"]):
            return "normalize_name"

    # Priority 3: Metadata (Headers)
    # Simple heuristic check
    has_header = (content.strip().startswith("---") or 
                  content.strip().startswith("#") or 
                  content.strip().startswith('"""') or
                  content.strip().startswith("//") or
                  content.strip().startswith("<!--"))
    header_exempt = set(rules.get("header_exempt_extensions", []))
    if not has_header and path.suffix.lower() not in header_exempt:
        return "add_header"

    # Priority 4: Integrity (Links)
    link_exts = set(rules.get("link_repair_extensions", [".md"]))
    if path.suffix.lower() in link_exts and ("] (../" in content or "]( " in content):
        return "repair_links"
        
    # Priority 5: Extraction (TODOs)
    todo_exts = set(rules.get("todo_extensions", []))
    if path.suffix.lower() in todo_exts and ("TODO" in content or "FIXME" in content):
        return "extract_todos"

    return "pass"

# --- 3. Action Adapters ---

def adapter_normalize_name(target: Path, dry_run: bool) -> str:
    new_name = target.name.lower().replace(" ", "_")
    new_path = target.with_name(new_name)
    if dry_run:
        return f"[PLAN] Rename '{target.name}' -> '{new_name}'"
    
    if not new_path.exists():
        target.rename(new_path)
        return f"[DONE] Renamed to {new_name}"
    return f"[SKIP] Target {new_name} exists"

def adapter_add_header(target: Path, content: str, dry_run: bool) -> str:
    header = ""
    if target.suffix == ".md":
        header = f"---\n# {target.stem}\n---\n\n"
    elif target.suffix == ".py":
        header = f'"""\n{target.stem}\n"""\n\n'
    else:
        header = f"// {target.stem}\n\n"
        
    if dry_run:
        return f"[PLAN] Prepend header ({len(header)} chars)"
    
    target.write_text(header + content, encoding="utf-8")
    return "[DONE] Added header"

def adapter_repair_links(target: Path, content: str, dry_run: bool) -> str:
    # Heuristic: Fix broken relative links (e.g. ] (../ -> ] (../../)
    # This is a simplified example.
    fixed = content.replace("] (../", "] (../../").replace("]( ", "](")
    
    count = 0
    if fixed != content:
        count = 1
        
    if dry_run:
        return f"[PLAN] Repair links (found {count} issues)"
        
    if count > 0:
        target.write_text(fixed, encoding="utf-8")
        return "[DONE] Repaired links"
    return "[SKIP] No links repaired"

def adapter_archive(target: Path, dry_run: bool) -> str:
    # Determine repo root (heuristic: look for .git or dumpster-dive)
    repo_root = target.parent
    while not (repo_root / "dumpster-dive").exists() and repo_root.parent != repo_root:
        repo_root = repo_root.parent
        
    archive_dir = repo_root / "dumpster-dive" / "archive"
    
    if dry_run:
        return f"[PLAN] Move to {archive_dir}"
    
    if not archive_dir.exists():
        return f"[ERR] Archive dir not found at {archive_dir}"
        
    dest = archive_dir / target.name
    if dest.exists():
        # Simple collision handling
        dest = archive_dir / f"{target.stem}_{target.stat().st_mtime_ns}{target.suffix}"
        
    shutil.move(str(target), str(dest))
    return f"[DONE] Archived to {dest.relative_to(repo_root)}"

def adapter_extract_todos(target: Path, content: str, dry_run: bool) -> str:
    todos = [line.strip() for line in content.splitlines() if "TODO" in line or "FIXME" in line]
    count = len(todos)
    
    # Repo root heuristic again
    repo_root = target.parent
    while not (repo_root / "dumpster-dive").exists() and repo_root.parent != repo_root:
        repo_root = repo_root.parent
        
    todo_file = repo_root / "dumpster-dive" / "TODO_EXTRACTION.md"

    if dry_run:
        return f"[PLAN] Append {count} items to {todo_file.name}"
    
    with open(todo_file, "a", encoding="utf-8") as f:
        f.write(f"\n## {target.name}\n")
        for item in todos:
            f.write(f"- [ ] {item}\n")
            
    # Optional: Remove TODOs from source? Policy says "Extract", usually implies keeping source clean or keeping as is.
    # For now, we just EXTRACT copy. Modifying source to remove them is risky without AST.
    return f"[DONE] Extracted to {todo_file.name}"

# --- Main Flow ---

def process_file(target: Path, rules: Dict[str, Any], dry_run: bool = True):
    try:
        # utf-8-sig handles BOM from Windows PowerShell Out-File
        content = target.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as e:
        print(f"Skipping {target.name}: {e}")
        return

    potency = calculate_potency(target, content, rules)
    action = determine_action(target, potency, content, rules)
    
    result_msg = ""
    
    if action == "pass":
        result_msg = "No action needed"
    elif action == "archive":
        result_msg = adapter_archive(target, dry_run)
    elif action == "normalize_name":
        result_msg = adapter_normalize_name(target, dry_run)
    elif action == "add_header":
        result_msg = adapter_add_header(target, content, dry_run)
    elif action == "repair_links":
        result_msg = adapter_repair_links(target, content, dry_run)
    elif action == "extract_todos":
        result_msg = adapter_extract_todos(target, content, dry_run)
        
    print(f"File: {target.name:<25} | Potency: {potency:<3} | Action: {action:<15} | {result_msg}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Artifact-Upcycle Intelligence")
    parser.add_argument("path", help="Target file or directory")
    parser.add_argument("--apply", action="store_true", help="Execute changes (default: dry-run)")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    # Determine Skill Root (assuming script is in /scripts)
    skill_root = Path(__file__).resolve().parent.parent
    rules = load_rules(skill_root)

    mode = "LIVE" if args.apply else "DRY-RUN"
    print(f"{'File':<25} | {'Scr':<3} | {'Action':<15} | Mode: {mode}")
    print("-" * 80)

    if target.is_file():
        process_file(target, rules, dry_run=not args.apply)
    else:
        # Recursive scan
        for file_path in target.rglob("*"): 
            if file_path.is_file() and ".git" not in str(file_path):
                process_file(file_path, rules, dry_run=not args.apply)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
