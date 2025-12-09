#!/usr/bin/env python3
"""Quick test of MAS-MCP functionality."""

from server import mas_scan, mas_entity_deep, mas_discover_unknown, mas_validate_entity
import json

print("=" * 60)
print("🏛️ MAS-MCP FUNCTIONALITY TEST")
print("=" * 60)

# Test 1: Full scan
print("\n📡 TEST 1: Full Codebase Scan")
result = mas_scan()
print(f"   Files scanned: {result['scan_metadata']['files_scanned']}")
print(f"   Files skipped: {result['scan_metadata']['files_skipped']}")
print(f"   Total signals: {result['scan_metadata']['total_signals']}")
print(f"   Signal breakdown:")
for sig_type, count in result['signal_counts'].items():
    print(f"      {sig_type}: {count}")
print(f"   Known entities: {list(result['entities'].keys())[:8]}...")

# Test 2: Deep entity extraction
print("\n🔍 TEST 2: Deep Entity Extraction (The Decorator)")
deep = mas_entity_deep("The Decorator", context_lines=25)
print(f"   Mentions found: {deep['all_mentions']}")
print(f"   Files analyzed: {len(deep['files_analyzed'])}")
print(f"   Consolidated metrics: {deep['consolidated_metrics']}")

# Test 3: Validation
print("\n✓ TEST 3: Validation (The Decorator)")
val = mas_validate_entity("The Decorator", expected_whr=0.464, expected_tier=0.5, expected_cup="K")
print(f"   Matches: {val['matches']}")
print(f"   Mismatches: {val['mismatches']}")
print(f"   Missing: {val['missing']}")
print(f"   Score: {val['score']:.2%}")

# Test 4: Unknown discovery
print("\n🔮 TEST 4: Unknown Entity Discovery")
unknown = mas_discover_unknown()
print(f"   Potential unknown entities: {unknown['total_candidates']}")
if unknown['potential_entities']:
    print(f"   Top candidates:")
    for e in unknown['potential_entities'][:5]:
        print(f"      - {e['name']} ({e['mentions']} mentions)")

print("\n" + "=" * 60)
print("✅ MAS-MCP TESTS COMPLETE")
print("=" * 60)
