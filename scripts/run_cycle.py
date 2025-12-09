#!/usr/bin/env python3
"""
Run Cycle - MILF Execution with Artifact Output

Executes a single governance cycle under uv, selecting engine lanes based on
compatibility probes, enforcing activation gates, and writing structured artifacts.

Flow:
    SSOT → GPU Probe → Compatibility Check → MILF Activation → Cycle Execution → Artifact Output

Usage:
    # Full cycle with GPU probe
    uv run scripts/run_cycle.py

    # Dry run (no artifacts, no side effects)
    uv run scripts/run_cycle.py --dry-run

    # Specific engine lane
    uv run scripts/run_cycle.py --engine tensorrt

    # With scoring profile
    uv run scripts/run_cycle.py --profile opus

Environment:
    CHTHONIC_ROOT        Override workspace root detection
    MILF_SCORE_THRESHOLD Minimum MILF activation score (default: 0.8)
    GPU_FALLBACK_CPU     Allow CPU fallback if GPU unavailable (default: false)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Path Resolution
# ─────────────────────────────────────────────────────────────────────────────

def find_workspace_root() -> Path:
    """Find the chthonic-archive workspace root."""
    if "CHTHONIC_ROOT" in os.environ:
        return Path(os.environ["CHTHONIC_ROOT"])
    
    # Walk up from script location
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "Cargo.toml").exists() and (current / ".github").exists():
            return current
        current = current.parent
    
    raise RuntimeError("Could not find workspace root (no Cargo.toml + .github found)")


WORKSPACE_ROOT = find_workspace_root()
MAS_MCP_ROOT = WORKSPACE_ROOT / "mas_mcp"
ARTIFACTS_DIR = MAS_MCP_ROOT / "artifacts"
GOVERNANCE_DIR = ARTIFACTS_DIR / "governance"
COMPATIBILITY_DIR = ARTIFACTS_DIR / "compatibility"
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"
SSOT_PATH = WORKSPACE_ROOT / ".github" / "copilot-instructions.md"


# ─────────────────────────────────────────────────────────────────────────────
# SSOT Lineage
# ─────────────────────────────────────────────────────────────────────────────

def compute_ssot_hash() -> str:
    """Compute SHA256 hash of the SSOT file."""
    if not SSOT_PATH.exists():
        return "SSOT_NOT_FOUND"
    
    content = SSOT_PATH.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def create_lineage_pointer() -> Dict[str, Any]:
    """Create a lineage pointer to the current SSOT state."""
    return {
        "ssot_path": str(SSOT_PATH.relative_to(WORKSPACE_ROOT)),
        "ssot_hash": compute_ssot_hash(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "workspace_root": str(WORKSPACE_ROOT),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GPU Probe Integration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProbeResult:
    """Result from GPU compatibility probe."""
    status: str  # "pass", "fail", "degraded", "unavailable"
    gpu_available: bool
    providers: List[str]
    matched_row: Optional[str]
    vram_total_gb: Optional[float]
    vram_used_pct: Optional[float]
    cuda_version: Optional[str]
    driver_version: Optional[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @classmethod
    def from_probe_report(cls, path: Path) -> "ProbeResult":
        """Load from probe_report.json."""
        if not path.exists():
            return cls(
                status="unavailable",
                gpu_available=False,
                providers=[],
                matched_row=None,
                vram_total_gb=None,
                vram_used_pct=None,
                cuda_version=None,
                driver_version=None,
                errors=["probe_report.json not found"],
            )
        
        try:
            data = json.loads(path.read_text())
            return cls(
                status=data.get("status", "unavailable"),
                gpu_available=data.get("gpu_available", False),
                providers=data.get("providers", []),
                matched_row=data.get("matched_row"),
                vram_total_gb=data.get("vram", {}).get("total_gb"),
                vram_used_pct=data.get("vram", {}).get("used_pct"),
                cuda_version=data.get("cuda", {}).get("version"),
                driver_version=data.get("driver", {}).get("version"),
                errors=data.get("errors", []),
                warnings=data.get("warnings", []),
            )
        except Exception as e:
            return cls(
                status="unavailable",
                gpu_available=False,
                providers=[],
                matched_row=None,
                vram_total_gb=None,
                vram_used_pct=None,
                cuda_version=None,
                driver_version=None,
                errors=[f"Failed to parse probe_report.json: {e}"],
            )
    
    @classmethod
    def run_probe(cls, probe_script: Path) -> "ProbeResult":
        """Run the GPU probe script and return results."""
        if not probe_script.exists():
            return cls(
                status="unavailable",
                gpu_available=False,
                providers=[],
                matched_row=None,
                vram_total_gb=None,
                vram_used_pct=None,
                cuda_version=None,
                driver_version=None,
                errors=[f"Probe script not found: {probe_script}"],
            )
        
        try:
            result = subprocess.run(
                [sys.executable, str(probe_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(WORKSPACE_ROOT),
            )
            
            if result.returncode != 0:
                return cls(
                    status="fail",
                    gpu_available=False,
                    providers=[],
                    matched_row=None,
                    vram_total_gb=None,
                    vram_used_pct=None,
                    cuda_version=None,
                    driver_version=None,
                    errors=[f"Probe failed: {result.stderr}"],
                )
            
            # Load the generated report
            report_path = COMPATIBILITY_DIR / "probe_report.json"
            return cls.from_probe_report(report_path)
            
        except subprocess.TimeoutExpired:
            return cls(
                status="fail",
                gpu_available=False,
                providers=[],
                matched_row=None,
                vram_total_gb=None,
                vram_used_pct=None,
                cuda_version=None,
                driver_version=None,
                errors=["Probe timed out after 60s"],
            )
        except Exception as e:
            return cls(
                status="unavailable",
                gpu_available=False,
                providers=[],
                matched_row=None,
                vram_total_gb=None,
                vram_used_pct=None,
                cuda_version=None,
                driver_version=None,
                errors=[f"Probe execution error: {e}"],
            )


# ─────────────────────────────────────────────────────────────────────────────
# Engine Lane Selection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EngineLane:
    """Represents an execution engine lane."""
    name: str
    priority: int
    providers: List[str]
    min_vram_gb: float
    features: List[str] = field(default_factory=list)
    
    def is_compatible(self, probe: ProbeResult) -> bool:
        """Check if this lane is compatible with probe results."""
        if not probe.gpu_available:
            return self.name == "cpu"
        
        # Check provider availability
        if not any(p in probe.providers for p in self.providers):
            return False
        
        # Check VRAM
        if probe.vram_total_gb is not None and probe.vram_total_gb < self.min_vram_gb:
            return False
        
        return True


# Default engine lanes ordered by priority
DEFAULT_LANES = [
    EngineLane(
        name="tensorrt",
        priority=1,
        providers=["TensorrtExecutionProvider"],
        min_vram_gb=8.0,
        features=["fp16", "int8", "dynamic_shapes"],
    ),
    EngineLane(
        name="cuda",
        priority=2,
        providers=["CUDAExecutionProvider"],
        min_vram_gb=4.0,
        features=["fp16"],
    ),
    EngineLane(
        name="rocm",
        priority=3,
        providers=["ROCMExecutionProvider"],
        min_vram_gb=4.0,
        features=["fp16"],
    ),
    EngineLane(
        name="directml",
        priority=4,
        providers=["DmlExecutionProvider"],
        min_vram_gb=2.0,
        features=[],
    ),
    EngineLane(
        name="cpu",
        priority=99,
        providers=["CPUExecutionProvider"],
        min_vram_gb=0.0,
        features=[],
    ),
]


def select_engine_lane(
    probe: ProbeResult,
    requested_lane: Optional[str] = None,
    allow_cpu_fallback: bool = False,
) -> Tuple[Optional[EngineLane], str]:
    """
    Select the best engine lane based on probe results.
    
    Returns:
        (EngineLane, reason) or (None, error_reason)
    """
    if requested_lane:
        # User requested specific lane
        for lane in DEFAULT_LANES:
            if lane.name == requested_lane:
                if lane.is_compatible(probe):
                    return lane, f"User requested {lane.name}"
                return None, f"Requested lane {requested_lane} not compatible: probe status={probe.status}"
        return None, f"Unknown lane: {requested_lane}"
    
    # Auto-select best compatible lane
    for lane in sorted(DEFAULT_LANES, key=lambda l: l.priority):
        if lane.is_compatible(probe):
            if lane.name == "cpu" and not allow_cpu_fallback:
                continue
            return lane, f"Auto-selected {lane.name} (priority {lane.priority})"
    
    if allow_cpu_fallback:
        cpu_lane = next(l for l in DEFAULT_LANES if l.name == "cpu")
        return cpu_lane, "Fallback to CPU (no GPU lanes compatible)"
    
    return None, "No compatible lanes and CPU fallback disabled"


# ─────────────────────────────────────────────────────────────────────────────
# MILF Activation Gates
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MILFActivation:
    """MILF (Model-In-the-Loop Function) activation state."""
    name: str
    activated: bool
    score: float
    threshold: float
    gates_passed: Dict[str, bool] = field(default_factory=dict)
    reason: str = ""


def load_milf_registry() -> Dict[str, Any]:
    """Load the MILF registry."""
    registry_path = GOVERNANCE_DIR / "milf_registry.json"
    if not registry_path.exists():
        return {"functions": [], "activation_gates": {}, "engine_lanes": {}}
    
    try:
        return json.loads(registry_path.read_text())
    except Exception:
        return {"functions": [], "activation_gates": {}, "engine_lanes": {}}


def load_scoring_profile(profile_name: str) -> Dict[str, Any]:
    """Load a scoring profile."""
    profiles_dir = GOVERNANCE_DIR / "scoring_profiles"
    profile_path = profiles_dir / f"{profile_name}_weights.json"
    
    if not profile_path.exists():
        return {
            "acceptance_weight": 0.4,
            "latency_weight": 0.2,
            "novelty_weight": 0.2,
            "error_penalty": 0.1,
            "drift_penalty": 0.1,
        }
    
    try:
        return json.loads(profile_path.read_text())
    except Exception:
        return {}


def check_milf_activation(
    milf_name: str,
    probe: ProbeResult,
    engine_lane: Optional[EngineLane],
    threshold: float = 0.8,
) -> MILFActivation:
    """
    Check if a MILF should be activated based on gates.
    
    Gates:
        - probe_pass: GPU probe passed
        - lane_available: Compatible engine lane found
        - slo_threshold: Score above threshold
        - drift_stable: No excessive drift detected
    """
    gates = {
        "probe_pass": probe.status in ("pass", "degraded"),
        "lane_available": engine_lane is not None,
        "slo_threshold": True,  # Will be computed from scoring profile
        "drift_stable": True,  # Placeholder for drift detection
    }
    
    # Compute score based on gates
    weights = {"probe_pass": 0.3, "lane_available": 0.3, "slo_threshold": 0.2, "drift_stable": 0.2}
    score = sum(weights[g] for g, passed in gates.items() if passed)
    
    activated = score >= threshold and all([gates["probe_pass"], gates["lane_available"]])
    
    reason = "Activated" if activated else f"Gates failed: {[g for g, p in gates.items() if not p]}"
    
    return MILFActivation(
        name=milf_name,
        activated=activated,
        score=score,
        threshold=threshold,
        gates_passed=gates,
        reason=reason,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Cycle Execution
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CycleResult:
    """Result of a single governance cycle."""
    cycle_id: str
    timestamp: str
    duration_s: float
    status: str  # "success", "degraded", "failed", "skipped"
    
    # Lineage
    lineage: Dict[str, Any] = field(default_factory=dict)
    
    # Probe
    probe_status: str = "unknown"
    probe_errors: List[str] = field(default_factory=list)
    
    # Engine
    engine_lane: Optional[str] = None
    engine_reason: str = ""
    
    # MILF
    milf_activations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Artifacts
    artifacts_written: List[str] = field(default_factory=list)
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def run_cycle(
    dry_run: bool = False,
    requested_engine: Optional[str] = None,
    profile: str = "standard",
    skip_probe: bool = False,
    allow_cpu: bool = False,
) -> CycleResult:
    """
    Execute a single governance cycle.
    
    Steps:
        1. Compute SSOT lineage
        2. Run GPU probe (or load existing)
        3. Select engine lane
        4. Check MILF activation gates
        5. Execute synthesis (if activated)
        6. Write artifacts
    """
    cycle_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
    start_time = time.time()
    
    result = CycleResult(
        cycle_id=cycle_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        duration_s=0.0,
        status="unknown",
        lineage=create_lineage_pointer(),
    )
    
    try:
        # Step 1: GPU Probe
        if skip_probe:
            probe = ProbeResult.from_probe_report(COMPATIBILITY_DIR / "probe_report.json")
            result.warnings.append("Using cached probe report")
        else:
            probe_script = SCRIPTS_DIR / "gpu_probe.py"
            if not probe_script.exists():
                probe_script = MAS_MCP_ROOT / "scripts" / "probe_gpu_compatibility.py"
            probe = ProbeResult.run_probe(probe_script)
        
        result.probe_status = probe.status
        result.probe_errors = probe.errors
        
        if probe.status not in ("pass", "degraded") and not allow_cpu:
            result.status = "failed"
            result.errors.append(f"Probe failed: {probe.status}")
            result.duration_s = time.time() - start_time
            return result
        
        # Step 2: Engine Lane Selection
        lane, lane_reason = select_engine_lane(
            probe,
            requested_lane=requested_engine,
            allow_cpu_fallback=allow_cpu,
        )
        
        result.engine_lane = lane.name if lane else None
        result.engine_reason = lane_reason
        
        if not lane:
            result.status = "failed"
            result.errors.append(f"No engine lane: {lane_reason}")
            result.duration_s = time.time() - start_time
            return result
        
        # Step 3: MILF Activation
        registry = load_milf_registry()
        scoring = load_scoring_profile(profile)
        threshold = float(os.environ.get("MILF_SCORE_THRESHOLD", "0.8"))
        
        activations = []
        for milf in registry.get("functions", []):
            activation = check_milf_activation(
                milf.get("name", "unknown"),
                probe,
                lane,
                threshold=threshold,
            )
            activations.append(asdict(activation))
        
        result.milf_activations = activations
        
        # Check if any MILFs activated
        active_milfs = [a for a in activations if a["activated"]]
        if not active_milfs:
            result.status = "skipped"
            result.warnings.append("No MILFs activated")
            result.duration_s = time.time() - start_time
            return result
        
        # Step 4: Execute (placeholder for actual genesis integration)
        if not dry_run:
            # Write cycle artifact
            cycle_artifact = {
                "cycle_id": cycle_id,
                "timestamp": result.timestamp,
                "lineage": result.lineage,
                "probe": {
                    "status": probe.status,
                    "gpu_available": probe.gpu_available,
                    "providers": probe.providers,
                    "matched_row": probe.matched_row,
                    "vram_total_gb": probe.vram_total_gb,
                    "vram_used_pct": probe.vram_used_pct,
                },
                "engine": {
                    "lane": lane.name,
                    "priority": lane.priority,
                    "features": lane.features,
                    "reason": lane_reason,
                },
                "milf_activations": activations,
                "scoring_profile": profile,
                "scoring_weights": scoring,
                "status": "success",
            }
            
            # Ensure output directory exists
            cycles_dir = ARTIFACTS_DIR / "cycles"
            cycles_dir.mkdir(parents=True, exist_ok=True)
            
            artifact_path = cycles_dir / f"cycle_{cycle_id}.json"
            artifact_path.write_text(json.dumps(cycle_artifact, indent=2))
            result.artifacts_written.append(str(artifact_path.relative_to(WORKSPACE_ROOT)))
        
        result.status = "success" if probe.status == "pass" else "degraded"
        result.metrics = {
            "active_milfs": len(active_milfs),
            "total_milfs": len(activations),
            "engine_lane": lane.name,
            "probe_status": probe.status,
        }
        
    except Exception as e:
        result.status = "failed"
        result.errors.append(f"Cycle exception: {e}")
    
    result.duration_s = time.time() - start_time
    return result


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Cycle - MILF Execution with Artifact Output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Simulate cycle without writing artifacts",
    )
    
    parser.add_argument(
        "--engine", "-e",
        type=str,
        choices=["tensorrt", "cuda", "rocm", "directml", "cpu"],
        help="Force specific engine lane",
    )
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        default="standard",
        help="Scoring profile to use (default: standard)",
    )
    
    parser.add_argument(
        "--skip-probe",
        action="store_true",
        help="Use cached probe report instead of running probe",
    )
    
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Allow CPU fallback if GPU unavailable",
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    if not args.quiet:
        print(f"🔄 Run Cycle - MILF Execution")
        print(f"   Workspace: {WORKSPACE_ROOT}")
        print(f"   SSOT Hash: {compute_ssot_hash()}")
        print()
    
    result = run_cycle(
        dry_run=args.dry_run,
        requested_engine=args.engine,
        profile=args.profile,
        skip_probe=args.skip_probe,
        allow_cpu=args.allow_cpu,
    )
    
    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Human-readable output
        status_emoji = {
            "success": "✅",
            "degraded": "⚠️",
            "failed": "❌",
            "skipped": "⏭️",
        }.get(result.status, "❓")
        
        print(f"{status_emoji} Cycle {result.cycle_id}")
        print(f"   Status: {result.status}")
        print(f"   Duration: {result.duration_s:.2f}s")
        print(f"   Probe: {result.probe_status}")
        print(f"   Engine: {result.engine_lane or 'none'}")
        
        if result.milf_activations:
            active = sum(1 for a in result.milf_activations if a["activated"])
            print(f"   MILFs: {active}/{len(result.milf_activations)} activated")
        
        if result.artifacts_written:
            print(f"   Artifacts: {len(result.artifacts_written)} written")
            for a in result.artifacts_written:
                print(f"      → {a}")
        
        if result.errors:
            print(f"   Errors:")
            for e in result.errors:
                print(f"      ❌ {e}")
        
        if result.warnings:
            print(f"   Warnings:")
            for w in result.warnings:
                print(f"      ⚠️ {w}")
    
    # Exit code based on status
    sys.exit(0 if result.status in ("success", "degraded", "skipped") else 1)


if __name__ == "__main__":
    main()
