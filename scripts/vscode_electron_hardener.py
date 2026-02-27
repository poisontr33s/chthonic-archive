#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
VS Code Electron Hardener — GPU acceleration, memory, and user-data repair.

Diagnoses and fixes the primary Electron fragility vectors:
1. GPU hardware acceleration disabled → patches argv.json
2. SwiftShader software rendering → forces hardware GPU
3. Memory limits too low → increases V8 heap
4. User-data-dir corruption → audits and reports stale caches
5. Extension host instability → generates safe-mode launch commands

Code patterns recycled from (WPTG provenance):
- vscode_error_autopsy.py    → classification, report structure
- vscode_terminal_crash_doctor.ps1 → argv.json awareness, code-insiders paths
- vscode_insiders_matrix.ps1       → stability scoring, matrix approach

@SID:           TOOL_VSCODE_ELECTRON_HARDENER_V1
@Type:          Utility
@Context:       Infrastructure / VS Code Stability
@Implements:    Electron/GPU hardening (CHTHONIC-GOLDEN-PHASE-1)

Usage:
    uv run scripts/vscode_electron_hardener.py diagnose     # read-only audit
    uv run scripts/vscode_electron_hardener.py patch         # apply safe GPU fixes to argv.json
    uv run scripts/vscode_electron_hardener.py audit-userdata # scan user-data-dir for corruption
    uv run scripts/vscode_electron_hardener.py launch-flags   # print safe launch command
    uv run scripts/vscode_electron_hardener.py full           # diagnose + patch + audit + report
    uv run scripts/vscode_electron_hardener.py --json         # JSON output mode
    uv run scripts/vscode_electron_hardener.py --dry-run      # show what would change without writing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.shared import configure_utf8_output, find_repo_root, setup_logging

# =============================================================================
# Constants — VS Code Insiders Paths
# =============================================================================

APPDATA = Path(os.environ.get("APPDATA", ""))

INSIDERS_USER_DATA = APPDATA / "Code - Insiders"
INSIDERS_ARGV = INSIDERS_USER_DATA / "argv.json"
INSIDERS_USER_SETTINGS = INSIDERS_USER_DATA / "User" / "settings.json"
INSIDERS_LOGS = INSIDERS_USER_DATA / "logs"
INSIDERS_CACHE = Path(os.environ.get("LOCALAPPDATA", "")) / "Code - Insiders" / "Cache"
INSIDERS_CRASHPAD = Path(os.environ.get("TEMP", "")) / "Electron Crashes"

# VS Code stable paths (fallback)
STABLE_USER_DATA = APPDATA / "Code"
STABLE_ARGV = STABLE_USER_DATA / "argv.json"

# Hardening profiles
PROFILE_STABILITY = "stability"
PROFILE_PERFORMANCE = "performance"

PROFILE_GPU_FLAGS = {
    PROFILE_STABILITY: {
        "disable-hardware-acceleration": True,
        "enable-gpu-rasterization": False,
        "ignore-gpu-blocklist": False,
    },
    PROFILE_PERFORMANCE: {
        "disable-hardware-acceleration": False,
        "enable-gpu-rasterization": True,
        "ignore-gpu-blocklist": True,
    },
}

# Memory tuning for large workspaces
MEMORY_FLAGS = {
    "js-flags": "--max-old-space-size=8192",  # 8GB V8 heap (default ~4GB)
}

# Recommended workspace settings for stability
PROFILE_TERMINAL_GPU = {
    PROFILE_STABILITY: "off",
    PROFILE_PERFORMANCE: "auto",
}

# User-data corruption signals
CORRUPTION_SIGNALS = [
    "Backups",  # excessive backup accumulation
    "CachedExtensions",  # stale extension cache
    "CachedData",  # stale V8 code cache
]

# Max cache age before it's considered stale (days)
MAX_CACHE_AGE_DAYS = 14


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class DiagnosticFinding:
    """A single diagnostic finding."""
    component: str  # GPU, MEMORY, USERDATA, SETTINGS, LAUNCH
    status: str     # OK, WARN, CRITICAL, FIXED
    message: str
    detail: str = ""
    action: str = ""  # what was/could be done


@dataclass
class HardeningReport:
    """Full hardening diagnostic and action report."""
    generated_utc: str = ""
    mode: str = ""
    profile: str = PROFILE_STABILITY
    dry_run: bool = False
    argv_path: str = ""
    user_data_path: str = ""
    findings: list[DiagnosticFinding] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    launch_command: str = ""
    health_score: int = 100

    def compute_score(self):
        crit = sum(1 for f in self.findings if f.status == "CRITICAL")
        warn = sum(1 for f in self.findings if f.status == "WARN")
        self.health_score = max(0, 100 - (crit * 30) - (warn * 10))


# =============================================================================
# Diagnostic Functions
# =============================================================================

def parse_jsonc_object(text: str) -> dict:
    """
    Parse a JSONC object with conservative preprocessing.

    Supports:
    - line comments that start with optional whitespace then //
    - trailing commas before } or ]
    """
    stripped = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
    stripped = re.sub(r",\s*([}\]])", r"\1", stripped)
    value = json.loads(stripped)
    if not isinstance(value, dict):
        raise json.JSONDecodeError("Top-level JSON value is not an object", stripped, 0)
    return value


def read_argv_json(path: Path) -> dict | None:
    """Read and parse argv.json, handling JSONC (comments)."""
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        return parse_jsonc_object(text)
    except (json.JSONDecodeError, OSError):
        return None


def diagnose_gpu(argv_data: dict | None, profile: str) -> list[DiagnosticFinding]:
    """Diagnose GPU acceleration state from argv.json."""
    findings: list[DiagnosticFinding] = []

    if argv_data is None:
        findings.append(DiagnosticFinding(
            component="GPU",
            status="CRITICAL",
            message="argv.json not found or unreadable",
            detail="VS Code cannot configure GPU without runtime flags file.",
            action="Create argv.json with GPU acceleration flags.",
        ))
        return findings

    disable_hw = bool(argv_data.get("disable-hardware-acceleration", False))
    gpu_raster = bool(argv_data.get("enable-gpu-rasterization", False))
    bypass_blocklist = bool(argv_data.get("ignore-gpu-blocklist", False))

    if profile == PROFILE_STABILITY:
        if disable_hw:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="OK",
                message="Crash-safe profile active (hardware acceleration disabled)",
                detail='Found "disable-hardware-acceleration": true',
                action='Keep this while terminal/renderer crashes are active.',
            ))
        else:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="WARN",
                message="Crash-safe profile expects GPU disabled",
                detail='Found "disable-hardware-acceleration": false',
                action='Set "disable-hardware-acceleration": true for maximum stability.',
            ))
        if gpu_raster:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="WARN",
                message="GPU rasterization enabled under stability profile",
                detail='Found "enable-gpu-rasterization": true',
                action='Set to false while isolating GPU-related crashes.',
            ))
    else:
        if disable_hw:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="CRITICAL",
                message="Performance profile blocked by disabled hardware acceleration",
                detail='Found "disable-hardware-acceleration": true',
                action='Set "disable-hardware-acceleration": false.',
            ))
        else:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="OK",
                message="Hardware acceleration enabled for performance profile",
            ))

        if not gpu_raster:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="WARN",
                message="GPU rasterization not enabled",
                detail="Enabling can improve rendering performance.",
                action='Add "enable-gpu-rasterization": true to argv.json.',
            ))
        if not bypass_blocklist:
            findings.append(DiagnosticFinding(
                component="GPU",
                status="WARN",
                message="GPU blocklist not bypassed",
                detail="Some GPUs are incorrectly blocklisted by Chromium.",
                action='Add "ignore-gpu-blocklist": true to argv.json.',
            ))

    return findings


def diagnose_memory(argv_data: dict | None) -> list[DiagnosticFinding]:
    """Diagnose V8 memory configuration."""
    findings: list[DiagnosticFinding] = []

    if argv_data is None:
        findings.append(DiagnosticFinding(
            component="MEMORY",
            status="WARN",
            message="Cannot check memory flags: argv.json missing",
        ))
        return findings

    js_flags = argv_data.get("js-flags", "")
    if "--max-old-space-size" not in js_flags:
        findings.append(DiagnosticFinding(
            component="MEMORY",
            status="WARN",
            message="V8 heap size not explicitly configured",
            detail="Default is ~4GB. Large workspaces benefit from 8GB.",
            action='Add "js-flags": "--max-old-space-size=8192" to argv.json.',
        ))
    else:
        findings.append(DiagnosticFinding(
            component="MEMORY",
            status="OK",
            message="V8 heap size configured in js-flags",
            detail=f"Current: {js_flags}",
        ))

    return findings


def diagnose_userdata(user_data: Path) -> list[DiagnosticFinding]:
    """Audit user-data directory for corruption signals."""
    findings: list[DiagnosticFinding] = []

    if not user_data.is_dir():
        findings.append(DiagnosticFinding(
            component="USERDATA",
            status="WARN",
            message=f"User data directory not found: {user_data}",
        ))
        return findings

    # Check total size of user data
    total_size = 0
    file_count = 0
    try:
        for f in user_data.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1
    except OSError:
        pass

    size_mb = total_size / (1024 * 1024)
    if size_mb > 2000:
        findings.append(DiagnosticFinding(
            component="USERDATA",
            status="CRITICAL",
            message=f"User data dir is {size_mb:.0f}MB ({file_count:,} files)",
            detail="Excessive size indicates cache bloat or state corruption.",
            action="Clear CachedData and CachedExtensions directories.",
        ))
    elif size_mb > 500:
        findings.append(DiagnosticFinding(
            component="USERDATA",
            status="WARN",
            message=f"User data dir is {size_mb:.0f}MB ({file_count:,} files)",
            detail="Consider clearing stale caches.",
        ))
    else:
        findings.append(DiagnosticFinding(
            component="USERDATA",
            status="OK",
            message=f"User data dir is {size_mb:.0f}MB ({file_count:,} files)",
        ))

    # Check for stale log sessions
    if INSIDERS_LOGS.is_dir():
        log_sessions = sorted(INSIDERS_LOGS.iterdir(), key=lambda p: p.name)
        if len(log_sessions) > 20:
            findings.append(DiagnosticFinding(
                component="USERDATA",
                status="WARN",
                message=f"Found {len(log_sessions)} log sessions in logs dir",
                detail="Excessive log sessions can slow startup.",
                action="Clean old log sessions (keep last 5).",
            ))

    # Check for crash dumps
    if INSIDERS_CRASHPAD.is_dir():
        crash_files = list(INSIDERS_CRASHPAD.rglob("*.dmp"))
        if crash_files:
            findings.append(DiagnosticFinding(
                component="USERDATA",
                status="WARN",
                message=f"Found {len(crash_files)} crash dump(s) in Electron Crashes",
                detail=f"Location: {INSIDERS_CRASHPAD}",
                action="Analyze crash dumps or clear after recording.",
            ))

    # Check for stale code caches
    for cache_dir_name in CORRUPTION_SIGNALS:
        cache_dir = user_data / cache_dir_name
        if cache_dir.is_dir():
            try:
                cache_age = (datetime.now() - datetime.fromtimestamp(cache_dir.stat().st_mtime)).days
                if cache_age > MAX_CACHE_AGE_DAYS:
                    findings.append(DiagnosticFinding(
                        component="USERDATA",
                        status="WARN",
                        message=f"Stale cache: {cache_dir_name} ({cache_age} days old)",
                        action=f"Consider clearing {cache_dir}.",
                    ))
            except OSError:
                pass

    return findings


def diagnose_settings(repo: Path, profile: str) -> list[DiagnosticFinding]:
    """Check workspace settings for known instability triggers."""
    findings: list[DiagnosticFinding] = []
    ws_settings = repo / ".vscode" / "settings.json"

    if not ws_settings.is_file():
        return findings

    try:
        text = ws_settings.read_text(encoding="utf-8")
        settings = parse_jsonc_object(text)
    except (json.JSONDecodeError, OSError):
        findings.append(DiagnosticFinding(
            component="SETTINGS",
            status="WARN",
            message="Failed to parse .vscode/settings.json",
        ))
        return findings

    # Check terminal GPU
    gpu_accel = settings.get("terminal.integrated.gpuAcceleration", "auto")
    expected = PROFILE_TERMINAL_GPU.get(profile, "off")
    if gpu_accel != expected:
        if profile == PROFILE_STABILITY:
            findings.append(DiagnosticFinding(
                component="SETTINGS",
                status="WARN",
                message='Terminal GPU acceleration should be "off" in crash-safe profile',
                detail=f'Current: "{gpu_accel}"',
                action='Set terminal.integrated.gpuAcceleration to "off".',
            ))
        else:
            findings.append(DiagnosticFinding(
                component="SETTINGS",
                status="WARN",
                message='Terminal GPU acceleration should be "auto" in performance profile',
                detail=f'Current: "{gpu_accel}"',
                action='Set terminal.integrated.gpuAcceleration to "auto".',
            ))
    else:
        findings.append(DiagnosticFinding(
            component="SETTINGS",
            status="OK",
            message=f'Terminal GPU acceleration matches profile ({gpu_accel})',
        ))

    return findings


# =============================================================================
# Patch Functions
# =============================================================================

def patch_argv(
    argv_path: Path,
    profile: str = PROFILE_STABILITY,
    dry_run: bool = False,
) -> tuple[dict, list[str]]:
    """
    Patch argv.json with safe GPU and memory flags.

    Returns:
        Tuple of (new argv data, list of action descriptions)
    """
    actions: list[str] = []

    # Read existing or create fresh
    existing = read_argv_json(argv_path)
    if existing is None:
        existing = {}
        actions.append(f"Creating new argv.json at {argv_path}")

    new_data = dict(existing)

    profile_flags = PROFILE_GPU_FLAGS.get(profile, PROFILE_GPU_FLAGS[PROFILE_STABILITY])
    actions.append(f"Applying GPU profile: {profile}")

    # Apply GPU flags
    for key, value in profile_flags.items():
        if new_data.get(key) != value:
            old_val = new_data.get(key, "<unset>")
            new_data[key] = value
            actions.append(f"argv.json: {key}: {old_val} -> {value}")

    # Apply memory flags
    for key, value in MEMORY_FLAGS.items():
        current = new_data.get(key, "")
        if "--max-old-space-size" not in current:
            new_data[key] = value
            actions.append(f"argv.json: {key}: {current!r} -> {value!r}")

    if not dry_run and actions:
        # Backup existing
        if argv_path.is_file():
            backup = argv_path.with_suffix(".json.bak")
            shutil.copy2(argv_path, backup)
            actions.insert(0, f"Backed up existing argv.json to {backup}")

        argv_path.parent.mkdir(parents=True, exist_ok=True)
        argv_path.write_text(
            json.dumps(new_data, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        actions.append(f"Wrote patched argv.json to {argv_path}")

    return new_data, actions


def generate_launch_flags(profile: str) -> str:
    """Generate a launch command for VS Code Insiders based on profile."""
    if profile == PROFILE_PERFORMANCE:
        flags = [
            "code-insiders",
            "--enable-gpu-rasterization",
            "--ignore-gpu-blocklist",
            "--force-gpu-mem-available-mb=4096",
            '--js-flags="--max-old-space-size=8192"',
        ]
    else:
        flags = [
            "code-insiders",
            "--disable-gpu",
            "--disable-extensions",
            '--user-data-dir="$env:TEMP\\code-insiders-safe"',
        ]
    return " ".join(flags)


# =============================================================================
# Output Formatters
# =============================================================================

def report_to_dict(report: HardeningReport) -> dict:
    return {
        "schema_version": 1,
        "generated_utc": report.generated_utc,
        "mode": report.mode,
        "profile": report.profile,
        "dry_run": report.dry_run,
        "health_score": report.health_score,
        "argv_path": report.argv_path,
        "user_data_path": report.user_data_path,
        "launch_command": report.launch_command,
        "findings": [asdict(f) for f in report.findings],
        "actions_taken": report.actions_taken,
    }


def report_to_markdown(report: HardeningReport) -> str:
    lines: list[str] = []
    lines.append("# VS Code Electron Hardener Report")
    lines.append("")
    lines.append(f"- **Generated (UTC):** {report.generated_utc}")
    lines.append(f"- **Mode:** {report.mode}")
    lines.append(f"- **Profile:** {report.profile}")
    lines.append(f"- **Dry Run:** {report.dry_run}")
    lines.append(f"- **Health Score:** {report.health_score}/100")
    lines.append(f"- **argv.json:** `{report.argv_path}`")
    lines.append("")

    # Findings
    lines.append("## Findings")
    lines.append("")
    lines.append("| Component | Status | Message |")
    lines.append("|---|---|---|")
    for f in report.findings:
        lines.append(f"| {f.component} | {f.status} | {f.message} |")
    lines.append("")

    # Detailed findings
    for f in report.findings:
        if f.detail or f.action:
            lines.append(f"### [{f.status}] {f.component}: {f.message}")
            if f.detail:
                lines.append(f"- **Detail:** {f.detail}")
            if f.action:
                lines.append(f"- **Action:** {f.action}")
            lines.append("")

    # Actions taken
    if report.actions_taken:
        lines.append("## Actions Taken")
        lines.append("")
        for a in report.actions_taken:
            lines.append(f"- {a}")
        lines.append("")

    # Launch command
    if report.launch_command:
        lines.append("## Recommended Launch Command")
        lines.append("")
        lines.append("```powershell")
        lines.append(report.launch_command)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def print_terminal_summary(report: HardeningReport):
    score = report.health_score
    indicator = "OK" if score >= 80 else ("WARN" if score >= 50 else "CRITICAL")

    print(f"\n{'='*60}")
    print(f"  Electron Hardener  [{indicator}]  Score: {score}/100")
    print(f"{'='*60}")
    print(f"  Mode: {report.mode}  |  Profile: {report.profile}  |  Dry-run: {report.dry_run}")
    print()

    for f in report.findings:
        icon = {"OK": "+", "WARN": "!", "CRITICAL": "X", "FIXED": "*"}.get(f.status, "?")
        print(f"  [{icon}] {f.component:<10} {f.status:<10} {f.message}")
    print()

    if report.actions_taken:
        print("  Actions:")
        for a in report.actions_taken:
            print(f"    -> {a}")
        print()

    if report.launch_command:
        print(f"  Launch command:")
        print(f"    {report.launch_command}")
        print()

    print(f"{'='*60}\n")


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VS Code Electron Hardener — GPU, memory, and user-data repair",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="diagnose",
        choices=["diagnose", "patch", "audit-userdata", "launch-flags", "full"],
        help="Operation mode (default: diagnose)",
    )
    parser.add_argument(
        "--profile",
        choices=[PROFILE_STABILITY, PROFILE_PERFORMANCE],
        default=PROFILE_STABILITY,
        help="Hardening profile (default: stability).",
    )
    parser.add_argument("--json", dest="emit_json", action="store_true")
    parser.add_argument("--md", dest="emit_md", action="store_true")
    parser.add_argument(
        "--emit", "-e", type=str, default=None,
        help="Write markdown report to file",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing",
    )
    parser.add_argument(
        "--stable", action="store_true",
        help="Target VS Code stable instead of Insiders",
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

    # Select target paths
    if args.stable:
        argv_path = STABLE_ARGV
        user_data = STABLE_USER_DATA
    else:
        argv_path = INSIDERS_ARGV
        user_data = INSIDERS_USER_DATA

    report = HardeningReport(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        mode=args.mode,
        profile=args.profile,
        dry_run=args.dry_run,
        argv_path=str(argv_path),
        user_data_path=str(user_data),
    )

    argv_data = read_argv_json(argv_path)

    # Diagnose
    if args.mode in ("diagnose", "full"):
        report.findings.extend(diagnose_gpu(argv_data, profile=args.profile))
        report.findings.extend(diagnose_memory(argv_data))
        report.findings.extend(diagnose_userdata(user_data))
        report.findings.extend(diagnose_settings(repo, profile=args.profile))

    # Patch argv.json
    if args.mode in ("patch", "full"):
        _, actions = patch_argv(argv_path, profile=args.profile, dry_run=args.dry_run)
        report.actions_taken.extend(actions)
        # Re-diagnose after patch
        if not args.dry_run and actions:
            argv_data = read_argv_json(argv_path)
            # Update findings with post-patch state
            gpu_findings = diagnose_gpu(argv_data, profile=args.profile)
            for f in gpu_findings:
                if f.status == "OK":
                    f.status = "FIXED"
            report.findings.extend(gpu_findings)

    # Audit user-data
    if args.mode == "audit-userdata":
        report.findings.extend(diagnose_userdata(user_data))

    # Launch flags
    if args.mode in ("launch-flags", "full"):
        report.launch_command = generate_launch_flags(profile=args.profile)

    report.compute_score()

    # Output
    if args.emit_json:
        json.dump(report_to_dict(report), sys.stdout, indent=2, ensure_ascii=False)
        print()
    elif args.emit_md:
        print(report_to_markdown(report))
    else:
        print_terminal_summary(report)

    if args.emit:
        out_path = repo / args.emit
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_to_markdown(report), encoding="utf-8")
        if not args.quiet:
            print(f"Wrote: {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
