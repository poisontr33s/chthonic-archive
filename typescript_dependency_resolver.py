#!/usr/bin/env python3
"""
TypeScript Dependency Resolution for DCRP.

Provides regex-based import extraction for .ts and .tsx files,
with Bun path alias resolution (@/ → mas_mcp/frontend/).

Author: The Decorator (Session 3, Phase 2)
Date: 2026-01-01
"""

import re
from pathlib import Path
from typing import Set


class TypeScriptRegexExtractor:
    """
    Lightweight TS/TSX import extraction via regex.
    
    Handles:
    - ES6 import statements (named, default, namespace)
    - Dynamic imports (await import("path"))
    - Re-exports (export { X } from "path")
    - Bun path aliases (@/ → mas_mcp/frontend/)
    - Relative imports (./path, ../path)
    - Index file resolution (./components → ./components/index.ts)
    """
    
    # Import/export patterns (non-greedy, handles multi-line)
    IMPORT_PATTERNS = [
        # import { X, Y } from "./path"
        # import { X as Y, Z } from "@/path"
        r'import\s+\{[^}]*\}\s+from\s+["\']([^"\']+)["\']',
        
        # import * as Module from "./path"
        r'import\s+\*\s+as\s+\w+\s+from\s+["\']([^"\']+)["\']',
        
        # import Default from "./path"
        # import Default, { Named } from "./path"
        r'import\s+\w+(?:\s*,\s*\{[^}]*\})?\s+from\s+["\']([^"\']+)["\']',
        
        # const X = await import("./path")
        # const X = import("./path")
        r'import\s*\(\s*["\']([^"\']+)["\']\s*\)',
        
        # export { X } from "./path"
        # export { X as Y } from "./path"
        r'export\s+\{[^}]*\}\s+from\s+["\']([^"\']+)["\']',
        
        # export * from "./path"
        # export * as Namespace from "./path"
        r'export\s+\*(?:\s+as\s+\w+)?\s+from\s+["\']([^"\']+)["\']',
        
        # import type { X } from "./path" (TypeScript type-only imports)
        r'import\s+type\s+\{[^}]*\}\s+from\s+["\']([^"\']+)["\']',
    ]
    
    def extract_imports(self, ts_file: Path) -> Set[str]:
        """
        Extract all import paths from TS/TSX file.
        
        Args:
            ts_file: Path to TypeScript source file
        
        Returns:
            Set of import path strings (unresolved)
        """
        try:
            content = ts_file.read_text(encoding='utf-8')
        except Exception as e:
            # Silently skip unreadable files (binary, permission issues)
            return set()
        
        imports = set()
        
        # Apply all patterns
        for pattern in self.IMPORT_PATTERNS:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.update(matches)
        
        return imports
    
    def resolve_import_path(
        self,
        import_path: str,
        source_file: Path,
        repo_root: Path
    ) -> Path | None:
        """
        Resolve TypeScript import path to actual file.
        
        Resolution order:
        1. Bun path aliases (@/ → mas_mcp/frontend/)
        2. Relative imports (./lib → same_dir/lib.ts)
        3. Parent imports (../utils → parent_dir/utils.ts)
        4. Try extensions: .ts, .tsx, .js, .jsx, none
        5. Try index files: ./components → ./components/index.ts
        
        Args:
            import_path: Import specifier from source code
            source_file: File containing the import
            repo_root: Repository root directory
        
        Returns:
            Resolved Path if file exists, None otherwise
        """
        
        # Skip Node built-ins and npm packages
        if not (import_path.startswith('.') or import_path.startswith('@/')):
            return None
        
        # Handle Bun path aliases (@/ → frontend root)
        if import_path.startswith('@/'):
            base = repo_root / 'mas_mcp' / 'frontend'
            relative_path = import_path[2:]  # Strip "@/"
        
        # Relative imports (./file, ../parent/file)
        elif import_path.startswith('./') or import_path.startswith('../'):
            base = source_file.parent
            relative_path = import_path
        
        # Absolute imports (treat as package, skip)
        else:
            return None
        
        # Try file with various extensions
        for ext in ['.ts', '.tsx', '.js', '.jsx', '']:
            if relative_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                # Already has extension
                candidate = base / relative_path
            else:
                # Append extension
                candidate = (base / relative_path).with_suffix(ext)
            
            # Normalize and check existence
            try:
                candidate = candidate.resolve()
                if candidate.exists() and candidate.is_file():
                    return candidate
            except (OSError, RuntimeError):
                # resolve() can fail on invalid paths
                continue
        
        # Try index file resolution (./components → ./components/index.ts)
        index_dir = base / relative_path
        if index_dir.is_dir():
            for ext in ['.ts', '.tsx', '.js', '.jsx']:
                index_file = index_dir / f'index{ext}'
                try:
                    index_file = index_file.resolve()
                    if index_file.exists() and index_file.is_file():
                        return index_file
                except (OSError, RuntimeError):
                    continue
        
        # Resolution failed
        return None
    
    def extract_and_resolve(
        self,
        ts_file: Path,
        repo_root: Path
    ) -> Set[Path]:
        """
        Extract and resolve all dependencies from TS file.
        
        Convenience method combining extract_imports + resolve_import_path.
        
        Args:
            ts_file: TypeScript source file
            repo_root: Repository root
        
        Returns:
            Set of resolved dependency Paths
        """
        import_paths = self.extract_imports(ts_file)
        
        dependencies = set()
        for import_path in import_paths:
            resolved = self.resolve_import_path(import_path, ts_file, repo_root)
            if resolved:
                dependencies.add(resolved)
        
        return dependencies


# Standalone testing function
def test_extractor():
    """Test TypeScript extraction on repository files."""
    import sys
    
    repo_root = Path(__file__).parent
    extractor = TypeScriptRegexExtractor()
    
    # Test files
    test_files = [
        repo_root / 'scripts' / 'mcp_artisan_server.ts',
        repo_root / 'scripts' / 'sentry_init.ts',
        repo_root / 'scripts' / 'overnight_daemon.ts',
    ]
    
    print("TypeScript Dependency Extraction Test\n" + "=" * 60)
    
    for ts_file in test_files:
        if not ts_file.exists():
            print(f"⚠️  SKIP {ts_file.name} (not found)")
            continue
        
        # Extract raw imports
        imports = extractor.extract_imports(ts_file)
        
        # Resolve to actual files
        deps = extractor.extract_and_resolve(ts_file, repo_root)
        
        print(f"\n📄 {ts_file.name}")
        print(f"   Raw imports:     {len(imports)}")
        print(f"   Resolved deps:   {len(deps)}")
        
        if deps:
            print("   Dependencies:")
            for dep in sorted(deps):
                rel_path = dep.relative_to(repo_root)
                print(f"     → {rel_path}")
    
    print("\n" + "=" * 60)
    print("✓ Test complete")


if __name__ == '__main__':
    test_extractor()
