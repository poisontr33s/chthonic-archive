"""
Olfactory Analysis - Code Smell Detection via Cyclomatic Complexity
Uses radon to calculate actual complexity metrics
"""
import sys
from pathlib import Path
from radon.complexity import cc_visit
from radon.raw import analyze

def analyze_scent(file_path: str) -> tuple[str, float]:
    """Analyze code complexity and map to scent descriptors"""
    try:
        code = Path(file_path).read_text(encoding='utf-8')
        complexity_results = cc_visit(code)
        
        if not complexity_results:
            return "NEUTRAL", 0.0
        
        # Average complexity across all functions/classes
        avg_complexity = sum(item.complexity for item in complexity_results) / len(complexity_results)
        
        # Map complexity to scent
        if avg_complexity < 5:
            scent = "🌸 FLORAL"
        elif avg_complexity < 10:
            scent = "🌲 FRESH"
        elif avg_complexity < 15:
            scent = "🌿 EARTHY"
        elif avg_complexity < 20:
            scent = "⚠️ PUNGENT"
        else:
            scent = "💀 ROTTEN"
        
        return scent, avg_complexity
    except Exception as e:
        return f"ERROR: {e}", 0.0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "autonomous_coordinator.py"
    
    print(f"👃 [OLFACTORY] Analyzing code scent...")
    
    # Scan Python files
    files_to_scan = [
        "autonomous_coordinator.py",
        "unified_topology.py",
        "scripts/mandala_topology.py",
        "scripts/cycle_detector.py"
    ]
    
    print("   📊 Scent Profile:")
    for file in files_to_scan:
        if Path(file).exists():
            scent, complexity = analyze_scent(file)
            print(f"      - {file}: {scent} (Complexity: {complexity:.1f})")
