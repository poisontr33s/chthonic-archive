#!/usr/bin/env python3
"""
MAS-MCP MILF Activator
Evaluates MILF activation gates and manages promotion/demotion.

SSOT: .github/copilot-instructions.md

Usage:
  python milf_activator.py [--registry PATH] [--cycles PATH] [--dry-run]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import statistics

MAS_MCP_ROOT = Path(__file__).parent.parent
DEFAULT_REGISTRY = MAS_MCP_ROOT / "artifacts" / "milf_registry.json"
DEFAULT_CYCLES = MAS_MCP_ROOT / "artifacts" / "cycle_reports"
DEFAULT_COMPAT = MAS_MCP_ROOT / "artifacts" / "compatibility" / "probe_report.json"

@dataclass
class ActivationEvaluation:
    milf_id: str
    current_status: str
    cycles_found: int
    metrics: dict
    gates_passed: dict
    recommendation: str  # "promote", "demote", "hold", "insufficient_data"
    reason: str

def load_cycles_for_milf(cycles_dir: Path, milf_id: str, limit: int = 50) -> list[dict]:
    """Load recent cycle reports that match this MILF's domain."""
    cycles = []
    
    if not cycles_dir.exists():
        return cycles
    
    for cycle_file in sorted(cycles_dir.glob("cycle_*.json"), reverse=True)[:limit]:
        try:
            with open(cycle_file) as f:
                cycle = json.load(f)
                # Match by engine or source
                if milf_id.startswith("milf_claude"):
                    if cycle.get("source", {}).get("engine") == "claude":
                        cycles.append(cycle)
                elif milf_id.startswith("milf_tensorrt"):
                    if "tensorrt" in str(cycle.get("metrics", {})):
                        cycles.append(cycle)
                elif milf_id.startswith("milf_onnx"):
                    if "onnx" in str(cycle.get("metrics", {})):
                        cycles.append(cycle)
                else:
                    cycles.append(cycle)  # Default: include all
        except Exception:
            continue
    
    return cycles

def compute_metrics(cycles: list[dict]) -> dict:
    """Compute aggregate metrics from cycles."""
    if not cycles:
        return {}
    
    accepted = sum(1 for c in cycles if c.get("metrics", {}).get("accepted", False))
    acceptance_rate = (accepted / len(cycles)) * 100 if cycles else 0
    
    latencies = [c.get("metrics", {}).get("latency_ms", 0) for c in cycles if c.get("metrics", {}).get("latency_ms")]
    
    error_count = sum(1 for c in cycles if c.get("metrics", {}).get("error_flags"))
    error_rate = (error_count / len(cycles)) * 100 if cycles else 0
    
    quality_scores = [c.get("metrics", {}).get("quality_score", 0) for c in cycles if c.get("metrics", {}).get("quality_score")]
    
    metrics = {
        "cycle_count": len(cycles),
        "acceptance_rate": round(acceptance_rate, 2),
        "error_rate": round(error_rate, 2),
    }
    
    if latencies:
        metrics["latency_p50_ms"] = round(statistics.median(latencies), 2)
        metrics["latency_p95_ms"] = round(statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies), 2)
    
    if quality_scores:
        metrics["quality_score_avg"] = round(statistics.mean(quality_scores), 2)
    
    return metrics

def evaluate_gates(milf: dict, metrics: dict, compat_row: Optional[str]) -> tuple[dict, str, str]:
    """Evaluate activation gates and return (gates_passed, recommendation, reason)."""
    gates = milf.get("activation_gates", {})
    gates_passed = {}
    
    # Check compatibility
    required_rows = milf.get("compatibility_rows", [])
    if required_rows and compat_row:
        gates_passed["compatibility"] = compat_row in required_rows
    elif required_rows:
        gates_passed["compatibility"] = False
    else:
        gates_passed["compatibility"] = True  # No requirement
    
    # Check minimum cycles
    min_cycles = gates.get("min_cycles", 5)
    cycle_count = metrics.get("cycle_count", 0)
    gates_passed["min_cycles"] = cycle_count >= min_cycles
    
    if not gates_passed["min_cycles"]:
        return gates_passed, "insufficient_data", f"Only {cycle_count}/{min_cycles} cycles evaluated"
    
    # Check acceptance threshold
    acceptance_threshold = gates.get("acceptance_threshold", 80)
    acceptance_rate = metrics.get("acceptance_rate", 0)
    gates_passed["acceptance"] = acceptance_rate >= acceptance_threshold
    
    # Check latency
    latency_max = gates.get("latency_p95_max_ms", 1000)
    latency_p95 = metrics.get("latency_p95_ms", 0)
    gates_passed["latency"] = latency_p95 <= latency_max if latency_p95 else True
    
    # Check error rate
    error_max = gates.get("error_rate_max", 10)
    error_rate = metrics.get("error_rate", 0)
    gates_passed["error_rate"] = error_rate <= error_max
    
    # Determine recommendation
    all_passed = all(gates_passed.values())
    critical_failed = not gates_passed.get("compatibility", True) or not gates_passed.get("acceptance", True)
    
    current_status = milf.get("status", "shadow")
    
    if all_passed:
        if current_status == "shadow":
            return gates_passed, "promote", "All gates passed"
        elif current_status == "paused":
            return gates_passed, "promote", "Gates recovered - ready for re-promotion"
        else:
            return gates_passed, "hold", "Already promoted, gates still passing"
    elif critical_failed:
        if current_status == "promoted":
            reasons = []
            if not gates_passed.get("compatibility"):
                reasons.append("compatibility row mismatch")
            if not gates_passed.get("acceptance"):
                reasons.append(f"acceptance {acceptance_rate}% < {acceptance_threshold}%")
            return gates_passed, "demote", f"Critical gates failed: {', '.join(reasons)}"
        else:
            return gates_passed, "hold", "Gates not met for promotion"
    else:
        return gates_passed, "hold", "Some gates failing, monitoring"

def evaluate_milf(milf: dict, cycles_dir: Path, compat_row: Optional[str]) -> ActivationEvaluation:
    """Evaluate a single MILF for activation/demotion."""
    milf_id = milf["milf_id"]
    
    # Load cycles
    cycles = load_cycles_for_milf(cycles_dir, milf_id)
    
    # Compute metrics
    metrics = compute_metrics(cycles)
    
    # Evaluate gates
    gates_passed, recommendation, reason = evaluate_gates(milf, metrics, compat_row)
    
    return ActivationEvaluation(
        milf_id=milf_id,
        current_status=milf.get("status", "shadow"),
        cycles_found=len(cycles),
        metrics=metrics,
        gates_passed=gates_passed,
        recommendation=recommendation,
        reason=reason
    )

def apply_recommendation(milf: dict, eval_result: ActivationEvaluation) -> bool:
    """Apply recommendation to MILF. Returns True if modified."""
    current = milf.get("status")
    new_status = None
    
    if eval_result.recommendation == "promote" and current in ["shadow", "paused"]:
        new_status = "promoted"
    elif eval_result.recommendation == "demote" and current == "promoted":
        new_status = "paused"
    
    if new_status and new_status != current:
        milf["status"] = new_status
        
        # Add to promotion history
        if "promotion_history" not in milf:
            milf["promotion_history"] = []
        
        milf["promotion_history"].append({
            "timestamp": datetime.now().isoformat() + "Z",
            "from_status": current,
            "to_status": new_status,
            "reason": eval_result.reason,
            "cycles_evaluated": eval_result.cycles_found
        })
        
        return True
    
    return False

def main():
    parser = argparse.ArgumentParser(description="MAS-MCP MILF Activator")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--cycles", type=Path, default=DEFAULT_CYCLES)
    parser.add_argument("--compat", type=Path, default=DEFAULT_COMPAT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    print("🔮 MAS-MCP MILF Activator")
    print(f"   SSOT: .github/copilot-instructions.md")
    print()
    
    # Load registry
    with open(args.registry) as f:
        registry = json.load(f)
    
    # Load compatibility row
    compat_row = None
    if args.compat.exists():
        with open(args.compat) as f:
            probe = json.load(f)
            compat_row = probe.get("active_row_id")
    
    print(f"📊 Active compatibility row: {compat_row or 'None'}")
    print()
    
    # Evaluate each MILF
    evaluations = []
    for milf in registry.get("functions", []):
        eval_result = evaluate_milf(milf, args.cycles, compat_row)
        evaluations.append((milf, eval_result))
    
    # Print results
    print("📋 Evaluation Results:")
    for milf, eval_result in evaluations:
        status_emoji = {
            "promote": "⬆️ ",
            "demote": "⬇️ ",
            "hold": "➡️ ",
            "insufficient_data": "⏳"
        }.get(eval_result.recommendation, "❓")
        
        print(f"   {status_emoji} {eval_result.milf_id}")
        print(f"      Status: {eval_result.current_status} → {eval_result.recommendation}")
        print(f"      Cycles: {eval_result.cycles_found}")
        if eval_result.metrics:
            print(f"      Metrics: accept={eval_result.metrics.get('acceptance_rate', 'N/A')}%, "
                  f"p95={eval_result.metrics.get('latency_p95_ms', 'N/A')}ms, "
                  f"errors={eval_result.metrics.get('error_rate', 'N/A')}%")
        print(f"      Gates: {eval_result.gates_passed}")
        print(f"      Reason: {eval_result.reason}")
        print()
    
    # Apply recommendations
    if not args.dry_run:
        modified = False
        for milf, eval_result in evaluations:
            if apply_recommendation(milf, eval_result):
                modified = True
                print(f"✅ Applied: {eval_result.milf_id} → {milf['status']}")
        
        if modified:
            registry["last_updated"] = datetime.now().isoformat() + "Z"
            with open(args.registry, 'w') as f:
                json.dump(registry, f, indent=2)
            print()
            print(f"💾 Registry updated: {args.registry}")
        else:
            print("ℹ️  No changes to apply")
    else:
        print("--- DRY RUN: No changes applied ---")

if __name__ == "__main__":
    main()
