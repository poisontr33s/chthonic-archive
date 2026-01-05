/**
 * MCP Smoke Test Suite
 * 
 * Executes all 6 canonical workflows from docs/MCP_USER_WORKFLOWS.md
 * Saves structured results per minimal reporting format (appendix)
 * 
 * Usage: bun run mcp/smoke-suite.ts
 * Artifacts: artifacts/mcp_run_<workflow>_<timestamp>.json
 */

import { scanRepository } from "./tools/scanRepository";
import { validateSSOT } from "./tools/validateSSOT";
import { queryDependencyGraph } from "./tools/queryDependencyGraph";
import { writeFile, mkdir } from "fs/promises";
import { resolve } from "path";

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, "-");
const ARTIFACTS_DIR = resolve(import.meta.dir, "..", "artifacts");

// Tool versions from git (update manually or parse from git log)
const TOOL_VERSIONS = {
  server_commit: "5c666b2",
  bootstrap_spec: "1752952",
  workflows_doc: "622e57f",
};

interface WorkflowResult {
  run_id: string;
  workflow: string;
  inputs: Record<string, unknown>;
  outputs: unknown;
  elapsed_ms: number;
  tool_versions: typeof TOOL_VERSIONS;
  notes: string;
  success: boolean;
  error?: string;
}

async function saveResult(result: WorkflowResult): Promise<void> {
  const filename = `mcp_run_${result.workflow}_${TIMESTAMP}.json`;
  const filepath = resolve(ARTIFACTS_DIR, filename);
  await writeFile(filepath, JSON.stringify(result, null, 2));
  console.log(`✅ Saved: ${filename}`);
}

async function runWorkflow(
  name: string,
  inputs: Record<string, unknown>,
  executor: () => Promise<unknown>
): Promise<WorkflowResult> {
  const start = performance.now();
  const result: WorkflowResult = {
    run_id: TIMESTAMP,
    workflow: name,
    inputs,
    outputs: null,
    elapsed_ms: 0,
    tool_versions: TOOL_VERSIONS,
    notes: "smoke suite validation run",
    success: false,
  };

  try {
    result.outputs = await executor();
    result.success = true;
  } catch (error) {
    result.error = error instanceof Error ? error.message : String(error);
  } finally {
    result.elapsed_ms = Math.round(performance.now() - start);
  }

  return result;
}

async function workflow1_Audit(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 1: Audit (scan → SSOT → dependency impact) ---");
  
  return runWorkflow("audit", {}, async () => {
    const scanData = await scanRepository();
    
    const ssotData = await validateSSOT();
    
    const graphStats = await queryDependencyGraph("stats");
    const graphData = JSON.parse(graphStats);
    
    // Extract top 5 nodes by degree (dependencies + dependents count)
    const graph = await import("../dependency_graph_production.json");
    const nodeDegrees = graph.nodes.map((node: any) => {
      const deps = graph.edges.filter((e: any) => e.source === node.id).length;
      const dependents = graph.edges.filter((e: any) => e.target === node.id).length;
      return { id: node.id, degree: deps + dependents };
    });
    nodeDegrees.sort((a, b) => b.degree - a.degree);
    const topNodes = nodeDegrees.slice(0, 5);
    
    return {
      scan: {
        count: scanData.file_count,
        largest: scanData.files.slice(0, 10).map((f: any) => ({
          path: f.path,
          size: f.size,
        })),
      },
      ssot: {
        path: ssotData.path,
        size: ssotData.size,
        sha256: ssotData.hash,
      },
      graph_summary: {
        top_by_degree: topNodes,
        total_nodes: graphData.nodes,
        total_edges: graphData.edges,
      },
    };
  });
}

async function workflow2_ChangeImpact(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 2: Change Impact (node → dependents → spectral) ---");
  
  return runWorkflow("impact", { component: "BLACKSMITH" }, async () => {
    const node = await queryDependencyGraph("node BLACKSMITH");
    const nodeData = JSON.parse(node);
    
    if (nodeData.error) {
      throw new Error(`Node not found: ${nodeData.error}`);
    }
    
    const deps = await queryDependencyGraph("dependencies BLACKSMITH");
    const depsData = JSON.parse(deps);
    
    const dependents = await queryDependencyGraph("dependents BLACKSMITH");
    const dependentsData = JSON.parse(dependents);
    
    // Get spectral tags for dependents
    const graph = await import("../dependency_graph_production.json");
    const dependentsWithSpectral = dependentsData.dependents.slice(0, 5).map((dep: string) => {
      const depNode = graph.nodes.find((n: any) => n.id === dep);
      return { path: dep, spectral: depNode?.spectral_freq || "UNKNOWN" };
    });
    
    return {
      node: nodeData.node.id,
      dependencies: depsData.dependencies,
      dependents: dependentsWithSpectral,
      impact_summary: {
        dependents_count: dependentsData.count,
        dependencies_count: depsData.count,
        high_risk: dependentsWithSpectral.filter((d: any) => 
          ["GOLD", "RED"].includes(d.spectral)
        ).map((d: any) => d.path),
      },
      recommendation: dependentsData.count > 10 
        ? "Manual review required (high coupling)"
        : "Low coupling - safe to modify with caution",
    };
  });
}

async function workflow3_CurriculumOrdering(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 3: Curriculum Ordering (spectral → relations → stats) ---");
  
  return runWorkflow("curriculum", { spectral_frequency: "GOLD" }, async () => {
    const spectral = await queryDependencyGraph("spectral GOLD");
    const spectralData = JSON.parse(spectral);
    
    const stats = await queryDependencyGraph("stats");
    const statsData = JSON.parse(stats);
    
    const graph = await import("../dependency_graph_production.json");
    
    // Calculate in-degree for GOLD nodes
    const goldNodes = spectralData.nodes.slice(0, 10).map((nodeId: string) => {
      const node = graph.nodes.find((n: any) => n.id === nodeId);
      const inDegree = graph.edges.filter((e: any) => e.target === nodeId).length;
      const deps = graph.edges
        .filter((e: any) => e.source === nodeId)
        .slice(0, 3)
        .map((e: any) => e.target);
      
      return {
        node: nodeId,
        in_degree: inDegree,
        dependencies: deps,
        rationale: `Referenced by ${inDegree} nodes - ${
          inDegree > 5 ? "foundational" : "specialized"
        } component`,
      };
    });
    
    goldNodes.sort((a, b) => b.in_degree - a.in_degree);
    
    return {
      frequency: "GOLD",
      ordered_nodes: goldNodes,
      stats: {
        total_gold: spectralData.count,
        total_nodes: statsData.nodes,
        gold_percentage: ((spectralData.count / statsData.nodes) * 100).toFixed(1),
      },
    };
  });
}

async function workflow4_DependencyTrace(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 4: Dependency Trace (dependencies → dependents → graph analysis) ---");
  
  return runWorkflow("trace", { component: "README.md", max_depth: 3 }, async () => {
    const graph = await import("../dependency_graph_production.json");
    
    // Find README.md node
    const rootNode = graph.nodes.find((n: any) => 
      n.id.toLowerCase().includes("readme.md")
    );
    
    if (!rootNode) {
      throw new Error("README.md not found in graph");
    }
    
    // Recursive trace (simplified to depth 3)
    const visited = new Set<string>();
    const adjacencyList: Record<string, string[]> = {};
    
    function traceDeps(nodeId: string, depth: number) {
      if (depth >= 3 || visited.has(nodeId)) return;
      visited.add(nodeId);
      
      const deps = graph.edges
        .filter((e: any) => e.source === nodeId)
        .map((e: any) => e.target);
      
      adjacencyList[nodeId] = deps;
      deps.forEach(dep => traceDeps(dep, depth + 1));
    }
    
    traceDeps(rootNode.id, 0);
    
    return {
      component: rootNode.id,
      adjacency_list: adjacencyList,
      flattened_paths: Array.from(visited),
      depth_stats: {
        max_depth: 3,
        nodes_explored: visited.size,
      },
    };
  });
}

async function workflow5_SpectralHealth(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 5: Spectral Health Check (stats → spectral filters → validation) ---");
  
  return runWorkflow("spectral", { thresholds: { min: 5, max: 50 } }, async () => {
    const stats = await queryDependencyGraph("stats");
    const statsData = JSON.parse(stats);
    
    const distribution = statsData.spectral_distribution;
    const totalNodes = statsData.nodes;
    
    const flags: any[] = [];
    const representatives: Record<string, string[]> = {};
    
    for (const [freq, count] of Object.entries(distribution) as [string, number][]) {
      const percentage = (count / totalNodes) * 100;
      
      if (percentage < 5 || percentage > 50) {
        flags.push({
          frequency: freq,
          count,
          percentage: percentage.toFixed(1),
          status: percentage < 5 ? "under-represented" : "over-represented",
        });
        
        const spectral = await queryDependencyGraph(`spectral ${freq}`);
        const spectralData = JSON.parse(spectral);
        representatives[freq] = spectralData.nodes.slice(0, 5);
      }
    }
    
    return {
      distribution,
      flags,
      representatives,
      recommendations: flags.map(f => 
        f.status === "under-represented"
          ? `Consider expanding ${f.frequency} category (currently ${f.percentage}%)`
          : `Review ${f.frequency} category dominance (${f.percentage}%)`
      ),
    };
  });
}

async function workflow6_NodeDiscovery(): Promise<WorkflowResult> {
  console.log("\n--- Workflow 6: Node Discovery (scan → node lookup → context) ---");
  
  return runWorkflow("discovery", { search_term: "Blacksmith" }, async () => {
    // Use graph directly for discovery since scan returns limited results
    const graph = await import("../dependency_graph_production.json");
    
    const matches = graph.nodes
      .filter((n: any) => n.id.toUpperCase().includes("BLACKSMITH"))
      .slice(0, 5)
      .map((n: any) => n.id);
    
    if (matches.length === 0) {
      throw new Error("No matches found for 'Blacksmith'");
    }
    
    const node = await queryDependencyGraph(`node ${matches[0]}`);
    const nodeData = JSON.parse(node);
    
    const deps = await queryDependencyGraph(`dependencies ${matches[0]}`);
    const depsData = JSON.parse(deps);
    
    const dependents = await queryDependencyGraph(`dependents ${matches[0]}`);
    const dependentsData = JSON.parse(dependents);
    
    return {
      matches,
      node_details: {
        path: nodeData.node.id,
        spectral: nodeData.node.spectral_freq,
        role: nodeData.node.role,
        essence: nodeData.node.essence,
        dependencies: depsData.dependencies.slice(0, 5),
        dependents: dependentsData.dependents.slice(0, 5),
      },
      summary: `${nodeData.node.role}: ${nodeData.node.essence}. Depends on ${depsData.count} components, referenced by ${dependentsData.count}.`,
    };
  });
}

async function main() {
  console.log("=== MCP Smoke Test Suite ===");
  console.log(`Timestamp: ${TIMESTAMP}`);
  console.log(`Tool versions: ${JSON.stringify(TOOL_VERSIONS)}\n`);
  
  // Ensure artifacts directory exists
  await mkdir(ARTIFACTS_DIR, { recursive: true });
  
  const results: WorkflowResult[] = [];
  
  // Run all workflows
  results.push(await workflow1_Audit());
  await saveResult(results[results.length - 1]);
  
  results.push(await workflow2_ChangeImpact());
  await saveResult(results[results.length - 1]);
  
  results.push(await workflow3_CurriculumOrdering());
  await saveResult(results[results.length - 1]);
  
  results.push(await workflow4_DependencyTrace());
  await saveResult(results[results.length - 1]);
  
  results.push(await workflow5_SpectralHealth());
  await saveResult(results[results.length - 1]);
  
  results.push(await workflow6_NodeDiscovery());
  await saveResult(results[results.length - 1]);
  
  // Summary
  console.log("\n=== Summary ===");
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  results.forEach(r => {
    const status = r.success ? "✅" : "❌";
    const time = `${r.elapsed_ms}ms`;
    console.log(`${status} ${r.workflow.padEnd(15)} ${time.padStart(8)} ${r.error || ""}`);
  });
  
  console.log(`\nTotal: ${passed}/${results.length} passed`);
  
  if (failed > 0) {
    console.error(`\n❌ ${failed} workflow(s) failed`);
    process.exit(1);
  }
  
  console.log("\n✅ All workflows passed");
  console.log(`\nNext step: git add artifacts/ && git commit -m "MCP: smoke suite results ${TIMESTAMP}"`);
}

main().catch(error => {
  console.error("Fatal error:", error);
  process.exit(1);
});
