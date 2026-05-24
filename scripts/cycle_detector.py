#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: cycle_detector.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Cycle Detection - Identify Circular Dependencies in Topology Graph
Uses networkx to analyze graph structure

@SID:           TOOL_CYCLE_DETECTOR_V1
@Shabti:        CLI Script
@Purpose:       Cycle Detection - Identify Circular Dependencies in Topology Graph
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import json
import networkx as nx
from pathlib import Path
import sys

def detect_cycles(graph_path='topology_graph.json'):
    print(f'🔍 Analyzing topology for circular dependencies...')
    if not Path(graph_path).exists():
        print('❌ Topology graph not found.')
        return

    try:
        data = json.loads(Path(graph_path).read_text(encoding='utf-8'))
        G = nx.DiGraph()
        for node in data.get('nodes', []):
            G.add_node(node['id'], **node)
        for edge in data.get('edges', []):
            G.add_edge(edge['source'], edge['target'], **edge)

        cycles = list(nx.simple_cycles(G))
        if cycles:
            print(f'⚠️  CRITICAL: {len(cycles)} Circular Dependencies Detected!')
            # Filter for cycles involving more than 2 nodes for brevity in logs
            complex_cycles = [c for c in cycles if len(c) > 2]
            print(f'   Complex Cycles (>2 nodes): {len(complex_cycles)}')
            # Output first 3 for review
            for i, c in enumerate(cycles[:3]):
                print(f'   Cycle {i+1}: {c}')
            sys.exit(1) # Return failure code to trigger immune response
        else:
            print('✅ Axiomatic Purity Confirmed: No Circular Dependencies.')
            sys.exit(0)
    except Exception as e:
        print(f'❌ Cycle Detection Failed: {e}')
        sys.exit(1)

if __name__ == '__main__':
    detect_cycles()
