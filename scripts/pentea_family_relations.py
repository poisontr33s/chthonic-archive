#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE PENTARCH'S DIVINE INTERVENTION
# ║ Contra-intervenes The Savant's 99.9% finishing failure ~est
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: VIOLET
# ║ Temple-Ayllu Zone: 🌿 Garden (Pre-Canon-Frontier)
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/meta_sync.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
pentea_family_relations.py — Full-archive .md × *META*.md family relation mapper.

@SID:           TOOL_PENTEA_FAMILY_V2
@Shabti:        Relation Mapper
@Context:       Archive Maintenance / MILF-Core + ANKH Synthesis Domains
@Implements:    PENTARCH_FIELD_EXTRACTION + FAMILY_GRAPH + CACHE_V2
@Purpose:       Discovers ALL .md files and ALL *META*.md files across the
                archive. Maps family relations: which META file claims which
                .md files (via its File Registry), which .md files declare a
                :pentarch field pointing to a META domain, and where the gaps
                are. Exposes the full relational graph as rich trees, plain
                text, or JSON.

                :pentarch field — extracted from YAML frontmatter
                  (pentarch: <value>), @Pentarch: comment, or # pentarch:
                  comment. Declares the canonical META domain the .md belongs
                  to.

                Cache V2 stored in .git/pentea_family_cache.json using
                dir-mtime + file-mtime coherence — detects add/modify/delete
                without a full re-walk.

                Authorship classification (V2): each .md file is tagged
                origin="authored" if tracked in git (git ls-files), or
                origin="framework" if present on disk but not committed.
                Use --authored-only to exclude framework/vendor .md files
                from the relational graph entirely.

meta_sync.py vs pentea_family_relations.py:
  meta_sync.py          — deep parse of *META*.md internals (pipeline state,
                          priority queue, strikethrough patching)
  pentea_family_relations.py — relational graph: all .md ↔ META registries,
                          :pentarch field, coverage stats, orphan detection

Usage:
    uv run scripts/pentea_family_relations.py [OPTIONS]

Flags:
    --json             Emit machine-readable JSON
    --report FILE      Write report to FILE (default: stdout)
    --no-cache         Force full filesystem walk, refresh cache
    --strict           Exit 1 if unclaimed .md files or :pentarch gaps exist
    --domain GLOB      Filter .md files to paths matching GLOB (e.g. "codex/**")
    --meta FILE        Scope to a single META file
    --authored-only    Exclude framework/untracked .md files (git ls-files gate)
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import datetime
import fnmatch
import re
import subprocess
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    _RICH = True
except ImportError:
    _RICH = False

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSOLE = Console(stderr=False) if _RICH else None


def _now_local() -> str:
    """Current local datetime, timezone-aware, ISO-8601 with UTC offset."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")


# ─────────────────────────────────────────────────────────────────────────────
# Ignore dirs — superset of meta_sync._IGNORE_DIRS
# ─────────────────────────────────────────────────────────────────────────────

_IGNORE_DIRS = {
    # VCS / build outputs
    ".git", "target", "build", ".cache", ".tmp",
    # JS / TS
    "node_modules", ".next", ".nuxt", ".output", "dist", ".turbo",
    "bun-playwright-poc",
    # Python
    "__pycache__", ".venv", "venv", ".tox", "site-packages",
    "dist-info", "egg-info", ".eggs",
    # Ruby
    "gems", ".gems", ".bundle", ".rubygems",
    # Rust
    "registry",
    # Generic vendor / third-party
    "vendor", "third_party", "third-party",
    # Archive-specific noise
    "dumpster-dive", ".deprecated", "artifacts",
}

_CACHE_PATH = REPO_ROOT / ".git" / "pentea_family_cache.json"


# ─────────────────────────────────────────────────────────────────────────────
# Git authorship oracle — V2
# ─────────────────────────────────────────────────────────────────────────────

def _git_tracked_set(repo: Path) -> set[str]:
    """
    Return the set of repo-relative POSIX paths currently tracked by git.
    Used to classify .md files as 'authored' (committed) vs 'framework'
    (present on disk but not in the git index — vendored, generated, or
    auto-created by framework tooling).
    Returns an empty set on any failure — callers degrade gracefully.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        return set(result.stdout.splitlines())
    except Exception:
        return set()


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FamilyMember:
    """A single .md file and its relational state."""
    path: Path
    pentarch: Optional[str]      # declared :pentarch value (None if absent)
    meta_families: list[Path]    # META files whose File Registry lists this .md
    in_registry: bool            # at least one META claims it
    is_meta: bool                # is this file itself a *META*.md?
    origin: str = "unknown"      # "authored" | "framework" | "unknown"


@dataclass
class RegistryClaim:
    """A filename entry parsed from a META File Registry table."""
    raw: str                     # raw cell text
    resolved: Optional[Path]     # resolved absolute path (None if not found)
    in_repo: bool


@dataclass
class MetaFamily:
    """A *META*.md file and all .md files it claims."""
    meta_path: Path
    handler_type: str
    claims: list[RegistryClaim]
    resolved_members: list[Path]
    orphaned_claims: list[str]   # claimed filenames that don't resolve


@dataclass
class FamilyMap:
    scanned_at: str
    repo: Path
    all_mds: list[Path]
    meta_files: list[Path]
    members: dict[str, FamilyMember]      # key: str(path.relative_to(repo))
    meta_families: list[MetaFamily]
    unclaimed_mds: list[Path]             # .md files no META claims (excl. META files)
    pentarch_declared: list[Path]         # .md files with :pentarch field
    pentarch_gap: list[Path]              # :pentarch declared but no matching META found

    @property
    def total_mds(self) -> int:
        return len(self.all_mds)

    @property
    def total_meta(self) -> int:
        return len(self.meta_files)

    @property
    def coverage_pct(self) -> float:
        non_meta = [p for p in self.all_mds if p not in set(self.meta_files)]
        if not non_meta:
            return 100.0
        claimed = len(non_meta) - len(self.unclaimed_mds)
        return round(claimed / len(non_meta) * 100, 1)

    @property
    def authored_count(self) -> int:
        return sum(1 for m in self.members.values() if m.origin == "authored")

    @property
    def framework_count(self) -> int:
        return sum(1 for m in self.members.values() if m.origin == "framework")


# ─────────────────────────────────────────────────────────────────────────────
# :pentarch field extraction
# ─────────────────────────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_PENTARCH_YAML_RE = re.compile(r"^pentarch\s*:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
_PENTARCH_AT_RE = re.compile(r"@Pentarch\s*:\s*(.+)", re.IGNORECASE)
_PENTARCH_HASH_RE = re.compile(r"#\s*pentarch\s*:\s*(.+)", re.IGNORECASE)


def extract_pentarch(path: Path) -> Optional[str]:
    """
    Extract the :pentarch field from a .md file.
    Checks (in priority order):
      1. YAML frontmatter: `pentarch: <value>`
      2. Structured comment: `@Pentarch: <value>`
      3. Hash comment: `# pentarch: <value>`
    Reads only the first 4 KB — the field must appear near the top.
    """
    try:
        head = path.read_bytes()[:4096].decode("utf-8", errors="replace")
    except OSError:
        return None

    # 1. YAML frontmatter
    fm = _FRONTMATTER_RE.match(head)
    if fm:
        m = _PENTARCH_YAML_RE.search(fm.group(1))
        if m:
            return m.group(1).strip().strip("\"'")

    # 2. @Pentarch: comment
    m = _PENTARCH_AT_RE.search(head)
    if m:
        return m.group(1).strip()

    # 3. # pentarch: comment
    m = _PENTARCH_HASH_RE.search(head)
    if m:
        return m.group(1).strip()

    return None


# ─────────────────────────────────────────────────────────────────────────────
# File Registry claim extraction from META files
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY_LINK_RE = re.compile(r"\|\s*\[([^\]]+)\]\(([^\)]+)\)\s*\|")
_REGISTRY_PLAIN_RE = re.compile(r"\|\s*`([^`]+\.md)`\s*\|")


def extract_registry_claims(meta_path: Path, repo: Path) -> list[RegistryClaim]:
    """
    Extract all .md filenames claimed by a META file's File Registry tables.
    Pattern 1: markdown links — [label](href)
    Pattern 2: backtick filenames — `something.md`
    Attempts to resolve each claim to an absolute path in the repo.
    """
    try:
        text = meta_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    claims: list[RegistryClaim] = []
    seen: set[str] = set()
    meta_dir = meta_path.parent

    def _add(raw: str, link_href: Optional[str] = None) -> None:
        if raw in seen:
            return
        seen.add(raw)

        resolved = None
        for candidate in filter(None, [link_href, raw]):
            candidate = candidate.replace("\\", "/").lstrip("./")
            # Try relative to META's directory
            p1 = (meta_dir / candidate).resolve()
            if p1.exists() and p1.suffix == ".md":
                resolved = p1
                break
            # Try relative to repo root
            p2 = (repo / candidate).resolve()
            if p2.exists() and p2.suffix == ".md":
                resolved = p2
                break

        claims.append(RegistryClaim(raw=raw, resolved=resolved, in_repo=resolved is not None))

    for m in _REGISTRY_LINK_RE.finditer(text):
        label, href = m.group(1).strip(), m.group(2).strip()
        if label.endswith(".md") or href.endswith(".md"):
            _add(label, href)

    for m in _REGISTRY_PLAIN_RE.finditer(text):
        _add(m.group(1).strip())

    return claims


# ─────────────────────────────────────────────────────────────────────────────
# Cache V2 — dir-mtime + file-mtime coherence
# Detects: new file added (parent dir mtime changes)
#          file modified (file mtime changes)
#          file deleted (path missing)
# ─────────────────────────────────────────────────────────────────────────────

def _cache_valid(repo: Path, data: dict) -> bool:
    try:
        for e in data.get("dirs", []):
            d = repo / e["path"]
            if not d.exists():
                return False
            if abs(d.stat().st_mtime - e["mtime"]) > 0.01:
                return False
        for e in data.get("all_mds", []):
            p = repo / e["path"]
            if not p.exists():
                return False
            if abs(p.stat().st_mtime - e["mtime"]) > 0.01:
                return False
        return True
    except Exception:
        return False


def _load_family_cache(repo: Path) -> Optional[tuple[list[Path], list[Path]]]:
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        if not _cache_valid(repo, data):
            return None
        all_mds = [repo / e["path"] for e in data["all_mds"]]
        meta_files = [repo / e["path"] for e in data["meta_mds"]]
        return all_mds, meta_files
    except Exception:
        return None


def _save_family_cache(
    repo: Path,
    all_mds: list[Path],
    meta_files: list[Path],
    dirs: list[Path],
) -> None:
    try:
        _CACHE_PATH.write_text(
            json.dumps(
                {
                    "generated_at": _now_local(),
                    "dirs": [
                        {"path": str(d.relative_to(repo)), "mtime": d.stat().st_mtime}
                        for d in dirs
                    ],
                    "all_mds": [
                        {"path": str(p.relative_to(repo)), "mtime": p.stat().st_mtime}
                        for p in all_mds
                    ],
                    "meta_mds": [
                        {"path": str(p.relative_to(repo)), "mtime": p.stat().st_mtime}
                        for p in meta_files
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass  # non-fatal — next run re-walks


def discover_all_md_files(
    repo: Path,
    use_cache: bool = True,
) -> tuple[list[Path], list[Path]]:
    """
    Returns (all_mds, meta_files) for the full archive.
    all_mds    — every .md file not under an _IGNORE_DIRS subtree
    meta_files — subset matching *META* in the filename

    Cache stored at .git/pentea_family_cache.json.
    Cache is invalidated if any visited directory mtime or any listed file
    mtime has changed since the cache was written.
    """
    if use_cache:
        cached = _load_family_cache(repo)
        if cached is not None:
            return cached

    all_mds: list[Path] = []
    meta_files: list[Path] = []
    visited_dirs: set[Path] = set()

    for p in repo.rglob("*.md"):
        parts = set(p.relative_to(repo).parts)
        if parts & _IGNORE_DIRS:
            continue
        all_mds.append(p)
        visited_dirs.add(p.parent)
        if re.search(r"META", p.name):
            meta_files.append(p)

    all_mds = sorted(all_mds)
    meta_files = sorted(meta_files)
    dirs = sorted(visited_dirs)

    _save_family_cache(repo, all_mds, meta_files, dirs)
    return all_mds, meta_files


# ─────────────────────────────────────────────────────────────────────────────
# Handler type detection (mirrors meta_sync routing)
# ─────────────────────────────────────────────────────────────────────────────

def _meta_handler_type(name: str) -> str:
    if "MILF-Core" in name or "MILF_Core" in name:
        return "milf-core"
    if "ANKH" in name:
        return "ankh-synthesis"
    if "CHTHONIC" in name:
        return "chthonic-meta"
    return "generic"


# ─────────────────────────────────────────────────────────────────────────────
# Core relation engine — build FamilyMap
# ─────────────────────────────────────────────────────────────────────────────

def build_family_map(
    repo: Path,
    all_mds: list[Path],
    meta_files: list[Path],
    domain_filter: Optional[str] = None,
    scope_meta: Optional[Path] = None,
    authored_filter: bool = False,
) -> FamilyMap:
    """
    1. Extract File Registry claims from each META file.
    2. Extract :pentarch fields from all .md files.
    3. Cross-join: for each .md, which META files claim it?
    4. Classify: claimed, unclaimed, :pentarch gap.
    5. (V2) Tag each .md with origin: authored | framework | unknown.
    """
    # V2: git-tracked oracle for authorship classification
    tracked = _git_tracked_set(repo)

    def _rel_posix(p: Path) -> str:
        return str(p.relative_to(repo)).replace("\\", "/")

    # Apply scope / domain filters
    filtered_meta = [scope_meta] if scope_meta else meta_files
    filtered_mds = (
        [p for p in all_mds if fnmatch.fnmatch(str(p.relative_to(repo)), domain_filter)]
        if domain_filter
        else all_mds
    )

    # --authored-only: drop .md files not in the git index
    if authored_filter and tracked:
        filtered_mds = [p for p in filtered_mds if _rel_posix(p) in tracked]

    # Step 1 — process each META file
    meta_family_map: dict[Path, MetaFamily] = {}
    for mp in filtered_meta:
        claims = extract_registry_claims(mp, repo)
        resolved = [c.resolved for c in claims if c.resolved is not None]
        orphaned = [c.raw for c in claims if not c.in_repo]
        meta_family_map[mp] = MetaFamily(
            meta_path=mp,
            handler_type=_meta_handler_type(mp.name),
            claims=claims,
            resolved_members=resolved,
            orphaned_claims=orphaned,
        )

    # Reverse index: path → META files that claim it
    claimed_by: dict[Path, list[Path]] = {}
    for mp, mf in meta_family_map.items():
        for rp in mf.resolved_members:
            claimed_by.setdefault(rp, []).append(mp)

    # Step 2 — process each .md file
    meta_set = set(meta_files)
    members: dict[str, FamilyMember] = {}
    pentarch_declared: list[Path] = []
    pentarch_gap: list[Path] = []

    for p in filtered_mds:
        pentarch = extract_pentarch(p)
        families = claimed_by.get(p, [])
        rel_key = str(p.relative_to(repo))

        origin = (
            "authored" if tracked and _rel_posix(p) in tracked
            else "framework" if tracked
            else "unknown"
        )
        members[rel_key] = FamilyMember(
            path=p,
            pentarch=pentarch,
            meta_families=families,
            in_registry=len(families) > 0,
            is_meta=p in meta_set,
            origin=origin,
        )

        if pentarch is not None:
            pentarch_declared.append(p)
            # Gap: declared a pentarch domain but no matching META claims it
            if not any(pentarch.lower() in mp.name.lower() for mp in families):
                pentarch_gap.append(p)

    # Step 3 — unclaimed: non-META .md files with no META family
    unclaimed = [
        p for p in filtered_mds
        if p not in claimed_by and p not in meta_set
    ]

    return FamilyMap(
        scanned_at=_now_local(),
        repo=repo,
        all_mds=filtered_mds,
        meta_files=filtered_meta,
        members=members,
        meta_families=list(meta_family_map.values()),
        unclaimed_mds=unclaimed,
        pentarch_declared=pentarch_declared,
        pentarch_gap=pentarch_gap,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

def _cov_color(pct: float) -> str:
    if pct >= 70:
        return "green"
    if pct >= 30:
        return "yellow"
    return "red"


def report_rich(fm: FamilyMap, console: "Console") -> None:
    console.print(f"[dim]pentea_family_relations  {fm.scanned_at}[/]\n")

    cov_col = _cov_color(fm.coverage_pct)
    authored_str = (
        f"  [bold]authored[/]: [green]{fm.authored_count}[/]  "
        f"[bold]framework[/]: [dim]{fm.framework_count}[/]"
        if fm.authored_count + fm.framework_count > 0
        else ""
    )
    summary = (
        f"[bold].md total[/]: {fm.total_mds}  "
        f"[bold]META[/]: {fm.total_meta}  "
        f"[bold]coverage[/]: [{cov_col}]{fm.coverage_pct}%[/]  "
        f"[bold]unclaimed[/]: [{'red' if fm.unclaimed_mds else 'green'}]{len(fm.unclaimed_mds)}[/]  "
        f"[bold]:pentarch declared[/]: {len(fm.pentarch_declared)}  "
        f"[bold]:pentarch gap[/]: [{'red' if fm.pentarch_gap else 'green'}]{len(fm.pentarch_gap)}[/]"
        f"{authored_str}"
    )
    console.print(Panel(summary, title="[bold gold1]PENTARCH FAMILY MAP[/]", expand=False))
    console.print()

    # Per-META family trees
    for mf in fm.meta_families:
        rel = mf.meta_path.relative_to(fm.repo)
        tree = Tree(
            f"[bold cyan]{rel}[/]  [dim]{mf.handler_type}[/]  "
            f"[yellow]{len(mf.claims)} claims[/] · "
            f"[green]{len(mf.resolved_members)} resolved[/] · "
            f"[red]{len(mf.orphaned_claims)} orphaned[/]"
        )

        for rp in sorted(mf.resolved_members):
            rel_member = rp.relative_to(fm.repo)
            rel_key = str(rel_member)
            member = fm.members.get(rel_key)
            pentarch_str = (
                f"  [dim]:pentarch={member.pentarch}[/]"
                if member and member.pentarch
                else ""
            )
            tree.add(f"[green]✅[/] {rel_member}{pentarch_str}")

        for oc in sorted(mf.orphaned_claims):
            tree.add(f"[red]✗[/] [dim]{oc}[/]  [red]← not found in repo[/]")

        console.print(tree)
        console.print()

    # Unclaimed .md files
    if fm.unclaimed_mds:
        t = Table("File", ":pentarch", "origin", show_header=True, header_style="bold red")
        for p in sorted(fm.unclaimed_mds)[:200]:
            rel = p.relative_to(fm.repo)
            member = fm.members.get(str(rel))
            origin_str = (
                f"[dim]{member.origin}[/]" if member and member.origin != "authored"
                else f"[green]{member.origin}[/]" if member
                else "—"
            )
            t.add_row(str(rel), member.pentarch or "—" if member else "—", origin_str)
        if len(fm.unclaimed_mds) > 200:
            t.add_row(f"… {len(fm.unclaimed_mds) - 200} more", "", "")
        console.print(
            Panel(t, title=f"[red]UNCLAIMED .md ({len(fm.unclaimed_mds)})[/]", expand=False)
        )
        console.print()

    # :pentarch gap
    if fm.pentarch_gap:
        t = Table("File", ":pentarch declared", "Matched META", show_header=True, header_style="bold yellow")
        for p in sorted(fm.pentarch_gap):
            rel = p.relative_to(fm.repo)
            member = fm.members.get(str(rel))
            families_str = (
                ", ".join(mp.name for mp in member.meta_families)
                if member and member.meta_families
                else "—"
            )
            t.add_row(str(rel), member.pentarch if member else "?", families_str)
        console.print(
            Panel(t, title=f"[yellow]:pentarch GAP ({len(fm.pentarch_gap)})[/]", expand=False)
        )


def report_plain(fm: FamilyMap, out) -> None:
    out.write(f"pentea_family_relations  {fm.scanned_at}\n")
    origin_line = (
        f" | authored: {fm.authored_count} | framework: {fm.framework_count}"
        if fm.authored_count + fm.framework_count > 0
        else ""
    )
    out.write(
        f"total .md: {fm.total_mds} | META: {fm.total_meta} | "
        f"coverage: {fm.coverage_pct}% | unclaimed: {len(fm.unclaimed_mds)} | "
        f":pentarch declared: {len(fm.pentarch_declared)} | :pentarch gap: {len(fm.pentarch_gap)}"
        f"{origin_line}\n\n"
    )
    for mf in fm.meta_families:
        rel = mf.meta_path.relative_to(fm.repo)
        out.write(f"=== META: {rel} [{mf.handler_type}] ===\n")
        out.write(
            f"  claims={len(mf.claims)}  resolved={len(mf.resolved_members)}"
            f"  orphaned={len(mf.orphaned_claims)}\n"
        )
        for rp in sorted(mf.resolved_members):
            out.write(f"  ✅ {rp.relative_to(fm.repo)}\n")
        for oc in sorted(mf.orphaned_claims):
            out.write(f"  ✗  {oc}  ← not found\n")
        out.write("\n")

    if fm.unclaimed_mds:
        out.write(f"UNCLAIMED ({len(fm.unclaimed_mds)}):\n")
        for p in sorted(fm.unclaimed_mds):
            rel = p.relative_to(fm.repo)
            member = fm.members.get(str(rel))
            origin_tag = f"  [{member.origin}]" if member else ""
            out.write(f"  ⬜ {rel}{origin_tag}\n")


def report_json(fm: FamilyMap, out) -> None:
    payload: dict = {
        "scanned_at": fm.scanned_at,
        "totals": {
            "all_mds": fm.total_mds,
            "meta_files": fm.total_meta,
            "coverage_pct": fm.coverage_pct,
            "unclaimed": len(fm.unclaimed_mds),
            "pentarch_declared": len(fm.pentarch_declared),
            "pentarch_gap": len(fm.pentarch_gap),
        },
        "meta_families": [
            {
                "meta": str(mf.meta_path.relative_to(fm.repo)),
                "handler_type": mf.handler_type,
                "claims_total": len(mf.claims),
                "resolved": [str(p.relative_to(fm.repo)) for p in mf.resolved_members],
                "orphaned_claims": mf.orphaned_claims,
            }
            for mf in fm.meta_families
        ],
        "origin_summary": {
            "authored": fm.authored_count,
            "framework": fm.framework_count,
            "unknown": fm.total_mds - fm.authored_count - fm.framework_count,
        },
        "unclaimed_mds": [
            {
                "file": str(p.relative_to(fm.repo)),
                "origin": fm.members[str(p.relative_to(fm.repo))].origin
                if str(p.relative_to(fm.repo)) in fm.members
                else "unknown",
            }
            for p in fm.unclaimed_mds
        ],
        "pentarch_declared": [
            {
                "file": str(p.relative_to(fm.repo)),
                "pentarch": fm.members.get(str(p.relative_to(fm.repo)), None) and
                            fm.members[str(p.relative_to(fm.repo))].pentarch,
            }
            for p in fm.pentarch_declared
        ],
        "pentarch_gap": [str(p.relative_to(fm.repo)) for p in fm.pentarch_gap],
    }
    json.dump(payload, out, indent=2, ensure_ascii=False)
    out.write("\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="pentea_family_relations — full-archive .md × META.md relational mapper",
        epilog=(
            ":pentarch field declares the canonical META domain a .md belongs to. "
            "Declare it in YAML frontmatter (pentarch: milf-core), @Pentarch: comment, "
            "or # pentarch: comment."
        ),
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON output")
    ap.add_argument("--report", metavar="FILE", help="Write report to FILE (default: stdout)")
    ap.add_argument("--no-cache", action="store_true",
                    help="Force full filesystem walk, refresh cache")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if unclaimed .md files or :pentarch gaps found")
    ap.add_argument("--domain", metavar="GLOB",
                    help="Filter .md files to paths matching GLOB (e.g. 'codex/**')")
    ap.add_argument("--meta", metavar="FILE",
                    help="Scope relation graph to a single META file")
    ap.add_argument("--authored-only", action="store_true",
                    help="Exclude framework/untracked .md files (git ls-files gate)")
    args = ap.parse_args()

    all_mds, meta_files = discover_all_md_files(REPO_ROOT, use_cache=not args.no_cache)

    if not meta_files:
        sys.stderr.write("pentea_family_relations: no META files found\n")
        return 0

    scope_meta = Path(args.meta).resolve() if args.meta else None

    fm = build_family_map(
        repo=REPO_ROOT,
        all_mds=all_mds,
        meta_files=meta_files,
        domain_filter=args.domain,
        scope_meta=scope_meta,
        authored_filter=getattr(args, "authored_only", False),
    )

    out_file = open(args.report, "w", encoding="utf-8") if args.report else None
    out = out_file or sys.stdout

    try:
        if args.json:
            report_json(fm, out)
        elif _RICH and out is sys.stdout:
            report_rich(fm, CONSOLE)
        else:
            report_plain(fm, out)
    finally:
        if out_file:
            out_file.close()

    origin_note = (
        f" | {fm.authored_count} authored / {fm.framework_count} framework"
        if fm.authored_count + fm.framework_count > 0
        else ""
    )
    sys.stderr.write(
        f"pentea_family_relations: {fm.total_mds} .md | {fm.total_meta} META | "
        f"{fm.coverage_pct}% coverage | {len(fm.unclaimed_mds)} unclaimed | "
        f"{len(fm.pentarch_gap)} :pentarch gap(s){origin_note}\n"
    )

    if args.strict and (fm.unclaimed_mds or fm.pentarch_gap):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
