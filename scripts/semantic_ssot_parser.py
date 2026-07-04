#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: semantic_ssot_parser.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
SSOT Semantic Decryption Prototype (Iterative Benchmark)
Extracts substrate concepts from SSOT.md using the precise grammar patterns
defined in .chthonic/grammar/patterns.json and maps them to the Triple-Abstraction
ontology in .chthonic/ankh_seeds.yaml.

@SID:           TOOL_SEMANTIC_SSOT_PARSER_V1
@Shabti:        CLI Script
@Purpose:       SSOT Semantic Decryption Prototype (Iterative Benchmark)
"""

import sys
import re
import json
import yaml
from pathlib import Path
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def load_ontology(seed_path: Path):
    if not seed_path.exists():
        return {}
    with open(seed_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    ontology_map = {}
    
    # Flatten the Andean and Egyptologic seeds into a searchable map
    for category in ['andean_bce', 'egyptologic_bce']:
        for seed in data.get(category, []):
            label = seed['label']
            terms = [t.lower() for t in seed.get('resonance_terms', [])]
            ontology_map[label] = {
                'principle': seed['principle'],
                'terms': terms,
                'category': category
            }
    return ontology_map

def extract_substrate_patterns(ssot_path: Path):
    if not ssot_path.exists():
        print(f"Error: {ssot_path} does not exist.")
        sys.exit(1)

    # Patterns derived from patterns.json
    # Matches: **(`FA⁵`)** or **(`Codex`/`SSOT`)**
    bold_parened_id = re.compile(r'\*\*\(\`([^\`\)]+)\`\)\*\*')
    
    # Matches: `The-Savant` (bare ticked titlecase/id)
    ticked_id = re.compile(r'(?<!\()\b\`([A-Za-z0-9\-\^]+)\`\b(?!\))')
    
    # Matches: (The-Savant) or (Phases α, β, γ)
    parened_phrase = re.compile(r'\(([A-Z][a-zA-Z0-9\-\s\,\α\β\γ]+)\)')
    
    extracted_concepts = defaultdict(int)
    
    with open(ssot_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip code blocks for this pass to avoid false positives in examples
            if line.startswith('```'):
                continue
                
            # Find bold parened ids (the highest weight architectural load-bearers)
            for match in bold_parened_id.finditer(line):
                raw_concept = match.group(1)
                # Split alias chains like Codex/SSOT/ASC
                aliases = [a.strip('`') for a in raw_concept.split('`/`')]
                for alias in aliases:
                    extracted_concepts[alias] += 2 # Heavy weight
            
            # Find bare ticked ids
            for match in ticked_id.finditer(line):
                concept = match.group(1)
                extracted_concepts[concept] += 1
                
    return extracted_concepts

def map_resonance(extracted_concepts, ontology_map):
    resonance_ledger = defaultdict(list)
    
    for concept, freq in extracted_concepts.items():
        concept_lower = concept.lower()
        matched = False
        
        # Simple exact substring resonance mapping
        for label, data in ontology_map.items():
            if concept_lower in data['terms'] or any(t in concept_lower for t in data['terms']):
                resonance_ledger[label].append({
                    'concept': concept,
                    'frequency': freq
                })
                matched = True
        
        if not matched and freq > 5:
            # High frequency unmapped concepts (potential new archetypes)
            resonance_ledger['UNMAPPED_HIGH_FREQ'].append({
                'concept': concept,
                'frequency': freq
            })
            
    return resonance_ledger

if __name__ == "__main__":
    ssot_file = Path(".chthonic/SSOT.md")
    seeds_file = Path(".chthonic/ankh_seeds.yaml")
    
    print("Initializing Triple-Abstraction Semantic Decryption...")
    
    try:
        ontology = load_ontology(seeds_file)
        print(f"Loaded {len(ontology)} ontological seeds.")
        
        concepts = extract_substrate_patterns(ssot_file)
        print(f"Extracted {len(concepts)} unique structural patterns from the substrate.")
        
        resonance = map_resonance(concepts, ontology)
        
        print("\n--- RESONANCE MAPPING (The Triple Abstraction) ---\n")
        for seed_label, matches in resonance.items():
            if seed_label == 'UNMAPPED_HIGH_FREQ':
                continue
            print(f"🌀 {seed_label} (Principle: {ontology[seed_label]['principle'][:60]}...)")
            sorted_matches = sorted(matches, key=lambda x: x['frequency'], reverse=True)
            for match in sorted_matches[:5]:
                print(f"   ↳ {match['concept']} (Freq: {match['frequency']})")
            print()
            
        if 'UNMAPPED_HIGH_FREQ' in resonance:
            print("\n⚠️ ORPHANED HIGH-FREQUENCY MANIFESTATIONS (Needs Ontological Grounding):")
            sorted_orphans = sorted(resonance['UNMAPPED_HIGH_FREQ'], key=lambda x: x['frequency'], reverse=True)
            for match in sorted_orphans[:10]:
                print(f"   ↳ {match['concept']} (Freq: {match['frequency']})")
                
    except Exception as e:
        print(f"Error during semantic parsing: {e}")
        sys.exit(1)
