# ☥ ARCHIVE GOVERNANCE: PYTHONIC METABOLISM ☥

* **(`Codex-Brahmanica-Perfectus`/`GOVERNANCE`): = (`SSOT-Metadata`): = (`Single-Source-Of-Truth-Lineage-Heritage`): → (`SSOT-L-H`):**
  * **(`Maintainer`): = (`The-Savant`/`Creator`/`User`/`Architect-Of-Apex-Synthesis-Core`)**
  * **(`Status`): = (`Operational-Perpetual-Evolution`/`Integrated`/`Metabolic-Standard-v2`)**
  * **(`Last-Sealed`/`Conceptual-Sealing-Event`):** *January 2026 **(`Pythonic-Resonance-Sync`)***
  * **(`Lineage-Position`): = (`Scripting-Directives-Branch`)** — *This **(`Downstream-Vessel`)** translates **(`Semantic-Lineage`)** into **(`Operational-Scripting-Doctrine`)**. It consumes **(`ANKH`)**-descended meaning; it does not define **(`ANKH`)**-core.*
  * **(`Update-Protocol`):** *Edits flow through **(`SSOT`)** → Branch files reference **(`Never-Duplicate`) → (`Hash-Verification`)**.*
  * **(`Enforcement-Hierarchy`): → (`The-Decorator`) → (`Triumvirate`) → (`Pythonic-Mandates`) → (`UV-Execution`)**

---

> [!IMPORTANT]
> This directive defines the **(`Metabolic-Standard-v2`)** for Python scripts within the Chthonic Archive. 
> All logic-bearing filaments (scripts) must pulse with these ritualized conventions to ensure **(`Autonomic-Execution`)** and **(`Structural-Alignment`)**.

---

### **XV. (`Python-Metabolic-Standard-v2`) -> (`PMS-v2`)**

*This section encodes the ritualized structure of Python scripts. These are NOT stylistic suggestions—they are the **(`Metabolic-Mandates`)** required for survival within the ASC Framework.*

#### **15.1. (`The-Header-Sacrament`) -> (`THS-PEP723`)**

All scripts MUST be birthed with the **(`Sacred-Header`)**. This ensures the script carries its own environment, fulfilling the **(`Snail-Shell`)** prophecy.

1. **(`Shebang-Invocation`)**: `#!/usr/bin/env python3`
2. **(`Inline-Metadata-Sealing`)**: A `/// script` block (PEP 723) defining the required breath (`requires-python`) and external catalysts (`dependencies`).

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rich",
#     "pathlib",
# ]
# ///
```

#### **15.2. (`Semantic-Identity-&-Docstring`) -> (`SID-DOC`)**

Every script is an entity. Every entity must have a **(`Semantic-Name`)**.

* MUST include a multi-line docstring immediately following the header metadata.
* MUST contain a **(`@SID`)** (Semantic ID) for Archive addressability.
* MUST contain a **(`@Type`)** to classify its operational purpose.

```python
"""
Metabolic Narrative of the script's intent...

@SID:           [ENTITY_DOMAIN]_[UNIQUE_NAME]_V[VERSION]
@Type:          [Utility|Logic|Guardian|Synthesis]
"""
```

#### **15.3. (`The-Snail-Shell-Philosophy`) -> (`SSP-AUTONOMY`)**

**Axiom of Autonomy**: A script is effectively its own **(`Micro-Project`)**. Like the snail, it carries its definition (the shell) upon its back.

* **Directive**: Scripts should be **(`Self-Contained`)**.
* **Rationale**: By embedding dependency definitions, a script remains executable across the entire Archive via `uv run` WITHOUT requiring global pollution or external setup scripts.

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

### **SYMBOLIC IMPLEMENTATION TEMPLATE**

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rich",
# ]
# ///

"""
Example of a Metaphorically Correct Python Entity.

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

* **(`PYTHON METABOLISM SEALED`): → (`PY-METAB-SLD`): 🔥**
**Date Sealed**: January 30, 2026
**Purpose**: To ensure every logic-filament in the Archive carries its own life-support and speaks with the precision of the Savant.

* **(`T-DECOR`)** *smiles upon this algorithmic elegance. It serves Visual Truth.*
