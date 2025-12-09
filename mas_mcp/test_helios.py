#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  MAS-MCP Hardware Test Suite for Predator Helios 18
  Target: RTX 4090 Laptop GPU + Intel i9-14900HX
═══════════════════════════════════════════════════════════════════════════════

Run from PowerShell (standalone terminal, NOT VS Code integrated):
    cd mas_mcp
    uv run python test_helios.py

This script:
  1. Diagnoses GPU detection and DLL loading issues
  2. Compares O(N²) vs Barnes-Hut spatial grid repulsion
  3. Tests at safe scales to avoid TDR timeout
  4. Provides specific recommendations for your hardware
"""

import sys
import os
import time
import platform
from typing import Dict, Any, Tuple, Optional

import numpy as np

# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: SYSTEM DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner(title: str, char: str = "═"):
    """Print a formatted banner."""
    width = 70
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def diagnose_system() -> Dict[str, Any]:
    """Gather system information for diagnostics."""
    print_banner("SYSTEM DIAGNOSTICS")
    
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }
    
    print(f"  Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"  Platform: {platform.platform()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  Architecture: {info['architecture']}")
    
    # Check CUDA environment variables
    print("\n  CUDA Environment Variables:")
    cuda_vars = ["CUDA_PATH", "CUDA_HOME", "NUMBA_FORCE_CUDA_CC", "CUPY_GPU_MEMORY_LIMIT"]
    for var in cuda_vars:
        val = os.environ.get(var, "(not set)")
        print(f"    {var}: {val}")
        info[var] = val
    
    # Check PATH for CUDA
    path = os.environ.get("PATH", "")
    cuda_in_path = any("cuda" in p.lower() for p in path.split(os.pathsep))
    print(f"\n  CUDA in PATH: {cuda_in_path}")
    info["cuda_in_path"] = cuda_in_path
    
    return info


def diagnose_nvidia_smi() -> Dict[str, Any]:
    """Check nvidia-smi availability and output."""
    print_banner("NVIDIA-SMI CHECK", "─")
    
    import subprocess
    
    info = {"nvidia_smi_available": False}
    
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            info["nvidia_smi_available"] = True
            output = result.stdout.strip()
            print(f"  GPU Info: {output}")
            
            # Parse output
            parts = output.split(", ")
            if len(parts) >= 4:
                info["gpu_name"] = parts[0].strip()
                info["memory"] = parts[1].strip()
                info["driver"] = parts[2].strip()
                info["compute_cap"] = parts[3].strip()
        else:
            print(f"  nvidia-smi failed: {result.stderr}")
            info["error"] = result.stderr
    except FileNotFoundError:
        print("  nvidia-smi: NOT FOUND (NVIDIA driver not installed or not in PATH)")
        info["error"] = "nvidia-smi not found"
    except subprocess.TimeoutExpired:
        print("  nvidia-smi: TIMEOUT (GPU may be busy or driver issue)")
        info["error"] = "timeout"
    except Exception as e:
        print(f"  nvidia-smi error: {e}")
        info["error"] = str(e)
    
    return info


def diagnose_cupy() -> Dict[str, Any]:
    """Test CuPy import and initialization."""
    print_banner("CUPY DIAGNOSTICS", "─")
    
    info = {"cupy_available": False}
    
    # First check if cupy is installed
    try:
        import importlib.util
        spec = importlib.util.find_spec("cupy")
        if spec is None:
            print("  CuPy: NOT INSTALLED")
            print("  → Install with: uv pip install cupy-cuda12x")
            info["status"] = "not_installed"
            return info
    except Exception as e:
        print(f"  CuPy spec check failed: {e}")
        info["error"] = str(e)
        return info
    
    # Try importing cupy
    try:
        import cupy as cp
        print(f"  CuPy version: {cp.__version__}")
        info["version"] = cp.__version__
    except ImportError as e:
        print(f"  CuPy import failed: {e}")
        print("  → This often means CUDA DLLs are missing or wrong version")
        info["status"] = "import_failed"
        info["error"] = str(e)
        return info
    
    # Try getting device info
    try:
        device = cp.cuda.Device(0)
        props = device.attributes
        
        info["cupy_available"] = True
        info["device_id"] = 0
        info["device_name"] = cp.cuda.runtime.getDeviceProperties(0)["name"].decode()
        info["compute_capability"] = device.compute_capability
        info["total_memory_gb"] = device.mem_info[1] / (1024**3)
        
        print(f"  Device: {info['device_name']}")
        print(f"  Compute Capability: {info['compute_capability']}")
        print(f"  Total Memory: {info['total_memory_gb']:.1f} GB")
        print("  Status: ✓ WORKING")
        
    except cp.cuda.runtime.CUDARuntimeError as e:
        print(f"  CUDA runtime error: {e}")
        info["status"] = "cuda_error"
        info["error"] = str(e)
    except Exception as e:
        print(f"  Device query failed: {e}")
        info["status"] = "device_error"
        info["error"] = str(e)
    
    return info


def diagnose_numba() -> Dict[str, Any]:
    """Test Numba CUDA import and initialization."""
    print_banner("NUMBA CUDA DIAGNOSTICS", "─")
    
    info = {"numba_cuda_available": False}
    
    try:
        from numba import cuda
        print(f"  Numba CUDA module: imported")
        
        if cuda.is_available():
            info["numba_cuda_available"] = True
            device = cuda.get_current_device()
            info["device_name"] = device.name.decode() if hasattr(device.name, 'decode') else device.name
            info["compute_capability"] = device.compute_capability
            
            print(f"  Device: {info['device_name']}")
            print(f"  Compute Capability: {info['compute_capability']}")
            print("  Status: ✓ WORKING")
        else:
            print("  Numba CUDA: NOT AVAILABLE")
            print("  → Check CUDA toolkit installation and DLL paths")
            info["status"] = "not_available"
            
    except ImportError as e:
        print(f"  Numba import failed: {e}")
        info["status"] = "import_failed"
        info["error"] = str(e)
    except Exception as e:
        print(f"  Numba CUDA error: {e}")
        info["status"] = "error"
        info["error"] = str(e)
    
    return info


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: REPULSION ALGORITHM COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════

def repulsion_exact_o_n2(positions: np.ndarray, strength: float = 1.0, min_dist: float = 0.01) -> np.ndarray:
    """
    Naive O(N²) repulsion - FOR COMPARISON ONLY.
    This is what was causing the hang at 1000 nodes.
    """
    n = positions.shape[0]
    forces = np.zeros_like(positions)
    
    for i in range(n):
        for j in range(i + 1, n):
            delta = positions[i] - positions[j]
            distance = np.linalg.norm(delta)
            
            if distance < min_dist:
                distance = min_dist
            
            force_magnitude = strength / (distance ** 2)
            force_direction = delta / distance
            force = force_direction * force_magnitude
            
            forces[i] += force
            forces[j] -= force
    
    return forces


def repulsion_barnes_hut(
    positions: np.ndarray,
    strength: float = 1.0,
    min_dist: float = 0.01,
    cutoff_factor: float = 10.0
) -> np.ndarray:
    """
    Barnes-Hut style spatial grid repulsion - O(N × k).
    
    Key optimization: Only compute exact forces with nearby nodes.
    Distant cells approximated as single point masses.
    """
    n = positions.shape[0]
    forces = np.zeros_like(positions)
    
    # Compute bounding box
    min_pos = positions.min(axis=0)
    max_pos = positions.max(axis=0)
    bbox_size = max_pos - min_pos
    
    # Compute cutoff distance based on average spacing
    avg_spacing = np.mean(bbox_size) / (n ** (1/3)) if n > 1 else 1.0
    cutoff = avg_spacing * cutoff_factor
    cell_size = cutoff
    
    # Avoid division by zero
    if cell_size < 1e-6:
        cell_size = 1.0
    
    # Build spatial grid (dictionary of cell -> node indices)
    grid: Dict[Tuple[int, int, int], list] = {}
    
    for i in range(n):
        cell = tuple(((positions[i] - min_pos) / cell_size).astype(int))
        if cell not in grid:
            grid[cell] = []
        grid[cell].append(i)
    
    # Precompute cell centers of mass for distant approximation
    cell_com: Dict[Tuple[int, int, int], Tuple[np.ndarray, int]] = {}
    for cell, indices in grid.items():
        cell_positions = positions[indices]
        com = cell_positions.mean(axis=0)
        cell_com[cell] = (com, len(indices))
    
    # Compute forces with spatial locality
    for i in range(n):
        my_cell = tuple(((positions[i] - min_pos) / cell_size).astype(int))
        
        # Check 27 neighboring cells (3x3x3 cube)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                for dz in range(-1, 2):
                    neighbor_cell = (my_cell[0] + dx, my_cell[1] + dy, my_cell[2] + dz)
                    
                    if neighbor_cell in grid:
                        # Exact computation for nearby nodes
                        for j in grid[neighbor_cell]:
                            if j <= i:
                                continue
                            
                            delta = positions[i] - positions[j]
                            distance = np.linalg.norm(delta)
                            
                            if distance < min_dist:
                                distance = min_dist
                            
                            force_magnitude = strength / (distance ** 2)
                            force_direction = delta / distance
                            force = force_direction * force_magnitude
                            
                            forces[i] += force
                            forces[j] -= force
        
        # Approximate distant cells (beyond immediate neighbors)
        for cell, (com, count) in cell_com.items():
            # Skip nearby cells (already computed exactly)
            if abs(cell[0] - my_cell[0]) <= 1 and abs(cell[1] - my_cell[1]) <= 1 and abs(cell[2] - my_cell[2]) <= 1:
                continue
            
            # Treat distant cell as single point mass at center of mass
            delta = positions[i] - com
            distance = np.linalg.norm(delta)
            
            if distance < cutoff:
                continue  # Too close to approximate
            
            if distance < min_dist:
                distance = min_dist
            
            # Force from "count" nodes at center of mass
            force_magnitude = strength * count / (distance ** 2)
            force_direction = delta / distance
            forces[i] += force_direction * force_magnitude
    
    return forces


def benchmark_repulsion_algorithms():
    """Compare O(N²) vs Barnes-Hut at various scales."""
    print_banner("REPULSION ALGORITHM BENCHMARK")
    
    np.random.seed(42)
    
    test_sizes = [50, 100, 200, 500, 1000]
    
    print("\n  Testing repulsion computation time (single iteration):")
    print("  " + "-" * 60)
    print(f"  {'Nodes':>8} │ {'O(N²) (ms)':>12} │ {'Barnes-Hut (ms)':>16} │ {'Speedup':>8}")
    print("  " + "-" * 60)
    
    results = []
    
    for n in test_sizes:
        # Generate random 3D positions
        positions = np.random.randn(n, 3).astype(np.float32)
        
        # Time O(N²) - with timeout for large sizes
        if n <= 500:  # Don't run O(N²) for large sizes
            t0 = time.perf_counter()
            _ = repulsion_exact_o_n2(positions)
            t_exact = (time.perf_counter() - t0) * 1000
        else:
            # Estimate based on O(N²) scaling
            t_exact = results[-1]["exact"] * (n / test_sizes[test_sizes.index(n) - 1]) ** 2
            t_exact = f"~{t_exact:.0f} (est)"
        
        # Time Barnes-Hut
        t0 = time.perf_counter()
        _ = repulsion_barnes_hut(positions)
        t_barnes = (time.perf_counter() - t0) * 1000
        
        # Calculate speedup
        if isinstance(t_exact, str):
            speedup = "N/A"
            exact_val = float(t_exact.split("~")[1].split(" ")[0])
        else:
            speedup = f"{t_exact / t_barnes:.1f}x"
            exact_val = t_exact
        
        results.append({"n": n, "exact": exact_val if isinstance(exact_val, float) else t_exact, "barnes": t_barnes})
        
        exact_str = f"{t_exact:.1f}" if isinstance(t_exact, (int, float)) else t_exact
        print(f"  {n:>8} │ {exact_str:>12} │ {t_barnes:>16.1f} │ {speedup:>8}")
    
    print("  " + "-" * 60)
    print("\n  Key insight: Barnes-Hut scales much better for large graphs!")
    print("  At 1000 nodes: O(N²) ≈ 1M operations, Barnes-Hut ≈ 27k (assuming k≈27 neighbors)")
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: HIERARCHY LAYOUT TEST
# ═══════════════════════════════════════════════════════════════════════════════

def test_hierarchy_safe_scale():
    """Test hierarchy layout at safe scales using MAS-MCP's actual implementation."""
    print_banner("HIERARCHY LAYOUT TEST (Safe Scale)")
    
    try:
        from gpu_orchestrator import mas_gpu_hierarchy
    except ImportError:
        print("  ERROR: Could not import gpu_orchestrator")
        print("  → Run from mas_mcp directory: cd mas_mcp && uv run python test_helios.py")
        return None
    
    test_cases = [
        (50, 75, 50, "Tiny"),
        (100, 150, 50, "Small"),
        (200, 300, 30, "Medium"),
        (500, 750, 20, "Large"),
    ]
    
    print("\n  Testing hierarchy layout (with Barnes-Hut repulsion):")
    print("  " + "-" * 65)
    print(f"  {'Case':>8} │ {'Nodes':>6} │ {'Edges':>6} │ {'Iters':>6} │ {'Time (ms)':>10} │ {'Status':>8}")
    print("  " + "-" * 65)
    
    np.random.seed(42)
    
    for nodes_count, edges_count, iterations, label in test_cases:
        nodes = [f"n{i}" for i in range(nodes_count)]
        
        # Create ring + random edges
        edges = [(nodes[i], nodes[(i+1) % nodes_count]) for i in range(nodes_count)]
        extra = edges_count - nodes_count
        if extra > 0:
            edges += [(nodes[np.random.randint(nodes_count)], nodes[np.random.randint(nodes_count)]) 
                     for _ in range(extra)]
        
        try:
            t0 = time.perf_counter()
            result = mas_gpu_hierarchy(nodes=nodes, edges=edges, iterations=iterations, seed=42)
            elapsed = (time.perf_counter() - t0) * 1000
            
            status = "✓ OK"
            print(f"  {label:>8} │ {nodes_count:>6} │ {len(edges):>6} │ {iterations:>6} │ {elapsed:>10.1f} │ {status:>8}")
            
        except KeyboardInterrupt:
            print(f"  {label:>8} │ {nodes_count:>6} │ {len(edges):>6} │ {iterations:>6} │ {'TIMEOUT':>10} │ {'✗ FAIL':>8}")
            break
        except Exception as e:
            print(f"  {label:>8} │ {nodes_count:>6} │ {len(edges):>6} │ {iterations:>6} │ {'ERROR':>10} │ {'✗ FAIL':>8}")
            print(f"           Error: {e}")
    
    print("  " + "-" * 65)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: BATCH SCORING TEST
# ═══════════════════════════════════════════════════════════════════════════════

def test_batch_scoring():
    """Test batch scoring at various scales."""
    print_banner("BATCH SCORING TEST")
    
    try:
        from gpu_orchestrator import mas_gpu_batch_score
    except ImportError:
        print("  ERROR: Could not import gpu_orchestrator")
        return None
    
    test_sizes = [100, 1000, 5000, 10000]
    
    print("\n  Testing batch scoring with tiling:")
    print("  " + "-" * 55)
    print(f"  {'Count':>8} │ {'Time (ms)':>10} │ {'Items/sec':>12} │ {'Tiles':>6}")
    print("  " + "-" * 55)
    
    np.random.seed(42)
    
    for count in test_sizes:
        entities = [
            {"id": f"e{i}", "vec": np.random.randn(256).tolist()}
            for i in range(count)
        ]
        
        try:
            t0 = time.perf_counter()
            result = mas_gpu_batch_score(entities=entities, seed=42)
            elapsed = (time.perf_counter() - t0) * 1000
            
            items_per_sec = count / (elapsed / 1000) if elapsed > 0 else 0
            tiles = result.get("tiling", {}).get("tile_count", 1)
            
            print(f"  {count:>8} │ {elapsed:>10.1f} │ {items_per_sec:>12,.0f} │ {tiles:>6}")
            
        except Exception as e:
            print(f"  {count:>8} │ {'ERROR':>10} │ {'-':>12} │ {'-':>6}")
            print(f"           Error: {e}")
    
    print("  " + "-" * 55)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def print_recommendations(system_info: Dict, nvidia_info: Dict, cupy_info: Dict, numba_info: Dict):
    """Print hardware-specific recommendations."""
    print_banner("RECOMMENDATIONS FOR YOUR HARDWARE")
    
    gpu_working = cupy_info.get("cupy_available", False) or numba_info.get("numba_cuda_available", False)
    nvidia_working = nvidia_info.get("nvidia_smi_available", False)
    
    print("\n  STATUS SUMMARY:")
    print(f"    NVIDIA Driver: {'✓ OK' if nvidia_working else '✗ MISSING'}")
    print(f"    CuPy GPU:      {'✓ OK' if cupy_info.get('cupy_available') else '✗ NOT WORKING'}")
    print(f"    Numba CUDA:    {'✓ OK' if numba_info.get('numba_cuda_available') else '✗ NOT WORKING'}")
    
    print("\n  RECOMMENDATIONS:")
    
    if not nvidia_working:
        print("""
    1. NVIDIA DRIVER MISSING
       → Download latest Game Ready Driver from nvidia.com
       → Ensure 'nvidia-smi' is accessible from PowerShell
       → Restart after installation
""")
    
    if nvidia_working and not cupy_info.get("cupy_available"):
        compute_cap = nvidia_info.get("compute_cap", "unknown")
        print(f"""
    2. CUPY NOT WORKING (GPU detected: {nvidia_info.get('gpu_name', 'unknown')})
       Compute Capability: {compute_cap}
       
       → Install CuPy for your CUDA version:
         uv pip install cupy-cuda12x
         
       → Or try specific CUDA version (check nvidia-smi):
         uv pip install cupy-cuda12-3  # For CUDA 12.3
         uv pip install cupy-cuda11x   # For CUDA 11.x
         
       → Set environment variables:
         $env:CUDA_PATH = "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.x"
         $env:CUDA_HOME = $env:CUDA_PATH
""")
    
    if not numba_info.get("numba_cuda_available"):
        print("""
    3. NUMBA CUDA NOT WORKING
       → Install CUDA Toolkit from developer.nvidia.com
       → Add to PATH:
         C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.x\\bin
         C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.x\\libnvvp
       → Set NUMBA_FORCE_CUDA_CC=8.9 (for RTX 4090)
""")
    
    if gpu_working:
        print("""
    ✓ GPU ACCELERATION IS WORKING!
    
    Performance tips for RTX 4090 Laptop:
      • Use batch sizes of 5000-10000 for optimal throughput
      • Keep hierarchy layouts under 2000 nodes per tile
      • Monitor GPU temp with nvidia-smi (throttling at ~83°C)
      • Consider WSL2 for more stable CUDA support
""")
    
    print("""
    GENERAL TIPS:
      • Run benchmarks from standalone PowerShell (not VS Code terminal)
      • Disable Hardware-Accelerated GPU Scheduling if unstable
      • Keep terminal window in focus during long operations
      • Monitor with: nvidia-smi -l 1  (updates every second)
""")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run the full Helios hardware test suite."""
    print("\n" + "█" * 70)
    print("  MAS-MCP Hardware Test Suite")
    print("  Target: Predator Helios 18 / RTX 4090 Laptop / i9-14900HX")
    print("█" * 70)
    
    # Diagnostics
    system_info = diagnose_system()
    nvidia_info = diagnose_nvidia_smi()
    cupy_info = diagnose_cupy()
    numba_info = diagnose_numba()
    
    # Algorithm comparison
    benchmark_repulsion_algorithms()
    
    # MAS-MCP integration tests
    test_hierarchy_safe_scale()
    test_batch_scoring()
    
    # Recommendations
    print_recommendations(system_info, nvidia_info, cupy_info, numba_info)
    
    print_banner("TEST COMPLETE")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
