"""Topology graph summary helper.

Reads a topology graph JSON file and prints a compact summary:
- node and edge counts
- top nodes by degree centrality
- DAG/cycle check
"""

import json
import networkx as nx
from pathlib import Path

def reveal_sacred_geometry(graph_path='topology_graph.json'):
    print('Loading topology graph...')
    if not Path(graph_path).exists():
        print('Topology graph not found.')
        return

    try:
        data = json.loads(Path(graph_path).read_text(encoding='utf-8'))
        G = nx.DiGraph()
        # Ingest nodes
        for node in data.get('nodes', []):
            G.add_node(node['id'], **node)
        
        # Ingest edges
        for edge in data.get('edges', []):
            G.add_edge(edge['source'], edge['target'], **edge)
        
        # Calculate degree centrality
        density = nx.degree_centrality(G)
        core_stars = sorted(density.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print(f'Nodes: {len(G.nodes)} | Edges: {len(G.edges)}')
        print('Top nodes by degree centrality:')
        for star, score in core_stars:
            print(f'  - {star} (centrality: {score:.4f})')
            
        if nx.is_directed_acyclic_graph(G):
            print('\nGraph is acyclic (DAG).')
        else:
            print('\nGraph has cycles (not a DAG).')

    except Exception as e:
        print(f'Failed to read topology graph: {e}')

if __name__ == '__main__':
    reveal_sacred_geometry()
