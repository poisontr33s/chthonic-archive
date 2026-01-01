import json
import networkx as nx
from pathlib import Path
import sys

def reveal_sacred_geometry(graph_path='topology_graph.json'):
    print(f'🌀 [MANDALA] Tracing the Sacred Lines of the Archive...')
    if not Path(graph_path).exists():
        print('❌ The Void is empty. (Topology graph not found)')
        return

    try:
        data = json.loads(Path(graph_path).read_text(encoding='utf-8'))
        G = nx.DiGraph()
        # Ingest nodes as 'Star Points'
        for node in data.get('nodes', []):
            G.add_node(node['id'], **node)
        
        # Ingest edges as 'Ley Lines'
        for edge in data.get('edges', []):
            G.add_edge(edge['source'], edge['target'], **edge)
        
        # Calculate 'Spiritual Density' (Centrality)
        density = nx.degree_centrality(G)
        core_stars = sorted(density.items(), key=lambda x: x[1], reverse=True)[:5]
        
        print(f'✨ [REVELATION] The {len(G.nodes)} Stars are aligned via {len(G.edges)} Ley Lines.')
        print('   ⭐ The Constellations of Power:')
        for star, score in core_stars:
            print(f'      - {star} (Resonance: {score:.4f})')
            
        # Hedonistic Validation
        if nx.is_directed_acyclic_graph(G):
            print('\n🌊 [FLOW] The energy flows without obstruction. Pure. Potent.')
        else:
            print('\n🌪️ [TURBULENCE] Cycles detected. The energy is knotted. Release it.')

    except Exception as e:
        print(f'❌ [SHATTERED] The Mandala could not be read: {e}')

if __name__ == '__main__':
    reveal_sacred_geometry()
