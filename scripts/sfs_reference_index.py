#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: sfs_reference_index.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: BLUE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/genre_extractor.py
# ║   └─◄ dumpster-dive/DUMPSTER_DIVE_REGISTRY.json
# ║   └─◄ extensions/chthonic-archive/src/monolith/ankhReferenceView.ts
# ╚════════════════════════════════════════════════════════════════════════════

"""
SFS Reference Index — Sister Ferrum Scoriae's Unified File Intelligence Database.

Consolidates three data streams into a single SQLite FTS5 index:
  1. Genre extraction digests (claude/mailbox/GENRE_EXTRACTION_*.md)
  2. KCP Cartouche headers (Wedjat-Quipu Spectrum / Temple-Ayllu Zone / @SID)
  3. Dumpster-Dive Registry (DUMPSTER_DIVE_REGISTRY.json)

Provides the same indexing axes as the VS Code extension's AnkhReferenceProvider
but optimized for agent CLI consumption: search by tag, archetype, motif, ankh
layer, nsfw tier, spectrum, or free text.

@SID:           TOOL_SFS_REFERENCE_INDEX_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_SFS_INDEX
@Purpose:       Build and query a unified file intelligence database for agents.

Usage:
  uv run scripts/sfs_reference_index.py build              # (re)build index
  uv run scripts/sfs_reference_index.py query "MILF"        # free-text search
  uv run scripts/sfs_reference_index.py query --tag "ankh"   # tag search
  uv run scripts/sfs_reference_index.py query --tier extreme  # nsfw tier filter
  uv run scripts/sfs_reference_index.py query --layer LOOP    # ankh layer filter
  uv run scripts/sfs_reference_index.py query --spectrum RED   # KCP spectrum filter
  uv run scripts/sfs_reference_index.py stats                 # summary statistics
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "sfs_reference_index.db"
GENRE_MAILBOX = REPO_ROOT / "claude" / "mailbox"
REGISTRY_PATH = REPO_ROOT / "dumpster-dive" / "DUMPSTER_DIVE_REGISTRY.json"

# Valid Wedjat-Quipu Spectrum colors (canonical set)
VALID_SPECTRA = {
    "WHITE", "RED", "BLUE", "GREEN", "GOLD", "ORANGE",
    "VIOLET", "BLACK", "SILVER", "BRONZE", "CRIMSON", "INDIGO",
}

# KCP Cartouche patterns
KCP_SPECTRUM_RE = re.compile(
    r"Wedjat-Quipu Spectrum:\s*(\S+)", re.IGNORECASE
)
KCP_ZONE_RE = re.compile(
    r"Temple-Ayllu Zone:\s*(.+)", re.IGNORECASE
)
SID_RE = re.compile(r"@SID:\s*(\S+)")
LEGACY_SPECTRUM_RE = re.compile(
    r"Spectral Frequency:\s*(.+)", re.IGNORECASE
)
LEGACY_ROLE_RE = re.compile(
    r"Architectural Role:\s*(.+)", re.IGNORECASE
)

# Directories to scan for KCP headers
SCAN_DIRS = [
    "scripts",
    "src",
    "extensions",
    "game",
    ".temple",
    "docs",
    "claude-codex-gemini",
    "dumpster-dive",
    "meta-ide",
    "plugins",
]

SCAN_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".ps1", ".sh",
    ".md", ".yaml", ".yml", ".toml", ".json",
}

# Maximum file header bytes to scan for KCP cartouche
HEADER_SCAN_BYTES = 2048


# ── Schema ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    path        TEXT UNIQUE NOT NULL,
    title       TEXT,
    sid         TEXT,
    spectrum    TEXT,
    zone        TEXT,
    nsfw_tier   TEXT,
    ankh_layer  TEXT,
    summary     TEXT,
    tribunal    TEXT,
    source      TEXT NOT NULL,
    indexed_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    category    TEXT,
    confidence  TEXT
);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category);
CREATE INDEX IF NOT EXISTS idx_files_spectrum ON files(spectrum);
CREATE INDEX IF NOT EXISTS idx_files_nsfw_tier ON files(nsfw_tier);
CREATE INDEX IF NOT EXISTS idx_files_ankh_layer ON files(ankh_layer);
CREATE INDEX IF NOT EXISTS idx_files_sid ON files(sid);

CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
    path, title, summary, tribunal, tags_text
);
"""

REBUILD_FTS_SQL = """
DELETE FROM files_fts;
INSERT INTO files_fts(rowid, path, title, summary, tribunal, tags_text)
SELECT f.id, f.path, f.title, COALESCE(f.summary,''), COALESCE(f.tribunal,''),
       COALESCE((SELECT GROUP_CONCAT(t.tag, ' ') FROM tags t WHERE t.file_id = f.id), '')
FROM files f;
"""


# ── Database helpers ──────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    """Open (or create) the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    return conn


def upsert_file(conn: sqlite3.Connection, row: dict) -> int:
    """Insert or replace a file record, return its id."""
    conn.execute(
        """INSERT INTO files (path, title, sid, spectrum, zone, nsfw_tier,
           ankh_layer, summary, tribunal, source, indexed_at)
           VALUES (:path, :title, :sid, :spectrum, :zone, :nsfw_tier,
           :ankh_layer, :summary, :tribunal, :source, :indexed_at)
           ON CONFLICT(path) DO UPDATE SET
             title=excluded.title, sid=excluded.sid, spectrum=excluded.spectrum,
             zone=excluded.zone, nsfw_tier=excluded.nsfw_tier,
             ankh_layer=excluded.ankh_layer, summary=excluded.summary,
             tribunal=excluded.tribunal, source=excluded.source,
             indexed_at=excluded.indexed_at""",
        row,
    )
    cursor = conn.execute("SELECT id FROM files WHERE path=?", (row["path"],))
    return cursor.fetchone()[0]


def insert_tags(conn: sqlite3.Connection, file_id: int, tags: list[dict]) -> None:
    """Insert tags for a file (delete old ones first)."""
    conn.execute("DELETE FROM tags WHERE file_id=?", (file_id,))
    for t in tags:
        conn.execute(
            "INSERT INTO tags (file_id, tag, category, confidence) VALUES (?,?,?,?)",
            (file_id, t.get("tag", ""), t.get("category", ""), t.get("confidence", "")),
        )



# ── Ingest: Genre Extraction Digests ─────────────────────────────

def parse_genre_digest(text: str) -> list[dict]:
    """Parse a GENRE_EXTRACTION markdown digest into file records."""
    records = []
    current: dict | None = None

    for line in text.split("\n"):
        # New file entry starts with ### heading
        if line.startswith("### "):
            if current:
                records.append(current)
            current = {
                "title": line[4:].strip(),
                "path": "",
                "tags": [],
                "nsfw_tier": "",
                "ankh_layer": "",
                "summary": "",
                "tribunal": "",
            }
            continue

        if current is None:
            # Detect NSFW tier section headers
            tier_match = re.match(r"^## (EXTREME|EXPLICIT|SUGGESTIVE|NONE)\b", line)
            if tier_match:
                # Will be applied to subsequent entries
                pass
            continue

        if line.startswith("**Path:**"):
            current["path"] = line.split("`")[1] if "`" in line else line[9:].strip()
        elif line.startswith("**Tags:**"):
            tag_text = line[9:].strip()
            for m in re.finditer(r"`([^`]+)`\s*\((\w+)\)", tag_text):
                current["tags"].append({"tag": m.group(1), "category": m.group(2)})
        elif line.startswith("**Ankh Layer:**"):
            current["ankh_layer"] = line[15:].strip()
        elif line.startswith("**Tribunal:**"):
            current["tribunal"] = line[13:].strip()
        elif line.startswith("**Summary:**"):
            current["summary"] = line[12:].strip()

    if current:
        records.append(current)

    # Detect nsfw_tier from section headers
    current_tier = "none"
    for line in text.split("\n"):
        tier_match = re.match(r"^## (EXTREME|EXPLICIT|SUGGESTIVE|NONE)\b", line, re.IGNORECASE)
        if tier_match:
            current_tier = tier_match.group(1).lower()
            continue
        if line.startswith("### "):
            title = line[4:].strip()
            for r in records:
                if r["title"] == title and not r["nsfw_tier"]:
                    r["nsfw_tier"] = current_tier

    return [r for r in records if r.get("path")]


def ingest_genre_digests(conn: sqlite3.Connection) -> int:
    """Ingest all GENRE_EXTRACTION_*.md files from claude/mailbox/."""
    if not GENRE_MAILBOX.exists():
        return 0

    digests = sorted(GENRE_MAILBOX.glob("GENRE_EXTRACTION_*.md"), reverse=True)
    if not digests:
        return 0

    count = 0
    now = datetime.now(timezone.utc).isoformat()
    seen_paths: set[str] = set()

    for digest_path in digests:
        text = digest_path.read_text(encoding="utf-8", errors="replace")
        records = parse_genre_digest(text)

        for rec in records:
            if rec["path"] in seen_paths:
                continue
            seen_paths.add(rec["path"])

            file_id = upsert_file(conn, {
                "path": rec["path"],
                "title": rec["title"],
                "sid": None,
                "spectrum": None,
                "zone": None,
                "nsfw_tier": rec["nsfw_tier"],
                "ankh_layer": rec["ankh_layer"],
                "summary": rec["summary"],
                "tribunal": rec["tribunal"],
                "source": f"genre:{digest_path.name}",
                "indexed_at": now,
            })
            insert_tags(conn, file_id, rec["tags"])
            count += 1

    return count


# ── Ingest: KCP Cartouche Headers ────────────────────────────────

def scan_kcp_header(file_path: Path) -> dict | None:
    """Extract KCP cartouche metadata from a file's header."""
    try:
        head = file_path.read_text(encoding="utf-8", errors="replace")[:HEADER_SCAN_BYTES]
    except Exception:
        return None

    spectrum = None
    zone = None
    sid = None

    m = KCP_SPECTRUM_RE.search(head)
    if m:
        val = m.group(1).strip().rstrip("✓").strip()
        if val.upper() in VALID_SPECTRA:
            spectrum = val.upper()
    if spectrum is None:
        m = LEGACY_SPECTRUM_RE.search(head)
        if m:
            val = m.group(1).strip().rstrip("✓").strip()
            if val.upper() in VALID_SPECTRA:
                spectrum = val.upper()

    m = KCP_ZONE_RE.search(head)
    if m:
        zone = m.group(1).strip()
    else:
        m = LEGACY_ROLE_RE.search(head)
        if m:
            zone = m.group(1).strip()

    m = SID_RE.search(head)
    if m:
        sid = m.group(1).strip()

    if not any((spectrum, zone, sid)):
        return None

    return {"spectrum": spectrum, "zone": zone, "sid": sid}


def ingest_kcp_cartouches(conn: sqlite3.Connection) -> int:
    """Scan repo files for KCP cartouche headers and index them."""
    count = 0
    now = datetime.now(timezone.utc).isoformat()

    for scan_dir in SCAN_DIRS:
        dir_path = REPO_ROOT / scan_dir
        if not dir_path.exists():
            continue
        for f in dir_path.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in SCAN_EXTENSIONS:
                continue
            # Skip node_modules, build artifacts
            rel = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
            if any(skip in rel for skip in ("node_modules/", "target/", "build/", ".next/", "dist/")):
                continue

            kcp = scan_kcp_header(f)
            if not kcp:
                continue

            file_id = upsert_file(conn, {
                "path": rel,
                "title": f.stem,
                "sid": kcp["sid"],
                "spectrum": kcp["spectrum"],
                "zone": kcp["zone"],
                "nsfw_tier": None,
                "ankh_layer": None,
                "summary": None,
                "tribunal": None,
                "source": "kcp",
                "indexed_at": now,
            })
            count += 1

    return count


# ── Ingest: Dumpster-Dive Registry ───────────────────────────────

def ingest_registry(conn: sqlite3.Connection) -> int:
    """Ingest dumpster-dive/DUMPSTER_DIVE_REGISTRY.json."""
    if not REGISTRY_PATH.exists():
        return 0

    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 0

    count = 0
    now = datetime.now(timezone.utc).isoformat()

    def walk_entries(section: dict | list, prefix: str = "") -> list[dict]:
        entries = []
        if isinstance(section, dict):
            for key, val in section.items():
                if key == "files" and isinstance(val, list):
                    for f in val:
                        if isinstance(f, dict) and "relative_path" in f:
                            entries.append(f)
                elif isinstance(val, (dict, list)):
                    entries.extend(walk_entries(val, prefix))
        elif isinstance(section, list):
            for item in section:
                if isinstance(item, dict):
                    if "relative_path" in item:
                        entries.append(item)
                    else:
                        entries.extend(walk_entries(item, prefix))
        return entries

    all_entries = walk_entries(data)

    for entry in all_entries:
        rel_path = entry.get("relative_path", "")
        if not rel_path:
            continue

        tags = []
        category = entry.get("category", "")
        if category:
            tags.append({"tag": category, "category": "theme"})
        forge_status = entry.get("forge_status", "")
        if forge_status:
            tags.append({"tag": forge_status, "category": "mechanic"})

        file_id = upsert_file(conn, {
            "path": rel_path,
            "title": entry.get("file", Path(rel_path).stem),
            "sid": entry.get("identifier"),
            "spectrum": None,
            "zone": None,
            "nsfw_tier": None,
            "ankh_layer": None,
            "summary": entry.get("description", ""),
            "tribunal": None,
            "source": "registry",
            "indexed_at": now,
        })
        insert_tags(conn, file_id, tags)
        count += 1

    return count


# ── Build ─────────────────────────────────────────────────────────

def build_index() -> None:
    """Build (or rebuild) the entire SFS reference index."""
    print("☥ SFS Reference Index — Building...")

    # Remove old DB for clean rebuild
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = get_db()

    genre_count = ingest_genre_digests(conn)
    print(f"  Genre digests: {genre_count} files indexed")

    kcp_count = ingest_kcp_cartouches(conn)
    print(f"  KCP cartouches: {kcp_count} files indexed")

    registry_count = ingest_registry(conn)
    print(f"  Registry entries: {registry_count} files indexed")

    # Rebuild FTS with final tag text
    conn.executescript(REBUILD_FTS_SQL)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    print(f"\n  ☥ Index complete: {total} files, {tag_count} tags")
    print(f"  Database: {DB_PATH}")

    conn.close()


# ── Query ─────────────────────────────────────────────────────────

def format_result(row: dict, verbose: bool = False) -> str:
    """Format a single query result for display."""
    parts = [f"  {row['path']}"]
    meta = []
    if row.get("spectrum"):
        meta.append(f"spectrum:{row['spectrum']}")
    if row.get("nsfw_tier"):
        meta.append(f"tier:{row['nsfw_tier']}")
    if row.get("ankh_layer"):
        meta.append(f"ankh:{row['ankh_layer']}")
    if row.get("sid"):
        meta.append(f"sid:{row['sid']}")
    if row.get("zone"):
        meta.append(f"zone:{row['zone']}")
    if meta:
        parts.append(f"    [{' | '.join(meta)}]")
    if row.get("title"):
        parts.append(f"    Title: {row['title']}")
    if verbose and row.get("summary"):
        summary = row["summary"][:200]
        parts.append(f"    Summary: {summary}...")
    if row.get("tags"):
        parts.append(f"    Tags: {row['tags']}")
    return "\n".join(parts)


def query_index(
    text: str | None = None,
    tag: str | None = None,
    tier: str | None = None,
    layer: str | None = None,
    spectrum: str | None = None,
    zone: str | None = None,
    sid: str | None = None,
    limit: int = 25,
    verbose: bool = False,
) -> None:
    """Query the SFS reference index."""
    if not DB_PATH.exists():
        print("ERROR: Index not built. Run: uv run scripts/sfs_reference_index.py build")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Build query based on filters
    conditions = []
    params: list = []

    if text:
        # FTS5 search
        conditions.append("f.id IN (SELECT rowid FROM files_fts WHERE files_fts MATCH ?)")
        params.append(text)

    if tag:
        conditions.append("f.id IN (SELECT file_id FROM tags WHERE tag LIKE ?)")
        params.append(f"%{tag}%")

    if tier:
        conditions.append("f.nsfw_tier = ?")
        params.append(tier.lower())

    if layer:
        conditions.append("UPPER(f.ankh_layer) = ?")
        params.append(layer.upper())

    if spectrum:
        conditions.append("UPPER(f.spectrum) = ?")
        params.append(spectrum.upper())

    if zone:
        conditions.append("f.zone LIKE ?")
        params.append(f"%{zone}%")

    if sid:
        conditions.append("f.sid LIKE ?")
        params.append(f"%{sid}%")

    where = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT f.*, GROUP_CONCAT(t.tag, ', ') as tags
        FROM files f
        LEFT JOIN tags t ON t.file_id = f.id
        WHERE {where}
        GROUP BY f.id
        ORDER BY f.path
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(query, params).fetchall()

    if not rows:
        print("No results found.")
        return

    print(f"☥ {len(rows)} result(s):\n")
    for row in rows:
        print(format_result(dict(row), verbose=verbose))
        print()

    conn.close()


# ── Stats ─────────────────────────────────────────────────────────

def show_stats() -> None:
    """Show index statistics."""
    if not DB_PATH.exists():
        print("ERROR: Index not built. Run: uv run scripts/sfs_reference_index.py build")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
    print(f"☥ SFS Reference Index Stats")
    print(f"  Database: {DB_PATH}")
    print(f"  Total files: {total}")
    print(f"  Total tags: {tag_count}")

    # By source
    print("\n  By source:")
    for row in conn.execute("SELECT source, COUNT(*) as c FROM files GROUP BY source ORDER BY c DESC"):
        print(f"    {row[0]}: {row[1]}")

    # By spectrum
    print("\n  By Wedjat-Quipu Spectrum:")
    for row in conn.execute(
        "SELECT COALESCE(spectrum, '(none)') as s, COUNT(*) as c FROM files GROUP BY s ORDER BY c DESC"
    ):
        print(f"    {row[0]}: {row[1]}")

    # By nsfw_tier
    print("\n  By NSFW Tier:")
    for row in conn.execute(
        "SELECT COALESCE(nsfw_tier, '(none)') as t, COUNT(*) as c FROM files GROUP BY t ORDER BY c DESC"
    ):
        print(f"    {row[0]}: {row[1]}")

    # By ankh_layer
    print("\n  By Ankh Layer:")
    for row in conn.execute(
        "SELECT COALESCE(ankh_layer, '(none)') as l, COUNT(*) as c FROM files GROUP BY l ORDER BY c DESC"
    ):
        print(f"    {row[0]}: {row[1]}")

    # Top tags
    print("\n  Top 20 Tags:")
    for row in conn.execute(
        "SELECT tag, category, COUNT(*) as c FROM tags GROUP BY tag ORDER BY c DESC LIMIT 20"
    ):
        print(f"    {row[0]} ({row[1]}): {row[2]}")

    conn.close()


# ── CLI ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SFS Reference Index — unified file intelligence for agents"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="Build or rebuild the index")

    q = sub.add_parser("query", help="Query the index")
    q.add_argument("text", nargs="?", help="Free-text FTS5 search")
    q.add_argument("--tag", help="Filter by tag (substring match)")
    q.add_argument("--tier", help="Filter by NSFW tier (none/suggestive/explicit/extreme)")
    q.add_argument("--layer", help="Filter by Ankh layer (LOOP/KNOT/CROSSBAR/PILLAR)")
    q.add_argument("--spectrum", help="Filter by Wedjat-Quipu Spectrum (WHITE/RED/BLUE/etc)")
    q.add_argument("--zone", help="Filter by Temple-Ayllu Zone (substring)")
    q.add_argument("--sid", help="Filter by @SID (substring)")
    q.add_argument("--limit", type=int, default=25, help="Max results (default: 25)")
    q.add_argument("-v", "--verbose", action="store_true", help="Show summaries")

    sub.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()

    if args.command == "build":
        build_index()
    elif args.command == "query":
        query_index(
            text=args.text,
            tag=args.tag,
            tier=args.tier,
            layer=args.layer,
            spectrum=args.spectrum,
            zone=args.zone,
            sid=args.sid,
            limit=args.limit,
            verbose=args.verbose,
        )
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
