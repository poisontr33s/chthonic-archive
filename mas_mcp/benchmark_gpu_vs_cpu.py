#!/usr/bin/env python3
"""Benchmark GPU vs CPU scoring with warmup."""

import sys
sys.path.insert(0, '.')

import time
import numpy as np
from gpu_scores import gpu_batch_score, cpu_batch_score, gpu_available

def benchmark(batch_sizes=[100, 500, 1000, 5000, 10000, 50000]):
    print('=' * 70)
    print('GPU vs CPU SCORING BENCHMARK (with warmup)')
    print('=' * 70)
    print(f'GPU available: {gpu_available()}')
    print()
    
    dim = 256
    n_ref = 1000
    seed = 42
    
    rng = np.random.default_rng(seed)
    reference = rng.random((n_ref, dim)).astype(np.float32)
    
    # Warmup GPU (JIT compile + memory pool)
    print('Warming up GPU...')
    warmup = rng.random((1000, dim)).astype(np.float32)
    for _ in range(3):
        _ = gpu_batch_score(warmup, reference, None, seed)
    print('Warmup complete.')
    print()
    
    print(f'{"Batch":>10} {"CPU (ms)":>12} {"GPU (ms)":>12} {"Speedup":>10}')
    print('-' * 46)
    
    results = []
    for n in batch_sizes:
        vectors = rng.random((n, dim)).astype(np.float32)
        features = rng.random((n, 6)).astype(np.float32)
        
        # Time CPU
        start = time.perf_counter()
        cpu_result = cpu_batch_score(vectors, reference, features, seed)
        cpu_ms = (time.perf_counter() - start) * 1000
        
        # Time GPU (using internal timer for fair comparison)
        gpu_result = gpu_batch_score(vectors, reference, features, seed)
        gpu_ms = gpu_result.compute_time_ms
        
        speedup = cpu_ms / gpu_ms
        results.append((n, cpu_ms, gpu_ms, speedup))
        print(f'{n:>10} {cpu_ms:>12.2f} {gpu_ms:>12.2f} {speedup:>10.2f}x')
    
    print()
    print('Summary:')
    for n, cpu_ms, gpu_ms, speedup in results:
        if speedup > 1:
            print(f'  Batch {n:>6}: GPU {speedup:.1f}x FASTER')
        else:
            print(f'  Batch {n:>6}: CPU {1/speedup:.1f}x faster (GPU overhead)')
    
    print()
    # Find crossover point
    for i, (n, cpu_ms, gpu_ms, speedup) in enumerate(results):
        if speedup >= 1:
            print(f'GPU crossover point: batch size ~{n} (first where GPU wins)')
            break
    else:
        print('GPU never crosses CPU performance in tested range')

if __name__ == '__main__':
    benchmark()
