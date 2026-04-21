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


def ensure_forge_dirs() -> None:
    """Create FORGE root + all stage directories if they do not exist."""
    FORGE.mkdir(parents=True, exist_ok=True)
    for stage_dir in FORGE_STAGES.values():
        stage_dir.mkdir(parents=True, exist_ok=True)

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


def _stage_target_name(companion_name: str, content_hash: str) -> str:
    if not content_hash:
        return companion_name
    p = Path(companion_name)
    return f"{p.stem}_{content_hash[:8]}{p.suffix}" if p.suffix else f"{companion_name}_{content_hash[:8]}"


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
        compact_manifest = stage_dir / ".forge_compact_manifest.json"
        if compact_manifest.exists():
            try:
                manifest = json.loads(compact_manifest.read_text(encoding="utf-8"))
                for record in manifest.get("receipts", []):
                    payload = record.get("payload", {})
                    h = payload.get("content_hash")
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


def _extract_provenance(extract_data: dict, intake_dir: Path, companion_name: str) -> dict | None:
    """Prefer inline bride provenance; fall back to legacy sidecar lookup."""
    provenance = extract_data.get("provenance")
    if isinstance(provenance, dict) and provenance:
        return provenance
    return _find_provenance_sidecar(intake_dir, companion_name)


def _provenance_payload(provenance_data: dict | None) -> dict | None:
    if not provenance_data:
        return None
    return {
        "sha256": provenance_data.get("hash") or provenance_data.get("content_hash"),
        "source_file": provenance_data.get("source_file"),
        "git_head": provenance_data.get("commit") or provenance_data.get("head_commit"),
        "snapshot_at": provenance_data.get("date") or provenance_data.get("snapshot_at"),
        "language": provenance_data.get("language"),
    }


def _count_all_extracts() -> int:
    """Count zombie extracts across primary and legacy intake paths."""
    count = 0
    for intake_dir in [INTAKE_PRIMARY, INTAKE_LEGACY]:
        if intake_dir.exists():
            count += sum(1 for _ in intake_dir.rglob(".zombie_extract_*.json"))
    return count


def _route_backlog_summary() -> dict:
    """Summarize actionable routing backlog after content-hash deduplication."""
    routed_hashes = load_routed_hashes()
    actionable = 0
    already = 0
    missing = 0
    errors = 0
    total_candidates = 0
    for extract_path, extract_data in scan_extracts():
        total_candidates += 1
        result = route_file(extract_path, extract_data, set(routed_hashes), dry_run=True)
        status = result.get("status")
        if status == "dry_run":
            actionable += 1
        elif status == "already_routed":
            already += 1
        elif status == "companion_missing":
            missing += 1
        else:
            errors += 1
    return {
        "intake_extract_files": _count_all_extracts(),
        "route_candidates": total_candidates,
        "already_routed": already,
        "actionable_unrouted": actionable,
        "companion_missing": missing,
        "errors": errors,
    }


def _find_receipt_metadata(extract_path: Path) -> dict | None:
    """Recover companion destination from the sibling zombie receipt when available."""
    name = extract_path.name
    if not name.startswith(".zombie_extract_"):
        return None
    receipt_name = name.replace(".zombie_extract_", ".zombie_receipt_", 1)
    receipt_path = extract_path.with_name(receipt_name)
    if not receipt_path.exists():
        return None
    try:
        return json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        return None


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
        for manifest_path in sorted(intake_dir.rglob(".zombie_compact_manifest.json")):
            if batch_filter:
                rel = safe_relative(manifest_path)
                if batch_filter not in rel:
                    continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            receipts_by_name: dict[str, dict] = {}
            for record in manifest.get("receipts", []):
                receipts_by_name[record.get("name", "")] = record.get("payload", {})
            for record in manifest.get("extracts", []):
                data = dict(record.get("payload", {}))
                if not data:
                    continue
                content_hash = data.get("content_hash", "")
                if content_hash and content_hash in seen_hashes:
                    continue
                if content_hash:
                    seen_hashes.add(content_hash)
                extract_name = record.get("name", "")
                receipt_name = extract_name.replace(".zombie_extract_", ".zombie_receipt_", 1)
                receipt_payload = receipts_by_name.get(receipt_name, {})
                if receipt_payload and not data.get("intake_destination"):
                    destination = str(receipt_payload.get("destination", "")).replace("\\", "/")
                    if destination:
                        data["intake_destination"] = destination
                        data["intake_companion"] = Path(destination).name
                        data["batch"] = receipt_payload.get("batch", data.get("batch"))
                if is_legacy:
                    data["_legacy_intake"] = True
                synthetic_path = manifest_path.with_name(extract_name or manifest_path.name)
                yield synthetic_path, data


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

    # Locate companion consumed file from canonical intake metadata when present.
    intake_dir         = extract_path.parent
    receipt_data       = _find_receipt_metadata(extract_path)
    intake_destination = extract_data.get("intake_destination")
    if receipt_data and receipt_data.get("destination"):
        intake_destination = str(receipt_data["destination"]).replace("\\", "/")
    companion_name     = extract_data.get("intake_companion") or Path(source).name
    if receipt_data and receipt_data.get("destination"):
        companion_name = Path(str(receipt_data["destination"])).name
    companion_path     = intake_dir / companion_name

    if intake_destination:
        resolved_destination = ROOT / Path(str(intake_destination))
        if resolved_destination.exists():
            companion_path = resolved_destination
            companion_name = resolved_destination.name

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

    target_name     = companion_name
    if (stage_dir / target_name).exists():
        target_name = _stage_target_name(companion_name, content_hash)
    target_path     = stage_dir / target_name
    receipt_path    = stage_dir / f".forge_receipt_{target_name}.json"
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
    provenance_data = _extract_provenance(extract_data, intake_dir, companion_name)

    # Write forge receipt sidecar
    provenance_payload = _provenance_payload(provenance_data)

    receipt: dict = {
        "source_extract":    safe_relative(extract_path),
        "routed_from":       safe_relative(companion_path),
        "routed_to":         safe_relative(target_path),
        "ore_rating":        ore_rating,
        "category":          category,
        "content_hash":      content_hash,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "provenance": provenance_payload,
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
        "provenance": provenance_payload,
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
    table.add_column("Compact",  justify="right")

    total_files    = 0
    total_receipts = 0
    total_compact  = 0

    for stage_name, stage_dir in sorted(FORGE_STAGES.items()):
        if not stage_dir.exists():
            table.add_row(stage_name, "[dim]0[/dim]", "[dim]0[/dim]", "[dim]0[/dim]")
            continue
        files    = [f for f in stage_dir.iterdir() if not f.name.startswith(".")]
        receipts = list(stage_dir.glob(".forge_receipt_*.json"))
        compact_manifest = stage_dir / ".forge_compact_manifest.json"
        compact_count = 1 if compact_manifest.exists() else 0
        total_files    += len(files)
        total_receipts += len(receipts)
        total_compact  += compact_count
        table.add_row(
            stage_name,
            str(len(files))    if files    else "[dim]0[/dim]",
            str(len(receipts)) if receipts else "[dim]0[/dim]",
            str(compact_count) if compact_count else "[dim]0[/dim]",
        )

    table.add_section()
    table.add_row("[bold]TOTAL[/bold]", str(total_files), str(total_receipts), str(total_compact))

    backlog = _route_backlog_summary()

    console.print(Panel(table, title="[bold]FORGE STATUS[/bold]", border_style="dim"))
    console.print(
        f"Intake extract files: [bold]{backlog['intake_extract_files']}[/bold]  |  "
        f"Route candidates: [bold]{backlog['route_candidates']}[/bold]  |  "
        f"Already routed: [green]{backlog['already_routed']}[/green]  |  "
        f"Actionable unrouted: [yellow]{backlog['actionable_unrouted']}[/yellow]"
    )


def _status_json() -> dict:
    data: dict[str, dict] = {}
    for stage_name, stage_dir in FORGE_STAGES.items():
        if not stage_dir.exists():
            data[stage_name] = {"files": 0, "receipts": 0, "compact_manifests": 0}
            continue
        files    = [f for f in stage_dir.iterdir() if not f.name.startswith(".")]
        receipts = list(stage_dir.glob(".forge_receipt_*.json"))
        compact_manifest = stage_dir / ".forge_compact_manifest.json"
        data[stage_name] = {
            "files": len(files),
            "receipts": len(receipts),
            "compact_manifests": 1 if compact_manifest.exists() else 0,
        }
    backlog = _route_backlog_summary()
    data["_summary"] = {
        **backlog,
    }
    return data


def _route_results_summary(results: list[dict]) -> dict:
    summary = {
        "routed": 0,
        "already_routed": 0,
        "companion_missing": 0,
        "dry_run": 0,
        "errors": 0,
        "stages": {},
    }
    for r in results:
        status = r.get("status", "error")
        if status in summary:
            summary[status] += 1
        elif status in {"error", "unknown_stage"}:
            summary["errors"] += 1
        else:
            summary["errors"] += 1
        stage = r.get("stage")
        if stage:
            summary["stages"][stage] = summary["stages"].get(stage, 0) + 1
    return summary


def _load_json_records(paths: list[Path]) -> list[dict]:
    records: list[dict] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            payload = {"_parse_error": str(exc)}
        records.append({
            "path": safe_relative(path),
            "name": path.name,
            "payload": payload,
        })
    return records


def _compact_intake_batch(batch_dir: Path, apply: bool = False) -> dict:
    extract_paths = sorted(batch_dir.glob(".zombie_extract_*.json"))
    receipt_paths = sorted(batch_dir.glob(".zombie_receipt_*.json"))
    if not extract_paths and not receipt_paths:
        return {
            "status": "skipped",
            "surface": "intake",
            "batch": safe_relative(batch_dir),
            "extract_count": 0,
            "receipt_count": 0,
        }

    extract_records = _load_json_records(extract_paths)
    receipt_records = _load_json_records(receipt_paths)
    manifest_path = batch_dir / ".zombie_compact_manifest.json"

    ore_histogram: dict[str, int] = {}
    category_histogram: dict[str, int] = {}
    for record in extract_records:
        payload = record["payload"]
        ore = str(payload.get("ore_rating", "?"))
        ore_histogram[ore] = ore_histogram.get(ore, 0) + 1
        category = str(payload.get("category", "unknown"))
        category_histogram[category] = category_histogram.get(category, 0) + 1

    manifest = {
        "kind": "zombie_intake_compaction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "batch": safe_relative(batch_dir),
        "apply_mode": apply,
        "extract_count": len(extract_records),
        "receipt_count": len(receipt_records),
        "ore_histogram": ore_histogram,
        "category_histogram": category_histogram,
        "extracts": extract_records,
        "receipts": receipt_records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if apply:
        for path in [*extract_paths, *receipt_paths]:
            path.unlink()

    return {
        "status": "compacted",
        "surface": "intake",
        "batch": safe_relative(batch_dir),
        "manifest": safe_relative(manifest_path),
        "extract_count": len(extract_records),
        "receipt_count": len(receipt_records),
        "deleted_sidecars": len(extract_records) + len(receipt_records) if apply else 0,
    }


def _intake_compaction_targets() -> list[Path]:
    extract_dirs = {p.parent for p in INTAKE_LEGACY.rglob(".zombie_extract_*.json")}
    receipt_dirs = {p.parent for p in INTAKE_LEGACY.rglob(".zombie_receipt_*.json")}
    return sorted(extract_dirs | receipt_dirs)


def _compact_forge_stage(stage_name: str, stage_dir: Path, apply: bool = False) -> dict:
    receipt_paths = sorted(stage_dir.glob(".forge_receipt_*.json"))
    if not receipt_paths:
        return {
            "status": "skipped",
            "surface": "forge",
            "stage": stage_name,
            "receipt_count": 0,
        }

    receipt_records = _load_json_records(receipt_paths)
    manifest_path = stage_dir / ".forge_compact_manifest.json"
    stage_targets: dict[str, int] = {}
    for record in receipt_records:
        payload = record["payload"]
        target = str(payload.get("routed_to", "unknown"))
        stage_targets[target] = stage_targets.get(target, 0) + 1

    manifest = {
        "kind": "forge_stage_compaction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage_name,
        "directory": safe_relative(stage_dir),
        "apply_mode": apply,
        "receipt_count": len(receipt_records),
        "targets": stage_targets,
        "receipts": receipt_records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if apply:
        for path in receipt_paths:
            path.unlink()

    return {
        "status": "compacted",
        "surface": "forge",
        "stage": stage_name,
        "manifest": safe_relative(manifest_path),
        "receipt_count": len(receipt_records),
        "deleted_sidecars": len(receipt_records) if apply else 0,
    }


def compact_sidecars(
    surface: str = "all",
    batch_filter: str | None = None,
    stage_filter: str | None = None,
    apply: bool = False,
) -> list[dict]:
    results: list[dict] = []

    if surface in {"all", "intake"}:
        for batch_dir in _intake_compaction_targets():
            if batch_filter and batch_filter not in safe_relative(batch_dir):
                continue
            results.append(_compact_intake_batch(batch_dir, apply=apply))

    if surface in {"all", "forge"}:
        for stage_name, stage_dir in sorted(FORGE_STAGES.items()):
            if stage_filter and stage_filter != stage_name:
                continue
            results.append(_compact_forge_stage(stage_name, stage_dir, apply=apply))

    return results


def _compact_results_summary(results: list[dict]) -> dict:
    summary = {
        "compacted": 0,
        "skipped": 0,
        "deleted_sidecars": 0,
        "intake_batches": 0,
        "forge_stages": 0,
    }
    for result in results:
        status = result.get("status")
        if status == "compacted":
            summary["compacted"] += 1
            summary["deleted_sidecars"] += int(result.get("deleted_sidecars", 0))
            if result.get("surface") == "intake":
                summary["intake_batches"] += 1
            elif result.get("surface") == "forge":
                summary["forge_stages"] += 1
        else:
            summary["skipped"] += 1
    return summary


def _render_compact_results(results: list[dict], apply: bool) -> None:
    from rich.panel import Panel
    from rich.table import Table

    console = _get_console()
    title = "[bold]SIDECAR COMPACTION — APPLY[/bold]" if apply else "[bold]SIDECAR COMPACTION — DRY RUN[/bold]"

    table = Table(title=None, box=None, show_header=True)
    table.add_column("Status", style="bold")
    table.add_column("Surface")
    table.add_column("Scope", style="dim")
    table.add_column("Extracts", justify="right")
    table.add_column("Receipts", justify="right")
    table.add_column("Deleted", justify="right")

    for result in results:
        scope = result.get("batch") or result.get("stage") or "?"
        table.add_row(
            result.get("status", "?"),
            result.get("surface", "?"),
            scope,
            str(result.get("extract_count", 0)),
            str(result.get("receipt_count", 0)),
            str(result.get("deleted_sidecars", 0)),
        )

    summary = _compact_results_summary(results)
    console.print(Panel(table, title=title, border_style="dim"))
    console.print(
        f"[green]{summary['compacted']} compacted[/green]  "
        f"[dim]{summary['skipped']} skipped[/dim]  "
        f"[yellow]{summary['deleted_sidecars']} sidecars removed[/yellow]"
    )


# ---------------------------------------------------------------------------
# Batch-level receipt + undo
# ---------------------------------------------------------------------------

def _write_batch_receipt(batch: str | None, results: list[dict], dry_run: bool) -> Path | None:
    """Write a batch-level summary receipt JSON to FORGE/.forge_batch_receipt_*.json.

    Returns the path written, or None when dry_run.
    """
    if dry_run:
        return None
    FORGE.mkdir(parents=True, exist_ok=True)
    label = batch or "unfiltered"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = FORGE / f".forge_batch_receipt_{label}_{ts}.json"
    payload: dict = {
        "batch":     label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run":   dry_run,
        "summary":   _route_results_summary(results),
        "results":   results,
    }
    receipt_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def undo_batch(batch: str, dry_run: bool = False) -> list[dict]:
    """Reverse a named batch route: remove staged files + forge receipt sidecars.

    Scans every forge stage for receipts whose source_extract contains `batch`.
    Returns a list of action dicts.
    """
    actions: list[dict] = []
    for stage_name, stage_dir in FORGE_STAGES.items():
        if not stage_dir.exists():
            continue
        for receipt_path in stage_dir.glob(".forge_receipt_*.json"):
            try:
                data = json.loads(receipt_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            source_extract = data.get("source_extract", "")
            if batch not in source_extract:
                continue
            routed_to = data.get("routed_to", "")
            staged_path = ROOT / routed_to if routed_to and not Path(routed_to).is_absolute() else Path(routed_to)
            action: dict = {
                "batch":        batch,
                "stage":        stage_name,
                "receipt":      safe_relative(receipt_path),
                "staged_file":  routed_to,
                "dry_run":      dry_run,
            }
            if dry_run:
                action["status"] = "would_remove"
            else:
                removed: list[str] = []
                if staged_path.exists():
                    staged_path.unlink()
                    removed.append("staged_file")
                receipt_path.unlink(missing_ok=True)
                removed.append("receipt")
                action["status"] = "removed"
                action["removed"] = removed
            actions.append(action)
    return actions


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

    p_retro = sub.add_parser("retro-collapse", help="Retro-route historical intake spray into forge stages")
    p_retro.add_argument("--dry-run", action="store_true", help="Preview retro-collapse without writing")
    p_retro.add_argument("--batch", type=str, default=None, metavar="NAME",
                         help="Restrict retro-collapse to one historical intake batch")
    p_retro.add_argument("--json", action="store_true", help="JSON output")

    p_compact = sub.add_parser("compact", help="Compact intake/forge sidecar spray into manifests")
    p_compact.add_argument("--dry-run", action="store_true", help="Preview compaction without deleting sidecars")
    p_compact.add_argument("--surface", choices=["all", "intake", "forge"], default="all",
                           help="Which sidecar surface to compact")
    p_compact.add_argument("--batch", type=str, default=None, metavar="NAME",
                           help="Restrict intake compaction to one batch")
    p_compact.add_argument("--stage", type=str, default=None, metavar="STAGE",
                           help="Restrict forge compaction to one stage")
    p_compact.add_argument("--json", action="store_true", help="JSON output")

    p_undo = sub.add_parser("undo", help="Reverse a named batch route: remove staged files + receipt sidecars")
    p_undo.add_argument("batch", type=str, metavar="BATCH", help="Batch name to undo (substring match on source_extract)")
    p_undo.add_argument("--dry-run", action="store_true", help="Preview removals without deleting")
    p_undo.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "route":
        ensure_forge_dirs()
        routed_hashes = load_routed_hashes()
        results: list[dict] = []
        for extract_path, extract_data in scan_extracts(batch_filter=args.batch):
            result = route_file(
                extract_path, extract_data, routed_hashes, dry_run=args.dry_run
            )
            results.append(result)
        _write_batch_receipt(args.batch, results, dry_run=args.dry_run)
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

    if args.command == "retro-collapse":
        ensure_forge_dirs()
        routed_hashes = load_routed_hashes()
        results: list[dict] = []
        for extract_path, extract_data in scan_extracts(batch_filter=args.batch):
            result = route_file(
                extract_path, extract_data, routed_hashes, dry_run=args.dry_run
            )
            results.append(result)
        _write_batch_receipt(args.batch, results, dry_run=args.dry_run)
        payload = {
            "summary": _route_results_summary(results),
            "results": results,
        }
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2))
        else:
            _render_route_results(results, dry_run=args.dry_run)
        return 0

    if args.command == "compact":
        results = compact_sidecars(
            surface=args.surface,
            batch_filter=args.batch,
            stage_filter=args.stage,
            apply=not args.dry_run,
        )
        payload = {
            "summary": _compact_results_summary(results),
            "results": results,
        }
        if getattr(args, "json", False):
            print(json.dumps(payload, indent=2))
        else:
            _render_compact_results(results, apply=not args.dry_run)
        return 0

    if args.command == "undo":
        actions = undo_batch(args.batch, dry_run=args.dry_run)
        if getattr(args, "json", False):
            print(json.dumps(actions, indent=2))
        else:
            console = _get_console()
            for a in actions:
                status_color = "yellow" if a.get("dry_run") else "red"
                console.print(
                    f"[{status_color}]{a['status']}[/{status_color}] "
                    f"[dim]{a['stage']}[/dim] {a.get('staged_file', '')}"
                )
            console.print(f"[dim]{len(actions)} entries processed for batch '{args.batch}'[/dim]")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
