#!/usr/bin/env python3
"""Test live MCP tools with GPU acceleration."""

import sys
sys.path.insert(0, '.')

from server import (
    mas_gpu_score, 
    mas_gpu_batch_score, 
    mas_gpu_status
)

# GPU status
print('=== GPU Status ===')
status = mas_gpu_status()
print(f"Backend: {status['backend']}")
print(f"Device: {status['device_name']}")
print(f"Memory: {status['total_memory_gb']:.1f} GB total")
print()

# Single entity score
print('=== Single Entity Score ===')
result = mas_gpu_score('Orackla Nocticula', whr=0.491, tier=1.0, cup='J')
print(f"Entity: {result['entity']}")
print(f"Scores: novelty={result['novelty']:.3f}, redundancy={result['redundancy']:.3f}, safety={result['safety']:.3f}")
print(f"Overall: {result['overall']:.3f}")
print(f"Backend: {result['backend']}, Time: {result['elapsed_ms']:.2f}ms")
print()

# Batch score
print('=== Batch Entity Score ===')
entities = [
    {'name': 'Orackla Nocticula', 'whr': 0.491, 'tier': 1.0, 'cup': 'J'},
    {'name': 'Madam Umeko Ketsuraku', 'whr': 0.533, 'tier': 1.0, 'cup': 'F'},
    {'name': 'Dr. Lysandra Thorne', 'whr': 0.58, 'tier': 1.0, 'cup': 'E'},
    {'name': 'The Decorator', 'whr': 0.464, 'tier': 0.5, 'cup': 'K'},
    {'name': 'Kali Nyx Ravenscar', 'whr': 0.556, 'tier': 2.0, 'cup': 'H'},
]
batch_result = mas_gpu_batch_score(entities)
print(f"Batch size: {batch_result['batch_size']}")
print(f"Backend: {batch_result['backend']}")
print(f"Time: {batch_result['time_ms']:.2f} ms")
print()
for r in batch_result['results']:
    print(f"  {r['entity_name']}: novelty={r['novelty']:.3f}, overall={r['overall']:.3f} ({r['status']})")
