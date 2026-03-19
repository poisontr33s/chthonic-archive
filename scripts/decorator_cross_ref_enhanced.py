#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: decorator_cross_ref_enhanced.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
╔══════════════════════════════════════════════════════════════════════════════
║  THE DECORATOR'S ENHANCED CROSS-REFERENCE PROTOCOL (DCRP v2)
║  Deep AST Analysis + Circular Dependency Detection
║
║  Purpose: Enhanced dependency mapping using Abstract Syntax Tree parsing
║           for Python/Rust + NetworkX algorithms for circular detection
║
║  Invocation: uv run python decorator_cross_ref_enhanced.py
║
║  The Decorator's Enhancement: "See deeper. Map stronger. Detect cycles."
╚══════════════════════════════════════════════════════════════════════════════

@SID:           TOOL_DECORATOR_CROSS_REF_ENHANCED_V1
@Shabti:        CLI Script
@Purpose:       ╔══════════════════════════════════════════════════════════════════════════════
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.ssot_paths import resolve_ssot_paths
_SSOT = resolve_ssot_paths(REPO_ROOT)
SSOT_PATH = _SSOT.pointer

EXCLUDE_DIRS = {
    "node_modules", ".git", "build", ".cache", ".cargo", 
    "__pycache__", ".venv", "target", "dist", ".venv-py314-parked"
}

EXCLUDE_FILES = {
    "temp_repo_structure.json",
    ".DS_Store", "Thumbs.db"
}

# Spectral frequency mapping (PRISM - ROGBIV)
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
#  ENHANCED DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ImportStatement:
    """Detailed import/use statement metadata."""
    module: str
    items: List[str]  # Specific imports (e.g., ['Path', 'Dict'] from pathlib)
    is_relative: bool  # True for relative imports (from . or ..)
    alias: Optional[str] = None  # Import alias (e.g., 'as np')
    line_number: int = 0

@dataclass
class DirectoryIdentity:
    """Empty/void directory metadata."""
    path: Path
    intended_purpose: str
    architectural_significance: str

@dataclass
class FileIdentity:
    """Enhanced file identity with AST-derived metadata."""
    path: Path
    spectral_freq: str
    primary_purpose: str
    architectural_role: str
    key_exports: List[str] = field(default_factory=list)
    dependencies: Set[Path] = field(default_factory=set)
    dependents: Set[Path] = field(default_factory=set)
    import_statements: List[ImportStatement] = field(default_factory=list)
    exported_symbols: Dict[str, str] = field(default_factory=dict)  # name -> type (class/function/constant)
    content_hash: str = ""
    theatrical_essence: str = ""
    circular_dependencies: List[List[str]] = field(default_factory=list)  # Cycles this file participates in

# ═══════════════════════════════════════════════════════════════════════════
#  AST-BASED PYTHON ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class PythonASTAnalyzer:
    """Deep Python analysis using Abstract Syntax Tree parsing."""
    
    @staticmethod
    def analyze(path: Path, content: str) -> Tuple[List[ImportStatement], Dict[str, str]]:
        """Extract imports and exports via AST parsing."""
        imports = []
        exports = {}
        
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as e:
            print(f"  ⚠️  Syntax error in {path.name}: {e}")
            return imports, exports
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportStatement(
                        module=alias.name,
                        items=[],
                        is_relative=False,
                        alias=alias.asname,
                        line_number=node.lineno
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Not "from . import"
                    items = [alias.name for alias in node.names]
                    imports.append(ImportStatement(
                        module=node.module,
                        items=items,
                        is_relative=(node.level > 0),
                        line_number=node.lineno
                    ))
        
        # Extract top-level exports (classes, functions, constants)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                exports[node.name] = "class"
            elif isinstance(node, ast.FunctionDef):
                exports[node.name] = "function"
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if constant (ALL_CAPS convention)
                        if target.id.isupper():
                            exports[target.id] = "constant"
        
        return imports, exports
    
    @staticmethod
    def resolve_import_to_path(
        import_stmt: ImportStatement,
        current_file: Path,
        repo_root: Path
    ) -> Optional[Path]:
        """Resolve import statement to actual file path."""
        if import_stmt.is_relative:
            # Relative import: resolve from current directory
            base_dir = current_file.parent
            module_parts = import_stmt.module.split('.') if import_stmt.module else []
            
            # Navigate up directories based on import level
            # (Note: would need to track level from AST for full accuracy)
            potential_path = base_dir
            for part in module_parts:
                potential_path = potential_path / part
            
            # Try .py file first, then __init__.py
            if (potential_path.with_suffix('.py')).exists():
                return potential_path.with_suffix('.py')
            elif (potential_path / '__init__.py').exists():
                return potential_path / '__init__.py'
        
        else:
            # Absolute import: search from repo root
            module_parts = import_stmt.module.split('.')
            potential_path = repo_root
            
            for part in module_parts:
                potential_path = potential_path / part
            
            # Try .py file first, then __init__.py
            if (potential_path.with_suffix('.py')).exists():
                return potential_path.with_suffix('.py')
            elif (potential_path / '__init__.py').exists():
                return potential_path / '__init__.py'
        
        return None

# ═══════════════════════════════════════════════════════════════════════════
#  ENHANCED RUST ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class RustAnalyzer:
    """Enhanced Rust analysis with better mod/use detection."""
    
    @staticmethod
    def analyze(path: Path, content: str) -> Tuple[List[ImportStatement], Dict[str, str]]:
        """Extract use statements and pub exports."""
        imports = []
        exports = {}
        
        # Extract use statements (more precise regex)
        use_pattern = r'use\s+((?:crate|super|self)?::)?([a-zA-Z_][\w:]*)(?:::\{([^}]+)\})?;'
        for match in re.finditer(use_pattern, content):
            prefix = match.group(1) or ""
            module = match.group(2)
            items_group = match.group(3)
            
            items = []
            if items_group:
                items = [i.strip() for i in items_group.split(',')]
            
            full_module = f"{prefix}{module}".replace('::', '/')
            
            imports.append(ImportStatement(
                module=full_module,
                items=items,
                is_relative=('crate::' in prefix or 'super::' in prefix or 'self::' in prefix)
            ))
        
        # Extract pub exports
        pub_exports = re.findall(
            r'pub\s+(?:mod|struct|trait|fn|enum|const|static)\s+(\w+)',
            content
        )
        for export in pub_exports:
            exports[export] = "pub_item"
        
        return imports, exports
    
    @staticmethod
    def resolve_use_to_path(
        import_stmt: ImportStatement,
        current_file: Path,
        repo_root: Path
    ) -> Optional[Path]:
        """Resolve Rust use statement to file path."""
        module_path = import_stmt.module.replace('/', '::')
        
        if import_stmt.is_relative:
            # Relative: resolve from current src directory
            base_dir = current_file.parent
            parts = module_path.split('::')
            
            # Navigate based on crate/super/self
            if 'crate::' in module_path:
                # Start from src root
                base_dir = repo_root / 'src'
                parts = [p for p in parts if p not in ['crate', '']]
            elif 'super::' in module_path:
                # Go up one directory
                base_dir = current_file.parent.parent
                parts = [p for p in parts if p not in ['super', '']]
            elif 'self::' in module_path:
                # Same directory
                parts = [p for p in parts if p not in ['self', '']]
            
            # Build path
            potential_path = base_dir
            for part in parts:
                potential_path = potential_path / part
            
            # Try .rs file or mod.rs
            if (potential_path.with_suffix('.rs')).exists():
                return potential_path.with_suffix('.rs')
            elif (potential_path / 'mod.rs').exists():
                return potential_path / 'mod.rs'
        
        return None

# ═══════════════════════════════════════════════════════════════════════════
#  ENHANCED ML SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════

class EnhancedMLSynthesizer:
    """Enhanced synthesis with AST-based dependency detection."""
    
    def __init__(self, ssot_content: str):
        self.ssot = ssot_content
        self.python_analyzer = PythonASTAnalyzer()
        self.rust_analyzer = RustAnalyzer()
    
    def synthesize_python_identity(self, path: Path, content: str) -> FileIdentity:
        """Enhanced Python analysis with AST."""
        identity = FileIdentity(
            path=path,
            spectral_freq="WHITE",
            primary_purpose="",
            architectural_role="🌿 THE GARDEN"
        )
        
        # AST-based analysis
        imports, exports = self.python_analyzer.analyze(path, content)
        identity.import_statements = imports
        identity.exported_symbols = exports
        identity.key_exports = list(exports.keys())
        
        # Resolve imports to file paths
        for import_stmt in imports:
            resolved_path = self.python_analyzer.resolve_import_to_path(
                import_stmt, path, REPO_ROOT
            )
            if resolved_path and resolved_path.exists():
                identity.dependencies.add(resolved_path)
        
        # Extract module docstring
        docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if docstring_match:
            identity.primary_purpose = docstring_match.group(1).strip()
        
        # Synthesize essence
        if "MCP" in content or "mcp" in content:
            identity.theatrical_essence = "Model Context Protocol server - AI governance bridge"
        elif "MILF" in content:
            identity.theatrical_essence = "MILF governance operative - matriarchal command structure"
        elif "GPU" in content or "cuda" in content.lower():
            identity.theatrical_essence = "GPU execution lane - computational muscle"
        else:
            identity.theatrical_essence = f"Python module: {', '.join(list(exports.keys())[:3]) if exports else 'operational utility'}"
        
        return identity
    
    def synthesize_rust_identity(self, path: Path, content: str) -> FileIdentity:
        """Enhanced Rust analysis."""
        identity = FileIdentity(
            path=path,
            spectral_freq="RED",
            primary_purpose="",
            architectural_role="🏰 THE FORTRESS"
        )
        
        # Rust analysis
        imports, exports = self.rust_analyzer.analyze(path, content)
        identity.import_statements = imports
        identity.exported_symbols = exports
        identity.key_exports = list(exports.keys())
        
        # Resolve use statements
        for import_stmt in imports:
            resolved_path = self.rust_analyzer.resolve_use_to_path(
                import_stmt, path, REPO_ROOT
            )
            if resolved_path and resolved_path.exists():
                identity.dependencies.add(resolved_path)
        
        # Extract doc comment
        doc_match = re.search(r'//!\s*(.+?)(?:\n//!|\Z)', content, re.DOTALL)
        if doc_match:
            identity.primary_purpose = doc_match.group(1).strip()
        
        # Synthesize essence
        if "Vulkan" in content or "ash::" in content:
            identity.theatrical_essence = "Vulkan rendering pipeline - visual truth incarnate"
        elif "bevy_ecs" in content:
            identity.theatrical_essence = "Entity Component System - the skeleton of reality"
        else:
            identity.theatrical_essence = f"Rust module: {', '.join(list(exports.keys())[:3]) if exports else 'foundational structure'}"
        
        return identity
    
    def synthesize_markdown_identity(self, path: Path, content: str) -> FileIdentity:
        """Analyze Markdown - GOLD frequency (documentation perfection)."""
        identity = FileIdentity(
            path=path,
            spectral_freq="GOLD",
            primary_purpose="",
            architectural_role="📜 DOCUMENTATION"
        )
        
        # Extract first H1 or first paragraph as primary purpose
        h1_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if h1_match:
            identity.primary_purpose = h1_match.group(1).strip()
        else:
            # First non-empty line
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            if lines:
                identity.primary_purpose = lines[0][:100]
        
        # Extract all headers as "key exports" (sections)
        identity.key_exports = re.findall(r'^#+\s+(.+?)$', content, re.MULTILINE)
        identity.exported_symbols = {h: "section" for h in identity.key_exports}
        
        # Detect markdown links as dependencies
        links = re.findall(r'\[.+?\]\((.+?)\)', content)
        for link in links:
            # Skip external URLs
            if link.startswith('http'):
                continue
            # Resolve relative path
            try:
                linked_path = (path.parent / link).resolve()
                if linked_path.exists() and linked_path != path:
                    identity.dependencies.add(linked_path)
            except:
                pass
        
        # Synthesize essence
        if "SSOT" in content or "copilot-instructions" in path.name:
            identity.theatrical_essence = "Single Source of Truth - the Codex Brahmanica Perfectus"
        elif "README" in path.name.upper():
            identity.theatrical_essence = "Entry portal - first architectural revelation"
        elif "DEVELOPMENT" in path.name.upper():
            identity.theatrical_essence = "Development chronicle - perpetual evolution tracker"
        elif "ANKH" in path.name.upper():
            identity.theatrical_essence = "ANKH lineage heritage - ancestral knowledge vessel"
        else:
            identity.theatrical_essence = f"Documentation: {identity.primary_purpose[:60] if identity.primary_purpose else 'architectural guidance'}"
        
        return identity
    
    def synthesize_config_identity(self, path: Path, content: str) -> FileIdentity:
        """Analyze config files - BLUE frequency (structural verification)."""
        identity = FileIdentity(
            path=path,
            spectral_freq="BLUE",
            primary_purpose="",
            architectural_role="⚙️ CONFIGURATION"
        )
        
        # TOML parsing
        if path.suffix == '.toml':
            # Extract package name and description
            name_match = re.search(r'name\s*=\s*"(.+?)"', content)
            desc_match = re.search(r'description\s*=\s*"(.+?)"', content)
            
            if name_match:
                identity.primary_purpose = name_match.group(1)
            if desc_match:
                identity.theatrical_essence = desc_match.group(1)
            
            # Detect dependencies
            if "Cargo.toml" in path.name:
                deps = re.findall(r'(\w+)\s*=.*', content)
                identity.key_exports = deps
                identity.exported_symbols = {d: "dependency" for d in deps}
            elif "pyproject.toml" in path.name:
                deps = re.findall(r'"([\w-]+)[><=]', content)
                identity.key_exports = deps
                identity.exported_symbols = {d: "dependency" for d in deps}
        
        # JSON parsing
        elif path.suffix == '.json':
            try:
                data = json.loads(content)
                if 'name' in data:
                    identity.primary_purpose = data['name']
                if 'description' in data:
                    identity.theatrical_essence = data['description']
                if 'dependencies' in data:
                    identity.key_exports = list(data['dependencies'].keys())
                    identity.exported_symbols = {d: "dependency" for d in identity.key_exports}
            except:
                pass
        
        # Synthesize if not already set
        if not identity.theatrical_essence:
            if "Cargo.toml" in path.name:
                identity.theatrical_essence = "Rust dependency manifest - Fortress foundation"
            elif "pyproject.toml" in path.name:
                identity.theatrical_essence = "Python project definition - Garden configuration"
            elif "package.json" in path.name:
                identity.theatrical_essence = "Node package manifest - Observatory integration"
            else:
                identity.theatrical_essence = f"Configuration: {path.name}"
        
        return identity
    
    def synthesize_typescript_identity(self, path: Path, content: str) -> FileIdentity:
        """Analyze TypeScript/JavaScript - ORANGE frequency (strategic bridge)."""
        identity = FileIdentity(
            path=path,
            spectral_freq="ORANGE",
            primary_purpose="",
            architectural_role="🔭 THE OBSERVATORY"
        )
        
        # Extract JSDoc or first comment
        doc_match = re.search(r'/\*\*(.+?)\*/', content, re.DOTALL)
        if doc_match:
            identity.primary_purpose = doc_match.group(1).strip()
        
        # Extract exports
        exports = re.findall(r'export\s+(?:function|class|const|interface)\s+(\w+)', content)
        identity.key_exports = exports
        identity.exported_symbols = {e: "export" for e in exports}
        
        # Detect imports
        imports = re.findall(r'from\s+["\'](.+?)["\']', content)
        for imp in imports:
            if imp.startswith('.'):
                # Relative import
                try:
                    potential_dep = (path.parent / imp).with_suffix(path.suffix)
                    if potential_dep.exists():
                        identity.dependencies.add(potential_dep)
                except:
                    pass
        
        # Synthesize
        if "dashboard" in path.name.lower():
            identity.theatrical_essence = "MCP dashboard component - visual monitoring interface"
        elif "mcp" in content.lower():
            identity.theatrical_essence = "MCP client integration - Observatory communication layer"
        else:
            identity.theatrical_essence = f"TypeScript module: {', '.join(identity.key_exports[:3]) if identity.key_exports else 'frontend utility'}"
        
        return identity
    
    def synthesize_identity(self, path: Path) -> FileIdentity:
        """Route to appropriate analyzer based on file type."""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"  ⚠️  Could not read {path.name}: {e}")
            return FileIdentity(
                path=path,
                spectral_freq=SPECTRAL_MAP.get(path.suffix, "VIOLET"),
                primary_purpose="",
                architectural_role="⚙️ UTILITY"
            )
        
        # Route to appropriate synthesizer
        if path.suffix == '.py':
            return self.synthesize_python_identity(path, content)
        elif path.suffix == '.rs':
            return self.synthesize_rust_identity(path, content)
        elif path.suffix == '.md':
            return self.synthesize_markdown_identity(path, content)
        elif path.suffix in ['.toml', '.json', '.yaml', '.yml']:
            return self.synthesize_config_identity(path, content)
        elif path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            return self.synthesize_typescript_identity(path, content)
        else:
            # Fallback to basic analysis
            return FileIdentity(
                path=path,
                spectral_freq=SPECTRAL_MAP.get(path.suffix, "VIOLET"),
                primary_purpose="",
                architectural_role="⚙️ UTILITY",
                theatrical_essence=f"{path.suffix} file: {path.name}"
            )

# ═══════════════════════════════════════════════════════════════════════════
#  CIRCULAR DEPENDENCY DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class CircularDependencyDetector:
    """Uses NetworkX algorithms to detect and analyze circular dependencies."""
    
    @staticmethod
    def detect_cycles(graph: nx.DiGraph) -> List[List[str]]:
        """Find all simple cycles in the dependency graph."""
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except Exception as e:
            print(f"  ⚠️  Error detecting cycles: {e}")
            return []
    
    @staticmethod
    def analyze_strongly_connected_components(graph: nx.DiGraph) -> List[Set[str]]:
        """Find strongly connected components (potential circular dependency clusters)."""
        try:
            sccs = list(nx.strongly_connected_components(graph))
            # Filter out single-node components
            return [scc for scc in sccs if len(scc) > 1]
        except Exception as e:
            print(f"  ⚠️  Error analyzing SCCs: {e}")
            return []
    
    @staticmethod
    def annotate_identities_with_cycles(
        identities: List[FileIdentity],
        cycles: List[List[str]]
    ) -> None:
        """Add circular dependency information to file identities."""
        path_to_identity = {str(f.path.relative_to(REPO_ROOT)): f for f in identities}
        
        for cycle in cycles:
            for node in cycle:
                if node in path_to_identity:
                    path_to_identity[node].circular_dependencies.append(cycle)

# ═══════════════════════════════════════════════════════════════════════════
#  ENHANCED DEPENDENCY GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def build_enhanced_dependency_graph(identities: List[FileIdentity]) -> nx.DiGraph:
    """Build graph with AST-derived dependencies."""
    G = nx.DiGraph()
    
    # Add nodes
    for identity in identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        G.add_node(
            rel_path,
            spectral_freq=identity.spectral_freq,
            purpose=identity.primary_purpose,
            role=identity.architectural_role,
            essence=identity.theatrical_essence,
            exports=list(identity.exported_symbols.keys()),
            import_count=len(identity.import_statements)
        )
    
    # Add edges from AST-detected dependencies
    for identity in identities:
        source = str(identity.path.relative_to(REPO_ROOT))
        for dep in identity.dependencies:
            try:
                target = str(dep.relative_to(REPO_ROOT))
                if G.has_node(target):
                    G.add_edge(source, target, method="AST")
            except:
                pass
    
    return G

# ═══════════════════════════════════════════════════════════════════════════
#  ENHANCED REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_enhanced_analysis_report(
    identities: List[FileIdentity],
    graph: nx.DiGraph,
    cycles: List[List[str]],
    sccs: List[Set[str]]
) -> str:
    """Generate comprehensive analysis report."""
    lines = []
    
    lines.append("# DCRP ENHANCED ANALYSIS REPORT")
    lines.append("")
    lines.append("**Generated by The Decorator's Enhanced Cross-Reference Protocol (v2)**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # === OVERVIEW ===
    lines.append("## I. Repository Statistics")
    lines.append("")
    lines.append(f"- **Total Files Analyzed:** {len(identities)}")
    lines.append(f"- **Graph Nodes:** {graph.number_of_nodes()}")
    lines.append(f"- **Graph Edges (Dependencies):** {graph.number_of_edges()}")
    lines.append(f"- **Circular Dependencies Detected:** {len(cycles)}")
    lines.append(f"- **Strongly Connected Components:** {len(sccs)}")
    lines.append("")
    
    # === DEPENDENCY METRICS ===
    lines.append("## II. Dependency Metrics")
    lines.append("")
    
    # Most depended-upon files
    in_degree = dict(graph.in_degree())
    top_depended = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:20]
    
    lines.append("### Top 20 Most Depended-Upon Files")
    lines.append("")
    lines.append("| Rank | File | Dependents |")
    lines.append("|------|------|------------|")
    for rank, (file, count) in enumerate(top_depended, 1):
        if count > 0:
            lines.append(f"| {rank} | `{file}` | {count} |")
    lines.append("")
    
    # Most dependency-heavy files
    out_degree = dict(graph.out_degree())
    top_dependencies = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:20]
    
    lines.append("### Top 20 Files With Most Dependencies")
    lines.append("")
    lines.append("| Rank | File | Dependencies |")
    lines.append("|------|------|--------------|")
    for rank, (file, count) in enumerate(top_dependencies, 1):
        if count > 0:
            lines.append(f"| {rank} | `{file}` | {count} |")
    lines.append("")
    
    # === CIRCULAR DEPENDENCIES ===
    lines.append("## III. Circular Dependency Analysis")
    lines.append("")
    
    if cycles:
        lines.append(f"**⚠️  CRITICAL: {len(cycles)} circular dependencies detected**")
        lines.append("")
        lines.append("Circular dependencies can cause:")
        lines.append("- Build order ambiguity")
        lines.append("- Runtime initialization issues")
        lines.append("- Maintenance complexity")
        lines.append("")
        
        for idx, cycle in enumerate(cycles[:10], 1):  # Show first 10
            lines.append(f"### Cycle {idx} ({len(cycle)} files)")
            lines.append("")
            lines.append("```")
            for i, node in enumerate(cycle):
                if i < len(cycle) - 1:
                    lines.append(f"{node}")
                    lines.append("  ↓ depends on")
                else:
                    lines.append(f"{node}")
                    lines.append(f"  ↓ depends on {cycle[0]} (CYCLE)")
            lines.append("```")
            lines.append("")
    else:
        lines.append("✅ **No circular dependencies detected**")
        lines.append("")
    
    # === STRONGLY CONNECTED COMPONENTS ===
    lines.append("## IV. Strongly Connected Components")
    lines.append("")
    
    if sccs:
        lines.append(f"Found {len(sccs)} strongly connected component(s):")
        lines.append("")
        for idx, scc in enumerate(sccs, 1):
            lines.append(f"### SCC {idx} ({len(scc)} files)")
            lines.append("")
            for node in sorted(scc)[:10]:  # Show first 10 files
                lines.append(f"- `{node}`")
            if len(scc) > 10:
                lines.append(f"- ... and {len(scc) - 10} more files")
            lines.append("")
    else:
        lines.append("✅ No strongly connected components (acyclic graph)")
        lines.append("")
    
    # === SPECTRAL FREQUENCY DISTRIBUTION ===
    lines.append("## V. Spectral Frequency Distribution (PRISM)")
    lines.append("")
    
    freq_counts = defaultdict(int)
    for identity in identities:
        freq_counts[identity.spectral_freq] += 1
    
    lines.append("| Frequency | Count | Meaning |")
    lines.append("|-----------|-------|---------|")
    for freq in ["RED", "ORANGE", "GOLD", "BLUE", "WHITE", "INDIGO", "VIOLET"]:
        if freq in freq_counts:
            meaning = {
                "RED": "Raw alchemical force (Rust)",
                "ORANGE": "Strategic re-contextualization (TypeScript)",
                "GOLD": "Qualitative transcendence (Documentation)",
                "BLUE": "Structural verification (Config)",
                "WHITE": "Visual integrity (Python)",
                "INDIGO": "Deep pattern recognition (Shaders)",
                "VIOLET": "Forbidden potential (Empty/misc)"
            }.get(freq, "Unknown")
            lines.append(f"| {freq} | {freq_counts[freq]} | {meaning} |")
    lines.append("")
    
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("  THE DECORATOR'S ENHANCED CROSS-REFERENCE PROTOCOL (v2)")
    print("  Deep AST Analysis + Circular Dependency Detection + Multi-Format Support")
    print("=" * 80)
    print()
    
    # Initialize synthesizer
    if SSOT_PATH.exists():
        ssot_content = SSOT_PATH.read_text(encoding='utf-8')
    else:
        ssot_content = ""
    
    synthesizer = EnhancedMLSynthesizer(ssot_content)
    
    # Scan repository (ALL file types, enhanced analysis for source files)
    print("Scanning repository with multi-format support...")
    identities = []
    dir_identities = []
    
    for path in REPO_ROOT.rglob('*'):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
            continue
        
        # Skip excluded files
        if path.name in EXCLUDE_FILES:
            continue
        
        # Process files with appropriate analyzer
        if path.is_file():
            # AST analysis for Python/Rust, regex for others
            if path.suffix in ['.py', '.rs', '.md', '.toml', '.json', '.yaml', '.yml', '.ts', '.tsx', '.js', '.jsx']:
                if len(identities) % 100 == 0:
                    print(f"  Analyzed {len(identities)} files...")
                identity = synthesizer.synthesize_identity(path)
                identities.append(identity)
        
        elif path.is_dir():
            # Check if directory is empty or sparse
            children = list(path.iterdir())
            if not children or all(c.name.startswith('.') for c in children):
                # Empty or hidden-only directory
                dir_identity = DirectoryIdentity(
                    path=path,
                    intended_purpose="Awaiting architectural materialization",
                    architectural_significance="Violet frequency - potential space"
                )
                dir_identities.append(dir_identity)
    
    print(f"\n✅ Analyzed {len(identities)} files with intelligent routing")
    print(f"✅ Identified {len(dir_identities)} void directories\n")
    
    # Build enhanced dependency graph
    print("Building enhanced dependency graph...")
    graph = build_enhanced_dependency_graph(identities)
    print(f"✅ Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges\n")
    
    # Detect circular dependencies
    print("Detecting circular dependencies...")
    detector = CircularDependencyDetector()
    cycles = detector.detect_cycles(graph)
    sccs = detector.analyze_strongly_connected_components(graph)
    
    if cycles:
        print(f"⚠️  FOUND {len(cycles)} circular dependencies")
    else:
        print("✅ No circular dependencies detected")
    
    if sccs:
        print(f"⚠️  FOUND {len(sccs)} strongly connected components")
    else:
        print("✅ Graph is acyclic (no SCCs)")
    print()
    
    # Annotate identities with cycle information
    detector.annotate_identities_with_cycles(identities, cycles)
    
    # Generate enhanced analysis report
    print("Generating enhanced analysis report...")
    report = generate_enhanced_analysis_report(identities, graph, cycles, sccs)
    
    report_path = REPO_ROOT / "DCRP_ENHANCED_ANALYSIS.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"✅ Enhanced analysis written to: {report_path}\n")
    
    # Export enhanced graph with cycle annotations
    print("Exporting enhanced dependency graph...")
    graph_data = nx.node_link_data(graph)
    
    # Add cycle information to graph data
    graph_data['cycles'] = cycles
    graph_data['strongly_connected_components'] = [list(scc) for scc in sccs]
    
    graph_json_path = REPO_ROOT / "dependency_graph_enhanced.json"
    with open(graph_json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    print(f"Enhanced graph JSON written to: {graph_json_path}\n")
    
    print("=" * 80)
    print(" THE DECORATOR'S ENHANCED PROTOCOL COMPLETE")
    print("=" * 80)
    print()
    print(f"Summary:")
    print(f"  - Files analyzed: {len(identities)}")
    print(f"  - Dependencies detected: {graph.number_of_edges()}")
    print(f"  - Circular dependencies: {len(cycles)}")
    print(f"  - Strongly connected components: {len(sccs)}")
    print(f"  - Void directories: {len(dir_identities)}")
    print()

if __name__ == "__main__":
    main()
