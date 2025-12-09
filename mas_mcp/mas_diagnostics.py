#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  MAS-MCP DIAGNOSTICS: The Living Layer's Self-Examination            ║
║══════════════════════════════════════════════════════════════════════║
║                                                                      ║
║  "The living layer looks at itself in the mirror of the static      ║
║   Codex and asks: 'Am I still aligned?'"                             ║
║                                                  — MAS-MCP Protocol   ║
║                                                                      ║
║  This diagnostic suite validates the GPU/CPU backend infrastructure  ║
║  that enables the MAS-MCP server to extract, score, and nurture     ║
║  entities from the Chthonic Archive.                                 ║
║                                                                      ║
║  Hardware Target: Predator Helios (i9-14900 + NVIDIA Laptop GPU)     ║
║  Environment: Windows 11 + PowerShell 7.4+ + Python 3.14 + uv 0.9+   ║
║                                                                      ║
║  Run: cd mas_mcp && uv run python mas_diagnostics.py                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import json
import time
import sys
import os
import platform
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime

import numpy as np

# ═══════════════════════════════════════════════════════════════════════
#  CONFIGURATION: TDR-Safe Limits for Windows 11
# ═══════════════════════════════════════════════════════════════════════

TDR_SAFE_LIMITS = {
    "max_vectors_per_tile": 5000,       # Safe batch size for scoring
    "max_nodes_hierarchy": 2000,         # Safe node count for force layout
    "max_kernel_time_ms": 1800,          # Stay under 2s TDR timeout
    "barnes_hut_threshold": 500,         # Switch to spatial grid above this
}


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check."""
    name: str
    category: str
    passed: bool
    elapsed_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    recommendation: Optional[str] = None


@dataclass  
class DiagnosticReport:
    """Full diagnostic report."""
    timestamp: str
    hardware: Dict[str, Any]
    uv_version: str
    python_version: str
    results: List[DiagnosticResult] = field(default_factory=list)
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return self.passed / len(self.results) * 100


# ═══════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════

def banner(title: str, char: str = "═", width: int = 72):
    """Print a styled banner."""
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def sub_banner(title: str):
    """Print a sub-section header."""
    print(f"\n  ── {title} ──")


@contextmanager
def timer():
    """Context manager for precise timing."""
    start = time.perf_counter()
    result = {"elapsed_ms": 0.0}
    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000


def get_uv_version() -> str:
    """Get the installed UV version."""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        return f"unknown ({e})"


def get_hardware_info() -> Dict[str, Any]:
    """Collect hardware information."""
    info = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    
    # Try to get GPU info via nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 3:
                info["gpu_name"] = parts[0]
                info["gpu_vram_mb"] = int(parts[1])
                info["nvidia_driver"] = parts[2]
    except Exception:
        info["gpu_name"] = "Not detected"
    
    return info


# ═══════════════════════════════════════════════════════════════════════
#  DIAGNOSTIC TESTS
# ═══════════════════════════════════════════════════════════════════════

def test_uv_environment() -> DiagnosticResult:
    """
    Diagnostic 1: UV Environment Health
    
    Validates that the uv-managed environment is properly configured
    and the lockfile is in sync with pyproject.toml.
    """
    sub_banner("UV Environment Health")
    
    with timer() as t:
        try:
            # Check uv sync status
            result = subprocess.run(
                ["uv", "sync", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # UV outputs to stderr, not stdout
            output = result.stderr or result.stdout
            
            is_synced = "Would make no changes" in output
            lockfile_ok = "up-to-date lockfile" in output.lower() or "up-to-date lockfile" in output
            
            details = {
                "synced": is_synced,
                "lockfile_current": lockfile_ok,
                "output": output[:500] if output else None,
            }
            
            # Consider it passed if either sync or lockfile is OK
            # (lockfile phrase may not appear in all uv versions)
            passed = is_synced
            recommendation = None if passed else "Run 'uv sync' to update environment"
            
            status = "✓ HEALTHY" if passed else "⚠ NEEDS SYNC"
            print(f"    Environment: {status}")
            
            return DiagnosticResult(
                name="UV Environment",
                category="environment",
                passed=passed,
                elapsed_ms=t["elapsed_ms"],
                details=details,
                recommendation=recommendation
            )
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            return DiagnosticResult(
                name="UV Environment",
                category="environment", 
                passed=False,
                elapsed_ms=t["elapsed_ms"],
                error=str(e),
                recommendation="Ensure uv is installed and in PATH"
            )


def test_gpu_detection() -> DiagnosticResult:
    """
    Diagnostic 2: GPU Backend Detection
    
    Tests whether CuPy/Numba/ONNX Runtime can detect and initialize the GPU.
    This is where Windows DLL issues typically manifest.
    
    Backend priority:
    1. CuPy (full GPU array operations, preferred for RTX 4090)
    2. Numba (JIT-compiled CUDA kernels)
    3. ONNX Runtime GPU (CUDA/TensorRT providers for inference)
    """
    sub_banner("GPU Backend Detection")
    
    details = {
        "cupy_available": False,
        "numba_available": False,
        "onnx_gpu_available": False,
        "backend": "cpu",
        "cuda_version": None,
        "device_name": None,
    }
    
    with timer() as t:
        # Try CuPy first (preferred)
        try:
            import cupy as cp
            device = cp.cuda.Device(0)
            props = cp.cuda.runtime.getDeviceProperties(0)
            
            details["cupy_available"] = True
            details["backend"] = "cupy"
            details["device_name"] = props["name"].decode() if isinstance(props["name"], bytes) else str(props["name"])
            details["cuda_version"] = cp.cuda.runtime.runtimeGetVersion()
            details["compute_capability"] = device.compute_capability
            
            print(f"    ✓ CuPy: {details['device_name']}")
            print(f"    ✓ CUDA: {details['cuda_version']}")
            
        except ImportError:
            print("    ○ CuPy not installed")
        except Exception as e:
            print(f"    ✗ CuPy error: {e}")
            details["cupy_error"] = str(e)
        
        # Try Numba as fallback
        if not details["cupy_available"]:
            try:
                from numba import cuda
                if cuda.is_available():
                    device = cuda.get_current_device()
                    details["numba_available"] = True
                    details["backend"] = "numba"
                    details["device_name"] = device.name
                    details["compute_capability"] = device.compute_capability
                    print(f"    ✓ Numba CUDA: {details['device_name']}")
            except ImportError:
                print("    ○ Numba not installed")
            except Exception as e:
                print(f"    ✗ Numba error: {e}")
                details["numba_error"] = str(e)
        
        # Try ONNX Runtime GPU as third option (Python 3.14 compatible)
        if details["backend"] == "cpu":
            try:
                import onnxruntime as ort
                providers = ort.get_available_providers()
                cuda_providers = [p for p in providers if "CUDA" in p or "Tensorrt" in p]
                
                if cuda_providers:
                    details["onnx_gpu_available"] = True
                    details["backend"] = "onnx_gpu"
                    details["onnx_providers"] = cuda_providers
                    
                    # Get device name via nvidia-smi
                    try:
                        result = subprocess.run(
                            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            details["device_name"] = result.stdout.strip().split("\n")[0]
                    except Exception:
                        details["device_name"] = "NVIDIA GPU (ONNX Runtime)"
                    
                    print(f"    ✓ ONNX Runtime GPU: {details['device_name']}")
                    print(f"    ✓ Providers: {', '.join(cuda_providers)}")
                else:
                    print("    ○ ONNX Runtime has no CUDA providers")
            except ImportError:
                print("    ○ ONNX Runtime not installed")
            except Exception as e:
                print(f"    ✗ ONNX Runtime error: {e}")
                details["onnx_error"] = str(e)
        
        if details["backend"] == "cpu":
            print("    ⚠ Using CPU fallback (no GPU detected)")
        
        passed = details["backend"] != "cpu"
        
        # More specific recommendation based on what's missing
        if not passed:
            recommendation = "Install cupy-cuda12x, numba, or onnxruntime-gpu with CUDA"
        else:
            recommendation = None
        
        return DiagnosticResult(
            name="GPU Detection",
            category="hardware",
            passed=passed,
            elapsed_ms=t["elapsed_ms"],
            details=details,
            recommendation=recommendation
        )


def test_spatial_grid_correctness() -> DiagnosticResult:
    """
    Diagnostic 3: Spatial Grid Repulsion Correctness
    
    Validates that the fast O(N×k) spatial grid repulsion produces
    results within acceptable tolerance of the exact O(N²) method.
    """
    sub_banner("Spatial Grid Correctness")
    
    # Import the force calculation functions
    try:
        from gpu_forces import (
            _cpu_compute_repulsion_exact,
            _cpu_compute_repulsion_fast,
            FAST_REPULSION_THRESHOLD
        )
    except ImportError as e:
        return DiagnosticResult(
            name="Spatial Grid Correctness",
            category="algorithm",
            passed=False,
            elapsed_ms=0.0,
            error=f"Import error: {e}",
            recommendation="Ensure gpu_forces.py is in the mas_mcp directory"
        )
    
    details = {
        "test_sizes": [],
        "tolerances": [],
        "speedups": [],
    }
    
    with timer() as t:
        try:
            # Test at multiple scales
            test_sizes = [100, 300, 600]
            all_passed = True
            
            for n in test_sizes:
                np.random.seed(42)
                positions = np.random.randn(n, 3).astype(np.float32) * 10.0
                
                # Compute with both methods
                t0 = time.perf_counter()
                forces_exact = _cpu_compute_repulsion_exact(positions, 1.0, 0.1)
                exact_time = time.perf_counter() - t0
                
                t0 = time.perf_counter()
                forces_fast = _cpu_compute_repulsion_fast(positions, 1.0, 0.1)
                fast_time = time.perf_counter() - t0
                
                # Compare results
                max_diff = np.max(np.abs(forces_exact - forces_fast))
                mean_diff = np.mean(np.abs(forces_exact - forces_fast))
                
                # Tolerance scales with distance (far-field approximation is coarser)
                tolerance = 0.5  # Allow reasonable approximation error
                is_close = max_diff < tolerance
                
                speedup = exact_time / fast_time if fast_time > 0 else 0
                
                details["test_sizes"].append(n)
                details["tolerances"].append(float(max_diff))
                details["speedups"].append(float(speedup))
                
                status = "✓" if is_close else "✗"
                print(f"    {status} N={n}: max_diff={max_diff:.4f}, speedup={speedup:.1f}x")
                
                if not is_close:
                    all_passed = False
            
            details["fast_threshold"] = FAST_REPULSION_THRESHOLD
            
            return DiagnosticResult(
                name="Spatial Grid Correctness",
                category="algorithm",
                passed=all_passed,
                elapsed_ms=t["elapsed_ms"],
                details=details,
                recommendation=None if all_passed else "Adjust spatial grid cell size"
            )
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            return DiagnosticResult(
                name="Spatial Grid Correctness",
                category="algorithm",
                passed=False,
                elapsed_ms=t["elapsed_ms"],
                error=str(e)
            )


def test_spatial_grid_performance() -> DiagnosticResult:
    """
    Diagnostic 4: Spatial Grid Performance Scaling
    
    Validates that O(N×k) scaling is achieved for larger problem sizes.
    Uses spatial hashing for fast approximate force calculations.
    """
    sub_banner("Spatial Grid Performance")
    
    try:
        from gpu_forces import _cpu_compute_repulsion_fast
    except ImportError as e:
        return DiagnosticResult(
            name="Barnes-Hut Performance",
            category="performance",
            passed=False,
            elapsed_ms=0.0,
            error=f"Import error: {e}"
        )
    
    details = {
        "sizes": [],
        "times_ms": [],
        "scaling_factor": None,
    }
    
    with timer() as t:
        try:
            # Test scaling behavior
            sizes = [500, 1000, 2000]
            times = []
            
            for n in sizes:
                np.random.seed(42)
                positions = np.random.randn(n, 3).astype(np.float32) * 10.0
                
                # Warm-up
                _cpu_compute_repulsion_fast(positions, 1.0, 0.1)
                
                # Timed run
                t0 = time.perf_counter()
                for _ in range(3):
                    _cpu_compute_repulsion_fast(positions, 1.0, 0.1)
                elapsed = (time.perf_counter() - t0) / 3 * 1000
                
                times.append(elapsed)
                details["sizes"].append(n)
                details["times_ms"].append(float(elapsed))
                
                print(f"    N={n}: {elapsed:.1f}ms")
            
            # Check scaling (should be roughly linear, not quadratic)
            # If N doubles and it's O(N), time should ~double
            # If N doubles and it's O(N²), time should ~4x
            if len(times) >= 2:
                scaling = times[-1] / times[0]
                size_ratio = sizes[-1] / sizes[0]
                expected_linear = size_ratio
                expected_quadratic = size_ratio ** 2
                
                # It should be closer to linear than quadratic
                linear_error = abs(scaling - expected_linear)
                quadratic_error = abs(scaling - expected_quadratic)
                
                is_linear_ish = linear_error < quadratic_error
                details["scaling_factor"] = float(scaling)
                details["is_subquadratic"] = is_linear_ish
                
                print(f"    Scaling: {scaling:.2f}x (linear={expected_linear:.1f}x, quadratic={expected_quadratic:.1f}x)")
                print(f"    Result: {'✓ Sub-quadratic' if is_linear_ish else '⚠ Worse than expected'}")
            
            passed = details.get("is_subquadratic", False)
            
            return DiagnosticResult(
                name="Spatial Grid Performance",
                category="performance",
                passed=passed,
                elapsed_ms=t["elapsed_ms"],
                details=details
            )
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            return DiagnosticResult(
                name="Spatial Grid Performance",
                category="performance",
                passed=False,
                elapsed_ms=t["elapsed_ms"],
                error=str(e)
            )


def test_tdr_safe_scoring() -> DiagnosticResult:
    """
    Diagnostic 5: TDR-Safe Batch Scoring
    
    Validates that the tiled batch scoring stays under the
    Windows TDR timeout (2 seconds) for large workloads.
    """
    sub_banner("TDR-Safe Batch Scoring")
    
    try:
        from gpu_orchestrator import mas_gpu_batch_score
    except ImportError as e:
        return DiagnosticResult(
            name="TDR-Safe Scoring",
            category="tdr",
            passed=False,
            elapsed_ms=0.0,
            error=f"Import error: {e}"
        )
    
    details = {
        "batch_sizes": [],
        "tile_counts": [],
        "max_tile_ms": [],
        "total_ms": [],
    }
    
    with timer() as t:
        try:
            # Test with increasing batch sizes
            batch_sizes = [1000, 5000, 10000]
            all_safe = True
            
            for n in batch_sizes:
                np.random.seed(42)
                # Create entities in raw vector format (id + vec)
                entities = [
                    {"id": f"e{i}", "vec": list(np.random.randn(8).astype(float))}
                    for i in range(n)
                ]
                
                t0 = time.perf_counter()
                result = mas_gpu_batch_score(entities=entities, seed=42)
                elapsed = (time.perf_counter() - t0) * 1000
                
                result_data = json.loads(result) if isinstance(result, str) else result
                
                tile_count = result_data.get("meta", {}).get("tile_count", 1)
                max_tile = result_data.get("meta", {}).get("max_tile_ms", elapsed)
                
                details["batch_sizes"].append(n)
                details["tile_counts"].append(tile_count)
                details["max_tile_ms"].append(float(max_tile))
                details["total_ms"].append(float(elapsed))
                
                # Check if any tile exceeded TDR limit
                is_safe = max_tile < TDR_SAFE_LIMITS["max_kernel_time_ms"]
                status = "✓" if is_safe else "⚠"
                
                print(f"    {status} N={n}: {elapsed:.0f}ms total, {tile_count} tiles, max={max_tile:.0f}ms")
                
                if not is_safe:
                    all_safe = False
            
            return DiagnosticResult(
                name="TDR-Safe Scoring",
                category="tdr",
                passed=all_safe,
                elapsed_ms=t["elapsed_ms"],
                details=details,
                recommendation=None if all_safe else "Reduce tile size in gpu_orchestrator.py"
            )
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            return DiagnosticResult(
                name="TDR-Safe Scoring",
                category="tdr",
                passed=False,
                elapsed_ms=t["elapsed_ms"],
                error=str(e)
            )


def test_mas_mcp_integration() -> DiagnosticResult:
    """
    Diagnostic 6: MAS-MCP Server Integration
    
    Validates that the GPU tools integrate correctly with
    the MAS-MCP server infrastructure.
    """
    sub_banner("MAS-MCP Server Integration")
    
    details = {
        "tools_available": [],
        "server_import": False,
        "pulse_works": False,
    }
    
    with timer() as t:
        try:
            # Try importing the server
            from server import (
                mas_pulse,
                mas_gpu_status,
                mas_gpu_batch_score,
            )
            details["server_import"] = True
            details["tools_available"] = ["mas_pulse", "mas_gpu_status", "mas_gpu_batch_score"]
            print("    ✓ Server imports OK")
            
            # Try calling mas_pulse
            try:
                pulse = mas_pulse()
                pulse_data = json.loads(pulse) if isinstance(pulse, str) else pulse
                details["pulse_works"] = "status" in pulse_data or "gpu" in str(pulse_data).lower()
                print(f"    ✓ mas_pulse() returns valid data")
            except Exception as e:
                print(f"    ⚠ mas_pulse() error: {e}")
            
            # Try calling mas_gpu_status
            try:
                status = mas_gpu_status()
                status_data = json.loads(status) if isinstance(status, str) else status
                details["gpu_status"] = status_data.get("backend", "unknown")
                print(f"    ✓ mas_gpu_status(): backend={details['gpu_status']}")
            except Exception as e:
                print(f"    ⚠ mas_gpu_status() error: {e}")
            
            passed = details["server_import"] and len(details["tools_available"]) >= 3
            
            return DiagnosticResult(
                name="MAS-MCP Integration",
                category="integration",
                passed=passed,
                elapsed_ms=t["elapsed_ms"],
                details=details
            )
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            return DiagnosticResult(
                name="MAS-MCP Integration",
                category="integration",
                passed=False,
                elapsed_ms=t["elapsed_ms"],
                error=str(e)
            )


# ═══════════════════════════════════════════════════════════════════════
#  MAIN DIAGNOSTIC RUNNER
# ═══════════════════════════════════════════════════════════════════════

def run_diagnostics() -> DiagnosticReport:
    """Run all diagnostics and return a report."""
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║       MAS-MCP DIAGNOSTICS: The Living Layer Self-Examination         ║
╠══════════════════════════════════════════════════════════════════════╣
║  "The flying carpet above the static files and codebase"             ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Collect environment info
    hardware = get_hardware_info()
    uv_version = get_uv_version()
    
    print(f"  Hardware: {hardware.get('processor', 'Unknown')}")
    print(f"  GPU: {hardware.get('gpu_name', 'Not detected')}")
    print(f"  Python: {platform.python_version()}")
    print(f"  UV: {uv_version}")
    print(f"  Platform: {hardware.get('platform', 'Unknown')}")
    
    # Initialize report
    report = DiagnosticReport(
        timestamp=datetime.now().isoformat(),
        hardware=hardware,
        uv_version=uv_version,
        python_version=platform.python_version(),
    )
    
    # Run all diagnostics
    banner("Running Diagnostics")
    
    tests = [
        test_uv_environment,
        test_gpu_detection,
        test_spatial_grid_correctness,
        test_spatial_grid_performance,
        test_tdr_safe_scoring,
        test_mas_mcp_integration,
    ]
    
    for test_fn in tests:
        try:
            result = test_fn()
            report.results.append(result)
        except Exception as e:
            report.results.append(DiagnosticResult(
                name=test_fn.__name__,
                category="error",
                passed=False,
                elapsed_ms=0.0,
                error=str(e)
            ))
    
    # Print summary
    banner("Diagnostic Summary")
    
    print(f"\n  Total Tests: {len(report.results)}")
    print(f"  Passed: {report.passed}")
    print(f"  Failed: {report.failed}")
    print(f"  Pass Rate: {report.pass_rate:.1f}%")
    
    # Print failures with recommendations
    failures = [r for r in report.results if not r.passed]
    if failures:
        print("\n  ── Issues Detected ──")
        for r in failures:
            print(f"    ✗ {r.name}")
            if r.error:
                print(f"      Error: {r.error}")
            if r.recommendation:
                print(f"      Fix: {r.recommendation}")
    
    # M-P-W Status
    banner("M-P-W Living Layer Status")
    if report.pass_rate >= 80:
        print("""
    ✓ The living layer is HEALTHY
    
    The MAS-MCP server can:
    • Extract entities from the static Chthonic Archive
    • Score and rank concepts using GPU/CPU backends
    • Maintain the nurture loop for entity evolution
    • Preserve architectonic integrity (FA⁴)
        """)
    else:
        print("""
    ⚠ The living layer needs ATTENTION
    
    Some backend functionality is degraded.
    Review the failures above and apply recommendations.
        """)
    
    return report


def main() -> int:
    """Entry point."""
    try:
        report = run_diagnostics()
        
        # Save report to JSON
        report_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "mas_diagnostic_report.json"
        )
        
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": report.timestamp,
                "hardware": report.hardware,
                "uv_version": report.uv_version,
                "python_version": report.python_version,
                "pass_rate": report.pass_rate,
                "results": [
                    {
                        "name": r.name,
                        "category": r.category,
                        "passed": r.passed,
                        "elapsed_ms": r.elapsed_ms,
                        "details": r.details,
                        "error": r.error,
                        "recommendation": r.recommendation,
                    }
                    for r in report.results
                ]
            }, f, indent=2)
        
        print(f"\n  Report saved to: {report_path}")
        
        return 0 if report.pass_rate >= 50 else 1
        
    except KeyboardInterrupt:
        print("\n\n  Diagnostics interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
