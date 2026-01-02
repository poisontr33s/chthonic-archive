"""
Tactile Feedback - Code Structure as Physical Texture
Uses AST import analysis to detect coupling
"""
import sys
import ast
from pathlib import Path

def analyze_texture(file_path: str) -> tuple[str, int]:
    """Analyze import coupling and map to texture descriptors"""
    try:
        code = Path(file_path).read_text(encoding='utf-8')
        tree = ast.parse(code)
        
        # Count imports
        import_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
        
        # Map import count to texture
        if import_count <= 3:
            texture = "🧵 SILK"
        elif import_count <= 6:
            texture = "🪨 SMOOTH"
        elif import_count <= 10:
            texture = "🌊 VELVET"
        elif import_count <= 15:
            texture = "🪵 ROUGH"
        else:
            texture = "⚡ SHARP"
        
        return texture, import_count
    except Exception as e:
        return f"ERROR: {e}", 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "autonomous_coordinator.py"
    
    print(f"✋ [TACTILE] Feeling code texture...")
    
    # Scan Python files
    files_to_scan = [
        "autonomous_coordinator.py",
        "scripts/code_scent.py",
        "scripts/mandala_topology.py",
        "unified_topology.py"
    ]
    
    print("   🧵 Texture Report:")
    for file in files_to_scan:
        if Path(file).exists():
            texture, imports = analyze_texture(file)
            print(f"      - {file}: {texture} ({imports} imports)")
