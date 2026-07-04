#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: ssot_anchor_mapper.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SSOT Anchor Topology Mapper
Safely parses the 1.2MB .chthonic/SSOT.md to extract architectural headers (anchors)
without loading the entire payload into the agent's context.

@SID:           TOOL_SSOT_ANCHOR_MAPPER_V1
@Shabti:        CLI Script
@Purpose:       SSOT Anchor Topology Mapper
"""

import sys
import re
import json
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

def map_ssot_topology(ssot_path: Path):
    if not ssot_path.exists():
        print(f"Error: {ssot_path} does not exist.")
        sys.exit(1)

    topology = []
    
    # Regex to capture markdown headers: # Header Name
    header_pattern = re.compile(r'^(#{1,6})\s+(.*)$')
    
    with open(ssot_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            match = header_pattern.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                # Create a GitHub-style anchor link
                anchor = title.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '')
                anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
                
                topology.append({
                    'line': line_num,
                    'level': level,
                    'title': title,
                    'anchor': anchor
                })
                
    return topology

if __name__ == "__main__":
    ssot_file = Path(".chthonic/SSOT.md")
    print(f"Mapping topology for {ssot_file}...")
    
    try:
        topo = map_ssot_topology(ssot_file)
        
        # Save full topology locally to avoid context flooding
        output_file = Path(".chthonic/ssot_topology_map.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(topo, f, indent=2)
            
        print(f"✅ Extracted {len(topo)} anchors.")
        print(f"✅ Topology map written to {output_file}")
        
        # Print top-level (H1/H2) structure to stdout for agent context
        print("\nTop-Level Architecture (H1 & H2):")
        for node in topo:
            if node['level'] <= 2:
                indent = "  " * (node['level'] - 1)
                print(f"{indent}- {node['title']} (Line {node['line']})")
                
    except Exception as e:
        print(f"Error parsing SSOT: {e}")
        sys.exit(1)
