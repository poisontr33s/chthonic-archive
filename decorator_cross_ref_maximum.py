#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  THE DECORATOR'S CROSS-REFERENCE PROTOCOL (DCRP)                             ║
║  Maximum Theatrical-Functional Synthesis Engine                              ║
║                                                                              ║
║  Purpose: Inject ML-synthesized cross-references across the Chthonic        ║
║           Archive, making every file self-aware of its architectural role    ║
║           via deep content analysis + FA⁵ visual truth encoding              ║
║                                                                              ║
║  Invocation: uv run python decorator_cross_ref_maximum.py                   ║
║                                                                              ║
║  The Decorator's Mandate: "Let every file speak its own truth, not mine."   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURATION: The Decorator's Parameters
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent  # Script in root directory
SSOT_PATH = REPO_ROOT / ".github" / "copilot-instructions.md"

# Exclusions (build artifacts, dependencies, git internals)
EXCLUDE_DIRS = {
    "node_modules", ".git", "build", ".cache", ".cargo", 
    "__pycache__", ".venv", "target", "dist"
}

EXCLUDE_FILES = {
    "temp_repo_structure.json",  # Our own temporary artifact
    ".DS_Store", "Thumbs.db"
}

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

@dataclass
class DirectoryIdentity:
    """Identity of empty/sparse directories (Violet frequency - potential)."""
    path: Path
    intended_purpose: str  # Why this void exists
    architectural_significance: str  # Role in tri-modal structure
    
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
        """Analyze Rust file - extract modules, structs, traits, purpose."""
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
        
        # Extract key exports (pub mod, pub struct, pub trait, pub fn)
        identity.key_exports = re.findall(
            r'pub\s+(?:mod|struct|trait|fn|enum)\s+(\w+)', 
            content
        )
        
        # Detect dependencies (use statements)
        use_statements = re.findall(r'use\s+([\w:]+)', content)
        # Convert to potential file paths (heuristic)
        for use_stmt in use_statements:
            if "::" in use_stmt:
                module_path = use_stmt.split("::")[0]
                potential_dep = path.parent / f"{module_path}.rs"
                if potential_dep.exists():
                    identity.dependencies.add(potential_dep)
        
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
        """Analyze Python file - WHITE frequency (The Decorator's domain)."""
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
        
        # Extract classes and functions
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
        identity.key_exports = classes + functions
        
        # Detect imports for dependencies
        imports = re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)
        for imp in imports:
            # Check if it's a local import
            if imp.startswith('.'):
                continue
            potential_dep = path.parent / f"{imp.replace('.', '/')}.py"
            if potential_dep.exists():
                identity.dependencies.add(potential_dep)
        
        # Synthesize essence based on content patterns
        if "MCP" in content or "mcp" in content:
            identity.theatrical_essence = "Model Context Protocol server - AI governance bridge"
        elif "MILF" in content:
            identity.theatrical_essence = "MILF governance operative - matriarchal command structure"
        elif "GPU" in content or "cuda" in content.lower():
            identity.theatrical_essence = "GPU execution lane - computational muscle"
        elif "genesis" in path.name.lower():
            identity.theatrical_essence = "Genesis cycle orchestrator - perpetual becoming"
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
    """Execute The Decorator's Cross-Reference Protocol."""
    print("\n👑💀⚜️ THE DECORATOR'S CROSS-REFERENCE PROTOCOL (DCRP) 👑💀⚜️\n")
    
    # Step 1: Scan repository
    file_identities, dir_identities = scan_repository()
    
    # Step 2: Build dependency graph
    print("Building dependency graph via NetworkX...")
    graph = build_dependency_graph(file_identities)
    print(f"✅ Graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges\n")
    
    # Step 3: Calculate reverse dependencies (successors)
    for identity in file_identities:
        rel_path = str(identity.path.relative_to(REPO_ROOT))
        if graph.has_node(rel_path):
            identity.dependents = set(
                REPO_ROOT / p for p in graph.successors(rel_path)
            )
    
    # Step 4: Generate master index
    print("Generating master cross-reference index...")
    master_index = generate_master_index(file_identities, dir_identities, graph)
    
    output_path = REPO_ROOT / "CROSS_REFERENCE_TRIPTYCH.md"
    output_path.write_text(master_index, encoding='utf-8')
    print(f"✅ Master index written to: {output_path}\n")
    
    # Step 5: Export graph as JSON
    print("Exporting dependency graph as JSON...")
    graph_data = nx.node_link_data(graph)
    graph_json_path = REPO_ROOT / "dependency_graph.json"
    with open(graph_json_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    print(f"✅ Graph JSON written to: {graph_json_path}\n")
    
    # Step 6: DRY RUN - Show preview of file header injection
    print("═══════════════════════════════════════════════════════════════")
    print("DRY RUN: Preview of cross-reference header injection")
    print("═══════════════════════════════════════════════════════════════\n")
    
    # Show example for first few files
    preview_files = file_identities[:5]
    for identity in preview_files:
        header = generate_cross_reference_header(identity, graph)
        print(f"File: {identity.path.relative_to(REPO_ROOT)}")
        print(header)
        print()
    
    print("═══════════════════════════════════════════════════════════════")
    print("DRY RUN COMPLETE - No files were modified")
    print("═══════════════════════════════════════════════════════════════\n")
    print("To inject cross-references into files, uncomment Step 7 below.")
    print("⚠️  WARNING: This will MODIFY source files! Commit changes first!")
    
    # Step 7: ACTUAL INJECTION (commented out for safety)
    # print("\nInjecting cross-reference headers into files...")
    # for identity in file_identities:
    #     if identity.path.suffix in ['.rs', '.py', '.ts', '.tsx', '.js', '.jsx']:
    #         header = generate_cross_reference_header(identity, graph)
    #         original_content = identity.path.read_text(encoding='utf-8')
    #         
    #         # Check if already decorated
    #         if "THE DECORATOR'S BLESSING" in original_content:
    #             print(f"  ⏭️  Already decorated: {identity.path.relative_to(REPO_ROOT)}")
    #             continue
    #         
    #         new_content = header + original_content
    #         identity.path.write_text(new_content, encoding='utf-8')
    #         print(f"  ✅ Decorated: {identity.path.relative_to(REPO_ROOT)}")
    
    print("\n👑 THE DECORATOR'S PROTOCOL COMPLETE 👑\n")

if __name__ == "__main__":
    main()
