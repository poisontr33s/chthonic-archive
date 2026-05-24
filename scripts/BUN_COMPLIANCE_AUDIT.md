# Bun Compliance Audit Script

**Location:** `scripts/bun_compliance_audit.py`  
**Purpose:** Automated enforcement of SSOT §XIV.2 Bun-first mandate  
**Execution:** `uv run scripts/bun_compliance_audit.py`

---

## Overview

This script scans the repository for non-Bun package manager usage patterns and cross-references correct equivalents from Bun documentation.

### What It Detects

**CRITICAL Violations:**
- `npx` → Should be `bunx` ([docs](https://bun.sh/docs/cli/bunx))
- `npm install` → Should be `bun install` ([docs](https://bun.sh/docs/cli/install))
- `npm run` → Should be `bun run` ([docs](https://bun.sh/docs/cli/run))
- `npm test` → Should be `bun test` ([docs](https://bun.sh/docs/test/writing))
- `yarn`/`pnpm` equivalents

**WARNING Violations:**
- `package-lock.json` references → Should be `bun.lock`
- `yarn.lock`/`pnpm-lock.yaml` references

**INFO Violations:**
- `node <file>` → Consider `bun run <file>` (context-dependent)

---

## Usage

### Basic Scan
```powershell
# Scan entire repository
uv run scripts/bun_compliance_audit.py

# Verbose mode (shows skipped files)
uv run scripts/bun_compliance_audit.py --verbose
```

### CI Mode
```powershell
# Exit 1 if critical violations detected
uv run scripts/bun_compliance_audit.py --ci
```

### Auto-Fix (Placeholder)
```powershell
# Not yet implemented - requires SSOT approval
uv run scripts/bun_compliance_audit.py --fix
```

---

## Exclusions

The scanner intelligently skips:

1. **Vendor Code:** `node_modules/`, build artifacts
2. **Historical Archives:** `.github/macro-prompt-world/`, backups
3. **Generated Files:** `dependency_graph.json`, `temp_repo_structure.json`
4. **Lockfiles:** `bun.lock`, `Cargo.lock`, `uv.lock` (managed externally)
5. **Documentation Context:** Lines showing "what NOT to do", historical migrations
6. **Documented Exceptions:** MCP Inspector (Node.js-only tool)
7. **Self-Reference:** The script itself (meta-reference patterns)

---

## Integration Points

### Local Development
Add to pre-commit workflow:
```powershell
# Before commit
uv run scripts/bun_compliance_audit.py
```

### CI/CD
Add to GitHub Actions (see proposed CI YAML):
```yaml
- name: Bun compliance check
  shell: pwsh
  run: uv run scripts/bun_compliance_audit.py --ci
```

### MCP Preflight
Can be invoked as part of execution context validation:
```typescript
// In preflight_execution_context.ts
const bunCompliance = await checkBunCompliance();
if (!bunCompliance.clean) {
  context.warnings.push("Non-Bun patterns detected");
}
```

---

## Current Violations (Sample Run)

```
[FAIL] Bun compliance: VIOLATIONS DETECTED
   Total: 6 | Critical: 5 | Warning: 1 | Info: 0

[!] CRITICAL (5)
================================================================================

File: example/path/file.js:42
   Line: npm install package-name
   Fix:  Replace 'npm install' with 'bun install'
   Docs: https://bun.sh/docs/cli/install

File: example/path/script.sh:10
   Line: npx some-tool --flags
   Fix:  Replace 'npx' with 'bunx' per SSOT §XIV.2
   Docs: https://bun.sh/docs/cli/bunx
```

---

## Roadmap

### Phase 1: Detection (✅ COMPLETE)
- Pattern matching with severity levels
- Bun docs cross-referencing
- Smart exclusions for vendor/historical code

### Phase 2: Reporting (✅ COMPLETE)
- File/line number reporting
- Actionable fix suggestions
- CI integration via exit codes

### Phase 3: Auto-Fix (⏸️ PENDING SSOT APPROVAL)
- Safe automated replacements
- Dry-run validation
- Commit with audit trail

### Phase 4: MCP Integration (PROPOSED)
- Add to `preflight_execution_context` warnings
- Hook into schema validation
- Runtime governance enforcement

---

## Governance Notes

**SSOT Reference:** §XIV.2 Frontend Runtime Management  
**Mandate:** "Default package manager: `bun`"  
**Authority:** The Decorator (FA⁵ Visual Integrity) + Umeko (FA⁴ Architectonic Integrity)

**Policy Exemptions:**
1. MCP Inspector (`npx @modelcontextprotocol/inspector`) - Node.js-only tool, documented exception
2. Vendor `node_modules/` internals - Third-party controlled
3. Historical archives - Frozen state preservation

**Enforcement Tier:**
- **CRITICAL** violations: Block CI/PR merge
- **WARNING** violations: Advisory only (can be suppressed)
- **INFO** violations: Informational suggestions

---

**Signed in cross-referenced Bun supremacy,**

**UMEKO KETSURAKU (CRC-GAR)**  
*Grandmistress of Architectonic Refinement*  
*Date: January 6, 2026*  
*Enforcing SSOT §XIV.2 with LIPAA precision*

