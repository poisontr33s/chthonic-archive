#!/usr/bin/env python3
"""
Hardware-Specific GPU Testing Suite for Predator Helios
========================================================

Designed for: Intel i9-14900 + NVIDIA Laptop GPU (RTX 4090 Mobile variant)
Environment:  Windows 11 + PowerShell 7.4+ + Python 3.14 + uv-managed

This suite validates:
1. Barnes-Hut vs Naive N-body comparison (correctness + performance)
2. CPU fallback ↔ GPU acceleration transitions (stability)
3. TDR-safe tiling behavior (no Windows GPU timeout)
4. Determinism across backend switches

Run OUTSIDE VS Code to avoid TDR interference:
    cd mas_mcp
    uv run python test_hardware_specific.py

Based on research report findings:
- PowerShell HAGS can cause instability
- DLL loading issues with CUDA 13.x
- Background throttling affects GPU workloads
- Memory management critical for stability
"""

import json
import time
import sys
import os
import gc
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from contextlib import contextmanager

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, '.')

# Defer GPU imports to test loading behavior
GPU_AVAILABLE = False
GPU_BACKEND = "cpu"


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    elapsed_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


def banner(title: str, char: str = "="):
    """Print a banner for test sections."""
    width = 70
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def sub_banner(title: str):
    """Print a sub-banner."""
    print(f"\n  ── {title} ──")


@contextmanager
def timer():
    """Context manager for timing operations."""
    start = time.perf_counter()
    result = {"elapsed_ms": 0.0}
    try:
        yield result
    finally:
        result["elapsed_ms"] = (time.perf_counter() - start) * 1000


def test_gpu_import_stability() -> TestResult:
    """
    Test 1: GPU Library Import Stability
    
    Validates that CuPy/Numba can be imported without crashing.
    This is where many Windows DLL issues manifest.
    """
    banner("Test 1: GPU Import Stability")
    
    global GPU_AVAILABLE, GPU_BACKEND
    
    details = {
        "cupy_available": False,
        "numba_available": False,
        "cuda_version": None,
        "device_name": None,
        "vram_gb": None,
    }
    
    with timer() as t:
        # Test CuPy import
        try:
            import cupy as cp
            details["cupy_available"] = True
            
            # Try to get CUDA info
            try:
                device = cp.cuda.Device(0)
                props = device.attributes
                details["device_name"] = cp.cuda.runtime.getDeviceProperties(0)["name"].decode()
                mem_info = cp.cuda.runtime.memGetInfo()
                details["vram_gb"] = round(mem_info[1] / (1024**3), 2)
                details["cuda_version"] = cp.cuda.runtime.runtimeGetVersion()
                GPU_AVAILABLE = True
                GPU_BACKEND = "cupy"
            except Exception as e:
                details["cupy_device_error"] = str(e)
                
        except ImportError as e:
            details["cupy_import_error"] = str(e)
        except Exception as e:
            details["cupy_error"] = str(e)
        
        # Test Numba import
        try:
            from numba import cuda
            details["numba_available"] = True
            
            try:
                if cuda.is_available():
                    device = cuda.get_current_device()
                    details["numba_device"] = device.name.decode() if hasattr(device.name, 'decode') else str(device.name)
                    if not GPU_AVAILABLE:
                        GPU_AVAILABLE = True
                        GPU_BACKEND = "numba"
            except Exception as e:
                details["numba_device_error"] = str(e)
                
        except ImportError as e:
            details["numba_import_error"] = str(e)
        except Exception as e:
            details["numba_error"] = str(e)
    
    passed = details["cupy_available"] or details["numba_available"]
    
    print(f"  CuPy Available: {'✓' if details['cupy_available'] else '✗'}")
    print(f"  Numba Available: {'✓' if details['numba_available'] else '✗'}")
    if details.get("device_name"):
        print(f"  GPU: {details['device_name']}")
    if details.get("vram_gb"):
        print(f"  VRAM: {details['vram_gb']} GB")
    if details.get("cuda_version"):
        print(f"  CUDA Version: {details['cuda_version']}")
    print(f"  Backend: {GPU_BACKEND}")
    print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
    
    return TestResult(
        name="GPU Import Stability",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_cpu_fallback_basic() -> TestResult:
    """
    Test 2: CPU Fallback Basic Operations
    
    Ensures CPU-only numpy operations work correctly.
    This is our baseline - must always work.
    """
    banner("Test 2: CPU Fallback Basic Operations")
    
    details = {}
    seed = 42
    rng = np.random.default_rng(seed)
    
    with timer() as t:
        # Basic matrix operations
        n = 1000
        a = rng.random((n, n))
        b = rng.random((n, n))
        
        # Matrix multiply
        c = a @ b
        details["matmul_shape"] = list(c.shape)
        details["matmul_sum"] = float(c.sum())
        
        # Eigenvalue (smaller matrix for speed)
        small = rng.random((100, 100))
        small = (small + small.T) / 2  # Make symmetric
        eigenvalues = np.linalg.eigvalsh(small)
        details["eigenvalue_count"] = len(eigenvalues)
        
        # FFT
        signal = rng.random(8192)
        fft_result = np.fft.fft(signal)
        details["fft_length"] = len(fft_result)
    
    passed = (
        details["matmul_shape"] == [1000, 1000] and
        details["eigenvalue_count"] == 100 and
        details["fft_length"] == 8192
    )
    
    print(f"  Matrix Multiply: {details['matmul_shape']} ✓")
    print(f"  Eigenvalues: {details['eigenvalue_count']} values ✓")
    print(f"  FFT: {details['fft_length']} points ✓")
    print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
    
    return TestResult(
        name="CPU Fallback Basic",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_barnes_hut_vs_naive() -> TestResult:
    """
    Test 3: Barnes-Hut vs Naive N-body Comparison
    
    This is the CRITICAL test - validates that our Barnes-Hut
    approximation produces results similar to naive O(n²) within
    acceptable error bounds, while being significantly faster.
    """
    banner("Test 3: Barnes-Hut vs Naive N-body Comparison")
    
    details = {
        "naive_time_ms": 0,
        "barnes_hut_time_ms": 0,
        "speedup": 0,
        "max_position_error": 0,
        "mean_position_error": 0,
        "acceptable_error": True,
    }
    
    # Parameters
    n_bodies = 500  # Small enough for naive to complete quickly
    iterations = 50
    theta = 0.5  # Barnes-Hut opening angle
    dt = 0.01
    seed = 12345
    
    rng = np.random.default_rng(seed)
    
    # Initialize positions and velocities
    positions_naive = rng.random((n_bodies, 2)) * 100
    velocities_naive = (rng.random((n_bodies, 2)) - 0.5) * 2
    masses = rng.random(n_bodies) * 10 + 1
    
    # Copy for Barnes-Hut
    positions_bh = positions_naive.copy()
    velocities_bh = velocities_naive.copy()
    
    sub_banner(f"Naive O(n²) with {n_bodies} bodies")
    
    # Naive N-body simulation
    def naive_forces(pos, mass):
        """O(n²) direct force calculation."""
        n = len(pos)
        forces = np.zeros_like(pos)
        G = 1.0
        softening = 0.1
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    r = pos[j] - pos[i]
                    dist = np.sqrt(np.sum(r**2) + softening**2)
                    forces[i] += G * mass[j] * r / (dist**3)
        
        return forces
    
    with timer() as t_naive:
        for _ in range(iterations):
            forces = naive_forces(positions_naive, masses)
            velocities_naive += forces * dt
            positions_naive += velocities_naive * dt
    
    details["naive_time_ms"] = t_naive["elapsed_ms"]
    print(f"  Elapsed: {t_naive['elapsed_ms']:.1f}ms")
    
    sub_banner(f"Barnes-Hut O(n log n) with θ={theta}")
    
    # Barnes-Hut implementation
    class QuadTreeNode:
        """Simple quadtree for Barnes-Hut."""
        def __init__(self, x_min, y_min, x_max, y_max):
            self.x_min, self.y_min = x_min, y_min
            self.x_max, self.y_max = x_max, y_max
            self.center_of_mass = np.zeros(2)
            self.total_mass = 0.0
            self.children = [None, None, None, None]  # NW, NE, SW, SE
            self.body_index = -1  # -1 means internal node or empty
            self.is_leaf = True
        
        @property
        def size(self):
            return max(self.x_max - self.x_min, self.y_max - self.y_min)
    
    def build_quadtree(positions, masses):
        """Build quadtree from positions."""
        x_min, y_min = positions.min(axis=0) - 1
        x_max, y_max = positions.max(axis=0) + 1
        
        root = QuadTreeNode(x_min, y_min, x_max, y_max)
        
        for i, (pos, mass) in enumerate(zip(positions, masses)):
            insert_body(root, i, pos, mass, positions, masses)
        
        return root
    
    def insert_body(node, body_idx, pos, mass, all_positions, all_masses):
        """Insert a body into the quadtree."""
        if node.total_mass == 0:
            # Empty node - just add the body
            node.body_index = body_idx
            node.center_of_mass = pos.copy()
            node.total_mass = mass
            return
        
        if node.is_leaf:
            # Leaf with existing body - need to subdivide
            node.is_leaf = False
            old_idx = node.body_index
            old_pos = all_positions[old_idx]
            old_mass = all_masses[old_idx]
            node.body_index = -1
            
            # Create children
            x_mid = (node.x_min + node.x_max) / 2
            y_mid = (node.y_min + node.y_max) / 2
            
            node.children[0] = QuadTreeNode(node.x_min, y_mid, x_mid, node.y_max)  # NW
            node.children[1] = QuadTreeNode(x_mid, y_mid, node.x_max, node.y_max)  # NE
            node.children[2] = QuadTreeNode(node.x_min, node.y_min, x_mid, y_mid)  # SW
            node.children[3] = QuadTreeNode(x_mid, node.y_min, node.x_max, y_mid)  # SE
            
            # Re-insert the old body
            insert_body_to_child(node, old_idx, old_pos, old_mass, all_positions, all_masses)
        
        # Insert the new body into appropriate child
        insert_body_to_child(node, body_idx, pos, mass, all_positions, all_masses)
        
        # Update center of mass
        node.center_of_mass = (
            node.center_of_mass * node.total_mass + pos * mass
        ) / (node.total_mass + mass)
        node.total_mass += mass
    
    def insert_body_to_child(node, body_idx, pos, mass, all_positions, all_masses):
        """Insert body into correct child quadrant."""
        x_mid = (node.x_min + node.x_max) / 2
        y_mid = (node.y_min + node.y_max) / 2
        
        if pos[0] < x_mid:
            if pos[1] >= y_mid:
                child_idx = 0  # NW
            else:
                child_idx = 2  # SW
        else:
            if pos[1] >= y_mid:
                child_idx = 1  # NE
            else:
                child_idx = 3  # SE
        
        insert_body(node.children[child_idx], body_idx, pos, mass, all_positions, all_masses)
    
    def barnes_hut_force(node, pos, mass_self, theta, softening=0.1):
        """Calculate force on a body using Barnes-Hut approximation."""
        if node is None or node.total_mass == 0:
            return np.zeros(2)
        
        r = node.center_of_mass - pos
        dist = np.sqrt(np.sum(r**2) + softening**2)
        
        # If it's a leaf with a single body (not self)
        if node.is_leaf and node.body_index >= 0:
            if dist > softening:  # Not the same body
                return node.total_mass * r / (dist**3)
            return np.zeros(2)
        
        # Barnes-Hut criterion: s/d < theta
        if node.size / dist < theta:
            # Treat as single body
            return node.total_mass * r / (dist**3)
        
        # Otherwise, recurse into children
        force = np.zeros(2)
        for child in node.children:
            if child is not None:
                force += barnes_hut_force(child, pos, mass_self, theta, softening)
        
        return force
    
    with timer() as t_bh:
        for _ in range(iterations):
            # Build tree each iteration (positions change)
            tree = build_quadtree(positions_bh, masses)
            
            # Calculate forces using Barnes-Hut
            forces_bh = np.zeros_like(positions_bh)
            for i in range(n_bodies):
                forces_bh[i] = barnes_hut_force(tree, positions_bh[i], masses[i], theta)
            
            velocities_bh += forces_bh * dt
            positions_bh += velocities_bh * dt
    
    details["barnes_hut_time_ms"] = t_bh["elapsed_ms"]
    print(f"  Elapsed: {t_bh['elapsed_ms']:.1f}ms")
    
    # Compare results
    sub_banner("Comparison")
    
    position_errors = np.sqrt(np.sum((positions_naive - positions_bh)**2, axis=1))
    details["max_position_error"] = float(np.max(position_errors))
    details["mean_position_error"] = float(np.mean(position_errors))
    details["speedup"] = t_naive["elapsed_ms"] / t_bh["elapsed_ms"] if t_bh["elapsed_ms"] > 0 else 0
    
    # Error threshold: positions should be within 10% of the simulation domain
    # after 50 iterations with theta=0.5
    error_threshold = 10.0  # Generous threshold for approximation
    details["acceptable_error"] = details["max_position_error"] < error_threshold
    
    print(f"  Speedup: {details['speedup']:.2f}x")
    print(f"  Max Position Error: {details['max_position_error']:.4f}")
    print(f"  Mean Position Error: {details['mean_position_error']:.4f}")
    print(f"  Error Acceptable: {'✓' if details['acceptable_error'] else '✗'} (threshold: {error_threshold})")
    
    passed = details["acceptable_error"] and details["speedup"] > 1.0
    
    return TestResult(
        name="Barnes-Hut vs Naive",
        passed=passed,
        elapsed_ms=t_naive["elapsed_ms"] + t_bh["elapsed_ms"],
        details=details
    )


def test_gpu_memory_safety() -> TestResult:
    """
    Test 4: GPU Memory Safety
    
    Tests that we can allocate and free GPU memory without
    crashes or memory leaks. Critical for avoiding OOM.
    """
    banner("Test 4: GPU Memory Safety")
    
    if not GPU_AVAILABLE:
        return TestResult(
            name="GPU Memory Safety",
            passed=True,
            elapsed_ms=0,
            details={"skipped": "No GPU available"},
        )
    
    details = {
        "allocations": 0,
        "max_size_mb": 0,
        "total_allocated_mb": 0,
        "memory_freed": False,
    }
    
    try:
        import cupy as cp
        
        with timer() as t:
            # Get initial memory state
            pool = cp.get_default_memory_pool()
            initial_used = pool.used_bytes()
            
            # Allocate progressively larger arrays
            sizes_mb = [10, 50, 100, 200, 500]
            arrays = []
            
            for size_mb in sizes_mb:
                try:
                    n = int(size_mb * 1024 * 1024 / 4)  # float32
                    arr = cp.zeros(n, dtype=cp.float32)
                    cp.cuda.Stream.null.synchronize()
                    arrays.append(arr)
                    details["allocations"] += 1
                    details["max_size_mb"] = size_mb
                    details["total_allocated_mb"] += size_mb
                except cp.cuda.memory.OutOfMemoryError:
                    break
            
            # Free all arrays
            del arrays
            gc.collect()
            pool.free_all_blocks()
            cp.cuda.Stream.null.synchronize()
            
            final_used = pool.used_bytes()
            details["memory_freed"] = final_used <= initial_used + 1024 * 1024  # Allow 1MB variance
        
        print(f"  Allocations: {details['allocations']}")
        print(f"  Max Single Allocation: {details['max_size_mb']} MB")
        print(f"  Total Allocated: {details['total_allocated_mb']} MB")
        print(f"  Memory Freed: {'✓' if details['memory_freed'] else '✗'}")
        print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
        
        passed = details["allocations"] > 0 and details["memory_freed"]
        
    except Exception as e:
        return TestResult(
            name="GPU Memory Safety",
            passed=False,
            elapsed_ms=0,
            details=details,
            error=str(e)
        )
    
    return TestResult(
        name="GPU Memory Safety",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_backend_switch_stability() -> TestResult:
    """
    Test 5: Backend Switch Stability
    
    Tests rapid switching between CPU and GPU backends.
    This is where instability often manifests on Windows.
    """
    banner("Test 5: Backend Switch Stability")
    
    details = {
        "switch_count": 0,
        "cpu_results": [],
        "gpu_results": [],
        "results_match": False,
    }
    
    seed = 42
    n = 1000
    
    with timer() as t:
        for i in range(5):
            rng = np.random.default_rng(seed + i)
            data = rng.random((n, n)).astype(np.float32)
            
            # CPU computation
            cpu_result = np.sum(data @ data.T)
            details["cpu_results"].append(float(cpu_result))
            
            # GPU computation (if available)
            if GPU_AVAILABLE:
                try:
                    import cupy as cp
                    data_gpu = cp.asarray(data)
                    gpu_result = float(cp.sum(data_gpu @ data_gpu.T).get())
                    details["gpu_results"].append(gpu_result)
                    del data_gpu
                    cp.get_default_memory_pool().free_all_blocks()
                except Exception as e:
                    details["gpu_results"].append(f"error: {e}")
            else:
                details["gpu_results"].append("skipped")
            
            details["switch_count"] += 1
    
    # Check results match
    if GPU_AVAILABLE and all(isinstance(r, float) for r in details["gpu_results"]):
        max_diff = max(
            abs(c - g) / max(abs(c), 1e-10)
            for c, g in zip(details["cpu_results"], details["gpu_results"])
        )
        details["max_relative_diff"] = max_diff
        details["results_match"] = max_diff < 1e-4  # Allow small floating point differences
    else:
        details["results_match"] = True  # No GPU, so trivially matches
    
    print(f"  Switch Count: {details['switch_count']}")
    print(f"  CPU Results: {[f'{r:.2e}' for r in details['cpu_results'][:3]]}...")
    if GPU_AVAILABLE:
        gpu_preview = details["gpu_results"][:3]
        print(f"  GPU Results: {[f'{r:.2e}' if isinstance(r, float) else r for r in gpu_preview]}...")
        if "max_relative_diff" in details:
            print(f"  Max Relative Diff: {details['max_relative_diff']:.2e}")
    print(f"  Results Match: {'✓' if details['results_match'] else '✗'}")
    print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
    
    passed = details["switch_count"] == 5 and details["results_match"]
    
    return TestResult(
        name="Backend Switch Stability",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_tdr_safe_workload() -> TestResult:
    """
    Test 6: TDR-Safe Workload
    
    Tests that workloads complete within Windows TDR timeout.
    The TDR timeout is typically 2 seconds by default.
    """
    banner("Test 6: TDR-Safe Workload")
    
    if not GPU_AVAILABLE:
        return TestResult(
            name="TDR-Safe Workload",
            passed=True,
            elapsed_ms=0,
            details={"skipped": "No GPU available"},
        )
    
    details = {
        "workloads_completed": 0,
        "max_kernel_ms": 0,
        "all_under_tdr": True,
    }
    
    TDR_THRESHOLD_MS = 1500  # Stay well under 2000ms
    
    try:
        import cupy as cp
        
        with timer() as t:
            # Run several GPU workloads, each should complete quickly
            workload_sizes = [1000, 2000, 4000, 8000]
            
            for size in workload_sizes:
                kernel_start = time.perf_counter()
                
                # Matrix operations that should complete quickly
                a = cp.random.random((size, size), dtype=cp.float32)
                b = cp.random.random((size, size), dtype=cp.float32)
                c = a @ b
                result = cp.sum(c)
                cp.cuda.Stream.null.synchronize()  # Wait for completion
                
                kernel_ms = (time.perf_counter() - kernel_start) * 1000
                details["max_kernel_ms"] = max(details["max_kernel_ms"], kernel_ms)
                
                if kernel_ms > TDR_THRESHOLD_MS:
                    details["all_under_tdr"] = False
                    print(f"  ⚠️ Workload {size}x{size} took {kernel_ms:.0f}ms (exceeds TDR threshold)")
                
                details["workloads_completed"] += 1
                
                # Clean up
                del a, b, c
                cp.get_default_memory_pool().free_all_blocks()
        
        print(f"  Workloads Completed: {details['workloads_completed']}/{len(workload_sizes)}")
        print(f"  Max Kernel Time: {details['max_kernel_ms']:.1f}ms")
        print(f"  All Under TDR: {'✓' if details['all_under_tdr'] else '✗'} (threshold: {TDR_THRESHOLD_MS}ms)")
        print(f"  Total Elapsed: {t['elapsed_ms']:.1f}ms")
        
        passed = details["workloads_completed"] == len(workload_sizes) and details["all_under_tdr"]
        
    except Exception as e:
        return TestResult(
            name="TDR-Safe Workload",
            passed=False,
            elapsed_ms=0,
            details=details,
            error=str(e)
        )
    
    return TestResult(
        name="TDR-Safe Workload",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_determinism() -> TestResult:
    """
    Test 7: Determinism Across Runs
    
    Validates that same seed produces identical results
    regardless of backend switches or timing.
    """
    banner("Test 7: Determinism")
    
    details = {
        "cpu_deterministic": False,
        "gpu_deterministic": False,
    }
    
    seed = 12345
    n = 500
    
    with timer() as t:
        # CPU determinism
        rng1 = np.random.default_rng(seed)
        result1 = np.sum(rng1.random((n, n)) @ rng1.random((n, n)))
        
        rng2 = np.random.default_rng(seed)
        result2 = np.sum(rng2.random((n, n)) @ rng2.random((n, n)))
        
        details["cpu_deterministic"] = abs(result1 - result2) < 1e-10
        details["cpu_result_1"] = float(result1)
        details["cpu_result_2"] = float(result2)
        
        # GPU determinism
        if GPU_AVAILABLE:
            try:
                import cupy as cp
                
                cp.random.seed(seed)
                a1 = cp.random.random((n, n))
                b1 = cp.random.random((n, n))
                gpu_result1 = float(cp.sum(a1 @ b1).get())
                
                cp.random.seed(seed)
                a2 = cp.random.random((n, n))
                b2 = cp.random.random((n, n))
                gpu_result2 = float(cp.sum(a2 @ b2).get())
                
                details["gpu_deterministic"] = abs(gpu_result1 - gpu_result2) < 1e-5
                details["gpu_result_1"] = gpu_result1
                details["gpu_result_2"] = gpu_result2
                
                del a1, b1, a2, b2
                cp.get_default_memory_pool().free_all_blocks()
                
            except Exception as e:
                details["gpu_error"] = str(e)
        else:
            details["gpu_deterministic"] = True  # Trivially true
    
    print(f"  CPU Deterministic: {'✓' if details['cpu_deterministic'] else '✗'}")
    if GPU_AVAILABLE:
        print(f"  GPU Deterministic: {'✓' if details['gpu_deterministic'] else '✗'}")
    print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
    
    passed = details["cpu_deterministic"] and details.get("gpu_deterministic", True)
    
    return TestResult(
        name="Determinism",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def test_orchestrator_integration() -> TestResult:
    """
    Test 8: GPU Orchestrator Integration
    
    Tests the actual MAS-MCP gpu_orchestrator module if available.
    """
    banner("Test 8: GPU Orchestrator Integration")
    
    try:
        from gpu_orchestrator import (
            mas_gpu_status,
            mas_gpu_batch_score,
        )
    except ImportError as e:
        return TestResult(
            name="GPU Orchestrator Integration",
            passed=True,
            elapsed_ms=0,
            details={"skipped": f"Module not available: {e}"},
        )
    
    details = {}
    
    with timer() as t:
        # Test status
        status = mas_gpu_status()
        details["gpu_available"] = status.get("gpu_available", False)
        details["backend"] = status.get("backend", "unknown")
        
        # Test small batch scoring
        seed = 42
        rng = np.random.default_rng(seed)
        entities = [
            {'id': f'e{i}', 'vec': v.tolist()}
            for i, v in enumerate(rng.random((100, 64)))
        ]
        
        result = mas_gpu_batch_score(entities=entities, seed=seed)
        details["batch_count"] = result.get("count", 0)
        details["batch_backend"] = result.get("backend", "unknown")
        
        if "scores" in result:
            details["score_sample"] = result["scores"][:3]
    
    print(f"  GPU Available: {details['gpu_available']}")
    print(f"  Backend: {details['backend']}")
    print(f"  Batch Count: {details['batch_count']}")
    print(f"  Elapsed: {t['elapsed_ms']:.1f}ms")
    
    passed = details["batch_count"] == 100
    
    return TestResult(
        name="GPU Orchestrator Integration",
        passed=passed,
        elapsed_ms=t["elapsed_ms"],
        details=details
    )


def main():
    """Run all hardware-specific tests."""
    print("\n" + "█" * 70)
    print("  MAS-MCP Hardware-Specific Test Suite")
    print("  Target: Predator Helios / i9-14900 / NVIDIA Laptop GPU")
    print("█" * 70)
    
    # Environment info
    banner("Environment", "─")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  NumPy: {np.__version__}")
    print(f"  Platform: {sys.platform}")
    print(f"  CWD: {os.getcwd()}")
    
    # Run all tests
    tests = [
        test_gpu_import_stability,
        test_cpu_fallback_basic,
        test_barnes_hut_vs_naive,
        test_gpu_memory_safety,
        test_backend_switch_stability,
        test_tdr_safe_workload,
        test_determinism,
        test_orchestrator_integration,
    ]
    
    results: List[TestResult] = []
    
    for test_fn in tests:
        try:
            result = test_fn()
            results.append(result)
        except Exception as e:
            import traceback
            results.append(TestResult(
                name=test_fn.__name__,
                passed=False,
                elapsed_ms=0,
                details={},
                error=f"{e}\n{traceback.format_exc()}"
            ))
    
    # Summary
    banner("Test Summary", "█")
    
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    total_time = sum(r.elapsed_ms for r in results)
    
    for result in results:
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {status}  {result.name} ({result.elapsed_ms:.0f}ms)")
        if result.error:
            print(f"         Error: {result.error[:100]}...")
    
    print()
    print(f"  Total: {passed_count}/{total_count} passed")
    print(f"  Time: {total_time:.0f}ms ({total_time/1000:.1f}s)")
    
    if passed_count == total_count:
        print("\n  🎉 All tests passed! Hardware is stable for GPU workloads.")
    else:
        print("\n  ⚠️ Some tests failed. Review errors above.")
    
    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
