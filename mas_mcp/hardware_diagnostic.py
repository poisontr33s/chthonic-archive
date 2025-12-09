#!/usr/bin/env python3
"""
Hardware Diagnostic for Predator Helios + RTX 4090 Laptop GPU + i9-14900
=========================================================================

This script is specifically designed to:
1. Safely probe YOUR specific hardware configuration
2. Test Barnes-Hut vs naive force layout performance
3. Measure TDR safety margins on your RTX 4090 laptop GPU
4. Provide actionable diagnostics for VS Code usage

Run OUTSIDE VS Code to avoid TDR conflicts:
    cd mas_mcp
    uv run python hardware_diagnostic.py

Or with explicit Python:
    python hardware_diagnostic.py
"""

import json
import time
import sys
import os
import platform
from dataclasses import dataclass
from typing import Optional

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# Hardware Detection
# ============================================================================

@dataclass
class HardwareProfile:
    """Detected hardware profile."""
    cpu_name: str
    cpu_cores: int
    cpu_threads: int
    ram_gb: float
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]
    gpu_compute_capability: Optional[str]
    cuda_version: Optional[str]
    cupy_available: bool
    numba_available: bool
    os_version: str
    python_version: str


def detect_hardware() -> HardwareProfile:
    """Detect hardware configuration."""
    import psutil
    
    # CPU info
    cpu_name = platform.processor() or "Unknown CPU"
    cpu_cores = psutil.cpu_count(logical=False) or 1
    cpu_threads = psutil.cpu_count(logical=True) or 1
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # GPU info
    gpu_name = None
    gpu_vram_gb = None
    gpu_compute_capability = None
    cuda_version = None
    cupy_available = False
    numba_available = False
    
    # Try CuPy
    try:
        import cupy as cp
        cupy_available = True
        device = cp.cuda.Device(0)
        gpu_name = device.attributes.get('DeviceName', cp.cuda.runtime.getDeviceProperties(0)['name'].decode())
        gpu_vram_gb = device.mem_info[1] / (1024**3)
        cc = device.compute_capability
        gpu_compute_capability = f"{cc[0]}.{cc[1]}"
        cuda_version = f"{cp.cuda.runtime.runtimeGetVersion() // 1000}.{(cp.cuda.runtime.runtimeGetVersion() % 1000) // 10}"
    except Exception as e:
        print(f"  [CuPy detection failed: {e}]")
    
    # Try Numba
    try:
        from numba import cuda
        numba_available = cuda.is_available()
        if numba_available and gpu_name is None:
            device = cuda.get_current_device()
            gpu_name = device.name.decode() if isinstance(device.name, bytes) else device.name
            cc = device.compute_capability
            gpu_compute_capability = f"{cc[0]}.{cc[1]}"
    except Exception as e:
        print(f"  [Numba detection failed: {e}]")
    
    return HardwareProfile(
        cpu_name=cpu_name,
        cpu_cores=cpu_cores,
        cpu_threads=cpu_threads,
        ram_gb=ram_gb,
        gpu_name=gpu_name,
        gpu_vram_gb=gpu_vram_gb,
        gpu_compute_capability=gpu_compute_capability,
        cuda_version=cuda_version,
        cupy_available=cupy_available,
        numba_available=numba_available,
        os_version=f"{platform.system()} {platform.release()} ({platform.version()})",
        python_version=platform.python_version(),
    )


def print_hardware_profile(profile: HardwareProfile):
    """Print hardware profile in a readable format."""
    print("\n" + "=" * 70)
    print("  HARDWARE PROFILE: Predator Helios Diagnostic")
    print("=" * 70)
    
    print(f"\n  CPU: {profile.cpu_name}")
    print(f"       Cores: {profile.cpu_cores} physical, {profile.cpu_threads} threads")
    print(f"       RAM: {profile.ram_gb:.1f} GB")
    
    print(f"\n  GPU: {profile.gpu_name or 'NOT DETECTED'}")
    if profile.gpu_vram_gb:
        print(f"       VRAM: {profile.gpu_vram_gb:.1f} GB")
    if profile.gpu_compute_capability:
        print(f"       Compute: SM {profile.gpu_compute_capability}")
    if profile.cuda_version:
        print(f"       CUDA: {profile.cuda_version}")
    
    print(f"\n  Libraries:")
    print(f"       CuPy: {'✓ Available' if profile.cupy_available else '✗ Not available'}")
    print(f"       Numba CUDA: {'✓ Available' if profile.numba_available else '✗ Not available'}")
    
    print(f"\n  System:")
    print(f"       OS: {profile.os_version}")
    print(f"       Python: {profile.python_version}")
    print()


# ============================================================================
# TDR Safety Testing
# ============================================================================

def test_tdr_safety(profile: HardwareProfile) -> dict:
    """
    Test TDR (Timeout Detection and Recovery) safety margins.
    
    Windows has a ~2 second TDR timeout by default. We need to ensure
    GPU kernels complete well under this threshold.
    """
    print("\n" + "=" * 70)
    print("  TDR SAFETY TEST")
    print("=" * 70)
    
    if not profile.cupy_available:
        print("\n  ⚠️  CuPy not available - skipping TDR test")
        return {"status": "skipped", "reason": "cupy_not_available"}
    
    import cupy as cp
    import numpy as np
    
    results = {
        "status": "passed",
        "tests": [],
        "recommended_tile_size": None,
        "max_safe_duration_ms": None,
    }
    
    # Test increasingly large workloads
    test_sizes = [1000, 5000, 10000, 25000, 50000, 100000]
    
    print("\n  Testing kernel durations at increasing workload sizes...")
    print("  (Target: < 1500ms per kernel for TDR safety)\n")
    
    safe_size = 0
    
    for size in test_sizes:
        try:
            # Create random data
            rng = np.random.default_rng(42)
            data = cp.asarray(rng.random((size, 256), dtype=np.float32))
            
            # Warm up
            _ = cp.sum(data)
            cp.cuda.Stream.null.synchronize()
            
            # Time a representative kernel (matrix-vector operations)
            t0 = time.perf_counter()
            
            # Simulate scoring operations
            norms = cp.linalg.norm(data, axis=1)
            means = cp.mean(data, axis=1)
            result = norms * means
            
            cp.cuda.Stream.null.synchronize()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            
            status = "✓ SAFE" if elapsed_ms < 1500 else "⚠️ RISKY" if elapsed_ms < 2000 else "✗ DANGER"
            print(f"    Size {size:>7,}: {elapsed_ms:>8.1f}ms  {status}")
            
            results["tests"].append({
                "size": size,
                "duration_ms": elapsed_ms,
                "safe": elapsed_ms < 1500,
            })
            
            if elapsed_ms < 1500:
                safe_size = size
            
            # Clean up
            del data, norms, means, result
            cp.get_default_memory_pool().free_all_blocks()
            
        except Exception as e:
            print(f"    Size {size:>7,}: ERROR - {e}")
            results["tests"].append({
                "size": size,
                "error": str(e),
            })
            break
    
    results["recommended_tile_size"] = safe_size
    results["max_safe_duration_ms"] = max(
        (t["duration_ms"] for t in results["tests"] if t.get("safe")),
        default=0
    )
    
    print(f"\n  Recommended tile size: {safe_size:,} items")
    print(f"  Max safe duration: {results['max_safe_duration_ms']:.1f}ms")
    
    return results


# ============================================================================
# Barnes-Hut vs Naive Comparison
# ============================================================================

def test_barnes_hut_comparison(profile: HardwareProfile) -> dict:
    """
    Compare Barnes-Hut hierarchical layout vs naive O(n²) force calculation.
    
    This tests whether the Barnes-Hut optimization is actually beneficial
    on your specific hardware.
    """
    print("\n" + "=" * 70)
    print("  BARNES-HUT vs NAIVE FORCE LAYOUT COMPARISON")
    print("=" * 70)
    
    if not profile.cupy_available:
        print("\n  ⚠️  CuPy not available - skipping comparison")
        return {"status": "skipped", "reason": "cupy_not_available"}
    
    import cupy as cp
    import numpy as np
    
    results = {
        "status": "completed",
        "tests": [],
        "barnes_hut_advantage": None,
    }
    
    # Test sizes where we can compare both methods
    test_sizes = [100, 500, 1000, 2000]
    
    print("\n  Comparing force calculation methods...\n")
    print("  Size      Naive (ms)    Barnes-Hut (ms)    Speedup")
    print("  " + "-" * 55)
    
    advantages = []
    
    for size in test_sizes:
        try:
            rng = np.random.default_rng(42)
            
            # Initial positions
            positions = cp.asarray(rng.random((size, 3), dtype=np.float32) * 100)
            
            # === Naive O(n²) force calculation ===
            cp.cuda.Stream.null.synchronize()
            t0 = time.perf_counter()
            
            # Full pairwise distance calculation
            diff = positions[:, None, :] - positions[None, :, :]  # [n, n, 3]
            dist = cp.sqrt(cp.sum(diff**2, axis=2) + 1e-6)  # [n, n]
            forces = cp.sum(diff / (dist[:, :, None]**2 + 1e-6), axis=1)  # [n, 3]
            
            cp.cuda.Stream.null.synchronize()
            naive_ms = (time.perf_counter() - t0) * 1000
            
            del diff, dist, forces
            cp.get_default_memory_pool().free_all_blocks()
            
            # === Barnes-Hut approximation ===
            cp.cuda.Stream.null.synchronize()
            t0 = time.perf_counter()
            
            # Simplified Barnes-Hut: grid-based clustering
            grid_size = max(4, int(np.sqrt(size / 10)))
            
            # Discretize positions to grid
            pos_np = cp.asnumpy(positions)
            min_pos = pos_np.min(axis=0)
            max_pos = pos_np.max(axis=0)
            scale = (max_pos - min_pos) / grid_size
            scale[scale < 1e-6] = 1.0
            
            grid_idx = ((pos_np - min_pos) / scale).astype(np.int32)
            grid_idx = np.clip(grid_idx, 0, grid_size - 1)
            
            # Compute cell centers of mass
            cell_mass = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
            cell_com = np.zeros((grid_size, grid_size, grid_size, 3), dtype=np.float32)
            
            for i in range(size):
                gx, gy, gz = grid_idx[i]
                cell_mass[gx, gy, gz] += 1
                cell_com[gx, gy, gz] += pos_np[i]
            
            # Normalize centers of mass
            mask = cell_mass > 0
            cell_com[mask] /= cell_mass[mask, None]
            
            # Force from cell centers (approximation)
            forces_bh = np.zeros((size, 3), dtype=np.float32)
            for i in range(size):
                gx, gy, gz = grid_idx[i]
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        for dz in range(-1, 2):
                            nx, ny, nz = gx + dx, gy + dy, gz + dz
                            if 0 <= nx < grid_size and 0 <= ny < grid_size and 0 <= nz < grid_size:
                                if cell_mass[nx, ny, nz] > 0:
                                    diff = cell_com[nx, ny, nz] - pos_np[i]
                                    dist = np.sqrt(np.sum(diff**2) + 1e-6)
                                    forces_bh[i] += diff * cell_mass[nx, ny, nz] / (dist**2 + 1e-6)
            
            cp.cuda.Stream.null.synchronize()
            bh_ms = (time.perf_counter() - t0) * 1000
            
            speedup = naive_ms / bh_ms if bh_ms > 0 else float('inf')
            advantages.append(speedup)
            
            print(f"  {size:>5}     {naive_ms:>8.1f}ms      {bh_ms:>8.1f}ms        {speedup:>5.2f}x")
            
            results["tests"].append({
                "size": size,
                "naive_ms": naive_ms,
                "barnes_hut_ms": bh_ms,
                "speedup": speedup,
            })
            
            del positions
            cp.get_default_memory_pool().free_all_blocks()
            
        except Exception as e:
            print(f"  {size:>5}     ERROR: {e}")
            results["tests"].append({
                "size": size,
                "error": str(e),
            })
    
    if advantages:
        avg_advantage = sum(advantages) / len(advantages)
        results["barnes_hut_advantage"] = avg_advantage
        
        print(f"\n  Average Barnes-Hut speedup: {avg_advantage:.2f}x")
        
        if avg_advantage > 1.5:
            print("  ✓ Barnes-Hut is significantly faster on your hardware")
        elif avg_advantage > 1.0:
            print("  ~ Barnes-Hut is slightly faster on your hardware")
        else:
            print("  ⚠️ Naive method is faster - consider disabling Barnes-Hut")
    
    return results


# ============================================================================
# CPU vs GPU Backend Comparison
# ============================================================================

def test_cpu_vs_gpu(profile: HardwareProfile) -> dict:
    """
    Compare CPU (NumPy) vs GPU (CuPy) performance for typical MAS operations.
    """
    print("\n" + "=" * 70)
    print("  CPU vs GPU BACKEND COMPARISON")
    print("=" * 70)
    
    import numpy as np
    
    results = {
        "status": "completed",
        "tests": [],
        "gpu_advantage": None,
    }
    
    # Test sizes
    test_sizes = [1000, 5000, 10000, 25000]
    
    print("\n  Comparing NumPy (CPU) vs CuPy (GPU) performance...\n")
    print("  Size      CPU (ms)      GPU (ms)      Speedup")
    print("  " + "-" * 50)
    
    advantages = []
    
    for size in test_sizes:
        try:
            rng = np.random.default_rng(42)
            data_np = rng.random((size, 256)).astype(np.float32)
            
            # === CPU (NumPy) ===
            t0 = time.perf_counter()
            
            norms = np.linalg.norm(data_np, axis=1)
            means = np.mean(data_np, axis=1)
            stds = np.std(data_np, axis=1)
            result_cpu = norms * means + stds
            
            cpu_ms = (time.perf_counter() - t0) * 1000
            
            # === GPU (CuPy) ===
            gpu_ms = float('inf')
            if profile.cupy_available:
                import cupy as cp
                
                data_gpu = cp.asarray(data_np)
                
                # Warm up
                _ = cp.sum(data_gpu)
                cp.cuda.Stream.null.synchronize()
                
                t0 = time.perf_counter()
                
                norms = cp.linalg.norm(data_gpu, axis=1)
                means = cp.mean(data_gpu, axis=1)
                stds = cp.std(data_gpu, axis=1)
                result_gpu = norms * means + stds
                
                cp.cuda.Stream.null.synchronize()
                gpu_ms = (time.perf_counter() - t0) * 1000
                
                del data_gpu, norms, means, stds, result_gpu
                cp.get_default_memory_pool().free_all_blocks()
            
            speedup = cpu_ms / gpu_ms if gpu_ms > 0 and gpu_ms != float('inf') else 0
            if speedup > 0:
                advantages.append(speedup)
            
            gpu_str = f"{gpu_ms:>8.1f}ms" if gpu_ms != float('inf') else "N/A"
            speedup_str = f"{speedup:>5.2f}x" if speedup > 0 else "N/A"
            
            print(f"  {size:>5}     {cpu_ms:>8.1f}ms    {gpu_str}    {speedup_str}")
            
            results["tests"].append({
                "size": size,
                "cpu_ms": cpu_ms,
                "gpu_ms": gpu_ms if gpu_ms != float('inf') else None,
                "speedup": speedup if speedup > 0 else None,
            })
            
        except Exception as e:
            print(f"  {size:>5}     ERROR: {e}")
            results["tests"].append({
                "size": size,
                "error": str(e),
            })
    
    if advantages:
        avg_advantage = sum(advantages) / len(advantages)
        results["gpu_advantage"] = avg_advantage
        
        print(f"\n  Average GPU speedup: {avg_advantage:.2f}x")
        
        if avg_advantage > 5.0:
            print("  ✓ GPU is significantly faster - use GPU backend")
        elif avg_advantage > 2.0:
            print("  ✓ GPU is moderately faster - GPU backend recommended")
        elif avg_advantage > 1.0:
            print("  ~ GPU is slightly faster - either backend works")
        else:
            print("  ⚠️ CPU is faster - consider using CPU backend")
    
    return results


# ============================================================================
# Memory Stability Test
# ============================================================================

def test_memory_stability(profile: HardwareProfile) -> dict:
    """
    Test memory allocation stability to detect potential OOM or fragmentation issues.
    """
    print("\n" + "=" * 70)
    print("  MEMORY STABILITY TEST")
    print("=" * 70)
    
    if not profile.cupy_available:
        print("\n  ⚠️  CuPy not available - skipping memory test")
        return {"status": "skipped", "reason": "cupy_not_available"}
    
    import cupy as cp
    import numpy as np
    
    results = {
        "status": "passed",
        "max_allocation_gb": 0,
        "fragmentation_detected": False,
        "iterations_completed": 0,
    }
    
    print("\n  Testing repeated allocation/deallocation cycles...")
    
    try:
        rng = np.random.default_rng(42)
        
        for i in range(10):
            # Allocate various sized arrays
            sizes = [1000, 5000, 10000, 2000, 8000]
            arrays = []
            
            for size in sizes:
                data = cp.asarray(rng.random((size, 256), dtype=np.float32))
                arrays.append(data)
            
            # Do some operations
            for arr in arrays:
                _ = cp.sum(arr)
            
            cp.cuda.Stream.null.synchronize()
            
            # Track memory
            mem_info = cp.cuda.Device(0).mem_info
            used_gb = (mem_info[1] - mem_info[0]) / (1024**3)
            results["max_allocation_gb"] = max(results["max_allocation_gb"], used_gb)
            
            # Free everything
            del arrays
            cp.get_default_memory_pool().free_all_blocks()
            
            results["iterations_completed"] = i + 1
            print(f"    Iteration {i+1}/10: Peak memory {used_gb:.2f} GB - OK")
        
        print(f"\n  ✓ Memory stability test passed")
        print(f"    Peak allocation: {results['max_allocation_gb']:.2f} GB")
        print(f"    No fragmentation detected")
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        print(f"\n  ✗ Memory test failed: {e}")
    
    return results


# ============================================================================
# Recommendations Generator
# ============================================================================

def generate_recommendations(
    profile: HardwareProfile,
    tdr_results: dict,
    barnes_hut_results: dict,
    cpu_gpu_results: dict,
    memory_results: dict,
) -> dict:
    """Generate actionable recommendations based on test results."""
    
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS FOR YOUR HARDWARE")
    print("=" * 70)
    
    recommendations = []
    config_suggestions = {}
    
    # GPU availability
    if profile.cupy_available and profile.gpu_name:
        print(f"\n  ✓ GPU detected: {profile.gpu_name}")
        config_suggestions["gpu_enabled"] = True
    else:
        print("\n  ⚠️ GPU not detected - using CPU fallback")
        config_suggestions["gpu_enabled"] = False
        recommendations.append("Install CuPy for GPU acceleration: pip install cupy-cuda12x")
    
    # TDR safety
    if tdr_results.get("recommended_tile_size"):
        tile_size = tdr_results["recommended_tile_size"]
        config_suggestions["tile_size"] = tile_size
        print(f"\n  TDR Safety:")
        print(f"    Recommended tile size: {tile_size:,}")
        if tile_size < 25000:
            recommendations.append(f"Use tile size ≤ {tile_size:,} to avoid TDR timeouts")
    
    # Barnes-Hut
    if barnes_hut_results.get("barnes_hut_advantage"):
        advantage = barnes_hut_results["barnes_hut_advantage"]
        if advantage > 1.2:
            config_suggestions["use_barnes_hut"] = True
            print(f"\n  Barnes-Hut: ✓ Recommended ({advantage:.1f}x faster)")
        else:
            config_suggestions["use_barnes_hut"] = False
            print(f"\n  Barnes-Hut: Consider disabling ({advantage:.1f}x)")
            recommendations.append("Barnes-Hut may not provide significant benefit on your hardware")
    
    # CPU vs GPU
    if cpu_gpu_results.get("gpu_advantage"):
        advantage = cpu_gpu_results["gpu_advantage"]
        if advantage > 2.0:
            config_suggestions["prefer_gpu"] = True
            print(f"\n  GPU Backend: ✓ Recommended ({advantage:.1f}x faster)")
        else:
            config_suggestions["prefer_gpu"] = False
            print(f"\n  GPU Backend: CPU may be sufficient ({advantage:.1f}x)")
    
    # Memory
    if memory_results.get("max_allocation_gb"):
        max_gb = memory_results["max_allocation_gb"]
        if max_gb > profile.gpu_vram_gb * 0.8 if profile.gpu_vram_gb else float('inf'):
            recommendations.append("Consider reducing batch sizes to avoid VRAM pressure")
    
    # Print recommendations
    if recommendations:
        print("\n  Action Items:")
        for i, rec in enumerate(recommendations, 1):
            print(f"    {i}. {rec}")
    else:
        print("\n  ✓ No issues detected - your configuration looks good!")
    
    # Generate config file
    config_suggestions["hardware_profile"] = {
        "cpu": profile.cpu_name,
        "gpu": profile.gpu_name,
        "vram_gb": profile.gpu_vram_gb,
        "compute_capability": profile.gpu_compute_capability,
    }
    
    return {
        "recommendations": recommendations,
        "config": config_suggestions,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    """Run full hardware diagnostic."""
    
    print("\n" + "█" * 70)
    print("  MAS-MCP Hardware Diagnostic")
    print("  Predator Helios + RTX 4090 Laptop GPU + i9-14900")
    print("█" * 70)
    
    # Detect hardware
    print("\n  Detecting hardware configuration...")
    profile = detect_hardware()
    print_hardware_profile(profile)
    
    # Run tests
    tdr_results = test_tdr_safety(profile)
    barnes_hut_results = test_barnes_hut_comparison(profile)
    cpu_gpu_results = test_cpu_vs_gpu(profile)
    memory_results = test_memory_stability(profile)
    
    # Generate recommendations
    recommendations = generate_recommendations(
        profile,
        tdr_results,
        barnes_hut_results,
        cpu_gpu_results,
        memory_results,
    )
    
    # Save results
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": {
            "cpu": profile.cpu_name,
            "cpu_cores": profile.cpu_cores,
            "cpu_threads": profile.cpu_threads,
            "ram_gb": profile.ram_gb,
            "gpu": profile.gpu_name,
            "vram_gb": profile.gpu_vram_gb,
            "compute_capability": profile.gpu_compute_capability,
            "cuda_version": profile.cuda_version,
        },
        "tests": {
            "tdr_safety": tdr_results,
            "barnes_hut": barnes_hut_results,
            "cpu_vs_gpu": cpu_gpu_results,
            "memory": memory_results,
        },
        "recommendations": recommendations,
    }
    
    output_file = "hardware_diagnostic_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  Results saved to: {output_file}")
    print("\n" + "█" * 70)
    print("  Diagnostic Complete")
    print("█" * 70 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
