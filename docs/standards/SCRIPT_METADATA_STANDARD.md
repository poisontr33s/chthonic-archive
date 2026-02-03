---
type: standard
category: governance
status: candidate
created: 2026-02-03
author: Gemini-3 Pro (Deep Research)
---

# Deep Research Candidate: Script Metadata & Shebang Standardization

**@SID:** STD_SCRIPT_METADATA_V1
**@Context:** Codebase Hygiene / Cross-Platform Compatibility
**@Purpose:** Define a robust, encoding-safe, and visually distinct header standard for all executable scripts.

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

### Python (`.py`)
- **Envelope:** Use `#` comments at the very top (before imports).
- **Shebang:** Line 1 (if executable) or after Envelope?
    - *Decision:* **Envelope First**, then Shebang? NO.
    - *Standard:* **Shebang MUST be Line 1** for the kernel to recognize it.
    - *Correction:* The Visual Envelope goes *below* the shebang, or the Shebang is part of the file metadata but physically top.
    - *Revised Layout:*
        1. Shebang
        2. Visual Envelope (Comment block)
        3. Module Docstring (with Semantic Tags)
        4. Imports

### PowerShell (`.ps1`)
- **Shebang:** Line 1 (`#!/usr/bin/env pwsh`).
- **Envelope:** Line 2+ (Comment block).
- **Doc-Block:** Use `<# ... #>` for help/metadata or just comments.

### TypeScript (`.ts`)
- **Shebang:** Line 1 (`#!/usr/bin/env bun`).
- **Envelope:** `//` comments.

---

## 5. Noise Reduction Strategy

By standardizing this structure, we enable:
1.  **Automated Auditing:** `chthonic audit` can parse `@SID` tags to build a graph.
2.  **Context Loading:** Agents can read *just the header* (first 20 lines) to understand a file's role without reading the full code.
3.  **Visual Scanning:** Humans can quickly identify "Official" vs "Scratchpad" scripts by the presence of the **Decorator's Blessing** (the envelope).
