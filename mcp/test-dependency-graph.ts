/**
 * Test suite for query_dependency_graph tool
 * 
 * Run with: bun run test-dependency-graph.ts
 */

import { queryDependencyGraph } from "./tools/queryDependencyGraph.ts";

async function runTests() {
  console.log("=== Dependency Graph Tool Test Suite ===\n");

  const tests = [
    { name: "Stats query", query: "stats" },
    { name: "Spectral filter (GOLD)", query: "spectral GOLD" },
    { name: "Spectral filter (BLUE)", query: "spectral BLUE" },
    { name: "Node lookup (SSOT)", query: "node copilot-instructions.md" },
    { name: "Dependencies query", query: "dependencies BLACKSMITH" },
    { name: "Dependents query", query: "dependents README.md" },
    { name: "Invalid command", query: "invalid" },
  ];

  for (const test of tests) {
    console.log(`\n--- Test: ${test.name} ---`);
    console.log(`Query: "${test.query}"`);
    
    try {
      const result = await queryDependencyGraph(test.query);
      const parsed = JSON.parse(result);
      
      if (parsed.error) {
        console.log("❌ Error:", parsed.error);
        if (parsed.supported_commands) {
          console.log("Supported commands:", parsed.supported_commands);
        }
      } else {
        console.log("✅ Success");
        
        // Show key result fields
        if (parsed.total_nodes !== undefined) {
          console.log(`   Nodes: ${parsed.total_nodes}`);
          console.log(`   Hyperedges: ${parsed.total_hyperedges}`);
          console.log(`   Spectral distribution:`, parsed.spectral_distribution);
        } else if (parsed.frequency) {
          console.log(`   Frequency: ${parsed.frequency}`);
          console.log(`   Count: ${parsed.total_count} (showing ${parsed.nodes.length})`);
        } else if (parsed.node) {
          console.log(`   ID: ${parsed.node.id}`);
          console.log(`   Spectral: ${parsed.node.spectral_freq}`);
          console.log(`   Role: ${parsed.node.role}`);
          console.log(`   Essence: ${parsed.node.essence}`);
        } else if (parsed.dependencies !== undefined) {
          console.log(`   File: ${parsed.file}`);
          console.log(`   Dependencies: ${parsed.count}`);
          if (parsed.count > 0 && parsed.count <= 5) {
            console.log(`   First few:`, parsed.dependencies.slice(0, 3));
          }
        } else if (parsed.dependents !== undefined) {
          console.log(`   File: ${parsed.file}`);
          console.log(`   Dependents: ${parsed.count}`);
          if (parsed.count > 0 && parsed.count <= 5) {
            console.log(`   First few:`, parsed.dependents.slice(0, 3));
          }
        }
      }
    } catch (error) {
      console.log("💥 Exception:", error instanceof Error ? error.message : error);
    }
  }

  console.log("\n=== Test Suite Complete ===");
}

runTests();
