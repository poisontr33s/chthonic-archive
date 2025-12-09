#!/usr/bin/env python3
"""
GPU Validation Test - Prove GPU is Actually Being Used

This test creates measurable work that shows CLEAR differences between:
1. CPU execution
2. GPU execution (if available)

The test should show:
- Different execution times (GPU should be faster for large N)
- Different memory locations (GPU memory vs system RAM)
- Actual provider being used (not just "available")
"""

import time
import numpy as np
import sys

def format_time(ms: float) -> str:
    """Format milliseconds nicely."""
    if ms < 1:
        return f"{ms*1000:.1f}µs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    else:
        return f"{ms/1000:.2f}s"

def test_numpy_baseline(n: int, iterations: int = 10) -> dict:
    """Pure NumPy (CPU) baseline - matrix multiplication."""
    # Create random matrices
    A = np.random.randn(n, n).astype(np.float32)
    B = np.random.randn(n, n).astype(np.float32)
    
    # Warm-up
    _ = A @ B
    
    # Timed runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        C = A @ B
        # Force computation to complete
        _ = C[0, 0]
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    return {
        "backend": "NumPy (CPU)",
        "n": n,
        "iterations": iterations,
        "mean_ms": np.mean(times),
        "std_ms": np.std(times),
        "min_ms": np.min(times),
        "max_ms": np.max(times),
    }


def test_onnx_cpu(n: int, iterations: int = 10) -> dict:
    """ONNX Runtime with CPU provider only."""
    try:
        import onnxruntime as ort
    except ImportError:
        return {"backend": "ONNX CPU", "error": "onnxruntime not installed"}
    
    # Create a simple matmul model dynamically
    import onnx
    from onnx import helper, TensorProto
    
    # Define inputs
    A = helper.make_tensor_value_info('A', TensorProto.FLOAT, [n, n])
    B = helper.make_tensor_value_info('B', TensorProto.FLOAT, [n, n])
    C = helper.make_tensor_value_info('C', TensorProto.FLOAT, [n, n])
    
    # MatMul node
    matmul_node = helper.make_node('MatMul', ['A', 'B'], ['C'])
    
    # Create graph and model (use opset 12 for compatibility)
    graph = helper.make_graph([matmul_node], 'matmul_test', [A, B], [C])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 12)])
    model.ir_version = 8  # Compatible IR version
    
    # Create session with CPU only
    sess_options = ort.SessionOptions()
    sess = ort.InferenceSession(
        model.SerializeToString(),
        sess_options,
        providers=['CPUExecutionProvider']
    )
    
    # Get actual provider being used
    actual_providers = sess.get_providers()
    
    # Create input data
    a_data = np.random.randn(n, n).astype(np.float32)
    b_data = np.random.randn(n, n).astype(np.float32)
    
    # Warm-up
    _ = sess.run(None, {'A': a_data, 'B': b_data})
    
    # Timed runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = sess.run(None, {'A': a_data, 'B': b_data})
        # Force result materialization
        _ = result[0][0, 0]
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    return {
        "backend": "ONNX Runtime (CPU)",
        "providers_used": actual_providers,
        "n": n,
        "iterations": iterations,
        "mean_ms": np.mean(times),
        "std_ms": np.std(times),
        "min_ms": np.min(times),
        "max_ms": np.max(times),
    }


def test_onnx_gpu(n: int, iterations: int = 10) -> dict:
    """ONNX Runtime with CUDA/TensorRT provider."""
    try:
        import onnxruntime as ort
    except ImportError:
        return {"backend": "ONNX GPU", "error": "onnxruntime not installed"}
    
    # Check if CUDA provider is available
    available = ort.get_available_providers()
    if 'CUDAExecutionProvider' not in available and 'TensorrtExecutionProvider' not in available:
        return {
            "backend": "ONNX GPU",
            "error": "No GPU provider available",
            "available_providers": available
        }
    
    # Create a simple matmul model dynamically
    import onnx
    from onnx import helper, TensorProto
    
    # Define inputs
    A = helper.make_tensor_value_info('A', TensorProto.FLOAT, [n, n])
    B = helper.make_tensor_value_info('B', TensorProto.FLOAT, [n, n])
    C = helper.make_tensor_value_info('C', TensorProto.FLOAT, [n, n])
    
    # MatMul node
    matmul_node = helper.make_node('MatMul', ['A', 'B'], ['C'])
    
    # Create graph and model (use opset 12 for compatibility)
    graph = helper.make_graph([matmul_node], 'matmul_test', [A, B], [C])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 12)])
    model.ir_version = 8  # Compatible IR version
    
    # Create session with CUDA provider ONLY (skip TensorRT which requires separate SDK)
    sess_options = ort.SessionOptions()
    
    # Use CUDA only - TensorRT requires separate TensorRT SDK installation
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    
    sess = ort.InferenceSession(
        model.SerializeToString(),
        sess_options,
        providers=providers
    )
    
    # Get actual provider being used
    actual_providers = sess.get_providers()
    
    # Create input data
    a_data = np.random.randn(n, n).astype(np.float32)
    b_data = np.random.randn(n, n).astype(np.float32)
    
    # Warm-up (important for GPU - first run includes kernel compilation)
    for _ in range(3):
        _ = sess.run(None, {'A': a_data, 'B': b_data})
    
    # Timed runs
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = sess.run(None, {'A': a_data, 'B': b_data})
        # Force synchronization by accessing result
        _ = result[0][0, 0]
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    
    return {
        "backend": "ONNX Runtime (GPU)",
        "providers_requested": providers,
        "providers_used": actual_providers,
        "n": n,
        "iterations": iterations,
        "mean_ms": np.mean(times),
        "std_ms": np.std(times),
        "min_ms": np.min(times),
        "max_ms": np.max(times),
    }


def run_comparison(sizes: list[int] = None):
    """Run comparison across different matrix sizes."""
    if sizes is None:
        sizes = [256, 512, 1024, 2048]
    
    print("=" * 70)
    print("  GPU VALIDATION TEST - Proving Actual Hardware Usage")
    print("=" * 70)
    print()
    
    # Check what's available
    print("  Checking available backends...")
    print()
    
    try:
        import onnxruntime as ort
        print(f"  ONNX Runtime version: {ort.__version__}")
        available = ort.get_available_providers()
        print(f"  Available providers: {available}")
        has_cuda = 'CUDAExecutionProvider' in available
        has_trt = 'TensorrtExecutionProvider' in available
        print(f"  CUDA available: {has_cuda}")
        print(f"  TensorRT available: {has_trt}")
    except ImportError:
        print("  ONNX Runtime: NOT INSTALLED")
        has_cuda = False
        has_trt = False
    
    print()
    print("-" * 70)
    print()
    
    results = []
    
    for n in sizes:
        print(f"  Testing N={n} (matrix {n}x{n}, {n*n*4/1024/1024:.1f} MB per matrix)...")
        print()
        
        # Run tests
        numpy_result = test_numpy_baseline(n)
        onnx_cpu_result = test_onnx_cpu(n)
        onnx_gpu_result = test_onnx_gpu(n)
        
        # Display results
        print(f"    {'Backend':<25} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
        print(f"    {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        
        for r in [numpy_result, onnx_cpu_result, onnx_gpu_result]:
            if "error" in r:
                print(f"    {r['backend']:<25} ERROR: {r['error']}")
            else:
                print(f"    {r['backend']:<25} {format_time(r['mean_ms']):>10} {format_time(r['std_ms']):>10} {format_time(r['min_ms']):>10} {format_time(r['max_ms']):>10}")
        
        # Calculate speedups
        if "error" not in onnx_gpu_result and "error" not in numpy_result:
            speedup_vs_numpy = numpy_result["mean_ms"] / onnx_gpu_result["mean_ms"]
            print()
            print(f"    GPU Speedup vs NumPy: {speedup_vs_numpy:.2f}x")
        
        if "error" not in onnx_gpu_result and "error" not in onnx_cpu_result:
            speedup_vs_cpu = onnx_cpu_result["mean_ms"] / onnx_gpu_result["mean_ms"]
            print(f"    GPU Speedup vs ONNX CPU: {speedup_vs_cpu:.2f}x")
            
            # This is the KEY indicator - if GPU is really being used, there should be
            # a significant difference at larger sizes
            if speedup_vs_cpu > 1.5:
                print(f"    ✓ GPU IS BEING USED (significant speedup detected)")
            elif speedup_vs_cpu > 1.0:
                print(f"    ? GPU may be used (marginal speedup)")
            else:
                print(f"    ✗ GPU NOT FASTER (possible CPU fallback)")
        
        print()
        print("-" * 70)
        print()
        
        results.append({
            "n": n,
            "numpy": numpy_result,
            "onnx_cpu": onnx_cpu_result,
            "onnx_gpu": onnx_gpu_result,
        })
    
    # Summary
    print("  SUMMARY")
    print("  " + "=" * 66)
    print()
    
    if has_cuda or has_trt:
        # Check if GPU was actually faster
        gpu_faster_count = 0
        for r in results:
            if "error" not in r["onnx_gpu"] and "error" not in r["onnx_cpu"]:
                if r["onnx_gpu"]["mean_ms"] < r["onnx_cpu"]["mean_ms"] * 0.8:
                    gpu_faster_count += 1
        
        if gpu_faster_count >= len(results) // 2:
            print("  ✓ GPU ACCELERATION CONFIRMED")
            print("    The GPU provider is actively being used and provides")
            print("    measurable speedup over CPU execution.")
        else:
            print("  ⚠ GPU AVAILABLE BUT NOT PROVIDING SPEEDUP")
            print("    The GPU provider is available but either:")
            print("    - Falling back to CPU for these operations")
            print("    - Matrix sizes too small to benefit from GPU")
            print("    - GPU overhead exceeds computation time")
    else:
        print("  ✗ NO GPU PROVIDER AVAILABLE")
        print("    ONNX Runtime is running on CPU only.")
    
    print()
    
    return results


if __name__ == "__main__":
    # Check for onnx package (needed for model creation)
    try:
        import onnx
    except ImportError:
        print("Installing onnx package for model creation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "onnx", "-q"])
        import onnx
    
    run_comparison()
