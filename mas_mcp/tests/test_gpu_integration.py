"""GPU integration tests for MAS-MCP.

These tests validate the GPU execution lane (CuPy / CUDA DLLs / batch scoring).
They are expected to be skipped on machines where GPU dependencies are not
installed.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest


def _maybe_prepend_cuda_bin_to_path() -> None:
    """Best-effort CUDA DLL path setup.

    Keep this optional: don't force hardcoded paths that break portability.
    Override with `MAS_CUDA_BIN` if needed.
    """

    cuda_bin = os.environ.get(
        "MAS_CUDA_BIN",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin",
    )
    if os.path.isdir(cuda_bin) and cuda_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = cuda_bin + os.pathsep + os.environ.get("PATH", "")


_maybe_prepend_cuda_bin_to_path()

# Ensure we can import the repo-local mas_mcp `server.py` when running tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import mas_gpu_batch_score, mas_gpu_score, mas_gpu_status, mas_pulse, mas_scan  # noqa: E402


@pytest.fixture(scope="session")
def gpu_status() -> dict:
    """Skip GPU integration tests unless the GPU lane is actually available."""

    status = mas_gpu_status()
    if not status.get("gpu_available", False):
        pytest.skip(
            "GPU lane not available (missing GPU deps or CUDA). Install extras like `uv sync --extra gpu` in your GPU venv.",
        )
    return status


def test_gpu_status(gpu_status):
    """Test GPU status tool"""
    print("\n" + "="*60)
    print("TEST: mas_gpu_status")
    print("="*60)
    
    result = mas_gpu_status()
    
    print(f"Backend: {result.get('backend', 'N/A')}")
    print(f"GPU Available: {result.get('gpu_available', False)}")
    
    if 'cupy' in result:
        cp_info = result['cupy']
        print(f"CuPy Device: {cp_info.get('device_name', 'N/A')}")
        print(f"Memory: {cp_info.get('total_memory_gb', 0):.1f} GB")
        print(f"Compute: SM {cp_info.get('compute_capability', 'N/A')}")
    
    assert result.get("gpu_available", False), "GPU not available!"
    print("✅ GPU status OK")
    return result


def test_single_score(gpu_status):
    """Test single entity scoring"""
    print("\n" + "="*60)
    print("TEST: mas_gpu_score (single entity)")
    print("="*60)
    
    result = mas_gpu_score(
        entity_name="Orackla Nocticula",
        whr=0.491,
        tier=1.0,
        cup="J"
    )
    
    print(f"Entity: {result['entity_name']}")
    print(f"Backend: {result['backend']}")
    print(f"Novelty: {result['novelty']:.4f}")
    print(f"Redundancy: {result['redundancy']:.4f}")
    print(f"Safety: {result['safety']:.4f}")
    print(f"Overall: {result['overall']:.4f}")
    
    if result.get("backend") != "cupy":
        pytest.skip(f"Expected CuPy backend for this test, got {result.get('backend')}")
    assert "novelty" in result
    assert "overall" in result
    print("✅ Single score OK")
    return result


def test_batch_score(gpu_status):
    """Test batch scoring with varying sizes"""
    print("\n" + "="*60)
    print("TEST: mas_gpu_batch_score (batch)")
    print("="*60)
    
    # Test entities from the Codex
    entities = [
        {"name": "The Decorator", "whr": 0.464, "tier": 0.5, "cup": "K"},
        {"name": "Orackla Nocticula", "whr": 0.491, "tier": 1.0, "cup": "J"},
        {"name": "Madam Umeko Ketsuraku", "whr": 0.533, "tier": 1.0, "cup": "F"},
        {"name": "Dr. Lysandra Thorne", "whr": 0.58, "tier": 1.0, "cup": "E"},
        {"name": "Kali Nyx Ravenscar", "whr": 0.556, "tier": 2.0, "cup": "H"},
        {"name": "Vesper Mnemosyne Lockhart", "whr": 0.573, "tier": 2.0, "cup": "F"},
        {"name": "Seraphine Kore Ashenhelm", "whr": 0.592, "tier": 2.0, "cup": "G"},
        {"name": "Claudine Sin'claire", "whr": 0.563, "tier": 3.0, "cup": "I"},
    ]
    
    result = mas_gpu_batch_score(entities)
    
    print(f"Count: {result['count']}")
    print(f"Backend: {result['backend']}")
    print(f"Elapsed: {result['elapsed_ms']:.2f} ms")
    print(f"\nAggregate:")
    for key, val in result['aggregate'].items():
        print(f"  {key}: {val:.4f}")
    
    print(f"\nTop scores:")
    for score in result['scores'][:3]:
        print(f"  {score['id']}: overall={score['overall']:.4f}")
    
    if result.get("backend") != "cupy":
        pytest.skip(f"Expected CuPy backend for this test, got {result.get('backend')}")
    assert result["count"] == len(entities)
    print("✅ Batch score OK")
    return result


def test_large_batch(gpu_status):
    """Test performance with larger batches"""
    print("\n" + "="*60)
    print("TEST: Large batch scaling")
    print("="*60)
    
    import random
    
    batch_sizes = [100, 500, 1000]
    
    for size in batch_sizes:
        entities = [
            {
                "name": f"Entity_{i}",
                "whr": 0.4 + random.random() * 0.3,
                "tier": random.choice([0.5, 1.0, 2.0, 3.0, 4.0]),
                "cup": random.choice(list("ABCDEFGHIJK")),
            }
            for i in range(size)
        ]
        
        start = time.perf_counter()
        result = mas_gpu_batch_score(entities)
        elapsed = (time.perf_counter() - start) * 1000
        
        throughput = size / (elapsed / 1000)
        
        print(f"  {size:,} entities: {result['elapsed_ms']:.2f} ms ({throughput:,.0f} entities/sec)")
    
    print("✅ Large batch OK")


def test_pulse(gpu_status):
    """Test the pulse tool (situational awareness)"""
    print("\n" + "="*60)
    print("TEST: mas_pulse (situational awareness)")
    print("="*60)
    
    result = mas_pulse()
    
    print(f"Status: {result.get('status', 'N/A')}")
    print(f"GPU Backend: {result.get('gpu_backend', 'N/A')}")
    print(f"Recommendations: {len(result.get('recommendations', []))}")
    
    if 'key_entities' in result:
        for ent, data in list(result['key_entities'].items())[:3]:
            print(f"  {ent}: {data}")
    
    print("✅ Pulse OK")
    return result


def test_scan(gpu_status):
    """Test the scan tool"""
    print("\n" + "="*60)
    print("TEST: mas_scan (codebase scan)")
    print("="*60)
    
    # Scan just the mas_mcp directory for speed
    result = mas_scan(target=".")
    
    print(f"Status: {result.get('status', 'N/A')}")
    print(f"Files scanned: {result.get('files_scanned', 0)}")
    
    if 'signal_counts' in result:
        for sig, count in result['signal_counts'].items():
            if count > 0:
                print(f"  {sig}: {count}")
    
    print("✅ Scan OK")
    return result


if __name__ == "__main__":
    print("="*60)
    print("MAS-MCP GPU INTEGRATION TEST SUITE")
    print("="*60)
    
    try:
        test_gpu_status()
        test_single_score()
        test_batch_score()
        test_large_batch()
        test_pulse()
        test_scan()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
