import { resolve } from "path";

interface GraphNode {
  id: string;
  spectral_freq: string;
  role: string;
  essence: string;
  exports_count: number;
}

interface DependencyGraph {
  directed: boolean;
  nodes: GraphNode[];
  edges: string[][]; // Hyperedges: arrays of node IDs
  metadata: {
    hyperedges: string[][];
    clusters: Array<{ members: string; break_edges: string; strategy: string }>;
    void_dirs: string[];
    validation: {
      graph_is_connected: boolean;
      graph_is_dag: boolean;
      largest_component_size: number;
    };
  };
}

/**
 * Query the dependency graph (read-only, loads existing JSON)
 * 
 * Supported queries:
 * - "node <filename>" - Get node details
 * - "dependencies <filename>" - Get what this file depends on
 * - "dependents <filename>" - Get what depends on this file
 * - "spectral <frequency>" - Filter nodes by spectral frequency (RED/ORANGE/GOLD/BLUE/WHITE/INDIGO/VIOLET)
 * - "stats" - Get graph statistics
 */
export async function queryDependencyGraph(query: string): Promise<string> {
  const repoRoot = resolve(import.meta.dir, "..", "..");
  const graphPath = resolve(repoRoot, "dependency_graph_production.json");

  try {
    const file = Bun.file(graphPath);
    if (!(await file.exists())) {
      return JSON.stringify({
        error: "dependency_graph_production.json not found",
        path: graphPath,
      });
    }

    const graph: DependencyGraph = await file.json();
    const parts = query.trim().toLowerCase().split(/\s+/);
    const command = parts[0];
    const arg = parts.slice(1).join(" ");

    switch (command) {
      case "node": {
        const node = graph.nodes.find((n) => n.id.toLowerCase().includes(arg.toLowerCase()));
        if (!node) {
          return JSON.stringify({ error: "Node not found", query: arg });
        }
        return JSON.stringify({ node }, null, 2);
      }

      case "dependencies": {
        // Find edges where this file is the source (what it points to)
        const deps = graph.edges
          .filter((edge) => edge.source.toLowerCase().includes(arg.toLowerCase()))
          .map((edge) => edge.target);
        
        const uniqueDeps = [...new Set(deps)];
        return JSON.stringify({
          file: arg,
          dependencies: uniqueDeps,
          count: uniqueDeps.length,
        }, null, 2);
      }

      case "dependents": {
        // Find edges where this file is the target (what points to it)
        const dependents = graph.edges
          .filter((edge) => edge.target.toLowerCase().includes(arg.toLowerCase()))
          .map((edge) => edge.source);
        
        const uniqueDependents = [...new Set(dependents)];
        return JSON.stringify({
          file: arg,
          dependents: uniqueDependents,
          count: uniqueDependents.length,
        }, null, 2);
      }

      case "spectral": {
        const freq = arg.toUpperCase();
        const filtered = graph.nodes.filter((n) => n.spectral_freq === freq);
        return JSON.stringify({
          frequency: freq,
          nodes: filtered.slice(0, 50), // Limit to 50 for readability
          total_count: filtered.length,
          truncated: filtered.length > 50,
        }, null, 2);
      }

      case "stats": {
        const freqCounts = graph.nodes.reduce((acc, node) => {
          acc[node.spectral_freq] = (acc[node.spectral_freq] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);

        return JSON.stringify({
          total_nodes: graph.nodes.length,
          total_hyperedges: graph.edges.length,
          directed: graph.directed,
          spectral_distribution: freqCounts,
          void_directories: graph.metadata.void_dirs.length,
          clusters: graph.metadata.clusters.length,
          validation: graph.metadata.validation,
        }, null, 2);
      }

      default: {
        return JSON.stringify({
          error: "Unknown query command",
          command,
          supported_commands: [
            "node <filename>",
            "dependencies <filename>",
            "dependents <filename>",
            "spectral <RED|ORANGE|GOLD|BLUE|WHITE|INDIGO|VIOLET>",
            "stats",
          ],
        });
      }
    }
  } catch (error) {
    return JSON.stringify({
      error: "Failed to query dependency graph",
      message: error instanceof Error ? error.message : String(error),
    });
  }
}
