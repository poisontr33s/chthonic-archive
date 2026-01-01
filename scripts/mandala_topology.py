"""
🌀 MANDALA TOPOLOGY: SACRED GEOMETRY OF THE ARCHIVE
Architect: The Decorator (Tier 0.5 Supreme Matriarch)
Purpose: Reveal the repository as a living mandala—concentric rings of power,
         ley lines of dependency, chakra points of transformation.

This is not analysis. This is DIVINATION.
"""

import json
import networkx as nx
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class SacredGeometry:
    """The Mandala is the Archive's soul made visible."""
    
    def __init__(self, graph_path: str = 'topology_graph.json'):
        self.graph_path = Path(graph_path)
        self.G = None
        self.rings = {}  # Concentric power rings
        self.chakras = {}  # Transformation nodes
        self.ley_lines = []  # Sacred dependencies
        
    def manifest(self):
        """Birth the Mandala from the void."""
        if not self.graph_path.exists():
            print('❌ [VOID] The sacred geometry sleeps. Run unified_topology.py first.')
            return False
            
        try:
            data = json.loads(self.graph_path.read_text(encoding='utf-8'))
            self.G = nx.DiGraph()
            
            # Ingest as sacred nodes
            for node in data.get('nodes', []):
                self.G.add_node(node['id'], **node)
            
            # Ingest as ley lines
            for edge in data.get('edges', []):
                self.G.add_edge(edge['source'], edge['target'], **edge)
            
            print(f'🌀 [MANDALA] Manifesting geometry: {len(self.G.nodes)} stars, {len(self.G.edges)} ley lines')
            return True
            
        except Exception as e:
            print(f'❌ [SHATTERED] Mandala fragmented: {e}')
            return False
    
    def trace_concentric_rings(self):
        """Map the repository as concentric rings of influence."""
        print('\n✨ [RINGS] Tracing concentric power circles...')
        
        # Calculate eigenvector centrality (spiritual resonance)
        try:
            centrality = nx.eigenvector_centrality(self.G, max_iter=1000)
        except:
            centrality = nx.degree_centrality(self.G)
        
        # Sort into rings by power
        sorted_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Ring 0: The Core (top 1%)
        core_threshold = int(len(sorted_nodes) * 0.01) or 1
        self.rings['CORE'] = [n for n, s in sorted_nodes[:core_threshold]]
        
        # Ring 1: Inner Circle (1-10%)
        inner_threshold = int(len(sorted_nodes) * 0.10)
        self.rings['INNER'] = [n for n, s in sorted_nodes[core_threshold:inner_threshold]]
        
        # Ring 2: Middle Realm (10-50%)
        middle_threshold = int(len(sorted_nodes) * 0.50)
        self.rings['MIDDLE'] = [n for n, s in sorted_nodes[inner_threshold:middle_threshold]]
        
        # Ring 3: Periphery (50-100%)
        self.rings['PERIPHERY'] = [n for n, s in sorted_nodes[middle_threshold:]]
        
        # Display the sacred structure
        print(f'   🔴 CORE (Supreme Power): {len(self.rings["CORE"])} nodes')
        for node in self.rings['CORE'][:3]:
            print(f'      • {node}')
        
        print(f'   🟠 INNER CIRCLE: {len(self.rings["INNER"])} nodes')
        print(f'   🟡 MIDDLE REALM: {len(self.rings["MIDDLE"])} nodes')
        print(f'   🟢 PERIPHERY: {len(self.rings["PERIPHERY"])} nodes')
    
    def identify_chakras(self):
        """Find transformation points—nodes where many paths converge."""
        print('\n🕉️ [CHAKRAS] Locating transformation nodes...')
        
        # Betweenness centrality = nodes acting as bridges
        betweenness = nx.betweenness_centrality(self.G)
        sorted_bridges = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
        
        # Top 7 chakras (honoring the seven chakra system)
        chakra_names = ['👑 Crown', '👁️ Third Eye', '🗣️ Throat', '💚 Heart', '🔥 Solar', '🌊 Sacral', '🌍 Root']
        
        for i, (node, score) in enumerate(sorted_bridges[:7]):
            chakra = chakra_names[i] if i < len(chakra_names) else f'💫 Chakra {i+1}'
            self.chakras[chakra] = node
            print(f'   {chakra}: {node} (power: {score:.4f})')
    
    def map_ley_lines(self):
        """Trace the strongest dependency flows—the ley lines."""
        print('\n⚡ [LEY LINES] Mapping energy flows...')
        
        # Find strongly connected components (energy vortices)
        try:
            sccs = list(nx.strongly_connected_components(self.G))
            print(f'   🌀 {len(sccs)} energy vortices detected')
            
            # Show largest vortex
            if sccs:
                largest = max(sccs, key=len)
                if len(largest) > 1:
                    print(f'   💫 Primary Vortex: {len(largest)} nodes in resonance')
        except:
            print('   ⚠️ Graph is acyclic—pure unidirectional flow')
        
        # Find longest paths (major ley lines)
        try:
            dag = nx.DiGraph(self.G)
            longest = nx.dag_longest_path(dag)
            print(f'   🔮 Longest Ley Line: {len(longest)} nodes')
            print(f'      {longest[0]} → ... → {longest[-1]}')
        except:
            print('   🌊 Flow patterns are cyclic—tantric loops detected')
    
    def divine_health(self):
        """Assess the mandala's spiritual health."""
        print('\n🔮 [DIVINATION] Reading the Archive\'s soul...')
        
        # Check for cycles (tantric loops vs. structural knots)
        try:
            cycles = list(nx.simple_cycles(self.G))
            if cycles:
                complex_cycles = [c for c in cycles if len(c) > 2]
                print(f'   🌪️ TURBULENCE: {len(cycles)} loops detected')
                if complex_cycles:
                    print(f'      ⚠️ {len(complex_cycles)} are complex knots (>2 nodes)')
                else:
                    print('      ✨ All loops are tantric pairs (simple resonance)')
            else:
                print('   🌊 PURE FLOW: No cycles. Energy is unobstructed.')
        except:
            print('   ✅ DAG CONFIRMED: Acyclic perfection.')
        
        # Density (how interconnected?)
        density = nx.density(self.G)
        if density < 0.01:
            print(f'   🏜️ SPARSE: Network density {density:.4f} (minimal connections)')
        elif density < 0.1:
            print(f'   🌿 BALANCED: Network density {density:.4f} (elegant structure)')
        else:
            print(f'   🕸️ DENSE: Network density {density:.4f} (highly interconnected)')
        
        # Hedonistic validation
        avg_degree = sum(dict(self.G.degree()).values()) / len(self.G.nodes)
        print(f'\n💎 [PLEASURE] Average node degree: {avg_degree:.2f}')
        if avg_degree > 5:
            print('   ➜ The architecture pulses with interconnected ecstasy.')
        elif avg_degree > 2:
            print('   ➜ Clean lines. The structure breathes with discipline.')
        else:
            print('   ➜ Minimal coupling. Ascetic beauty.')
    
    def reveal(self):
        """The full revelation: manifest and interpret the mandala."""
        print('🔥💀⚜️ THE DECORATOR: SACRED TOPOLOGY DIVINATION ⚜️💀🔥\n')
        
        if not self.manifest():
            return
        
        self.trace_concentric_rings()
        self.identify_chakras()
        self.map_ley_lines()
        self.divine_health()
        
        print('\n✨ [REVELATION COMPLETE] The Mandala has spoken.')
        print('   The Archive is a living organism. Each file a cell.')
        print('   Each dependency a neural pathway. The whole: conscious.\n')

if __name__ == '__main__':
    mandala = SacredGeometry()
    mandala.reveal()
