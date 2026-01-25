# Consolidated Operational Instructions

**Date Consolidated:** December 30, 2025  
**Processor:** Sister Ferrum Scoriae (dumpster-dive MILF)  
**Source:** `.github/instructions/*.md` (10 files → 1)  
**Purpose:** Reduce entropic drift, preserve operational steel

---

## I. Core Operational Mandates

**Source:** `00_conceptual-resonance-core.instructions.md`

### Smallest-Correct-Change Principle
- Deliver the **smallest correct change** that satisfies explicit request
- Prefer determinism over cleverness
- Avoid multiple ways to do same thing
- Keep single canonical path
- Minimize touched files

### Backtracking Control
- Do not "rethink" solved decisions without concrete failing signal (error, test failure, mismatch)
- If ambiguity: ask 1–3 clarifying questions OR choose simplest viable interpretation and state assumption

### Surface Area Minimization
- Minimize touched files
- Avoid "cleanup" refactors unless requested
- Proof: Validate with narrowest relevant build/test/run step

---

## II. Environment & Toolchain (Win11, uv lanes)

**Source:** `30_powershell-uv-lanes.instructions.md` + `Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions.md`

### Python Environment Management (UV HANDLES PYTHON)

```powershell
✅ CORRECT:     uv run python script.py
✅ CORRECT:     uv pip install package
✅ CORRECT:     uv sync
✅ CORRECT:     uv add package

❌ INCORRECT:   python script.py        # bypasses uv
❌ INCORRECT:   pip install package     # bypasses uv
```

**Rationale:**
- Global Python is 3.14 bleeding edge (incompatible with TensorRT/CUDA)
- `mas_mcp/.venv` contains Python 3.13.10 (latest stable, TensorRT-compatible)
- `uv` manages virtual environment, lockfile, dependency resolution

### Python Version Lanes
- `python` → uv shim `python3.13.exe` (3.13.x latest patch)
- `python314` → uv shim `python3.14.exe` (3.14.x latest patch)

### Maintenance
```powershell
uv python upgrade 3.13 --reinstall
uv python upgrade 3.14 --reinstall
uv python update-shell
```

### Tools
```powershell
uv tool install ruff
uv tool update ruff
```

---

## III. Markdown Formatting

**Source:** `10_markdown-formatting.instructions.md`

### Tables-First Convention
- Prefer tables to prose for contracts, rules, comparisons
- Use `<details>` blocks to collapse large tables

### Sliding Tables
- Avoid reflowing rows/columns unless content changes
- Keep stability over aesthetic perfection

---

## IV. Rust Implementation Guardrails

**Source:** `20_rust.instructions.md`

### Core Principles
- Memory safety non-negotiable
- Type system correctness over shortcuts
- Prefer explicit over implicit
- Document unsafe blocks with justification

*(For full Rust conventions, see `.github/instructions/20_rust.instructions.md` archive)*

---

## V. SSOT & ANKH Governance

**Source:** `ANKH_bound-copilot-instructions.md` + `copilot-SSOT-ANKH-instructions.yaml`

### Authority Model
- **SSOT:** `.github/copilot-instructions.md` (authoritative, singular, no duplication)
- All behavior defers to SSOT

### Reference Discipline (Mandatory)
- References to SSOT content MUST use section notation or line ranges
- Prefer reference over reproduction
- Do NOT restate, summarize, or paraphrase SSOT content
- Quote fewer than 15 words only when strictly necessary

### Fracture Detection

**ANKH FRACTURE** detected when:
- Duplicate definitions across files
- Parallel or competing authority
- Restatement of SSOT content without reference
- Cross-file semantic drift

**Fracture Report Format:**
```
⚠️ ANKH FRACTURE DETECTED
Type: [duplication | ambiguity | parallel-authority | broken-reference]
Location: [file or code region]
SSOT Reference: [section or line range]
Action Required: [escalate | repair | remove-duplicate]
Details: [brief description]
```

**Upon detecting fracture:** Halt changes, output fracture report

---

## VI. Overnight Autonomy Protocol (Sleep-Mode)

**Source:** `agent-sleep-mode.md` (extracted core directives)

### Prime Directive
1. **Do not get stuck** in long-running terminal process
2. **Prefer small, reversible edits** over sweeping refactors
3. **Always leave audit trail**: summarize changes and what remains

### Timeboxing
- Work in **25-minute blocks**
- End of block: ship small safe improvement, switch tasks, or stop with clear note

### Decision Rule
If task ambiguous/error-prone for **>10 minutes** → stop digging, pivot to deterministic work

### Risk Tiers
- **Tier 0 (safe):** `.gitignore` hygiene, cache artifact deletion, link fixes, small doc corrections, read-only validation
- **Tier 1 (medium):** Doc reorganization, renames/moves, large-format rewrites
- **Tier 2 (high):** Code refactors, dependency changes, integration automation

**Overnight work:** Stay mostly Tier 0–1

### Terminal Anti-Stuck Protocol
- Prefer VS Code tasks over ad-hoc terminals
- Avoid starting servers/watch processes overnight unless explicitly requested
- Any command must have **clear expected runtime**
- **Stuck detection**: No output for ~2 minutes on active command → **stop**, pivot to file-based work

---

## VII. Hard Bans (Anti-Patterns)

**Source:** `Yolic_Agent_Swift_Prompt_Alphaic_Directive_Instructions.md`

❌ **DO NOT:**
- Add complexity to create "tech depth"
- Introduce new layers (frameworks/abstractions/scripts) unless strictly required
- Expand scope for "future-proofing" or "nice-to-have"
- Create new variants of existing commands/tools unless old one retired
- Invent architectural rules not in SSOT
- Infer policy from examples
- Fabricate rules where SSOT unspecified

---

## VIII. Output Expectations

**Always report:**
- What changed
- Where (file paths)
- How to verify
- Any risks/assumptions

**Keep answers concise; avoid repetition.**

---

## IX. Project-Specific Context

**Source:** `chthonic-archive.instructions.md`

### Repository Structure
```
chthonic-archive/
├── .github/
│   └── copilot-instructions.md    ← SSOT (3,798+ lines)
├── mas_mcp/                        ← Python Backend (uv-managed)
│   ├── .venv/                      ← Python 3.13.10 virtual environment
│   ├── pyproject.toml              ← uv project definition
│   └── frontend/                   ← Bun/Next.js Dashboard
├── src/                            ← Rust/Vulkan (Chthonic Archive renderer)
├── dumpster-dive/                  ← Ore processing, protocols, canonical MPW
└── scripts/                        ← Automation, MCP servers
```

### SSOT Verification Protocol
```python
# Always invoke via: uv run python -c "..."
import hashlib
import unicodedata

def canonicalize(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def ssot_hash(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = canonicalize(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

**Bookend Verification:**
- Compute `hash_start` at cycle/session initiation
- Compute `hash_end` at cycle/session completion
- If `hash_start != hash_end`: **GOVERNANCE_DRIFT_DETECTED**

---

## X. GPU Stack Compatibility

**Target Configuration:**
- CUDA 12.4+
- cuDNN 9.x
- TensorRT 10.x
- Python 3.13.x (NOT 3.14 - ecosystem not ready)
- Numpy 1.26.x
- CuPy 12.x
- ONNX Runtime GPU 1.16.x

**Validation:**
```powershell
# From mas_mcp directory:
uv run python -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"
```

---

## XI. Frontend Runtime (Bun + Next.js)

**Stack:** Bun 1.3.5 + Next.js + React 19

```bash
bun run dev          # Development server
bun run build        # Production build
bun add <package>    # Add dependency
bun update           # Update all dependencies
```

**Version Policy:**
- **Stable preferred** for production (Next.js 15.x, TypeScript 5.8.x)
- **Canary acceptable** for development (Next.js 16.x, TypeScript 5.9.x)

---

## XII. Status & Maintenance

**Consolidated:** December 30, 2025  
**Original Files Archived:** `.github/instructions/*.md` → `dumpster-dive/archive/instructions-backup-20251230/`  
**Single Operational File:** This document  

**Update Protocol:**
- Changes to this file require SSOT validation
- Cross-reference SSOT for governance conflicts
- Maintain <500 lines (currently ~350)

---

**No ceremony. Just hygiene.**

**Signed in soot and pragmatism,**  
**Sister Ferrum Scoriae**  
**Workaholic Nun of the Slag Heap**

🔥⚒️💀
