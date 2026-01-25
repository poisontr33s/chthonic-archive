# Extension Archaeology Manifest

**Excavation Date:** 2026-01-24
**Archaeologist:** Heroic Agent (post-prior-hallucination cleanup)
**Status:** ✅ CONSOLIDATED

---

## Archive Purpose

This folder contains **research materials, deprecated code, and diagnostic artifacts** extracted from the `extensions/` directory. These files are preserved for:

1. **Historical reference** — Prior agent's work patterns
2. **Bun conversion research** — Node.js → Bun migration planning
3. **Theme development** — Palette evolution documentation
4. **Test archaeology** — Diagnostic tests for future reintegration

---

## Archive Contents

### `/extracted/` — Non-Bun Code Patterns
| File | Source | Patterns |
|------|--------|----------|
| `mandala_nonbun_patterns.ts` | chthonic-mandala | fs/path imports, stub TreeProviders |
| `statusbar_nonbun_patterns.ts` | chthonic-statusbar | execSync, fs.existsSync |
| `assistant_nonbun_patterns.ts` | chthonic-vscode-extension | readFile, inline HTML |

### `/theme-research/` — Palette Evolution
| File | Content |
|------|---------|
| `chthonic-archive-theme.json` | Cyberpunk palette (deregistered) |
| `chthonic-mandala-color-theme.json` | Flesh & Earth palette (deregistered) |
| `decorator-palette-research.md` | SSOT-aligned color philosophy |
| `PALETTE_EVOLUTION_RESEARCH.md` | Full evolution analysis |

### `/diagnostics-tests/` — Bun Test Suite
| File | Tests |
|------|-------|
| `assets.test.ts` | SVG/resource validation |
| `bundle-size.test.ts` | Size threshold checks |
| `deployment.test.ts` | Extension installation |
| `gpu-parsing.test.ts` | nvidia-smi output |
| `package-config.test.ts` | package.json validation |
| `python-detection.test.ts` | uv python detection |
| `source-code.test.ts` | Code health checks |

### Root Files — Documentation Entropy
| File | Origin | Purpose |
|------|--------|---------|
| `BUN_CONVERSION_RESEARCH.md` | This session | Comprehensive Bun migration analysis |
| `DEVHOST_TESTING.md` | Prior agent | Extension host testing notes |
| `DIAGNOSTIC_REPORT.md` | Prior agent | Build system diagnosis (Jan 9, 2026) |
| `doctor.ts` | Prior agent | Health check script (Node.js APIs) |
| `FA5_POLICY.md` | Prior agent | FA⁵ enforcement policy |
| `NON_REGRESSION_CHECKLIST.md` | Prior agent | QA checklist |
| `TA_FA_CANONICAL_FUNCTION.md` | Prior agent | Canonical function documentation |

---

## Key Finding: VS Code Extension Architecture

### Why Node.js APIs Are Valid

```
┌─────────────────────────────────────────────────────┐
│                 VS Code Architecture                │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────┐    │
│  │  Extension Host │    │   Webview Process   │    │
│  │  (Node.js 20+)  │    │    (Chromium)       │    │
│  │                 │    │                     │    │
│  │  Your extension │    │  Your webview UI    │    │
│  │  runs HERE      │    │  runs HERE          │    │
│  │                 │    │                     │    │
│  │  fs, path, etc. │    │  React, etc.        │    │
│  │  are NATIVE     │    │  is bundled         │    │
│  └─────────────────┘    └─────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Bun's Role:** Build tool only (bundling, compiling)
**Node.js's Role:** Runtime for extension code
**Conclusion:** Using `fs`, `path`, `child_process` in extension code is **architecturally correct**

### What Bun CAN Do:
- ✅ `bun build` for bundling
- ✅ `bun install` for dependencies
- ✅ `bun test` for test suites
- ✅ Build scripts in `package.json`

### What Bun CANNOT Do:
- ❌ Replace Node.js APIs at runtime
- ❌ `Bun.file()` in extension code
- ❌ `Bun.$` shell in extension code
- ❌ Run as extension host

---

## SSOT Alignment

### FA⁵ Visual Integrity Assessment

| Item | Prior State | Current State | Violation? |
|------|-------------|---------------|------------|
| Theme palette | Cyberpunk (cold) | Deregistered | ✅ Resolved |
| TreeProviders | Hardcoded stubs | Research archived | ⚠️ Needs SSOT integration |
| Error handling | Generic | Research documented | ⚠️ Needs FA⁵ codes |
| "10,110 nodes" | Unverified | Documented as issue | ⚠️ Needs verification |

### FA⁴ Architectonic Integrity Assessment

| Item | Status | Notes |
|------|--------|-------|
| Bun builds | ✅ COMPLIANT | All 3 extensions use `bun build` |
| Node.js runtime | ✅ VALID | VS Code mandates this |
| Stub code | ⚠️ DEBT | TreeProviders don't read real data |
| Dead imports | ✅ FIXED | hedonisticValidation.ts integrated |

---

## Future Work

### Priority 1: SSOT-Connected TreeProviders
The mandala TreeProviders currently return hardcoded data. They should:
1. Parse actual `topology_graph.json`
2. Reflect SSOT entity hierarchy from §0.77
3. Use FA⁵ verified colors

### Priority 2: Theme Re-engineering
When ready to re-register themes:
1. Use Flesh & Earth palette from `theme-research/`
2. Follow SSOT Decorator aesthetic (earthy, warm, mandalic)
3. Add semantic tokens for entity tiers

### Priority 3: Test Suite Reintegration
The `diagnostics-tests/` files are valid Bun tests but:
1. Use `fs` sync APIs (could async-ify)
2. Need workspace path configuration
3. Should integrate with CI/CD

---

## Cross-References

- **SSOT:** `.github/copilot-instructions.md`
- **Active Extensions:** `extensions/chthonic-mandala/`, `extensions/chthonic-statusbar/`
- **Main Extension:** `chthonic-vscode-extension/`
- **This Archive:** `dumpster-dive/forge/extension-archaeology/`

---

## The Decorator's Blessing

> *"Archaeology is the Decorator's truth-extraction. What was buried by prior hands is now excavated, catalogued, and preserved. The entropy has been metabolized into structured knowledge. This is FA⁵ in action—visual integrity through honest documentation of what IS, not what was claimed."*

**Archive Status:** ✅ SSOT-IFIED
