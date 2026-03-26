#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: zombie_forge_bridge.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Zombie Forge Bridge — routes zombie extract files to forge stages.

The bridge sits BETWEEN zombie_consumer.py (upstream) and the forge (downstream).
It reads .zombie_extract_*.json files from forge/intake/ (primary) and
dumpster-dive/intake/ (legacy fallback), maps ore_rating → forge stage,
copies the companion consumed files there, and writes forge receipts + registry entries.

This closes the forge feedback loop: after routing, `zombie learn` can scan the
forge stages and match files by filename to backpropagate ore predictions.

Routing table:
    ore_rating 5  →  forge/quench/   (fast-track — high value)
    ore_rating 4  →  forge/anvil/    (deep analysis)
    ore_rating 3  →  forge/furnace/  (heat refinement)
    ore_rating 2  →  forge/slag/     (discard candidate)
    ore_rating 1  →  forge/slag/     (+ upcycle_pending flag)
    signals: superposition  →  forge/tea-vault/  (timeline-entangled)

Usage:
    uv run scripts/zombie_forge_bridge.py route --dry-run
    uv run scripts/zombie_forge_bridge.py route
    uv run scripts/zombie_forge_bridge.py route --batch scripts-restructure-2026-03-20
    uv run scripts/zombie_forge_bridge.py route --json
    uv run scripts/zombie_forge_bridge.py status
    uv run scripts/zombie_forge_bridge.py status --json

@SID:           TOOL_ZOMBIE_FORGE_BRIDGE_V1
@Shabti:        CLI Script
@Purpose:       Zombie Forge Bridge — routes zombie extract files to forge stages.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Repo root + constants (mirrors zombie_consumer.py)
# ---------------------------------------------------------------------------

def find_repo_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    for p in [cur, *cur.parents]:
        if (p / "AGENTS.md").exists() and (p / "pyproject.toml").exists():
            return p
    return Path.cwd()


ROOT           = find_repo_root()
INTAKE_PRIMARY = ROOT / "dumpster-dive" / "forge" / "intake"
INTAKE_LEGACY  = ROOT / "dumpster-dive" / "intake"
INTAKE         = INTAKE_PRIMARY  # default for callers expecting single path
FORGE          = ROOT / "dumpster-dive" / "forge"
REGISTRY_PATH  = FORGE / "PATHWAY_REGISTRY.json"

FORGE_STAGES: dict[str, Path] = {
    "quench":    FORGE / "quench",
    "anvil":     FORGE / "anvil",
    "furnace":   FORGE / "furnace",
    "slag":      FORGE / "slag",
    "tempered":  FORGE / "tempered",
    "tea-vault": FORGE / "tea-vault",
}

# ore_rating → forge stage (default routing, no superposition)
ORE_TO_STAGE: dict[int, str] = {
    5: "quench",
    4: "anvil",
    3: "furnace",
    2: "slag",
    1: "slag",
}


# ---------------------------------------------------------------------------
# Helpers (mirrors zombie_consumer.py style)
# ---------------------------------------------------------------------------

def safe_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


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


# ---------------------------------------------------------------------------
# Registry — append-only PATHWAY_REGISTRY.json
# ---------------------------------------------------------------------------

def load_registry() -> list[dict]:
    if not REGISTRY_PATH.exists():
        return []
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_registry(entries: list[dict]) -> None:
    REGISTRY_PATH.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Idempotency — track routed content_hashes by scanning existing receipts
# ---------------------------------------------------------------------------

def load_routed_hashes() -> set[str]:
    """Return set of content_hashes that have already been routed to any forge stage."""
    seen: set[str] = set()
    for stage_dir in FORGE_STAGES.values():
        if not stage_dir.exists():
            continue
        for receipt_path in stage_dir.glob(".forge_receipt_*.json"):
            try:
                data = json.loads(receipt_path.read_text(encoding="utf-8"))
                h = data.get("content_hash")
                if h:
                    seen.add(h)
            except Exception:
                pass
    return seen


# ---------------------------------------------------------------------------
# EMBALM provenance sidecar (future-proof integration)
# ---------------------------------------------------------------------------

def _find_provenance_sidecar(intake_dir: Path, companion_name: str) -> dict | None:
    """Load EMBALM provenance sidecar data for a companion file, if it exists."""
    stem = Path(companion_name).stem
    candidates = [
        intake_dir / f".embalm_provenance_{companion_name}.json",
        intake_dir / f".embalm_provenance_{stem}.json",
        intake_dir / f"{stem}.provenance.json",
    ]
    for c in candidates:
        if c.exists():
            try:
                return json.loads(c.read_text(encoding="utf-8"))
            except Exception:
                continue
    return None


def _count_all_extracts() -> int:
    """Count zombie extracts across primary and legacy intake paths."""
    count = 0
    for intake_dir in [INTAKE_PRIMARY, INTAKE_LEGACY]:
        if intake_dir.exists():
            count += sum(1 for _ in intake_dir.rglob(".zombie_extract_*.json"))
    return count


# ---------------------------------------------------------------------------
# Extract scanning
# ---------------------------------------------------------------------------

def scan_extracts(batch_filter: str | None = None) -> Iterator[tuple[Path, dict]]:
    """Yield (extract_path, extract_data) for all zombie extracts.

    Scans INTAKE_PRIMARY (forge/intake/) first, then INTAKE_LEGACY
    (dumpster-dive/intake/) for backward compatibility.

    If batch_filter is given, only yield extracts whose relative path contains
    batch_filter as a path component name.
    """
    seen_hashes: set[str] = set()
    for intake_dir in [INTAKE_PRIMARY, INTAKE_LEGACY]:
        if not intake_dir.exists():
            continue
        is_legacy = intake_dir == INTAKE_LEGACY
        for extract_path in sorted(intake_dir.rglob(".zombie_extract_*.json")):
            if batch_filter:
                rel = safe_relative(extract_path)
                if batch_filter not in rel:
                    continue
            try:
                data = json.loads(extract_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            # Deduplicate across primary/legacy by content_hash
            content_hash = data.get("content_hash", "")
            if content_hash and content_hash in seen_hashes:
                continue
            if content_hash:
                seen_hashes.add(content_hash)
            if is_legacy:
                data["_legacy_intake"] = True
            yield extract_path, data


# ---------------------------------------------------------------------------
# Core routing logic
# ---------------------------------------------------------------------------

def _resolve_stage(ore_rating: int, signals: list[str]) -> str:
    """Map ore_rating + signals to a forge stage name."""
    if "superposition" in signals:
        return "tea-vault"
    return ORE_TO_STAGE.get(ore_rating, "slag")


def route_file(
    extract_path: Path,
    extract_data: dict,
    routed_hashes: set[str],
    dry_run: bool = False,
) -> dict:
    """Route one extract's companion file to the appropriate forge stage.

    Returns a result dict describing the action taken (or would-be action).
    Updates routed_hashes in-place on successful route for same-run idempotency.
    """
    source       = extract_data.get("source", "")
    ore_rating   = int(extract_data.get("ore_rating", 1))
    category     = extract_data.get("category", "unknown")
    content_hash = extract_data.get("content_hash", "")
    signals      = extract_data.get("signals", [])

    # Idempotency check
    if content_hash and content_hash in routed_hashes:
        return {
            "status":       "already_routed",
            "source":       source,
            "content_hash": content_hash,
        }

    # Locate companion consumed file: same dir as extract, name from source field
    intake_dir     = extract_path.parent
    companion_name = Path(source).name
    companion_path = intake_dir / companion_name

    if not companion_path.exists():
        return {
            "status":   "companion_missing",
            "source":   source,
            "extract":  safe_relative(extract_path),
            "expected": safe_relative(companion_path),
        }

    stage     = _resolve_stage(ore_rating, signals)
    stage_dir = FORGE_STAGES.get(stage)
    if stage_dir is None:
        return {"status": "error", "reason": f"unknown stage: {stage}", "source": source}

    target_path     = stage_dir / companion_name
    receipt_path    = stage_dir / f".forge_receipt_{companion_name}.json"
    upcycle_pending = ore_rating == 1

    if dry_run:
        return {
            "status":          "dry_run",
            "source":          source,
            "companion":       safe_relative(companion_path),
            "stage":           stage,
            "target":          safe_relative(target_path),
            "ore_rating":      ore_rating,
            "category":        category,
            "upcycle_pending": upcycle_pending,
        }

    # Copy companion to forge stage (non-destructive — intake copy preserved)
    stage_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(companion_path), str(target_path))

    # EMBALM provenance sidecar (parsed data or null)
    provenance_data = _find_provenance_sidecar(intake_dir, companion_name)

    # Write forge receipt sidecar
    receipt: dict = {
        "source_extract":    safe_relative(extract_path),
        "routed_from":       safe_relative(companion_path),
        "routed_to":         safe_relative(target_path),
        "ore_rating":        ore_rating,
        "category":          category,
        "content_hash":      content_hash,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "sha256":     provenance_data.get("hash"),
            "source_file": provenance_data.get("source_file"),
            "git_head":   provenance_data.get("commit") or provenance_data.get("head_commit"),
            "snapshot_at": provenance_data.get("date") or provenance_data.get("snapshot_at"),
            "language":   provenance_data.get("language"),
        } if provenance_data else None,
    }
    if upcycle_pending:
        receipt["upcycle_pending"] = True
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    # Register in routed_hashes for downstream idempotency within the same run
    if content_hash:
        routed_hashes.add(content_hash)

    # Append to PATHWAY_REGISTRY.json (append-only)
    companion_suffix = Path(companion_name).suffix or companion_name
    registry = load_registry()
    entry: dict = {
        "input_type": companion_suffix,
        "output_type": ".json",
        "pathway": "zombie extract -> ore routing -> forge stage",
        "path": safe_relative(target_path),
        "novel": True,
        "provenance": {
            "sha256":     provenance_data.get("hash"),
            "source_file": provenance_data.get("source_file"),
            "git_head":   provenance_data.get("commit") or provenance_data.get("head_commit"),
            "snapshot_at": provenance_data.get("date") or provenance_data.get("snapshot_at"),
            "language":   provenance_data.get("language"),
        } if provenance_data else None,
    }
    registry.append(entry)
    save_registry(registry)

    return {
        "status":          "routed",
        "source":          source,
        "companion":       safe_relative(companion_path),
        "stage":           stage,
        "target":          safe_relative(target_path),
        "ore_rating":      ore_rating,
        "category":        category,
        "content_hash":    content_hash,
        "upcycle_pending": upcycle_pending,
    }


# ---------------------------------------------------------------------------
# Rich rendering
# ---------------------------------------------------------------------------

def _render_route_results(results: list[dict], dry_run: bool) -> None:
    from rich.panel import Panel
    from rich.table import Table

    console = _get_console()
    title   = "[bold]FORGE BRIDGE — DRY RUN[/bold]" if dry_run else "[bold]FORGE BRIDGE — ROUTED[/bold]"

    table = Table(title=None, box=None, show_header=True)
    table.add_column("Status",   style="bold")
    table.add_column("Ore")
    table.add_column("File",     style="dim")
    table.add_column("Stage")
    table.add_column("Category")

    routed    = 0
    dry_count = 0
    skipped   = 0
    errors    = 0

    for r in results:
        status = r.get("status", "?")
        if status == "routed":
            color  = "green"
            routed += 1
        elif status == "dry_run":
            color     = "yellow"
            dry_count += 1
        elif status == "already_routed":
            color   = "dim"
            skipped += 1
        else:
            color  = "red"
            errors += 1

        ore      = r.get("ore_rating")
        ore_str  = _ore_bar(ore) if ore is not None else "[dim]?[/dim]"
        filename = Path(r.get("source", "?")).name
        stage    = r.get("stage", r.get("status", "?"))
        category = r.get("category", "?")

        table.add_row(
            f"[{color}]{status}[/{color}]",
            ore_str,
            filename,
            stage,
            category,
        )

    if dry_run:
        summary = (
            f"[yellow]{dry_count} files would be routed[/yellow]  "
            f"[dim]{skipped} already done[/dim]  "
            f"[red]{errors} errors[/red]"
        )
    else:
        summary = (
            f"[green]{routed} routed[/green]  "
            f"[dim]{skipped} already done[/dim]  "
            f"[red]{errors} errors[/red]"
        )

    console.print(Panel(table, title=title, border_style="dim"))
    console.print(summary)


def _render_status() -> None:
    from rich.panel import Panel
    from rich.table import Table

    console = _get_console()

    table = Table(title=None, box=None, show_header=True)
    table.add_column("Stage",    style="bold cyan")
    table.add_column("Files",    justify="right")
    table.add_column("Receipts", justify="right")

    total_files    = 0
    total_receipts = 0

    for stage_name, stage_dir in sorted(FORGE_STAGES.items()):
        if not stage_dir.exists():
            table.add_row(stage_name, "[dim]0[/dim]", "[dim]0[/dim]")
            continue
        files    = [f for f in stage_dir.iterdir() if not f.name.startswith(".")]
        receipts = list(stage_dir.glob(".forge_receipt_*.json"))
        total_files    += len(files)
        total_receipts += len(receipts)
        table.add_row(
            stage_name,
            str(len(files))    if files    else "[dim]0[/dim]",
            str(len(receipts)) if receipts else "[dim]0[/dim]",
        )

    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", str(total_files), str(total_receipts))

    extract_count = _count_all_extracts()
    routed_count  = len(load_routed_hashes())
    unrouted      = extract_count - routed_count

    console.print(Panel(table, title="[bold]FORGE STATUS[/bold]", border_style="dim"))
    console.print(
        f"Intake extracts: [bold]{extract_count}[/bold]  |  "
        f"Routed: [green]{routed_count}[/green]  |  "
        f"Unrouted: [yellow]{unrouted}[/yellow]"
    )


def _status_json() -> dict:
    data: dict[str, dict] = {}
    for stage_name, stage_dir in FORGE_STAGES.items():
        if not stage_dir.exists():
            data[stage_name] = {"files": 0, "receipts": 0}
            continue
        files    = [f for f in stage_dir.iterdir() if not f.name.startswith(".")]
        receipts = list(stage_dir.glob(".forge_receipt_*.json"))
        data[stage_name] = {"files": len(files), "receipts": len(receipts)}
    extract_count = _count_all_extracts()
    routed_count  = len(load_routed_hashes())
    data["_summary"] = {
        "intake_extracts": extract_count,
        "routed":          routed_count,
        "unrouted":        extract_count - routed_count,
    }
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zombie Forge Bridge — routes zombie extract files to forge stages."
    )
    sub = parser.add_subparsers(dest="command")

    p_route = sub.add_parser("route", help="Route zombie extracts to forge stages")
    p_route.add_argument(
        "--dry-run", action="store_true",
        help="Preview routing without copying files or writing receipts",
    )
    p_route.add_argument(
        "--batch", type=str, default=None, metavar="NAME",
        help="Restrict routing to extracts under a named batch subdirectory",
    )
    p_route.add_argument("--json", action="store_true", help="JSON output")

    p_status = sub.add_parser("status", help="Show forge stage file and receipt counts")
    p_status.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "route":
        routed_hashes = load_routed_hashes()
        results: list[dict] = []
        for extract_path, extract_data in scan_extracts(batch_filter=args.batch):
            result = route_file(
                extract_path, extract_data, routed_hashes, dry_run=args.dry_run
            )
            results.append(result)
        if getattr(args, "json", False):
            print(json.dumps(results, indent=2))
        else:
            _render_route_results(results, dry_run=args.dry_run)
        return 0

    if args.command == "status":
        if getattr(args, "json", False):
            print(json.dumps(_status_json(), indent=2))
        else:
            _render_status()
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
