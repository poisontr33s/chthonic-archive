# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  THE DECORATOR'S BLESSING: bun_compliance_audit.py                       ║
# ║  Python module: Severity, Violation, BunComplianceScanner, safe_print, main ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║  Spectral Frequency: WHITE                                                  ║
# ║  Architectural Role: 🌿 THE GARDEN                                           ║
# ║  Purpose: Bun Compliance Audit Script                                       ║
# ║  Exports: Severity, Violation, BunComplianceScanner, safe_print, main       ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║  Cross-References (Bidirectional):                                      ║
# ║    (Standalone file - no detected dependencies)                          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

#!/usr/bin/env python3
"""
Bun Compliance Audit Script
============================

Scans repository for non-Bun package manager usage and suggests corrections
per SSOT §XIV.2 mandate: "Default package manager: bun"

Usage:
    uv run python scripts/bun_compliance_audit.py                  # Full scan
    uv run python scripts/bun_compliance_audit.py --fix            # Auto-fix mode (destructive)
    uv run python scripts/bun_compliance_audit.py --ci             # CI mode (exit 1 on violations)
    uv run python scripts/bun_compliance_audit.py --verbose        # Detailed output

Exit Codes:
    0 - Compliant (or violations fixed in --fix mode)
    1 - Violations found (--ci mode)
    2 - Script error

Bun Documentation References:
    - bunx: https://bun.sh/docs/cli/bunx
    - bun install: https://bun.sh/docs/cli/install
    - bun run: https://bun.sh/docs/cli/run
    - bun test: https://bun.sh/docs/test/writing
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Violation severity levels"""
    CRITICAL = "CRITICAL"  # Violates SSOT mandate directly
    WARNING = "WARNING"    # Sub-optimal but not blocking
    INFO = "INFO"          # Informational suggestion


@dataclass
class Violation:
    """Represents a Bun compliance violation"""
    file: Path
    line_num: int
    line_content: str
    pattern: str
    severity: Severity
    suggestion: str
    docs_ref: str


class BunComplianceScanner:
    """Scans for non-Bun package manager usage"""
    
    # Patterns to detect (regex -> severity, suggestion, docs)
    VIOLATION_PATTERNS: Dict[str, Tuple[Severity, str, str]] = {
        # Package execution
        r'\bnpx\b(?!\s+@modelcontextprotocol/inspector)': (
            Severity.CRITICAL,
            "Replace 'npx' with 'bunx' per SSOT §XIV.2",
            "https://bun.sh/docs/cli/bunx"
        ),
        r'\byarn\s+dlx\b': (
            Severity.CRITICAL,
            "Replace 'yarn dlx' with 'bunx'",
            "https://bun.sh/docs/cli/bunx"
        ),
        r'\bpnpm\s+dlx\b': (
            Severity.CRITICAL,
            "Replace 'pnpm dlx' with 'bunx'",
            "https://bun.sh/docs/cli/bunx"
        ),
        
        # Package installation
        r'\bnpm\s+install\b': (
            Severity.CRITICAL,
            "Replace 'npm install' with 'bun install'",
            "https://bun.sh/docs/cli/install"
        ),
        r'\bnpm\s+i\b': (
            Severity.CRITICAL,
            "Replace 'npm i' with 'bun install'",
            "https://bun.sh/docs/cli/install"
        ),
        r'\byarn\s+add\b': (
            Severity.CRITICAL,
            "Replace 'yarn add' with 'bun add'",
            "https://bun.sh/docs/cli/install"
        ),
        r'\bpnpm\s+add\b': (
            Severity.CRITICAL,
            "Replace 'pnpm add' with 'bun add'",
            "https://bun.sh/docs/cli/install"
        ),
        
        # Script execution
        r'\bnpm\s+run\b': (
            Severity.CRITICAL,
            "Replace 'npm run' with 'bun run'",
            "https://bun.sh/docs/cli/run"
        ),
        r'\byarn\s+run\b': (
            Severity.CRITICAL,
            "Replace 'yarn run' with 'bun run'",
            "https://bun.sh/docs/cli/run"
        ),
        r'\bpnpm\s+run\b': (
            Severity.CRITICAL,
            "Replace 'pnpm run' with 'bun run'",
            "https://bun.sh/docs/cli/run"
        ),
        
        # Test execution
        r'\bnpm\s+test\b': (
            Severity.CRITICAL,
            "Replace 'npm test' with 'bun test'",
            "https://bun.sh/docs/test/writing"
        ),
        r'\byarn\s+test\b': (
            Severity.CRITICAL,
            "Replace 'yarn test' with 'bun test'",
            "https://bun.sh/docs/test/writing"
        ),
        
        # Lockfile references
        r'package-lock\.json': (
            Severity.WARNING,
            "Should reference 'bun.lock' instead of 'package-lock.json'",
            "https://bun.sh/docs/cli/install"
        ),
        r'yarn\.lock': (
            Severity.WARNING,
            "Should reference 'bun.lock' instead of 'yarn.lock'",
            "https://bun.sh/docs/cli/install"
        ),
        r'pnpm-lock\.yaml': (
            Severity.WARNING,
            "Should reference 'bun.lock' instead of 'pnpm-lock.yaml'",
            "https://bun.sh/docs/cli/install"
        ),
        
        # Node.js runtime (informational - context-dependent)
        r'\bnode\s+[a-zA-Z0-9_\-./]+\.(?:js|ts|mjs|cjs)\b': (
            Severity.INFO,
            "Consider 'bun run <file>' instead of 'node <file>' where appropriate",
            "https://bun.sh/docs/cli/run"
        ),
    }
    
    # Exclusions (patterns that are acceptable despite matching)
    EXCLUSIONS = {
        # MCP Inspector is Node.js-only tool (documented exception)
        r'npx\s+@modelcontextprotocol/inspector',
        # Documentation of what NOT to do
        r'(?:DO NOT|❌|INCORRECT|WRONG|AVOID).*(?:npm|npx|yarn|pnpm)',
        # Historical references (changelogs, migration docs)
        r'(?:previously|before|migrated from|replaced).*(?:npm|npx|yarn|pnpm)',
        # Educational documentation files (migration guides, config history)
        r'BUN_COMPLIANCE_COMPLETE\.md',
        r'WIN11_CONFIGURATION\.md',
        # Package registry mentions (neutral context)
        r'(?:npm registry|PyPI|crates\.io)',
        # This script's own violation patterns (meta-reference)
        r'Replace.*with.*bunx',
        r'Replace.*with.*bun\s+(?:install|add|run|test)',
        # Documentation showing equivalence or detection patterns
        r"Bun's\s+(?:npx|npm)\s+equivalent",
        r'per\s+SSOT.*XIV',  # Documentation references
        r'violation\s+patterns.*(?:npm|npx|yarn|pnpm)',  # Scanner documentation
        r'Detection.*patterns.*(?:npm|npx|yarn|pnpm)',  # Scanner documentation
        r'`(?:npm|npx|yarn|pnpm)`\s*→',  # Mapping/migration docs showing old → new
        r'Should\s+be\s+`bun',  # Fix recommendations
        r'bunx.*npx\s+equivalent',  # Cross-reference documentation
        # Lockfile documentation (showing what the scanner detects)
        r'`(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml)`.*references',
        # Example output in documentation (showing what violations look like)
        r'^\s+Line:\s+(?:npm|npx|yarn|pnpm)',  # Indented example violation output
        r'example/path/.*(?:npm|npx|yarn|pnpm)',  # Example file paths
        # Neutral lockfile mentions (ignore lists, file enumerations)
        r'(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml).*(?:bun\.lock|Cargo\.lock|uv\.lock)',
        r'(?:bun\.lock|Cargo\.lock|uv\.lock).*(?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml)',
        # File lists and sets (Python/JS code)
        r'["\'](?:package-lock\.json|yarn\.lock|pnpm-lock\.yaml)["\']',
        # node_modules internals (vendor code)
        r'node_modules',
    }
    
    # Paths to skip entirely
    SKIP_PATHS = {
        'dist/',  # Bundled vendor code (e.g., React in VSCode extension)
        '.git',
        'node_modules',
        '.venv',
        '__pycache__',
        'target',
        'build',
        '.cache',
        '.cargo',
        'logs',
        'artifacts',
        'dumpster-dive/intake/overnight-daemon',  # Daemon logs
        'dumpster-dive/from-github/macro-prompt-world',  # Archive/historical content (canonical location)
        '.github/ssot_backups',  # Backup archives
        'dependency_graph.json',  # Generated artifact
        'temp_repo_structure.json',  # Generated snapshot
        'bun.lock',  # Managed by Bun
        'Cargo.lock',  # Managed by Cargo
        'uv.lock',  # Managed by uv
        'BUN_COMPLIANCE_COMPLETE.md',  # Educational migration guide
        'WIN11_CONFIGURATION.md',  # Historical setup documentation
    }
    
    def __init__(self, repo_root: Path, verbose: bool = False):
        self.repo_root = repo_root
        self.verbose = verbose
        self.violations: List[Violation] = []
        
    def is_excluded_line(self, line: str) -> bool:
        """Check if line matches exclusion patterns"""
        for pattern in self.EXCLUSIONS:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def should_skip_path(self, path: Path) -> bool:
        """Check if path should be skipped"""
        path_str = str(path.relative_to(self.repo_root)).replace('\\', '/')
        for skip in self.SKIP_PATHS:
            if skip in path_str:
                return True
        # Skip binary/generated files
        if path.suffix in {'.pyc', '.so', '.dll', '.exe', '.lock', '.sqlite'}:
            return True
        return False
    
    def scan_file(self, file_path: Path):
        """Scan single file for violations"""
        if self.should_skip_path(file_path):
            return
        
        # Skip this script itself (meta-reference)
        if file_path.name == 'bun_compliance_audit.py':
            return
            
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            if self.verbose:
                safe_print(f"[WARN] Skipping {file_path}: {e}")
            return
        
        for line_num, line in enumerate(content.splitlines(), start=1):
            # Skip excluded lines (documentation, historical, etc.)
            if self.is_excluded_line(line):
                continue
            
            # Check against violation patterns
            for pattern, (severity, suggestion, docs_ref) in self.VIOLATION_PATTERNS.items():
                if re.search(pattern, line):
                    self.violations.append(Violation(
                        file=file_path,
                        line_num=line_num,
                        line_content=line.strip(),
                        pattern=pattern,
                        severity=severity,
                        suggestion=suggestion,
                        docs_ref=docs_ref
                    ))
    
    def scan(self):
        """Scan entire repository"""
        text_extensions = {
            '.md', '.txt', '.yml', '.yaml', '.json', '.toml',
            '.ts', '.js', '.tsx', '.jsx', '.mjs', '.cjs',
            '.py', '.rs', '.sh', '.ps1', '.psm1',
        }
        
        for path in self.repo_root.rglob('*'):
            if path.is_file() and path.suffix in text_extensions:
                self.scan_file(path)
    
    def print_report(self):
        """Print violation report"""
        if not self.violations:
            safe_print("[PASS] Bun compliance: CLEAN (no violations detected)")
            return
        
        # Group by severity
        by_severity = {s: [] for s in Severity}
        for v in self.violations:
            by_severity[v.severity].append(v)
        
        total = len(self.violations)
        critical = len(by_severity[Severity.CRITICAL])
        warning = len(by_severity[Severity.WARNING])
        info = len(by_severity[Severity.INFO])
        
        safe_print(f"[FAIL] Bun compliance: VIOLATIONS DETECTED")
        safe_print(f"   Total: {total} | Critical: {critical} | Warning: {warning} | Info: {info}\n")
        
        for severity in [Severity.CRITICAL, Severity.WARNING, Severity.INFO]:
            violations = by_severity[severity]
            if not violations:
                continue
            
            icon = "[!]" if severity == Severity.CRITICAL else "[W]" if severity == Severity.WARNING else "[i]"
            safe_print(f"{icon} {severity.value} ({len(violations)})")
            safe_print("=" * 80)
            
            for v in violations:
                rel_path = v.file.relative_to(self.repo_root)
                safe_print(f"\nFile: {rel_path}:{v.line_num}")
                safe_print(f"   Line: {v.line_content[:100]}")
                safe_print(f"   Fix:  {v.suggestion}")
                safe_print(f"   Docs: {v.docs_ref}")
            
            safe_print("")
    
    def get_exit_code(self) -> int:
        """Determine exit code based on violations"""
        if not self.violations:
            return 0
        # Exit 1 if any CRITICAL violations exist
        if any(v.severity == Severity.CRITICAL for v in self.violations):
            return 1
        return 0


def safe_print(msg: str):
    """Print with Windows console encoding fallback"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback: encode to UTF-8 with replacement for Windows console
        import sys
        safe_msg = msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        # Strip problematic Unicode chars (arrows, emojis)
        safe_msg = safe_msg.replace('→', '->')  .replace('✓', '[OK]').replace('✗', '[FAIL]')
        print(safe_msg)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scan repository for Bun compliance violations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--ci', action='store_true',
                       help='CI mode: exit 1 on violations')
    parser.add_argument('--fix', action='store_true',
                       help='Auto-fix mode (NOT IMPLEMENTED - placeholder)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    
    if args.verbose:
        safe_print(f"[SCAN] Checking {repo_root} for Bun compliance violations...")
    
    scanner = BunComplianceScanner(repo_root, verbose=args.verbose)
    scanner.scan()
    scanner.print_report()
    
    if args.fix:
        safe_print("\n[WARNING] Auto-fix mode not yet implemented (requires SSOT approval)")
        return 2
    
    exit_code = scanner.get_exit_code()
    
    if args.ci and exit_code != 0:
        safe_print("\n[CI FAILURE] Critical Bun compliance violations detected")
        safe_print("   Run locally to see details: uv run python scripts/bun_compliance_audit.py")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
