#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: meta_sync.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GOLD
# ║ Temple-Ayllu Zone: 🏰 FORTRESS
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ scripts/autonomous_coordinator.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
meta_sync.py — Cross-archive META registry synchronizer.

@SID:           TOOL_META_SYNC_V1
@Shabti:        Registry Tool
@Context:       Archive Maintenance / MILF-Core Pipeline
@Implements:    CONCEPT_MLRSP_LEND + META_CROSS_SYNC
@Purpose:       Discovers all META files in the archive, extracts their
                pipeline state and priority queue sections, cross-references
                git log for committed items, emits a unified summary, and
                optionally patches META files to ensure done items are
                correctly crossed out.

Lending mechanism derived from SSOT §10.6 MLRSP:
  $lend${capability}@$from${source}@$to${target}@$duration${temp|perm}
  Allows extraction logic from one META handler to be borrowed by another.

Usage:
    uv run scripts/meta_sync.py [--patch] [--report FILE] [--json]

Flags:
    --patch          Write ~~strikethrough~~ patches back to META files
                     for done Priority Queue items. Dry-run by default.
    --report FILE    Write the summary to FILE (default: stdout)
    --json           Emit machine-readable JSON instead of rich tables
    --strict         Exit 1 if any META file has a sync discrepancy
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import datetime
import re
import sys
import json
import subprocess
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    _RICH = True
except ImportError:
    _RICH = False

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSOLE = Console(stderr=False) if _RICH else None


def _now_local() -> str:
    """Current local datetime, timezone-aware, ISO-8601 with UTC offset."""
    return datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")

# ─────────────────────────────────────────────────────────────────────────────
# MLRSP Lend  §10.6 — $lend${capability}@$from${source}@$to${target}@$duration
# ─────────────────────────────────────────────────────────────────────────────

def lend(capability: str, from_source: object, to_target: object, duration: str = "temporary"):
    """
    MLRSP lending protocol (SSOT §10.6):
      Borrow a callable capability from one META handler object to another.

      duration="temporary" — returns the fn; does NOT attach to target
      duration="permanent" — attaches fn to target instance as a bound method

    Example:
      extract_fn = lend("extract_pipeline_state", milf_handler, ankh_handler)
      rows = extract_fn(ankh_handler.text)
    """
    fn = getattr(from_source, capability, None)
    if fn is None:
        raise AttributeError(
            f"MLRSP LEND FAILED: {type(from_source).__name__} has no capability '{capability}'"
        )
    if duration == "permanent":
        import types
        setattr(to_target, capability, types.MethodType(fn.__func__ if hasattr(fn, '__func__') else fn, to_target))
    return fn


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineStep:
    label: str          # e.g. "Step 7"
    description: str
    status: str         # "done" | "pending" | "unblocked"
    ref: str            # e.g. "Step7" or "Pending"

@dataclass
class QueueItem:
    id: str             # e.g. "MC-04"
    task: str           # raw cell text
    task_clean: str     # stripped of ~~ markers
    done: bool
    commit_ref: str
    notes: str

@dataclass
class DeclaredGap:
    gap: str            # raw cell text
    gap_clean: str
    closed: bool
    severity: str

@dataclass
class FileRegistryEntry:
    filename: str
    signal: str
    status: str         # "Complete" | "Active" | "Source" | "Superseded"

@dataclass
class MetaSyncResult:
    path: Path
    handler_type: str
    pipeline_steps: list[PipelineStep] = field(default_factory=list)
    queue_items: list[QueueItem] = field(default_factory=list)
    declared_gaps: list[DeclaredGap] = field(default_factory=list)
    file_registry: list[FileRegistryEntry] = field(default_factory=list)
    patch_hunks: list[tuple[str, str]] = field(default_factory=list)   # (old, new)
    errors: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Git helpers
# ─────────────────────────────────────────────────────────────────────────────

def _git_completed_trailers(repo: Path) -> set[str]:
    """Return all Pentea-Completed: values from git log."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--format=%B", "--all"],
            cwd=repo, text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return set()
    completed = set()
    for line in out.splitlines():
        m = re.match(r"Pentea-Completed:\s+(.+)", line.strip())
        if m:
            completed.add(m.group(1).strip())
    return completed


def _git_all_commits(repo: Path) -> list[tuple[str, str]]:
    """Return list of (short_hash, subject) for all commits."""
    try:
        out = subprocess.check_output(
            ["git", "log", "--format=%h %s", "--all"],
            cwd=repo, text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return []
    result = []
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            result.append((parts[0], parts[1]))
    return result


def _git_tracked_files(repo: Path) -> set[str]:
    """Return set of all files currently tracked by git (relative paths)."""
    try:
        out = subprocess.check_output(
            ["git", "ls-files"],
            cwd=repo, text=True, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return set()
    return set(out.splitlines())


# ─────────────────────────────────────────────────────────────────────────────
# MILF-Core META handler
# ─────────────────────────────────────────────────────────────────────────────

class MilfCoreMetaHandler:
    """
    Handles MILF-Core-META.md style documents.
    Sections parsed:
      - § Pipeline State  (fenced code block, one step per line)
      - § Priority Queue  (markdown table)
      - § File Registry   (markdown table, multiple subsections)
    """

    HANDLER_TYPE = "milf-core"

    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")

    def extract_pipeline_state(self, text: Optional[str] = None) -> list[PipelineStep]:
        """Parse the fenced code block under '## § Pipeline State'."""
        src = text if text is not None else self.text
        steps: list[PipelineStep] = []
        m = re.search(r"##\s+§\s+Pipeline\s+State\s*\n+```(.*?)```", src, re.DOTALL)
        if not m:
            return steps
        block = m.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Pattern: "Step N  description  ✅|⬜ ref"
            lm = re.match(r"(Step\s+[\w\-]+)\s{2,}(.+?)\s{2,}(✅|⬜)\s+(.*)", line)
            if not lm:
                # Try looser match for "Steps 11-28" etc.
                lm = re.match(r"(Steps?\s+[\w\-]+)\s+(.*?)\s+(✅|⬜)\s+(.*)", line)
            if lm:
                label, desc, mark, ref = lm.group(1), lm.group(2).strip(), lm.group(3), lm.group(4).strip()
                status = "done" if mark == "✅" else (
                    "unblocked" if "unblocked" in ref.lower() else "pending"
                )
                steps.append(PipelineStep(label=label, description=desc, status=status, ref=ref))
        return steps

    def extract_priority_queue(self) -> list[QueueItem]:
        """Parse the markdown table under '## § Priority Queue'."""
        items: list[QueueItem] = []
        m = re.search(r"##\s+§\s+Priority\s+Queue.*?\n(.*?)(?:\n##|\Z)", self.text, re.DOTALL)
        if not m:
            return items
        block = m.group(1)
        for row in re.finditer(r"\|\s*([A-Z\-]+\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", block):
            id_, task_raw, _, notes = row.group(1), row.group(2), row.group(3), row.group(4)
            if id_.startswith("ID"):  # header row
                continue
            done = "✅" in notes or "~~" in task_raw
            task_clean = re.sub(r"~~(.+?)~~", r"\1", task_raw).strip()
            commit_m = re.search(r"`([0-9a-f]{7,}|Step\w+)`", notes)
            commit_ref = commit_m.group(1) if commit_m else ""
            items.append(QueueItem(
                id=id_, task=task_raw, task_clean=task_clean,
                done=done, commit_ref=commit_ref, notes=notes.strip()
            ))
        return items

    def extract_file_registry(self) -> list[FileRegistryEntry]:
        """Parse all file registry table rows (multiple subsections merged)."""
        entries: list[FileRegistryEntry] = []
        # Match all markdown table rows with a [filename](link) cell
        for m in re.finditer(r"\|\s*\[([^\]]+)\]\([^\)]+\)\s*\|[^|]*\|[^|]*\|\s*(✅[^|]*)\|", self.text):
            filename = m.group(1).strip()
            status_cell = m.group(2).strip()
            if "Complete" in status_cell:
                status = "Complete"
            elif "Active" in status_cell:
                status = "Active"
            elif "Source" in status_cell:
                status = "Source"
            elif "Superseded" in status_cell:
                status = "Superseded"
            else:
                status = status_cell[:20]
            entries.append(FileRegistryEntry(filename=filename, signal="", status=status))
        return entries

    def build_patches(self, completed_ids: set[str]) -> list[tuple[str, str]]:
        """
        Generate (old_line, new_line) patches for Priority Queue rows whose
        task_clean matches a completed ID but are not yet struck through.
        """
        patches = []
        items = self.extract_priority_queue()
        for item in items:
            if item.id in completed_ids and not item.done:
                # Add strikethrough to the task cell
                new_task = f"~~{item.task_clean}~~"
                old_row_pattern = re.compile(
                    r"(\|\s*" + re.escape(item.id) + r"\s*\|\s*)" + re.escape(item.task) + r"(\s*\|)"
                )
                new_row = lambda m, nt=new_task: m.group(1) + nt + m.group(2)
                patched = old_row_pattern.sub(new_row, self.text)
                if patched != self.text:
                    # Record hunk as (old_text_segment, new_text_segment) — use full file
                    patches.append((self.text, patched))
        return patches

    def sync(self, git_completed: set[str]) -> MetaSyncResult:
        result = MetaSyncResult(path=self.path, handler_type=self.HANDLER_TYPE)
        result.pipeline_steps = self.extract_pipeline_state()
        result.queue_items = self.extract_priority_queue()
        result.file_registry = self.extract_file_registry()

        # Find queue items that git says are done but META has not crossed out
        for item in result.queue_items:
            if item.id in git_completed and not item.done:
                result.errors.append(
                    f"SYNC GAP: {item.id} completed in git (Pentea-Completed trailer) "
                    f"but not marked done in META. Task: '{item.task_clean}'"
                )
                # Generate patch hunk
                patches = self.build_patches({item.id})
                result.patch_hunks.extend(patches)

        return result


# ─────────────────────────────────────────────────────────────────────────────
# ANKH Synthesis META handler
# ─────────────────────────────────────────────────────────────────────────────

class AnkhSynthesisMetaHandler:
    """
    Handles ANKH_SYNTHESIS_META.md style documents.
    Sections parsed:
      - Corpus File Inventory (Baselined Files table)
      - Declared Gaps table
    Uses lend() to borrow file_registry extraction logic from MilfCoreMetaHandler.
    """

    HANDLER_TYPE = "ankh-synthesis"

    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")

    def extract_declared_gaps(self) -> list[DeclaredGap]:
        """Parse the Declared Gaps table."""
        gaps: list[DeclaredGap] = []
        m = re.search(r"###\s+Declared\s+Gaps.*?\n(.*?)(?:\n---|\n##|\Z)", self.text, re.DOTALL)
        if not m:
            return gaps
        block = m.group(1)
        for row in re.finditer(r"\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(~~.*?~~|.*?)\s*\|", block):
            gap_raw = row.group(1).strip()
            notes = row.group(3).strip()
            severity_raw = row.group(4).strip()
            if gap_raw.lower() in ("gap", "---"):
                continue
            closed = "CLOSED" in notes or "✅" in severity_raw or "~~" in gap_raw
            gap_clean = re.sub(r"~~(.+?)~~", r"\1", gap_raw).strip()
            severity_clean = re.sub(r"~~(.+?)~~", r"\1", severity_raw).strip()
            gaps.append(DeclaredGap(
                gap=gap_raw, gap_clean=gap_clean,
                closed=closed, severity=severity_clean
            ))
        return gaps

    def extract_corpus_inventory(self) -> list[FileRegistryEntry]:
        """
        Parse Corpus File Inventory (Baselined Files table).
        Borrows file_registry logic from MilfCoreMetaHandler via lend().
        """
        milf_dummy = MilfCoreMetaHandler.__new__(MilfCoreMetaHandler)
        milf_dummy.text = self.text

        # MLRSP lend: borrow extract_file_registry from MilfCoreMetaHandler
        borrowed_fn = lend("extract_file_registry", milf_dummy, self, duration="temporary")
        return borrowed_fn()

    def sync(self, git_completed: set[str]) -> MetaSyncResult:  # noqa: ARG002
        result = MetaSyncResult(path=self.path, handler_type=self.HANDLER_TYPE)
        result.declared_gaps = self.extract_declared_gaps()
        result.file_registry = self.extract_corpus_inventory()

        # Check: any open gaps that have a corresponding closed indicator missed?
        for gap in result.declared_gaps:
            if not gap.closed:
                # Gaps that are not closed are just pending — not an error
                pass

        return result


# ─────────────────────────────────────────────────────────────────────────────
# Generic fallback handler
# ─────────────────────────────────────────────────────────────────────────────

class GenericMetaHandler:
    """
    Fallback for META files with unrecognized structure.
    Extracts any markdown table with a Status column.
    Also borrows pipeline_state extraction from MilfCoreMetaHandler via lend().
    """

    HANDLER_TYPE = "generic"

    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")

    def extract_pipeline_state(self, text: Optional[str] = None) -> list[PipelineStep]:
        milf_dummy = MilfCoreMetaHandler.__new__(MilfCoreMetaHandler)
        milf_dummy.text = text if text is not None else self.text
        borrowed_fn = lend("extract_pipeline_state", milf_dummy, self, duration="temporary")
        return borrowed_fn()

    def sync(self, git_completed: set[str]) -> MetaSyncResult:  # noqa: ARG002
        result = MetaSyncResult(path=self.path, handler_type=self.HANDLER_TYPE)
        result.pipeline_steps = self.extract_pipeline_state()
        return result


# ─────────────────────────────────────────────────────────────────────────────
# META discovery + handler routing
# ─────────────────────────────────────────────────────────────────────────────

# Directories whose subtrees should never be walked for META files.
# Covers: build outputs, package caches, language module trees,
# Ruby gem dirs, Python venvs, JS/TS node_modules, vendor trees.
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
    "registry",          # cargo registry cache under target/
    # Generic vendor / third-party
    "vendor", "third_party", "third-party",
    # Archive-specific noise
    "dumpster-dive", ".deprecated", "artifacts",
}

# ─────────────────────────────────────────────────────────────────────────────
# Discovery cache — stored in .git/ so it is never committed
# ─────────────────────────────────────────────────────────────────────────────

_CACHE_PATH = REPO_ROOT / ".git" / "meta_sync_cache.json"


def _load_cache(repo: Path) -> list[Path] | None:
    """
    Return cached META file paths if every entry still exists with the same
    mtime. Returns None if the cache is absent, stale, or corrupt.
    """
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        entries = data["files"]          # [{"path": str, "mtime": float}, ...]
        paths: list[Path] = []
        for e in entries:
            p = repo / e["path"]
            if not p.exists():
                return None             # file was deleted — cache is stale
            if abs(p.stat().st_mtime - e["mtime"]) > 0.01:
                return None             # mtime changed — cache is stale
            paths.append(p)
        return paths
    except Exception:                   # malformed JSON or missing keys
        return None


def _save_cache(repo: Path, paths: list[Path]) -> None:
    """Persist the discovered file list + their mtimes to .git/meta_sync_cache.json."""
    try:
        entries = [
            {"path": str(p.relative_to(repo)), "mtime": p.stat().st_mtime}
            for p in paths
        ]
        _CACHE_PATH.write_text(
            json.dumps({"generated_at": _now_local(), "files": entries}, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass                            # non-fatal — next run will re-walk


def discover_meta_files(repo: Path, use_cache: bool = True) -> list[Path]:
    """
    Find all files matching *META*.md in the repo, excluding noise dirs.

    On first run (or when --no-cache is passed) performs a full rglob walk
    and saves results to .git/meta_sync_cache.json.  Subsequent runs load
    the cache and skip the walk if every entry is still valid (mtime match).
    Cache is invalidated automatically when any file is added, removed, or
    modified.
    """
    if use_cache:
        cached = _load_cache(repo)
        if cached is not None:
            return sorted(cached)

    found: list[Path] = []
    for p in repo.rglob("*META*.md"):
        parts = set(p.relative_to(repo).parts)
        if parts & _IGNORE_DIRS:
            continue
        found.append(p)

    found = sorted(found)
    _save_cache(repo, found)
    return found


def _handler_for(path: Path) -> MilfCoreMetaHandler | AnkhSynthesisMetaHandler | GenericMetaHandler:
    name = path.name
    if "MILF-Core-META" in name:
        return MilfCoreMetaHandler(path)
    if "ANKH_SYNTHESIS_META" in name or "ANKH-SYNTHESIS-META" in name:
        return AnkhSynthesisMetaHandler(path)
    return GenericMetaHandler(path)


# ─────────────────────────────────────────────────────────────────────────────
# Apply patches
# ─────────────────────────────────────────────────────────────────────────────

def apply_patches(result: MetaSyncResult) -> bool:
    """Write patched content back to file. Returns True if any change was made."""
    if not result.patch_hunks:
        return False
    # Patches are (old_full_text, new_full_text) — apply last one (sequential)
    _, new_text = result.patch_hunks[-1]
    result.path.write_text(new_text, encoding="utf-8")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

def _status_color(status: str) -> str:
    if status in ("done", "Complete", "Active", "Source"):
        return "green"
    if status in ("unblocked",):
        return "yellow"
    return "red" if "ERROR" in status.upper() else "dim"


def report_rich(results: list[MetaSyncResult], console: "Console") -> None:
    console.print(f"[dim]meta_sync  {_now_local()}[/]\n")
    for r in results:
        rel = r.path.relative_to(REPO_ROOT)
        title = f"[bold gold1]{r.handler_type.upper()}[/] — [cyan]{rel}[/]"
        console.print(Panel(title, expand=False))

        if r.pipeline_steps:
            t = Table("Step", "Description", "Status", "Ref", show_header=True, header_style="bold")
            for s in r.pipeline_steps:
                color = _status_color(s.status)
                t.add_row(s.label, s.description[:60], f"[{color}]{s.status}[/]", s.ref[:30])
            console.print(t)

        if r.queue_items:
            t = Table("ID", "Task", "Done", "Commit", "Notes", show_header=True, header_style="bold")
            for q in r.queue_items:
                done_str = "[green]✅[/]" if q.done else "[dim]⬜[/]"
                t.add_row(q.id, q.task_clean[:50], done_str, q.commit_ref, q.notes[:40])
            console.print(t)

        if r.declared_gaps:
            t = Table("Gap", "Closed", "Severity", show_header=True, header_style="bold")
            for g in r.declared_gaps:
                closed_str = "[green]✅[/]" if g.closed else "[dim]⬜[/]"
                t.add_row(g.gap_clean[:60], closed_str, g.severity[:20])
            console.print(t)

        if r.file_registry:
            t = Table("File", "Status", show_header=True, header_style="bold")
            for e in r.file_registry:
                color = _status_color(e.status)
                t.add_row(e.filename[:60], f"[{color}]{e.status}[/]")
            console.print(t)

        if r.errors:
            for err in r.errors:
                console.print(f"  [bold red]⚠  {err}[/]")
        else:
            console.print("  [green]✓ No sync gaps detected[/]")

        if r.patch_hunks:
            console.print(f"  [yellow]→ {len(r.patch_hunks)} patch hunk(s) available (run with --patch to apply)[/]")

        console.print()


def report_plain(results: list[MetaSyncResult], out) -> None:
    out.write(f"meta_sync  {_now_local()}\n")
    for r in results:
        rel = r.path.relative_to(REPO_ROOT)
        out.write(f"\n=== {r.handler_type.upper()} | {rel} ===\n")
        for s in r.pipeline_steps:
            mark = "✅" if s.status == "done" else ("→" if s.status == "unblocked" else "⬜")
            out.write(f"  {mark} {s.label}: {s.description[:60]}\n")
        for q in r.queue_items:
            mark = "✅" if q.done else "⬜"
            out.write(f"  {mark} {q.id}: {q.task_clean[:50]}\n")
        for g in r.declared_gaps:
            mark = "✅" if g.closed else "⬜"
            out.write(f"  {mark} GAP: {g.gap_clean[:60]}\n")
        for err in r.errors:
            out.write(f"  ⚠  {err}\n")


def report_json(results: list[MetaSyncResult], out) -> None:
    payload = []
    _ts = _now_local()
    for r in results:
        payload.append({
            "file": str(r.path.relative_to(REPO_ROOT)),
            "handler": r.handler_type,
            "pipeline_steps": [
                {"label": s.label, "description": s.description, "status": s.status, "ref": s.ref}
                for s in r.pipeline_steps
            ],
            "queue_items": [
                {"id": q.id, "task": q.task_clean, "done": q.done, "commit_ref": q.commit_ref}
                for q in r.queue_items
            ],
            "declared_gaps": [
                {"gap": g.gap_clean, "closed": g.closed, "severity": g.severity}
                for g in r.declared_gaps
            ],
            "file_registry_count": len(r.file_registry),
            "sync_errors": r.errors,
            "patch_available": len(r.patch_hunks) > 0,
        })
    json.dump({"scanned_at": _ts, "results": payload}, out, indent=2, ensure_ascii=False)
    out.write("\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="META registry sync — cross-archive pipeline state + priority queue checker",
        epilog="MLRSP lend() used internally: MilfCoreMetaHandler capabilities lend to AnkhSynthesisMetaHandler and GenericMetaHandler.",
    )
    ap.add_argument("--patch", action="store_true",
                    help="Apply ~~strikethrough~~ patches to Priority Queue items confirmed done in git")
    ap.add_argument("--report", metavar="FILE",
                    help="Write report to FILE (default: stdout)")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON output")
    ap.add_argument("--strict", action="store_true",
                    help="Exit code 1 if any sync gaps found")
    ap.add_argument("--meta", metavar="FILE",
                    help="Process a single META file instead of auto-discovering")
    ap.add_argument("--no-cache", action="store_true",
                    help="Force a full filesystem walk, ignoring the .git/meta_sync_cache.json cache")
    args = ap.parse_args()

    # Discover META files
    if args.meta:
        meta_files = [Path(args.meta).resolve()]
    else:
        meta_files = discover_meta_files(REPO_ROOT, use_cache=not args.no_cache)

    if not meta_files:
        sys.stderr.write("meta_sync: no META files found\n")
        return 0

    # Git state
    git_completed = _git_completed_trailers(REPO_ROOT)

    # Process each META file
    results: list[MetaSyncResult] = []
    patched_files: list[Path] = []

    for mf in meta_files:
        try:
            handler = _handler_for(mf)
            result = handler.sync(git_completed)
            results.append(result)

            if args.patch and result.patch_hunks:
                if apply_patches(result):
                    patched_files.append(mf)
        except Exception as exc:
            r = MetaSyncResult(path=mf, handler_type="error")
            r.errors.append(f"Handler error: {exc}")
            results.append(r)

    # Report
    out_file = open(args.report, "w", encoding="utf-8") if args.report else None
    out = out_file or sys.stdout

    try:
        if args.json:
            report_json(results, out)
        elif _RICH and out is sys.stdout:
            report_rich(results, CONSOLE)
        else:
            report_plain(results, out)
    finally:
        if out_file:
            out_file.close()

    if patched_files:
        sys.stderr.write(f"meta_sync: patched {len(patched_files)} file(s):\n")
        for p in patched_files:
            sys.stderr.write(f"  {p.relative_to(REPO_ROOT)}\n")

    # Summary line
    total_errors = sum(len(r.errors) for r in results)
    total_gaps = sum(len(r.patch_hunks) for r in results)
    sys.stderr.write(
        f"meta_sync: {len(results)} META file(s) scanned | "
        f"{total_errors} sync error(s) | "
        f"{total_gaps} patch hunk(s) {'applied' if args.patch else 'available'}\n"
    )

    if args.strict and total_errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
