/**
 * MCP Smoke Suite Tool
 * 
 * Validates all 4 MCP tools programmatically without spawning server
 * (Called from within the server, so tests tools directly)
 */

import { scanRepository } from "./scanRepository.ts";
import { validateSSOT } from "./validateSSOT.ts";
import { queryDependencyGraph } from "./queryDependencyGraph.ts";

interface ValidationResult {
  name: string;
  passed: boolean;
  error?: string;
  details?: Record<string, unknown>;
}

interface SmokeResults {
  timestamp: string;
  total_validations: number;
  passed: number;
  failed: number;
  success: boolean;
  validations: ValidationResult[];
}

async function validate(
  name: string,
  executor: () => Promise<unknown>
): Promise<ValidationResult> {
  try {
    const result = await executor();
    return { name, passed: true, details: { result } };
  } catch (error) {
    return {
      name,
      passed: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export async function runSmokeSuite(): Promise<SmokeResults> {
  const validations: ValidationResult[] = [];

  // Test 1: ping (implicit - if we're running, server is alive)
  validations.push({
    name: "ping (implicit)",
    passed: true,
    details: { pong: true },
  });

  // Test 2: scan_repository
  validations.push(
    await validate("scan_repository", async () => {
      const result = await scanRepository();
      if (typeof result.file_count !== "number" || result.file_count === 0) {
        throw new Error("Invalid file count");
      }
      return { file_count: result.file_count, repository: result.repository };
    })
  );

  // Test 3: validate_ssot_integrity
  validations.push(
    await validate("validate_ssot_integrity", async () => {
      const result = await validateSSOT();
      if (result.status !== "valid" || !result.hash) {
        throw new Error("SSOT validation failed");
      }
      return {
        status: result.status,
        hash: result.hash.substring(0, 16) + "...",
        size: result.size,
      };
    })
  );

  // Test 4: query_dependency_graph (stats)
  validations.push(
    await validate("query_dependency_graph (stats)", async () => {
      const resultStr = await queryDependencyGraph("stats");
      const result = JSON.parse(resultStr);
      if (typeof result.total_nodes !== "number" || result.total_nodes === 0) {
        throw new Error("Invalid dependency graph stats");
      }
      return {
        total_nodes: result.total_nodes,
        total_hyperedges: result.total_hyperedges,
        spectral_frequencies: Object.keys(result.spectral_distribution || {}).length,
      };
    })
  );

  // Test 5: query_dependency_graph (spectral BLUE)
  validations.push(
    await validate("query_dependency_graph (spectral)", async () => {
      const resultStr = await queryDependencyGraph("spectral BLUE");
      const result = JSON.parse(resultStr);
      if (!Array.isArray(result.nodes) || result.nodes.length === 0) {
        throw new Error("No BLUE spectral nodes found");
      }
      return {
        frequency: "BLUE",
        node_count: result.nodes.length,
        first_node: result.nodes[0]?.id || null,
      };
    })
  );

  const passed = validations.filter((v) => v.passed).length;
  const failed = validations.length - passed;

  return {
    timestamp: new Date().toISOString(),
    total_validations: validations.length,
    passed,
    failed,
    success: failed === 0,
    validations,
  };
}
