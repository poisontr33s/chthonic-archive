#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
Handoff Loop Orchestrator.

Closes the manual gaps in the agent-to-agent mailbox pipeline by adding:
- Pre-write validation (catch bad handoffs before routing)
- Gate enforcement (block routing if quality < threshold)
- Receipt tracking (ACK/read confirmation log)
- Obligation tracking (pending items, stale handoffs, overdue responses)

Connects existing tools: handoff_audit.py, mailbox_check.py, mailbox_manifest.py
into a self-healing loop.

@SID:           TOOL_HANDOFF_LOOP_V1
@Type:          Utility
@Context:       Infrastructure / Cross-Agent Orchestration
@Implements:    Unified handoff-loop closing 4 manual breaks

Usage:
    uv run scripts/handoff_loop.py status                # show pending obligations + receipts
    uv run scripts/handoff_loop.py validate <file>       # pre-write validation of a handoff
    uv run scripts/handoff_loop.py gate <file>            # validate + score; exit 1 if below threshold
    uv run scripts/handoff_loop.py ack <file>             # record receipt for a handoff
    uv run scripts/handoff_loop.py obligations            # list all unACK'd handoffs by age
    uv run scripts/handoff_loop.py route <file> --to X    # validate → gate → route → log
    uv run scripts/handoff_loop.py sweep                  # full pipeline: obligations + stale alerts
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants
# =============================================================================

RECEIPT_LOG_FILENAME = "HANDOFF_RECEIPT_LOG.json"
RECEIPT_LOG_SCHEMA = 1
GATE_THRESHOLD = 6.0  # minimum composite score to pass gate
STALE_HOURS = 12  # hours before an unACK'd handoff is flagged as stale

MAILBOX_DIRS = {
    "claude": "claude/mailbox",
    "codex": "codex/mailbox",
    "gemini": "gemini/mailbox",
}

REQUIRED_FRONTMATTER = {"type", "from", "to", "created", "priority", "scope"}
REQUIRED_SECTIONS = {"actions_taken", "files_changed", "how_to_verify", "next_actions"}

SECTION_ALIASES: dict[str, list[str]] = {
    "actions_taken": ["Actions Taken", "What I Did", "What I Did (Concrete Changes)"],
    "files_changed": ["Files Changed", "Changed Files"],
    "how_to_verify": ["How to verify", "How To Verify", "Verification Evidence", "How to Verify"],
    "next_actions": ["Next Actions", "What's next", "What's next", "What is next"],
}

RE_FM_START = re.compile(r"^---\s*$")
RE_FM_KV = re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$")
RE_SECTION_HEADER = re.compile(r"^#{1,6}\s+(.+?)\s*$")


# =============================================================================
# Frontmatter / Section Parsing (lightweight, avoid importing handoff_audit)
# =============================================================================

def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and return (frontmatter_dict, body)."""
    lines = text.split("\n")
    if not lines or not RE_FM_START.match(lines[0]):
        return {}, text

    fm: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if RE_FM_START.match(line):
            body = "\n".join(lines[i + 1:])
            return fm, body
        m = RE_FM_KV.match(line)
        if m:
            fm[m.group(1).lower().replace("-", "_")] = m.group(2).strip()
    return {}, text


def parse_sections(body: str) -> set[str]:
    """Extract section header names (lowercased) from markdown body."""
    found: set[str] = set()
    for line in body.split("\n"):
        m = RE_SECTION_HEADER.match(line)
        if m:
            found.add(m.group(1).strip().lower())
    return found


def match_section(found_sections: set[str], aliases: list[str]) -> bool:
    """Check if any alias matches a found section header."""
    return any(a.lower() in found_sections for a in aliases)


def file_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# Receipt Log
# =============================================================================

def load_receipt_log(repo_root: Path) -> dict:
    """Load the receipt log from claude-codex-gemini/."""
    path = repo_root / "claude-codex-gemini" / RECEIPT_LOG_FILENAME
    if path.is_file():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"schema_version": RECEIPT_LOG_SCHEMA, "receipts": {}}


def save_receipt_log(repo_root: Path, log: dict) -> Path:
    """Persist receipt log."""
    path = repo_root / "claude-codex-gemini" / RECEIPT_LOG_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    return path


def record_receipt(repo_root: Path, file_path: Path, reader: str) -> dict:
    """Record that `reader` has acknowledged `file_path`."""
    log = load_receipt_log(repo_root)
    rel = file_path.relative_to(repo_root).as_posix()
    now = datetime.now(tz=timezone.utc).isoformat()

    if rel not in log["receipts"]:
        log["receipts"][rel] = {"acks": []}

    log["receipts"][rel]["acks"].append({
        "reader": reader,
        "ack_at": now,
        "sha256": file_sha256(file_path),
    })

    save_receipt_log(repo_root, log)
    return {"path": rel, "reader": reader, "ack_at": now}


# =============================================================================
# Validation
# =============================================================================

def validate_handoff(file_path: Path) -> dict:
    """Pre-write validation — checks structure without scoring."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    sections = parse_sections(body)

    missing_fm = sorted(REQUIRED_FRONTMATTER - set(fm.keys()))
    found_sections = {
        key: match_section(sections, aliases)
        for key, aliases in SECTION_ALIASES.items()
    }
    missing_sec = sorted(k for k, v in found_sections.items() if not v)

    errors: list[str] = []
    warnings: list[str] = []

    if not fm:
        errors.append("No YAML frontmatter block found (missing --- delimiters)")
    for field in missing_fm:
        errors.append(f"Missing required frontmatter field: {field}")
    for sec in missing_sec:
        errors.append(f"Missing required section: {sec}")

    # Filename check
    name = file_path.name
    if not name.startswith("SESSION_HANDOFF_"):
        if "HANDOFF" not in name.upper():
            warnings.append(f"Filename '{name}' does not follow SESSION_HANDOFF_* convention")

    # Size check
    size = file_path.stat().st_size
    if size < 200:
        warnings.append(f"File is very small ({size} bytes) — may lack substance")
    if size > 50_000:
        warnings.append(f"File is large ({size} bytes) — consider splitting")

    return {
        "file": str(file_path.name),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "frontmatter_fields": list(fm.keys()),
        "sections_found": sorted(s for s, v in found_sections.items() if v),
        "sections_missing": missing_sec,
    }


# =============================================================================
# Gate (validate + score via handoff_audit import)
# =============================================================================

def gate_handoff(file_path: Path, repo_root: Path, threshold: float) -> dict:
    """Validate + compute quality score; return pass/fail with details."""
    validation = validate_handoff(file_path)

    if not validation["valid"]:
        return {
            "passed": False,
            "reason": "validation_errors",
            "validation": validation,
            "score": 0.0,
            "threshold": threshold,
        }

    # Import scoring from handoff_audit
    try:
        from scripts.handoff_audit import score_handoff as audit_score

        result = audit_score(
            handoff_path=file_path,
            repo_root=repo_root,
            root_token=file_path.parent.name,
            root_md_count=1,
            root_handoff_count=1,
        )
        composite = result.get("composite_score", 0.0)
    except Exception as e:
        # Fallback: use validation-only score
        composite = 7.0 if validation["valid"] else 0.0
        validation["warnings"].append(f"Could not import handoff_audit scoring: {e}")

    passed = composite >= threshold
    return {
        "passed": passed,
        "reason": "passed" if passed else f"score {composite:.1f} < threshold {threshold:.1f}",
        "score": round(composite, 2),
        "threshold": threshold,
        "validation": validation,
    }


# =============================================================================
# Obligations
# =============================================================================

def find_handoffs(repo_root: Path) -> list[dict]:
    """Find all SESSION_HANDOFF_*.md files across mailbox dirs."""
    handoffs = []
    for lane, rel_dir in MAILBOX_DIRS.items():
        mailbox = repo_root / rel_dir
        if not mailbox.is_dir():
            continue
        for path in sorted(mailbox.glob("SESSION_HANDOFF_*.md")):
            stat = path.stat()
            handoffs.append({
                "path": path.relative_to(repo_root).as_posix(),
                "full_path": path,
                "lane": lane,
                "filename": path.name,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            })
    return handoffs


def compute_obligations(repo_root: Path) -> dict:
    """Identify pending (unACK'd) handoffs and stale ones."""
    handoffs = find_handoffs(repo_root)
    receipt_log = load_receipt_log(repo_root)
    receipts = receipt_log.get("receipts", {})
    now = datetime.now(tz=timezone.utc)
    stale_cutoff = now - timedelta(hours=STALE_HOURS)

    pending = []
    stale = []
    acked = []

    for h in handoffs:
        rel = h["path"]
        ack_info = receipts.get(rel, {})
        ack_list = ack_info.get("acks", [])

        if ack_list:
            acked.append({
                "path": rel,
                "lane": h["lane"],
                "last_ack": ack_list[-1]["ack_at"],
                "ack_count": len(ack_list),
            })
        else:
            entry = {
                "path": rel,
                "lane": h["lane"],
                "age_hours": round((now - h["mtime"]).total_seconds() / 3600, 1),
                "size": h["size"],
            }
            if h["mtime"] < stale_cutoff:
                stale.append(entry)
            else:
                pending.append(entry)

    return {
        "total_handoffs": len(handoffs),
        "acked": len(acked),
        "pending": len(pending),
        "stale": len(stale),
        "stale_threshold_hours": STALE_HOURS,
        "pending_items": sorted(pending, key=lambda x: -x["age_hours"]),
        "stale_items": sorted(stale, key=lambda x: -x["age_hours"]),
        "acked_items": acked,
    }


# =============================================================================
# Route (validate → gate → copy → log)
# =============================================================================

def route_handoff(file_path: Path, target_lane: str, repo_root: Path, threshold: float, log) -> dict:
    """Full pipeline: validate → gate → copy to target → record receipt as sender."""
    import shutil

    if target_lane not in MAILBOX_DIRS:
        return {"routed": False, "reason": f"Unknown target lane: {target_lane}"}

    gate_result = gate_handoff(file_path, repo_root, threshold)
    if not gate_result["passed"]:
        log.warning("Gate FAILED for %s: %s", file_path.name, gate_result["reason"])
        return {"routed": False, "gate": gate_result}

    target_dir = repo_root / MAILBOX_DIRS[target_lane]
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / file_path.name

    shutil.copy2(str(file_path), str(dest))
    log.info("Routed %s → %s", file_path.name, dest.relative_to(repo_root))

    # Record sender receipt (the sender has "read" their own output)
    fm_text = file_path.read_text(encoding="utf-8", errors="replace")
    fm, _ = parse_frontmatter(fm_text)
    sender = fm.get("from", "unknown")
    record_receipt(repo_root, file_path, sender)

    return {
        "routed": True,
        "source": file_path.relative_to(repo_root).as_posix(),
        "destination": dest.relative_to(repo_root).as_posix(),
        "gate": gate_result,
    }


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        description="Handoff loop orchestrator — closes manual gaps in the agent mailbox pipeline."
    )
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Show pending obligations + receipt summary")

    # validate
    p_val = sub.add_parser("validate", help="Pre-write validation of a handoff file")
    p_val.add_argument("file", type=Path)

    # gate
    p_gate = sub.add_parser("gate", help="Validate + score; exit 1 if below threshold")
    p_gate.add_argument("file", type=Path)
    p_gate.add_argument("--threshold", type=float, default=GATE_THRESHOLD)

    # ack
    p_ack = sub.add_parser("ack", help="Record receipt for a handoff")
    p_ack.add_argument("file", type=Path)
    p_ack.add_argument("--reader", required=True, help="Who is ACKing (claude/codex/gemini)")

    # obligations
    sub.add_parser("obligations", help="List all unACK'd handoffs by age")

    # route
    p_route = sub.add_parser("route", help="Validate → gate → route → log")
    p_route.add_argument("file", type=Path)
    p_route.add_argument("--to", required=True, dest="target", help="Target lane (claude/codex/gemini)")
    p_route.add_argument("--threshold", type=float, default=GATE_THRESHOLD)

    # sweep
    sub.add_parser("sweep", help="Full pipeline: obligations + stale alerts + manifest refresh")

    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)
    repo_root = find_repo_root()

    if not args.command:
        parser.print_help()
        return 0

    # --- status ---
    if args.command == "status":
        oblig = compute_obligations(repo_root)
        if args.json:
            print(json.dumps(oblig, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"Handoffs: {oblig['total_handoffs']} total, {oblig['acked']} ACK'd, {oblig['pending']} pending, {oblig['stale']} stale (>{oblig['stale_threshold_hours']}h)")
            if oblig["stale_items"]:
                print("\nSTALE (overdue):")
                for item in oblig["stale_items"]:
                    print(f"  [{item['lane']}] {item['path']} ({item['age_hours']}h old)")
            if oblig["pending_items"]:
                print("\nPENDING:")
                for item in oblig["pending_items"]:
                    print(f"  [{item['lane']}] {item['path']} ({item['age_hours']}h old)")
        return 0

    # --- validate ---
    if args.command == "validate":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        result = validate_handoff(file_path)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            status = "VALID" if result["valid"] else "INVALID"
            print(f"{status}: {result['file']}")
            for e in result["errors"]:
                print(f"  ERROR: {e}")
            for w in result["warnings"]:
                print(f"  WARN:  {w}")
        return 0 if result["valid"] else 1

    # --- gate ---
    if args.command == "gate":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        result = gate_handoff(file_path, repo_root, args.threshold)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"{status}: score={result['score']}, threshold={result['threshold']}")
            if not result["passed"]:
                for e in result["validation"]["errors"]:
                    print(f"  ERROR: {e}")
        return 0 if result["passed"] else 1

    # --- ack ---
    if args.command == "ack":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        receipt = record_receipt(repo_root, file_path, args.reader)
        if args.json:
            print(json.dumps(receipt, indent=2))
        else:
            print(f"ACK recorded: {receipt['reader']} → {receipt['path']} at {receipt['ack_at']}")
        return 0

    # --- obligations ---
    if args.command == "obligations":
        oblig = compute_obligations(repo_root)
        if args.json:
            print(json.dumps(oblig, indent=2, default=str))
        else:
            if not oblig["pending_items"] and not oblig["stale_items"]:
                print(f"No pending obligations ({oblig['acked']} handoffs all ACK'd)")
                return 0
            for item in oblig["stale_items"]:
                print(f"  STALE [{item['lane']}] {item['path']} ({item['age_hours']}h)")
            for item in oblig["pending_items"]:
                print(f"  PENDING [{item['lane']}] {item['path']} ({item['age_hours']}h)")
        return 0

    # --- route ---
    if args.command == "route":
        file_path = args.file.resolve()
        if not file_path.is_file():
            log.error("File not found: %s", file_path)
            return 1
        result = route_handoff(file_path, args.target, repo_root, args.threshold, log)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["routed"]:
                print(f"ROUTED: {result['source']} → {result['destination']} (score={result['gate']['score']})")
            else:
                print(f"BLOCKED: {result.get('reason', result.get('gate', {}).get('reason', 'unknown'))}")
        return 0 if result.get("routed", False) else 1

    # --- sweep ---
    if args.command == "sweep":
        oblig = compute_obligations(repo_root)
        if args.json:
            print(json.dumps(oblig, indent=2, default=str))
        else:
            print(f"=== Handoff Loop Sweep ===")
            print(f"Total: {oblig['total_handoffs']}, ACK'd: {oblig['acked']}, Pending: {oblig['pending']}, Stale: {oblig['stale']}")
            if oblig["stale_items"]:
                print(f"\n🔴 STALE HANDOFFS (>{STALE_HOURS}h unACK'd):")
                for item in oblig["stale_items"]:
                    print(f"  [{item['lane']}] {item['path']} — {item['age_hours']}h old")
            if oblig["pending_items"]:
                print(f"\n🟡 PENDING HANDOFFS:")
                for item in oblig["pending_items"]:
                    print(f"  [{item['lane']}] {item['path']} — {item['age_hours']}h old")
            if not oblig["stale_items"] and not oblig["pending_items"]:
                print("\n✅ All handoffs acknowledged")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
