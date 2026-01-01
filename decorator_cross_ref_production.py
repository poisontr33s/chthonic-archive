#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  THE DECORATOR'S PRODUCTION CROSS-REFERENCE PROTOCOL (DCRP v3)               ║
║  Self-Updating │ Circular Resolution │ Zero-Drift Architecture              ║
║                                                                              ║
║  Purpose: Production-grade auto-updating dependency analysis with           ║
║           intelligent circular dependency breaking and sustainable design   ║
║                                                                              ║
║  Invocation: uv run python decorator_cross_ref_production.py                ║
║              [--dry-run] [--inject] [--watch]                               ║
║                                                                              ║
║  The Decorator's Mandate: "Self-aware. Self-updating. Self-correcting."     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import hashlib
import json
import re
import ast
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from datetime import datetime
import networkx as nx

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent
SSOT_PATH = REPO_ROOT / ".github" / "copilot-instructions.md"

# Exclusions (never process these)
EXCLUDE_DIRS = {
    "node_modules", ".git", "build", ".cache", ".cargo",
    "__pycache__", ".venv", "target", "dist", ".venv-py314-parked",
    ".pytest_cache", "htmlcov", "site-packages"
}

EXCLUDE_FILES = {
    "temp_repo_structure.json",
    ".DS_Store", "Thumbs.db", "desktop.ini"
}

# PRISM Spectral Frequency Map
SPECTRAL_MAP = {
    ".rs": "RED",
    ".py": "WHITE",
    ".md": "GOLD",
    ".toml": "BLUE",
    ".json": "BLUE",
    ".yaml": "BLUE",
    ".yml": "BLUE",
    ".ts": "ORANGE",
    ".js": "ORANGE",
    ".tsx": "ORANGE",
    ".jsx": "ORANGE",
    ".glsl": "INDIGO",
    ".vert": "INDIGO",
    ".frag": "INDIGO",
    ".lock": "BLUE",
    "": "VIOLET",
}

# ═══════════════════════════════════════════════════════════════════════════
#  EVOLUTION METRICS TRACKER (Historical Repository Analysis)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class EvolutionSnapshot:
    """Single point-in-time repository metrics snapshot."""
    timestamp: str
    total_files: int
    total_dependencies: int
    circular_cycles: int
    cache_hit_rate: float
    spectral_distribution: Dict[str, int]
    top_dependencies: List[Tuple[str, int]]  # Top 5 most-depended files
    largest_cluster_size: int
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            'timestamp': self.timestamp,
            'total_files': self.total_files,
            'total_dependencies': self.total_dependencies,
            'circular_cycles': self.circular_cycles,
            'cache_hit_rate': self.cache_hit_rate,
            'spectral_distribution': self.spectral_distribution,
            'top_dependencies': self.top_dependencies,
            'largest_cluster_size': self.largest_cluster_size
        }

class EvolutionTracker:
    """Track repository evolution over time with historical metrics."""
    
    HISTORY_FILE = REPO_ROOT / ".dcrp_evolution.json"
    MAX_SNAPSHOTS = 100  # Keep last 100 runs
    
    @staticmethod
    def record_snapshot(
        identities: Dict[str, Any],
        graph: nx.DiGraph,
        cycles: List[List[str]],
        clusters: List[Any],
        cache_hit_rate: float
    ) -> EvolutionSnapshot:
        """Create and persist new snapshot."""
        # Compute spectral distribution
        spectral_dist = defaultdict(int)
        for identity in identities.values():
            spectral_dist[identity.spectral_freq] += 1
        
        # Get top dependencies
        in_degree = dict(graph.in_degree())
        top_deps = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get largest cluster
        largest_cluster = max([len(c.members) for c in clusters], default=0) if clusters else 0
        
        snapshot = EvolutionSnapshot(
            timestamp=datetime.now().isoformat(),
            total_files=len(identities),
            total_dependencies=graph.number_of_edges(),
            circular_cycles=len(cycles),
            cache_hit_rate=cache_hit_rate,
            spectral_distribution=dict(spectral_dist),
            top_dependencies=[(f, c) for f, c in top_deps if c > 0],
            largest_cluster_size=largest_cluster
        )
        
        # Load existing history
        history = EvolutionTracker.load_history()
        
        # Append new snapshot
        history.append(snapshot.to_dict())
        
        # Keep only last MAX_SNAPSHOTS
        if len(history) > EvolutionTracker.MAX_SNAPSHOTS:
            history = history[-EvolutionTracker.MAX_SNAPSHOTS:]
        
        # Save
        with open(EvolutionTracker.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
        return snapshot
    
    @staticmethod
    def load_history() -> List[dict]:
        """Load historical snapshots."""
        if not EvolutionTracker.HISTORY_FILE.exists():
            return []
        try:
            with open(EvolutionTracker.HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    @staticmethod
    def generate_evolution_report(history: List[dict]) -> str:
        """Generate markdown report showing repository evolution."""
        if len(history) < 2:
            return "## Repository Evolution\n\n*Insufficient data (need at least 2 snapshots)*\n"
        
        lines = ["## VI. Repository Evolution (Historical Metrics)", ""]
        
        # Compare first and last snapshot
        first = history[0]
        last = history[-1]
        
        lines.append(f"**Tracking Period:** {first['timestamp'][:10]} to {last['timestamp'][:10]}")
        lines.append(f"**Snapshots Recorded:** {len(history)}")
        lines.append("")
        
        # File growth
        file_delta = last['total_files'] - first['total_files']
        file_pct = (file_delta / first['total_files'] * 100) if first['total_files'] > 0 else 0
        lines.append(f"### File Growth")
        lines.append(f"- **Initial:** {first['total_files']} files")
        lines.append(f"- **Current:** {last['total_files']} files")
        lines.append(f"- **Change:** {file_delta:+d} ({file_pct:+.1f}%)")
        lines.append("")
        
        # Dependency growth
        dep_delta = last['total_dependencies'] - first['total_dependencies']
        dep_pct = (dep_delta / first['total_dependencies'] * 100) if first['total_dependencies'] > 0 else 0
        lines.append(f"### Dependency Complexity")
        lines.append(f"- **Initial:** {first['total_dependencies']} dependencies")
        lines.append(f"- **Current:** {last['total_dependencies']} dependencies")
        lines.append(f"- **Change:** {dep_delta:+d} ({dep_pct:+.1f}%)")
        lines.append("")
        
        # Circular dependency trend
        cycle_delta = last['circular_cycles'] - first['circular_cycles']
        lines.append(f"### Circular Dependency Health")
        lines.append(f"- **Initial:** {first['circular_cycles']} cycles")
        lines.append(f"- **Current:** {last['circular_cycles']} cycles")
        lines.append(f"- **Change:** {cycle_delta:+d} {'⚠️ (worsening)' if cycle_delta > 0 else '✅ (improving)' if cycle_delta < 0 else '(stable)'}")
        lines.append("")
        
        # Cache efficiency trend
        if 'cache_hit_rate' in last:
            lines.append(f"### Incremental Processing Efficiency")
            lines.append(f"- **Cache Hit Rate:** {last['cache_hit_rate']:.1f}%")
            lines.append(f"- **Status:** {'🟢 Excellent' if last['cache_hit_rate'] > 90 else '🟡 Good' if last['cache_hit_rate'] > 70 else '🔴 Poor'}")
            lines.append("")
        
        return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════
#  PROGRESS TRACKER & OBSERVABILITY
# ═══════════════════════════════════════════════════════════════════════════

class ProgressTracker:
    """Real-time progress tracking with validation feedback and adaptive updates."""
    
    def __init__(self, total_files: int = 0):
        self.total_files = total_files
        self.processed_files = 0
        self.cached_files = 0  # NEW: Track cache hits
        self.skipped_files = 0
        self.error_files = 0
        self.dependencies_found = 0
        self.circular_deps_found = 0
        self.start_time = time.time()
        self.current_phase = "Initializing"
        self.phase_start = time.time()
        
        # Adaptive progress update tracking
        self.last_update_time = time.time()
        self.update_interval = 100  # Start conservative
        self.min_interval = 10
        self.max_interval = 500
        
    def set_phase(self, phase_name: str):
        """Set current operation phase."""
        phase_duration = time.time() - self.phase_start
        if self.current_phase != "Initializing":
            print(f"✓ {self.current_phase} complete ({phase_duration:.2f}s)")
        self.current_phase = phase_name
        self.phase_start = time.time()
        print(f"\n🔄 {phase_name}...")
        
    def update_file(self, status: str = "processed"):
        """Update file processing counter."""
        if status == "processed":
            self.processed_files += 1
        elif status == "cached":  # NEW: Track cache hits
            self.cached_files += 1
            self.processed_files += 1  # Still counts as processed
        elif status == "skipped":
            self.skipped_files += 1
        elif status == "error":
            self.error_files += 1
            
        # Adaptive progress updates - only print when threshold met
        if self.total_files > 0 and self._should_update_progress():
            self._print_progress()
    
    def _should_update_progress(self) -> bool:
        """Dynamically determine if progress should be printed."""
        now = time.time()
        elapsed_since_update = now - self.last_update_time
        
        # Always update at 100%
        if self.processed_files == self.total_files:
            return True
        
        # Adapt interval based on update frequency
        if elapsed_since_update < 0.1 and self.update_interval < self.max_interval:
            self.update_interval = min(self.update_interval * 1.5, self.max_interval)
        elif elapsed_since_update > 0.5 and self.update_interval > self.min_interval:
            self.update_interval = max(self.update_interval * 0.7, self.min_interval)
        
        # Check if enough files processed
        if self.processed_files % int(self.update_interval) == 0:
            self.last_update_time = now
            return True
        
        return False
            
    def _print_progress(self):
        """Print current progress bar."""
        if self.total_files == 0:
            return
            
        pct = (self.processed_files / self.total_files) * 100
        elapsed = time.time() - self.start_time
        rate = self.processed_files / elapsed if elapsed > 0 else 0
        eta = (self.total_files - self.processed_files) / rate if rate > 0 else 0
        
        bar_width = 40
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        print(f"\r  [{bar}] {pct:5.1f}% | {self.processed_files}/{self.total_files} files | "
              f"{rate:.1f} files/s | ETA: {eta:.0f}s", end="", flush=True)
              
    def add_dependencies(self, count: int):
        """Track dependencies found."""
        self.dependencies_found += count
        
    def add_circular_deps(self, count: int):
        """Track circular dependencies."""
        self.circular_deps_found += count
        
    def print_summary(self):
        """Print final summary statistics."""
        total_time = time.time() - self.start_time
        print(f"\n\n{'='*80}")
        print(f"{'DCRP EXECUTION SUMMARY':^80}")
        print(f"{'='*80}")
        print(f"  Total Files Analyzed:     {self.total_files:>6}")
        print(f"  Successfully Processed:   {self.processed_files:>6}")
        print(f"  Cache Hits (unchanged):   {self.cached_files:>6}")  # NEW
        print(f"  Skipped (excluded):       {self.skipped_files:>6}")
        print(f"  Errors Encountered:       {self.error_files:>6}")
        print(f"  Dependencies Detected:    {self.dependencies_found:>6}")
        print(f"  Circular Dependencies:    {self.circular_deps_found:>6}")
        print(f"  Total Execution Time:     {total_time:>6.2f}s")
        print(f"  Average Processing Rate:  {self.total_files/total_time:>6.1f} files/s")
        if self.cached_files > 0:  # NEW
            cache_rate = (self.cached_files / self.total_files) * 100
            print(f"  Cache Hit Rate:           {cache_rate:>6.1f}%")
        print(f"{'='*80}\n")

# ═══════════════════════════════════════════════════════════════════════════
#  STATE MANAGEMENT (Incremental Processing)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ProcessingState:
    """Track processing state for incremental updates."""
    file_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # rel_path -> {mtime, hash, identity}
    last_run: str = ""
    
    def save(self, path: Path):
        """Save state to JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'file_states': self.file_states,
                'last_run': datetime.now().isoformat()
            }, f, indent=2)
    
    @staticmethod
    def load(path: Path) -> 'ProcessingState':
        """Load state from JSON."""
        if not path.exists():
            return ProcessingState()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ProcessingState(
                    file_states=data.get('file_states', {}),
                    last_run=data.get('last_run', '')
                )
        except:
            return ProcessingState()
    
    def is_file_unchanged(self, rel_path: str, current_mtime: float, current_hash: str) -> bool:
        """Check if file hasn't changed since last run."""
        if rel_path not in self.file_states:
            return False
        
        state = self.file_states[rel_path]
        return (state.get('mtime') == current_mtime and 
                state.get('hash') == current_hash)
    
    def update_file(self, rel_path: str, mtime: float, content_hash: str, identity: 'FileIdentity'):
        """Update file state."""
        # Convert identity to JSON-serializable dict
        identity_dict = asdict(identity)
        # Convert Path to string
        if isinstance(identity_dict.get('path'), Path):
            identity_dict['path'] = str(identity_dict['path'])
        # Convert sets to lists
        if isinstance(identity_dict.get('dependencies'), set):
            identity_dict['dependencies'] = list(identity_dict['dependencies'])
        if isinstance(identity_dict.get('dependents'), set):
            identity_dict['dependents'] = list(identity_dict['dependents'])
        
        self.file_states[rel_path] = {
            'mtime': mtime,
            'hash': content_hash,
            'identity': identity_dict
        }

# ═══════════════════════════════════════════════════════════════════════════
#  CORE DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FileIdentity:
    """File metadata with dependency tracking."""
    path: Path
    spectral_freq: str
    primary_purpose: str
    architectural_role: str
    theatrical_essence: str
    key_exports: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)  # Relative paths as strings
    dependents: Set[str] = field(default_factory=set)
    content_hash: str = ""
    circular_with: List[List[str]] = field(default_factory=list)  # Cycles this file participates in
    last_updated: str = ""

@dataclass
class CircularCluster:
    """Group of files in circular dependency."""
    members: Set[str]
    break_edges: List[Tuple[str, str]]  # Edges to remove to break cycle
    resolution_strategy: str

# ═══════════════════════════════════════════════════════════════════════════
#  DEPENDENCY ANALYZER (AST-based for Python/Rust)
# ═══════════════════════════════════════════════════════════════════════════

class DependencyExtractor:
    """Extract dependencies using AST for code, regex for others."""
    
    @staticmethod
    def extract_python_deps(path: Path, content: str) -> Set[Path]:
        """AST-based Python dependency extraction."""
        deps = set()
        try:
            tree = ast.parse(content, filename=str(path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_path = DependencyExtractor._resolve_python_import(
                            alias.name, path, REPO_ROOT
                        )
                        if module_path:
                            deps.add(module_path)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_path = DependencyExtractor._resolve_python_import(
                            node.module, path, REPO_ROOT, is_from=True, level=node.level
                        )
                        if module_path:
                            deps.add(module_path)
        except SyntaxError:
            pass  # Silently skip unparseable files
        
        return deps
    
    @staticmethod
    def _resolve_python_import(
        module_name: str,
        current_file: Path,
        repo_root: Path,
        is_from: bool = False,
        level: int = 0
    ) -> Optional[Path]:
        """Resolve Python import to actual file path."""
        # Relative imports
        if level > 0:
            base_dir = current_file.parent
            for _ in range(level - 1):
                base_dir = base_dir.parent
            
            if module_name:
                module_parts = module_name.split('.')
                target = base_dir
                for part in module_parts:
                    target = target / part
            else:
                target = base_dir
            
            # Try .py file, then __init__.py
            if (target.with_suffix('.py')).exists():
                return target.with_suffix('.py')
            elif (target / '__init__.py').exists():
                return target / '__init__.py'
            return None
        
        # Absolute imports
        module_parts = module_name.split('.')
        
        # Try from repo root first (local packages)
        target = repo_root
        for part in module_parts:
            target = target / part
        
        if (target.with_suffix('.py')).exists():
            return target.with_suffix('.py')
        elif (target / '__init__.py').exists():
            return target / '__init__.py'
        
        # Not a local import (stdlib or site-packages)
        return None
    
    @staticmethod
    def extract_rust_deps(path: Path, content: str) -> Set[Path]:
        """Regex-based Rust dependency extraction."""
        deps = set()
        
        # Extract use statements
        use_pattern = r'use\s+((?:crate|super|self)?::)?([a-zA-Z_][\w:]*)(?:::\{[^}]+\})?;'
        for match in re.finditer(use_pattern, content):
            prefix = match.group(1) or ""
            module = match.group(2)
            
            if 'crate::' in prefix or 'super::' in prefix or 'self::' in prefix:
                # Local module reference
                module_path = DependencyExtractor._resolve_rust_use(
                    f"{prefix}{module}", path, REPO_ROOT
                )
                if module_path:
                    deps.add(module_path)
        
        return deps
    
    @staticmethod
    def _resolve_rust_use(use_path: str, current_file: Path, repo_root: Path) -> Optional[Path]:
        """Resolve Rust use statement to file path."""
        parts = use_path.replace('::', '/').split('/')
        
        if 'crate' in parts:
            # From src root
            base_dir = repo_root / 'src'
            parts = [p for p in parts if p not in ['crate', '']]
        elif 'super' in parts:
            # Up one directory
            base_dir = current_file.parent.parent
            parts = [p for p in parts if p not in ['super', '']]
        elif 'self' in parts:
            # Current directory
            base_dir = current_file.parent
            parts = [p for p in parts if p not in ['self', '']]
        else:
            return None  # External crate
        
        # Build path
        target = base_dir
        for part in parts:
            target = target / part
        
        # Try .rs or mod.rs
        if (target.with_suffix('.rs')).exists():
            return target.with_suffix('.rs')
        elif (target / 'mod.rs').exists():
            return target / 'mod.rs'
        
        return None
    
    @staticmethod
    def extract_markdown_deps(path: Path, content: str) -> Set[Path]:
        """Extract markdown link dependencies."""
        deps = set()
        
        # Find markdown links
        links = re.findall(r'\[.+?\]\((.+?)\)', content)
        for link in links:
            if link.startswith('http'):
                continue  # Skip external
            
            try:
                # Resolve relative path
                linked_path = (path.parent / link).resolve()
                if linked_path.exists() and linked_path != path:
                    deps.add(linked_path)
            except:
                pass
        
        return deps
    
    @staticmethod
    def extract_typescript_deps(path: Path, content: str) -> Set[Path]:
        """Extract TypeScript/JavaScript import dependencies."""
        deps = set()
        
        # Extract imports
        imports = re.findall(r'from\s+["\'](.+?)["\']', content)
        for imp in imports:
            if imp.startswith('.'):
                # Relative import
                try:
                    # Try with original extension, then .ts/.tsx/.js/.jsx
                    for ext in [path.suffix, '.ts', '.tsx', '.js', '.jsx']:
                        potential_dep = (path.parent / imp).with_suffix(ext)
                        if potential_dep.exists():
                            deps.add(potential_dep)
                            break
                except:
                    pass
        
        return deps
    
    @staticmethod
    def extract_dependencies(path: Path) -> Set[Path]:
        """Route to appropriate extractor based on file type."""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except:
            return set()
        
        if path.suffix == '.py':
            return DependencyExtractor.extract_python_deps(path, content)
        elif path.suffix == '.rs':
            return DependencyExtractor.extract_rust_deps(path, content)
        elif path.suffix == '.md':
            return DependencyExtractor.extract_markdown_deps(path, content)
        elif path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            return DependencyExtractor.extract_typescript_deps(path, content)
        else:
            return set()

# ═══════════════════════════════════════════════════════════════════════════
#  CIRCULAR DEPENDENCY RESOLVER
# ═══════════════════════════════════════════════════════════════════════════

class CircularDependencyResolver:
    """Detect and resolve circular dependencies using graph algorithms."""
    
    @staticmethod
    def detect_cycles(graph: nx.DiGraph) -> List[List[str]]:
        """Find all simple cycles using Johnson's algorithm."""
        try:
            return list(nx.simple_cycles(graph))
        except:
            return []
    
    @staticmethod
    def break_cycles_intelligently(
        graph: nx.DiGraph,
        cycles: List[List[str]]
    ) -> Tuple[List[CircularCluster], List[Tuple[str, str]]]:
        """
        Break cycles using fast greedy heuristic (optimized).
        
        Strategy:
        1. Find strongly connected components (SCCs) - O(V+E)
        2. For each SCC, use greedy heuristic instead of betweenness - O(E) vs O(V*E)
        3. Remove edges targeting high-degree nodes (breaks more cycles)
        """
        clusters = []
        edges_to_remove = []
        
        # Group cycles into SCCs
        sccs = list(nx.strongly_connected_components(graph))
        sccs = [scc for scc in sccs if len(scc) > 1]  # Filter single-node SCCs
        
        for scc in sccs:
            subgraph = graph.subgraph(scc).copy()
            
            # OPTIMIZATION: Use greedy heuristic instead of betweenness
            # Rationale: Removing edges to high-degree nodes breaks more cycles
            out_degrees = dict(subgraph.out_degree())
            in_degrees = dict(subgraph.in_degree())
            
            # Score each edge by target's degree (higher = more impact)
            edge_scores = {}
            for edge in subgraph.edges():
                source, target = edge
                # Score = out_degree of target (how many other nodes it reaches)
                edge_scores[edge] = out_degrees[target] + in_degrees[target]
            
            # Sort edges by score (highest first)
            sorted_edges = sorted(edge_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Remove edges until acyclic (greedy)
            temp_graph = subgraph.copy()
            removed = []
            
            for edge, score in sorted_edges:
                temp_graph.remove_edge(*edge)
                removed.append(edge)
                
                # Check if acyclic now
                if nx.is_directed_acyclic_graph(temp_graph):
                    break  # Success - no more cycles
            
            # Determine resolution strategy
            if len(scc) == 2:
                strategy = "BIDIRECTIONAL_LINK"  # Two files referencing each other
            elif len(scc) <= 5:
                strategy = "SMALL_CLUSTER"  # Tight coupling, consider refactoring
            else:
                strategy = "LARGE_COMPONENT"  # Major architectural issue
            
            cluster = CircularCluster(
                members=scc,
                break_edges=removed,
                resolution_strategy=strategy
            )
            clusters.append(cluster)
            edges_to_remove.extend(removed)
        
        return clusters, edges_to_remove
    
    @staticmethod
    def annotate_files_with_cycles(
        identities: Dict[str, FileIdentity],
        cycles: List[List[str]]
    ) -> None:
        """Add cycle membership to file identities."""
        for cycle in cycles:
            for node in cycle:
                if node in identities:
                    identities[node].circular_with.append(cycle)

# ═══════════════════════════════════════════════════════════════════════════
#  INTELLIGENT FILE SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════

class IntelligentSynthesizer:
    """ML-style synthesis of file purpose and role."""
    
    @staticmethod
    def synthesize_identity(path: Path) -> FileIdentity:
        """Generate rich file identity."""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except:
            content = ""
        
        # Compute content hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]
        
        # Base identity
        identity = FileIdentity(
            path=path,
            spectral_freq=SPECTRAL_MAP.get(path.suffix, "VIOLET"),
            primary_purpose="",
            architectural_role="",
            theatrical_essence="",
            content_hash=content_hash,
            last_updated=datetime.now().isoformat()
        )
        
        # Route to appropriate analyzer
        if path.suffix == '.py':
            IntelligentSynthesizer._synthesize_python(identity, path, content)
        elif path.suffix == '.rs':
            IntelligentSynthesizer._synthesize_rust(identity, path, content)
        elif path.suffix == '.md':
            IntelligentSynthesizer._synthesize_markdown(identity, path, content)
        elif path.suffix in ['.toml', '.json', '.yaml', '.yml']:
            IntelligentSynthesizer._synthesize_config(identity, path, content)
        elif path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            IntelligentSynthesizer._synthesize_typescript(identity, path, content)
        else:
            identity.theatrical_essence = f"{path.suffix} file: {path.name}"
            identity.architectural_role = "⚙️ UTILITY"
        
        return identity
    
    @staticmethod
    def _synthesize_python(identity: FileIdentity, path: Path, content: str):
        """Python-specific synthesis."""
        identity.architectural_role = "🌿 THE GARDEN"
        
        # Extract docstring
        doc_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if doc_match:
            identity.primary_purpose = doc_match.group(1).strip()[:200]
        
        # Extract exports
        try:
            tree = ast.parse(content)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    identity.key_exports.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    identity.key_exports.append(node.name)
        except:
            pass
        
        # Synthesize essence
        if "MCP" in content or "mcp" in content:
            identity.theatrical_essence = "Model Context Protocol server - AI governance bridge"
        elif "MILF" in content:
            identity.theatrical_essence = "MILF governance operative - matriarchal command"
        elif "decorator" in path.name.lower():
            identity.theatrical_essence = "The Decorator's cross-reference system"
        else:
            identity.theatrical_essence = f"Python module: {', '.join(identity.key_exports[:3]) if identity.key_exports else 'utility'}"
    
    @staticmethod
    def _synthesize_rust(identity: FileIdentity, path: Path, content: str):
        """Rust-specific synthesis."""
        identity.architectural_role = "🏰 THE FORTRESS"
        
        # Extract doc comment
        doc_match = re.search(r'//!\s*(.+?)(?:\n//!|\Z)', content, re.DOTALL)
        if doc_match:
            identity.primary_purpose = doc_match.group(1).strip()[:200]
        
        # Extract pub exports
        pub_items = re.findall(r'pub\s+(?:mod|struct|trait|fn|enum)\s+(\w+)', content)
        identity.key_exports = pub_items
        
        # Synthesize
        if "Vulkan" in content or "ash::" in content:
            identity.theatrical_essence = "Vulkan rendering pipeline - visual truth incarnate"
        else:
            identity.theatrical_essence = f"Rust module: {', '.join(identity.key_exports[:3]) if identity.key_exports else 'foundation'}"
    
    @staticmethod
    def _synthesize_markdown(identity: FileIdentity, path: Path, content: str):
        """Markdown-specific synthesis."""
        identity.architectural_role = "📜 DOCUMENTATION"
        
        # Extract title
        h1_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if h1_match:
            identity.primary_purpose = h1_match.group(1).strip()
        
        # Extract headers as exports
        identity.key_exports = re.findall(r'^#+\s+(.+?)$', content, re.MULTILINE)
        
        # Synthesize
        if "SSOT" in content or "copilot-instructions" in path.name:
            identity.theatrical_essence = "Single Source of Truth - Codex Brahmanica Perfectus"
        elif "ANKH" in path.name.upper():
            identity.theatrical_essence = "ANKH lineage heritage - ancestral knowledge"
        else:
            identity.theatrical_essence = f"Documentation: {identity.primary_purpose[:60] if identity.primary_purpose else path.stem}"
    
    @staticmethod
    def _synthesize_config(identity: FileIdentity, path: Path, content: str):
        """Config file synthesis."""
        identity.architectural_role = "⚙️ CONFIGURATION"
        
        if "Cargo.toml" in path.name:
            identity.theatrical_essence = "Rust dependency manifest - Fortress foundation"
        elif "pyproject.toml" in path.name:
            identity.theatrical_essence = "Python project definition - Garden configuration"
        elif "package.json" in path.name:
            identity.theatrical_essence = "Node package manifest - Observatory integration"
        else:
            identity.theatrical_essence = f"Configuration: {path.name}"
    
    @staticmethod
    def _synthesize_typescript(identity: FileIdentity, path: Path, content: str):
        """TypeScript/JavaScript synthesis."""
        identity.architectural_role = "🔭 THE OBSERVATORY"
        
        # Extract exports
        exports = re.findall(r'export\s+(?:function|class|const|interface)\s+(\w+)', content)
        identity.key_exports = exports
        
        # Synthesize
        if "dashboard" in path.name.lower():
            identity.theatrical_essence = "MCP dashboard component - visual interface"
        else:
            identity.theatrical_essence = f"TypeScript: {', '.join(identity.key_exports[:3]) if identity.key_exports else path.stem}"

# ═══════════════════════════════════════════════════════════════════════════
#  REPOSITORY SCANNER (Filesystem-aware)
# ═══════════════════════════════════════════════════════════════════════════

class RepositoryScanner:
    """Scan repository with smart filtering and incremental change detection."""
    
    @staticmethod
    def scan_repository(tracker: Optional[ProgressTracker] = None, use_cache: bool = True) -> Tuple[Dict[str, FileIdentity], Set[Path]]:
        """
        Scan all files in repository with incremental processing.
        
        Args:
            tracker: Progress tracker for real-time feedback
            use_cache: If True, skip unchanged files (faster re-runs)
        
        Returns:
            - identities: Map of relative_path -> FileIdentity
            - void_dirs: Empty directories
        """
        identities = {}
        void_dirs = set()
        
        # Load previous state for incremental processing
        state_path = REPO_ROOT / ".dcrp_state.json"
        state = ProcessingState.load(state_path) if use_cache else ProcessingState()
        
        # Single-pass filesystem traversal
        all_paths = list(REPO_ROOT.rglob('*'))
        
        if tracker:
            # Count trackable files
            trackable_count = sum(
                1 for p in all_paths
                if p.is_file()
                and not any(excluded in p.parts for excluded in EXCLUDE_DIRS)
                and p.name not in EXCLUDE_FILES
                and (p.suffix in SPECTRAL_MAP or p.suffix == '')
            )
            tracker.total_files = trackable_count
            print(f"  Discovered {trackable_count} trackable files")
            
            if use_cache and state.file_states:
                print(f"  Loading state from previous run ({len(state.file_states)} files cached)")
        
        for path in all_paths:
            # Skip excluded directories
            if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
                continue
            
            # Skip excluded files
            if path.name in EXCLUDE_FILES:
                continue
            
            if path.is_file():
                # Process trackable files
                if path.suffix in SPECTRAL_MAP or path.suffix == '':
                    try:
                        rel_path = str(path.relative_to(REPO_ROOT))
                        
                        # Check if file unchanged (incremental processing)
                        if use_cache:
                            mtime = path.stat().st_mtime
                            # Quick mtime check first
                            if rel_path in state.file_states and state.file_states[rel_path].get('mtime') == mtime:
                                # File unchanged - reuse cached identity
                                cached_data = state.file_states[rel_path]['identity'].copy()
                                # Convert string path back to Path
                                if isinstance(cached_data.get('path'), str):
                                    cached_data['path'] = Path(cached_data['path'])
                                # Convert lists back to sets
                                if isinstance(cached_data.get('dependencies'), list):
                                    cached_data['dependencies'] = set(cached_data['dependencies'])
                                if isinstance(cached_data.get('dependents'), list):
                                    cached_data['dependents'] = set(cached_data['dependents'])
                                
                                identity = FileIdentity(**cached_data)
                                identities[rel_path] = identity
                                if tracker:
                                    tracker.update_file("cached")
                                continue
                        
                        # File new or changed - full processing
                        identity = IntelligentSynthesizer.synthesize_identity(path)
                        identities[rel_path] = identity
                        
                        # Update state
                        if use_cache:
                            state.update_file(rel_path, path.stat().st_mtime, identity.content_hash, identity)
                        
                        if tracker:
                            tracker.update_file("processed")
                            
                    except Exception as e:
                        if tracker:
                            tracker.update_file("error")
                        print(f"\n  ⚠️  Error processing {path.name}: {e}", flush=True)
            
            elif path.is_dir():
                # Check for void directories
                children = list(path.iterdir())
                if not children or all(c.name.startswith('.') for c in children):
                    void_dirs.add(path)
        
        # Save updated state
        if use_cache:
            state.save(state_path)
        
        return identities, void_dirs

# ═══════════════════════════════════════════════════════════════════════════
#  DEPENDENCY GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════════

class DependencyGraphBuilder:
    """Build and analyze dependency graph."""
    
    @staticmethod
    def build_graph(identities: Dict[str, FileIdentity], tracker: Optional[ProgressTracker] = None) -> nx.DiGraph:
        """Build directed graph from file identities."""
        G = nx.DiGraph()
        
        if tracker:
            print(f"  Adding {len(identities)} nodes to graph...", flush=True)
        
        # Add nodes
        for rel_path, identity in identities.items():
            G.add_node(
                rel_path,
                spectral_freq=identity.spectral_freq,
                role=identity.architectural_role,
                essence=identity.theatrical_essence,
                exports_count=len(identity.key_exports)
            )
        
        # Extract dependencies for all files
        path_to_relpath = {identity.path: rel_path for rel_path, identity in identities.items()}
        
        if tracker:
            print(f"  Extracting dependencies from {len(identities)} files...", flush=True)
            dep_count = 0
        
        for i, (rel_path, identity) in enumerate(identities.items()):
            deps = DependencyExtractor.extract_dependencies(identity.path)
            
            # Convert Path objects to relative paths
            for dep_path in deps:
                try:
                    dep_rel = str(dep_path.relative_to(REPO_ROOT))
                    if dep_rel in identities:
                        G.add_edge(rel_path, dep_rel, method="AST")
                        identity.dependencies.add(dep_rel)
                        if tracker:
                            dep_count += 1
                except:
                    pass
            
            # Progress update every 100 files
            if tracker and (i + 1) % 100 == 0:
                print(f"  Progress: {i+1}/{len(identities)} files, {dep_count} dependencies found", flush=True)
        
        # Compute reverse dependencies (dependents)
        for rel_path, identity in identities.items():
            for dep in identity.dependencies:
                if dep in identities:
                    identities[dep].dependents.add(rel_path)
        
        return G

# ═══════════════════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generate analysis reports."""
    
    @staticmethod
    def generate_summary(
        identities: Dict[str, FileIdentity],
        graph: nx.DiGraph,
        cycles: List[List[str]],
        clusters: List[CircularCluster],
        void_dirs: Set[Path]
    ) -> str:
        """Generate comprehensive analysis report."""
        lines = []
        
        lines.append("# DCRP Production Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().isoformat()}")
        lines.append(f"**Engine:** The Decorator's Production Cross-Reference Protocol v3")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # === OVERVIEW ===
        lines.append("## I. Repository Overview")
        lines.append("")
        lines.append(f"- **Total Files:** {len(identities)}")
        lines.append(f"- **Graph Nodes:** {graph.number_of_nodes()}")
        lines.append(f"- **Dependencies (Edges):** {graph.number_of_edges()}")
        lines.append(f"- **Void Directories:** {len(void_dirs)}")
        lines.append(f"- **Circular Dependencies:** {len(cycles)}")
        lines.append(f"- **Circular Clusters:** {len(clusters)}")
        lines.append("")
        
        # === DEPENDENCY METRICS ===
        lines.append("## II. Dependency Metrics")
        lines.append("")
        
        in_degree = dict(graph.in_degree())
        top_depended = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:15]
        
        lines.append("### Most Depended-Upon Files")
        lines.append("")
        lines.append("| File | Dependents |")
        lines.append("|------|------------|")
        for file, count in top_depended:
            if count > 0:
                lines.append(f"| `{file}` | {count} |")
        lines.append("")
        
        # === CIRCULAR DEPENDENCIES ===
        if cycles:
            lines.append("## III. Circular Dependencies (CRITICAL)")
            lines.append("")
            lines.append(f"⚠️  **{len(cycles)} circular dependencies detected**")
            lines.append("")
            
            for idx, cycle in enumerate(cycles[:10], 1):
                lines.append(f"### Cycle {idx}")
                lines.append("")
                lines.append("```")
                for i, node in enumerate(cycle):
                    lines.append(f"{node}")
                    if i < len(cycle) - 1:
                        lines.append("  ↓")
                lines.append(f"  ↓ (back to {cycle[0]})")
                lines.append("```")
                lines.append("")
        else:
            lines.append("## III. Circular Dependencies")
            lines.append("")
            lines.append("✅ **No circular dependencies detected**")
            lines.append("")
        
        # === RESOLUTION STRATEGY ===
        if clusters:
            lines.append("## IV. Circular Cluster Resolution")
            lines.append("")
            
            for idx, cluster in enumerate(clusters, 1):
                lines.append(f"### Cluster {idx} - {cluster.resolution_strategy}")
                lines.append("")
                lines.append(f"**Members:** {len(cluster.members)}")
                lines.append("")
                lines.append("**Edges to Break:**")
                for edge in cluster.break_edges:
                    lines.append(f"- `{edge[0]}` → `{edge[1]}`")
                lines.append("")
        
        # === SPECTRAL DISTRIBUTION ===
        lines.append("## V. Spectral Frequency Distribution")
        lines.append("")
        
        freq_counts = defaultdict(int)
        for identity in identities.values():
            freq_counts[identity.spectral_freq] += 1
        
        lines.append("| Frequency | Count | Meaning |")
        lines.append("|-----------|-------|---------|")
        for freq in ["RED", "ORANGE", "GOLD", "BLUE", "WHITE", "INDIGO", "VIOLET"]:
            if freq in freq_counts:
                meanings = {
                    "RED": "Rust - Raw alchemical force",
                    "ORANGE": "TypeScript - Strategic bridge",
                    "GOLD": "Markdown - Documentation perfection",
                    "BLUE": "Config - Structural verification",
                    "WHITE": "Python - Visual integrity",
                    "INDIGO": "Shaders - Pattern recognition",
                    "VIOLET": "Misc - Forbidden potential"
                }
                lines.append(f"| {freq} | {freq_counts[freq]} | {meanings[freq]} |")
        lines.append("")
        
        return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="The Decorator's Production DCRP")
    parser.add_argument('--dry-run', action='store_true', help='Analysis only, no file modification')
    parser.add_argument('--inject', action='store_true', help='Inject cross-reference headers into files')
    parser.add_argument('--force-full-scan', action='store_true', help='Bypass cache, scan all files')
    args = parser.parse_args()
    
    # Set UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 80)
    print("  THE DECORATOR'S PRODUCTION CROSS-REFERENCE PROTOCOL (v3)")
    print("  Self-Updating | Circular Resolution | Zero-Drift Architecture")
    print("=" * 80)
    print()
    
    # Initialize progress tracker
    tracker = ProgressTracker()
    
    # STEP 1: Scan repository
    tracker.set_phase("STEP 1: Repository Scanning")
    use_cache = not args.force_full_scan  # Use cache unless forced
    identities, void_dirs = RepositoryScanner.scan_repository(tracker, use_cache=use_cache)
    tracker.total_files = len(identities)
    print(f"\n  ✓ Discovered {len(identities)} files, {len(void_dirs)} void directories")
    if tracker.cached_files > 0:
        cache_pct = (tracker.cached_files / len(identities)) * 100
        print(f"  ✓ Cache hits: {tracker.cached_files} files ({cache_pct:.1f}%) - incremental processing active")
    print()
    
    # STEP 2: Build dependency graph
    tracker.set_phase("STEP 2: Dependency Graph Construction")
    graph = DependencyGraphBuilder.build_graph(identities, tracker)
    tracker.add_dependencies(graph.number_of_edges())
    print(f"\n  ✓ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print()
    
    # STEP 3: Detect circular dependencies
    tracker.set_phase("STEP 3: Circular Dependency Detection")
    resolver = CircularDependencyResolver()
    cycles = resolver.detect_cycles(graph)
    
    if cycles:
        tracker.add_circular_deps(len(cycles))
        print(f"\n  ⚠️  FOUND {len(cycles)} circular dependency chains")
        clusters, edges_to_break = resolver.break_cycles_intelligently(graph, cycles)
        print(f"  ✓ Identified {len(clusters)} circular clusters")
        print(f"  ✓ Proposed {len(edges_to_break)} edges to break")
        
        # Validate cycle breaking
        print(f"\n  🔍 Validating cycle resolution...")
        for i, cluster in enumerate(clusters):
            print(f"    Cluster {i+1}/{len(clusters)}: {len(cluster.members)} files, "
                  f"breaking {len(cluster.break_edges)} edges via {cluster.resolution_strategy}")
        
        resolver.annotate_files_with_cycles(identities, cycles)
    else:
        print(f"\n  ✅ No circular dependencies detected - graph is acyclic")
        clusters = []
    print()
    
    # STEP 4: Generate reports
    tracker.set_phase("STEP 4: Analysis Report Generation")
    
    # Record evolution snapshot
    cache_hit_rate = (tracker.cached_files / len(identities) * 100) if len(identities) > 0 else 0
    snapshot = EvolutionTracker.record_snapshot(identities, graph, cycles, clusters, cache_hit_rate)
    print(f"\n  ✓ Evolution snapshot recorded: {snapshot.timestamp}")
    
    # Generate base report
    report = ReportGenerator.generate_summary(identities, graph, cycles, clusters, void_dirs)
    
    # Append evolution report
    history = EvolutionTracker.load_history()
    if len(history) >= 2:
        evolution_report = EvolutionTracker.generate_evolution_report(history)
        report = report + "\n" + evolution_report
        print(f"  ✓ Evolution tracking: {len(history)} historical snapshots")
    
    report_path = REPO_ROOT / "DCRP_PRODUCTION_ANALYSIS.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"  ✓ Markdown Report: {report_path}")
    
    # Export graph with validation metadata
    graph_data = nx.node_link_data(graph)
    graph_data['metadata'] = {
        'generated_at': datetime.now().isoformat(),
        'total_files': len(identities),
        'total_dependencies': graph.number_of_edges(),
        'cycles_detected': len(cycles),
        'cycles': cycles,
        'clusters': [
            {
                'members': list(c.members),
                'break_edges': c.break_edges,
                'strategy': c.resolution_strategy
            }
            for c in clusters
        ],
        'void_dirs': [str(p.relative_to(REPO_ROOT)) for p in void_dirs],
        'validation': {
            'graph_is_connected': nx.is_weakly_connected(graph),
            'graph_is_dag': nx.is_directed_acyclic_graph(graph) if not cycles else False,
            'largest_component_size': len(max(nx.weakly_connected_components(graph), key=len)),
        }
    }
    
    graph_path = REPO_ROOT / "dependency_graph_production.json"
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    print(f"  ✓ Graph JSON: {graph_path}")
    
    # Print validation results
    print(f"\n  🔍 Graph Validation:")
    print(f"    - Is weakly connected: {graph_data['metadata']['validation']['graph_is_connected']}")
    print(f"    - Is DAG (acyclic): {graph_data['metadata']['validation']['graph_is_dag']}")
    print(f"    - Largest component: {graph_data['metadata']['validation']['largest_component_size']} files")
    print()
    
    # STEP 5: File injection (if requested)
    if args.inject and not args.dry_run:
        tracker.set_phase("STEP 5: Cross-Reference Header Injection")
        print("  ⚠️  FILE INJECTION NOT YET IMPLEMENTED")
        print("  ⚠️  (Requires header generation logic)")
        print()
    
    # Print final summary
    tracker.print_summary()
    
    print("=" * 80)
    print(" PRODUCTION DCRP COMPLETE")
    print("=" * 80)
    print()
    print(f"Execution Mode: {'DRY RUN (no modifications)' if args.dry_run else 'ANALYSIS ONLY'}")
    print(f"Next Steps:")
    print(f"  1. Review {report_path}")
    print(f"  2. Validate circular dependency resolutions")
    print(f"  3. Run with --inject to apply cross-reference headers (when implemented)")
    print()

if __name__ == "__main__":
    main()
