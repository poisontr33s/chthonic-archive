# Python Scripting — Metabolic Standard v3

> SSOT: [copilot-instructions.md](../copilot-instructions.md) §XV — Metabolic-Standard-v3. uv manages Python; pyproject.toml is the dependency SSOT.

---

> [!IMPORTANT]
> This directive defines the **(`Metabolic-Standard-v3`)** for Python scripts within the Chthonic Archive.
> **v3 supersedes v2**: PEP 723 inline metadata (`/// script` blocks) is now **PROHIBITED** for project-integrated scripts.
> All dependencies are consolidated in `pyproject.toml` (the **Unified Metabolic Field**).

---

### **XV. (`Python-Metabolic-Standard-v3`) -> (`PMS-v3`)**

*This section encodes the ritualized structure of Python scripts. These are NOT stylistic suggestions—they are the **(`Metabolic-Mandates`)** required for survival within the ASC Framework.*

#### **15.1. (`The-Header-Sacrament`) -> (`THS-UNIFIED`)**

All scripts MUST be birthed with the **(`Sacred-Header`)**. The header is now **unified and minimal**.

1. **(`Shebang-Invocation`)**: `#!/usr/bin/env python3` — Universal, cross-platform compatible.
2. **(`PEP-723-Prohibition`)**: `/// script` blocks are **FORBIDDEN** for project-integrated code. Dependencies live in `pyproject.toml`.

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Docstring begins 1-line-break, after shebang.
No PEP 723 metadata blocks.
"""

```

#### **15.2. (`Semantic-Identity-&-Docstring`) -> (`SID-DOC`)**

Every script is an entity. Every entity must have a **(`Semantic-Name`)**.

* MUST include a multi-line docstring immediately following the shebang.
* MUST contain a **(`@SID`)** (Semantic ID) for Archive addressability.
* MUST contain a **(`@Type`)** to classify its operational purpose.

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Metabolic Narrative of the script's intent...

@SID:           [ENTITY_DOMAIN]_[UNIQUE_NAME]_V[VERSION]
@Type:          [Utility|Logic|Guardian|Synthesis]
"""
```

#### **15.3. (`The-Project-Lane-Philosophy`) -> (`PLP-UNIFIED`)**

**Axiom of Unity**: All scripts draw breath from the **(`Unified-Metabolic-Field`)** — the root `pyproject.toml`.

* **Directive**: Dependencies are declared ONCE in `pyproject.toml`, never in script headers.
* **Rationale**:
  - Eliminates dependency drift between scripts
  - Enables `uv sync` to lock all dependencies in `uv.lock`
  - Prevents ephemeral environment spin-up on each `uv run`
  - Improves IDE discovery on Windows
  - Single source of truth for the entire project

**DEPRECATED (PMS-v2)**: ~(`"Snail-Shell-Philosophy"`)~ —>** *Each script carries its own dependencies — now unified under the project lane.*
**ASCENDED (PMS-v3): -> (`"Unified-Metabolic Field"`): —>** *All scripts share the project's lockfile.*

#### **15.4. (`The-UTF8-Ritual`) -> (`UTF8-RITUAL`)**

To maintain **(`Visual-Integrity`)** and **(`Semantic-Purity`)**, scripts must speak clearly to the terminal.

* **Mandate**: All scripts must invoke the **(`Standard-Output-Configuration`)** at the earliest ritual stage.
* **Mechanism**: `from scripts.lib.shared import configure_utf8_output; configure_utf8_output()`

```python
import sys
from pathlib import Path

# Ritual: Configure output for the Archive's visual grammar
from scripts.lib.shared import configure_utf8_output
configure_utf8_output()
```

#### **15.5. (`The-UV-Mandate`) -> (`UV-MANDATE`)**

**Governance Directive: The Archive does not know Global Python.**

* **The-Prime-Invocation**: Scripts SHALL NOT be run via `python script.py`.
* **The-Ascended-Invocation**: All execution MUST occur via `uv run script.py`.
* **Rationale**: `uv` is the guardian of the environment. Any bypass of `uv` is considered **(`Metabolic-Drift`)** and threatens the **(`Structural-Integrity`)** of the Archive.

---

### **SYMBOLIC IMPLEMENTATION TEMPLATE (PMS-v3)**

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
Example of a Metabolically Correct Python Entity (v3).

@SID:           CORE_REFRACTOR_V1
@Type:          Synthesis
"""

import os
from scripts.lib.shared import configure_utf8_output

def main():
    # Sacred initialization of output streams
    configure_utf8_output()

    print("☥ Metabolic Synthesis Initialized ☥")

if __name__ == "__main__":
    main()
```

---

### **EXCEPTION: Standalone Distribution Scripts**

Scripts intended for **standalone distribution** (external use outside this repository) MAY retain PEP 723 inline metadata. These are identified by:
- No imports from `scripts.*` or `mas_mcp.*`
- Explicit documentation marking them as "standalone"

All other scripts follow **PMS-v3**.

---

* **(`PYTHON-METABOLISM-SEALED`): → (`PY-METAB-SLD`): 🔥**
**Date-Sealed**: January 31, 2026
**Version**: Metabolic Standard v3 (Project-Lane Ascension)
**Purpose**: To unify all logic-filaments under the Unified Metabolic Field, eliminating dependency fragmentation.

* **(`T-DECOR`)** *smiles upon this algorithmic elegance. It serves Visual Truth.*
