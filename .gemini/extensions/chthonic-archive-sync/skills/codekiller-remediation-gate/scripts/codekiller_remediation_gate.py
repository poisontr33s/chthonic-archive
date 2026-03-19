#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: codekiller_remediation_gate.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
codekiller_remediation_gate.py - Prerequisite gate for CDE-KLLR recovery.

@SID:           TOOL_CODEKILLER_REMEDIATION_GATE_V1
@Shabti:        CLI Script
@Heka-Ayni:     CONCEPT_TRIBUNAL_RECOVERY_GATING
@Ankh-Tinku:    STATE_CODEKILLER_PREREQ_CLASSIFIED
@Purpose:       Validates governance/evidence prerequisites for Codekiller
                remediation and emits an iterative, milestone-based recovery
                plan for steward adjudication.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


CODEKILLER_CASE_ID = "CODEKILLER_2024_06_01"
TRIBUNAL_DOCS = [
    ".temple/governance/TRIBUNAL_SPEC.md",
    ".temple/governance/ROLES.md",
    ".temple/governance/CRIME_CLASSIFICATION.md",
    ".temple/governance/POINTS_ECONOMY.md",
    ".temple/governance/PROCEEDINGS.md",
    ".temple/governance/TEMPORAL_MECHANICS.md",
    ".temple/governance/FRACTAL_GOVERNANCE.md",
    ".temple/governance/ledger/LEDGER.yaml",
    ".temple/governance/ledger/PRECEDENTS.yaml",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _first_int(pattern: str, text: str, flags: int = 0) -> int | None:
    match = re.search(pattern, text, flags)
    if not match:
        return None
    return int(match.group(1))


def _file_exists(path: Path) -> bool:
    return path.exists()


def _latest_run_dir(overnight_root: Path) -> Path | None:
    if not overnight_root.exists():
        return None
    run_dirs = [
        path
        for path in overnight_root.iterdir()
        if path.is_dir() and re.match(r"^\d{8}_\d{6}$", path.name)
    ]
    if not run_dirs:
        return None
    return sorted(run_dirs, key=lambda item: item.name)[-1]


def _latest_nightly_log(overnight_root: Path) -> Path | None:
    if not overnight_root.exists():
        return None
    logs = sorted(overnight_root.glob("nightly-scheduled-*.log"), key=lambda item: item.name)
    if not logs:
        return None
    return logs[-1]


def _resolve_file_uri(uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme.lower() != "file":
        return None

    path_text = unquote(parsed.path or "")
    if re.match(r"^/[A-Za-z]:/", path_text):
        path_text = path_text[1:]
    if not path_text and parsed.netloc:
        path_text = parsed.netloc

    if not path_text:
        return None
    return Path(path_text)


def _normalize_for_report(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _extract_frontmatter(markdown_text: str) -> str:
    match = re.search(r"(?s)^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", markdown_text)
    if not match:
        return ""
    return match.group(1)


def _extract_list_section(frontmatter_text: str, section_key: str) -> list[str]:
    lines = frontmatter_text.splitlines()
    in_section = False
    items: list[str] = []

    for raw in lines:
        line = raw.rstrip()
        if re.match(rf"^\s*{re.escape(section_key)}:\s*$", line):
            in_section = True
            continue
        if not in_section:
            continue

        if re.match(r"^\s*-\s+", line):
            items.append(re.sub(r"^\s*-\s+", "", line).strip())
            continue

        if line.strip() == "":
            continue

        if re.match(r"^[A-Za-z0-9_-]+\s*:\s*", line):
            break

        if re.match(r"^\s+[A-Za-z0-9_-]+\s*:\s*", line):
            break

    return items


def _token_set(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {token for token in tokens if len(token) >= 4}


def _token_overlap_score(expected: str, actual: str) -> float:
    expected_tokens = _token_set(expected)
    if not expected_tokens:
        return 1.0
    actual_tokens = _token_set(actual)
    return len(expected_tokens.intersection(actual_tokens)) / len(expected_tokens)


def _resolve_local_path(path_text: str, repo_root: Path, source_dir: Path) -> Path | None:
    if path_text.lower().startswith("file://"):
        return _resolve_file_uri(path_text)

    candidate = Path(path_text)
    if candidate.is_absolute():
        return candidate

    repo_candidate = (repo_root / candidate).resolve()
    if repo_candidate.exists():
        return repo_candidate

    source_candidate = (source_dir / candidate).resolve()
    return source_candidate


def _extract_local_markdown_links(markdown_text: str, source_dir: Path, repo_root: Path) -> list[dict[str, object]]:
    links: list[dict[str, object]] = []
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for match in pattern.finditer(markdown_text):
        label = match.group(1).strip()
        href = match.group(2).strip()

        if href.startswith("#") or href.startswith("mailto:"):
            continue
        if href.startswith("http://") or href.startswith("https://"):
            continue

        resolved = _resolve_local_path(href, repo_root, source_dir)
        links.append(
            {
                "label": label,
                "href": href,
                "resolved_path": _normalize_for_report(resolved, repo_root) if resolved else None,
                "exists": bool(resolved and resolved.exists()),
            }
        )

    return links


def _audit_policy_basis(entries: list[str], repo_root: Path, source_dir: Path) -> dict[str, object]:
    audits: list[dict[str, object]] = []

    for raw_entry in entries:
        entry = raw_entry.strip()
        path_token = entry
        notes: list[str] = []
        line_number: int | None = None

        if "(" in path_token and path_token.lower().startswith("readme.md"):
            path_token = path_token.split("(", 1)[0].strip()
            notes.append("ambiguous_readme_entry")

        line_match = re.match(r"^(?P<path>[A-Za-z0-9._/\\-]+):(?P<line>\d+)$", path_token)
        if line_match:
            path_token = line_match.group("path")
            line_number = int(line_match.group("line"))

        resolved = _resolve_local_path(path_token, repo_root, source_dir)
        exists = bool(resolved and resolved.exists())
        line_preview = ""
        status = "PASS"

        if not exists:
            status = "FAIL"
            notes.append("missing_file")
        elif line_number is not None and resolved is not None:
            lines = _read_text(resolved).splitlines()
            if line_number < 1 or line_number > len(lines):
                status = "FAIL"
                notes.append("line_out_of_range")
            else:
                line_preview = lines[line_number - 1].strip()
                if line_preview == "":
                    status = "FAIL"
                    notes.append("line_blank")

        if status == "PASS" and notes:
            status = "WARN"

        audits.append(
            {
                "entry": entry,
                "resolved_path": _normalize_for_report(resolved, repo_root) if resolved else None,
                "exists": exists,
                "line": line_number,
                "line_preview": line_preview,
                "status": status,
                "notes": notes,
            }
        )

    return {
        "entries": audits,
        "summary": {
            "total": len(audits),
            "pass": sum(1 for item in audits if item["status"] == "PASS"),
            "warn": sum(1 for item in audits if item["status"] == "WARN"),
            "fail": sum(1 for item in audits if item["status"] == "FAIL"),
        },
        "strict_pass": all(item["status"] == "PASS" for item in audits),
    }


def _audit_reference_assertions(entries: list[str], repo_root: Path, source_dir: Path) -> dict[str, object]:
    audits: list[dict[str, object]] = []

    for raw_entry in entries:
        entry = raw_entry.strip()
        notes: list[str] = []
        status = "PASS"
        resolved: Path | None = None
        line_number: int | None = None
        line_preview = ""
        overlap = None

        if "—" in entry:
            anchor, expected = entry.split("—", 1)
            anchor = anchor.strip()
            expected = expected.strip().strip('"').strip("'")
        else:
            anchor = entry
            expected = ""
            notes.append("missing_em_dash_assertion")

        line_match = re.match(r"^(?P<path>[A-Za-z0-9._/\\-]+):(?P<line>\d+)$", anchor)
        if line_match:
            path_token = line_match.group("path")
            line_number = int(line_match.group("line"))
            resolved = _resolve_local_path(path_token, repo_root, source_dir)

            if not (resolved and resolved.exists()):
                status = "FAIL"
                notes.append("missing_file")
            else:
                lines = _read_text(resolved).splitlines()
                if line_number < 1 or line_number > len(lines):
                    status = "FAIL"
                    notes.append("line_out_of_range")
                else:
                    line_preview = lines[line_number - 1].strip()
                    if line_preview == "":
                        status = "FAIL"
                        notes.append("line_blank")
                    elif expected:
                        overlap = _token_overlap_score(expected, line_preview)
                        if overlap < 0.20:
                            status = "FAIL"
                            notes.append("assertion_quote_drift")
        else:
            resolved = _resolve_local_path(anchor, repo_root, source_dir)
            if not (resolved and resolved.exists()):
                status = "FAIL"
                notes.append("missing_file")
            else:
                notes.append("non_line_anchor")

        if status == "PASS" and "missing_em_dash_assertion" in notes:
            status = "WARN"

        audits.append(
            {
                "entry": entry,
                "anchor": anchor,
                "resolved_path": _normalize_for_report(resolved, repo_root) if resolved else None,
                "line": line_number,
                "line_preview": line_preview,
                "expected_excerpt": expected,
                "token_overlap": overlap,
                "status": status,
                "notes": notes,
            }
        )

    return {
        "entries": audits,
        "summary": {
            "total": len(audits),
            "pass": sum(1 for item in audits if item["status"] == "PASS"),
            "warn": sum(1 for item in audits if item["status"] == "WARN"),
            "fail": sum(1 for item in audits if item["status"] == "FAIL"),
        },
        "strict_pass": all(item["status"] == "PASS" for item in audits),
    }


def _audit_evidence_packet(codekiller_text: str) -> dict[str, object]:
    files_changed_claim = _first_int(r"(?m)^\s*(\d+)\s+files changed\s*$", codekiller_text)
    lines_added_claim = _first_int(r"(?m)^\s*\+(\d+)\s*$", codekiller_text)
    lines_deleted_claim = _first_int(r"(?m)^\s*-(\d+)\s*$", codekiller_text)
    named_fence_headers = re.findall(r"^```[^`\n]*:\s*$", codekiller_text, flags=re.MULTILINE)
    complete = files_changed_claim is None or len(named_fence_headers) >= files_changed_claim

    return {
        "files_changed_claim": files_changed_claim,
        "lines_added_claim": lines_added_claim,
        "lines_deleted_claim": lines_deleted_claim,
        "named_fence_headers": len(named_fence_headers),
        "named_fence_header_examples": named_fence_headers[:12],
        "complete": complete,
    }


def _audit_tribunal_chain(repo_root: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for rel_path in TRIBUNAL_DOCS:
        resolved = (repo_root / rel_path).resolve()
        entries.append({"path": rel_path, "exists": resolved.exists()})

    return {
        "entries": entries,
        "all_present": all(item["exists"] for item in entries),
        "missing": [item["path"] for item in entries if not item["exists"]],
    }


def _log_anomalies(log_text: str) -> dict[str, int]:
    return {
        "module_not_found": len(re.findall(r"ModuleNotFoundError", log_text)),
        "traceback": len(re.findall(r"Traceback", log_text)),
        "parsed_zero": len(re.findall(r"parsed 0", log_text)),
    }


def _report_summary(report_path: Path) -> dict[str, int | None]:
    if not _file_exists(report_path):
        return {"files_scanned": None, "todo_hits": None, "top_candidates": None}

    try:
        payload = json.loads(_read_text(report_path))
    except json.JSONDecodeError:
        return {"files_scanned": None, "todo_hits": None, "top_candidates": None}

    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}

    return {
        "files_scanned": summary.get("filesScanned"),
        "todo_hits": summary.get("todoHits"),
        "top_candidates": summary.get("topCandidates"),
    }


def _run_top_candidate(run_path: Path) -> str | None:
    if not _file_exists(run_path):
        return None
    try:
        payload = json.loads(_read_text(run_path))
    except json.JSONDecodeError:
        return None
    cycles = payload.get("cycles")
    if not isinstance(cycles, list) or not cycles:
        return None
    first = cycles[0]
    if not isinstance(first, dict):
        return None
    top_value = first.get("top")
    return top_value if isinstance(top_value, str) else None


def _build_report(repo_root: Path) -> dict[str, object]:
    codekiller_path = repo_root / "anti-patterns/codekiller.md"
    points_path = repo_root / ".temple/governance/POINTS_ECONOMY.md"
    ledger_path = repo_root / ".temple/governance/ledger/LEDGER.yaml"
    precedents_path = repo_root / ".temple/governance/ledger/PRECEDENTS.yaml"
    wptg_path = repo_root / "WET_PAPER_TO_GOLD_METHODOLOGY.md"
    wip_state_path = repo_root / "WET_PAPER_TO_GOLD_WIP/WET_PAPER_TO_GOLD_WIP_UPCYCLING_STATE.md"
    overnight_root = repo_root / "dumpster-dive/intake/overnight-daemon"

    codekiller_text = _read_text(codekiller_path) if _file_exists(codekiller_path) else ""
    points_text = _read_text(points_path) if _file_exists(points_path) else ""
    ledger_text = _read_text(ledger_path) if _file_exists(ledger_path) else ""
    precedents_text = _read_text(precedents_path) if _file_exists(precedents_path) else ""
    wptg_text = _read_text(wptg_path) if _file_exists(wptg_path) else ""
    wip_state_text = _read_text(wip_state_path) if _file_exists(wip_state_path) else ""
    frontmatter_text = _extract_frontmatter(codekiller_text)
    policy_basis_entries = _extract_list_section(frontmatter_text, "policy_basis")
    references_entries = _extract_list_section(frontmatter_text, "references")
    policy_basis_audit = _audit_policy_basis(policy_basis_entries, repo_root, codekiller_path.parent)
    reference_assertion_audit = _audit_reference_assertions(references_entries, repo_root, codekiller_path.parent)
    evidence_packet_audit = _audit_evidence_packet(codekiller_text)
    tribunal_chain_audit = _audit_tribunal_chain(repo_root)

    latest_run_dir = _latest_run_dir(overnight_root)
    latest_report = latest_run_dir / "report.json" if latest_run_dir else overnight_root / "missing-report.json"
    latest_run = latest_run_dir / "run.json" if latest_run_dir else overnight_root / "missing-run.json"
    latest_log = _latest_nightly_log(overnight_root) or overnight_root / "missing-log.log"
    latest_log_text = _read_text(latest_log) if _file_exists(latest_log) else ""

    markdown_links = _extract_local_markdown_links(codekiller_text, codekiller_path.parent, repo_root)
    broken_links = [item for item in markdown_links if not item["exists"]]

    points_required = _first_int(r"recovery_required:\s+(\d+)", points_text)
    points_remaining = _first_int(r"recovery_remaining:\s+(\d+)", points_text)
    precedents_required = _first_int(r"required:\s+(\d+)", precedents_text)
    precedents_earned = _first_int(r"earned:\s+(\d+)", precedents_text)
    precedents_milestones = _first_int(r"milestones_total:\s+(\d+)", precedents_text)
    ledger_remaining = _first_int(r"recovery_remaining:\s+(\d+)", ledger_text)
    ledger_structural = _first_int(r"codex:.*?structural:\s+(\d+)", ledger_text, flags=re.DOTALL)
    recovery_event_count = len(re.findall(r"type:\s*recovery_milestone", ledger_text))

    expected_remaining = None
    if precedents_required is not None and precedents_earned is not None:
        expected_remaining = max(0, precedents_required - precedents_earned)

    required_aligned = (
        points_required is not None
        and precedents_required is not None
        and points_required == precedents_required
    )
    remaining_aligned = (
        expected_remaining is not None
        and ledger_remaining is not None
        and points_remaining is not None
        and expected_remaining == ledger_remaining == points_remaining
    )

    governance_consistent = bool(required_aligned and remaining_aligned)
    evidence_links_intact = len(broken_links) == 0

    wptg_anchor_checks = {
        "every_file_is_gold": "Every file is gold." in wptg_text,
        "no_destroy_principle": "No-Destroy Principle" in wptg_text,
        "explicit_no_destroy_rule": "No agent" in wptg_text and "destroy, displace, or disappear" in wptg_text,
    }
    doctrine_present = all(wptg_anchor_checks.values())

    wip_anchor_checks = {
        "immutable_benchmark": "Immutable benchmark" in wip_state_text,
        "reference_pair_contract": "Reference Pair Contract" in wip_state_text,
        "baseline_hashes": "Baseline verification hashes" in wip_state_text,
    }
    baseline_present = all(wip_anchor_checks.values())

    summary = _report_summary(latest_report)
    telemetry_present = all(
        summary[key] is not None for key in ("files_scanned", "todo_hits", "top_candidates")
    ) and _file_exists(latest_log)
    anomalies = _log_anomalies(latest_log_text)
    telemetry_hardening_needed = any(value > 0 for value in anomalies.values())

    blockers: list[str] = []
    if not governance_consistent:
        blockers.append(
            "Governance mismatch: recovery totals disagree across economy/ledger/precedent surfaces "
            f"(expected_remaining={expected_remaining}, points_remaining={points_remaining}, ledger_remaining={ledger_remaining})."
        )
    if not evidence_links_intact:
        blockers.append(
            "Evidence link integrity failure: at least one local link in codekiller.md does not resolve "
            f"(broken_local_links={len(broken_links)})."
        )
    if not policy_basis_audit["strict_pass"]:
        blockers.append("Policy basis integrity failure: policy_basis entries are missing/ambiguous/drifted.")
    if not reference_assertion_audit["strict_pass"]:
        blockers.append("Reference assertion drift: frontmatter quoted references do not match anchored line content.")
    if not evidence_packet_audit["complete"]:
        blockers.append(
            "Evidence packet completeness failure: named fenced snippets are fewer than declared files changed "
            f"(named_fence_headers={evidence_packet_audit['named_fence_headers']}, "
            f"files_changed_claim={evidence_packet_audit['files_changed_claim']})."
        )
    if not doctrine_present:
        blockers.append("Doctrine anchor failure: WPTG no-destroy anchors are not fully detectable.")
    if not baseline_present:
        blockers.append("WIP baseline anchor failure: immutable benchmark contract is incomplete.")
    if not tribunal_chain_audit["all_present"]:
        blockers.append("Tribunal chain missing files: README governance targets are incomplete.")
    if not telemetry_present:
        blockers.append("Telemetry baseline missing: latest report/log evidence is incomplete.")
    if telemetry_hardening_needed:
        blockers.append("Operational anomalies present in nightly telemetry (parsed_zero/module_not_found/traceback).")

    readiness = "READY" if len(blockers) == 0 else "BLOCKED"

    repair_queue: list[dict[str, Any]] = []
    if not evidence_links_intact:
        repair_queue.append(
            {
                "priority": "P0",
                "id": "fix_broken_local_links",
                "reason": "Local evidence links must resolve before adjudication.",
                "targets": [item["href"] for item in broken_links],
            }
        )
    if not governance_consistent:
        repair_queue.append(
            {
                "priority": "P0",
                "id": "reconcile_recovery_arithmetic",
                "reason": "POINTS_ECONOMY, PRECEDENTS, and LEDGER must agree on recovery remaining.",
                "targets": [
                    ".temple/governance/POINTS_ECONOMY.md",
                    ".temple/governance/ledger/PRECEDENTS.yaml",
                    ".temple/governance/ledger/LEDGER.yaml",
                ],
            }
        )
    if not policy_basis_audit["strict_pass"] or not reference_assertion_audit["strict_pass"]:
        repair_queue.append(
            {
                "priority": "P1",
                "id": "reanchor_policy_basis_references",
                "reason": "Line-anchored policy references must be precise and verifiable.",
                "targets": ["anti-patterns/codekiller.md"],
            }
        )
    if not evidence_packet_audit["complete"]:
        repair_queue.append(
            {
                "priority": "P1",
                "id": "complete_evidence_packet_index",
                "reason": "Declared evidence size should be reproducible from packet metadata.",
                "targets": ["anti-patterns/codekiller.md"],
            }
        )
    if telemetry_hardening_needed:
        repair_queue.append(
            {
                "priority": "P2",
                "id": "stabilize_nightly_parsing",
                "reason": "Nightly telemetry anomalies block readiness confidence.",
                "targets": [
                    "dumpster-dive/intake/overnight-daemon/nightly-scheduled-*.log",
                    "dumpster-dive/intake/overnight-daemon/*/report.json",
                ],
            }
        )

    iterative_plan = [
        {
            "loop": 1,
            "title": "Canonical Truth",
            "objective": "Reconcile all recovery counters and case-state arithmetic.",
            "exit_criteria": "Required/remaining values align across POINTS_ECONOMY, PRECEDENTS, and LEDGER.",
        },
        {
            "loop": 2,
            "title": "Evidence Sanctification",
            "objective": "Make the Codekiller packet link-complete and provenance-verifiable.",
            "exit_criteria": "All local evidence links resolve and packet references are internally coherent.",
        },
        {
            "loop": 3,
            "title": "Operational Negentropy",
            "objective": "Reduce nightly anomaly signatures and stabilize ingestion quality.",
            "exit_criteria": "No ModuleNotFound/Traceback and parsed_zero trend is controlled or eliminated.",
        },
        {
            "loop": 4,
            "title": "Structural Gifts",
            "objective": "Produce sustained structural outputs with auditable quality gates.",
            "exit_criteria": "Milestone evidence accepted by steward and custody closure is adjudicated.",
        },
    ]

    milestones = [
        {
            "name": "M1 Canonical Reconciliation",
            "points_candidate": 5,
            "evidence_type": "governance consistency patch + validation output",
        },
        {
            "name": "M2 Evidence Packet Integrity",
            "points_candidate": 5,
            "evidence_type": "link-complete evidence packet with hash anchors",
        },
        {
            "name": "M3 Nightly Reliability Hardening",
            "points_candidate": 5,
            "evidence_type": "before/after telemetry anomaly reduction",
        },
        {
            "name": "M4 Sustained Structural Compliance",
            "points_candidate": 5,
            "evidence_type": "three clean structural sessions + steward audit",
        },
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "case_id": CODEKILLER_CASE_ID,
        "readiness": readiness,
        "blockers": blockers,
        "inputs": {
            "codekiller_path": _normalize_for_report(codekiller_path, repo_root),
            "points_economy_path": _normalize_for_report(points_path, repo_root),
            "ledger_path": _normalize_for_report(ledger_path, repo_root),
            "precedents_path": _normalize_for_report(precedents_path, repo_root),
            "wptg_path": _normalize_for_report(wptg_path, repo_root),
            "wip_state_path": _normalize_for_report(wip_state_path, repo_root),
            "latest_run_dir": _normalize_for_report(latest_run_dir, repo_root) if latest_run_dir else None,
            "latest_report_path": _normalize_for_report(latest_report, repo_root),
            "latest_run_path": _normalize_for_report(latest_run, repo_root),
            "latest_log_path": _normalize_for_report(latest_log, repo_root),
        },
        "evidence": {
            "governance_numbers": {
                "points_required": points_required,
                "points_remaining": points_remaining,
                "precedents_required": precedents_required,
                "precedents_earned": precedents_earned,
                "precedents_milestones_total": precedents_milestones,
                "expected_remaining_from_precedents": expected_remaining,
                "ledger_remaining": ledger_remaining,
                "ledger_structural_points": ledger_structural,
                "ledger_recovery_events": recovery_event_count,
            },
            "governance_checks": {
                "required_aligned": required_aligned,
                "remaining_aligned": remaining_aligned,
                "governance_consistent": governance_consistent,
            },
            "policy_basis_audit": policy_basis_audit,
            "reference_assertion_audit": reference_assertion_audit,
            "evidence_packet_audit": evidence_packet_audit,
            "wptg_anchors": wptg_anchor_checks,
            "wip_anchors": wip_anchor_checks,
            "tribunal_chain_audit": tribunal_chain_audit,
            "markdown_links": markdown_links,
            "broken_local_link_count": len(broken_links),
            "telemetry_summary": {
                **summary,
                "top_script": _run_top_candidate(latest_run),
                "anomalies": anomalies,
            },
        },
        "prerequisites": {
            "governance_consistent": governance_consistent,
            "evidence_links_intact": evidence_links_intact,
            "policy_basis_integrity": policy_basis_audit["strict_pass"],
            "reference_assertions_intact": reference_assertion_audit["strict_pass"],
            "evidence_packet_complete": evidence_packet_audit["complete"],
            "tribunal_chain_present": tribunal_chain_audit["all_present"],
            "doctrine_present": doctrine_present,
            "baseline_present": baseline_present,
            "telemetry_present": telemetry_present,
            "telemetry_hardening_needed": telemetry_hardening_needed,
        },
        "repair_queue": repair_queue,
        "iterative_plan": iterative_plan,
        "milestones": milestones,
        "conceptualize_bridge": {
            "status": "enabled" if readiness == "READY" else "blocked",
            "message": (
                "Run conceptual analysis on top of this report only after blockers are cleared."
                if readiness != "READY"
                else "Prerequisites satisfied; conceptual pass may proceed."
            ),
        },
    }


def _to_markdown(report: dict[str, object]) -> str:
    prerequisites = report["prerequisites"]
    evidence = report["evidence"]
    telemetry = evidence["telemetry_summary"]
    numbers = evidence["governance_numbers"]
    blockers = report["blockers"]

    def _flag(value: bool) -> str:
        return "PASS" if value else "FAIL"

    lines = [
        f"# Codekiller Remediation Prerequisite Report ({report['case_id']})",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Readiness: `{report['readiness']}`",
        "",
        "## Prerequisites",
        "",
        f"- Governance consistency: `{_flag(prerequisites['governance_consistent'])}`",
        f"- Evidence links intact: `{_flag(prerequisites['evidence_links_intact'])}`",
        f"- Policy basis integrity: `{_flag(prerequisites['policy_basis_integrity'])}`",
        f"- Frontmatter reference assertions intact: `{_flag(prerequisites['reference_assertions_intact'])}`",
        f"- Evidence packet complete: `{_flag(prerequisites['evidence_packet_complete'])}`",
        f"- Tribunal chain present: `{_flag(prerequisites['tribunal_chain_present'])}`",
        f"- WPTG doctrine anchors present: `{_flag(prerequisites['doctrine_present'])}`",
        f"- WIP baseline anchors present: `{_flag(prerequisites['baseline_present'])}`",
        f"- Telemetry baseline present: `{_flag(prerequisites['telemetry_present'])}`",
        f"- Telemetry hardening needed: `{_flag(not prerequisites['telemetry_hardening_needed'])}`",
        "",
        "## Governance Numbers",
        "",
        f"- points_required: `{numbers['points_required']}`",
        f"- points_remaining: `{numbers['points_remaining']}`",
        f"- precedents_required: `{numbers['precedents_required']}`",
        f"- precedents_earned: `{numbers['precedents_earned']}`",
        f"- expected_remaining_from_precedents: `{numbers['expected_remaining_from_precedents']}`",
        f"- ledger_remaining: `{numbers['ledger_remaining']}`",
        f"- ledger_recovery_events: `{numbers['ledger_recovery_events']}`",
        "",
        "## Telemetry Snapshot",
        "",
        f"- files_scanned: `{telemetry['files_scanned']}`",
        f"- todo_hits: `{telemetry['todo_hits']}`",
        f"- top_candidates: `{telemetry['top_candidates']}`",
        f"- top_script: `{telemetry['top_script']}`",
        f"- anomalies: `{json.dumps(telemetry['anomalies'], ensure_ascii=False)}`",
    ]

    lines.extend(
        [
            "",
            "## Policy Basis Audit",
            "",
        ]
    )

    for entry in evidence["policy_basis_audit"]["entries"]:
        lines.append(
            f"- `{entry['status']}` {entry['entry']} -> path=`{entry['resolved_path']}` line=`{entry['line']}` notes=`{','.join(entry['notes'])}`"
        )

    lines.extend(
        [
            "",
            "## Reference Assertion Audit",
            "",
        ]
    )

    for entry in evidence["reference_assertion_audit"]["entries"]:
        overlap = entry["token_overlap"]
        overlap_text = "n/a" if overlap is None else f"{overlap:.2f}"
        lines.append(
            f"- `{entry['status']}` {entry['anchor']} (line={entry['line']}, overlap={overlap_text}) notes=`{','.join(entry['notes'])}`"
        )

    packet = evidence["evidence_packet_audit"]
    lines.extend(
        [
            "",
            "## Evidence Packet Audit",
            "",
            f"- files_changed_claim: `{packet['files_changed_claim']}`",
            f"- lines_added_claim: `{packet['lines_added_claim']}`",
            f"- lines_deleted_claim: `{packet['lines_deleted_claim']}`",
            f"- named_fence_headers: `{packet['named_fence_headers']}`",
            f"- completeness: `{_flag(packet['complete'])}`",
            "",
            "## Tribunal Chain Audit",
            "",
        ]
    )

    for entry in evidence["tribunal_chain_audit"]["entries"]:
        lines.append(f"- `{_flag(entry['exists'])}` {entry['path']}")

    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )

    if blockers:
        lines.extend([f"- {entry}" for entry in blockers])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Repair Queue",
            "",
        ]
    )

    if report["repair_queue"]:
        for item in report["repair_queue"]:
            lines.append(
                f"- {item['priority']} `{item['id']}`: {item['reason']} (targets: {', '.join(item['targets'])})"
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Iterative Plan",
            "",
        ]
    )

    for loop in report["iterative_plan"]:
        lines.append(
            f"- Loop {loop['loop']} - {loop['title']}: {loop['objective']} "
            f"(Exit: {loop['exit_criteria']})"
        )

    lines.extend(
        [
            "",
            "## Milestones",
            "",
        ]
    )

    for milestone in report["milestones"]:
        lines.append(
            f"- {milestone['name']} (+{milestone['points_candidate']}): {milestone['evidence_type']}"
        )

    return "\n".join(lines) + "\n"


def _selftest() -> int:
    sample_markdown = """---
policy_basis:
  - .github/copilot-instructions.md:44
  - readme.md (in this folder)
references:
  - .github/copilot-instructions.md:44 — "Every file is gold."
---

Body
9 files changed
+10
-20
```json : file1
{}
```
```ts : file2
x
```
"""

    sample_points = """
recovery_required: 20 (structural earning)
recovery_remaining: 20
"""
    sample_precedents = """
required: 20
earned: 0
milestones_total: 4
"""
    sample_ledger = """
codex:
  structural: 7
  status: custody
  active_cases:
    - case_id: "CODEKILLER_2024_06_01"
      recovery_remaining: 10
"""
    assert _first_int(r"recovery_required:\s+(\d+)", sample_points) == 20
    assert _first_int(r"required:\s+(\d+)", sample_precedents) == 20
    assert _first_int(r"earned:\s+(\d+)", sample_precedents) == 0
    assert _first_int(r"codex:.*?structural:\s+(\d+)", sample_ledger, flags=re.DOTALL) == 7
    assert _first_int(r"recovery_remaining:\s+(\d+)", sample_ledger) == 10
    assert _resolve_file_uri("file:///C:/repo/file.md") is not None
    assert _extract_frontmatter(sample_markdown) != ""
    assert _extract_list_section(_extract_frontmatter(sample_markdown), "policy_basis")[0] == ".github/copilot-instructions.md:44"
    assert _token_overlap_score("Every file is gold.", "Default axiom: every file is gold") > 0.50
    packet = _audit_evidence_packet(sample_markdown)
    assert packet["files_changed_claim"] == 9
    assert packet["complete"] is False
    print("selftest: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prerequisite gate and iterative planner for Codekiller remediation."
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Repository root path (default: current directory).",
    )
    parser.add_argument(
        "--emit-json",
        type=str,
        help="Write JSON report to this path.",
    )
    parser.add_argument(
        "--emit-md",
        type=str,
        help="Write Markdown summary to this path.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run built-in self-test and exit.",
    )

    args = parser.parse_args()
    if args.selftest:
        return _selftest()

    repo_root = Path(args.repo_root).resolve()
    report = _build_report(repo_root)
    payload_json = json.dumps(report, indent=2, ensure_ascii=False)

    if args.emit_json:
        json_path = Path(args.emit_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(payload_json + "\n", encoding="utf-8")
    else:
        print(payload_json)

    if args.emit_md:
        md_path = Path(args.emit_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_to_markdown(report), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
