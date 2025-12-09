#!/usr/bin/env python3
"""Test MAS-MCP scanning on M-P-W Codex and GPU integration."""

import sys
from pathlib import Path

sys.path.insert(0, '.')
from server import mas_scan, mas_gpu_status, mas_gpu_score, PROJECT_ROOT

# Debug paths
mpw_path = PROJECT_ROOT / "macro-prompt-world"
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"M-P-W path: {mpw_path}")
print(f"Exists: {mpw_path.exists()}")
if mpw_path.exists():
    print(f"Files: {list(mpw_path.glob('*'))}")

# Scan the M-P-W Codex using relative path from PROJECT_ROOT
result = mas_scan('macro-prompt-world')

print()
print('=== M-P-W Codex Scan Results ===')
print(f'Files scanned: {result.get("files_scanned", 0)}')
print(f'Total signals: {result.get("total_signals", 0)}')
print()

print('Entities found:')
entities = result.get('entities', {})
for name in list(entities.keys())[:15]:
    info = entities[name]
    print(f'  - {name}: {info.get("occurrences", 0)} occurrences')

print()
print('Signal breakdown by type:')
for signal_type, count in result.get('signal_counts', {}).items():
    print(f'  {signal_type}: {count}')

# GPU Tests
print()
print('=' * 60)
print('=== GPU INFRASTRUCTURE TEST ===')
print('=' * 60)

# GPU Status
print()
print('GPU Status:')
status = mas_gpu_status()
print(f'  Backend: {status.get("backend")}')
print(f'  Device: {status.get("device")}')
print(f'  VRAM: {status.get("total_memory_gb")}GB')

# Score M-P-W entities
print()
print('Scoring M-P-W Entities via GPU:')

entities_to_score = [
    ("The Decorator", 0.464, 0.5, "K"),
    ("Orackla Nocticula", 0.491, 1.0, "J"),
    ("Madam Umeko Ketsuraku", 0.533, 1.0, "F"),
    ("Dr. Lysandra Thorne", 0.58, 1.0, "E"),
    ("Claudine Sin'claire", 0.563, 1.0, "I"),
]

for name, whr, tier, cup in entities_to_score:
    score = mas_gpu_score(name, whr=whr, tier=tier, cup=cup)
    overall = score.get("overall_score", "N/A")
    if isinstance(overall, (int, float)):
        overall_str = f'{overall:.4f}'
    else:
        overall_str = str(overall)
    print(f'  {name}:')
    print(f'    WHR: {whr}, Tier: {tier}, Cup: {cup}')
    print(f'    Overall Score: {overall_str}')
    print(f'    Backend: {score.get("backend")}')
