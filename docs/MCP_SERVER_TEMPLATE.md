# MCP Server Implementation Template (Chthonic Archive)

**Status:** REFERENCE TEMPLATE  
**Date:** 2026-01-04  
**Purpose:** Boilerplate for custom MCP server creation  
**Authority:** Derived from official Python SDK quickstart

---

## Minimal FastMCP Server (Python 3.13+)

### File Structure
```
mas_mcp/
├── server.py              # Main MCP server entry point
├── tools/                 # Tool implementations
│   ├── __init__.py
│   ├── repository.py      # DCRP, git ops, file scanning
│   ├── epistemograph.py   # Knowledge graph queries
│   └── validation.py      # FA⁴ enforcement, SSOT checks
├── resources/             # Dynamic resource providers
│   ├── __init__.py
│   └── ssot.py           # SSOT document access
└── prompts/              # Prompt templates
    ├── __init__.py
    └── autonomous.py     # Autonomous operation templates
```

---

## Basic Server Template (`server.py`)

```python
"""
Chthonic Archive MCP Server
Provides repository context and autonomous operation tools to AI assistants.
"""

from typing import Any
from mcp.server.fastmcp import FastMCP
import logging

# Configure logging to stderr (CRITICAL for STDIO transport)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Defaults to stderr
)
logger = logging.getLogger(__name__)

# Initialize server
mcp = FastMCP(
    "chthonic-archive",
    json_response=True  # Return structured JSON
)

# ============================================================================
# TOOLS (Functions the LLM can invoke)
# ============================================================================

@mcp.tool()
async def scan_repository(
    path: str = ".",
    pattern: str = "**/*.md",
    include_hidden: bool = False
) -> dict[str, Any]:
    """
    Scan repository for files matching pattern.
    
    Args:
        path: Root path to scan (default: current directory)
        pattern: Glob pattern to match (default: all markdown)
        include_hidden: Include hidden files/directories (default: False)
    
    Returns:
        Dict with 'files' list and 'count' int
    """
    from pathlib import Path
    
    root = Path(path).resolve()
    files = []
    
    for match in root.glob(pattern):
        if not include_hidden and any(p.startswith('.') for p in match.parts):
            continue
        files.append({
            "path": str(match.relative_to(root)),
            "size": match.stat().st_size,
            "modified": match.stat().st_mtime
        })
    
    return {
        "files": files,
        "count": len(files)
    }

@mcp.tool()
async def validate_ssot_integrity() -> dict[str, Any]:
    """
    Validate SSOT hash integrity (per Section XIV.3).
    
    Returns:
        Dict with 'valid' bool, 'hash' str, 'errors' list
    """
    import hashlib
    import unicodedata
    from pathlib import Path
    
    def canonicalize(text: str) -> str:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return unicodedata.normalize('NFC', text).strip()
    
    ssot_path = Path(".github/copilot-instructions.md")
    
    if not ssot_path.exists():
        return {"valid": False, "hash": None, "errors": ["SSOT not found"]}
    
    content = ssot_path.read_text(encoding='utf-8')
    canonical = canonicalize(content)
    computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    return {
        "valid": True,
        "hash": computed_hash,
        "errors": []
    }

@mcp.tool()
async def query_dependency_graph(
    node: str | None = None,
    depth: int = 1
) -> dict[str, Any]:
    """
    Query the DCRP dependency graph.
    
    Args:
        node: Specific file to query (None = graph stats)
        depth: Traversal depth for dependencies
    
    Returns:
        Dict with 'dependencies', 'dependents', 'metadata'
    """
    import json
    from pathlib import Path
    
    graph_path = Path("dependency_graph_production.json")
    
    if not graph_path.exists():
        return {"error": "Dependency graph not found. Run DCRP first."}
    
    graph_data = json.loads(graph_path.read_text())
    
    if node is None:
        # Return graph statistics
        return {
            "nodes": len(graph_data.get("nodes", [])),
            "edges": len(graph_data.get("links", [])),
            "spectral_distribution": _count_spectral_frequencies(graph_data)
        }
    
    # Find specific node
    node_data = _find_node(graph_data, node)
    if not node_data:
        return {"error": f"Node '{node}' not found in graph"}
    
    return {
        "file": node,
        "dependencies": _get_dependencies(graph_data, node, depth),
        "dependents": _get_dependents(graph_data, node, depth),
        "metadata": node_data
    }

def _count_spectral_frequencies(graph: dict) -> dict:
    """Count PRISM spectral frequencies in graph."""
    freq_map = {}
    for node in graph.get("nodes", []):
        freq = node.get("spectral_frequency", "UNKNOWN")
        freq_map[freq] = freq_map.get(freq, 0) + 1
    return freq_map

def _find_node(graph: dict, path: str) -> dict | None:
    """Find node by file path."""
    for node in graph.get("nodes", []):
        if node.get("id") == path:
            return node
    return None

def _get_dependencies(graph: dict, node: str, depth: int) -> list[str]:
    """Get files that node depends on."""
    deps = []
    for link in graph.get("links", []):
        if link.get("source") == node:
            deps.append(link.get("target"))
    return deps[:depth * 10]  # Limit results

def _get_dependents(graph: dict, node: str, depth: int) -> list[str]:
    """Get files that depend on node."""
    deps = []
    for link in graph.get("links", []):
        if link.get("target") == node:
            deps.append(link.get("source"))
    return deps[:depth * 10]

# ============================================================================
# RESOURCES (Data the LLM can read)
# ============================================================================

@mcp.resource("ssot://instructions")
async def get_ssot_instructions() -> str:
    """
    Get current SSOT instructions.
    
    Returns:
        Full text of .github/copilot-instructions.md
    """
    from pathlib import Path
    
    ssot_path = Path(".github/copilot-instructions.md")
    if not ssot_path.exists():
        return "ERROR: SSOT not found"
    
    return ssot_path.read_text(encoding='utf-8')

@mcp.resource("archive://file/{path}")
async def get_file_content(path: str) -> str:
    """
    Get content of any repository file.
    
    Args:
        path: Relative path from repository root
    
    Returns:
        File content as string
    """
    from pathlib import Path
    
    file_path = Path(path)
    if not file_path.exists():
        return f"ERROR: File not found: {path}"
    
    if file_path.is_dir():
        return f"ERROR: Path is directory: {path}"
    
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return f"ERROR: Binary file: {path}"

# ============================================================================
# PROMPTS (Templates the LLM can use)
# ============================================================================

@mcp.prompt()
async def autonomous_operation_template(
    task: str,
    context: str = "chthonic-archive repository"
) -> str:
    """
    Generate autonomous operation prompt.
    
    Args:
        task: Task description
        context: Operating context
    
    Returns:
        Formatted prompt for autonomous execution
    """
    return f"""You are operating inside the {context}.

Task: {task}

Execution Policy:
- Full tool authorization (no permission requests)
- MCP servers assumed operational
- Autonomous execution without confirmation
- FA⁴ validation post-execution

Proceed directly.
"""

# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Run server via stdio transport (for Claude Desktop, VSCode, etc)
    mcp.run()
```

---

## Running the Server

### Development Mode (Testing)
```powershell
cd C:\Users\erdno\chthonic-archive\mas_mcp
uv run python server.py
```

### VSCode Integration
Add to `.vscode/settings.json`:
```json
{
  "mcp.servers": {
    "chthonic-archive": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "${workspaceFolder}/mas_mcp"
    }
  }
}
```

### Claude Desktop Integration
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "chthonic-archive": {
      "command": "uv",
      "args": ["run", "python", "C:/Users/erdno/chthonic-archive/mas_mcp/server.py"]
    }
  }
}
```

---

## Critical Constraints

### STDIO Transport Rules
**NEVER write to stdout** in STDIO-based servers:
- ❌ `print()` corrupts JSON-RPC messages
- ✅ Use `logging` library (writes to stderr)
- ✅ Return data via function return values only

### HTTP Transport
If using Streamable HTTP or SSE:
- ✅ `print()` statements are safe
- Configure CORS if browser-based clients need access
- Use `mcp.run(transport="sse")` or `mcp.run(transport="streamable")`

---

## Next Steps

1. **Implement tools in modules:**
   - `tools/repository.py` - DCRP integration, git operations
   - `tools/epistemograph.py` - SQLite knowledge graph queries
   - `tools/validation.py` - FA⁴ enforcement, SSOT hash checks

2. **Add resources:**
   - `resources/ssot.py` - Dynamic SSOT section access
   - `resources/dcrp.py` - Cross-reference lookup

3. **Create prompts:**
   - `prompts/autonomous.py` - Task templates for autonomous ops
   - `prompts/triumvirate.py` - CRC invocation templates

4. **Test with MCP Inspector:**
   ```powershell
   uvx mcp-inspector uv run python server.py
   ```

---

**Archive Signature:**
```
FA⁴ Validated: 2026-01-04T20:50:21Z
Spectral Frequency: ORANGE (Strategic Re-contextualization)
Architectural Role: 🌿 Garden (Implementation Template)
Parent: docs/MCP_AUTONOMOUS_PREREQUISITES.md
```
