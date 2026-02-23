---
type: standard
category: governance
status: canonical
created: 2026-02-03
updated: 2026-02-24
author: Gemini-3 Pro (Deep Research)
ratified-by: Claude Code Opus 4.6
---

# Script Metadata & Shebang Standardization

**@SID:** STD_SCRIPT_METADATA_V2
**@Context:** Codebase Hygiene / Cross-Platform Compatibility
**@Purpose:** Define a robust, encoding-safe, and visually distinct header standard for all authored scripts.

> Ratified from `candidate` → `canonical` on 2026-02-24.
> Reconciled with PMS-v3 (Python Metabolic Standard v3) for unified governance.

---

## 1. The "Open-Sided" Metadata Envelope

To resolve persistent rendering issues with ASCII boxes (misaligned right borders due to emoji/Unicode width variation), we adopt the **Open-Sided Envelope**.

### Visual Style
- **Top Border:** `╔` followed by 80 `═` characters.
- **Left Border:** `║` followed by a single space.
- **Divider:** `╠` followed by 80 `═` characters.
- **Bottom Border:** `╚` followed by 80 `═` characters.
- **Right Border:** **NONE**. (Eliminates width calculation entirely).

### Template (Canonical)

```python
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <filename>
# ║ Module: <exports / key symbols>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: <WHITE|RED|BLUE|...>
# ║ Architectural Role: <INFRASTRUCTURE|THE GARDEN|...>
# ║ Semantic ID: <SID_UPPERCASE>
# ║ Purpose: <Concise description of utility>
# ║ Exports: <List of main functions/classes>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Cross-References (Bidirectional):
# ║   └─◄ <relative_path_to_dependency>
# ╚════════════════════════════════════════════════════════════════════════════
```

---

## 2. Cross-Platform Shebangs

We prioritize `env` for portability across Linux (Debian/Alpine), macOS, and Windows (via Git Bash/WSL).

| Language | Extension | Canonical Shebang | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | `.py` | `#!/usr/bin/env python3` | Works with `uv`, `venv` |
| **PowerShell** | `.ps1` | `#!/usr/bin/env pwsh` | Enables `./script.ps1` on Linux/Mac |
| **Bash** | `.sh` | `#!/usr/bin/env bash` | Avoids `/bin/bash` vs `/usr/bin/bash` |
| **Node/Bun** | `.ts`, `.js` | `#!/usr/bin/env bun` | Standardize on Bun runtime |

**Windows Note:** While Windows ignores shebangs natively, they are critical for:
1.  **WSL / Git Bash:** Allowing scripts to run seamlessly.
2.  **Python Launcher (`py.exe`):** Which *does* read shebangs to select versions.

---

## 3. Semantic Tags (The "Doc-Block")

Immediately following the visual envelope (or inside the module docstring for Python), we use **Semantic Tags** to create a searchable knowledge graph.

### Ontology
*   **`@SID`**: Unique, immutable identifier (e.g., `TOOL_AUDIT_V1`).
*   **`@Type`**: Artifact classification (e.g., `CLI Tool`, `Library`, `Config`).
*   **`@Context`**: Domain or lane (e.g., `Hygiene`, `DevOps`).
*   **`@SessionOrigin`**: Provenance (e.g., `SESSION_2026_02_03`).
*   **`@Implements`**: Link to a concept or spec (e.g., `CONCEPT_SSOT`).

### Implementation (Python Docstring)

```python
#!/usr/bin/env python3
"""
<filename> - <One-line description>

@SID:           <SID>
@Type:          <Type>
@Context:       <Context>
@Implements:    <Concept_ID>

<Detailed description...>
"""
```

---

## 4. Language-Specific Adaptations

### Python (`.py`) — PMS-v3 Canonical Layout

Python files follow a **specific ordering** ratified under PMS-v3:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Script description — narrative of intent.

@SID:           TOOL_EXAMPLE_V1
@Type:          Utility
"""

import sys
from pathlib import Path
```

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env python3` | Yes — shebang |
| 2 | `#-*- coding: utf-8 -*-` | Yes — tight, NO space after `#` |
| 3 | (blank) | Yes |
| 4+ | `"""` docstring with `@SID` + `@Type` `"""` | Yes |
| N | (blank) | Yes |
| N+1 | imports | — |

**Note**: The Decorator's Blessing envelope is **optional** for Python — the `@SID`/`@Type` docstring fulfills the semantic identity requirement. Scripts that carry the envelope keep it between the coding line and the docstring.

### PowerShell (`.ps1`)

```powershell
#!/usr/bin/env pwsh
# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <filename>.ps1
# ║ Module: <description>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: <COLOR>
# ║ Architectural Role: <ROLE>
# ║ Semantic ID: <SID>
# ╚════════════════════════════════════════════════════════════════════════════
```

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env pwsh` | Yes — shebang |
| 2+ | Decorator's Blessing envelope | Recommended |
| N | `@SID` within envelope or `<# #>` block | Recommended |

### TypeScript / TSX (`.ts`, `.tsx`)

```typescript
#!/usr/bin/env bun
// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: <filename>.ts
// ║ Module: <exports / key symbols>
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: <COLOR>
// ║ Architectural Role: <ROLE>
// ║ @SID: <SID>
// ╚════════════════════════════════════════════════════════════════════════════
```

| Line | Content | Required |
|------|---------|----------|
| 1 | `#!/usr/bin/env bun` | Yes for CLI scripts; omit for library modules / VS Code extension source |
| 2+ | Decorator's Blessing envelope | Recommended for scripts; optional for library modules |
| Alt | `/** JSDoc */` with `@SID` | Acceptable for library modules (VS Code extension source) |

**VS Code extension source** (`extensions/chthonic-archive/src/`) uses JSDoc `/** */` with `@SID` instead of the envelope:

```typescript
/**
 * Module description.
 * @SID EXTENSION_MODULE_V1
 */
import * as vscode from 'vscode';
```

### Rust (`.rs`)

Rust has no shebang. The Decorator's Blessing envelope is the canonical header:

```rust
// ╔════════════════════════════════════════════════════════════════════════════
// ║  THE DECORATOR'S BLESSING: <filename>.rs
// ║  Module: <description>
// ╠════════════════════════════════════════════════════════════════════════════
// ║  Spectral Frequency: <COLOR>
// ║  Architectural Role: <ROLE>
// ║  @SID: <SID>
// ╚════════════════════════════════════════════════════════════════════════════
```

### Config Files (JSON, TOML, YAML)

Config files carry structural metadata (keys like `name`, `version`, `description`) as content. No shebang, no envelope. `@SID` is expressed via the file's position in the project hierarchy, not inline.

### CSS / Tailwind

CSS is generated output in this repo. No header convention applies to generated CSS.
For authored CSS, a `/* @SID */` comment at line 1 is acceptable but not required.

---

## 5. Noise Reduction Strategy

By standardizing this structure, we enable:
1.  **Automated Auditing:** `chthonic audit` can parse `@SID` tags to build a graph.
2.  **Context Loading:** Agents can read *just the header* (first 20 lines) to understand a file's role without reading the full code.
3.  **Visual Scanning:** Humans can quickly identify "Official" vs "Scratchpad" scripts by the presence of the **Decorator's Blessing** (the envelope).

---

## 6. Compliance Matrix (2026-02-24 Audit)

| Language | Files | Shebang | Decorator's Blessing | @SID |
|----------|-------|---------|---------------------|------|
| Python | 120 | 120/120 (100%) | 57/120 (48%) | 47/120 (39%) |
| PowerShell | 82 | 82/82 (100%) | 32/82 (39%) | 2/82 (2%) |
| TypeScript | 62 | 10/62 (16%) | 26/62 (42%) | 3/62 (5%) |
| Rust | 15 | N/A | 15/15 (100%) | 0/15 (0%) |
| **Total** | **279** | **212/264 (80%)** | **130/279 (47%)** | **52/279 (19%)** |

### Known Systemic Debt

- **Python `#-*-` spacing**: 92/120 scripts use `# -*- coding: utf-8 -*-` (spaced) vs canonical `#-*- coding: utf-8 -*-` (tight). Batch tooling target.
- **TypeScript shebangs**: Only 10/62 have `#!/usr/bin/env bun`. Library modules correctly omit; CLI scripts need addition.
- **@SID coverage**: 19% overall. Highest priority for incremental improvement.
- **Rust @SID**: 0/15. All have the Blessing envelope but lack `@SID` tags within.

---

## 7. Hierarchy (Priority Order)

When conventions conflict:

1. **PMS-v3** (Python-specific: shebang, `#-*-`, docstring @SID/@Type) — highest authority for `.py`
2. **STD_SCRIPT_METADATA_V2** (this document) — universal cross-language standard
3. **Decorator's Blessing** (visual envelope) — recommended, not mandatory
4. **Per-framework conventions** (Next.js, Tailwind, Cargo) — respected for config files

The hierarchy ensures Python's metabolic standard is never overridden by the general standard, while all other languages follow this document.
