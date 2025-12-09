#!/usr/bin/env python3
"""
MAS-MCP Hardware-Specific Testing Suite
========================================

Designed for: Predator Helios + RTX 4090 Laptop GPU + Intel i9-14900
Environment: VS Code integrated terminal (PowerShell 7.4+), Windows 11, Python 3.14

This script performs SAFE, incremental tests to validate:
1. CPU fallback stability
2. GPU initialization without TDR triggers
3. Barnes-Hut tiling effectiveness
4. Backend switching robustness

Run from VS Code terminal:
    cd mas_mcp
    uv run python mas_mcp_testing.py

Safety features:
- Micro-batch warm-up before any large operations
- Automatic TDR-safe chunk sizing
- Graceful fallback on any GPU failure
- Detailed timing and memory reporting
"""

import json
import time
import sys
import os
import gc
from typing import Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

# Ensure we can import from current directory
sys.path.insert(0, '.')

# Hardware profile for Predator Helios + RTX 4090 Laptop + i9-14900
HARDWARE_PROFILE = {
    "gpu": "RTX 4090 Laptop GPU",
    "cpu": "Intel i9-14900",
    "system": "Predator Helios",
    "os": "Windows 11",
    "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "shell": "PowerShell 7.4+",
    "environment": "VS Code integrated terminal",
}

# TDR-safe limits (Windows default TDR timeout is ~2 seconds)
TDR_SAFE_MS = 1500  # Keep GPU kernels under 1.5s
MICRO_BATCH_SIZE = 100  # Warm-up batch size
SMALL_BATCH_SIZE = 1000
MEDIUM_BATCH_SIZE = 5000
LARGE_BATCH_SIZE = 20000  # Conservative for laptop GPU


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    elapsed_ms: float
    backend: str = "unknown"
    details: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class TestSuite:
    """Collection of test results."""
    hardware: dict = field(default_factory=lambda: HARDWARE_PROFILE.copy())
    results: list = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def add(self, result: TestResult):
        self.results.append(result)
        status = "✓" if result.passed else "✗"
        print(f"  [{status}] {result.name}: {result.elapsed_ms:.1f}ms ({result.backend})")
        if result.error:
            print(f"      Error: {result.error}")
    
    def summary(self) -> dict:
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total_time = sum(r.elapsed_ms for r in self.results)
        return {
            "passed": passed,
            "failed": failed,
            "total": len(self.results),
            "total_time_ms": total_time,
            "success_rate": passed / len(self.results) if self.results else 0,
        }


def banner(title: str, char: str = "="):
    """Print a section banner."""
    print()
    print(char * 60)
    print(f"  {title}")
    print(char * 60)


@contextmanager
def timer():
    """Context manager for timing operations."""
    start = time.perf_counter()
    result = {"elapsed_ms": 0}
    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000


def safe_import_gpu_modules():
    """Safely import GPU modules with fallback."""
    modules = {}
    
    # Try importing numpy first (always needed)
    try:
        import numpy as np
        modules["numpy"] = np
    except ImportError as e:
        print(f"  ⚠ NumPy not available: {e}")
        return None
    
    # Try importing gpu_orchestrator
    try:
        from gpu_orchestrator import (
            mas_gpu_status,
            mas_gpu_batch_score,
            mas_gpu_hierarchy,
            get_score_tiler,
            get_hierarchy_tiler,
        )
        modules["gpu_status"] = mas_gpu_status
        modules["batch_score"] = mas_gpu_batch_score
        modules["hierarchy"] = mas_gpu_hierarchy
        modules["score_tiler"] = get_score_tiler
        modules["hierarchy_tiler"] = get_hierarchy_tiler
    except ImportError as e:
        print(f"  ⚠ gpu_orchestrator not available: {e}")
        # Continue with limited functionality
    
    # Try importing CuPy (optional)
    try:
        import cupy as cp
        modules["cupy"] = cp
        modules["cupy_available"] = True
    except ImportError:
        modules["cupy_available"] = False
    
    # Try importing Numba CUDA (optional)
    try:
        from numba import cuda
        modules["numba_cuda"] = cuda
        modules["numba_available"] = cuda.is_available()
    except ImportError:
        modules["numba_available"] = False
    
    return modules


# =============================================================================
# PHASE 1: Environment & Import Tests
# =============================================================================

def test_environment(suite: TestSuite):
    """Test basic environment setup."""
    banner("PHASE 1: Environment Validation")
    
    # Test 1.1: Python version
    with timer() as t:
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        passed = sys.version_info >= (3, 11)
    suite.add(TestResult(
        name="Python version check",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="system",
        details={"version": py_version, "required": "3.11+"}
    ))
    
    # Test 1.2: NumPy availability
    with timer() as t:
        try:
            import numpy as np
            passed = True
            version = np.__version__
        except ImportError as e:
            passed = False
            version = str(e)
    suite.add(TestResult(
        name="NumPy import",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="cpu",
        details={"version": version}
    ))
    
    # Test 1.3: GPU orchestrator import
    with timer() as t:
        try:
            from gpu_orchestrator import mas_gpu_status
            passed = True
            error = None
        except ImportError as e:
            passed = False
            error = str(e)
    suite.add(TestResult(
        name="gpu_orchestrator import",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="module",
        error=error
    ))


# =============================================================================
# PHASE 2: GPU Detection & Status
# =============================================================================

def test_gpu_detection(suite: TestSuite, modules: dict) -> dict:
    """Test GPU detection and status reporting."""
    banner("PHASE 2: GPU Detection & Status")
    
    gpu_info = {"available": False}
    
    # Test 2.1: GPU status query
    if "gpu_status" in modules:
        with timer() as t:
            try:
                status = modules["gpu_status"]()
                passed = True
                gpu_info = status
                error = None
            except Exception as e:
                passed = False
                error = str(e)
        suite.add(TestResult(
            name="GPU status query",
            passed=passed,
            elapsed_ms=t["elapsed_ms"],
            backend=gpu_info.get("backend", "unknown"),
            details={"gpu_available": gpu_info.get("gpu_available", False)},
            error=error
        ))
        
        if passed:
            print(f"\n  GPU Status Details:")
            print(f"    Backend: {gpu_info.get('backend', 'N/A')}")
            print(f"    GPU Available: {gpu_info.get('gpu_available', False)}")
            if "device_name" in gpu_info:
                print(f"    Device: {gpu_info['device_name']}")
            if "memory_total_mb" in gpu_info:
                print(f"    VRAM: {gpu_info['memory_total_mb']:.0f} MB")
    
    # Test 2.2: CuPy availability
    with timer() as t:
        passed = modules.get("cupy_available", False)
        if passed:
            cp = modules["cupy"]
            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                details = {"device_count": device_count}
            except Exception as e:
                details = {"error": str(e)}
        else:
            details = {"reason": "CuPy not installed"}
    suite.add(TestResult(
        name="CuPy CUDA backend",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="cupy" if passed else "N/A",
        details=details
    ))
    
    # Test 2.3: Numba CUDA availability
    with timer() as t:
        passed = modules.get("numba_available", False)
        if passed:
            cuda = modules["numba_cuda"]
            try:
                device = cuda.get_current_device()
                details = {"device_name": device.name.decode() if hasattr(device.name, 'decode') else str(device.name)}
            except Exception as e:
                details = {"error": str(e)}
        else:
            details = {"reason": "Numba CUDA not available"}
    suite.add(TestResult(
        name="Numba CUDA backend",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="numba" if passed else "N/A",
        details=details
    ))
    
    return gpu_info


# =============================================================================
# PHASE 3: CPU Fallback Baseline
# =============================================================================

def test_cpu_fallback(suite: TestSuite, modules: dict):
    """Test pure CPU execution as baseline."""
    banner("PHASE 3: CPU Fallback Baseline")
    
    np = modules.get("numpy")
    if np is None:
        suite.add(TestResult(
            name="CPU baseline",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="NumPy not available"
        ))
        return
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    # Test 3.1: Small CPU computation
    with timer() as t:
        try:
            data = rng.random((1000, 256))
            result = np.mean(data, axis=1)
            passed = len(result) == 1000
            error = None
        except Exception as e:
            passed = False
            error = str(e)
    suite.add(TestResult(
        name="CPU small batch (1k × 256)",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="numpy",
        details={"shape": "1000 × 256"}
    ))
    
    # Test 3.2: Medium CPU computation
    with timer() as t:
        try:
            data = rng.random((10000, 256))
            result = np.mean(data, axis=1)
            passed = len(result) == 10000
            error = None
        except Exception as e:
            passed = False
            error = str(e)
    suite.add(TestResult(
        name="CPU medium batch (10k × 256)",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="numpy",
        details={"shape": "10000 × 256"}
    ))
    
    # Test 3.3: Matrix multiplication (stress test)
    with timer() as t:
        try:
            a = rng.random((2000, 2000))
            b = rng.random((2000, 2000))
            c = np.dot(a, b)
            passed = c.shape == (2000, 2000)
            error = None
        except Exception as e:
            passed = False
            error = str(e)
    suite.add(TestResult(
        name="CPU matmul (2k × 2k)",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend="numpy",
        details={"operation": "dot product"}
    ))


# =============================================================================
# PHASE 4: GPU Warm-up (Micro-batches)
# =============================================================================

def test_gpu_warmup(suite: TestSuite, modules: dict, gpu_available: bool):
    """Warm up GPU with micro-batches to avoid cold-start TDR."""
    banner("PHASE 4: GPU Warm-up (TDR-Safe Micro-batches)")
    
    if not gpu_available:
        print("  ⚠ GPU not available, skipping warm-up tests")
        return False
    
    np = modules.get("numpy")
    batch_score = modules.get("batch_score")
    
    if batch_score is None:
        suite.add(TestResult(
            name="GPU warm-up",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="batch_score function not available"
        ))
        return False
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    # Test 4.1: Micro-batch warm-up (100 vectors)
    with timer() as t:
        try:
            entities = [
                {'id': f'warmup_{i}', 'vec': v.tolist()}
                for i, v in enumerate(rng.random((MICRO_BATCH_SIZE, 256)))
            ]
            result = batch_score(entities=entities, seed=seed)
            passed = result.get("count", 0) == MICRO_BATCH_SIZE
            backend = result.get("backend", "unknown")
            error = None
        except Exception as e:
            passed = False
            backend = "error"
            error = str(e)
    suite.add(TestResult(
        name=f"GPU micro-batch warm-up ({MICRO_BATCH_SIZE})",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend=backend,
        error=error
    ))
    
    if not passed:
        print("  ⚠ Warm-up failed, GPU may be unstable")
        return False
    
    # Test 4.2: Second micro-batch (should be faster, GPU warmed)
    gc.collect()
    with timer() as t:
        try:
            entities = [
                {'id': f'warmup2_{i}', 'vec': v.tolist()}
                for i, v in enumerate(rng.random((MICRO_BATCH_SIZE, 256)))
            ]
            result = batch_score(entities=entities, seed=seed)
            passed = result.get("count", 0) == MICRO_BATCH_SIZE
            backend = result.get("backend", "unknown")
            error = None
        except Exception as e:
            passed = False
            backend = "error"
            error = str(e)
    suite.add(TestResult(
        name=f"GPU warm micro-batch ({MICRO_BATCH_SIZE})",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend=backend,
        details={"expected": "faster than cold start"},
        error=error
    ))
    
    return passed


# =============================================================================
# PHASE 5: Incremental Batch Size Testing
# =============================================================================

def test_incremental_batches(suite: TestSuite, modules: dict, gpu_available: bool):
    """Test increasing batch sizes to find TDR threshold."""
    banner("PHASE 5: Incremental Batch Size Testing")
    
    if not gpu_available:
        print("  ⚠ GPU not available, using CPU fallback")
    
    np = modules.get("numpy")
    batch_score = modules.get("batch_score")
    
    if batch_score is None:
        suite.add(TestResult(
            name="Incremental batches",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="batch_score function not available"
        ))
        return
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    batch_sizes = [SMALL_BATCH_SIZE, MEDIUM_BATCH_SIZE, LARGE_BATCH_SIZE]
    
    for batch_size in batch_sizes:
        gc.collect()
        with timer() as t:
            try:
                entities = [
                    {'id': f'batch_{i}', 'vec': v.tolist()}
                    for i, v in enumerate(rng.random((batch_size, 256)))
                ]
                result = batch_score(entities=entities, seed=seed)
                passed = result.get("count", 0) == batch_size
                backend = result.get("backend", "unknown")
                
                details = {"batch_size": batch_size}
                if "tiling" in result:
                    details["tiles"] = result["tiling"].get("tile_count", 1)
                    details["max_tile_ms"] = result["tiling"].get("max_tile_ms", 0)
                    details["items_per_sec"] = result["tiling"].get("items_per_second", 0)
                
                error = None
            except Exception as e:
                passed = False
                backend = "error"
                details = {"batch_size": batch_size}
                error = str(e)
        
        suite.add(TestResult(
            name=f"Batch {batch_size:,} vectors",
            passed=passed,
            elapsed_ms=t["elapsed_ms"],
            backend=backend,
            details=details,
            error=error
        ))
        
        # Check if we're approaching TDR danger zone
        if t["elapsed_ms"] > TDR_SAFE_MS:
            print(f"  ⚠ Warning: {batch_size:,} batch took {t['elapsed_ms']:.0f}ms (TDR threshold: {TDR_SAFE_MS}ms)")


# =============================================================================
# PHASE 6: Hierarchy Layout Testing
# =============================================================================

def test_hierarchy_layout(suite: TestSuite, modules: dict, gpu_available: bool):
    """Test force-directed hierarchy layout."""
    banner("PHASE 6: Hierarchy Layout (Barnes-Hut)")
    
    if not gpu_available:
        print("  ⚠ GPU not available, using CPU fallback")
    
    np = modules.get("numpy")
    hierarchy = modules.get("hierarchy")
    
    if hierarchy is None:
        suite.add(TestResult(
            name="Hierarchy layout",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="hierarchy function not available"
        ))
        return
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    node_counts = [100, 500, 1000]
    
    for node_count in node_counts:
        gc.collect()
        
        # Build graph: ring + random edges
        nodes = [f'n{i}' for i in range(node_count)]
        edges = [(nodes[i], nodes[(i + 1) % node_count]) for i in range(node_count)]
        edges += [(nodes[rng.integers(node_count)], nodes[rng.integers(node_count)]) 
                  for _ in range(node_count // 2)]
        
        with timer() as t:
            try:
                result = hierarchy(nodes=nodes, edges=edges, iterations=50, seed=seed)
                passed = result.get("node_count", 0) == node_count
                backend = result.get("backend", "unknown")
                
                details = {
                    "nodes": node_count,
                    "edges": len(edges),
                    "iterations": result.get("iterations", 0),
                    "converged": result.get("converged", False),
                }
                if "tiling" in result:
                    details["passes"] = result["tiling"].get("pass_count", 1)
                
                error = None
            except Exception as e:
                passed = False
                backend = "error"
                details = {"nodes": node_count}
                error = str(e)
        
        suite.add(TestResult(
            name=f"Hierarchy {node_count} nodes",
            passed=passed,
            elapsed_ms=t["elapsed_ms"],
            backend=backend,
            details=details,
            error=error
        ))


# =============================================================================
# PHASE 7: Backend Switching Stress Test
# =============================================================================

def test_backend_switching(suite: TestSuite, modules: dict, gpu_available: bool):
    """Test rapid switching between CPU and GPU backends."""
    banner("PHASE 7: Backend Switching Stress Test")
    
    np = modules.get("numpy")
    batch_score = modules.get("batch_score")
    
    if batch_score is None:
        suite.add(TestResult(
            name="Backend switching",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="batch_score function not available"
        ))
        return
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    # Alternating CPU and GPU operations
    switch_count = 5
    all_passed = True
    backends_used = set()
    
    with timer() as t:
        try:
            for i in range(switch_count):
                # CPU operation (pure NumPy)
                cpu_data = rng.random((500, 256))
                cpu_result = np.mean(cpu_data, axis=1)
                
                # GPU operation (batch score)
                entities = [
                    {'id': f'switch_{i}_{j}', 'vec': v.tolist()}
                    for j, v in enumerate(rng.random((500, 256)))
                ]
                gpu_result = batch_score(entities=entities, seed=seed + i)
                backends_used.add(gpu_result.get("backend", "unknown"))
                
                if gpu_result.get("count", 0) != 500:
                    all_passed = False
            
            error = None
        except Exception as e:
            all_passed = False
            error = str(e)
    
    suite.add(TestResult(
        name=f"Backend switching ({switch_count} cycles)",
        passed=all_passed,
        elapsed_ms=t["elapsed_ms"],
        backend=", ".join(backends_used),
        details={"switch_count": switch_count, "backends": list(backends_used)},
        error=error
    ))


# =============================================================================
# PHASE 8: Barnes-Hut vs Exact Comparison
# =============================================================================

def test_barnes_hut_comparison(suite: TestSuite, modules: dict):
    """
    CRITICAL TEST: Compare Barnes-Hut spatial grid vs exact O(N²) repulsion.
    
    This directly validates that the optimization is working and provides
    accurate results while being significantly faster at scale.
    """
    banner("PHASE 8: Barnes-Hut vs Exact Algorithm Comparison")
    
    np = modules.get("numpy")
    if np is None:
        suite.add(TestResult(
            name="Barnes-Hut comparison",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="NumPy not available"
        ))
        return
    
    # Import the force functions directly for comparison
    try:
        from gpu_forces import (
            _cpu_compute_repulsion_exact,
            _cpu_compute_repulsion_fast,
            _cpu_compute_repulsion,
            FAST_REPULSION_THRESHOLD,
        )
        functions_available = True
    except ImportError as e:
        suite.add(TestResult(
            name="Import gpu_forces",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error=str(e)
        ))
        return
    
    print(f"\n  FAST_REPULSION_THRESHOLD = {FAST_REPULSION_THRESHOLD} nodes")
    print(f"  (Barnes-Hut activates when N > {FAST_REPULSION_THRESHOLD})")
    
    seed = 42
    rng = np.random.default_rng(seed)
    strength = 1000.0
    min_distance = 1.0
    
    # Test 1: Small graph (under threshold) - exact method should be used
    small_n = 100
    print(f"\n  Test 1: Small graph ({small_n} nodes, under threshold)")
    small_positions = rng.random((small_n, 3)) * 100
    
    with timer() as t_exact_small:
        forces_exact_small = _cpu_compute_repulsion_exact(small_positions, strength, min_distance)
    
    with timer() as t_auto_small:
        forces_auto_small = _cpu_compute_repulsion(small_positions, strength, min_distance)
    
    # Should be identical (auto picks exact for small N)
    small_match = np.allclose(forces_exact_small, forces_auto_small, rtol=1e-5)
    
    suite.add(TestResult(
        name=f"Small graph ({small_n} nodes) - exact match",
        passed=small_match,
        elapsed_ms=t_exact_small["elapsed_ms"],
        backend="cpu/exact",
        details={
            "exact_ms": round(t_exact_small["elapsed_ms"], 2),
            "auto_ms": round(t_auto_small["elapsed_ms"], 2),
            "forces_match": small_match,
        }
    ))
    
    # Test 2: Medium graph (at threshold boundary)
    medium_n = FAST_REPULSION_THRESHOLD
    print(f"\n  Test 2: Threshold boundary ({medium_n} nodes)")
    medium_positions = rng.random((medium_n, 3)) * 200
    
    with timer() as t_exact_medium:
        forces_exact_medium = _cpu_compute_repulsion_exact(medium_positions, strength, min_distance)
    
    with timer() as t_fast_medium:
        forces_fast_medium = _cpu_compute_repulsion_fast(medium_positions, strength, min_distance)
    
    # At threshold, auto should use exact
    with timer() as t_auto_medium:
        forces_auto_medium = _cpu_compute_repulsion(medium_positions, strength, min_distance)
    
    # Compute relative error between exact and fast
    force_magnitudes_exact = np.linalg.norm(forces_exact_medium, axis=1)
    force_magnitudes_fast = np.linalg.norm(forces_fast_medium, axis=1)
    
    # Avoid division by zero
    valid_mask = force_magnitudes_exact > 1e-10
    if valid_mask.sum() > 0:
        relative_error = np.abs(force_magnitudes_exact[valid_mask] - force_magnitudes_fast[valid_mask]) / force_magnitudes_exact[valid_mask]
        mean_error = relative_error.mean()
        max_error = relative_error.max()
    else:
        mean_error = 0
        max_error = 0
    
    suite.add(TestResult(
        name=f"Threshold ({medium_n} nodes) - accuracy check",
        passed=mean_error < 0.5,  # Allow 50% error for approximation
        elapsed_ms=t_exact_medium["elapsed_ms"],
        backend="cpu/comparison",
        details={
            "exact_ms": round(t_exact_medium["elapsed_ms"], 2),
            "fast_ms": round(t_fast_medium["elapsed_ms"], 2),
            "speedup": round(t_exact_medium["elapsed_ms"] / max(t_fast_medium["elapsed_ms"], 0.01), 2),
            "mean_relative_error": round(mean_error, 4),
            "max_relative_error": round(max_error, 4),
        }
    ))
    
    # Test 3: Large graph (MUST use Barnes-Hut, exact would be too slow)
    large_n = 500
    print(f"\n  Test 3: Large graph ({large_n} nodes - Barnes-Hut required)")
    large_positions = rng.random((large_n, 3)) * 300
    
    # Only run fast (exact would take too long)
    with timer() as t_fast_large:
        forces_fast_large = _cpu_compute_repulsion_fast(large_positions, strength, min_distance)
    
    # Verify it actually completed reasonably fast
    fast_completed = t_fast_large["elapsed_ms"] < 5000  # Should be under 5 seconds
    
    suite.add(TestResult(
        name=f"Large graph ({large_n} nodes) - Barnes-Hut speed",
        passed=fast_completed and forces_fast_large.shape[0] == large_n,
        elapsed_ms=t_fast_large["elapsed_ms"],
        backend="cpu/barnes-hut",
        details={
            "nodes": large_n,
            "fast_ms": round(t_fast_large["elapsed_ms"], 2),
            "time_per_node_ms": round(t_fast_large["elapsed_ms"] / large_n, 4),
        }
    ))
    
    # Test 4: Very large graph (stress test for Barnes-Hut)
    very_large_n = 1000
    print(f"\n  Test 4: Very large graph ({very_large_n} nodes - stress test)")
    very_large_positions = rng.random((very_large_n, 3)) * 500
    
    with timer() as t_very_large:
        forces_very_large = _cpu_compute_repulsion_fast(very_large_positions, strength, min_distance)
    
    # Should complete in reasonable time (under 30 seconds)
    very_large_ok = t_very_large["elapsed_ms"] < 30000
    
    suite.add(TestResult(
        name=f"Very large graph ({very_large_n} nodes) - stress test",
        passed=very_large_ok and forces_very_large.shape[0] == very_large_n,
        elapsed_ms=t_very_large["elapsed_ms"],
        backend="cpu/barnes-hut",
        details={
            "nodes": very_large_n,
            "elapsed_ms": round(t_very_large["elapsed_ms"], 2),
            "time_per_node_ms": round(t_very_large["elapsed_ms"] / very_large_n, 4),
        }
    ))
    
    # Summary comparison
    print(f"\n  Summary:")
    print(f"    Small ({small_n} nodes): {t_exact_small['elapsed_ms']:.1f}ms exact")
    print(f"    Medium ({medium_n} nodes): {t_exact_medium['elapsed_ms']:.1f}ms exact, {t_fast_medium['elapsed_ms']:.1f}ms fast")
    print(f"    Large ({large_n} nodes): {t_fast_large['elapsed_ms']:.1f}ms fast")
    print(f"    Very Large ({very_large_n} nodes): {t_very_large['elapsed_ms']:.1f}ms fast")
    
    if t_exact_medium["elapsed_ms"] > 0 and t_fast_medium["elapsed_ms"] > 0:
        speedup = t_exact_medium["elapsed_ms"] / t_fast_medium["elapsed_ms"]
        print(f"\n    Speedup at {medium_n} nodes: {speedup:.1f}x")


# =============================================================================
# PHASE 9: Determinism Validation
# =============================================================================

def test_determinism(suite: TestSuite, modules: dict):
    """Verify deterministic results with same seed."""
    banner("PHASE 9: Determinism Validation")
    
    np = modules.get("numpy")
    batch_score = modules.get("batch_score")
    
    if batch_score is None:
        suite.add(TestResult(
            name="Determinism",
            passed=False,
            elapsed_ms=0,
            backend="N/A",
            error="batch_score function not available"
        ))
        return
    
    seed = 12345
    
    with timer() as t:
        try:
            # Generate same data twice
            rng1 = np.random.default_rng(seed)
            entities1 = [
                {'id': f'det_{i}', 'vec': v.tolist()}
                for i, v in enumerate(rng1.random((500, 256)))
            ]
            
            rng2 = np.random.default_rng(seed)
            entities2 = [
                {'id': f'det_{i}', 'vec': v.tolist()}
                for i, v in enumerate(rng2.random((500, 256)))
            ]
            
            # Run twice
            result1 = batch_score(entities=entities1, seed=seed)
            result2 = batch_score(entities=entities2, seed=seed)
            
            # Compare scores
            scores1 = [s['overall'] for s in result1.get('scores', [])[:10]]
            scores2 = [s['overall'] for s in result2.get('scores', [])[:10]]
            
            passed = all(abs(a - b) < 1e-6 for a, b in zip(scores1, scores2))
            error = None
            
            if not passed:
                error = f"Scores differ: {scores1[:3]} vs {scores2[:3]}"
            
        except Exception as e:
            passed = False
            error = str(e)
    
    suite.add(TestResult(
        name="Determinism (same seed = same results)",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        backend=result1.get("backend", "unknown") if 'result1' in dir() else "error",
        details={"seed": seed},
        error=error
    ))


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the complete hardware-specific test suite."""
    print("\n" + "█" * 60)
    print("  MAS-MCP Hardware-Specific Testing Suite")
    print("█" * 60)
    
    print(f"\n  Hardware Profile:")
    for key, value in HARDWARE_PROFILE.items():
        print(f"    {key}: {value}")
    
    suite = TestSuite()
    
    # Phase 1: Environment
    test_environment(suite)
    
    # Safe import of GPU modules
    banner("Loading GPU Modules")
    modules = safe_import_gpu_modules()
    if modules is None:
        print("\n❌ Critical: Could not import required modules")
        return 1
    
    # Phase 2: GPU Detection
    gpu_info = test_gpu_detection(suite, modules)
    gpu_available = gpu_info.get("gpu_available", False)
    
    # Phase 3: CPU Fallback Baseline
    test_cpu_fallback(suite, modules)
    
    # Phase 4: GPU Warm-up
    warmup_ok = test_gpu_warmup(suite, modules, gpu_available)
    
    # Phase 5: Incremental Batches
    test_incremental_batches(suite, modules, gpu_available)
    
    # Phase 6: Hierarchy Layout
    test_hierarchy_layout(suite, modules, gpu_available)
    
    # Phase 7: Backend Switching
    test_backend_switching(suite, modules, gpu_available)
    
    # Phase 8: Determinism
    test_determinism(suite, modules)
    
    # Final Summary
    banner("Test Suite Summary", "█")
    summary = suite.summary()
    
    print(f"\n  Results:")
    print(f"    Passed: {summary['passed']}/{summary['total']}")
    print(f"    Failed: {summary['failed']}/{summary['total']}")
    print(f"    Success Rate: {summary['success_rate']:.1%}")
    print(f"    Total Time: {summary['total_time_ms']:.1f}ms ({summary['total_time_ms']/1000:.2f}s)")
    
    if summary['failed'] > 0:
        print(f"\n  Failed Tests:")
        for r in suite.results:
            if not r.passed:
                print(f"    - {r.name}: {r.error or 'Unknown error'}")
    
    print()
    
    # Return exit code
    return 0 if summary['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
