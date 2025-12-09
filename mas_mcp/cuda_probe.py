#!/usr/bin/env python3
"""
CUDA-only probe for MAS-MCP GPU readiness.

This script validates that ONNX Runtime is using CUDA (not TensorRT or CPU fallback).
Run this before enabling GPU features in MAS-MCP.

Usage:
    uv run python cuda_probe.py
"""

import sys
import os
import time
from typing import Any

def check_cudnn_dlls() -> dict[str, Any]:
    """Check if cuDNN DLLs are accessible."""
    cudnn_path = os.environ.get("CUDNN_PATH", "")
    cuda_path = os.environ.get("CUDA_PATH", "")
    
    result = {
        "CUDNN_PATH": cudnn_path,
        "CUDA_PATH": cuda_path,
        "cudnn_dll_found": False,
        "cuda_in_path": False,
    }
    
    # Check for cuDNN DLL
    cudnn_dll_paths = [
        os.path.join(cudnn_path, "bin", "13.1", "cudnn64_9.dll"),
        os.path.join(cudnn_path, "bin", "12.8", "cudnn64_9.dll"),
    ]
    for p in cudnn_dll_paths:
        if os.path.exists(p):
            result["cudnn_dll_found"] = True
            result["cudnn_dll_path"] = p
            break
    
    # Check CUDA in PATH
    path_env = os.environ.get("PATH", "")
    result["cuda_in_path"] = "CUDA" in path_env or "cuda" in path_env.lower()
    
    return result


def test_onnx_cuda_only(n: int = 1024, iterations: int = 5) -> dict[str, Any]:
    """
    Test ONNX Runtime with CUDA provider ONLY.
    
    Forces CUDA provider and validates it's actually being used (not fallback).
    """
    try:
        import onnxruntime as ort
        import numpy as np
    except ImportError as e:
        return {"error": f"Import failed: {e}"}
    
    # Check available providers
    available = ort.get_available_providers()
    
    result = {
        "onnxruntime_version": ort.__version__,
        "available_providers": available,
        "cuda_available": "CUDAExecutionProvider" in available,
        "tensorrt_available": "TensorrtExecutionProvider" in available,
    }
    
    if not result["cuda_available"]:
        result["error"] = "CUDAExecutionProvider not available"
        return result
    
    # Create minimal matmul model
    import onnx
    from onnx import helper, TensorProto
    
    A = helper.make_tensor_value_info('A', TensorProto.FLOAT, [n, n])
    B = helper.make_tensor_value_info('B', TensorProto.FLOAT, [n, n])
    C = helper.make_tensor_value_info('C', TensorProto.FLOAT, [n, n])
    
    matmul_node = helper.make_node('MatMul', ['A', 'B'], ['C'])
    graph = helper.make_graph([matmul_node], 'cuda_probe', [A, B], [C])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 12)])
    model.ir_version = 8
    
    # Create CUDA-only session with explicit device config
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    
    # CUDA provider with explicit config (skip TensorRT entirely)
    providers = [
        ("CUDAExecutionProvider", {
            "device_id": 0,
            "arena_extend_strategy": "kSameAsRequested",
            "gpu_mem_limit": 2 * 1024 * 1024 * 1024,  # 2GB limit for safety
            "cudnn_conv_algo_search": "EXHAUSTIVE",
        }),
        # CPU fallback (should not be used if CUDA works)
        ("CPUExecutionProvider", {}),
    ]
    
    try:
        sess = ort.InferenceSession(
            model.SerializeToString(),
            sess_options,
            providers=providers
        )
    except Exception as e:
        result["error"] = f"Session creation failed: {e}"
        return result
    
    # Get actual provider being used
    actual_providers = sess.get_providers()
    result["session_providers"] = actual_providers
    result["using_cuda"] = "CUDAExecutionProvider" in actual_providers
    
    if not result["using_cuda"]:
        result["warning"] = "CUDA provider not in session - possible fallback to CPU"
    
    # Create input data
    a_data = np.random.randn(n, n).astype(np.float32)
    b_data = np.random.randn(n, n).astype(np.float32)
    
    # Warm-up runs (important for GPU kernel compilation)
    for _ in range(3):
        _ = sess.run(None, {'A': a_data, 'B': b_data})
    
    # Timed runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        out = sess.run(None, {'A': a_data, 'B': b_data})
        # Force sync by accessing result
        _ = out[0][0, 0]
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)
    
    result["benchmark"] = {
        "n": n,
        "iterations": iterations,
        "mean_ms": float(np.mean(times)),
        "std_ms": float(np.std(times)),
        "min_ms": float(np.min(times)),
        "max_ms": float(np.max(times)),
    }
    
    # Compare with CPU to verify GPU is actually faster
    cpu_sess = ort.InferenceSession(
        model.SerializeToString(),
        sess_options,
        providers=["CPUExecutionProvider"]
    )
    
    # Warm-up CPU
    for _ in range(3):
        _ = cpu_sess.run(None, {'A': a_data, 'B': b_data})
    
    cpu_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        out = cpu_sess.run(None, {'A': a_data, 'B': b_data})
        _ = out[0][0, 0]
        elapsed_ms = (time.perf_counter() - start) * 1000
        cpu_times.append(elapsed_ms)
    
    cpu_mean = float(np.mean(cpu_times))
    gpu_mean = result["benchmark"]["mean_ms"]
    
    result["cpu_benchmark"] = {
        "mean_ms": cpu_mean,
        "min_ms": float(np.min(cpu_times)),
    }
    
    speedup = cpu_mean / gpu_mean if gpu_mean > 0 else 0
    result["speedup_vs_cpu"] = speedup
    result["gpu_confirmed"] = speedup > 1.2  # At least 20% faster = GPU is working
    
    return result


def print_status(result: dict[str, Any]) -> None:
    """Pretty-print the probe results."""
    print("\n" + "=" * 70)
    print("  🎮 MAS-MCP CUDA PROBE - GPU Readiness Check")
    print("=" * 70)
    
    # Environment
    print("\n📦 Environment:")
    if "CUDNN_PATH" in result.get("env", {}):
        env = result["env"]
        print(f"   CUDNN_PATH: {env['CUDNN_PATH']}")
        print(f"   CUDA_PATH:  {env['CUDA_PATH']}")
        print(f"   cuDNN DLL:  {'✅ Found' if env['cudnn_dll_found'] else '❌ Not found'}")
        print(f"   CUDA PATH:  {'✅ In PATH' if env['cuda_in_path'] else '❌ Not in PATH'}")
    
    # ONNX Runtime
    print("\n🧠 ONNX Runtime:")
    print(f"   Version: {result.get('onnxruntime_version', 'N/A')}")
    print(f"   Available: {result.get('available_providers', [])}")
    print(f"   Session:   {result.get('session_providers', [])}")
    
    cuda_status = "✅" if result.get("using_cuda") else "❌"
    print(f"   CUDA:      {cuda_status} {'Active' if result.get('using_cuda') else 'Not active'}")
    
    # Benchmark
    if "benchmark" in result:
        bench = result["benchmark"]
        cpu_bench = result.get("cpu_benchmark", {})
        print(f"\n⚡ Benchmark (N={bench['n']}, {bench['iterations']} iterations):")
        print(f"   GPU Mean: {bench['mean_ms']:.2f}ms (±{bench['std_ms']:.2f}ms)")
        print(f"   CPU Mean: {cpu_bench.get('mean_ms', 0):.2f}ms")
        print(f"   Speedup:  {result.get('speedup_vs_cpu', 0):.2f}x")
    
    # Final verdict
    print("\n" + "-" * 70)
    if result.get("gpu_confirmed"):
        print("  ✅ GPU ACCELERATION CONFIRMED - MAS-MCP GPU tools ready")
    elif result.get("error"):
        print(f"  ❌ ERROR: {result['error']}")
    elif result.get("warning"):
        print(f"  ⚠️  WARNING: {result['warning']}")
    else:
        print("  ⚠️  GPU not significantly faster - check configuration")
    print("-" * 70 + "\n")


def main():
    """Run the CUDA probe."""
    print("🔍 Checking environment...")
    env_result = check_cudnn_dlls()
    
    print("🧪 Testing ONNX Runtime CUDA provider...")
    onnx_result = test_onnx_cuda_only(n=2048, iterations=5)
    
    # Combine results
    full_result = {
        "env": env_result,
        **onnx_result,
    }
    
    print_status(full_result)
    
    # Exit code based on GPU confirmation
    if full_result.get("gpu_confirmed"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
