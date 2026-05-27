#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import unittest
from pathlib import Path
import sys
import os

# Add parent directory to path to import mas_mcp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.state import PatternRegistry, MemoryBank
from logic.scanner import quick_entity_extract

class TestLogicQualia(unittest.TestCase):
    def setUp(self):
        self.registry = PatternRegistry()
        self.temp_memory = Path("test_memory.json")
        self.memory = MemoryBank(self.temp_memory)

    def tearDown(self):
        if self.temp_memory.exists():
            os.remove(self.temp_memory)

    def test_pattern_registry_dna(self):
        """Verify the 'DNA' patterns are present and compile-able."""
        patterns = self.registry.get_all_patterns()
        
        # Check for core entities
        entity_names = [p["name"] for p in patterns["ENTITY"]]
        self.assertIn("The Decorator", entity_names)
        self.assertIn("Orackla Nocticula", entity_names)
        self.assertIn("Claudine Sin'claire", entity_names)
        
        # Check for metrics
        metric_names = [p["name"] for p in patterns["METRIC"]]
        self.assertIn("WHR", metric_names)
        self.assertIn("TIER", metric_names)

    def test_quick_entity_extract(self):
        """Verify the extraction logic still works with simulated content."""
        mock_content = """
        ### Profile - The Decorator
        Physique:
        **Measurements**: B120/W55/H112
        WHR: 0.464
        Tier: 0.5
        K-cup
        """
        
        result = quick_entity_extract(mock_content, "The Decorator")
        self.assertIsNotNone(result)
        self.assertEqual(result["whr"], 0.464)
        self.assertEqual(result["tier"], 0.5)
        self.assertEqual(result["cup"], "K")

    def test_memory_bank_persistence(self):
        """Verify the MemoryBank holds 'Truths' correctly."""
        truth = {"whr": 0.464, "tier": 0.5, "cup": "K"}
        self.memory.record_truth("The Decorator", truth)
        
        # Reload to verify persistence
        new_memory = MemoryBank(self.temp_memory)
        stored_truth = new_memory.get_known_truth("The Decorator")
        self.assertEqual(stored_truth["metrics"]["whr"], 0.464)

if __name__ == "__main__":
    unittest.main()
