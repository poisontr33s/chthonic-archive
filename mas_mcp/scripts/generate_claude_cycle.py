#!/usr/bin/env python3
"""
MAS-MCP Claude Cycle Report Generator
Usage: python generate_claude_cycle.py --model claude-3.5-sonnet --intent code_generation --accepted true

Generates a cycle report JSON file in mas_mcp/artifacts/cycle_reports/
"""

import argparse
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Default paths
ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts" / "cycle_reports"

def generate_cycle_id() -> str:
    """Generate unique cycle ID: claude_YYYYMMDD_HHMMSS_hash8"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M%S")
    hash_suffix = hashlib.sha256(now.isoformat().encode()).hexdigest()[:8]
    return f"claude_{date_str}_{hash_suffix}"

def compute_quality_score(
    accepted: bool,
    acceptance_type: str,
    revisions: int,
    error_flags: list[str]
) -> float:
    """Compute quality score based on acceptance and errors."""
    base_score = 100.0
    
    # Acceptance penalties
    if not accepted:
        base_score -= 50
    elif acceptance_type == "partial":
        base_score -= 20
    elif acceptance_type == "rejected":
        base_score -= 60
    
    # Revision penalties (diminishing)
    base_score -= min(revisions * 5, 25)
    
    # Error penalties
    error_weights = {
        "syntax_error": 15,
        "type_error": 12,
        "runtime_error": 20,
        "build_failure": 25,
        "test_failure": 15,
        "lint_warning": 3,
        "security_issue": 30,
        "performance_issue": 10,
        "incomplete": 15,
        "off_topic": 25,
        "hallucination": 35,
    }
    for flag in error_flags:
        base_score -= error_weights.get(flag, 10)
    
    return max(0, min(100, base_score))

def evaluate_slo(quality_score: float) -> str:
    """Evaluate SLO status based on quality score."""
    if quality_score >= 90:
        return "excellent"
    elif quality_score >= 70:
        return "acceptable"
    elif quality_score >= 35:
        return "degraded"
    else:
        return "critical"

def create_cycle_report(
    model: str = "claude-3.5-sonnet",
    session_id: str = "manual",
    intent: str = "code_generation",
    domain: str = "unknown",
    complexity: str = "moderate",
    context_files: Optional[list[str]] = None,
    artifact_type: str = "code",
    files_created: Optional[list[str]] = None,
    files_modified: Optional[list[str]] = None,
    tools_invoked: Optional[list[str]] = None,
    terminal_commands: int = 0,
    latency_ms: float = 0,
    time_to_first_token_ms: float = 0,
    accepted: bool = True,
    acceptance_type: str = "full",
    revisions: int = 0,
    error_flags: Optional[list[str]] = None,
    context_tokens: int = 0,
    output_tokens: int = 0,
    lineage_parent: Optional[str] = None,
    tags: Optional[list[str]] = None,
    prompt_content: str = "",
    output_content: str = "",
) -> dict:
    """Create a complete cycle report."""
    
    cycle_id = generate_cycle_id()
    timestamp = datetime.now().isoformat() + "Z"
    
    # Hash prompt and output for privacy
    prompt_hash = hashlib.sha256(prompt_content.encode()).hexdigest()
    artifact_hash = hashlib.sha256(output_content.encode()).hexdigest()
    
    # Compute quality score
    error_flags = error_flags or []
    quality_score = compute_quality_score(accepted, acceptance_type, revisions, error_flags)
    slo_status = evaluate_slo(quality_score)
    
    report = {
        "cycle_id": cycle_id,
        "timestamp": timestamp,
        "source": {
            "engine": "claude",
            "model": model,
            "session_id": session_id,
            "context_tokens": context_tokens,
            "output_tokens": output_tokens,
        },
        "input": {
            "prompt_hash": prompt_hash,
            "intent": intent,
            "domain": domain,
            "complexity": complexity,
            "context_files": context_files or [],
        },
        "output": {
            "artifact_type": artifact_type,
            "artifact_hash": artifact_hash,
            "files_created": files_created or [],
            "files_modified": files_modified or [],
            "tools_invoked": tools_invoked or [],
            "terminal_commands": terminal_commands,
        },
        "metrics": {
            "latency_ms": latency_ms,
            "time_to_first_token_ms": time_to_first_token_ms,
            "accepted": accepted,
            "acceptance_type": acceptance_type,
            "revisions": revisions,
            "error_flags": error_flags,
            "quality_score": round(quality_score, 2),
        },
        "governance": {
            "slo_status": slo_status,
            "lineage_parent": lineage_parent,
            "tags": tags or [],
        },
    }
    
    return report

def save_cycle_report(report: dict, output_dir: Optional[Path] = None) -> Path:
    """Save cycle report to JSON file."""
    output_dir = output_dir or ARTIFACTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"cycle_{report['cycle_id']}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    
    return filepath

def main():
    parser = argparse.ArgumentParser(description='Generate Claude Cycle Report')
    
    # Source
    parser.add_argument('--model', default='claude-3.5-sonnet', 
                        choices=['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 
                                 'claude-3.5-sonnet', 'claude-3.5-haiku', 'claude-4-opus'])
    parser.add_argument('--session-id', default='manual')
    parser.add_argument('--context-tokens', type=int, default=0)
    parser.add_argument('--output-tokens', type=int, default=0)
    
    # Input
    parser.add_argument('--intent', default='code_generation',
                        choices=['code_generation', 'code_review', 'refactoring', 'debugging',
                                 'documentation', 'architecture', 'analysis', 'explanation', 'other'])
    parser.add_argument('--domain', default='unknown')
    parser.add_argument('--complexity', default='moderate',
                        choices=['trivial', 'simple', 'moderate', 'complex', 'extreme'])
    parser.add_argument('--context-files', nargs='*', default=[])
    
    # Output
    parser.add_argument('--artifact-type', default='code',
                        choices=['code', 'documentation', 'analysis', 'schema', 
                                 'configuration', 'script', 'explanation', 'mixed'])
    parser.add_argument('--files-created', nargs='*', default=[])
    parser.add_argument('--files-modified', nargs='*', default=[])
    parser.add_argument('--tools-invoked', nargs='*', default=[])
    parser.add_argument('--terminal-commands', type=int, default=0)
    
    # Metrics
    parser.add_argument('--latency-ms', type=float, default=0)
    parser.add_argument('--ttft-ms', type=float, default=0)
    parser.add_argument('--accepted', type=lambda x: x.lower() == 'true', default=True)
    parser.add_argument('--acceptance-type', default='full',
                        choices=['full', 'partial', 'rejected', 'pending'])
    parser.add_argument('--revisions', type=int, default=0)
    parser.add_argument('--error-flags', nargs='*', default=[])
    
    # Governance
    parser.add_argument('--lineage-parent', default=None)
    parser.add_argument('--tags', nargs='*', default=[])
    
    # Output path
    parser.add_argument('--output-dir', type=Path, default=None)
    parser.add_argument('--dry-run', action='store_true', help='Print JSON without saving')
    
    args = parser.parse_args()
    
    report = create_cycle_report(
        model=args.model,
        session_id=args.session_id,
        intent=args.intent,
        domain=args.domain,
        complexity=args.complexity,
        context_files=args.context_files,
        artifact_type=args.artifact_type,
        files_created=args.files_created,
        files_modified=args.files_modified,
        tools_invoked=args.tools_invoked,
        terminal_commands=args.terminal_commands,
        latency_ms=args.latency_ms,
        time_to_first_token_ms=args.ttft_ms,
        accepted=args.accepted,
        acceptance_type=args.acceptance_type,
        revisions=args.revisions,
        error_flags=args.error_flags,
        context_tokens=args.context_tokens,
        output_tokens=args.output_tokens,
        lineage_parent=args.lineage_parent,
        tags=args.tags,
    )
    
    if args.dry_run:
        print(json.dumps(report, indent=2))
    else:
        filepath = save_cycle_report(report, args.output_dir)
        print(f"✅ Cycle report saved: {filepath}")
        print(f"   Quality Score: {report['metrics']['quality_score']}%")
        print(f"   SLO Status: {report['governance']['slo_status']}")

if __name__ == "__main__":
    main()
