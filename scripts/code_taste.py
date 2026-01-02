"""
Gustatory Validation - Commit Quality as Flavor Profiles
Uses git diff stats to determine commit "taste"
"""
import subprocess
import sys

def analyze_taste() -> tuple[str, dict]:
    """Analyze last commit and map to flavor descriptors"""
    try:
        # Get diff stats for last commit
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            return "BLAND", {}
        
        # Parse stats
        stats_line = result.stdout.strip().split('\n')[-1] if result.stdout else ""
        
        # Extract numbers
        files_changed = 0
        insertions = 0
        deletions = 0
        
        if "file" in stats_line:
            parts = stats_line.split(',')
            for part in parts:
                if "file" in part:
                    files_changed = int(part.split()[0])
                elif "insertion" in part:
                    insertions = int(part.split()[0])
                elif "deletion" in part:
                    deletions = int(part.split()[0])
        
        # Determine flavor based on metrics
        net_growth = insertions - deletions
        
        if net_growth > 500:
            flavor = "🍰 SWEET"  # Large feature addition
        elif net_growth > 100:
            flavor = "🍷 UMAMI"  # Balanced growth
        elif net_growth > 0:
            flavor = "🍋 TANGY"  # Small refinement
        elif net_growth == 0:
            flavor = "🧂 SALTY"  # Refactoring only
        else:
            flavor = "🌶️ BITTER"  # Code removal
        
        return flavor, {
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "net_growth": net_growth
        }
    except Exception as e:
        return f"ERROR: {e}", {}

if __name__ == "__main__":
    print(f"👅 [GUSTATORY] Tasting commit quality...")
    flavor, stats = analyze_taste()
    print(f"   🍷 Flavor Profile: {flavor}")
    if stats:
        print(f"      Files changed: {stats['files_changed']}")
        print(f"      Insertions: +{stats['insertions']}")
        print(f"      Deletions: -{stats['deletions']}")
        print(f"      Net growth: {stats['net_growth']:+d} lines")
