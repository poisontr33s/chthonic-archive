#!/usr/bin/env python3
"""
GPU ACCELERATION BENCHMARK
TensorRT vs CUDA vs CPU execution providers

Tests inference latency on a real model to demonstrate
the value of our tri-marathonian GPU stack efforts.
"""

import sys
import time
import numpy as np
import onnxruntime as ort
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════════
# BENCHMARK CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

WARMUP_RUNS = 5
BENCHMARK_RUNS = 50

def create_dummy_model():
    """Create a simple ONNX model for benchmarking if no model exists."""
    try:
        import onnx
        from onnx import helper, TensorProto
        
        # Simple MatMul + ReLU model (simulates transformer-like workload)
        X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [1, 512, 768])
        Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [1, 512, 768])
        
        # Weight tensor - use raw_data instead of vals to avoid binary dump
        weight_data = np.random.randn(768, 768).astype(np.float32)
        W = helper.make_tensor('W', TensorProto.FLOAT, [768, 768], weight_data.flatten().tolist())
        
        matmul = helper.make_node('MatMul', ['X', 'W'], ['matmul_out'])
        relu = helper.make_node('Relu', ['matmul_out'], ['Y'])
        
        graph = helper.make_graph([matmul, relu], 'benchmark_model', [X], [Y], [W])
        model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 17)])
        
        # Downgrade IR version to 8 for compatibility (ONNX Runtime supports up to 12)
        model.ir_version = 8
        
        model_path = Path(__file__).parent / 'benchmark_model.onnx'
        onnx.save(model, str(model_path))
        return model_path
    except ImportError:
        return None

def benchmark_provider(model_path: Path, provider: str, input_shape: tuple) -> dict:
    """Benchmark a single execution provider."""
    results = {
        'provider': provider,
        'status': 'failed',
        'latency_ms': None,
        'throughput': None,
        'error': None
    }
    
    try:
        # Create session with specific provider
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        session = ort.InferenceSession(
            str(model_path),
            sess_options,
            providers=[provider]
        )
        
        # Verify the provider is actually being used
        active_providers = session.get_providers()
        if provider not in active_providers:
            results['error'] = f"Provider {provider} not active, using {active_providers}"
            return results
        
        # Create input
        input_name = session.get_inputs()[0].name
        input_data = np.random.randn(*input_shape).astype(np.float32)
        
        # Warmup
        for _ in range(WARMUP_RUNS):
            session.run(None, {input_name: input_data})
        
        # Benchmark
        latencies = []
        for _ in range(BENCHMARK_RUNS):
            start = time.perf_counter()
            session.run(None, {input_name: input_data})
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms
        
        results['status'] = 'success'
        results['latency_ms'] = {
            'mean': np.mean(latencies),
            'std': np.std(latencies),
            'min': np.min(latencies),
            'max': np.max(latencies),
            'p50': np.percentile(latencies, 50),
            'p95': np.percentile(latencies, 95),
            'p99': np.percentile(latencies, 99),
        }
        results['throughput'] = 1000.0 / results['latency_ms']['mean']  # inferences/sec
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def print_results(results: list[dict]):
    """Pretty print benchmark results."""
    print("\n" + "═" * 70)
    print("🔥💀⚓ GPU ACCELERATION BENCHMARK RESULTS")
    print("═" * 70)
    
    # Find best performer for comparison
    successful = [r for r in results if r['status'] == 'success']
    if not successful:
        print("❌ No providers succeeded!")
        return
    
    baseline = min(successful, key=lambda x: x['latency_ms']['mean'])
    
    for r in results:
        provider = r['provider'].replace('ExecutionProvider', '')
        
        if r['status'] == 'success':
            lat = r['latency_ms']
            speedup = baseline['latency_ms']['mean'] / lat['mean'] if r != baseline else 1.0
            
            status = "🏆" if r == baseline else "  "
            print(f"\n{status} {provider}")
            print(f"   ├─ Mean:       {lat['mean']:>8.3f} ms")
            print(f"   ├─ Std:        {lat['std']:>8.3f} ms")
            print(f"   ├─ P50:        {lat['p50']:>8.3f} ms")
            print(f"   ├─ P95:        {lat['p95']:>8.3f} ms")
            print(f"   ├─ Throughput: {r['throughput']:>8.1f} inf/sec")
            if r != baseline:
                print(f"   └─ vs Best:    {speedup:>8.2f}x {'slower' if speedup < 1 else 'faster'}")
            else:
                print(f"   └─ 🏆 FASTEST")
        else:
            print(f"\n❌ {provider}")
            print(f"   └─ Error: {r['error']}")
    
    print("\n" + "═" * 70)
    
    # Summary
    if len(successful) >= 2:
        tensorrt = next((r for r in successful if 'Tensorrt' in r['provider']), None)
        cuda = next((r for r in successful if 'CUDA' in r['provider']), None)
        cpu = next((r for r in successful if 'CPU' in r['provider']), None)
        
        print("\n📊 SPEEDUP SUMMARY:")
        if tensorrt and cuda:
            speedup = cuda['latency_ms']['mean'] / tensorrt['latency_ms']['mean']
            print(f"   TensorRT vs CUDA: {speedup:.2f}x faster")
        if tensorrt and cpu:
            speedup = cpu['latency_ms']['mean'] / tensorrt['latency_ms']['mean']
            print(f"   TensorRT vs CPU:  {speedup:.2f}x faster")
        if cuda and cpu:
            speedup = cpu['latency_ms']['mean'] / cuda['latency_ms']['mean']
            print(f"   CUDA vs CPU:      {speedup:.2f}x faster")
    
    print("\n" + "═" * 70)

def main():
    print("🔥💀⚓ GPU ACCELERATION BENCHMARK")
    print("═" * 70)
    print(f"   ONNX Runtime: {ort.__version__}")
    print(f"   Available:    {ort.get_available_providers()}")
    print(f"   Warmup:       {WARMUP_RUNS} runs")
    print(f"   Benchmark:    {BENCHMARK_RUNS} runs")
    print("═" * 70)
    
    # Find or create model
    model_path = Path(__file__).parent / 'benchmark_model.onnx'
    if not model_path.exists():
        print("\n📦 Creating benchmark model...")
        model_path = create_dummy_model()
        if model_path is None:
            print("❌ Could not create model (onnx package not installed)")
            print("   Install with: uv add onnx")
            return
    
    print(f"\n📦 Model: {model_path}")
    
    # Input shape for our dummy model
    input_shape = (1, 512, 768)
    print(f"📐 Input shape: {input_shape}")
    
    # Providers to benchmark (in order of expected performance)
    providers = [
        'TensorrtExecutionProvider',
        'CUDAExecutionProvider', 
        'CPUExecutionProvider'
    ]
    
    # Filter to available providers
    available = ort.get_available_providers()
    providers = [p for p in providers if p in available]
    
    print(f"\n🏃 Benchmarking {len(providers)} providers...")
    
    results = []
    for provider in providers:
        print(f"\n   Testing {provider}...", end=" ", flush=True)
        result = benchmark_provider(model_path, provider, input_shape)
        if result['status'] == 'success':
            print(f"✅ {result['latency_ms']['mean']:.2f} ms")
        else:
            print(f"❌ {result['error'][:50]}...")
        results.append(result)
    
    print_results(results)

if __name__ == '__main__':
    main()
