#!/usr/bin/env python3
"""
run_cycle.py - Unified MILF Execution Cycle

This script orchestrates a complete synthesis cycle:
1. Probes GPU compatibility → selects engine lane
2. Loads MILF registry → identifies eligible MILFs
3. Executes selected MILF with appropriate engine
4. Writes cycle report with lineage tracking
5. Triggers activation gate evaluation

Usage:
    python scripts/run_cycle.py [--milf-id MILF_ID] [--dry-run] [--verbose]
    mas-cycle  # via pyproject.toml entry point

Architecture:
    SSOT (copilot-instructions.md)
        ↓
    artifacts/milf_registry.json (activation gates)
        ↓
    artifacts/compatibility/matrix.json (engine lanes)
        ↓
    probe_report.json → Engine Selection
        ↓
    Execution → cycle_report.json
        ↓
    milf_activator.py → promotion/demotion
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Paths
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
SSOT_PATH = PROJECT_ROOT.parent / ".github" / "copilot-instructions.md"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
REPORTS_DIR = PROJECT_ROOT / "cycle_reports"

MILF_REGISTRY_PATH = ARTIFACTS_DIR / "milf_registry.json"
SCORING_PROFILES_PATH = ARTIFACTS_DIR / "scoring_profiles.json"
COMPATIBILITY_MATRIX_PATH = ARTIFACTS_DIR / "compatibility" / "matrix.json"
PROBE_REPORT_PATH = ARTIFACTS_DIR / "probe_report.json"


# ─────────────────────────────────────────────────────────────────────────────
# Type Definitions
# ─────────────────────────────────────────────────────────────────────────────

class EngineLane(TypedDict):
    primary: str
    fallback: str | None
    required_providers: list[str]


class ActivationGates(TypedDict):
    min_cycles: int
    acceptance_threshold: int
    latency_p95_max_ms: int
    error_rate_max: int
    drift_guard: bool


class MILF(TypedDict):
    milf_id: str
    name: str
    intent: str
    description: str
    engine_lane: EngineLane
    compatibility_rows: list[str]
    scoring_profile: str
    activation_gates: ActivationGates
    status: str


class ProbeReport(TypedDict):
    matched_row: str | None
    available_providers: list[str]
    vram_total_gb: float
    vram_free_gb: float
    degradation_recommended: bool
    probe_timestamp: str


class CycleReport(TypedDict):
    cycle_id: str
    milf_id: str
    milf_name: str
    engine_lane: str
    execution_provider: str
    latency_ms: float
    vram_used_mb: float
    acceptance_score: int
    status: str
    lineage: dict[str, Any]
    timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def compute_ssot_hash() -> str:
    """Compute SHA256 hash of the SSOT for lineage tracking."""
    if not SSOT_PATH.exists():
        return "ssot_not_found"
    content = SSOT_PATH.read_bytes()
    return hashlib.sha256(content).hexdigest()[:12]


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON file with error handling."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def log(msg: str, level: str = "INFO", verbose: bool = True) -> None:
    """Simple logging with timestamp."""
    if verbose or level in ("ERROR", "WARN"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [{level}] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Probe Phase
# ─────────────────────────────────────────────────────────────────────────────

def run_gpu_probe(verbose: bool = True) -> ProbeReport:
    """
    Run GPU compatibility probe and return report.
    
    If probe_report.json exists and is less than 1 hour old, use cached.
    Otherwise, run probe_gpu_compatibility.py to generate fresh report.
    """
    # Check for cached probe report
    if PROBE_REPORT_PATH.exists():
        try:
            cached = load_json(PROBE_REPORT_PATH)
            probe_ts = datetime.fromisoformat(cached.get("probe_timestamp", "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - probe_ts).total_seconds()
            if age_seconds < 3600:  # 1 hour cache
                log(f"Using cached probe report (age: {age_seconds:.0f}s)", verbose=verbose)
                return cached
        except (json.JSONDecodeError, ValueError):
            pass  # Invalid cache, regenerate
    
    # Run probe script
    log("Running GPU compatibility probe...", verbose=verbose)
    probe_script = PROJECT_ROOT / "scripts" / "probe_gpu_compatibility.py"
    
    if not probe_script.exists():
        log("Probe script not found, using fallback CPU configuration", "WARN", verbose)
        return {
            "matched_row": None,
            "available_providers": ["CPUExecutionProvider"],
            "vram_total_gb": 0.0,
            "vram_free_gb": 0.0,
            "degradation_recommended": True,
            "probe_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    try:
        result = subprocess.run(
            [sys.executable, str(probe_script)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            log(f"Probe failed: {result.stderr}", "WARN", verbose)
    except subprocess.TimeoutExpired:
        log("Probe timed out", "WARN", verbose)
    except Exception as e:
        log(f"Probe error: {e}", "WARN", verbose)
    
    # Load the generated report
    if PROBE_REPORT_PATH.exists():
        return load_json(PROBE_REPORT_PATH)
    
    # Fallback
    return {
        "matched_row": None,
        "available_providers": ["CPUExecutionProvider"],
        "vram_total_gb": 0.0,
        "vram_free_gb": 0.0,
        "degradation_recommended": True,
        "probe_timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Engine Selection
# ─────────────────────────────────────────────────────────────────────────────

def select_execution_provider(
    milf: MILF,
    probe: ProbeReport,
    verbose: bool = True
) -> tuple[str, str]:
    """
    Select execution provider based on MILF requirements and probe results.
    
    Returns:
        (engine_lane, execution_provider)
    """
    engine_lane = milf["engine_lane"]
    available = probe["available_providers"]
    matched_row = probe.get("matched_row")
    degraded = probe.get("degradation_recommended", False)
    
    # Check if MILF's compatibility rows include the matched row
    if matched_row and matched_row not in milf.get("compatibility_rows", []):
        log(f"MILF {milf['milf_id']} not compatible with {matched_row}", "WARN", verbose)
        return ("cpu", "CPUExecutionProvider")
    
    # Check primary engine
    primary = engine_lane.get("primary", "cpu")
    required = engine_lane.get("required_providers", [])
    
    if not degraded and all(p in available for p in required):
        # Primary lane available
        provider = required[0] if required else "CPUExecutionProvider"
        log(f"Selected primary lane: {primary} ({provider})", verbose=verbose)
        return (primary, provider)
    
    # Check fallback
    fallback = engine_lane.get("fallback")
    if fallback:
        if fallback == "onnxruntime_cuda" and "CUDAExecutionProvider" in available:
            log(f"Selected fallback: onnxruntime_cuda (CUDAExecutionProvider)", verbose=verbose)
            return ("onnxruntime_cuda", "CUDAExecutionProvider")
        elif fallback == "cpu":
            log(f"Selected fallback: cpu (CPUExecutionProvider)", verbose=verbose)
            return ("cpu", "CPUExecutionProvider")
    
    # Ultimate fallback
    log("Falling back to CPU execution", "WARN", verbose=verbose)
    return ("cpu", "CPUExecutionProvider")


# ─────────────────────────────────────────────────────────────────────────────
# MILF Execution (Stub)
# ─────────────────────────────────────────────────────────────────────────────

def execute_milf(
    milf: MILF,
    engine_lane: str,
    provider: str,
    verbose: bool = True
) -> dict[str, Any]:
    """
    Execute a MILF with the selected engine lane.
    
    This is a stub implementation. In production, this would:
    1. Load the appropriate model/engine
    2. Run inference with actual inputs
    3. Validate outputs against expected schema
    4. Measure latency and resource usage
    
    Returns execution results dict.
    """
    log(f"Executing {milf['milf_id']} with {engine_lane}/{provider}...", verbose=verbose)
    
    start_time = time.perf_counter()
    
    # Simulate execution (replace with actual logic)
    # In real implementation, this would call milf_genesis_v2.py functions
    import random
    simulated_latency = random.uniform(5, 100)  # ms
    simulated_vram = random.uniform(100, 1000)  # MB
    simulated_success = random.random() > 0.1  # 90% success rate
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000 + simulated_latency
    
    return {
        "success": simulated_success,
        "latency_ms": elapsed_ms,
        "vram_used_mb": simulated_vram if engine_lane != "cpu" else 0,
        "outputs": {"simulated": True},
        "error": None if simulated_success else "Simulated failure",
    }


def calculate_acceptance_score(
    milf: MILF,
    execution_result: dict[str, Any],
    scoring_profiles: dict[str, Any],
) -> int:
    """
    Calculate acceptance score based on execution results and scoring profile.
    """
    profile_id = milf.get("scoring_profile", "inference_default")
    profiles = scoring_profiles.get("profiles", {})
    profile = profiles.get(profile_id, profiles.get("inference_default", {}))
    
    weights = profile.get("weights", {})
    penalties = profile.get("penalties", {})
    
    # Base score
    score = 70 if execution_result.get("success") else 30
    
    # Apply latency weight
    latency = execution_result.get("latency_ms", 0)
    gates = milf.get("activation_gates", {})
    max_latency = gates.get("latency_p95_max_ms", 100)
    if latency <= max_latency:
        score += weights.get("latency_p95", 20)
    else:
        score -= 10  # Latency penalty
    
    # Apply error penalty
    if not execution_result.get("success"):
        score += penalties.get("timeout", -25)
    
    # Clamp to 0-100
    return max(0, min(100, score))


# ─────────────────────────────────────────────────────────────────────────────
# Main Cycle Logic
# ─────────────────────────────────────────────────────────────────────────────

def run_cycle(
    milf_id: str | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> CycleReport | None:
    """
    Execute a complete synthesis cycle.
    
    Args:
        milf_id: Specific MILF to execute (None = first eligible)
        dry_run: If True, don't write artifacts
        verbose: Enable verbose logging
    
    Returns:
        CycleReport if successful, None otherwise
    """
    log("═" * 60, verbose=verbose)
    log("MAS-MCP SYNTHESIS CYCLE", verbose=verbose)
    log("═" * 60, verbose=verbose)
    
    # Step 1: Compute SSOT hash for lineage
    ssot_hash = compute_ssot_hash()
    log(f"SSOT hash: {ssot_hash}", verbose=verbose)
    
    # Step 2: Load governance artifacts
    try:
        registry = load_json(MILF_REGISTRY_PATH)
        scoring_profiles = load_json(SCORING_PROFILES_PATH)
        matrix = load_json(COMPATIBILITY_MATRIX_PATH)
    except FileNotFoundError as e:
        log(str(e), "ERROR", verbose)
        return None
    
    # Step 3: Run GPU probe
    probe = run_gpu_probe(verbose)
    
    # Step 4: Select MILF
    functions: list[MILF] = registry.get("functions", [])
    
    if milf_id:
        milf = next((m for m in functions if m["milf_id"] == milf_id), None)
        if not milf:
            log(f"MILF not found: {milf_id}", "ERROR", verbose)
            return None
    else:
        # Select first eligible MILF (shadow or active, matching compatibility)
        eligible = [
            m for m in functions
            if m.get("status") in ("shadow", "active")
            and (not probe.get("matched_row") or probe["matched_row"] in m.get("compatibility_rows", []))
        ]
        if not eligible:
            log("No eligible MILFs found", "ERROR", verbose)
            return None
        milf = eligible[0]
    
    log(f"Selected MILF: {milf['milf_id']} ({milf['name']})", verbose=verbose)
    
    # Step 5: Select execution provider
    engine_lane, provider = select_execution_provider(milf, probe, verbose)
    
    if dry_run:
        log("DRY RUN - skipping execution", verbose=verbose)
        return None
    
    # Step 6: Execute MILF
    result = execute_milf(milf, engine_lane, provider, verbose)
    
    # Step 7: Calculate score
    score = calculate_acceptance_score(milf, result, scoring_profiles)
    status = "accepted" if result.get("success") and score >= milf["activation_gates"]["acceptance_threshold"] else "rejected"
    
    log(f"Execution result: {status} (score: {score})", verbose=verbose)
    
    # Step 8: Build cycle report
    cycle_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    report: CycleReport = {
        "cycle_id": cycle_id,
        "milf_id": milf["milf_id"],
        "milf_name": milf["name"],
        "engine_lane": engine_lane,
        "execution_provider": provider,
        "latency_ms": round(result.get("latency_ms", 0), 2),
        "vram_used_mb": round(result.get("vram_used_mb", 0), 2),
        "acceptance_score": score,
        "status": status,
        "lineage": {
            "ssot_hash": ssot_hash,
            "registry_version": registry.get("registry_version", "unknown"),
            "matrix_row": probe.get("matched_row"),
            "scoring_profile": milf.get("scoring_profile"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Step 9: Save cycle report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"cycle_{cycle_id}.json"
    save_json(report_path, report)
    log(f"Cycle report saved: {report_path}", verbose=verbose)
    
    # Step 10: Trigger activation gate evaluation (optional)
    activator_script = PROJECT_ROOT / "scripts" / "milf_activator.py"
    if activator_script.exists():
        log("Triggering MILF activator...", verbose=verbose)
        try:
            subprocess.run(
                [sys.executable, str(activator_script)],
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            log(f"Activator warning: {e}", "WARN", verbose)
    
    log("═" * 60, verbose=verbose)
    log("CYCLE COMPLETE", verbose=verbose)
    log("═" * 60, verbose=verbose)
    
    return report


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    """CLI entry point for mas-cycle command."""
    parser = argparse.ArgumentParser(
        description="Run a MAS-MCP synthesis cycle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run cycle with first eligible MILF
    python scripts/run_cycle.py

    # Run specific MILF
    python scripts/run_cycle.py --milf-id milf_tensorrt_inference

    # Dry run (no artifacts written)
    python scripts/run_cycle.py --dry-run --verbose
        """,
    )
    parser.add_argument(
        "--milf-id",
        type=str,
        default=None,
        help="Specific MILF ID to execute (default: first eligible)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Probe and select but don't execute",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Enable verbose output",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output",
    )
    
    args = parser.parse_args()
    verbose = args.verbose and not args.quiet
    
    try:
        report = run_cycle(
            milf_id=args.milf_id,
            dry_run=args.dry_run,
            verbose=verbose,
        )
        return 0 if report else 1
    except KeyboardInterrupt:
        log("Interrupted", "WARN", verbose)
        return 130
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR", verbose=True)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
