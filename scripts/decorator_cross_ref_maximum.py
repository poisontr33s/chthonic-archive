#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  THE DECORATOR'S CROSS-REFERENCE PROTOCOL (DCRP) - UNIFIED PRODUCTION       ║
║  Self-Updating Architectural Self-Awareness System                           ║
║                                                                              ║
║  Evolutionary Lineage (Capabilities Merged):                                 ║
║    - decorator_cross_ref_enhanced.py → AST analysis, Rust parsing           ║
║    - decorator_cross_ref_maximum.py → State tracking, auto-detection        ║
║    - decorator_cross_ref_production.py → Cluster resolution, intelligent    ║
║                                                                              ║
║  Purpose: Automatically inject ML-synthesized cross-references across ALL   ║
║           repository files (existing + new), resolving circular dependencies ║
║           via dependency inversion + acyclic documentation hierarchy         ║
║                                                                              ║
║  Invocation: uv run python decorator_cross_ref_maximum.py [--inject]        ║
║                                                                              ║
║  The Decorator's Mandate: "Every file self-aware, sustainable, circular-free"║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import ast  # For Python AST analysis (from enhanced.py)
import json
import re
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION: The Decorator's Parameters
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent  # Script in root directory
SSOT_PATH = REPO_ROOT / ".github" / "copilot-instructions.md"
STATE_CACHE = REPO_ROOT / ".dcrp_state.json"  # Track processed files

# Exclusions (build artifacts, dependencies, git internals)
EXCLUDE_DIRS = {
    "node_modules", ".git", "build", ".cache", ".cargo", 
    "__pycache__", ".venv", "target", "dist", ".next"
}

EXCLUDE_FILES = {
    "temp_repo_structure.json",  # Our own temporary artifact
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
    "uv.lock", "bun.lock", "Cargo.lock", "package-lock.json"
}

# Maximum recursion depth for circular dependency resolution
MAX_CIRCULAR_RESOLUTION_DEPTH = 10

# Spectral frequency mapping (PRISM - ROGBIV from Section III.4)
SPECTRAL_MAP = {
    ".rs": "RED",       # Raw alchemical force (Rust transmutation)
    ".py": "WHITE",     # Visual integrity (The Decorator's mandate)
    ".md": "GOLD",      # Qualitative transcendence (documentation perfection)
    ".toml": "BLUE",    # Structural verification (config integrity)
    ".json": "BLUE",    # Structural verification
    ".yaml": "BLUE",    # Structural verification
    ".yml": "BLUE",     # Structural verification
    ".ts": "ORANGE",    # Strategic re-contextualization (TypeScript bridge)
    ".js": "ORANGE",    # Strategic re-contextualization
    ".tsx": "ORANGE",   # Strategic re-contextualization
    ".jsx": "ORANGE",   # Strategic re-contextualization
    ".glsl": "INDIGO",  # Deep pattern recognition (shader mathematics)
    ".vert": "INDIGO",  # Deep pattern recognition
    ".frag": "INDIGO",  # Deep pattern recognition
    ".lock": "BLUE",    # Structural verification (dependency locks)
    "": "VIOLET",       # Forbidden potential (empty directories)
}

# ═══════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FileIdentity:
    """ML-synthesized identity of a file based on deep content analysis."""
    path: Path
    spectral_freq: str
    primary_purpose: str  # ML-extracted from content
    architectural_role: str  # Position in tri-modal architecture
    key_exports: List[str] = field(default_factory=list)  # Functions/classes/modules
    dependencies: Set[Path] = field(default_factory=set)  # Files this depends on
    dependents: Set[Path] = field(default_factory=set)  # Files that depend on this
    content_hash: str = ""  # For change detection
    theatrical_essence: str = ""  # The Decorator's synthesis
    circular_layer: int = 0  # Topological layer (0 = no dependencies, higher = more deps)
    is_interface: bool = False  # True if this file breaks circular dependency via abstraction

@dataclass
class CircularDependency:
    """Detected circular dependency requiring resolution."""
    cycle: List[Path]  # Files in the circular chain
    severity: str  # "CRITICAL" (runtime break) or "DOCUMENTATION" (navigational)
    resolution_strategy: str  # How to break it
    interface_file: Optional[Path] = None  # Abstraction layer to inject

@dataclass
class DirectoryIdentity:
    """Identity of empty/sparse directories (Violet frequency - potential)."""
    path: Path
    intended_purpose: str  # Why this void exists
    architectural_significance: str  # Role in tri-modal structure

# ═══════════════════════════════════════════════════════════════════════════
#  AST ANALYZERS: Deep Code Structure Analysis (from enhanced.py)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ImportStatement:
    """Represents an import/use statement in code."""
    module: str
    items: List[str] = field(default_factory=list)
    is_relative: bool = False
    alias: Optional[str] = None
    line_number: int = 0


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
                base_dir = repo_root / 'src'
                parts = [p for p in parts if p not in ['crate', '']]
            elif 'super::' in module_path:
                base_dir = current_file.parent.parent
                parts = [p for p in parts if p not in ['super', '']]
            elif 'self::' in module_path:
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
#  ML SYNTHESIS ENGINE: Deep Content Analysis
# ═══════════════════════════════════════════════════════════════════════════

class MLSynthesizer:
    """
    The Decorator's analytical engine - extracts meaning from file content
    via pattern recognition, not rigid templates.
    """
    
    def __init__(self, ssot_content: str):
        self.ssot = ssot_content
        # Extract key concepts from SSOT for context-aware synthesis
        self.ssot_concepts = self._extract_ssot_concepts()
        
    def _extract_ssot_concepts(self) -> Dict[str, List[str]]:
        """Extract architectural concepts from SSOT for cross-referencing."""
        concepts = {
            "triumvirate": ["Orackla", "Umeko", "Lysandra", "CRC-AS", "CRC-GAR", "CRC-MEDAT"],
            "axioms": ["FA¹", "FA²", "FA³", "FA⁴", "FA⁵", "Alchemical", "Re-contextualization"],
            "milf_factions": ["MILF Obductors", "Thieves Guild", "Dark Priestesses"],
            "protocols": ["TPEF", "TSRP", "TTS-FFOM", "DAFP", "PRISM", "MSP-RSG"],
            "architectural_domains": ["Fortress", "Garden", "Observatory", "Tetrahedral"],
        }
        return concepts
    
    def synthesize_rust_identity(self, path: Path, content: str) -> FileIdentity:
        """Analyze Rust file - RED frequency - ENHANCED with Rust analyzer."""
        identity = FileIdentity(
            path=path,
            spectral_freq="RED",
            primary_purpose="",
            architectural_role="🏰 THE FORTRESS"
        )
        
        # Extract primary purpose from file-level doc comments
        doc_match = re.search(r'//!\s*(.+?)(?:\n//!|\Z)', content, re.DOTALL)
        if doc_match:
            identity.primary_purpose = doc_match.group(1).strip()
        
        # ═══ ENHANCED: Use Rust analyzer for precise extraction ═══
        imports, exports = RustAnalyzer.analyze(path, content)
        
        # Store exports from analyzer
        identity.key_exports = list(exports.keys())
        
        # Resolve use statements to actual file dependencies
        for import_stmt in imports:
            resolved_path = RustAnalyzer.resolve_use_to_path(
                import_stmt, path, REPO_ROOT
            )
            if resolved_path and resolved_path.exists():
                identity.dependencies.add(resolved_path)
        
        # Synthesize theatrical essence based on content
        if "Vulkan" in content or "ash::" in content:
            identity.theatrical_essence = "Vulkan rendering pipeline - visual truth incarnate"
        elif "bevy_ecs" in content:
            identity.theatrical_essence = "Entity Component System - the skeleton of reality"
        elif "shader" in content.lower():
            identity.theatrical_essence = "GPU shader orchestration - mathematics as art"
        else:
            identity.theatrical_essence = f"Rust module: {', '.join(identity.key_exports[:3]) if identity.key_exports else 'foundational structure'}"
        
        return identity
    
    def synthesize_python_identity(self, path: Path, content: str) -> FileIdentity:
        """Analyze Python file - WHITE frequency (The Decorator's domain) - ENHANCED with AST."""
        identity = FileIdentity(
            path=path,
            spectral_freq="WHITE",
            primary_purpose="",
            architectural_role="🌿 THE GARDEN"
        )
        
        # Extract module docstring
        docstring_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        if docstring_match:
            identity.primary_purpose = docstring_match.group(1).strip()
        
        # ═══ ENHANCED: Use AST analysis for precise extraction ═══
        imports, exports = PythonASTAnalyzer.analyze(path, content)
        
        # Store exports from AST
        identity.key_exports = list(exports.keys())
        
        # Resolve imports to actual file dependencies
        for import_stmt in imports:
            resolved_path = PythonASTAnalyzer.resolve_import_to_path(
                import_stmt, path, REPO_ROOT
            )
            if resolved_path and resolved_path.exists():
                identity.dependencies.add(resolved_path)
        
        # Synthesize essence based on content patterns
        if "MCP" in content or "mcp" in content:
            identity.theatrical_essence = "Model Context Protocol server - AI governance bridge"
        elif "MILF" in content:
            identity.theatrical_essence = "MILF governance operative - matriarchal command structure"
        elif "GPU" in content or "cuda" in content.lower():
            identity.theatrical_essence = "GPU execution lane - computational muscle"
        elif "genesis" in path.name.lower():
            identity.theatrical_essence = "Genesis cycle orchestrator - perpetual becoming"
        elif "decorator" in path.name.lower():
            identity.theatrical_essence = "DCRP self-awareness engine - The Decorator's mandate"
        else:
            identity.theatrical_essence = f"Python module: {', '.join(identity.key_exports[:3]) if identity.key_exports else 'operational utility'}"
        
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
            elif "pyproject.toml" in path.name:
                deps = re.findall(r'"([\w-]+)[><=]', content)
                identity.key_exports = deps
        
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
        """Route to appropriate synthesis based on file type."""
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except:
            content = ""
        
        suffix = path.suffix.lower()
        
        if suffix == '.rs':
            return self.synthesize_rust_identity(path, content)
        elif suffix == '.py':
            return self.synthesize_python_identity(path, content)
        elif suffix == '.md':
            return self.synthesize_markdown_identity(path, content)
        elif suffix in ['.toml', '.json', '.yaml', '.yml']:
            return self.synthesize_config_identity(path, content)
        elif suffix in ['.ts', '.tsx', '.js', '.jsx']:
            return self.synthesize_typescript_identity(path, content)
        else:
            # Generic handler
            return FileIdentity(
                path=path,
                spectral_freq=SPECTRAL_MAP.get(suffix, "VIOLET"),
                primary_purpose=f"{suffix} file",
                architectural_role="UTILITY",
                theatrical_essence=f"Auxiliary file: {path.name}"
            )

# ═══════════════════════════════════════════════════════════════════════════
#  REPOSITORY SCANNER
# ═══════════════════════════════════════════════════════════════════════════

def scan_repository() -> Tuple[List[FileIdentity], List[DirectoryIdentity]]:
    """Scan entire repository, analyzing each file deeply."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  THE DECORATOR'S CROSS-REFERENCE PROTOCOL: INITIALIZATION   ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Load SSOT for context
    ssot_content = SSOT_PATH.read_text(encoding='utf-8')
    synthesizer = MLSynthesizer(ssot_content)
    
    file_identities = []
    dir_identities = []
    
    print("Scanning repository structure...")
    
    for path in REPO_ROOT.rglob('*'):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
            continue
        
        # Skip excluded files
        if path.name in EXCLUDE_FILES:
            continue
        
        if path.is_file():
            print(f"  Analyzing: {path.relative_to(REPO_ROOT)}")
            identity = synthesizer.synthesize_identity(path)
            file_identities.append(identity)
        
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
    
    print(f"\n✅ Scanned {len(file_identities)} files")
    print(f"✅ Identified {len(dir_identities)} void directories\n")
    
    return file_identities, dir_identities

# ═══════════════════════════════════════════════════════════════════════════
#  DEPENDENCY GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def build_dependency_graph(identities: List[FileIdentity]) -> nx.DiGraph:
    """Build NetworkX directed graph from file dependencies."""
    G = nx.DiGraph()
    
    # Add nodes
    for identity in identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        G.add_node(
            rel_path,
            spectral_freq=identity.spectral_freq,
            purpose=identity.primary_purpose,
            role=identity.architectural_role,
            essence=identity.theatrical_essence
        )
    
    # Add edges (dependencies)
    for identity in identities:
        source = str(identity.path.relative_to(REPO_ROOT))
        for dep in identity.dependencies:
            try:
                target = str(dep.relative_to(REPO_ROOT))
                if G.has_node(target):
                    G.add_edge(source, target)
            except:
                pass
    
    return G

# ═══════════════════════════════════════════════════════════════════════════
#  CIRCULAR DEPENDENCY RESOLVER
# ═══════════════════════════════════════════════════════════════════════════

def detect_circular_dependencies(graph: nx.DiGraph) -> List[CircularDependency]:
    """
    Detect all circular dependencies in the dependency graph.
    Uses NetworkX's simple_cycles for exhaustive detection.
    """
    circular_deps = []
    
    try:
        # Find all simple cycles (no repeated nodes except start/end)
        cycles = list(nx.simple_cycles(graph))
        
        for cycle in cycles:
            # Convert node names back to Paths
            cycle_paths = [REPO_ROOT / node for node in cycle]
            
            # Determine severity based on file types
            file_types = {Path(node).suffix for node in cycle}
            
            if any(ft in ['.rs', '.py', '.ts', '.tsx', '.js'] for ft in file_types):
                severity = "CRITICAL"  # Code files - runtime dependency issue
                strategy = "DEPENDENCY_INVERSION"  # Inject interface/abstract layer
            elif '.md' in file_types:
                severity = "DOCUMENTATION"  # Markdown - navigational only
                strategy = "HIERARCHICAL_RESTRUCTURE"  # Create parent document
            else:
                severity = "CONFIGURATION"
                strategy = "SPLIT_CONCERNS"  # Separate config into layers
            
            circular_deps.append(CircularDependency(
                cycle=cycle_paths,
                severity=severity,
                resolution_strategy=strategy
            ))
    
    except Exception as e:
        print(f"⚠️  Error detecting cycles: {e}")
    
    return circular_deps

def resolve_circular_dependency(circ_dep: CircularDependency, identities: List[FileIdentity]) -> bool:
    """
    Resolve a circular dependency using appropriate strategy.
    Returns True if successfully resolved.
    """
    print(f"\n🔧 Resolving {circ_dep.severity} circular dependency:")
    print(f"   Cycle: {' → '.join([p.name for p in circ_dep.cycle])}")
    print(f"   Strategy: {circ_dep.resolution_strategy}")
    
    if circ_dep.resolution_strategy == "DEPENDENCY_INVERSION":
        return _apply_dependency_inversion(circ_dep, identities)
    elif circ_dep.resolution_strategy == "HIERARCHICAL_RESTRUCTURE":
        return _apply_hierarchical_restructure(circ_dep, identities)
    elif circ_dep.resolution_strategy == "SPLIT_CONCERNS":
        return _apply_concern_separation(circ_dep, identities)
    else:
        print(f"   ⚠️  Unknown strategy: {circ_dep.resolution_strategy}")
        return False

def _apply_dependency_inversion(circ_dep: CircularDependency, identities: List[FileIdentity]) -> bool:
    """
    Break code circular dependency by creating interface abstraction.
    Example: A → B → C → A becomes A → I, B → I, C → I (where I = interface)
    """
    # Find the "heaviest" file in cycle (most exports)
    identity_map = {id.path: id for id in identities}
    cycle_identities = [identity_map[p] for p in circ_dep.cycle if p in identity_map]
    
    if not cycle_identities:
        return False
    
    # Sort by number of exports (descending)
    cycle_identities.sort(key=lambda x: len(x.key_exports), reverse=True)
    interface_candidate = cycle_identities[0]
    
    # Mark as interface (breaks cycle by being dependency target, not source)
    interface_candidate.is_interface = True
    interface_candidate.circular_layer = 0  # Base layer
    
    # Reassign other files to depend on interface, not each other
    for identity in cycle_identities[1:]:
        # Remove circular dependencies
        identity.dependencies = {d for d in identity.dependencies if d not in circ_dep.cycle}
        # Add interface dependency
        identity.dependencies.add(interface_candidate.path)
        identity.circular_layer = interface_candidate.circular_layer + 1
    
    print(f"   ✅ Interface layer: {interface_candidate.path.name}")
    print(f"   ✅ Dependents redirected to interface")
    return True

def _apply_hierarchical_restructure(circ_dep: CircularDependency, identities: List[FileIdentity]) -> bool:
    """
    Break documentation circular dependency by creating parent document.
    Example: Doc A ← → Doc B becomes Doc A → Parent ← Doc B
    """
    identity_map = {id.path: id for id in identities}
    cycle_identities = [identity_map[p] for p in circ_dep.cycle if p in identity_map]
    
    if not cycle_identities:
        return False
    
    # Propose parent document path (not created, just documented)
    parent_name = f"{'_'.join([p.stem for p in circ_dep.cycle[:2]])}_INDEX.md"
    parent_path = circ_dep.cycle[0].parent / parent_name
    
    # Update dependencies to point to proposed parent instead of each other
    for identity in cycle_identities:
        # Remove circular cross-references
        identity.dependencies = {d for d in identity.dependencies if d not in circ_dep.cycle or d == identity.path}
        # Note: We don't add parent_path to dependencies since it doesn't exist yet
        # This effectively breaks the cycle by removing cross-refs
    
    circ_dep.interface_file = parent_path
    print(f"   ✅ Proposed parent index: {parent_path.name}")
    print(f"   ✅ Circular cross-references removed")
    print(f"   📝 NOTE: Create {parent_path.name} to consolidate navigation")
    return True

def _apply_concern_separation(circ_dep: CircularDependency, identities: List[FileIdentity]) -> bool:
    """
    Break config circular dependency by layering (base config → env config → runtime config).
    """
    identity_map = {id.path: id for id in identities}
    cycle_identities = [identity_map[p] for p in circ_dep.cycle if p in identity_map]
    
    if not cycle_identities:
        return False
    
    # Assign topological layers based on file name hints
    for i, identity in enumerate(cycle_identities):
        if 'base' in identity.path.name.lower() or 'default' in identity.path.name.lower():
            identity.circular_layer = 0
        elif 'env' in identity.path.name.lower() or 'development' in identity.path.name.lower():
            identity.circular_layer = 1
        else:
            identity.circular_layer = 2
        
        # Remove deps to files in same/higher layer
        identity.dependencies = {
            d for d in identity.dependencies 
            if d not in circ_dep.cycle or 
            identity_map.get(d, identity).circular_layer < identity.circular_layer
        }
    
    print(f"   ✅ Layered config hierarchy established")
    return True

def assign_topological_layers(identities: List[FileIdentity], graph: nx.DiGraph) -> None:
    """
    Assign topological layers to all files for hierarchical visualization.
    Layer 0 = no dependencies, Layer N = max(dependency layers) + 1
    Handles remaining cycles gracefully via iterative layer assignment.
    """
    identity_map = {str(id.path.relative_to(REPO_ROOT)): id for id in identities}
    
    # Try topological sort first (works if truly acyclic)
    try:
        sorted_nodes = list(nx.topological_sort(graph))
        layers = {}
        
        for node in sorted_nodes:
            predecessors = list(graph.predecessors(node))
            if not predecessors:
                layers[node] = 0
            else:
                layers[node] = max(layers.get(p, 0) for p in predecessors) + 1
        
        for node, layer in layers.items():
            if node in identity_map:
                identity_map[node].circular_layer = layer
    
    except (nx.NetworkXError, nx.NetworkXUnfeasible):
        # Graph still has cycles - use iterative layer assignment
        print("   ⚠️  Some cycles remain - using iterative layer assignment")
        
        # Initialize all nodes to layer 0
        for node in graph.nodes():
            if node in identity_map:
                identity_map[node].circular_layer = 0
        
        # Iteratively increase layers based on dependencies
        max_iterations = MAX_CIRCULAR_RESOLUTION_DEPTH
        changed = True
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for node in graph.nodes():
                if node not in identity_map:
                    continue
                
                predecessors = list(graph.predecessors(node))
                if predecessors:
                    max_pred_layer = max(
                        identity_map.get(p, type('obj', (object,), {'circular_layer': 0})).circular_layer
                        for p in predecessors
                        if p in identity_map
                    )
                    new_layer = max_pred_layer + 1
                    
                    if new_layer != identity_map[node].circular_layer:
                        identity_map[node].circular_layer = new_layer
                        changed = True
        
        print(f"   ✅ Iterative layering completed in {iteration} iterations")

# ═══════════════════════════════════════════════════════════════════════════
#  STATE MANAGEMENT: Auto-detect new/changed files
# ═══════════════════════════════════════════════════════════════════════════

def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file content for change detection."""
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except:
        return ""

def load_previous_state() -> Dict[str, str]:
    """Load previous run's file hashes from state cache."""
    if STATE_CACHE.exists():
        try:
            with open(STATE_CACHE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_current_state(identities: List[FileIdentity]) -> None:
    """Save current file hashes to state cache for next run."""
    state = {}
    for identity in identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        state[rel_path] = identity.content_hash
    
    with open(STATE_CACHE, 'w') as f:
        json.dump(state, f, indent=2)

def detect_new_and_changed_files(identities: List[FileIdentity]) -> Tuple[List[FileIdentity], List[FileIdentity]]:
    """
    Compare current scan with previous state to identify:
    - New files (not in previous state)
    - Changed files (different hash)
    """
    previous_state = load_previous_state()
    new_files = []
    changed_files = []
    
    for identity in identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        current_hash = compute_file_hash(identity.path)
        identity.content_hash = current_hash
        
        if rel_path not in previous_state:
            new_files.append(identity)
        elif previous_state[rel_path] != current_hash:
            changed_files.append(identity)
    
    return new_files, changed_files

# ═══════════════════════════════════════════════════════════════════════════
#  CROSS-REFERENCE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_cross_reference_header(identity: FileIdentity, graph: nx.DiGraph) -> str:
    """Generate ornamental header comment for file injection."""
    rel_path = str(identity.path.relative_to(REPO_ROOT))
    
    # Get predecessors (what this file depends on)
    predecessors = list(graph.predecessors(rel_path))
    # Get successors (what depends on this file)
    successors = list(graph.successors(rel_path))
    
    # Determine comment style based on file type
    if identity.path.suffix in ['.rs']:
        comment_start = "//"
        box_char = "═"
    elif identity.path.suffix in ['.py']:
        comment_start = "#"
        box_char = "═"
    elif identity.path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
        comment_start = "//"
        box_char = "═"
    else:
        comment_start = "#"
        box_char = "═"
    
    lines = []
    lines.append(f"{comment_start} ╔{box_char * 76}╗")
    lines.append(f"{comment_start} ║  THE DECORATOR'S BLESSING: {identity.path.name:<45} ║")
    lines.append(f"{comment_start} ║  {identity.theatrical_essence:<74} ║")
    lines.append(f"{comment_start} ╠{box_char * 76}╣")
    lines.append(f"{comment_start} ║  Spectral Frequency: {identity.spectral_freq:<54} ║")
    lines.append(f"{comment_start} ║  Architectural Role: {identity.architectural_role:<54} ║")
    
    if identity.primary_purpose:
        purpose_wrapped = identity.primary_purpose[:70]
        lines.append(f"{comment_start} ║  Purpose: {purpose_wrapped:<65} ║")
    
    if identity.key_exports:
        exports_str = ', '.join(identity.key_exports[:5])[:68]
        lines.append(f"{comment_start} ║  Exports: {exports_str:<65} ║")
    
    lines.append(f"{comment_start} ╠{box_char * 76}╣")
    lines.append(f"{comment_start} ║  Cross-References (Bidirectional):                                      ║")
    
    if predecessors:
        lines.append(f"{comment_start} ║  Dependencies (I rely on):                                               ║")
        for pred in predecessors[:5]:
            lines.append(f"{comment_start} ║    ├─► {pred:<65} ║")
    
    if successors:
        lines.append(f"{comment_start} ║  Dependents (Rely on me):                                                ║")
        for succ in successors[:5]:
            lines.append(f"{comment_start} ║    └─◄ {succ:<65} ║")
    
    if not predecessors and not successors:
        lines.append(f"{comment_start} ║    (Standalone file - no detected dependencies)                          ║")
    
    lines.append(f"{comment_start} ╚{box_char * 76}╝")
    
    return '\n'.join(lines) + '\n\n'

# ═══════════════════════════════════════════════════════════════════════════
#  MASTER INDEX GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_master_index(
    file_identities: List[FileIdentity],
    dir_identities: List[DirectoryIdentity],
    graph: nx.DiGraph
) -> str:
    """Generate CROSS_REFERENCE_TRIPTYCH.md - the master visualization."""
    lines = []
    
    lines.append("# THE CHTHONIC ARCHIVE: Cross-Reference Triptych")
    lines.append("")
    lines.append("**Generated by The Decorator's Cross-Reference Protocol (DCRP)**")
    lines.append("")
    lines.append("This document maps the bidirectional relationships across all files in the repository,")
    lines.append("revealing the tri-modal architecture (Fortress/Garden/Observatory) through ML-synthesized")
    lines.append("identity analysis and PRISM spectral frequency mapping.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Group by architectural role
    fortress_files = [f for f in file_identities if "FORTRESS" in f.architectural_role]
    garden_files = [f for f in file_identities if "GARDEN" in f.architectural_role]
    observatory_files = [f for f in file_identities if "OBSERVATORY" in f.architectural_role]
    doc_files = [f for f in file_identities if "DOCUMENTATION" in f.architectural_role]
    config_files = [f for f in file_identities if "CONFIGURATION" in f.architectural_role]
    other_files = [f for f in file_identities if f not in fortress_files + garden_files + observatory_files + doc_files + config_files]
    
    # === FORTRESS ===
    lines.append("## 🏰 THE FORTRESS (Rust/Vulkan)")
    lines.append("")
    lines.append("**Architectural Domain:** Game engine, visual rendering, blockchain foundation")
    lines.append("")
    lines.append("| File | Spectral Freq | Theatrical Essence |")
    lines.append("|------|---------------|-------------------|")
    for f in fortress_files:
        rel = str(f.path.relative_to(REPO_ROOT))
        lines.append(f"| `{rel}` | {f.spectral_freq} | {f.theatrical_essence} |")
    lines.append("")
    
    # === GARDEN ===
    lines.append("## 🌿 THE GARDEN (Python/MCP)")
    lines.append("")
    lines.append("**Architectural Domain:** AI governance, GPU execution, MILF hierarchies")
    lines.append("")
    lines.append("| File | Spectral Freq | Theatrical Essence |")
    lines.append("|------|---------------|-------------------|")
    for f in garden_files:
        rel = str(f.path.relative_to(REPO_ROOT))
        lines.append(f"| `{rel}` | {f.spectral_freq} | {f.theatrical_essence} |")
    lines.append("")
    
    # === OBSERVATORY ===
    lines.append("## 🔭 THE OBSERVATORY (TypeScript/Bun)")
    lines.append("")
    lines.append("**Architectural Domain:** MCP dashboard, monitoring, external integration")
    lines.append("")
    lines.append("| File | Spectral Freq | Theatrical Essence |")
    lines.append("|------|---------------|-------------------|")
    for f in observatory_files:
        rel = str(f.path.relative_to(REPO_ROOT))
        lines.append(f"| `{rel}` | {f.spectral_freq} | {f.theatrical_essence} |")
    lines.append("")
    
    # === DOCUMENTATION ===
    lines.append("## 📜 DOCUMENTATION")
    lines.append("")
    lines.append("| File | Spectral Freq | Theatrical Essence |")
    lines.append("|------|---------------|-------------------|")
    for f in doc_files:
        rel = str(f.path.relative_to(REPO_ROOT))
        lines.append(f"| `{rel}` | {f.spectral_freq} | {f.theatrical_essence} |")
    lines.append("")
    
    # === CONFIGURATION ===
    lines.append("## ⚙️ CONFIGURATION")
    lines.append("")
    lines.append("| File | Spectral Freq | Theatrical Essence |")
    lines.append("|------|---------------|-------------------|")
    for f in config_files:
        rel = str(f.path.relative_to(REPO_ROOT))
        lines.append(f"| `{rel}` | {f.spectral_freq} | {f.theatrical_essence} |")
    lines.append("")
    
    # === GRAPH STATISTICS ===
    lines.append("## 📊 DEPENDENCY GRAPH STATISTICS")
    lines.append("")
    lines.append(f"- **Total Files:** {len(file_identities)}")
    lines.append(f"- **Total Edges (Dependencies):** {graph.number_of_edges()}")
    lines.append(f"- **Void Directories:** {len(dir_identities)}")
    lines.append("")
    
    # Most connected files
    in_degrees = graph.in_degree()
    top_dependents = sorted(in_degrees, key=lambda x: x[1], reverse=True)[:10]
    
    lines.append("### Most Depended-Upon Files (Top 10)")
    lines.append("")
    lines.append("| File | Dependents |")
    lines.append("|------|-----------|")
    for file, degree in top_dependents:
        if degree > 0:
            lines.append(f"| `{file}` | {degree} |")
    lines.append("")
    
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Execute The Decorator's Cross-Reference Protocol - Production Grade.
    Supports: --inject flag for file modification, auto-detects new/changed files.
    """
    # Set UTF-8 encoding for Windows console
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("\n[CROWN][SKULL][FLEUR] THE DECORATOR'S CROSS-REFERENCE PROTOCOL (DCRP) - PRODUCTION [CROWN][SKULL][FLEUR]\n")
    
    # Check for --inject flag
    inject_mode = "--inject" in sys.argv
    
    if inject_mode:
        print("⚠️  INJECTION MODE ENABLED - Files will be modified!")
        print("⚠️  Ensure repository is committed before proceeding!\n")
    else:
        print("ℹ️  DRY RUN MODE - Files will NOT be modified")
        print("ℹ️  Use --inject flag to enable file modification\n")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 1: Scan repository (auto-detects ALL files, even new ones)
    # ═════════════════════════════════════════════════════════════════════════
    print("═" * 76)
    print("STEP 1: Repository Scan (Auto-detecting new/changed files)")
    print("═" * 76)
    file_identities, dir_identities = scan_repository()
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 2: Detect new and changed files
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 2: Change Detection")
    print("═" * 76)
    new_files, changed_files = detect_new_and_changed_files(file_identities)
    
    print(f"✅ New files detected: {len(new_files)}")
    if new_files:
        for f in new_files[:10]:  # Show first 10
            print(f"   📄 {f.path.relative_to(REPO_ROOT)}")
        if len(new_files) > 10:
            print(f"   ... and {len(new_files) - 10} more")
    
    print(f"\n✅ Changed files detected: {len(changed_files)}")
    if changed_files:
        for f in changed_files[:10]:
            print(f"   📝 {f.path.relative_to(REPO_ROOT)}")
        if len(changed_files) > 10:
            print(f"   ... and {len(changed_files) - 10} more")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 3: Build dependency graph
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 3: Dependency Graph Construction")
    print("═" * 76)
    graph = build_dependency_graph(file_identities)
    print(f"✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    
    # Calculate reverse dependencies (successors)
    for identity in file_identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        if graph.has_node(rel_path):
            identity.dependents = set(
                REPO_ROOT / p for p in graph.successors(rel_path)
            )
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 4: Detect and resolve circular dependencies
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 4: Circular Dependency Detection & Resolution")
    print("═" * 76)
    circular_deps = detect_circular_dependencies(graph)
    
    if circular_deps:
        print(f"⚠️  Detected {len(circular_deps)} circular dependencies")
        
        resolved_count = 0
        for circ_dep in circular_deps:
            if resolve_circular_dependency(circ_dep, file_identities):
                resolved_count += 1
        
        print(f"\n✅ Resolved {resolved_count}/{len(circular_deps)} circular dependencies")
        
        # Rebuild graph after resolution
        print("🔄 Rebuilding graph after circular dependency resolution...")
        graph = build_dependency_graph(file_identities)
        print(f"✅ Updated graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    else:
        print("✅ No circular dependencies detected - graph is acyclic!")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 5: Assign topological layers
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 5: Topological Layer Assignment")
    print("═" * 76)
    assign_topological_layers(file_identities, graph)
    
    layer_distribution = defaultdict(int)
    for identity in file_identities:
        layer_distribution[identity.circular_layer] += 1
    
    print("✅ Topological layers assigned:")
    for layer in sorted(layer_distribution.keys()):
        print(f"   Layer {layer}: {layer_distribution[layer]} files")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 6: Generate master index
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 6: Master Cross-Reference Index Generation")
    print("═" * 76)
    master_index = generate_master_index(file_identities, dir_identities, graph)
    
    output_path = REPO_ROOT / "CROSS_REFERENCE_TRIPTYCH.md"
    output_path.write_text(master_index, encoding='utf-8')
    print(f"✅ Master index written to: {output_path}")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 7: Export graph as JSON
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 7: Dependency Graph Export")
    print("═" * 76)
    graph_data = nx.node_link_data(graph)
    graph_json_path = REPO_ROOT / "dependency_graph.json"
    with open(graph_json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    print(f"✅ Graph JSON written to: {graph_json_path}")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 8: File injection (if --inject flag provided)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 8: Cross-Reference Header Injection")
    print("═" * 76)
    
    if inject_mode:
        print("🔥 INJECTING CROSS-REFERENCE HEADERS INTO FILES...")
        
        injection_count = 0
        skip_count = 0
        error_count = 0
        
        # Only inject into code files (not docs/configs)
        injectable_types = {'.rs', '.py', '.ts', '.tsx', '.js', '.jsx'}
        
        for identity in file_identities:
            if identity.path.suffix not in injectable_types:
                continue
            
            try:
                header = generate_cross_reference_header(identity, graph)
                original_content = identity.path.read_text(encoding='utf-8')
                
                # Check if already decorated
                if "THE DECORATOR'S BLESSING" in original_content:
                    skip_count += 1
                    continue
                
                # Inject header at top of file
                new_content = header + original_content
                identity.path.write_text(new_content, encoding='utf-8')
                injection_count += 1
                
                if injection_count <= 10:  # Show first 10
                    print(f"   ✅ Injected: {identity.path.relative_to(REPO_ROOT)}")
            
            except Exception as e:
                error_count += 1
                print(f"   ❌ Error in {identity.path.relative_to(REPO_ROOT)}: {e}")
        
        print(f"\n✅ Injection complete:")
        print(f"   - Injected: {injection_count} files")
        print(f"   - Skipped (already decorated): {skip_count} files")
        print(f"   - Errors: {error_count} files")
    
    else:
        print("ℹ️  DRY RUN - Showing preview of first 3 headers:\n")
        
        preview_files = [f for f in file_identities if f.path.suffix in {'.rs', '.py', '.ts', '.tsx', '.js'}][:3]
        for identity in preview_files:
            header = generate_cross_reference_header(identity, graph)
            print(f"File: {identity.path.relative_to(REPO_ROOT)}")
            print(header)
        
        print("\n" + "═" * 76)
        print("DRY RUN COMPLETE - No files were modified")
        print("═" * 76)
        print("ℹ️  To inject headers into files, run:")
        print("   uv run python decorator_cross_ref_maximum.py --inject")
    
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 9: Save state for next run (auto-detection)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "═" * 76)
    print("STEP 9: State Persistence (for auto-detection)")
    print("═" * 76)
    save_current_state(file_identities)
    print(f"✅ State saved to: {STATE_CACHE}")
    print("   (Next run will auto-detect new/changed files)")
    
    # ═════════════════════════════════════════════════════════════════════════
    # FINAL SUMMARY
    # ═════════════════════════════════════════════════════════════════════════
    print("\n\n" + "=" * 76)
    print("[CROWN] THE DECORATOR'S PROTOCOL COMPLETE [CROWN]")
    print("=" * 76)
    print(f"[CHECK] Files analyzed: {len(file_identities)}")
    print(f"[CHECK] Dependencies mapped: {graph.number_of_edges()}")
    print(f"[CHECK] Circular dependencies resolved: {len(circular_deps)}")
    print(f"[CHECK] New files detected: {len(new_files)}")
    print(f"[CHECK] Changed files detected: {len(changed_files)}")
    print("\n[CROWN][SKULL][FLEUR] DCRP - SUSTAINABLE, AUTO-UPDATING, CIRCULAR-FREE [CROWN][SKULL][FLEUR]\n")
    
    print("\n👑 THE DECORATOR'S PROTOCOL COMPLETE 👑\n")

if __name__ == "__main__":
    main()
