#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: zombie_consumer.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

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

The zombie evolves through three feedback mechanisms:
  1. Adaptive Bite Heuristics — cluster_profiles adjust ore_rating from meal history
  2. Import Graph Intelligence — tracks co-occurrence, detects redundancy, skips duplicates
  3. Forge Feedback Loop  — reads forge outcomes, backpropagates into ore predictions

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
    uv run scripts/zombie_consumer.py stats                    # polars analytics on consumption_log
    uv run scripts/zombie_consumer.py learn                    # read forge outcomes, adjust heuristics
    uv run scripts/zombie_consumer.py profiles                 # show adaptive cluster profiles
    uv run scripts/zombie_consumer.py imports                  # show import graph intelligence
    uv run scripts/zombie_consumer.py graph                    # networkx graph analysis + centrality
    uv run scripts/zombie_consumer.py graph --dot out.dot      # export DOT for Graphviz

@SID:           TOOL_ZOMBIE_CONSUMER_V1
@Shabti:        CLI Script
@Purpose:       Zombie Consumer — feeds on codebase dead files, extracts intelligence, routes remains to the forge.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
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

def _empty_memory() -> dict:
    return {
        "schema_version": 2,
        "created": datetime.now(timezone.utc).isoformat(),
        "files_consumed": 0,
        "total_patterns_extracted": 0,
        "total_imports_seen": [],
        "total_sids_seen": [],
        "total_functions_seen": [],
        "cluster_signals": {},
        # --- Upgrade 1: Adaptive Bite Heuristics ---
        "cluster_profiles": {},
        # --- Upgrade 2: Import Graph Intelligence ---
        "import_graph": {},
        "content_hashes_seen": [],
        # --- Upgrade 3: Forge Feedback Loop ---
        "forge_feedback": {
            "total_tempered": 0,
            "total_slag": 0,
            "ore_prediction_errors": [],
        },
        "consumption_log": [],
    }


def _migrate_memory(mem: dict) -> dict:
    """Forward-migrate schema 1 → 2 without data loss."""
    if mem.get("schema_version", 1) >= 2:
        return mem
    mem["schema_version"] = 2
    mem.setdefault("cluster_profiles", {})
    mem.setdefault("import_graph", {})
    mem.setdefault("content_hashes_seen", [])
    mem.setdefault("forge_feedback", {
        "total_tempered": 0,
        "total_slag": 0,
        "ore_prediction_errors": [],
    })
    return mem


def load_memory() -> dict:
    if MEMORY_PATH.exists():
        mem = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        return _migrate_memory(mem)
    return _empty_memory()


def save_memory(mem: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    mem["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_PATH.write_text(json.dumps(mem, indent=2) + "\n", encoding="utf-8")


def _load_polars():
    import polars as pl
    return pl


def _consumption_log_frame(mem: dict):
    """Materialize consumption_log into a polars frame for fast grouping."""
    pl = _load_polars()
    rows: list[dict] = []
    for idx, entry in enumerate(mem.get("consumption_log", []), start=1):
        consumed = entry.get("consumed", "")
        destination = entry.get("destination", "")
        batch = entry.get("batch", "")
        timestamp = entry.get("timestamp")
        try:
            ts = datetime.fromisoformat(timestamp) if timestamp else None
        except ValueError:
            ts = None
        rows.append({
            "meal_index": idx,
            "consumed": consumed,
            "destination": destination,
            "batch": batch,
            "source_ext": Path(consumed).suffix.lower() or "(none)",
            "destination_ext": Path(destination).suffix.lower() or "(none)",
            "source_name": Path(consumed).name,
            "destination_name": Path(destination).name,
            "timestamp": ts,
        })
    if not rows:
        return pl.DataFrame(
            schema={
                "meal_index": pl.Int64,
                "consumed": pl.Utf8,
                "destination": pl.Utf8,
                "batch": pl.Utf8,
                "source_ext": pl.Utf8,
                "destination_ext": pl.Utf8,
                "source_name": pl.Utf8,
                "destination_name": pl.Utf8,
                "timestamp": pl.Datetime(time_unit="us", time_zone="UTC"),
            }
        )
    return pl.DataFrame(rows)


def _cluster_profiles_frame(mem: dict):
    pl = _load_polars()
    rows = []
    for category, profile in mem.get("cluster_profiles", {}).items():
        rows.append({
            "category": category,
            "count": profile.get("count", 0),
            "avg_ore": profile.get("avg_ore", 0.0),
            "avg_extractable": profile.get("avg_extractable", 0.0),
            "yield_rate": profile.get("yield_rate", 0.0),
        })
    if not rows:
        return pl.DataFrame(
            schema={
                "category": pl.Utf8,
                "count": pl.Int64,
                "avg_ore": pl.Float64,
                "avg_extractable": pl.Float64,
                "yield_rate": pl.Float64,
            }
        )
    return pl.DataFrame(rows).sort(["avg_ore", "count"], descending=[True, True])


def build_stats(mem: dict) -> dict:
    """Polars-backed analytics for the zombie's current memory."""
    log_df = _consumption_log_frame(mem)
    profiles_df = _cluster_profiles_frame(mem)

    stage_counts: list[dict] = []
    ext_counts: list[dict] = []
    batch_counts: list[dict] = []
    top_profiles: list[dict] = []

    if log_df.height:
        stage_counts = (
            log_df.with_columns(
                batch_root=log_df["batch"].str.split("/").list.get(0).fill_null("(none)")
            )
            .group_by("batch_root")
            .len()
            .sort("len", descending=True)
            .rename({"len": "count"})
            .to_dicts()
        )
        ext_counts = (
            log_df.group_by("source_ext")
            .len()
            .sort("len", descending=True)
            .rename({"source_ext": "ext", "len": "count"})
            .to_dicts()
        )
        batch_counts = (
            log_df.group_by("batch")
            .len()
            .sort("len", descending=True)
            .head(8)
            .rename({"len": "count"})
            .to_dicts()
        )

    if profiles_df.height:
        top_profiles = profiles_df.head(8).to_dicts()

    return {
        "files_consumed": mem.get("files_consumed", 0),
        "target_200_remaining": max(0, 200 - mem.get("files_consumed", 0)),
        "distinct_batches": log_df["batch"].n_unique() if log_df.height else 0,
        "distinct_extensions": log_df["source_ext"].n_unique() if log_df.height else 0,
        "stage_counts": stage_counts,
        "extension_counts": ext_counts,
        "batch_counts": batch_counts,
        "top_profiles": top_profiles,
    }


# ---------------------------------------------------------------------------
# Upgrade 1 — Adaptive Bite Heuristics (steal from tensor weights)
# ---------------------------------------------------------------------------

def _update_cluster_profile(mem: dict, category: str, ore_rating: int, extractable_count: int) -> None:
    """Update running statistics for a category — called after each digest."""
    profiles = mem.setdefault("cluster_profiles", {})
    p = profiles.get(category)
    if p is None:
        p = {"count": 0, "ore_sum": 0, "extractable_sum": 0, "top_signals": {}}
        profiles[category] = p
    p["count"] += 1
    p["ore_sum"] += ore_rating
    p["extractable_sum"] += extractable_count
    p["avg_ore"] = round(p["ore_sum"] / p["count"], 2)
    p["avg_extractable"] = round(p["extractable_sum"] / p["count"], 2)
    p["yield_rate"] = round(
        sum(1 for _ in range(p["count"]) if p["avg_extractable"] > 0.5) / max(p["count"], 1), 2
    )


def _adaptive_ore_rating(category: str, base_rating: int, mem: dict) -> tuple[int, bool]:
    """Adjust ore_rating from cluster history. Returns (adjusted_rating, auto_deep)."""
    profiles = mem.get("cluster_profiles", {})
    p = profiles.get(category)
    if p is None or p.get("count", 0) < 3:
        return base_rating, False  # not enough data to learn from
    learned_ore = round(p["avg_ore"])
    # Bonus: high-yield categories auto-deepen
    auto_deep = p.get("yield_rate", 0) > 0.6
    # Penalty: categories that consistently produce nothing get downgraded
    if p.get("avg_extractable", 0) < 0.3 and p["count"] >= 5:
        learned_ore = max(1, learned_ore - 1)
    return max(1, min(5, learned_ore)), auto_deep


# ---------------------------------------------------------------------------
# Upgrade 2 — Import Graph Intelligence (steal from pool exclusion)
# ---------------------------------------------------------------------------

def _update_import_graph(mem: dict, imports: list[str], ore_rating: int) -> None:
    """Track import co-occurrence and ore correlation."""
    graph = mem.setdefault("import_graph", {})
    import_set = set(imports)
    for imp in imports:
        node = graph.get(imp)
        if node is None:
            node = {"seen": 0, "ore_sum": 0, "co_occurs": {}}
            graph[imp] = node
        node["seen"] += 1
        node["ore_sum"] += ore_rating
        node["ore_avg"] = round(node["ore_sum"] / node["seen"], 2)
        for other in import_set - {imp}:
            node["co_occurs"][other] = node["co_occurs"].get(other, 0) + 1


def _import_redundancy_score(imports: list[str], mem: dict) -> float:
    """0.0 = novel, 1.0 = fully redundant (already seen everything)."""
    graph = mem.get("import_graph", {})
    if not imports or not graph:
        return 0.0
    known = sum(1 for i in imports if i in graph)
    return round(known / len(imports), 2)


def _is_content_duplicate(content_hash: str, mem: dict) -> bool:
    """Check if this exact content was already consumed."""
    return content_hash in mem.get("content_hashes_seen", [])


# ---------------------------------------------------------------------------
# Upgrade 3 — Forge Feedback Loop (steal from tensor feedback)
# ---------------------------------------------------------------------------

FORGE_STATES = {
    "tempered": ROOT / "dumpster-dive" / "forge" / "tempered",
    "slag":     ROOT / "dumpster-dive" / "forge" / "slag",
    "anvil":    ROOT / "dumpster-dive" / "forge" / "anvil",
    "furnace":  ROOT / "dumpster-dive" / "forge" / "furnace",
    "quench":   ROOT / "dumpster-dive" / "forge" / "quench",
    "intake":   ROOT / "dumpster-dive" / "forge" / "intake",
}


def _scan_forge_outcomes() -> list[dict]:
    """Read forge state directories and match against consumption log."""
    outcomes: list[dict] = []
    for state, state_dir in FORGE_STATES.items():
        if not state_dir.exists():
            continue
        for item in state_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                outcomes.append({
                    "name": item.name,
                    "forge_state": state,
                    "path": str(item.relative_to(ROOT)),
                })
    return outcomes


def learn_from_forge(mem: dict) -> dict:
    """Backpropagate forge outcomes into zombie heuristics.

    If a file the zombie rated ore-4 ended up in SLAG → the heuristics were wrong.
    If a file rated ore-2 reached TEMPERED → the zombie was too conservative.
    """
    feedback = mem.setdefault("forge_feedback", {
        "total_tempered": 0, "total_slag": 0, "ore_prediction_errors": [],
    })
    log = mem.get("consumption_log", [])
    consumed_names = {Path(e["consumed"]).name: e for e in log}

    outcomes = _scan_forge_outcomes()
    new_lessons = 0

    already_seen = {e.get("file") for e in feedback.get("ore_prediction_errors", [])}

    for outcome in outcomes:
        name = outcome["name"]
        if name not in consumed_names or name in already_seen:
            continue

        entry = consumed_names[name]
        # Find the extract to get the zombie's original ore prediction
        extract_stem = f".zombie_extract_{Path(name).stem}_"
        extract_candidates = list(INTAKE.rglob(f"{extract_stem}*.json"))
        if not extract_candidates:
            continue

        extract = json.loads(extract_candidates[0].read_text(encoding="utf-8"))
        predicted_ore = extract.get("ore_rating", 3)
        forge_state = outcome["forge_state"]

        # Score the forge outcome
        forge_ore = {"tempered": 5, "quench": 4, "furnace": 3, "anvil": 3, "intake": 2, "slag": 1}
        actual_ore = forge_ore.get(forge_state, 3)
        error = actual_ore - predicted_ore

        if abs(error) >= 1:
            category = extract.get("category", "unknown")
            feedback["ore_prediction_errors"].append({
                "file": name,
                "predicted": predicted_ore,
                "actual": actual_ore,
                "forge_state": forge_state,
                "error": error,
                "category": category,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Adjust cluster profile based on forge reality
            profiles = mem.get("cluster_profiles", {})
            if category in profiles:
                p = profiles[category]
                # Weighted correction: nudge avg_ore toward actual
                correction = error * 0.3  # 30% learning rate
                p["avg_ore"] = round(max(1.0, min(5.0, p["avg_ore"] + correction)), 2)
            new_lessons += 1

        if forge_state == "tempered":
            feedback["total_tempered"] = feedback.get("total_tempered", 0) + 1
        elif forge_state == "slag":
            feedback["total_slag"] = feedback.get("total_slag", 0) + 1

    return {
        "outcomes_scanned": len(outcomes),
        "consumed_matched": len([o for o in outcomes if o["name"] in consumed_names]),
        "new_lessons": new_lessons,
        "total_errors": len(feedback.get("ore_prediction_errors", [])),
    }

# ---------------------------------------------------------------------------
# BITE — assess a file for ore signals
# ---------------------------------------------------------------------------

def bite(path: Path, deep: bool = False) -> dict:
    """Scan a file and return ore assessment.

    The zombie learns: if cluster_profiles exist in memory, ore_rating and
    deep-scan decisions are adjusted based on what prior meals taught us.
    """
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

    # Categorize (static baseline)
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

    # --- Upgrade 1: Adaptive Bite Heuristics ---
    mem = load_memory()
    adapted_ore, auto_deep = _adaptive_ore_rating(
        result["category"], result["ore_rating"], mem,
    )
    if adapted_ore != result["ore_rating"]:
        result["signals"].append(f"ore_adapted:{result['ore_rating']}->{adapted_ore}")
        result["ore_rating"] = adapted_ore
    if auto_deep and not deep:
        deep = True
        result["signals"].append("auto_deep_from_history")

    # --- Upgrade 2: Content dedup check ---
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    if _is_content_duplicate(content_hash, mem):
        result["signals"].append("content_duplicate")
        result["ore_rating"] = max(1, result["ore_rating"] - 1)

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

    # --- Upgrade 2: Import redundancy scoring ---
    imports_found = [
        v for ex in result.get("extractable", [])
        if ex["type"] == "imports" for v in ex["values"]
    ]
    if imports_found:
        redundancy = _import_redundancy_score(imports_found, mem)
        result["import_redundancy"] = redundancy
        if redundancy > 0.8:
            result["signals"].append(f"high_import_redundancy:{redundancy}")
            result["ore_rating"] = max(1, result["ore_rating"] - 1)

    # Hash for dedup
    result["content_hash"] = content_hash

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


def _artifact_stem(path: Path) -> str:
    """Stable per-source stem so duplicate basenames do not collide in one batch."""
    rel = safe_relative(path)
    digest = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:8]
    return f"{path.stem}_{digest}"


def _artifact_filename(path: Path) -> str:
    stem = _artifact_stem(path)
    return f"{stem}{path.suffix}" if path.suffix else stem


def _git_output(*args: str) -> str | None:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _build_bride_provenance(path: Path, assessment: dict) -> dict:
    """Inline Novia-style provenance without invoking the unfinished embalm tool."""
    source = safe_relative(path)
    return {
        "operator": "Novia Cadaveris",
        "forge_matriarch": "Sister Ferrum Scoriae",
        "pathway": "zombie -> bridge -> forge",
        "source_file": source,
        "hash": assessment.get("content_hash", ""),
        "content_hash": assessment.get("content_hash", ""),
        "language": path.suffix.lower() or "(none)",
        "byte_size": assessment.get("size_bytes", 0),
        "line_count": assessment.get("size_lines", 0),
        "category": assessment.get("category", "unknown"),
        "signals": assessment.get("signals", []),
        "landmarks": {
            item["type"]: item["values"]
            for item in assessment.get("extractable", [])
        },
        "head_commit": _git_output("rev-parse", "HEAD") or "unknown",
        "git_status": _git_output("status", "--porcelain", "--", source) or "clean",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "canon": {
            "dumpster_domain": "dumpster-dive",
            "corpse_axis": "Novia Cadaveris",
            "forge_axis": "Sister Ferrum Scoriae",
        },
    }


def _load_forge_bridge_module():
    module_path = ROOT / "scripts" / "zombie_forge_bridge.py"
    spec = importlib.util.spec_from_file_location("zombie_forge_bridge_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load forge bridge module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
    extract["provenance"] = _build_bride_provenance(path, assessment)
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
    extract_name = f".zombie_extract_{_artifact_stem(path)}.json"
    extract_path = out_dir / extract_name
    extract_path.write_text(json.dumps(intelligence, indent=2) + "\n", encoding="utf-8")

    # Update memory
    mem = load_memory()
    mem["files_consumed"] += 1
    intel = intelligence.get("intelligence", {})
    mem["total_patterns_extracted"] += len(intel)

    for imp in intel.get("imports", []):
        if imp not in mem["total_imports_seen"]:
            mem["total_imports_seen"].append(imp)

    for sid in intel.get("sid", []):
        if sid not in mem["total_sids_seen"]:
            mem["total_sids_seen"].append(sid)

    for fn in intel.get("definitions", []):
        if fn not in mem["total_functions_seen"]:
            mem["total_functions_seen"].append(fn)

    # Track cluster signals (v1 compat)
    cat = intelligence.get("category", "unknown")
    mem["cluster_signals"][cat] = mem["cluster_signals"].get(cat, 0) + 1

    # --- Upgrade 1: Update cluster profile with actual extraction stats ---
    extractable_count = len(intel)
    _update_cluster_profile(mem, cat, intelligence.get("ore_rating", 3), extractable_count)

    # --- Upgrade 2: Update import graph + content hash registry ---
    imports_found = intel.get("imports", [])
    if imports_found:
        _update_import_graph(mem, imports_found, intelligence.get("ore_rating", 3))

    content_hash = intelligence.get("content_hash", "")
    if content_hash:
        hashes = mem.setdefault("content_hashes_seen", [])
        if content_hash not in hashes:
            hashes.append(content_hash)

    save_memory(mem)

    return {
        "status": "digested",
        "extract_path": str(extract_path.relative_to(ROOT)),
        "ore_rating": intelligence["ore_rating"],
        "intelligence_keys": list(intelligence.get("intelligence", {}).keys()),
    }


def _update_extract_metadata(extract_path: Path, updates: dict) -> None:
    """Patch extract metadata after excrete so bridge routing has canonical intake paths."""
    if not extract_path.exists():
        return
    data = json.loads(extract_path.read_text(encoding="utf-8"))
    data.update(updates)
    extract_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

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
    target_name = path.name
    if (target_dir / target_name).exists():
        target_name = _artifact_filename(path)
    target = target_dir / target_name

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
    receipt_path = target_dir / f".zombie_receipt_{_artifact_stem(path)}.json"
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

    batch = batch_name or f"zombie-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}"

    if dry_run:
        target_dir = INTAKE / batch
        forge_bridge = _load_forge_bridge_module()
        stage = forge_bridge._resolve_stage(assessment["ore_rating"], assessment["signals"])
        return {
            "status": "dry_run",
            "source": assessment["path"],
            "target": str((target_dir / path.name).relative_to(ROOT)),
            "ore_rating": assessment["ore_rating"],
            "category": assessment["category"],
            "signals": assessment["signals"],
            "extractable_count": len(assessment.get("extractable", [])),
            "forge_stage": stage,
        }

    batch_dir = INTAKE / batch

    # Digest into the same batch directory the companion file will occupy.
    digest_result = digest(path, output_dir=batch_dir)

    # Then excrete (moves the file)
    excrete_result = excrete(path, batch_name=batch)

    extract_path = ROOT / digest_result["extract_path"]
    intake_destination = excrete_result["destination"].replace("\\", "/")
    _update_extract_metadata(
        extract_path,
        {
            "batch": batch,
            "intake_destination": intake_destination,
            "intake_companion": Path(intake_destination).name,
        },
    )

    forge_bridge = _load_forge_bridge_module()
    routed_hashes = forge_bridge.load_routed_hashes()
    bridge_result = forge_bridge.route_file(
        extract_path,
        json.loads(extract_path.read_text(encoding="utf-8")),
        routed_hashes,
        dry_run=False,
    )

    # Digest boundary artifacts into manifests so the zombie family stays compact.
    forge_bridge.compact_sidecars(surface="intake", batch_filter=batch, apply=True)
    if bridge_result.get("stage"):
        forge_bridge.compact_sidecars(surface="forge", stage_filter=bridge_result["stage"], apply=True)

    return {
        "status": "consumed",
        "digest": digest_result,
        "excrete": excrete_result,
        "bridge": bridge_result,
    }

# ---------------------------------------------------------------------------
# HUNGER — scan repo for consumable candidates
# ---------------------------------------------------------------------------

HUNGER_ZONES = [
    {"path": ROOT, "recursive": False, "label": "root"},
    {"path": ROOT / "scripts", "recursive": True, "label": "scripts_recursive"},
    {"path": ROOT / "claude-codex-gemini", "recursive": True, "label": "triadic_recursive"},
    {"path": ROOT / "artifacts", "recursive": False, "label": "artifacts_snapshots"},
]

# Build artifacts and frozen snapshots
BUILD_ARTIFACT_PATTERNS = re.compile(
    r"\.(o|obj|log|pdb|ilk|exp|lib|dll|so|dylib)$"
    r"|^NUL\."
    r"|^mkmf\.log$",
    re.IGNORECASE,
)
FROZEN_SNAPSHOT_PATTERNS = re.compile(
    r"\.frozen\."
    r"|\.backup\."
    r"|\.snapshot\."
    r"|^hf_discovery_spaces_"
    r"|^hf_mcp_.*\.(json|registry\.json)$"
    r"|^mcp_run_",
    re.IGNORECASE,
)

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "target",
    "dumpster-dive", "corpse-vault",  # already consumed
}

ROOT_JSON_TEMP_NAMES = {
    "cargo_test.json",
    "status_test.json",
    "validate_test.json",
    "meta_cli_test.json",
    "scan_audit_tmp.json",
    "server_debug.json",
    "collisions_tmp.json",
    "kcp_batch1_verify.json",
    "stage2_1_audit.json",
    "stage2_1_final_audit.json",
    "stage2_1_recolor_audit.json",
    "stage2_1_round3_audit.json",
}

HUNGER_GLOB_PATTERNS = [
    "extensions/*/legacy.package.snapshot.json",
    "extensions/*/*.vsix",
    "extensions/chthonic-archive/.chthonic/cache/insiders-post-restart-verify-*.json",
    "extensions/chthonic-archive/.chthonic/cache/insiders-post-restart-verify-latest.json",
    "extensions/chthonic-archive/.chthonic/ruby/vendor/bundle/**/mkmf.log",
]


def _iter_zone_files(zone_path: Path, recursive: bool):
    """Yield files from a hunger zone with skip-dir filtering."""
    if recursive:
        for item in zone_path.rglob("*"):
            if any(part in SKIP_DIRS for part in item.parts):
                continue
            if item.is_file():
                yield item
    else:
        for item in zone_path.iterdir():
            if item.is_dir() and item.name in SKIP_DIRS:
                continue
            if item.is_file():
                yield item


def hunger() -> list[dict]:
    """Scan the repo for files the zombie wants to eat."""
    candidates = []
    seen_paths: set[str] = set()

    def add_candidate(item: Path, reason: str) -> None:
        rel = safe_relative(item)
        if rel in seen_paths:
            return
        assessment = bite(item)
        assessment["hunger_reason"] = reason
        candidates.append(assessment)
        seen_paths.add(rel)

    for zone_cfg in HUNGER_ZONES:
        zone = zone_cfg["path"]
        recursive = zone_cfg.get("recursive", False)

        if not zone.exists():
            continue

        for item in _iter_zone_files(zone, recursive):

            name = item.name

            # Backup files — always hungry
            if BACKUP_PATTERNS.search(name):
                add_candidate(item, "backup_file")
                continue

            # Legacy markers
            if LEGACY_PATTERNS.search(name):
                add_candidate(item, "legacy_marker")
                continue

            # Recovered files
            if RECOVERED_PATTERNS.search(name):
                add_candidate(item, "recovered_salvage")
                continue

            # Root-level Python files (strays)
            if zone == ROOT and item.suffix == ".py":
                add_candidate(item, "root_level_stray")
                continue

            # Root-level JSON temporaries (Phase A seed set)
            if zone == ROOT and item.suffix == ".json" and name in ROOT_JSON_TEMP_NAMES:
                add_candidate(item, "root_json_temporary")
                continue

            # Build artifacts (any zone)
            if BUILD_ARTIFACT_PATTERNS.search(name):
                add_candidate(item, "build_artifact")
                continue

            # Frozen snapshots and timestamped runs (primarily artifacts/)
            if FROZEN_SNAPSHOT_PATTERNS.search(name):
                add_candidate(item, "frozen_snapshot")
                continue

    # Extension-cache seam: snapshot manifests, verify caches, packaged builds, and build logs.
    for pattern in HUNGER_GLOB_PATTERNS:
        for item in ROOT.glob(pattern):
            if not item.is_file():
                continue
            if item.suffix == ".vsix":
                add_candidate(item, "packaged_build_artifact")
            elif item.name == "mkmf.log":
                add_candidate(item, "build_artifact")
            elif "insiders-post-restart-verify" in item.name:
                add_candidate(item, "extension_verify_cache")
            else:
                add_candidate(item, "frozen_snapshot")

    # Sort by ore rating (lowest first — eat the weakest)
    candidates.sort(key=lambda c: c.get("ore_rating", 0))
    return candidates

# ---------------------------------------------------------------------------
# Wire 1 — NetworkX graph from import_graph memory
# ---------------------------------------------------------------------------

def build_nx_graph(mem: dict) -> "nx.DiGraph":
    """Build a NetworkX directed graph from the zombie's import_graph memory."""
    import networkx as nx

    graph_data = mem.get("import_graph", {})
    G = nx.DiGraph()

    for imp, node in graph_data.items():
        G.add_node(imp, seen=node.get("seen", 0), ore_avg=node.get("ore_avg", 0))
        for co_imp, weight in node.get("co_occurs", {}).items():
            G.add_edge(imp, co_imp, weight=weight)

    return G


def graph_centrality(G: "nx.DiGraph") -> dict[str, dict[str, float]]:
    """Compute centrality metrics for the import graph."""
    import networkx as nx

    if len(G) == 0:
        return {}

    # Use undirected view for betweenness/closeness (co-occurrence is symmetric)
    U = G.to_undirected()
    degree = dict(nx.degree_centrality(U))
    betweenness = dict(nx.betweenness_centrality(U))
    result = {}
    for node in G.nodes:
        result[node] = {
            "degree": round(degree.get(node, 0), 4),
            "betweenness": round(betweenness.get(node, 0), 4),
            "seen": G.nodes[node].get("seen", 0),
            "ore_avg": G.nodes[node].get("ore_avg", 0),
        }
    return result


def export_dot(G: "nx.DiGraph") -> str:
    """Export the import graph as DOT format for Graphviz."""
    lines = ["digraph zombie_imports {", '  rankdir=LR;', '  node [shape=box, style=filled];']

    for node, data in G.nodes(data=True):
        ore = data.get("ore_avg", 0)
        seen = data.get("seen", 0)
        # Color by ore: green=high, yellow=mid, red=low
        if ore >= 3.5:
            color = "#90EE90"
        elif ore >= 2.0:
            color = "#FFFF99"
        else:
            color = "#FFB3B3"
        label = f"{node}\\nore:{ore} seen:{seen}"
        lines.append(f'  "{node}" [label="{label}", fillcolor="{color}"];')

    for u, v, data in G.edges(data=True):
        weight = data.get("weight", 1)
        penwidth = max(1, min(4, weight))
        lines.append(f'  "{u}" -> "{v}" [penwidth={penwidth}, label="{weight}"];')

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Wire 2 — Rich rendering for all zombie output
# ---------------------------------------------------------------------------

def _get_console():
    from rich.console import Console
    return Console(force_terminal=True)


def _ore_bar(rating: float, width: int = 5) -> str:
    """Color-coded ore bar: green/yellow/red blocks (ASCII-safe)."""
    filled = round(rating)
    if rating >= 3.5:
        color = "green"
    elif rating >= 2.0:
        color = "yellow"
    else:
        color = "red"
    return f"[{color}]{'#' * filled}{'-' * (width - filled)}[/{color}] {rating}/5"


def _render_bite(result: dict) -> None:
    from rich.table import Table
    from rich.panel import Panel

    console = _get_console()
    if "error" in result:
        console.print(f"[red]ERROR:[/red] {result['error']}")
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Path", result.get("path", "?"))
    table.add_row("Category", result.get("category", "?"))
    table.add_row("Ore Rating", _ore_bar(result.get("ore_rating", 0)))
    table.add_row("Size", f"{result.get('size_lines', '?')} lines, {result.get('size_bytes', 0)} bytes")
    table.add_row("Signals", ", ".join(result.get("signals", [])) or "none")
    redundancy = result.get("import_redundancy")
    if redundancy is not None:
        table.add_row("Import Redundancy", f"{redundancy * 100:.0f}%")
    for ex in result.get("extractable", []):
        table.add_row(f"Extractable \\[{ex['type']}]", f"{len(ex['values'])} items")

    console.print(Panel(table, title="[bold]BITE[/bold]", border_style="dim"))


def _render_memory(mem: dict) -> None:
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns

    console = _get_console()

    # Core stats
    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column("Key", style="bold cyan")
    stats.add_column("Value")
    stats.add_row("Schema", f"v{mem.get('schema_version', '?')}")
    stats.add_row("Files consumed", str(mem.get("files_consumed", 0)))
    stats.add_row("Patterns extracted", str(mem.get("total_patterns_extracted", 0)))
    stats.add_row("Unique imports", str(len(mem.get("total_imports_seen", []))))
    stats.add_row("Unique SIDs", str(len(mem.get("total_sids_seen", []))))
    stats.add_row("Unique functions", str(len(mem.get("total_functions_seen", []))))
    stats.add_row("Content hashes", str(len(mem.get("content_hashes_seen", []))))
    console.print(Panel(stats, title="[bold]ZOMBIE MEMORY[/bold]", border_style="dim"))

    # Cluster signals
    signals = mem.get("cluster_signals", {})
    if signals:
        sig_table = Table(title="Cluster Signals", box=None)
        sig_table.add_column("Category", style="bold")
        sig_table.add_column("Count", justify="right")
        for cat, count in sorted(signals.items(), key=lambda kv: kv[1], reverse=True):
            sig_table.add_row(cat, str(count))
        console.print(sig_table)

    # Cluster profiles
    profiles = mem.get("cluster_profiles", {})
    if profiles:
        prof_table = Table(title="Cluster Profiles (Adaptive)", box=None)
        prof_table.add_column("Category", style="bold")
        prof_table.add_column("n", justify="right")
        prof_table.add_column("Avg Ore")
        prof_table.add_column("Avg Extract", justify="right")
        prof_table.add_column("Yield", justify="right")
        for cat, p in sorted(profiles.items(), key=lambda kv: kv[1].get("avg_ore", 0), reverse=True):
            yield_pct = f"{p.get('yield_rate', 0) * 100:.0f}%"
            prof_table.add_row(cat, str(p.get("count", 0)), _ore_bar(p.get("avg_ore", 0)),
                               str(p.get("avg_extractable", "?")), yield_pct)
        console.print(prof_table)

    # Import graph summary
    graph = mem.get("import_graph", {})
    if graph:
        ig_table = Table(title=f"Import Graph ({len(graph)} nodes)", box=None)
        ig_table.add_column("Import", style="bold")
        ig_table.add_column("Seen", justify="right")
        ig_table.add_column("Ore Avg")
        ig_table.add_column("Co-occurs", justify="right")
        top = sorted(graph.items(), key=lambda kv: kv[1].get("seen", 0), reverse=True)[:8]
        for imp, node in top:
            co = len(node.get("co_occurs", {}))
            ig_table.add_row(imp, str(node["seen"]), _ore_bar(node.get("ore_avg", 0)), str(co))
        console.print(ig_table)

    # Forge feedback
    fb = mem.get("forge_feedback", {})
    if fb and (fb.get("total_tempered", 0) or fb.get("total_slag", 0) or fb.get("ore_prediction_errors")):
        fb_table = Table(title="Forge Feedback", box=None)
        fb_table.add_column("Metric", style="bold cyan")
        fb_table.add_column("Value")
        fb_table.add_row("Tempered", str(fb.get("total_tempered", 0)))
        fb_table.add_row("Slag", str(fb.get("total_slag", 0)))
        errors = fb.get("ore_prediction_errors", [])
        fb_table.add_row("Prediction errors", str(len(errors)))
        console.print(fb_table)
        if errors:
            err_table = Table(title="Recent Prediction Errors", box=None)
            err_table.add_column("File", style="bold")
            err_table.add_column("Predicted")
            err_table.add_column("Actual")
            err_table.add_column("State")
            err_table.add_column("Error", justify="right")
            for e in errors[-5:]:
                color = "green" if e["error"] > 0 else "red"
                err_table.add_row(e["file"], str(e["predicted"]), str(e["actual"]),
                                  e["forge_state"], f"[{color}]{e['error']:+d}[/{color}]")
            console.print(err_table)

    # Last meals
    log = mem.get("consumption_log", [])
    if log:
        meal_table = Table(title="Last 5 Meals", box=None)
        meal_table.add_column("Source", style="bold")
        meal_table.add_column("Destination")
        for entry in log[-5:]:
            meal_table.add_row(entry.get("consumed", "?"), entry.get("destination", "?"))
        console.print(meal_table)


def _render_profiles(profiles: dict) -> None:
    from rich.table import Table

    console = _get_console()
    profiles_df = _cluster_profiles_frame({"cluster_profiles": profiles})
    if profiles_df.is_empty():
        console.print("[dim]No cluster profiles yet. Feed more files to build adaptive heuristics.[/dim]")
        return

    table = Table(title=f"Cluster Profiles ({profiles_df.height} categories)")
    table.add_column("Category", style="bold")
    table.add_column("Samples", justify="right")
    table.add_column("Avg Ore")
    table.add_column("Avg Extractable", justify="right")
    table.add_column("Yield Rate", justify="right")
    table.add_column("Auto-deep?", justify="center")

    for row in profiles_df.iter_rows(named=True):
        yield_rate = row["yield_rate"]
        yield_pct = f"{yield_rate * 100:.0f}%"
        auto_deep = "[green]yes[/green]" if yield_rate > 0.6 else "[dim]no[/dim]"
        table.add_row(
            row["category"],
            str(row["count"]),
            _ore_bar(row["avg_ore"]),
            str(row["avg_extractable"]),
            yield_pct,
            auto_deep,
        )

    console.print(table)


def _render_stats(stats: dict) -> None:
    from rich.panel import Panel
    from rich.table import Table

    console = _get_console()

    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Key", style="bold cyan")
    summary.add_column("Value")
    summary.add_row("Files consumed", str(stats["files_consumed"]))
    summary.add_row("Remaining to 200", str(stats["target_200_remaining"]))
    summary.add_row("Distinct batches", str(stats["distinct_batches"]))
    summary.add_row("Distinct extensions", str(stats["distinct_extensions"]))
    console.print(Panel(summary, title="[bold]ZOMBIE STATS (Polars)[/bold]", border_style="dim"))

    if stats["stage_counts"]:
        stage_table = Table(title="Batch Root Volume", box=None)
        stage_table.add_column("Batch Root", style="bold")
        stage_table.add_column("Meals", justify="right")
        for row in stats["stage_counts"][:8]:
            stage_table.add_row(row["batch_root"], str(row["count"]))
        console.print(stage_table)

    if stats["extension_counts"]:
        ext_table = Table(title="Top Source Extensions", box=None)
        ext_table.add_column("Extension", style="bold")
        ext_table.add_column("Meals", justify="right")
        for row in stats["extension_counts"][:8]:
            ext_table.add_row(row["ext"], str(row["count"]))
        console.print(ext_table)

    if stats["top_profiles"]:
        profile_table = Table(title="Top Cluster Profiles", box=None)
        profile_table.add_column("Category", style="bold")
        profile_table.add_column("Count", justify="right")
        profile_table.add_column("Avg Ore")
        profile_table.add_column("Yield", justify="right")
        for row in stats["top_profiles"]:
            profile_table.add_row(
                row["category"],
                str(row["count"]),
                _ore_bar(row["avg_ore"]),
                f"{row['yield_rate'] * 100:.0f}%",
            )
        console.print(profile_table)

    if stats["batch_counts"]:
        batch_table = Table(title="Top Batches", box=None)
        batch_table.add_column("Batch", style="bold")
        batch_table.add_column("Meals", justify="right")
        for row in stats["batch_counts"][:8]:
            batch_table.add_row(row["batch"], str(row["count"]))
        console.print(batch_table)


def _render_imports(graph: dict) -> None:
    from rich.table import Table

    console = _get_console()
    if not graph:
        console.print("[dim]No import graph yet. Feed Python files to build import intelligence.[/dim]")
        return

    table = Table(title=f"Import Graph ({len(graph)} nodes)")
    table.add_column("Import", style="bold")
    table.add_column("Seen", justify="right")
    table.add_column("Ore Avg")
    table.add_column("Top Co-occurrences")

    for imp, node in sorted(graph.items(), key=lambda kv: kv[1].get("seen", 0), reverse=True):
        co = node.get("co_occurs", {})
        top_co = sorted(co.items(), key=lambda kv: kv[1], reverse=True)[:3]
        co_str = ", ".join(f"{k}({v})" for k, v in top_co) if top_co else "[dim]none[/dim]"
        table.add_row(imp, str(node["seen"]), _ore_bar(node.get("ore_avg", 0)), co_str)

    console.print(table)


def _render_learn(result: dict, mem: dict) -> None:
    from rich.table import Table
    from rich.panel import Panel

    console = _get_console()

    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column("Key", style="bold cyan")
    stats.add_column("Value")
    stats.add_row("Forge states scanned", str(result["outcomes_scanned"]))
    stats.add_row("Matched to consumed", str(result["consumed_matched"]))
    stats.add_row("New lessons", str(result["new_lessons"]))
    stats.add_row("Total prediction errors", str(result["total_errors"]))
    console.print(Panel(stats, title="[bold]FORGE FEEDBACK LOOP[/bold]", border_style="dim"))

    fb = mem.get("forge_feedback", {})
    if result["new_lessons"] > 0:
        err_table = Table(title="New Lessons Learned", box=None)
        err_table.add_column("File", style="bold")
        err_table.add_column("Predicted")
        err_table.add_column("Actual")
        err_table.add_column("Forge State")
        err_table.add_column("Verdict")
        for e in fb.get("ore_prediction_errors", [])[-result["new_lessons"]:]:
            direction = "[red]too high[/red]" if e["error"] < 0 else "[green]too low[/green]"
            err_table.add_row(e["file"], str(e["predicted"]), str(e["actual"]),
                              e["forge_state"], direction)
        console.print(err_table)
        console.print("[green]Cluster profiles adjusted — ore heuristics updated.[/green]")
    else:
        console.print("[dim]No new prediction errors found. Heuristics holding.[/dim]")


def _render_graph(G: "nx.DiGraph", centrality: dict, dot_path: str | None = None) -> None:
    from rich.table import Table
    from rich.panel import Panel

    console = _get_console()

    if len(G) == 0:
        console.print("[dim]No import graph yet. Feed Python files first.[/dim]")
        return

    import networkx as nx
    U = G.to_undirected()
    components = list(nx.connected_components(U))

    # Summary
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Key", style="bold cyan")
    summary.add_column("Value")
    summary.add_row("Nodes", str(len(G)))
    summary.add_row("Edges", str(len(G.edges)))
    summary.add_row("Components", str(len(components)))
    density = nx.density(U) if len(G) > 1 else 0
    summary.add_row("Density", f"{density:.3f}")
    if dot_path:
        summary.add_row("DOT exported", dot_path)
    console.print(Panel(summary, title="[bold]IMPORT GRAPH (NetworkX)[/bold]", border_style="dim"))

    # Centrality rankings
    table = Table(title="Centrality Rankings")
    table.add_column("Import", style="bold")
    table.add_column("Seen", justify="right")
    table.add_column("Ore Avg")
    table.add_column("Degree", justify="right")
    table.add_column("Betweenness", justify="right")
    table.add_column("Role")

    ranked = sorted(centrality.items(), key=lambda kv: kv[1]["degree"], reverse=True)
    for imp, c in ranked:
        # Classify role by centrality
        if c["degree"] > 0.5 and c["betweenness"] > 0.1:
            role = "[bold green]hub[/bold green]"
        elif c["degree"] > 0.3:
            role = "[yellow]connector[/yellow]"
        elif c["betweenness"] > 0.1:
            role = "[cyan]bridge[/cyan]"
        else:
            role = "[dim]leaf[/dim]"
        table.add_row(imp, str(c["seen"]), _ore_bar(c["ore_avg"]),
                      f"{c['degree']:.3f}", f"{c['betweenness']:.3f}", role)

    console.print(table)

    # Components
    if len(components) > 1:
        console.print(f"\n[bold]Connected components:[/bold]")
        for i, comp in enumerate(sorted(components, key=len, reverse=True), 1):
            console.print(f"  {i}. {', '.join(sorted(comp))}")


def _render_hunger(candidates: list[dict]) -> None:
    from rich.table import Table

    console = _get_console()
    if not candidates:
        console.print("[dim]The zombie is sated. No obvious candidates found.[/dim]")
        return

    table = Table(title=f"HUNGER: {len(candidates)} candidate(s)")
    table.add_column("Ore")
    table.add_column("Path", style="bold")
    table.add_column("Category")
    table.add_column("Reason")
    table.add_column("Signals")

    for c in candidates:
        table.add_row(
            _ore_bar(c.get("ore_rating", 0)),
            c.get("path", "?"),
            c.get("category", "?"),
            c.get("hunger_reason", "?"),
            ", ".join(c.get("signals", [])[:3]),
        )

    console.print(table)


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

    p_feed = sub.add_parser("feed", help="Full pipeline: bite + chew + digest + excrete + forge bridge")
    p_feed.add_argument("path", type=Path)
    p_feed.add_argument("--batch", type=str, default=None)
    p_feed.add_argument("--dry-run", action="store_true")

    p_hunger = sub.add_parser("hunger", help="Scan repo for consumable candidates")
    p_hunger.add_argument("--json", action="store_true")

    p_memory = sub.add_parser("memory", help="Show what the zombie has learned")
    p_memory.add_argument("--json", action="store_true")

    p_stats = sub.add_parser("stats", help="Polars analytics on consumption_log + profiles")
    p_stats.add_argument("--json", action="store_true")

    p_learn = sub.add_parser("learn", help="Read forge outcomes, backpropagate into ore heuristics")
    p_learn.add_argument("--json", action="store_true")

    p_profiles = sub.add_parser("profiles", help="Show adaptive cluster profiles")
    p_profiles.add_argument("--json", action="store_true")

    p_imports = sub.add_parser("imports", help="Show import graph intelligence")
    p_imports.add_argument("--json", action="store_true")

    p_graph = sub.add_parser("graph", help="NetworkX graph analysis + DOT export")
    p_graph.add_argument("--json", action="store_true")
    p_graph.add_argument("--dot", type=str, default=None, metavar="FILE",
                         help="Export DOT file (e.g. --dot zombie_imports.dot)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "bite":
        result = bite(args.path.resolve(), deep=args.deep)
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            _render_bite(result)
        return 0

    if args.command == "chew":
        result = chew(args.path.resolve())
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            from rich.table import Table
            from rich.panel import Panel
            console = _get_console()
            if "error" in result:
                console.print(f"[red]ERROR:[/red] {result['error']}")
                return 1
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="bold cyan")
            table.add_column("Value")
            table.add_row("Source", result.get("source", "?"))
            table.add_row("Ore Rating", _ore_bar(result.get("ore_rating", 0)))
            for key, vals in result.get("intelligence", {}).items():
                table.add_row(f"\\[{key}]", f"{len(vals) if isinstance(vals, list) else '1'} items")
            console.print(Panel(table, title="[bold]CHEW[/bold]", border_style="dim"))
        return 0

    if args.command == "digest":
        result = digest(args.path.resolve())
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        console = _get_console()
        console.print(f"[bold]DIGEST:[/bold] {result.get('extract_path', '?')}")
        console.print(f"  Ore Rating: {_ore_bar(result.get('ore_rating', 0))}")
        console.print(f"  Intelligence: {', '.join(result.get('intelligence_keys', []))}")
        return 0

    if args.command == "excrete":
        result = excrete(args.path.resolve(), batch_name=args.batch, dry_run=args.dry_run)
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        console = _get_console()
        if result.get("status") == "dry_run":
            console.print(f"[yellow]DRY RUN:[/yellow] {result['source']} -> {result['target']}")
        else:
            console.print(f"[green]EXCRETED:[/green] {result['consumed']} -> {result['destination']}")
        return 0

    if args.command == "feed":
        result = feed(args.path.resolve(), batch_name=args.batch, dry_run=args.dry_run)
        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            return 1
        console = _get_console()
        if result.get("status") == "dry_run":
            console.print(f"[yellow]DRY RUN FEED:[/yellow] {result['source']}")
            console.print(f"  -> {result['target']}")
            console.print(f"  Ore Rating: {_ore_bar(result['ore_rating'])}")
            console.print(f"  Category: {result['category']}")
            console.print(f"  Forge Stage: {result['forge_stage']}")
            console.print(f"  Signals: {', '.join(result['signals'])}")
            console.print(f"  Extractable items: {result['extractable_count']}")
        else:
            console.print(f"[green]CONSUMED:[/green] {result['excrete']['consumed']}")
            console.print(f"  -> {result['excrete']['destination']}")
            console.print(f"  Intelligence: {', '.join(result['digest'].get('intelligence_keys', []))}")
            bridge = result.get("bridge", {})
            if bridge:
                console.print(f"  Forge Route: {bridge.get('stage', bridge.get('status', '?'))} -> {bridge.get('target', '?')}")
        return 0

    if args.command == "hunger":
        candidates = hunger()
        if getattr(args, "json", False):
            print(json.dumps(candidates, indent=2))
        else:
            _render_hunger(candidates)
        return 0

    if args.command == "memory":
        mem = load_memory()
        if getattr(args, "json", False):
            print(json.dumps(mem, indent=2))
        else:
            _render_memory(mem)
        return 0

    if args.command == "stats":
        mem = load_memory()
        stats = build_stats(mem)
        if getattr(args, "json", False):
            print(json.dumps(stats, indent=2))
        else:
            _render_stats(stats)
        return 0

    if args.command == "learn":
        mem = load_memory()
        result = learn_from_forge(mem)
        save_memory(mem)
        if getattr(args, "json", False):
            print(json.dumps(result, indent=2))
        else:
            _render_learn(result, mem)
        return 0

    if args.command == "profiles":
        mem = load_memory()
        profiles = mem.get("cluster_profiles", {})
        if getattr(args, "json", False):
            print(json.dumps(profiles, indent=2))
        else:
            _render_profiles(profiles)
        return 0

    if args.command == "imports":
        mem = load_memory()
        graph = mem.get("import_graph", {})
        if getattr(args, "json", False):
            print(json.dumps(graph, indent=2))
        else:
            _render_imports(graph)
        return 0

    if args.command == "graph":
        mem = load_memory()
        G = build_nx_graph(mem)
        if getattr(args, "json", False):
            centrality = graph_centrality(G)
            print(json.dumps({
                "nodes": len(G),
                "edges": len(G.edges),
                "centrality": centrality,
            }, indent=2))
        else:
            centrality = graph_centrality(G)
            dot_path = None
            if args.dot:
                dot_content = export_dot(G)
                dot_file = Path(args.dot)
                dot_file.write_text(dot_content, encoding="utf-8")
                dot_path = str(dot_file)
            _render_graph(G, centrality, dot_path)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
