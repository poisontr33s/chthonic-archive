#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: archaeology_mcp.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Archaeology MCP Server — repo-agnostic, env-configurable.

Single script that serves any git repo. Point at it from any mcp.json entry
with a different ARCHAEOLOGY_REPO_ROOT env var to get a specialized instance.

Env vars (all optional — defaults to this script's parent repo):
  ARCHAEOLOGY_REPO_ROOT   Absolute path to the repo root to target
  ARCHAEOLOGY_DB_PATH     Override for archive.db location (default: REPO_ROOT/archive.db)
  ARCHAEOLOGY_SCANNER     Override path to district_scanner.py (default: REPO_ROOT/scripts/district_scanner.py)

When ARCHAEOLOGY_SCANNER is absent from a target repo, the built-in
fallback scanner runs instead — repo-agnostic, produces a compatible
district_scan_full_sweep.json so all downstream tools work without modification.

Tools:
  archaeology_scan          — run scanner (specialized or fallback) + rebuild archive.db
  archaeology_query         — query archive.db (district / entity / generation / top / unread / search / report)
  archaeology_mark_read     — record a file as read with summary
  archaeology_fetch_json    — read a generated JSON artifact and return parsed content (+ repo_info)
  archaeology_lessons_compile — compile cross-session lessons from all JSON artifacts + DB

Registration pattern (mcp.json):
  "pnk-archaeology":        { cwd: .../psychonoir-kontrapunkt-large-file-holder }           — specialized
  "pnk-public-archaeology": { env: ARCHAEOLOGY_REPO_ROOT=.../PsychoNoir-Kontrapunkt }       — fallback scanner
  "chthonic-archaeology":   { env: ARCHAEOLOGY_REPO_ROOT=.../chthonic-archive }              — fallback scanner

@SID:           ARCHAEOLOGY_MCP_MULTI
@Shabti:        CLI Script
@Purpose:       Archaeology MCP Server — repo-agnostic, env-configurable.
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# @SID: ARCHAEOLOGY_MCP_MULTI

import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

_DEFAULT_ROOT = Path(__file__).parent.parent

REPO_ROOT   = Path(os.environ.get("ARCHAEOLOGY_REPO_ROOT", str(_DEFAULT_ROOT))).resolve()
SCRIPTS_DIR = REPO_ROOT / "scripts"
DB_PATH     = Path(os.environ.get("ARCHAEOLOGY_DB_PATH",   str(REPO_ROOT / "archive.db"))).resolve()
SCANNER     = Path(os.environ.get("ARCHAEOLOGY_SCANNER",   str(SCRIPTS_DIR / "district_scanner.py"))).resolve()

_REPO_NAME  = REPO_ROOT.name

SCAN_FULL_JSON    = SCRIPTS_DIR / "district_scan_full_sweep.json"
SCAN_RESULTS_JSON = SCRIPTS_DIR / "district_scan_results.json"
READS_EXPORT_JSON = SCRIPTS_DIR / "reads_export.json"

GENERATION_LABELS = {-2: "PRESERVED", -1: "GRAVEYARD", 0: "UNCLASSIFIED", 1: "GEN1-RAW", 2: "GEN2-STUB", 3: "GEN3-FULLDEPTH"}

mcp = FastMCP(
    "pnk-archaeology",
    instructions=(
        f"PsychoNoir-Kontrapunkt archaeology layer — scanning {_REPO_NAME}. "
        "Scan districts, query entity archive, track reads, and compile lessons from JSON artifacts."
    ),
)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _run(cmd: list[str], cwd: Path = REPO_ROOT) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))
    return result.returncode, result.stdout, result.stderr


def _gen_label(gen) -> str:
    return GENERATION_LABELS.get(int(gen) if gen is not None else 0, str(gen))


def _fallback_scan(sweep_min_lines: int) -> dict:
    """
    Built-in repo-agnostic scanner — used when district_scanner.py is absent.

    Walks REPO_ROOT, collects .md and .json files at or above sweep_min_lines,
    groups by top-level subdirectory as 'district', and writes
    district_scan_full_sweep.json in a format compatible with build_archive_db.py.
    """
    SKIP_DIRS = {".git", "node_modules", "__pycache__", "target", ".bundle"}

    detail: dict[str, dict] = {}
    total_files = 0

    for filepath in REPO_ROOT.rglob("*"):
        if not filepath.is_file():
            continue
        if any(part in SKIP_DIRS or part.startswith(".venv") for part in filepath.parts):
            continue
        if filepath.suffix not in (".md", ".json"):
            continue
        try:
            line_count = sum(1 for _ in filepath.open(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        if line_count < sweep_min_lines:
            continue

        rel = filepath.relative_to(REPO_ROOT)
        parts = rel.parts
        district = parts[0].upper().lstrip(".") if len(parts) > 1 else "ROOT"
        entity = filepath.stem
        total_files += 1

        detail.setdefault(district, {}).setdefault(entity, []).append({
            "path": str(rel),
            "tier": "unclassified",
            "line_count": line_count,
            "suffix": filepath.suffix,
        })

    result = {"total_files": total_files, "detail": detail}
    SCRIPTS_DIR.mkdir(exist_ok=True)
    with open(SCAN_FULL_JSON, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    return result


def _build_db_from_scan(data: dict, source_file: str) -> dict:
    """
    Minimal in-process DB builder — used when build_archive_db.py is absent.
    Mirrors the schema from build_archive_db.py (upsert-safe).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source_file TEXT,
            total_files INTEGER DEFAULT 0,
            district_count INTEGER DEFAULT 0,
            entity_count INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS districts (
            name TEXT PRIMARY KEY,
            entity_count INTEGER DEFAULT 0,
            active_count INTEGER DEFAULT 0,
            graveyard_count INTEGER DEFAULT 0,
            top_file_lines INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS entities (
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            max_line_count INTEGER DEFAULT 0,
            generation INTEGER DEFAULT 0,
            canonical_file TEXT,
            PRIMARY KEY (name, district)
        );
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            district TEXT NOT NULL,
            entity TEXT NOT NULL,
            suffix TEXT,
            line_count INTEGER DEFAULT 0,
            generation INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            session_date TEXT,
            lines_read TEXT,
            summary TEXT,
            timestamp TEXT NOT NULL
        );
    """)
    now = datetime.now(timezone.utc).isoformat()
    detail = data.get("detail", {})
    total_entities = sum(len(v) for v in detail.values())
    total_file_rows = 0

    scan_row = conn.execute(
        "INSERT INTO scans (timestamp, source_file, total_files, district_count, entity_count) VALUES (?,?,?,?,?)",
        (now, source_file, data.get("total_files", 0), len(detail), total_entities),
    )
    for dist_name, entities in detail.items():
        dist_files: list[dict] = []
        for entity_name, file_list in entities.items():
            for f in file_list:
                conn.execute(
                    "INSERT OR REPLACE INTO files (path, district, entity, suffix, line_count, generation) VALUES (?,?,?,?,?,?)",
                    (f["path"], dist_name, entity_name, f.get("suffix", ""), f.get("line_count", 0), 0),
                )
                total_file_rows += 1
                dist_files.append(f)
            max_lc = max((f.get("line_count", 0) for f in file_list), default=0)
            canonical = max(file_list, key=lambda x: x.get("line_count", 0), default={}).get("path", "")
            conn.execute(
                "INSERT OR REPLACE INTO entities (name, district, max_line_count, generation, canonical_file) VALUES (?,?,?,?,?)",
                (entity_name, dist_name, max_lc, 0, canonical),
            )
        top_lines = max((f.get("line_count", 0) for f in dist_files), default=0)
        conn.execute(
            "INSERT OR REPLACE INTO districts (name, entity_count, active_count, graveyard_count, top_file_lines) VALUES (?,?,?,?,?)",
            (dist_name, len(entities), len(dist_files), 0, top_lines),
        )
    conn.execute("UPDATE scans SET file_count=? WHERE id=?", (total_file_rows, scan_row.lastrowid))
    conn.commit()
    conn.close()
    return {"districts": len(detail), "entities": total_entities, "file_rows": total_file_rows}


# ─── tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def archaeology_scan(
    sweep_min_lines: int = 200,
    rebuild_db: bool = True,
) -> dict:
    """
    Run the district scanner across the target repo then rebuild archive.db.

    Uses the specialized district_scanner.py when present (PNK-LFH mode).
    Falls back to a built-in repo-agnostic walker for any other repo.

    Args:
        sweep_min_lines: Minimum line count for a file to be included (default 200).
        rebuild_db: If True (default), rebuild archive.db after scanning.

    Returns:
        dict with scan stats and DB upsert summary. 'scanner_mode' = 'specialized' | 'fallback'.
    """
    scanner_mode = "specialized" if SCANNER.exists() else "fallback"
    scan_stats: dict = {}

    if scanner_mode == "specialized":
        rc, stdout, stderr = _run([
            "uv", "run", str(SCANNER),
            "--sweep-min-lines", str(sweep_min_lines),
            "--output", str(SCAN_FULL_JSON),
        ])
        if rc != 0:
            return {
                "error": f"Scanner failed (exit {rc})",
                "stderr": stderr[:2000],
                "repo": str(REPO_ROOT),
            }
        if SCAN_FULL_JSON.exists():
            with open(SCAN_FULL_JSON, encoding="utf-8") as fh:
                d = json.load(fh)
            scan_stats = {
                "total_files_scanned": d.get("total_files", 0),
                "districts": len(d.get("detail", {})),
                "entities": sum(len(v) for v in d.get("detail", {}).values()),
            }
    else:
        d = _fallback_scan(sweep_min_lines)
        scan_stats = {
            "total_files_scanned": d.get("total_files", 0),
            "districts": len(d.get("detail", {})),
            "entities": sum(len(v) for v in d.get("detail", {}).values()),
        }

    db_result: dict = {}
    if rebuild_db:
        build_script = SCRIPTS_DIR / "build_archive_db.py"
        if build_script.exists():
            rc2, stdout2, stderr2 = _run(["uv", "run", str(build_script)])
            if rc2 != 0:
                db_result = {"error": stderr2[:1000]}
            else:
                db_result = {"status": "ok", "output": stdout2.strip()}
        else:
            with open(SCAN_FULL_JSON, encoding="utf-8") as fh:
                scan_json = json.load(fh)
            stats = _build_db_from_scan(scan_json, str(SCAN_FULL_JSON))
            db_result = {"status": "ok (in-process)", **stats}

    return {
        "repo": str(REPO_ROOT),
        "repo_name": _REPO_NAME,
        "scanner_mode": scanner_mode,
        "scan": scan_stats,
        "db_rebuild": db_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def archaeology_query(
    command: str,
    term: str = "",
    n: int = 20,
) -> dict:
    """
    Query archive.db for entity/district/generation data.

    Args:
        command: One of: district | entity | generation | top | unread | search | report
            - district <term>   List entities in a district (term = district name substring)
            - entity <term>     List .md files for an entity (term = entity name substring)
            - generation <term> List files of a generation (-1 graveyard, 0 unclassified, 1 raw, 2 stub, 3 fulldepth)
            - top               Top N .md files by line count (use n parameter)
            - unread            Top 50 unread Gen1+ files
            - search <term>     Substring search on path or entity name
            - report            Full JSON status report
        term: Search term or generation number (as string) depending on command.
        n: Limit for 'top' command (default 20).

    Returns:
        Structured dict with results.
    """
    conn = _get_conn()
    if conn is None:
        return {"error": "archive.db not found — run archaeology_scan first"}

    try:
        cmd = command.lower().strip()

        if cmd == "report":
            scan = conn.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1").fetchone()
            districts = conn.execute("SELECT * FROM districts ORDER BY entity_count DESC").fetchall()
            reads_total = conn.execute("SELECT COUNT(*) as c FROM reads").fetchone()["c"]
            unread_count = conn.execute(
                "SELECT COUNT(*) as c FROM files f LEFT JOIN reads r ON f.path=r.file_path "
                "WHERE r.file_path IS NULL AND f.suffix='.md' AND f.generation>=1"
            ).fetchone()["c"]
            gen_counts = conn.execute(
                "SELECT generation, COUNT(*) as c FROM files WHERE suffix='.md' GROUP BY generation ORDER BY generation"
            ).fetchall()
            return {
                "last_scan": dict(scan) if scan else None,
                "reads_total": reads_total,
                "unread_gen1plus": unread_count,
                "generation_breakdown": {_gen_label(r["generation"]): r["c"] for r in gen_counts},
                "districts": [
                    {"name": d["name"], "entity_count": d["entity_count"],
                     "active": d["active_count"], "graveyard": d["graveyard_count"],
                     "top_file_lines": d["top_file_lines"]}
                    for d in districts
                ],
            }

        elif cmd == "district":
            rows = conn.execute(
                "SELECT * FROM entities WHERE UPPER(district) LIKE UPPER(?) ORDER BY max_line_count DESC",
                (f"%{term}%",),
            ).fetchall()
            return {
                "district_match": term,
                "count": len(rows),
                "entities": [
                    {"name": r["name"], "district": r["district"], "max_line_count": r["max_line_count"],
                     "generation": _gen_label(r["generation"]), "canonical_file": r["canonical_file"]}
                    for r in rows
                ],
            }

        elif cmd == "entity":
            rows = conn.execute(
                "SELECT * FROM files WHERE LOWER(entity) LIKE LOWER(?) AND suffix='.md' ORDER BY line_count DESC",
                (f"%{term}%",),
            ).fetchall()
            return {
                "entity_match": term,
                "count": len(rows),
                "files": [
                    {"path": r["path"], "line_count": r["line_count"],
                     "generation": _gen_label(r["generation"]), "district": r["district"]}
                    for r in rows
                ],
            }

        elif cmd == "generation":
            try:
                gen_num = int(term)
            except ValueError:
                return {"error": f"generation requires a number, got: '{term}'"}
            rows = conn.execute(
                "SELECT * FROM files WHERE generation=? AND suffix='.md' ORDER BY line_count DESC LIMIT 100",
                (gen_num,),
            ).fetchall()
            return {
                "generation": gen_num,
                "label": _gen_label(gen_num),
                "count": len(rows),
                "files": [
                    {"path": r["path"], "line_count": r["line_count"],
                     "district": r["district"], "entity": r["entity"]}
                    for r in rows
                ],
            }

        elif cmd == "top":
            rows = conn.execute(
                "SELECT * FROM files WHERE suffix='.md' ORDER BY line_count DESC LIMIT ?", (n,)
            ).fetchall()
            return {
                "top": n,
                "files": [
                    {"path": r["path"], "line_count": r["line_count"],
                     "district": r["district"], "generation": _gen_label(r["generation"])}
                    for r in rows
                ],
            }

        elif cmd == "unread":
            rows = conn.execute(
                "SELECT f.* FROM files f LEFT JOIN reads r ON f.path=r.file_path "
                "WHERE r.file_path IS NULL AND f.suffix='.md' AND f.generation>=1 "
                "ORDER BY f.line_count DESC LIMIT 50"
            ).fetchall()
            return {
                "unread_gen1plus": len(rows),
                "files": [
                    {"path": r["path"], "line_count": r["line_count"],
                     "district": r["district"], "generation": _gen_label(r["generation"])}
                    for r in rows
                ],
            }

        elif cmd == "search":
            rows = conn.execute(
                "SELECT * FROM files WHERE (LOWER(path) LIKE LOWER(?) OR LOWER(entity) LIKE LOWER(?)) "
                "AND suffix='.md' ORDER BY line_count DESC LIMIT 40",
                (f"%{term}%", f"%{term}%"),
            ).fetchall()
            return {
                "search_term": term,
                "count": len(rows),
                "results": [
                    {"path": r["path"], "line_count": r["line_count"],
                     "district": r["district"], "entity": r["entity"],
                     "generation": _gen_label(r["generation"])}
                    for r in rows
                ],
            }

        else:
            return {"error": f"Unknown command: '{command}'. Valid: district|entity|generation|top|unread|search|report"}

    finally:
        conn.close()


@mcp.tool()
def archaeology_mark_read(path: str, lines: str, summary: str) -> dict:
    """
    Record a file as read in the archive's reads table.

    Args:
        path: Repo-relative path to the file (as it appears in archive.db files.path column).
        lines: Lines read, e.g. "1-80" or "all" or "101-200".
        summary: Short text summary of key findings from the read.

    Returns:
        Confirmation dict with path and lines.
    """
    conn = _get_conn()
    if conn is None:
        return {"error": "archive.db not found"}
    try:
        now = datetime.now(timezone.utc).isoformat()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        exists = conn.execute("SELECT 1 FROM files WHERE path=?", (path,)).fetchone()
        conn.execute(
            "INSERT INTO reads (file_path, session_date, lines_read, summary, timestamp) VALUES (?,?,?,?,?)",
            (path, today, lines, summary, now),
        )
        conn.commit()
        return {
            "status": "ok",
            "path": path,
            "lines": lines,
            "file_in_db": bool(exists),
            "timestamp": now,
        }
    finally:
        conn.close()


@mcp.tool()
def archaeology_fetch_json(
    artifact: str = "scan_full",
    max_entities: int = 30,
) -> dict:
    """
    Fetch a generated JSON artifact and return parsed, summarized content.

    Args:
        artifact: Which artifact to fetch:
            "scan_full"         district_scan_full_sweep.json — full scan results
            "scan_results"      district_scan_results.json — earlier scan pass
            "reads_export"      reads_export.json — read history log
            "historical_list"   list all historical scans in CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS/03_HISTORICAL_SCANS/
            "historical_latest" parse the most recent historical scan JSON header
            "repo_info"         repo root path, present scripts, DB status — use to probe any repo
        max_entities: Maximum number of entities to include in per-district breakdown (default 30).

    Returns:
        Parsed, summarized artifact content. Every result includes 'repo' + 'repo_name' fields.
    """
    meta = {"repo": str(REPO_ROOT), "repo_name": _REPO_NAME}

    if artifact == "repo_info":
        return {
            **meta,
            "db_exists": DB_PATH.exists(),
            "db_size_mb": round(DB_PATH.stat().st_size / 1_048_576, 3) if DB_PATH.exists() else 0,
            "scanner_available": SCANNER.exists(),
            "scanner_mode": "specialized" if SCANNER.exists() else "fallback",
            "build_db_available": (SCRIPTS_DIR / "build_archive_db.py").exists(),
            "query_archive_available": (SCRIPTS_DIR / "query_archive.py").exists(),
            "scan_full_exists": SCAN_FULL_JSON.exists(),
            "scripts_dir": str(SCRIPTS_DIR),
            "db_path": str(DB_PATH),
        }

    if artifact == "scan_full":
        if not SCAN_FULL_JSON.exists():
            return {"error": "district_scan_full_sweep.json not found — run archaeology_scan first"}
        with open(SCAN_FULL_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        detail = data.get("detail", {})
        summary_out = {
            "total_files": data.get("total_files"),
            "districts": len(detail),
            "entities_total": sum(len(v) for v in detail.values()),
            "district_breakdown": {},
        }
        for dist_name, entities in detail.items():
            top = sorted(entities.items(), key=lambda x: max(
                (f.get("line_count", 0) for f in x[1]), default=0
            ), reverse=True)[:max_entities]
            summary_out["district_breakdown"][dist_name] = [
                {"entity": k, "file_count": len(v),
                 "max_lines": max((f.get("line_count", 0) for f in v), default=0)}
                for k, v in top
            ]
        return summary_out

    elif artifact == "scan_results":
        if not SCAN_RESULTS_JSON.exists():
            return {"error": "district_scan_results.json not found"}
        with open(SCAN_RESULTS_JSON, encoding="utf-8") as fh:
            data = json.load(fh)
        detail = data.get("detail", {})
        return {
            "total_files": data.get("total_files"),
            "districts": len(detail),
            "entities_total": sum(len(v) for v in detail.values()),
            "note": "Earlier scan pass — compare with scan_full for delta",
        }

    elif artifact == "reads_export":
        if not READS_EXPORT_JSON.exists():
            return {"error": "reads_export.json not found — run uv run scripts/query_archive.py --export-reads"}
        with open(READS_EXPORT_JSON, encoding="utf-8") as fh:
            reads = json.load(fh)
        return {
            "read_count": len(reads),
            "reads": reads,
        }

    elif artifact == "historical_list":
        hist_dir = REPO_ROOT / "CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS" / "03_HISTORICAL_SCANS"
        if not hist_dir.exists():
            return {"error": f"{hist_dir} not found"}
        files = sorted(hist_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return {
            "historical_scan_count": len(files),
            "scans": [
                {"name": f.name, "size_mb": round(f.stat().st_size / 1_048_576, 2)}
                for f in files
            ],
        }

    elif artifact == "historical_latest":
        hist_dir = REPO_ROOT / "CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS" / "03_HISTORICAL_SCANS"
        if not hist_dir.exists():
            return {"error": f"{hist_dir} not found"}
        files = sorted(hist_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return {"error": "No historical scan files found"}
        latest = files[0]
        # Read only first 1000 chars for structure probe (these are massive files)
        with open(latest, encoding="utf-8") as fh:
            head = fh.read(4000)
        # Count lines
        with open(latest, encoding="utf-8") as fh:
            line_count = sum(1 for _ in fh)
        return {
            "file": latest.name,
            "size_mb": round(latest.stat().st_size / 1_048_576, 2),
            "line_count": line_count,
            "head_preview": head[:2000],
        }

    else:
        return {
            "error": f"Unknown artifact: '{artifact}'",
            "valid_options": ["scan_full", "scan_results", "reads_export",
                              "historical_list", "historical_latest", "repo_info"],
        }


@mcp.tool()
def archaeology_lessons_compile() -> dict:
    """
    Compile cross-session lessons from all JSON artifacts + archive.db.

    Synthesizes:
    - Generation distribution (how much of the repo is structured vs raw vs graveyard)
    - District health (active / graveyard ratios)
    - Read coverage (how much of the Gen1+ surface has been examined)
    - Top unread entities by line count (highest-value targets remaining)
    - Scan delta (if multiple scan artifacts exist — entity count progression)
    - Historical scan inventory (Sep-Oct 2025 bedrock scans in 03_HISTORICAL_SCANS)
    - Reads log (what has been examined, key summaries)

    Returns:
        dict with lessons_learned structure, coverage metrics, and priority targets.
    """
    lessons: dict = {
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "repo": str(REPO_ROOT),
        "repo_name": _REPO_NAME,
        "generation_distribution": {},
        "district_health": [],
        "read_coverage": {},
        "priority_targets": [],
        "scan_delta": {},
        "historical_inventory": {},
        "reads_log": [],
        "key_findings": [],
    }

    # ── 1. DB-based analysis ──────────────────────────────────────────────────
    conn = _get_conn()
    if conn:
        try:
            # Generation distribution
            gen_rows = conn.execute(
                "SELECT generation, COUNT(*) as c, SUM(line_count) as total_lines "
                "FROM files WHERE suffix='.md' GROUP BY generation ORDER BY generation"
            ).fetchall()
            total_md = sum(r["c"] for r in gen_rows)
            lessons["generation_distribution"] = {
                _gen_label(r["generation"]): {
                    "file_count": r["c"],
                    "total_lines": r["total_lines"],
                    "pct_of_md": round(r["c"] / total_md * 100, 1) if total_md else 0,
                }
                for r in gen_rows
            }

            # District health
            dist_rows = conn.execute(
                "SELECT name, entity_count, active_count, graveyard_count, top_file_lines "
                "FROM districts ORDER BY entity_count DESC"
            ).fetchall()
            lessons["district_health"] = [
                {
                    "district": r["name"],
                    "entities": r["entity_count"],
                    "active": r["active_count"],
                    "graveyard": r["graveyard_count"],
                    "top_file_lines": r["top_file_lines"],
                    "graveyard_pct": round(r["graveyard_count"] / r["entity_count"] * 100, 1)
                        if r["entity_count"] else 0,
                }
                for r in dist_rows
            ]

            # Read coverage
            total_gen1plus = conn.execute(
                "SELECT COUNT(*) as c FROM files WHERE suffix='.md' AND generation>=1"
            ).fetchone()["c"]
            total_read = conn.execute(
                "SELECT COUNT(DISTINCT file_path) as c FROM reads"
            ).fetchone()["c"]
            total_lines_gen1plus = conn.execute(
                "SELECT SUM(line_count) as s FROM files WHERE suffix='.md' AND generation>=1"
            ).fetchone()["s"] or 0
            lessons["read_coverage"] = {
                "gen1plus_files": total_gen1plus,
                "files_read": total_read,
                "pct_read": round(total_read / total_gen1plus * 100, 1) if total_gen1plus else 0,
                "total_gen1plus_lines": total_lines_gen1plus,
                "note": "Each gen1+ file represents a primary source entity profile — coverage measures depth of archaeology",
            }

            # Priority targets — top unread Gen1+ by line count
            unread_rows = conn.execute(
                "SELECT f.path, f.line_count, f.district, f.entity, f.generation "
                "FROM files f LEFT JOIN reads r ON f.path=r.file_path "
                "WHERE r.file_path IS NULL AND f.suffix='.md' AND f.generation>=1 "
                "ORDER BY f.line_count DESC LIMIT 15"
            ).fetchall()
            lessons["priority_targets"] = [
                {
                    "path": r["path"],
                    "line_count": r["line_count"],
                    "district": r["district"],
                    "entity": r["entity"],
                    "generation": _gen_label(r["generation"]),
                }
                for r in unread_rows
            ]

            # Reads log
            read_rows = conn.execute(
                "SELECT * FROM reads ORDER BY id"
            ).fetchall()
            lessons["reads_log"] = [
                {
                    "path": r["file_path"],
                    "session_date": r["session_date"],
                    "lines_read": r["lines_read"],
                    "summary": r["summary"],
                }
                for r in read_rows
            ]

            # Key findings synthesized
            graveyard_pct = round(
                sum(d["graveyard"] for d in lessons["district_health"]) /
                max(sum(d["entities"] for d in lessons["district_health"]), 1) * 100,
                1
            )
            gen3_count = lessons["generation_distribution"].get("GEN3-FULLDEPTH", {}).get("file_count", 0)
            gen1_count = lessons["generation_distribution"].get("GEN1-RAW", {}).get("file_count", 0)
            unclass_count = lessons["generation_distribution"].get("UNCLASSIFIED", {}).get("file_count", 0)
            findings = [
                f"Repo: {_REPO_NAME} — {total_md} entity-profile .md files across {len(dist_rows)} districts",
                f"Generation ladder: GEN3-FULLDEPTH={gen3_count} (cRPG-ready), GEN1-RAW={gen1_count} (primary source), UNCLASSIFIED={unclass_count}",
                f"Graveyard rate: {graveyard_pct}% of all tracked entities deprecated/archived",
                f"Read coverage: {total_read}/{total_gen1plus} gen1+ files ({round(total_read/max(total_gen1plus,1)*100,1)}%) — archaeology in progress",
                f"GEN3-FULLDEPTH files are the cRPG-portable entity card targets — {gen3_count} confirmed",
            ]
            # PNK-LFH specific enrichments (silently skipped for other repos)
            if _REPO_NAME == "psychonoir-kontrapunkt-large-file-holder":
                findings += [
                    "T1.5 Bridge tier: autonomously invented by Claudine 5.0 Oct 2025 — Eva Blue elevated from T2 via co-occurrence analysis",
                    "Caribbean Archipelago: deprecated Sep 29, 2025 — GRAVEYARD classification",
                ]
            lessons["key_findings"] = findings

        finally:
            conn.close()

    # ── 2. Scan delta (compare scan_results vs scan_full) ─────────────────────
    scan_sizes: dict = {}
    for name, path in [("scan_results", SCAN_RESULTS_JSON), ("scan_full", SCAN_FULL_JSON)]:
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            detail = data.get("detail", {})
            scan_sizes[name] = {
                "total_files": data.get("total_files"),
                "districts": len(detail),
                "entities": sum(len(v) for v in detail.values()),
            }
    if len(scan_sizes) == 2:
        delta = scan_sizes["scan_full"]["entities"] - scan_sizes["scan_results"]["entities"]
        scan_sizes["delta_entities"] = delta
        scan_sizes["note"] = f"+{delta} entities found in sweep vs initial scan" if delta >= 0 else f"{delta} entity delta"
    lessons["scan_delta"] = scan_sizes

    # ── 3. Historical inventory ───────────────────────────────────────────────
    hist_dir = REPO_ROOT / "CLAUDINE_SUPREME_CONSCIOUSNESS_NEXUS" / "03_HISTORICAL_SCANS"
    if hist_dir.exists():
        hist_files = sorted(hist_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        lessons["historical_inventory"] = {
            "count": len(hist_files),
            "files": [
                {"name": f.name, "size_mb": round(f.stat().st_size / 1_048_576, 2)}
                for f in hist_files
            ],
            "note": "Bedrock JSON scans from Sep-Oct 2025 — primary source before SQLite layer existed. "
                    "archaeology_fetch_json(artifact='historical_latest') to probe structure.",
        }

    return lessons


# ─── entry ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
