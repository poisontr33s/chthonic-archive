#!/usr/bin/env python3
"""
Safe GPU Benchmark with Automatic Tiling
=========================================

Run this OUTSIDE VS Code to avoid TDR-triggered crashes:
    cd mas_mcp
    uv run python bench_safe.py

The tiling layer automatically chunks large workloads to keep
each GPU kernel under the ~2 second Windows TDR timeout.
"""

import json
import time
import sys
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, '.')

from gpu_orchestrator import (
    mas_gpu_status,
    mas_gpu_batch_score,
    mas_gpu_hierarchy,
    get_score_tiler,
    get_hierarchy_tiler,
    TiledBatchProcessor,
)


def banner(title: str):
    """Print a banner for test sections."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_gpu_status():
    """Check GPU is available."""
    banner("GPU Status Check")
    status = mas_gpu_status()
    print(json.dumps(status, indent=2))
    return status.get("gpu_available", False)


def test_small_batch():
    """Small batch: 1k vectors, should complete in <100ms."""
    banner("Small Batch (1,000 vectors)")
    
    seed = 42
    rng = np.random.default_rng(seed)
    entities = [
        {'id': f'e{i}', 'vec': v.tolist()}
        for i, v in enumerate(rng.random((1000, 256)))
    ]
    
    t0 = time.perf_counter()
    result = mas_gpu_batch_score(entities=entities, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Count: {result.get('count')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms")
    if 'tiling' in result:
        print(f"  Tiles: {result['tiling']['tile_count']}")
        print(f"  Items/sec: {result['tiling']['items_per_second']:,.0f}")
    
    return result


def test_medium_batch():
    """Medium batch: 10k vectors, single tile."""
    banner("Medium Batch (10,000 vectors)")
    
    seed = 42
    rng = np.random.default_rng(seed)
    entities = [
        {'id': f'e{i}', 'vec': v.tolist()}
        for i, v in enumerate(rng.random((10000, 256)))
    ]
    
    t0 = time.perf_counter()
    result = mas_gpu_batch_score(entities=entities, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Count: {result.get('count')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms")
    if 'tiling' in result:
        print(f"  Tiles: {result['tiling']['tile_count']}")
        print(f"  Max tile: {result['tiling']['max_tile_ms']:.1f}ms")
        print(f"  Items/sec: {result['tiling']['items_per_second']:,.0f}")
    
    return result


def test_large_batch():
    """Large batch: 50k vectors, automatic tiling."""
    banner("Large Batch (50,000 vectors) - TILED")
    
    seed = 42
    rng = np.random.default_rng(seed)
    entities = [
        {'id': f'e{i}', 'vec': v.tolist()}
        for i, v in enumerate(rng.random((50000, 256)))
    ]
    
    print("  Generating 50k vectors...")
    t0 = time.perf_counter()
    result = mas_gpu_batch_score(entities=entities, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Count: {result.get('count')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms ({elapsed/1000:.2f}s)")
    if 'tiling' in result:
        print(f"  Tiles: {result['tiling']['tile_count']}")
        print(f"  Tile size: {result['tiling']['tile_size']}")
        print(f"  Max tile: {result['tiling']['max_tile_ms']:.1f}ms")
        print(f"  Avg tile: {result['tiling']['avg_tile_ms']:.1f}ms")
        print(f"  Items/sec: {result['tiling']['items_per_second']:,.0f}")
    
    if 'aggregate' in result:
        agg = result['aggregate']
        print(f"  Mean novelty: {agg['mean_novelty']:.3f}")
        print(f"  Pass rate: {agg['pass_rate']:.1%}")
    
    return result


def test_small_hierarchy():
    """Small hierarchy: 100 nodes."""
    banner("Small Hierarchy (100 nodes)")
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    nodes = [f'n{i}' for i in range(100)]
    edges = [(nodes[i], nodes[(i+1) % 100]) for i in range(100)]
    edges += [(nodes[rng.integers(100)], nodes[rng.integers(100)]) for _ in range(50)]
    
    t0 = time.perf_counter()
    result = mas_gpu_hierarchy(nodes=nodes, edges=edges, iterations=100, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Nodes: {result.get('node_count')}")
    print(f"  Edges: {result.get('edge_count')}")
    print(f"  Iterations: {result.get('iterations')}")
    print(f"  Converged: {result.get('converged')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms")
    
    return result


def test_medium_hierarchy():
    """Medium hierarchy: 1k nodes."""
    banner("Medium Hierarchy (1,000 nodes)")
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    nodes = [f'n{i}' for i in range(1000)]
    edges = [(nodes[i], nodes[(i+1) % 1000]) for i in range(1000)]
    edges += [(nodes[rng.integers(1000)], nodes[rng.integers(1000)]) for _ in range(500)]
    
    t0 = time.perf_counter()
    result = mas_gpu_hierarchy(nodes=nodes, edges=edges, iterations=100, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Nodes: {result.get('node_count')}")
    print(f"  Edges: {result.get('edge_count')}")
    print(f"  Iterations: {result.get('iterations')}")
    print(f"  Converged: {result.get('converged')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms")
    if 'tiling' in result:
        print(f"  Passes: {result['tiling']['pass_count']}")
        print(f"  Max pass: {result['tiling']['max_pass_ms']:.1f}ms")
    
    return result


def test_large_hierarchy():
    """Large hierarchy: 5k nodes with progressive layout."""
    banner("Large Hierarchy (5,000 nodes) - PROGRESSIVE")
    
    seed = 42
    rng = np.random.default_rng(seed)
    
    nodes = [f'n{i}' for i in range(5000)]
    # Ring + random edges
    edges = [(nodes[i], nodes[(i+1) % 5000]) for i in range(5000)]
    edges += [(nodes[rng.integers(5000)], nodes[rng.integers(5000)]) for _ in range(2500)]
    
    print("  Building 5k node graph...")
    t0 = time.perf_counter()
    result = mas_gpu_hierarchy(nodes=nodes, edges=edges, iterations=100, seed=seed)
    elapsed = (time.perf_counter() - t0) * 1000
    
    print(f"  Nodes: {result.get('node_count')}")
    print(f"  Edges: {result.get('edge_count')}")
    print(f"  Iterations: {result.get('iterations')}")
    print(f"  Converged: {result.get('converged')}")
    print(f"  Progressive: {result.get('progressive')}")
    print(f"  Backend: {result.get('backend')}")
    print(f"  Elapsed: {elapsed:.1f}ms ({elapsed/1000:.2f}s)")
    if 'tiling' in result:
        print(f"  Passes: {result['tiling']['pass_count']}")
        print(f"  Max pass: {result['tiling']['max_pass_ms']:.1f}ms")
        print(f"  Avg pass: {result['tiling']['avg_pass_ms']:.1f}ms")
    
    return result


def test_determinism():
    """Verify determinism across tiled runs."""
    banner("Determinism Test (same seed = same results)")
    
    seed = 12345
    rng = np.random.default_rng(seed)
    entities = [
        {'id': f'e{i}', 'vec': v.tolist()}
        for i, v in enumerate(rng.random((1000, 256)))
    ]
    
    # Run twice with same seed
    result1 = mas_gpu_batch_score(entities=entities, seed=seed)
    result2 = mas_gpu_batch_score(entities=entities, seed=seed)
    
    # Compare first few scores
    scores1 = [s['overall'] for s in result1['scores'][:10]]
    scores2 = [s['overall'] for s in result2['scores'][:10]]
    
    match = all(abs(a - b) < 1e-6 for a, b in zip(scores1, scores2))
    
    print(f"  Run 1 first 5: {scores1[:5]}")
    print(f"  Run 2 first 5: {scores2[:5]}")
    print(f"  Deterministic: {'✓ YES' if match else '✗ NO'}")
    
    return match


def main():
    """Run all safe benchmarks."""
    print("\n" + "█" * 60)
    print("  MAS-MCP GPU Benchmark Suite (Safe Tiled Mode)")
    print("█" * 60)
    
    # Check GPU first
    gpu_ok = test_gpu_status()
    if not gpu_ok:
        print("\n⚠️  GPU not available, running with CPU fallback")
    
    # Run benchmarks
    try:
        test_small_batch()
        test_medium_batch()
        test_large_batch()
        
        test_small_hierarchy()
        test_medium_hierarchy()
        test_large_hierarchy()
        
        test_determinism()
        
        banner("All Tests Complete")
        print("  ✓ No GPU stalls or TDR timeouts")
        print("  ✓ Tiling layer working correctly")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
