#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: server.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🏛️ THE HYPOSTYLE
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ mas_mcp/logic/governance.py
# ║   └─◄ mas_mcp/lib/gpu_probe.py
# ╚════════════════════════════════════════════════════════════════════════════

"""
server.py — M-P-W Router Server (Modularized).

@SID:           SERVER_MPW_ROUTER_V1
@Shabti:        Router
@Purpose:       Core MAS MCP gateway server. Routes entity analysis,
                governance policy, narrative drift, qualia alignment,
                and GPU probing via FastMCP.
"""

import logging
import sys
from pathlib import Path
from fastmcp import FastMCP

from mas_mcp.logic.resonance import ArchiveVault, LexiconFilter
from mas_mcp.logic.tools import (
    mas_scan_logic, mas_entity_deep_logic, mas_pulse_logic,
    mas_narrative_scan_logic, mas_qualia_check_logic,
    mas_validate_entity_logic
)
from mas_mcp.gpu_orchestrator import (
    mas_gpu_batch_score,
    mas_gpu_score,
    mas_gpu_status,
)
from mas_mcp.logic.pid_reader import mas_pid_reader_logic
from mas_mcp.logic.governance import policy_check_logic
from mas_mcp.logic.ssot_binding import (
    resolve_ssot, resolve_ssot_for_lexicon,
    init_session_bookend, check_session_bookend,
    compute_ssot_vitals,
    read_journal_tail,
)
from mas_mcp.logic.ssot_manifest import SSOT_PROTO_RELPATH
from mas_mcp.lib.gpu_probe import probe_gpu_capabilities

# Config
PROJECT_ROOT = Path(__file__).parent.parent

# Allow scripts/ imports (link_audit, scm_triage) to resolve from repo root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.link_audit import build_collision_index, audit_file, scan_repo_markdown
from scripts.scm_triage import audit as scm_audit, generate_fix_recommendations, suppress_noise
ARCHIVE_PATH = Path(__file__).parent / "archive_vault.json"
SSOT_PATH, SSOT_ARCHIVE_PATH = resolve_ssot(PROJECT_ROOT)
SSOT_LEXICON_PATH = resolve_ssot_for_lexicon(PROJECT_ROOT)
MPW_SOURCE = PROJECT_ROOT / SSOT_PROTO_RELPATH

logger = logging.getLogger("mas-mcp")

mcp = FastMCP("mas-mcp", instructions="MAS - Metadata-Persistence-Workspace")
VAULT = ArchiveVault(ARCHIVE_PATH)
LEXICON = LexiconFilter()

# Bookend: stamp SSOT vitals at server startup for session drift detection + journal
if SSOT_PATH.exists():
    _session_start_hash = init_session_bookend(SSOT_PATH, project_root=PROJECT_ROOT, source_kind="pointer")
    logger.debug("SSOT bookend stamped: %s...", _session_start_hash[:16])

@mcp.tool()
def mas_narrative_scan(target: str = "."):
    """Calculates Cultural Drift against the SSOT Lexicon."""
    result = mas_narrative_scan_logic(target, PROJECT_ROOT, SSOT_LEXICON_PATH)
    if SSOT_LEXICON_PATH.exists():
        vitals = compute_ssot_vitals(SSOT_LEXICON_PATH, source_kind="archive")
        result["ssot_hash"] = vitals["sha256"][:16]
        result["ssot_fingerprint"] = vitals["fingerprint"]
        result["ssot_source_kind"] = vitals["source_kind"]
    else:
        result["ssot_hash"] = None
        result["ssot_fingerprint"] = None
        result["ssot_source_kind"] = None
    return result

@mcp.tool()
def mas_qualia_check(target: str):
    """Vets a text block or directory for canonical alignment (Phase 3 Gate)."""
    return mas_qualia_check_logic(target, PROJECT_ROOT)

@mcp.tool()
def mas_scan(target: str = "."):
    """Scan files for lexicon impulses, entity drift, and canonical alignment signals."""
    result = mas_scan_logic(target, PROJECT_ROOT, LEXICON)
    if SSOT_PATH.exists():
        vitals = compute_ssot_vitals(SSOT_PATH, source_kind="pointer")
        result["ssot_hash"] = vitals["sha256"][:16]
        result["ssot_fingerprint"] = vitals["fingerprint"]
        result["ssot_source_kind"] = vitals["source_kind"]
    else:
        result["ssot_hash"] = None
        result["ssot_fingerprint"] = None
        result["ssot_source_kind"] = None
    return result

@mcp.tool()
def mas_pulse():
    """Report session pulse: entity status, drift alerts, MPW fingerprint, SSOT bookend integrity, journal timeline, and recommendations."""
    pulse = mas_pulse_logic(VAULT, MPW_SOURCE, LEXICON)
    pulse["ssot_bookend"] = check_session_bookend()
    pulse["ssot_journal"] = read_journal_tail(PROJECT_ROOT, n=5)
    return pulse

@mcp.tool()
def mas_gpu_probe():
    """Probe GPU capabilities: CUDA version, VRAM, driver, and compute features."""
    return probe_gpu_capabilities().to_dict()

@mcp.tool()
def mas_entity_deep(entity_name: str, context_lines: int = 5):
    """Deep-scan the archive for a named entity: proximity mentions, consolidated metrics, and cross-file analysis."""
    return mas_entity_deep_logic(entity_name, context_lines, PROJECT_ROOT)

@mcp.tool()
def mas_validate_entity(entity_name: str, expected_whr: float = None, expected_tier: int = None, expected_cup: str = None):
    """Validate an entity against expected metrics. Records fractures on mismatch, seals truths on full match."""
    return mas_validate_entity_logic(entity_name, expected_whr, expected_tier, expected_cup, PROJECT_ROOT, VAULT)

@mcp.tool()
def mas_discover_unknown(target: str = "."):
    """
    Compatibility discovery tool for the documented MAS surface.

    The current scan logic only enumerates known ENTITY impulses, so this shim
    returns the scan-derived entity list as potential candidates. That keeps the
    advertised tool available while the deeper unknown-discovery heuristic is
    reintroduced.
    """
    result = mas_scan_logic(target, PROJECT_ROOT, LEXICON)
    entities = list(result.get("entities", {}).values())
    return {
        "target": target,
        "total_candidates": len(entities),
        "potential_entities": entities,
        "scan_metadata": result.get("scan_metadata", {}),
    }

@mcp.tool()
def mas_policy_check(code: str):
    """Security policy gate: scan code for prohibited or guarded patterns (exec, eval, rm -rf, etc). Returns risk band."""
    return policy_check_logic(code)


@mcp.tool()
def mas_link_audit(target: str = "."):
    """Audit markdown link health: broken refs, ambiguous paths, basename collisions. Pass a file path or '.' for full repo scan."""
    collision_index = build_collision_index(PROJECT_ROOT)
    if target == ".":
        md_files = scan_repo_markdown(PROJECT_ROOT)
        results = []
        totals = {"total_links": 0, "ok": 0, "broken": 0, "ambiguous": 0}
        for f in md_files:
            r = audit_file(f, PROJECT_ROOT, collision_index)
            totals["total_links"] += r["total_links"]
            totals["ok"] += r["ok"]
            totals["broken"] += r["broken"]
            totals["ambiguous"] += r["ambiguous"]
            if r["issues"]:
                results.append({"file": str(f.relative_to(PROJECT_ROOT)), "issues": r["issues"]})
        return {**totals, "files_scanned": len(md_files), "files_with_issues": results}
    else:
        file_path = Path(target) if Path(target).is_absolute() else PROJECT_ROOT / target
        r = audit_file(file_path, PROJECT_ROOT, collision_index)
        # Strip verbose 'all' list — MCP consumers only need stats + issues
        r.pop("all", None)
        return r


@mcp.tool()
def mas_workspace_health():
    """Root directory health audit: file hygiene, redundancy, versioning issues, and cleanup candidates."""
    # Lazy import — rootdir_health_audit hijacks sys.stdout on import (Windows UTF-8 shim)
    # which would break FastMCP's stdio transport if loaded at module level.
    from scripts.rootdir_health_audit import scan_directory, analyze_files, generate_json_report
    import json as _json
    files = scan_directory(PROJECT_ROOT)
    report = analyze_files(files)
    return _json.loads(generate_json_report(report))


@mcp.tool()
def mas_scm_triage():
    """Git working-tree triage: classify changes as signal/noise/ghost/mailbox, generate gitignore and cleanup recommendations."""
    result = scm_audit(PROJECT_ROOT, logger)
    recommendations = generate_fix_recommendations(result)
    return {"audit": result, "recommendations": recommendations}


@mcp.tool()
def mas_scm_suppress(dry_run: bool = True):
    """Apply noise suppression from scm_triage results: append patterns to .gitignore, skip-worktree ghosts. Set dry_run=False to execute."""
    result = scm_audit(PROJECT_ROOT, logger)
    recommendations = generate_fix_recommendations(result)
    suppression = suppress_noise(PROJECT_ROOT, recommendations, dry_run=dry_run)
    return {"triage_summary": result["by_classification"], "suppression": suppression}


@mcp.tool()
def mas_pid_reader(
    last: int = 20,
    sid: str = None,
    pid: int = None,
    failed_only: bool = False,
    summary_only: bool = False,
    cwd_filter: str = None,
):
    """
    Read the terminal session manifest (manifest/terminal_session.jsonl) produced by
    chthonic-shell-hook.ps1 (PID reader). Returns structured, machine-readable session
    data: command history, exit codes, durations, session metadata, and aggregate stats.

    Use for: documentation supplementation, session archaeology, failure triage,
    CI gate data, cross-session command audit.

    Parameters:
      last        — last N completed commands (default 20)
      sid         — filter by session ID (8-char hex, e.g. '964b4806')
      pid         — filter by process PID
      failed_only — return only failed commands (exit_code != 0)
      summary_only — return stats + active sessions only, no entries
      cwd_filter  — substring filter on working directory path
    """
    return mas_pid_reader_logic(
        PROJECT_ROOT,
        last=last,
        sid=sid,
        pid=pid,
        failed_only=failed_only,
        summary_only=summary_only,
        cwd_filter=cwd_filter,
    )


def main():
    # Clamp third-party loggers for quiet stdio transport
    for name in ("fastmcp", "mcp", "docket", "pydocket"):
        logging.getLogger(name).setLevel(logging.WARNING)
    mcp.run(transport="stdio", log_level="ERROR", show_banner=False)

if __name__ == "__main__":
    main()
