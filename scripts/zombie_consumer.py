#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Zombie Consumer — feeds on codebase dead files, extracts intelligence, routes remains to the forge.

The zombie sits ABOVE dumpster-dive/. It doesn't delete — it consumes:
  1. BITE    — scan a file/directory for ore signals (what's extractable?)
  2. CHEW    — extract value: imports, docstrings, patterns, SIDs, cross-refs
  3. DIGEST  — write an intelligence extract (what was learned)
  4. EXCRETE — git mv the consumed file into dumpster-dive/intake/ with metadata

The zombie grows smarter with each file it eats. Its memory lives in
dumpster-dive/intake/.zombie_memory.json — a cumulative knowledge graph of
what patterns it has seen, what clusters it has identified, and what it
recommends for future consumption.

Usage:
    uv run scripts/zombie_consumer.py bite <path>              # assess one file
    uv run scripts/zombie_consumer.py bite <path> --deep       # full extraction scan
    uv run scripts/zombie_consumer.py chew <path>              # extract intelligence
    uv run scripts/zombie_consumer.py digest <path>            # write extract + rate ore
    uv run scripts/zombie_consumer.py excrete <path>           # git mv to intake + receipt
    uv run scripts/zombie_consumer.py feed <path>              # full pipeline: bite→chew→digest→excrete
    uv run scripts/zombie_consumer.py feed <path> --dry-run    # show what would happen
    uv run scripts/zombie_consumer.py hunger                   # scan repo for consumable candidates
    uv run scripts/zombie_consumer.py memory                   # show what the zombie has learned
    uv run scripts/zombie_consumer.py memory --json            # JSON output
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo discovery
# ---------------------------------------------------------------------------

def find_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return Path.cwd()

ROOT = find_repo_root()
INTAKE = ROOT / "dumpster-dive" / "intake"
MEMORY_PATH = INTAKE / ".zombie_memory.json"

# ---------------------------------------------------------------------------
# Ore signal patterns
# ---------------------------------------------------------------------------

RE_SID = re.compile(r"@SID:\s*(\S+)")
RE_SHABTI = re.compile(r"@Shabti:\s*(.+)")
RE_IMPLEMENTS = re.compile(r"@Implements:\s*(.+)")
RE_DECORATOR_HEADER = re.compile(r"#\s*[╔╠╚║]")
RE_IMPORT = re.compile(r"^(?:from|import)\s+(\S+)", re.MULTILINE)
RE_DEF = re.compile(r"^(?:def|class)\s+(\w+)", re.MULTILINE)
RE_DOCSTRING = re.compile(r'"""(.+?)"""', re.DOTALL)
RE_MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

# File categories for ore rating heuristics
BACKUP_PATTERNS = re.compile(r"\.(bak|backup|old|orig|save)[-\d]*$", re.IGNORECASE)
LEGACY_PATTERNS = re.compile(r"(LEGACY|deprecated|obsolete|removed)", re.IGNORECASE)
RECOVERED_PATTERNS = re.compile(r"^recovered_", re.IGNORECASE)
TEST_PATTERNS = re.compile(r"^(test_|edge_case_test|.*_test\.py)$", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Memory (the zombie's growing intelligence)
# ---------------------------------------------------------------------------

def load_memory() -> dict:
    if MEMORY_PATH.exists():
        return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": 1,
        "created": datetime.now(timezone.utc).isoformat(),
        "files_consumed": 0,
        "total_patterns_extracted": 0,
        "total_imports_seen": [],
        "total_sids_seen": [],
        "total_functions_seen": [],
        "cluster_signals": {},
        "consumption_log": [],
    }


def save_memory(mem: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    mem["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_PATH.write_text(json.dumps(mem, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# BITE — assess a file for ore signals
# ---------------------------------------------------------------------------

def bite(path: Path, deep: bool = False) -> dict:
    """Scan a file and return ore assessment."""
    if not path.exists():
        return {"error": f"Path not found: {path}"}

    rel = safe_relative(path)
    stat = path.stat()
    ext = path.suffix.lower()
    name = path.name

    result: dict = {
        "path": rel,
        "name": name,
        "ext": ext,
        "size_bytes": stat.st_size,
        "size_lines": 0,
        "signals": [],
        "ore_rating": 0,
        "category": "unknown",
        "extractable": [],
    }

    # Read content
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        result["size_lines"] = content.count("\n") + 1
    except Exception:
        result["signals"].append("unreadable")
        result["ore_rating"] = 1
        result["category"] = "slag"
        return result

    # Categorize
    if BACKUP_PATTERNS.search(name):
        result["category"] = "backup"
        result["ore_rating"] = 2
        result["signals"].append("backup_file")
    elif LEGACY_PATTERNS.search(name) or LEGACY_PATTERNS.search(content[:500]):
        result["category"] = "legacy"
        result["ore_rating"] = 3
        result["signals"].append("legacy_marker")
    elif RECOVERED_PATTERNS.search(name):
        result["category"] = "recovered"
        result["ore_rating"] = 3
        result["signals"].append("recovered_salvage")
    elif TEST_PATTERNS.search(name):
        result["category"] = "test"
        result["ore_rating"] = 2
        result["signals"].append("test_file")
    else:
        result["category"] = "candidate"
        result["ore_rating"] = 3

    # Extract signals
    sids = RE_SID.findall(content)
    if sids:
        result["signals"].append(f"has_sid:{','.join(sids)}")
        result["extractable"].append({"type": "sid", "values": sids})
        result["ore_rating"] = max(result["ore_rating"], 3)

    shabtis = RE_SHABTI.findall(content)
    if shabtis:
        result["signals"].append("has_shabti")
        result["extractable"].append({"type": "shabti", "values": shabtis})

    implements = RE_IMPLEMENTS.findall(content)
    if implements:
        result["signals"].append("has_implements")
        result["extractable"].append({"type": "implements", "values": implements})

    if RE_DECORATOR_HEADER.search(content):
        result["signals"].append("has_decorator_header")
        result["ore_rating"] = max(result["ore_rating"], 3)

    # Language-specific extraction
    if ext == ".py" and deep:
        result = _bite_python_deep(path, content, result)
    elif ext == ".ps1" and deep:
        result = _bite_ps1_deep(content, result)
    elif ext in (".md", ".markdown") and deep:
        result = _bite_markdown_deep(content, result)

    # Hash for dedup
    result["content_hash"] = hashlib.sha256(content.encode()).hexdigest()[:16]

    return result


def _bite_python_deep(path: Path, content: str, result: dict) -> dict:
    """Deep extraction for Python files."""
    imports = RE_IMPORT.findall(content)
    if imports:
        result["extractable"].append({"type": "imports", "values": imports})
        result["signals"].append(f"imports:{len(imports)}")

    defs = RE_DEF.findall(content)
    if defs:
        result["extractable"].append({"type": "definitions", "values": defs})
        result["signals"].append(f"definitions:{len(defs)}")

    docstrings = RE_DOCSTRING.findall(content)
    if docstrings:
        # Just the first one (module docstring)
        first_doc = docstrings[0].strip()[:200]
        result["extractable"].append({"type": "docstring", "values": [first_doc]})

    # Check if it has a main entry point
    if "if __name__" in content:
        result["signals"].append("has_main")
        result["ore_rating"] = max(result["ore_rating"], 3)

    # Check for argparse (CLI tool)
    if "argparse" in content or "typer" in content or "click" in content:
        result["signals"].append("has_cli")
        result["ore_rating"] = max(result["ore_rating"], 4)

    return result


def _bite_ps1_deep(content: str, result: dict) -> dict:
    """Deep extraction for PowerShell files."""
    functions = re.findall(r"function\s+([\w-]+)", content)
    if functions:
        result["extractable"].append({"type": "ps1_functions", "values": functions})
        result["signals"].append(f"ps1_functions:{len(functions)}")

    params = re.findall(r"\[Parameter\(", content)
    if params:
        result["signals"].append(f"ps1_params:{len(params)}")
        result["ore_rating"] = max(result["ore_rating"], 3)

    return result


def _bite_markdown_deep(content: str, result: dict) -> dict:
    """Deep extraction for Markdown files."""
    links = RE_MD_LINK.findall(content)
    if links:
        result["extractable"].append({"type": "md_links", "values": [f"[{l}]({t})" for l, t in links[:20]]})
        result["signals"].append(f"md_links:{len(links)}")

    headings = re.findall(r"^(#{1,3})\s+(.+)", content, re.MULTILINE)
    if headings:
        result["extractable"].append({"type": "md_headings", "values": [h for _, h in headings[:15]]})

    return result


def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)

# ---------------------------------------------------------------------------
# CHEW — extract value from a file
# ---------------------------------------------------------------------------

def chew(path: Path) -> dict:
    """Extract all intelligence from a file."""
    assessment = bite(path, deep=True)
    if "error" in assessment:
        return assessment

    extract: dict = {
        "source": assessment["path"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ore_rating": assessment["ore_rating"],
        "category": assessment["category"],
        "signals": assessment["signals"],
        "intelligence": {},
    }

    # Compile intelligence from extractables
    for item in assessment.get("extractable", []):
        extract["intelligence"][item["type"]] = item["values"]

    extract["content_hash"] = assessment.get("content_hash", "")
    return extract

# ---------------------------------------------------------------------------
# DIGEST — write an intelligence extract file
# ---------------------------------------------------------------------------

def digest(path: Path, output_dir: Path | None = None) -> dict:
    """Write an intelligence extract alongside the file."""
    intelligence = chew(path)
    if "error" in intelligence:
        return intelligence

    out_dir = output_dir or INTAKE
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write the extract
    extract_name = f".zombie_extract_{path.stem}.json"
    extract_path = out_dir / extract_name
    extract_path.write_text(json.dumps(intelligence, indent=2) + "\n", encoding="utf-8")

    # Update memory
    mem = load_memory()
    mem["files_consumed"] += 1
    mem["total_patterns_extracted"] += len(intelligence.get("intelligence", {}))

    for imp in intelligence.get("intelligence", {}).get("imports", []):
        if imp not in mem["total_imports_seen"]:
            mem["total_imports_seen"].append(imp)

    for sid in intelligence.get("intelligence", {}).get("sid", []):
        if sid not in mem["total_sids_seen"]:
            mem["total_sids_seen"].append(sid)

    for fn in intelligence.get("intelligence", {}).get("definitions", []):
        if fn not in mem["total_functions_seen"]:
            mem["total_functions_seen"].append(fn)

    # Track cluster signals
    cat = intelligence.get("category", "unknown")
    mem["cluster_signals"][cat] = mem["cluster_signals"].get(cat, 0) + 1

    save_memory(mem)

    return {
        "status": "digested",
        "extract_path": str(extract_path.relative_to(ROOT)),
        "ore_rating": intelligence["ore_rating"],
        "intelligence_keys": list(intelligence.get("intelligence", {}).keys()),
    }

# ---------------------------------------------------------------------------
# EXCRETE — move consumed file to dumpster-dive/intake/
# ---------------------------------------------------------------------------

def excrete(path: Path, batch_name: str | None = None, dry_run: bool = False) -> dict:
    """Git mv the file to dumpster-dive/intake/ with a receipt."""
    if not path.exists():
        return {"error": f"Path not found: {path}"}

    rel = safe_relative(path)
    batch = batch_name or f"zombie-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}"
    target_dir = INTAKE / batch
    target = target_dir / path.name

    if dry_run:
        return {
            "status": "dry_run",
            "source": rel,
            "target": str(target.relative_to(ROOT)),
            "batch": batch,
        }

    target_dir.mkdir(parents=True, exist_ok=True)

    # git mv for tracked files, regular mv for untracked
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(path)],
        cwd=str(ROOT), capture_output=True, text=True,
    )
    if proc.returncode == 0:
        subprocess.run(
            ["git", "mv", str(path), str(target)],
            cwd=str(ROOT), check=True,
        )
    else:
        import shutil
        shutil.move(str(path), str(target))

    # Write receipt
    receipt = {
        "consumed": rel,
        "destination": str(target.relative_to(ROOT)),
        "batch": batch,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    receipt_path = target_dir / f".zombie_receipt_{path.stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    # Log to memory
    mem = load_memory()
    mem["consumption_log"].append(receipt)
    save_memory(mem)

    return {"status": "excreted", **receipt}

# ---------------------------------------------------------------------------
# FEED — full pipeline: bite → chew → digest → excrete
# ---------------------------------------------------------------------------

def feed(path: Path, batch_name: str | None = None, dry_run: bool = False) -> dict:
    """Full consumption pipeline."""
    assessment = bite(path, deep=True)
    if "error" in assessment:
        return assessment

    if dry_run:
        batch = batch_name or f"zombie-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}"
        target_dir = INTAKE / batch
        return {
            "status": "dry_run",
            "source": assessment["path"],
            "target": str((target_dir / path.name).relative_to(ROOT)),
            "ore_rating": assessment["ore_rating"],
            "category": assessment["category"],
            "signals": assessment["signals"],
            "extractable_count": len(assessment.get("extractable", [])),
        }

    # Digest first (extracts intelligence)
    digest_result = digest(path, output_dir=INTAKE / (batch_name or "zombie-extracts"))

    # Then excrete (moves the file)
    excrete_result = excrete(path, batch_name=batch_name)

    return {
        "status": "consumed",
        "digest": digest_result,
        "excrete": excrete_result,
    }

# ---------------------------------------------------------------------------
# HUNGER — scan repo for consumable candidates
# ---------------------------------------------------------------------------

HUNGER_ZONES = [
    ROOT,                    # root-level strays
    ROOT / "scripts",        # scripts/ dead weight
]

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "target",
    "dumpster-dive", "corpse-vault",  # already consumed
}


def hunger() -> list[dict]:
    """Scan the repo for files the zombie wants to eat."""
    candidates = []

    for zone in HUNGER_ZONES:
        if not zone.exists():
            continue
        for item in zone.iterdir():
            if item.is_dir() and item.name in SKIP_DIRS:
                continue
            if item.is_dir():
                continue  # only top-level files in each zone

            name = item.name

            # Backup files — always hungry
            if BACKUP_PATTERNS.search(name):
                assessment = bite(item)
                assessment["hunger_reason"] = "backup_file"
                candidates.append(assessment)
                continue

            # Legacy markers
            if LEGACY_PATTERNS.search(name):
                assessment = bite(item)
                assessment["hunger_reason"] = "legacy_marker"
                candidates.append(assessment)
                continue

            # Recovered files
            if RECOVERED_PATTERNS.search(name):
                assessment = bite(item)
                assessment["hunger_reason"] = "recovered_salvage"
                candidates.append(assessment)
                continue

            # Root-level Python files (strays)
            if zone == ROOT and item.suffix == ".py":
                assessment = bite(item)
                assessment["hunger_reason"] = "root_level_stray"
                candidates.append(assessment)
                continue

    # Sort by ore rating (lowest first — eat the weakest)
    candidates.sort(key=lambda c: c.get("ore_rating", 0))
    return candidates

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zombie Consumer — feeds on dead files, extracts intelligence, routes to the forge."
    )
    sub = parser.add_subparsers(dest="command")

    p_bite = sub.add_parser("bite", help="Assess a file for ore signals")
    p_bite.add_argument("path", type=Path)
    p_bite.add_argument("--deep", action="store_true", help="Full extraction scan")
    p_bite.add_argument("--json", action="store_true")

    p_chew = sub.add_parser("chew", help="Extract intelligence from a file")
    p_chew.add_argument("path", type=Path)
    p_chew.add_argument("--json", action="store_true")

    p_digest = sub.add_parser("digest", help="Write intelligence extract + rate ore")
    p_digest.add_argument("path", type=Path)

    p_excrete = sub.add_parser("excrete", help="Git mv file to dumpster-dive/intake/")
    p_excrete.add_argument("path", type=Path)
    p_excrete.add_argument("--batch", type=str, default=None)
    p_excrete.add_argument("--dry-run", action="store_true")

    p_feed = sub.add_parser("feed", help="Full pipeline: bite + chew + digest + excrete")
    p_feed.add_argument("path", type=Path)
    p_feed.add_argument("--batch", type=str, default=None)
    p_feed.add_argument("--dry-run", action="store_true")

    p_hunger = sub.add_parser("hunger", help="Scan repo for consumable candidates")
    p_hunger.add_argument("--json", action="store_true")

    p_memory = sub.add_parser("memory", help="Show what the zombie has learned")
    p_memory.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "bite":
        result = bite(args.path.resolve(), deep=args.deep)
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            print(f"BITE: {result.get('path', result.get('error', '?'))}")
            print(f"  Category: {result.get('category', '?')}")
            print(f"  Ore Rating: {result.get('ore_rating', '?')}/5")
            print(f"  Size: {result.get('size_lines', '?')} lines, {result.get('size_bytes', 0)} bytes")
            print(f"  Signals: {', '.join(result.get('signals', []))}")
            for ex in result.get("extractable", []):
                print(f"  Extractable [{ex['type']}]: {len(ex['values'])} items")
        return 0

    if args.command == "chew":
        result = chew(args.path.resolve())
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            print(f"CHEW: {result.get('source', result.get('error', '?'))}")
            print(f"  Ore Rating: {result.get('ore_rating', '?')}/5")
            for key, vals in result.get("intelligence", {}).items():
                print(f"  [{key}]: {len(vals) if isinstance(vals, list) else '1'} items")
        return 0

    if args.command == "digest":
        result = digest(args.path.resolve())
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        print(f"DIGEST: {result.get('extract_path', '?')}")
        print(f"  Ore Rating: {result.get('ore_rating', '?')}/5")
        print(f"  Intelligence: {', '.join(result.get('intelligence_keys', []))}")
        return 0

    if args.command == "excrete":
        result = excrete(args.path.resolve(), batch_name=args.batch, dry_run=args.dry_run)
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        if result.get("status") == "dry_run":
            print(f"DRY RUN: {result['source']} -> {result['target']}")
        else:
            print(f"EXCRETED: {result['consumed']} -> {result['destination']}")
        return 0

    if args.command == "feed":
        result = feed(args.path.resolve(), batch_name=args.batch, dry_run=args.dry_run)
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        if result.get("status") == "dry_run":
            print(f"DRY RUN FEED: {result['source']}")
            print(f"  -> {result['target']}")
            print(f"  Ore Rating: {result['ore_rating']}/5")
            print(f"  Category: {result['category']}")
            print(f"  Signals: {', '.join(result['signals'])}")
            print(f"  Extractable items: {result['extractable_count']}")
        else:
            print(f"CONSUMED: {result['excrete']['consumed']}")
            print(f"  -> {result['excrete']['destination']}")
            print(f"  Intelligence: {', '.join(result['digest'].get('intelligence_keys', []))}")
        return 0

    if args.command == "hunger":
        candidates = hunger()
        if getattr(args, "json", False):
            print(json.dumps(candidates, indent=2))
        else:
            if not candidates:
                print("The zombie is sated. No obvious candidates found.")
            else:
                print(f"HUNGER: {len(candidates)} candidate(s) found\n")
                for c in candidates:
                    print(f"  [{c.get('ore_rating', '?')}/5] {c.get('path', '?')}")
                    print(f"    Category: {c.get('category', '?')} | Reason: {c.get('hunger_reason', '?')}")
                    print(f"    Signals: {', '.join(c.get('signals', []))}")
                    print()
        return 0

    if args.command == "memory":
        mem = load_memory()
        if getattr(args, "json", False):
            print(json.dumps(mem, indent=2))
        else:
            print("ZOMBIE MEMORY")
            print(f"  Files consumed: {mem.get('files_consumed', 0)}")
            print(f"  Patterns extracted: {mem.get('total_patterns_extracted', 0)}")
            print(f"  Unique imports seen: {len(mem.get('total_imports_seen', []))}")
            print(f"  Unique SIDs seen: {len(mem.get('total_sids_seen', []))}")
            print(f"  Unique functions seen: {len(mem.get('total_functions_seen', []))}")
            print(f"  Cluster signals: {json.dumps(mem.get('cluster_signals', {}))}")
            log = mem.get("consumption_log", [])
            if log:
                print(f"\n  Last 5 meals:")
                for entry in log[-5:]:
                    print(f"    {entry.get('consumed', '?')} -> {entry.get('destination', '?')}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
