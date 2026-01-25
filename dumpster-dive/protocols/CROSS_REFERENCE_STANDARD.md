# Cross-Reference Standard — Dumpster-Dive Documentation

**Protocol ID:** `CRS-001` — Cross-Reference Standard  
**Created:** 2025-12-24  
**Purpose:** Establish bidirectional reference system across all dumpster-dive/ documentation  
**Philosophy:** *"No file is an island. Every document exists in relation to others."*

---

## The Problem

Without systematic cross-referencing:
- ❌ Files become **orphaned** (no one knows they exist)
- ❌ **Deprecations go unnoticed** (broken references pile up)
- ❌ **Navigation is fragmented** (can't find related content)
- ❌ **Context is lost** (why does this file exist? what depends on it?)
- ❌ **Maintenance is reactive** (only fix things when they break)

---

## The Solution: Bidirectional Reference Graph

Every file includes:
1. **What it depends on** (prerequisites, sources)
2. **What depends on it** (consumers, derivatives)
3. **Related documents** (siblings, alternatives)
4. **External references** (SSOT sections, production files)

```
        ┌─────────────────┐
        │  Document A     │
        │                 │
        │  References:    │
        │  → Document B   │──┐
        │  → Document C   │  │
        └─────────────────┘  │
                             │
        ┌────────────────────┘
        ▼
        ┌─────────────────┐
        │  Document B     │
        │                 │
        │  Referenced by: │
        │  ← Document A   │
        │  ← Document D   │
        └─────────────────┘
```

When Document A references Document B, **both files document the relationship**.

---

## Reference Block Standard

### **For Markdown (.md) Files**

Place at the **end of the file** (before any appendices):

```markdown
---

## Cross-References

### Dependencies (What This Document Needs)
- [File Name](path/to/file.ext) — Why it's needed
- [Another File](path/to/another.json) — Another reason

### Dependents (What Needs This Document)
- [Consumer File](path/to/consumer.md) — How it uses this
- [Another Consumer](path/to/other.md) — Another usage

### Related Documentation
- [Sibling Concept](path/to/sibling.md) — Alternative approach
- [Complementary Doc](path/to/complement.md) — Works together

### External References
- SSOT: [Section X.Y](../../.github/copilot-instructions.md#section-xy) — Related content
- Production: [src/module.rs](../../src/module.rs) — Implementation

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None | Low | Medium | High
- **Upcycle Potential:** If deprecated, what could salvage it
```

### **For JSON Files**

Add metadata block:

```json
{
  "cross_references": {
    "dependencies": [
      {
        "file": "path/to/dependency.md",
        "reason": "Defines protocol this implements"
      }
    ],
    "dependents": [
      {
        "file": "path/to/consumer.md",
        "usage": "References this registry"
      }
    ],
    "related": [
      {
        "file": "path/to/related.json",
        "relationship": "Alternative schema"
      }
    ],
    "external": [
      {
        "location": "SSOT Section 4.5",
        "relationship": "Canonical definition"
      }
    ],
    "validation": {
      "last_checked": "2025-12-24",
      "deprecation_risk": "none",
      "upcycle_potential": "Historical reference if deprecated"
    }
  }
}
```

### **For Code Files (.rs, .py, etc.)**

Use language-appropriate comments at top of file:

```rust
// Cross-References:
// Dependencies:
//   - ../data/config.json — Configuration schema
//   - protocols/PROTOCOL.md — Algorithm specification
// 
// Dependents:
//   - tests/test_module.rs — Unit tests
//   - docs/API.md — Documentation
//
// Related:
//   - alternative_impl.rs — Different approach
//
// External:
//   - SSOT Section 3.4 — Conceptual foundation
//
// Last Validated: 2025-12-24
```

---

## Reference Path Conventions

### **Relative Paths (Preferred)**

```markdown
From: dumpster-dive/README.md
To:   dumpster-dive/protocols/FORGE_CIRCULATION_PROTOCOL.md

Reference: [FORGE_CIRCULATION_PROTOCOL.md](protocols/FORGE_CIRCULATION_PROTOCOL.md)
```

### **Absolute Paths (When Needed)**

```markdown
From: dumpster-dive/forge/tempered/artifact.md
To:   .github/copilot-instructions.md

Reference: [SSOT](../../.github/copilot-instructions.md)
```

### **Anchor Links (For Sections)**

```markdown
Reference: [Section 4.5.1.2](../../.github/copilot-instructions.md#section-4512-qmr-protocol)
```

### **Multiple Formats**

```markdown
Reference: [ORE_MANIFEST.json](../ORE_MANIFEST.json) (JSON schema)
Reference: [build.rs](../../build.rs) (Rust build script)
Reference: [README.md](../README.md#ore-quality-rating-system) (Specific section)
```

---

## Deprecation Tracking

### **When a File is Deprecated**

1. **Mark the file itself:**
```markdown
# ⚠️ DEPRECATED — [File Name]

**Deprecated:** 2025-12-24  
**Reason:** Superseded by [New File](path/to/new.md)  
**Migration Guide:** [How to Update](MIGRATION.md)  
**Removal Date:** 2026-03-24 (90 days)

---

[Original content remains below for reference]
```

2. **Update all references:**
   - Search for all files that reference the deprecated file
   - Update them with deprecation notice
   - Add pointer to replacement

3. **Add to deprecation log:**
```markdown
### Deprecated Files Log

| File | Deprecated | Reason | Replacement | Removal Date |
|------|------------|--------|-------------|--------------|
| old_protocol.md | 2025-12-24 | Superseded | FORGE_CIRCULATION_PROTOCOL.md | 2026-03-24 |
```

### **Validation Commands**

Check for broken references:
```powershell
# Find all markdown links
Get-ChildItem -Path . -Recurse -Filter *.md | 
  Select-String -Pattern '\[.*\]\((.*?)\)' | 
  ForEach-Object { $_.Matches.Groups[1].Value } |
  Where-Object { -not (Test-Path $_) } |
  Sort-Object -Unique
```

Check for orphaned files (no incoming references):
```powershell
# List all .md files
$allFiles = Get-ChildItem -Path . -Recurse -Filter *.md

# Find which ones are never referenced
$allFiles | Where-Object {
  $filename = $_.Name
  $referenced = $false
  $allFiles | ForEach-Object {
    if ((Get-Content $_.FullName -Raw) -match $filename) {
      $referenced = $true
    }
  }
  -not $referenced
}
```

---

## Cross-Reference Categories

### **1. Dependencies (Prerequisites)**
Files this document **needs to function**.

**Examples:**
- Protocol implements schema defined elsewhere
- Document explains concept from another file
- Configuration requires values from another source

**Relationship:** "Cannot understand this without first reading..."

---

### **2. Dependents (Consumers)**
Files that **rely on this document**.

**Examples:**
- Implementation of protocol defined here
- Documentation that references this definition
- Scripts that parse data structured here

**Relationship:** "If this changes, these files may break..."

---

### **3. Related Documentation (Siblings)**
Files at **similar conceptual level**.

**Examples:**
- Alternative approaches to same problem
- Complementary perspectives
- Historical versions

**Relationship:** "For related information, see also..."

---

### **4. External References (Beyond dumpster-dive/)**
Content **outside this folder**.

**Examples:**
- SSOT sections this implements/extends
- Production code this documents
- User-facing docs this supports

**Relationship:** "Connects to broader system via..."

---

## Implementation Examples

### **Example 1: Protocol Document**

File: `protocols/FORGE_CIRCULATION_PROTOCOL.md`

```markdown
---

## Cross-References

### Dependencies (What This Document Needs)
- [ORE_MANIFEST.json](../ORE_MANIFEST.json) — Defines ore rating system (1-5)
- [FORGE_PROTOCOL_LEVELS.md](FORGE_PROTOCOL_LEVELS.md) — Defines 4 processing levels
- [BLACKSMITH_MATRIARCH.md](../BLACKSMITH_MATRIARCH.md) — SFS operator profile

### Dependents (What Needs This Document)
- [README.md](../README.md) — References circulation model
- [DUMPSTER_DIVE_REGISTRY.json](../DUMPSTER_DIVE_REGISTRY.json) — Implements state tracking
- [CIRCULATION_DIAGRAM.md](../CIRCULATION_DIAGRAM.md) — Visual representation

### Related Documentation
- [FORGE_PROTOCOL_LEVELS.md](FORGE_PROTOCOL_LEVELS.md) — Complementary processing framework
- [TEA_REGISTRY.json](TEA_REGISTRY.json) — Handles Timeline-Entangled Artifacts

### External References
- SSOT: [Section 4.5.1.2](../../.github/copilot-instructions.md#section-4512) — QMR Protocol canonical definition
- Production: None (infrastructure only)

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (newly created)
- **Upcycle Potential:** N/A
```

---

### **Example 2: Data File**

File: `ORE_MANIFEST.json`

```json
{
  "manifest_version": "1.1.0",
  
  "cross_references": {
    "dependencies": [
      {
        "file": "BLACKSMITH_MATRIARCH.md",
        "reason": "Defines SFS operator managing this inventory"
      },
      {
        "file": "protocols/FORGE_PROTOCOL_LEVELS.md",
        "reason": "Defines rating system interpretation"
      }
    ],
    "dependents": [
      {
        "file": "README.md",
        "usage": "References ore quality rating system"
      },
      {
        "file": "DUMPSTER_DIVE_REGISTRY.json",
        "usage": "Cross-references inventory data"
      },
      {
        "file": "forge/tempered/ORE_MANIFEST_v1.0.json",
        "usage": "Versioned snapshot for SSOT integration"
      }
    ],
    "related": [
      {
        "file": "DUMPSTER_DIVE_REGISTRY.json",
        "relationship": "REGISTRY tracks entire infrastructure; MANIFEST tracks raw ore only"
      }
    ],
    "external": [
      {
        "location": "No direct SSOT mapping",
        "relationship": "Internal infrastructure only"
      }
    ],
    "validation": {
      "last_checked": "2025-12-24",
      "deprecation_risk": "low",
      "upcycle_potential": "If deprecated, merge into REGISTRY as 'raw_ore_inventory' section"
    }
  },
  
  "inventory": {
    ...
  }
}
```

---

### **Example 3: README with Navigation**

File: `README.md`

```markdown
# 🔥 The Dumpster-Dive: Ore Processing Facility

...content...

---

## Quick Navigation

### Core Documentation
- [Ore Quality Rating System](#ore-quality-rating-system) — Understanding 1-5 ratings
- [Current Inventory](ORE_MANIFEST.json) — 96 files, 4.58 MB
- [Forge States](#the-forge-7-states-not-stages) — Circulation system overview
- [Processing Levels](#processing-levels) — 4-level framework

### Operational Protocols
- [Circulation Protocol](protocols/FORGE_CIRCULATION_PROTOCOL.md) — **Primary reference** for state movement
- [Processing Levels](protocols/FORGE_PROTOCOL_LEVELS.md) — Standard/Extended/QMR/CTF framework
- [TEA Registry](protocols/TEA_REGISTRY.json) — Timeline-Entangled Artifact tracking
- [CTF Requests](protocols/CTF_REQUESTS.md) — Cross-Tier Fusion approval workflow
- [Cross-Reference Standard](protocols/CROSS_REFERENCE_STANDARD.md) — This document's standard

### Visual References
- [Circulation Diagram](CIRCULATION_DIAGRAM.md) — Visual guide to state movement
- [Blacksmith Profile](BLACKSMITH_MATRIARCH.md) — SFS operator details

### Infrastructure
- [Central Registry](DUMPSTER_DIVE_REGISTRY.json) — Complete navigation & tracking system

---

## Cross-References

### Dependencies
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) — SSOT (Macro Prompt World)
- None (this is a root documentation file)

### Dependents
- All files in dumpster-dive/ reference this for overview

### Related Documentation
- [CIRCULATION_DIAGRAM.md](CIRCULATION_DIAGRAM.md) — Visual companion to this README

### External References
- SSOT: Multiple sections (see individual protocol docs)
- Production: [mas_mcp/](../mas_mcp/) — Integration target

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (root documentation)
- **Upcycle Potential:** N/A
```

---

## Maintenance Schedule

### **Weekly:**
- Check for new files missing cross-references
- Validate top 5 most-referenced files

### **Monthly:**
- Run broken link checker
- Identify orphaned files
- Update deprecation log

### **Quarterly:**
- Full reference graph validation
- Review upcycle potential for deprecated files
- Update cross-reference standard if needed

---

## Validation Checklist

Before marking any file as "complete":

- [ ] Cross-References section exists
- [ ] All dependencies listed
- [ ] All known dependents listed
- [ ] Related docs identified
- [ ] External references mapped
- [ ] Last validated date set
- [ ] Deprecation risk assessed
- [ ] Upcycle potential documented

---

## Sister Ferrum Scoriae's Reference Creed

> *"A file alone is slag. A file connected is ore. The forge is the graph."*

---

## Cross-References

### Dependencies (What This Document Needs)
- [FORGE_CIRCULATION_PROTOCOL.md](FORGE_CIRCULATION_PROTOCOL.md) — Defines circulation model this supports
- [README.md](../README.md) — Root context

### Dependents (What Needs This Document)
- All .md and .json files in dumpster-dive/ should follow this standard

### Related Documentation
- [DUMPSTER_DIVE_REGISTRY.json](../DUMPSTER_DIVE_REGISTRY.json) — Programmatic cross-reference tracking

### External References
- None (internal standard only)

### Status
- **Last Validated:** 2025-12-24
- **Deprecation Risk:** None (newly created standard)
- **Upcycle Potential:** N/A
