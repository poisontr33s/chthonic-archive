# Python Metabolic Standard v3 (PMS-v3) Transition

**Date:** 2026-01-31
**Status:** Complete
**Supersedes:** PMS-v2 (Snail Shell Philosophy)

---

## Executive Summary

Transitioned the Chthonic Archive from **Script Lane** (PEP 723 inline metadata) to **Project Lane** (pyproject.toml SSOT). This eliminates dependency fragmentation, improves Windows IDE discovery, and prevents ephemeral environment spin-up on each `uv run`.

---

## The Problem: Snail Shell Philosophy (PMS-v2)

PMS-v2 mandated each Python script carry its own dependencies via PEP 723 `/// script` blocks:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = ["fastmcp"]
# ///
```

**Issues on Windows 11:**
1. Each `uv run` created ephemeral environments
2. Dependencies drifted between scripts
3. IDE discovery failed (no single lockfile)
4. The `env -S` shebang is Unix-specific, non-functional on Windows

---

## The Solution: Unified Metabolic Field (PMS-v3)

All dependencies consolidated in `pyproject.toml`. Scripts retain only the universal shebang:

```python
#!/usr/bin/env python3
"""
Docstring begins immediately after shebang.
@SID: ...
"""
```

**Benefits:**
- Single `uv.lock` for entire project
- `uv run` uses project `.venv` (no spin-up)
- IDE discovers all dependencies
- Cross-platform compatible

---

## Changes Made

### 1. Governance Update
**File:** `.github/instructions/python-scripting.instructions.md`

| Section | v2 | v3 |
|---------|----|----|
| Version | Metabolic-Standard-v2 | Metabolic-Standard-v3 |
| Header Sacrament | PEP 723 required | PEP 723 **prohibited** |
| Philosophy | Snail Shell (self-contained) | Unified Metabolic Field |
| Dependencies | Per-script | pyproject.toml only |

### 2. Dependency Consolidation
**File:** `pyproject.toml`

```toml
dependencies = [
    "networkx>=3.6",
    "fastmcp>=0.1.0",  # Added from script blocks
]
```

### 3. PEP 723 Block Removal
**Files purged (5 total):**

| File | Previous Dependencies |
|------|----------------------|
| `scripts/autonomous_coordinator.py` | `[]` |
| `scripts/extract_session_value.py` | `[]` |
| `scripts/run_narrative_scan.py` | `["fastmcp"]` |
| `scripts/run_qualia_check.py` | `["fastmcp"]` |
| `scripts/test_narrative_scan.py` | `["fastmcp"]` |

### 4. Validation
```
uv sync → Resolved 90 packages, Installed 86
grep -r "/// script" → 0 results
```

---

## Exception: Standalone Distribution Scripts

Scripts intended for **external use** (no `scripts.*` or `mas_mcp.*` imports) may retain PEP 723 if explicitly documented as "standalone."

---

## Verification Commands

```powershell
# Confirm no PEP 723 blocks remain
rg "/// script" --type py

# Confirm lockfile integrity
uv sync

# Test execution via Project Lane
uv run scripts/run_narrative_scan.py
```

---

## Pending: SID Standardization

The `@SID` (Semantic Identity) convention requires a **separate pass** across:
- All `.py` files in the polyglot codebase
- Rust, TypeScript, and PowerShell files (cross-language alignment)
- The `ankh_atlas/` system (ankhological transition)

**Status:** Deferred — requires deeper intel on script purposes before standardization.
**Dependency:** Ankh research completion, SSOT stabilization.

This is **not** part of PMS-v3. It's a parallel governance track.

---

## Cross-References

- **Governance:** [python-scripting.instructions.md](../../.github/instructions/python-scripting.instructions.md)
- **Research:** [Accurate_PEP_Standards_Win11_Uv_Python.md](./Accurate_PEP_Standards_Win11_Uv_Python.md)
- **Manifest:** [pyproject.toml](../../pyproject.toml)
- **Ankh Atlas:** `ankh_atlas/` (pending transition)

---

## Key Insight

> **Project Lane > Script Lane** for Windows + `uv` because the kernel doesn't execute shebangs. PEP 723 adds overhead without benefit when a `pyproject.toml` exists.

---

**Document Metadata**
- Created: 2026-01-31
- Author: Claude (Opus 4.5)
- Session: Codex Onboarding + PMS-v3 Transition
