#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
VS Code Error Autopsy — Electron/Node fragility classifier and severity scorer.

Ingests VS Code Insiders logs (Window.log, Extension Host, --status output, matrix
reports, stderr captures) and classifies every error into a fragility category.
Each error gets a severity score and root-cause annotation. Outputs structured
JSON + Markdown reports for triage and hardening decisions.

Code patterns recycled from (WPTG provenance):
- skill_health.py    → classification engine, regex-based scoring, dual JSON+MD output
- scm_triage.py      → line-by-line pattern matching, severity ranking
- vscode_terminal_crash_doctor.ps1 → crash signature patterns, log collection paths
- vscode_insiders_matrix.ps1       → stability scoring formula (100 - crash*25 - gpu*2)

@SID:           TOOL_VSCODE_ERROR_AUTOPSY_V1
@Type:          Utility
@Context:       Infrastructure / VS Code Stability
@Implements:    Electron/Node fragility diagnosis (CHTHONIC-GOLDEN-PHASE-1)

Usage:
    uv run scripts/vscode_error_autopsy.py                        # auto-discover logs, full report
    uv run scripts/vscode_error_autopsy.py --json                 # emit JSON report
    uv run scripts/vscode_error_autopsy.py --md                   # emit markdown report
    uv run scripts/vscode_error_autopsy.py --logs-dir debugging_data
    uv run scripts/vscode_error_autopsy.py --matrix-dir codex/mailbox/VSCODE_INSIDERS_MATRIX_*
    uv run scripts/vscode_error_autopsy.py --severity high        # filter by severity
    uv run scripts/vscode_error_autopsy.py --category gpu         # filter by category
    uv run scripts/vscode_error_autopsy.py --emit claude/mailbox/VSCODE_ERROR_AUTOPSY_LATEST.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants & Classification Rules
# =============================================================================

# Severity levels (descending)
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_INFO = "INFO"

SEVERITY_RANK = {
    SEVERITY_CRITICAL: 5,
    SEVERITY_HIGH: 4,
    SEVERITY_MEDIUM: 3,
    SEVERITY_LOW: 2,
    SEVERITY_INFO: 1,
}


@dataclass
class ErrorPattern:
    """A compiled error detection pattern with classification metadata."""
    name: str
    category: str
    severity: str
    pattern: re.Pattern[str]
    root_cause: str
    remediation: str
    dedupe_key: str = ""  # for collapsing repeated identical errors

    def __post_init__(self):
        if not self.dedupe_key:
            self.dedupe_key = self.name


# Error detection patterns — ordered by severity (critical first)
ERROR_PATTERNS: list[ErrorPattern] = [
    # === GPU / Electron Renderer ===
    ErrorPattern(
        name="shared_image_manager_produce_memory",
        category="GPU",
        severity=SEVERITY_HIGH,
        pattern=re.compile(
            r"SharedImageManager::ProduceMemory.*non-existent mailbox",
            re.IGNORECASE,
        ),
        root_cause="Chromium GPU command buffer referencing destroyed shared image mailbox. "
                    "Indicates GPU process instability or software rendering fallback.",
        remediation="For crash containment, first run with --disable-gpu and terminal GPU off. "
                     "After stability returns, test hardware acceleration with updated GPU drivers.",
    ),
    ErrorPattern(
        name="gpu_all_disabled",
        category="GPU",
        severity=SEVERITY_HIGH,
        pattern=re.compile(
            r"(unavailable_software|disabled_software).*?(gpu_compositing|webgl|2d_canvas|webgpu)",
            re.IGNORECASE,
        ),
        root_cause="All hardware GPU features disabled. Running on SwiftShader (software Vulkan). "
                    "Causes high CPU usage, UI lag, and renderer instability.",
        remediation="Check GPU driver status. Create/edit argv.json with "
                     '"enable-proposed-api" and GPU flags. Run with --disable-gpu to isolate.',
    ),
    ErrorPattern(
        name="swiftshader_active",
        category="GPU",
        severity=SEVERITY_MEDIUM,
        pattern=re.compile(r"SwiftShader", re.IGNORECASE),
        root_cause="Software Vulkan renderer active instead of hardware GPU. "
                    "Performance degradation and increased crash risk.",
        remediation="If crashes persist, keep software-safe mode (--disable-gpu) until stable. "
                     "Then validate hardware path via driver updates and controlled re-enable.",
    ),
    ErrorPattern(
        name="renderer_process_gone",
        category="GPU",
        severity=SEVERITY_CRITICAL,
        pattern=re.compile(r"renderer process gone|reason:\s*crashed", re.IGNORECASE),
        root_cause="Electron renderer process crashed. Window becomes unresponsive.",
        remediation="Collect crash dump from %TEMP%/Electron Crashes. "
                     "Disable GPU acceleration as workaround. Report to VS Code issues.",
    ),

    # === Extension Host ===
    ErrorPattern(
        name="chat_participant_not_declared",
        category="EXTHOST",
        severity=SEVERITY_MEDIUM,
        pattern=re.compile(
            r"chatParticipant must be declared in package\.json:\s*(\S+)",
            re.IGNORECASE,
        ),
        root_cause="Extension tries to register a chat participant not declared in its package.json. "
                    "Typically claude-code or similar AI extensions with incomplete manifest.",
        remediation="Update extension or wait for publisher fix. "
                     "Disable the extension if it causes instability.",
    ),
    ErrorPattern(
        name="extension_activation_failed",
        category="EXTHOST",
        severity=SEVERITY_HIGH,
        pattern=re.compile(
            r"Activating extension .+ failed",
            re.IGNORECASE,
        ),
        root_cause="Extension failed to activate. May block dependent features.",
        remediation="Check extension host log for stack trace. "
                     "Reinstall the extension or report to publisher.",
    ),
    ErrorPattern(
        name="deprecated_module",
        category="EXTHOST",
        severity=SEVERITY_LOW,
        pattern=re.compile(
            r"DeprecationWarning.*(?:punycode|buffer|url|querystring|domain)",
            re.IGNORECASE,
        ),
        root_cause="Node.js deprecated module used by extension or VS Code itself.",
        remediation="Informational only. Will break in future Node.js versions.",
    ),
    ErrorPattern(
        name="experimental_feature_warning",
        category="EXTHOST",
        severity=SEVERITY_INFO,
        pattern=re.compile(r"experimental feature", re.IGNORECASE),
        root_cause="Extension using experimental API/feature.",
        remediation="Informational. Monitor for breakage on updates.",
    ),

    # === Memory / Listener Leaks ===
    ErrorPattern(
        name="listener_leak",
        category="MEMORY",
        severity=SEVERITY_HIGH,
        pattern=re.compile(
            r"potential listener LEAK detected.*?having (\d+) listeners",
            re.IGNORECASE,
        ),
        root_cause="Event emitter accumulating listeners without cleanup. "
                    "Causes memory growth and eventual slowdown.",
        remediation="Identify the emitter source from stack trace. "
                     "If VS Code internal, report upstream. If extension, file bug.",
    ),
    ErrorPattern(
        name="memory_pressure",
        category="MEMORY",
        severity=SEVERITY_MEDIUM,
        pattern=re.compile(
            r"(out of memory|heap limit|allocation failed|FATAL ERROR.*heap)",
            re.IGNORECASE,
        ),
        root_cause="V8 heap exhausted. Extension or operation consuming too much memory.",
        remediation="Increase --max-old-space-size in argv.json. "
                     "Profile with --inspect-extensions to find the leak.",
    ),

    # === PTY / Terminal Host ===
    ErrorPattern(
        name="pty_host_exit",
        category="PTY",
        severity=SEVERITY_CRITICAL,
        pattern=re.compile(
            r"pty[\s-]host (exited|terminated|crashed)",
            re.IGNORECASE,
        ),
        root_cause="PTY host process died. All terminals become unresponsive.",
        remediation="Check for ACCESS_VIOLATION in logs. "
                     "Disable terminal GPU accel: terminal.integrated.gpuAcceleration=off.",
    ),
    ErrorPattern(
        name="terminal_exit_access_violation",
        category="PTY",
        severity=SEVERITY_CRITICAL,
        pattern=re.compile(
            r"terminated with exit code -1073741819",
            re.IGNORECASE,
        ),
        root_cause="Terminal process crashed with STATUS_ACCESS_VIOLATION (0xC0000005). "
                    "Commonly tied to native crash in pwsh/electron host/driver boundary.",
        remediation="Use -NoProfile terminal launch, keep terminal GPU acceleration off, "
                     "and isolate extensions with --disable-extensions for crash triage.",
    ),
    ErrorPattern(
        name="shell_integration_timeout",
        category="PTY",
        severity=SEVERITY_MEDIUM,
        pattern=re.compile(
            r"_waitForShellIntegration.*?Timed out (\d+)ms",
            re.IGNORECASE,
        ),
        root_cause="Shell integration handshake exceeded timeout. "
                    "First terminal after startup is slow due to profile loading.",
        remediation="Use -NoProfile for PowerShell terminals during triage. "
                     "Increase terminal integration timeout if available.",
    ),
    ErrorPattern(
        name="conpty_error",
        category="PTY",
        severity=SEVERITY_HIGH,
        pattern=re.compile(r"conpty.*?(error|fail|crash|exception)", re.IGNORECASE),
        root_cause="Windows ConPTY subsystem error. May cause terminal rendering issues.",
        remediation="Update Windows. Check terminal.integrated.windowsEnableConpty setting.",
    ),

    # === Network / CDN ===
    ErrorPattern(
        name="embeddings_cdn_404",
        category="NETWORK",
        severity=SEVERITY_LOW,
        pattern=re.compile(
            r"Failed to fetch remote embeddings cache",
            re.IGNORECASE,
        ),
        root_cause="Embeddings CDN returned 404. Version mismatch between client and CDN.",
        remediation="Self-resolving on next Insiders update. Informational only.",
    ),
    ErrorPattern(
        name="network_fetch_error",
        category="NETWORK",
        severity=SEVERITY_LOW,
        pattern=re.compile(
            r"(ECONNREFUSED|ENOTFOUND|ETIMEDOUT|ERR_NETWORK|fetch failed)",
            re.IGNORECASE,
        ),
        root_cause="Network connectivity issue. Extension or telemetry endpoint unreachable.",
        remediation="Check network/proxy settings. Typically transient.",
    ),

    # === UI / Renderer Crashes ===
    ErrorPattern(
        name="type_error_null_ref",
        category="UI",
        severity=SEVERITY_HIGH,
        pattern=re.compile(
            r"TypeError: Cannot read propert(?:y|ies) of (?:undefined|null)",
            re.IGNORECASE,
        ),
        root_cause="Null reference in UI renderer. Component accessed before initialization.",
        remediation="Report to VS Code issues with full stack trace. "
                     "May be triggered by specific chat/editor operations.",
    ),
    ErrorPattern(
        name="unhandled_rejection",
        category="UI",
        severity=SEVERITY_MEDIUM,
        pattern=re.compile(
            r"(UnhandledPromiseRejection|unhandled rejection)",
            re.IGNORECASE,
        ),
        root_cause="Async operation failed without catch handler.",
        remediation="Check stack trace for originating extension or VS Code module.",
    ),

    # === Access Violation / Crash Dump ===
    ErrorPattern(
        name="access_violation",
        category="CRASH",
        severity=SEVERITY_CRITICAL,
        pattern=re.compile(
            r"(0xC0000005|STATUS_ACCESS_VIOLATION|access violation)",
            re.IGNORECASE,
        ),
        root_cause="Native code access violation. Typically in GPU driver, Node native addon, "
                    "or Electron/Chromium native code.",
        remediation="Collect crash dumps. Disable GPU. Update native extensions. "
                     "Check for corrupt user-data-dir.",
    ),
    ErrorPattern(
        name="segfault",
        category="CRASH",
        severity=SEVERITY_CRITICAL,
        pattern=re.compile(r"(SIGSEGV|segmentation fault)", re.IGNORECASE),
        root_cause="Segmentation fault in native code.",
        remediation="Collect core dump. Likely GPU driver or native extension issue.",
    ),
]


@dataclass
class ClassifiedError:
    """A single classified error occurrence."""
    pattern_name: str
    category: str
    severity: str
    root_cause: str
    remediation: str
    source_file: str
    line_number: int
    raw_line: str
    match_text: str

    @property
    def severity_rank(self) -> int:
        return SEVERITY_RANK.get(self.severity, 0)


@dataclass
class AutopsyReport:
    """Full autopsy report aggregating all classified errors."""
    generated_utc: str = ""
    repo_root: str = ""
    log_sources: list[str] = field(default_factory=list)
    errors: list[ClassifiedError] = field(default_factory=list)
    category_summary: dict[str, int] = field(default_factory=dict)
    severity_summary: dict[str, int] = field(default_factory=dict)
    stability_score: int = 100
    top_remediations: list[str] = field(default_factory=list)
    deduped_count: int = 0
    total_lines_scanned: int = 0

    def compute_summaries(self):
        """Compute aggregate summaries from classified errors."""
        self.category_summary = {}
        self.severity_summary = {}
        for err in self.errors:
            self.category_summary[err.category] = self.category_summary.get(err.category, 0) + 1
            self.severity_summary[err.severity] = self.severity_summary.get(err.severity, 0) + 1

        # Stability score: 100 - (critical*25 + high*10 + medium*3 + low*1)
        crit = self.severity_summary.get(SEVERITY_CRITICAL, 0)
        high = self.severity_summary.get(SEVERITY_HIGH, 0)
        med = self.severity_summary.get(SEVERITY_MEDIUM, 0)
        low = self.severity_summary.get(SEVERITY_LOW, 0)
        self.stability_score = max(0, 100 - (crit * 25) - (high * 10) - (med * 3) - (low * 1))

        # Top remediations: unique, ordered by severity
        seen_remediations: set[str] = set()
        sorted_errors = sorted(self.errors, key=lambda e: -e.severity_rank)
        for err in sorted_errors:
            if err.remediation not in seen_remediations:
                seen_remediations.add(err.remediation)
                self.top_remediations.append(
                    f"[{err.severity}] {err.category}/{err.pattern_name}: {err.remediation}"
                )
            if len(self.top_remediations) >= 10:
                break


# =============================================================================
# Log Discovery
# =============================================================================

# Well-known log locations relative to repo root
KNOWN_LOG_DIRS = [
    "debugging_data",
    "logs",
]

# Well-known matrix/triage output dirs
KNOWN_MAILBOX_PATTERNS = [
    "codex/mailbox/VSCODE_INSIDERS_MATRIX_*",
    "codex/mailbox/VSCODE_TERMINAL_TRIAGE_*",
]

# Insiders logs in AppData
INSIDERS_LOGS_DIR = Path(os.environ.get("APPDATA", "")) / "Code - Insiders" / "logs"


def discover_log_files(
    repo: Path,
    extra_dirs: list[Path] | None = None,
    include_defaults: bool = True,
) -> list[Path]:
    """Auto-discover all log files relevant to VS Code error autopsy."""
    files: list[Path] = []

    if include_defaults:
        # Repo-local log dirs
        for d in KNOWN_LOG_DIRS:
            log_dir = repo / d
            if log_dir.is_dir():
                for f in log_dir.rglob("*.log"):
                    files.append(f)

        # Matrix/triage mailbox outputs
        import glob
        for pattern in KNOWN_MAILBOX_PATTERNS:
            for match_dir in glob.glob(str(repo / pattern)):
                mp = Path(match_dir)
                if mp.is_dir():
                    for f in mp.rglob("*.log"):
                        files.append(f)
                    for f in mp.rglob("*.err.log"):
                        files.append(f)

    # Extra user-specified dirs
    if extra_dirs:
        for d in extra_dirs:
            if d.is_dir():
                for f in d.rglob("*.log"):
                    files.append(f)
            elif d.is_file():
                files.append(d)

    if include_defaults:
        # Insiders AppData logs (latest session only)
        if INSIDERS_LOGS_DIR.is_dir():
            session_dirs = sorted(
                INSIDERS_LOGS_DIR.iterdir(),
                key=lambda p: p.stat().st_mtime if p.is_dir() else 0,
                reverse=True,
            )
            if session_dirs:
                latest = session_dirs[0]
                for f in latest.rglob("*.log"):
                    files.append(f)

    # Deduplicate by resolved path
    seen: set[str] = set()
    deduped: list[Path] = []
    for f in files:
        key = str(f.resolve())
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return sorted(deduped)


# =============================================================================
# Classification Engine
# =============================================================================

def classify_file(filepath: Path, patterns: list[ErrorPattern]) -> tuple[list[ClassifiedError], int]:
    """
    Scan a single log file and classify every matching line.

    Returns:
        Tuple of (classified errors, total lines scanned)
    """
    errors: list[ClassifiedError] = []
    lines_scanned = 0

    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return errors, 0

    for line_num, line in enumerate(text.splitlines(), 1):
        lines_scanned += 1
        for pat in patterns:
            m = pat.pattern.search(line)
            if m:
                errors.append(ClassifiedError(
                    pattern_name=pat.name,
                    category=pat.category,
                    severity=pat.severity,
                    root_cause=pat.root_cause,
                    remediation=pat.remediation,
                    source_file=str(filepath),
                    line_number=line_num,
                    raw_line=line.strip()[:500],  # truncate very long lines
                    match_text=m.group(0)[:200],
                ))
                break  # first matching pattern wins per line

    return errors, lines_scanned


def deduplicate_errors(errors: list[ClassifiedError]) -> tuple[list[ClassifiedError], int]:
    """
    Collapse repeated identical errors, keeping the first occurrence.

    Returns:
        Tuple of (deduped errors, number of duplicates removed)
    """
    seen: dict[str, ClassifiedError] = {}
    counts: dict[str, int] = {}

    for err in errors:
        key = f"{err.pattern_name}|{err.source_file}"
        if key not in seen:
            seen[key] = err
            counts[key] = 1
        else:
            counts[key] += 1

    deduped = list(seen.values())
    total_removed = sum(c - 1 for c in counts.values())
    return deduped, total_removed


# =============================================================================
# Output Formatters
# =============================================================================

def report_to_dict(report: AutopsyReport) -> dict:
    """Convert report to JSON-serializable dict."""
    return {
        "schema_version": 1,
        "generated_utc": report.generated_utc,
        "repo_root": report.repo_root,
        "stability_score": report.stability_score,
        "total_lines_scanned": report.total_lines_scanned,
        "total_errors": len(report.errors),
        "deduped_count": report.deduped_count,
        "log_sources": report.log_sources,
        "category_summary": report.category_summary,
        "severity_summary": report.severity_summary,
        "top_remediations": report.top_remediations,
        "errors": [asdict(e) for e in report.errors],
    }


def report_to_markdown(report: AutopsyReport) -> str:
    """Convert report to markdown for human consumption."""
    lines: list[str] = []
    lines.append("# VS Code Error Autopsy Report")
    lines.append("")
    lines.append(f"- **Generated (UTC):** {report.generated_utc}")
    lines.append(f"- **Stability Score:** {report.stability_score}/100")
    lines.append(f"- **Total Lines Scanned:** {report.total_lines_scanned:,}")
    lines.append(f"- **Total Errors (deduped):** {len(report.errors)}")
    lines.append(f"- **Duplicates Collapsed:** {report.deduped_count}")
    lines.append(f"- **Log Sources:** {len(report.log_sources)}")
    lines.append("")

    # Severity summary
    lines.append("## Severity Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---:|")
    for sev in [SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO]:
        count = report.severity_summary.get(sev, 0)
        if count > 0:
            lines.append(f"| {sev} | {count} |")
    lines.append("")

    # Category summary
    lines.append("## Category Summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for cat, count in sorted(report.category_summary.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {count} |")
    lines.append("")

    # Top remediations
    if report.top_remediations:
        lines.append("## Top Remediations (Priority Order)")
        lines.append("")
        for i, rem in enumerate(report.top_remediations, 1):
            lines.append(f"{i}. {rem}")
        lines.append("")

    # Error details
    lines.append("## Error Details")
    lines.append("")
    for err in sorted(report.errors, key=lambda e: -e.severity_rank):
        lines.append(f"### [{err.severity}] {err.category}/{err.pattern_name}")
        lines.append(f"- **Source:** `{err.source_file}` L{err.line_number}")
        lines.append(f"- **Match:** `{err.match_text}`")
        lines.append(f"- **Root Cause:** {err.root_cause}")
        lines.append(f"- **Remediation:** {err.remediation}")
        lines.append("")

    # Log sources
    lines.append("## Log Sources Scanned")
    lines.append("")
    for src in report.log_sources:
        lines.append(f"- `{src}`")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VS Code Error Autopsy — classify Electron/Node fragility from logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--logs-dir", "-l",
        action="append",
        default=[],
        help="Additional log directory/file to scan (repeatable)",
    )
    parser.add_argument(
        "--matrix-dir",
        action="append",
        default=[],
        help="Additional matrix/triage directory or file to scan (repeatable)",
    )
    parser.add_argument(
        "--json", dest="emit_json", action="store_true",
        help="Emit JSON report to stdout",
    )
    parser.add_argument(
        "--md", dest="emit_md", action="store_true",
        help="Emit Markdown report to stdout",
    )
    parser.add_argument(
        "--emit", "-e", type=str, default=None,
        help="Write Markdown report to this file path (relative to repo root)",
    )
    parser.add_argument(
        "--emit-json", dest="emit_json_file", type=str, default=None,
        help="Write JSON report to this file path (relative to repo root)",
    )
    parser.add_argument(
        "--severity", "-s", type=str, default=None,
        choices=["critical", "high", "medium", "low", "info"],
        help="Filter errors to this severity or above",
    )
    parser.add_argument(
        "--category", "-c", type=str, default=None,
        help="Filter errors to this category (GPU, EXTHOST, MEMORY, PTY, NETWORK, UI, CRASH)",
    )
    parser.add_argument(
        "--no-appdata", action="store_true",
        help="Skip scanning AppData VS Code Insiders logs",
    )
    parser.add_argument(
        "--only-provided", action="store_true",
        help="Scan only paths passed via --logs-dir/--matrix-dir (skip default discovery).",
    )
    parser.add_argument(
        "--no-dedupe", action="store_true",
        help="Show all error occurrences (no deduplication)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    log = setup_logging(verbose=args.verbose, quiet=args.quiet)

    repo = find_repo_root()
    log.info("Repo root: %s", repo)

    # Discover logs
    extra_inputs = list(args.logs_dir or []) + list(args.matrix_dir or [])
    extra = [Path(d) for d in extra_inputs] if extra_inputs else None
    if args.no_appdata:
        # Temporarily disable AppData scanning
        global INSIDERS_LOGS_DIR
        INSIDERS_LOGS_DIR = Path("/nonexistent")

    log_files = discover_log_files(
        repo,
        extra,
        include_defaults=not args.only_provided,
    )
    log.info("Discovered %d log files", len(log_files))

    if not log_files:
        print("No log files found. Use --logs-dir to specify paths.", file=sys.stderr)
        return 1

    # Classify
    all_errors: list[ClassifiedError] = []
    total_lines = 0
    sources: list[str] = []

    for filepath in log_files:
        log.debug("Scanning: %s", filepath)
        errs, lines = classify_file(filepath, ERROR_PATTERNS)
        all_errors.extend(errs)
        total_lines += lines
        if errs:
            sources.append(str(filepath))

    log.info("Scanned %d lines, found %d raw errors", total_lines, len(all_errors))

    # Deduplicate
    deduped_count = 0
    if not args.no_dedupe:
        all_errors, deduped_count = deduplicate_errors(all_errors)
        log.info("After dedup: %d errors (%d collapsed)", len(all_errors), deduped_count)

    # Filter by severity
    if args.severity:
        min_rank = SEVERITY_RANK.get(args.severity.upper(), 0)
        all_errors = [e for e in all_errors if e.severity_rank >= min_rank]

    # Filter by category
    if args.category:
        cat_filter = args.category.upper()
        all_errors = [e for e in all_errors if e.category == cat_filter]

    # Build report
    report = AutopsyReport(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        repo_root=str(repo),
        log_sources=sources,
        errors=all_errors,
        deduped_count=deduped_count,
        total_lines_scanned=total_lines,
    )
    report.compute_summaries()

    # Output
    if args.emit_json:
        json.dump(report_to_dict(report), sys.stdout, indent=2, ensure_ascii=False)
        print()
    elif args.emit_md:
        print(report_to_markdown(report))
    else:
        # Default: terminal summary
        _print_terminal_summary(report)

    # Write to file if requested
    if args.emit:
        out_path = repo / args.emit
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_to_markdown(report), encoding="utf-8")
        log.info("Wrote MD report: %s", out_path)
        if not args.quiet:
            print(f"\nWrote: {out_path}", file=sys.stderr)

    if args.emit_json_file:
        out_path = repo / args.emit_json_file
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report_to_dict(report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("Wrote JSON report: %s", out_path)
        if not args.quiet:
            print(f"\nWrote: {out_path}", file=sys.stderr)

    return 0 if report.stability_score >= 50 else 1


def _print_terminal_summary(report: AutopsyReport):
    """Print a concise terminal summary."""
    score = report.stability_score
    indicator = "OK" if score >= 80 else ("WARN" if score >= 50 else "CRITICAL")

    print(f"\n{'='*60}")
    print(f"  VS Code Error Autopsy  [{indicator}]  Score: {score}/100")
    print(f"{'='*60}")
    print(f"  Lines scanned:  {report.total_lines_scanned:>8,}")
    print(f"  Errors found:   {len(report.errors):>8}")
    print(f"  Duplicates:     {report.deduped_count:>8}")
    print(f"  Log sources:    {len(report.log_sources):>8}")
    print()

    if report.severity_summary:
        print("  Severity Breakdown:")
        for sev in [SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO]:
            count = report.severity_summary.get(sev, 0)
            if count > 0:
                bar = "#" * min(count, 40)
                print(f"    {sev:<10} {count:>4}  {bar}")
        print()

    if report.category_summary:
        print("  Category Breakdown:")
        for cat, count in sorted(report.category_summary.items(), key=lambda x: -x[1]):
            bar = "#" * min(count, 40)
            print(f"    {cat:<10} {count:>4}  {bar}")
        print()

    if report.top_remediations:
        print("  Top Remediations:")
        for i, rem in enumerate(report.top_remediations[:5], 1):
            print(f"    {i}. {rem}")
        print()

    print(f"{'='*60}\n")


if __name__ == "__main__":
    sys.exit(main())
