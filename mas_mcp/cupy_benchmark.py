#!/usr/bin/env python3
"""RTX 4090 Laptop GPU - Full CuPy Benchmark Suite"""

import os
os.add_dll_directory(r'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin')

import numpy as np
import cupy as cp
import time

def main():
    print('=' * 60)
    print('RTX 4090 LAPTOP GPU - FULL BENCHMARK SUITE')
    print('=' * 60)

    # Get device info
    device = cp.cuda.Device(0)
    props = cp.cuda.runtime.getDeviceProperties(0)
    mem = device.mem_info
    gpu_name = props["name"].decode()
    print(f'GPU: {gpu_name}')
    print(f'Memory: {mem[1]/(1024**3):.1f} GB total, {mem[0]/(1024**3):.1f} GB free')
    print(f'Compute Capability: {props["major"]}.{props["minor"]}')
    print()

    # Benchmark 1: GEMM (FP32)
    print('--- GEMM FP32 (4096x4096) ---')
    n = 4096
    a = cp.random.rand(n, n, dtype=cp.float32)
    b = cp.random.rand(n, n, dtype=cp.float32)

    # Warmup
    c = cp.matmul(a, b)
    cp.cuda.Stream.null.synchronize()

    # Timed
    start = time.perf_counter()
    for _ in range(10):
        c = cp.matmul(a, b)
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 10
    flops = 2 * n**3 / elapsed
    print(f'Time: {elapsed*1000:.2f} ms')
    print(f'TFLOPS: {flops/1e12:.2f}')
    del a, b, c
    cp.get_default_memory_pool().free_all_blocks()
    print()

    # Benchmark 2: GEMM (FP16)
    print('--- GEMM FP16 (8192x8192) ---')
    n = 8192
    a16 = cp.random.rand(n, n, dtype=cp.float32).astype(cp.float16)
    b16 = cp.random.rand(n, n, dtype=cp.float32).astype(cp.float16)

    c16 = cp.matmul(a16, b16)
    cp.cuda.Stream.null.synchronize()

    start = time.perf_counter()
    for _ in range(10):
        c16 = cp.matmul(a16, b16)
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 10
    flops = 2 * n**3 / elapsed
    print(f'Time: {elapsed*1000:.2f} ms')
    print(f'TFLOPS: {flops/1e12:.2f}')
    del a16, b16, c16
    cp.get_default_memory_pool().free_all_blocks()
    print()

    # Benchmark 3: Memory bandwidth
    print('--- Memory Bandwidth (1 GB copy) ---')
    size_gb = 1
    arr = cp.random.rand(int(size_gb * 1024**3 / 4), dtype=cp.float32)
    cp.cuda.Stream.null.synchronize()

    start = time.perf_counter()
    for _ in range(10):
        arr2 = arr.copy()
        del arr2
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 10
    bandwidth = size_gb / elapsed
    print(f'Bandwidth: {bandwidth:.1f} GB/s')
    del arr
    cp.get_default_memory_pool().free_all_blocks()
    print()

    # Benchmark 4: Vector ops (element-wise)
    print('--- Element-wise Ops (100M elements) ---')
    n = 100_000_000
    x = cp.random.rand(n, dtype=cp.float32)
    y = cp.random.rand(n, dtype=cp.float32)

    z = x + y * x
    cp.cuda.Stream.null.synchronize()

    start = time.perf_counter()
    for _ in range(100):
        z = x + y * x
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 100
    ops = 2 * n  # 1 add + 1 mul per element
    print(f'Time: {elapsed*1000:.3f} ms')
    print(f'GFLOPS: {ops/elapsed/1e9:.1f}')
    del x, y, z
    cp.get_default_memory_pool().free_all_blocks()
    print()

    # Benchmark 5: FFT (signal processing)
    print('--- FFT 1D (16M complex elements) ---')
    n = 16 * 1024 * 1024
    signal = cp.random.rand(n, dtype=cp.float32) + 1j * cp.random.rand(n, dtype=cp.float32)
    signal = signal.astype(cp.complex64)

    fft_result = cp.fft.fft(signal)
    cp.cuda.Stream.null.synchronize()

    start = time.perf_counter()
    for _ in range(10):
        fft_result = cp.fft.fft(signal)
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 10
    print(f'Time: {elapsed*1000:.2f} ms')
    # FFT is O(n log n) - 5n log2(n) complex ops estimated
    fft_ops = 5 * n * np.log2(n)
    print(f'GFLOPS: {fft_ops/elapsed/1e9:.1f}')
    del signal, fft_result
    cp.get_default_memory_pool().free_all_blocks()
    print()

    # Benchmark 6: Reduction (sum)
    print('--- Reduction Sum (500M elements) ---')
    n = 500_000_000
    arr = cp.random.rand(n, dtype=cp.float32)
    
    total = cp.sum(arr)
    cp.cuda.Stream.null.synchronize()

    start = time.perf_counter()
    for _ in range(20):
        total = cp.sum(arr)
    cp.cuda.Stream.null.synchronize()
    elapsed = (time.perf_counter() - start) / 20
    # Bandwidth-bound: reading n elements
    bandwidth = (n * 4) / elapsed / 1e9  # GB/s
    print(f'Time: {elapsed*1000:.2f} ms')
    print(f'Effective Bandwidth: {bandwidth:.1f} GB/s')
    del arr
    cp.get_default_memory_pool().free_all_blocks()
    print()

    print('=' * 60)
    print('BENCHMARK COMPLETE')
    print('=' * 60)

if __name__ == '__main__':
    main()
