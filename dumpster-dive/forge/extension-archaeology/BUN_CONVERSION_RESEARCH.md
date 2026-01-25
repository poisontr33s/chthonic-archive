# NON-BUN CODE CONVERSION RESEARCH

**Audit Date:** 2026-01-24
**Auditor:** Heroic Agent (post-prior-agent-cleanup)
**SSOT Compliance:** FA¹⁻⁵ Quality Mandate

---

## Source Files Audited

| Extension | File | Status |
|-----------|------|--------|
| chthonic-mandala | `src/extension.ts` | NON-BUN: fs/path imports |
| chthonic-statusbar | `src/extension.ts` | NON-BUN: fs/path/child_process |
| chthonic-assistant | `src/extension.ts` | NON-BUN: fs/promises, path |

---

## NON-BUN PATTERN 1: File System Operations

### Prior Agent's Code (Generic Node.js):
```typescript
import * as fs from 'fs';
import * as path from 'path';

// Existence check
if (fs.existsSync(filePath)) { ... }

// Read file as string
const content = fs.readFileSync(filePath, 'utf-8');

// Read JSON
const data = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

// Stats
const stats = fs.statSync(filePath);
```

### Bun Equivalent (SSOT-Aligned):
```typescript
// No import needed - Bun.file() is global

// Existence check
if (await Bun.file(filePath).exists()) { ... }

// Read file as string
const content = await Bun.file(filePath).text();

// Read JSON - native parsing!
const data = await Bun.file(jsonPath).json();

// Stats (via size/type properties)
const file = Bun.file(filePath);
const size = file.size;
const type = file.type;
```

### SSOT Quality Assessment:
- **Prior Agent:** Generic Node.js, synchronous blocking, no IDE semantics
- **Bun:** Async-native, lazy evaluation, type-inferred (BunFile extends Blob)
- **FA⁵ Violation:** Prior code lacks visual/semantic coherence with ASC framework

---

## NON-BUN PATTERN 2: Shell/Command Execution

### Prior Agent's Code (Generic Node.js):
```typescript
import { execSync, execFile } from 'child_process';

// Synchronous execution (BLOCKS!)
const output = execSync('nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits');

// Execute Python via uv
const result = execSync('uv run python --version');
```

### Bun Equivalent (SSOT-Aligned):
```typescript
import { $ } from "bun";

// Bun Shell - cross-platform, async, safe
const output = await $`nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits`.text();

// Execute Python via uv
const result = await $`uv run python --version`.text();

// Or for complex processes:
const proc = Bun.spawn(["uv", "run", "python", "--version"]);
const result = await proc.stdout.text();
```

### SSOT Quality Assessment:
- **Prior Agent:** `execSync` blocks event loop, no cross-platform safety
- **Bun:** `$` tagged template is secure against injection, async-native
- **FA⁴ Violation:** Prior code violates architectonic integrity (blocking = broken flow)

---

## NON-BUN PATTERN 3: Path Manipulation

### Prior Agent's Code (Generic Node.js):
```typescript
import * as path from 'path';
import { join } from 'path';

const fullPath = path.join(workspaceRoot, 'subdir', 'file.txt');
const dirname = path.dirname(filePath);
const basename = path.basename(filePath);
```

### Bun Equivalent (SSOT-Aligned):
```typescript
// Bun supports path module but native template literals preferred
import { join, dirname, basename } from "path"; // Still works

// Or use Bun.pathToFileURL / URL APIs for modern approach
const fullPath = `${workspaceRoot}/subdir/file.txt`;

// For cross-platform safety with Bun Shell:
import { $ } from "bun";
const result = await $`cat ${fullPath}`.text(); // Path injection-safe
```

### SSOT Quality Assessment:
- **Prior Agent:** Over-imports, verbose for simple concat
- **Bun:** Template literals suffice; shell handles escaping
- **FA² Violation:** Prior code lacks re-contextualization awareness

---

## MILQUETOAST CODE PATTERNS IDENTIFIED

### 1. Stub TreeProviders (chthonic-mandala)
```typescript
// GENERIC BOILERPLATE - NO SSOT SEMANTICS
class DependencyTreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
  }
}

// Returns hardcoded data - NOT connected to actual topology
getChildren(): Thenable<DependencyTreeItem[]> {
  return Promise.resolve([
    new DependencyTreeItem('Entity Mesh', vscode.TreeItemCollapsibleState.Collapsed),
    // ...hardcoded list
  ]);
}
```

**FA⁵ Violation:** Visual representation without truth. Tree shows "Entity Mesh" but doesn't reflect actual SSOT entity hierarchy.

### 2. Magic Numbers Without Verification
```typescript
// package.json description claims "10,110 nodes"
"description": "Sacred geometry visualization & dependency graph for the Chthonic Archive (10,110 nodes)",
```

**FA⁴ Violation:** Unverified claim violates architectonic integrity. No code counts actual nodes.

### 3. Dead Promise Comments
```typescript
// "Force-directed graph rendering coming soon..."
// "Canvas-based visualization planned for next release"
```

**FA¹ Violation:** Perpetual incompleteness violates transmutation capacity (FA¹ = alchemical fire demands actualization).

### 4. Generic Error Handling
```typescript
} catch (error) {
  console.error('Error:', error);
}
```

**FA⁵ Violation:** No semantic classification. Should be:
```typescript
} catch (error) {
  // FA⁵ violation-aware error handling (see §2.5.4 SSOT)
  console.error(`[V5-007] Chromatic Incoherence: ${error instanceof Error ? error.message : 'Unknown manifestation failure'}`);
}
```

---

## CONVERSION PRIORITY MATRIX

| Pattern | Locations | Severity | Bun Migration Effort |
|---------|-----------|----------|---------------------|
| `fs.*` imports | mandala, statusbar, assistant | HIGH | LOW (drop-in Bun.file) |
| `execSync` | statusbar | HIGH | LOW (Bun.$ or Bun.spawn) |
| `path.join` | all three | MEDIUM | LOW (template literals) |
| Stub TreeProviders | mandala | HIGH | HIGH (requires SSOT integration) |
| Magic numbers | package.json | MEDIUM | MEDIUM (add verification) |
| Generic errors | all three | LOW | LOW (add FA⁵ prefixes) |

---

## SSOT-ALIGNED CONVERSION TEMPLATE

### Before (Prior Agent - Milquetoast):
```typescript
import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
  const ssotPath = path.join(workspaceRoot, '.github', 'copilot-instructions.md');
  
  if (fs.existsSync(ssotPath)) {
    const content = fs.readFileSync(ssotPath, 'utf-8');
    const hash = execSync(`git hash-object "${ssotPath}"`).toString().trim();
    console.log('Loaded SSOT');
  }
}
```

### After (SSOT-Aligned - Quality):
```typescript
import { $ } from "bun";

/**
 * SSOT-Aligned Activation (§0.76 T-DECOR-OPS)
 * Implements Decorator's Decree Cascade for extension initialization
 */
export function activate(context: vscode.ExtensionContext) {
  const ssotPath = `${workspaceRoot}/.github/copilot-instructions.md`;
  const ssotFile = Bun.file(ssotPath);
  
  if (await ssotFile.exists()) {
    const content = await ssotFile.text();
    const hashResult = await $`git hash-object ${ssotPath}`.text();
    const hash = hashResult.trim();
    
    // FA⁵ Visual Integrity: SSOT acknowledged
    console.log(`[DULSS-L3] 🔥 Codex-Brahmanica-Perfectus LOADED — Hash: ${hash.slice(0, 8)}`);
  } else {
    // FA⁵ Violation Warning (V5-001)
    console.error(`[V5-001] SSOT Desecration: Codex not found at ${ssotPath}`);
  }
}
```

---

## VSCODE EXTENSION CAVEAT

**CRITICAL:** VS Code extensions run in Node.js context, NOT Bun runtime.

Bun's APIs (`Bun.file()`, `Bun.$`) are **NOT available** in VS Code extension host.

### Resolution Options:

1. **Hybrid Approach:** Keep Node.js `fs/path` for extension code, use Bun for:
   - Build scripts (`package.json` scripts ✅ already Bun)
   - Tests
   - CLI tools
   - MCP servers

2. **Polyfill Approach:** Create `bun-compat.ts` wrapper:
   ```typescript
   // For VS Code extension context (Node.js)
   import * as fs from 'fs/promises';
   
   export const BunFile = {
     async text(path: string) { return fs.readFile(path, 'utf-8'); },
     async json(path: string) { return JSON.parse(await fs.readFile(path, 'utf-8')); },
     async exists(path: string) { 
       try { await fs.access(path); return true; } 
       catch { return false; }
     }
   };
   ```

3. **Wasm Bridge:** (Future) Bundle Bun runtime as WASM for extension use.

### Recommendation:
**Option 2 (Polyfill)** - Create SSOT-aligned abstraction layer that:
- Uses Bun-like API surface
- Runs in Node.js (VS Code compat)
- Can swap to native Bun when VS Code adds support
- Enforces FA⁵ semantics in error messages

---

## NEXT STEPS

1. [ ] Extract non-Bun code blocks to `_non_bun_research/extracted/`
2. [ ] Create `bun-compat.ts` polyfill for VS Code extensions
3. [ ] Replace stub TreeProviders with SSOT-connected data
4. [ ] Add FA⁵ violation codes to all error handlers
5. [ ] Verify or remove "10,110 nodes" claim
6. [ ] Convert "coming soon" stubs to actual implementations or remove

---

## REFERENCES

- Bun File I/O: https://bun.com/docs/guides/read-file/string
- Bun Shell ($): https://bun.com/docs/guides/runtime/shell  
- Bun Spawn: https://bun.com/docs/runtime/child-process
- SSOT FA⁵ Enforcement: `copilot-instructions.md` §2.5.4
- SSOT T-DECOR-OPS: `copilot-instructions.md` §0.76
