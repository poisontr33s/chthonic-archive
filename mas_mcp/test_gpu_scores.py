#!/usr/bin/env python3
"""Test MAS-MCP GPU scoring with validation."""

import sys
sys.path.insert(0, '.')

from gpu_scores import validate_gpu_cpu_parity, batch_score
import numpy as np

def main():
    print('=' * 60)
    print('MAS-MCP GPU SCORING VALIDATION')
    print('=' * 60)

    # Run validation with substantial batch
    report = validate_gpu_cpu_parity(n_vectors=5000, dim=512, n_reference=2000)
    print(f'Status: {report["status"]}')

    if 'timing' in report:
        print(f'CPU: {report["timing"]["cpu_ms"]:.2f} ms')
        print(f'GPU: {report["timing"]["gpu_ms"]:.2f} ms')
        print(f'Speedup: {report["timing"]["speedup"]:.1f}x')
        print()
        print('Differences (must be < tolerance):')
        for k, v in report['differences'].items():
            print(f'  {k}: {v:.2e}')
        print(f'Max difference: {report["max_difference"]:.2e} (tolerance: {report["tolerance"]})')
    else:
        print(f'Reason: {report.get("reason", "unknown")}')
    print()
    
    # Test actual batch scoring
    print('=' * 60)
    print('BATCH SCORING TEST')
    print('=' * 60)
    
    rng = np.random.default_rng(42)
    vectors = rng.random((1000, 256)).astype(np.float32)
    reference = rng.random((500, 256)).astype(np.float32)
    features = rng.random((1000, 6)).astype(np.float32)
    
    result = batch_score(vectors, reference, features, seed=42)
    
    print(f'Backend: {result.backend_used}')
    print(f'Batch size: {result.batch_size}')
    print(f'Compute time: {result.compute_time_ms:.2f} ms')
    print(f'Seed: {result.seed_used}')
    print()
    print('Score Statistics:')
    print(f'  Novelty:    mean={result.novelty.mean():.3f}, std={result.novelty.std():.3f}')
    print(f'  Redundancy: mean={result.redundancy.mean():.3f}, std={result.redundancy.std():.3f}')
    print(f'  Safety:     mean={result.safety.mean():.3f}, std={result.safety.std():.3f}')
    print(f'  Overall:    mean={result.overall.mean():.3f}, std={result.overall.std():.3f}')
    print()
    
    # Threshold test
    passing = result.meets_thresholds()
    grace = result.in_grace_window()
    print(f'Passing thresholds: {passing.sum()}/{len(passing)} ({100*passing.sum()/len(passing):.1f}%)')
    print(f'In grace window: {grace.sum()}/{len(grace)} ({100*grace.sum()/len(grace):.1f}%)')

if __name__ == '__main__':
    main()
