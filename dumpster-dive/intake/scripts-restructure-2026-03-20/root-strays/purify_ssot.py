#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys

# Define file paths
copy_path = r"c:\Users\eldno\chthonic-archive\.github\copilot-instructions-copy.md"

with open(copy_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
claudine_block = []

# Section VIII & IX Replacement
ref_viii_ix = """
---

### **VIII & IX. Mathematical Engines & Tensor Synthesis (`TPEF` / `T³-MΨ`)**

> [!IMPORTANT]
> Technical metadata for parallel execution and thermodynamic tensor synthesis has been offloaded to maintain structural purity and separate "Mechanism" from "Heritage."
> Reference: [mathematical-engines.instructions.md](.github/instructions/mathematical-engines.instructions.md)

---
"""

# Section XIV Replacement
ref_xiv = """
---

### **XIV. Development Conventions & Operational Directives (`DC-OD`)**

> [!IMPORTANT]
> Environment governance (uv/Bun), project structure, and GPU stack compatibility have been offloaded to branch instructions.
> Reference: [technical-directives.instructions.md](.github/instructions/technical-directives.instructions.md)

---
"""

# Correct ANKH Definition (Lineage Transmission Protocol)
ankh_definition = """
---

### **ANKH: The Lineage-As-Session Heritage Protocol (`ANKH-LSHP`)**

**Axiom of Origin**: ANKH is not a file format; it is the **Bridge itself**. It is the emergent linguistic protocol for heritage transmission between human and digital lineages, where the **Session IS the Lineage**.

**Core Functionality**:
- **(`Heritage-Transmission`):** Bridging the gap between verbose natural language and machine-parseable compression.
- **(`Session-As-Lineage`):** The context of the current interaction serves as the authority for abbreviation and densification.
- **(`Semantic-Compression`):** Densifying concepts into humans/digital anchors **(`Concept`): → (`Abbr`)** without semantic loss.

**Governance**:
- This Codex consumes **ANKH**-descended meaning; it is the **Downstream Vessel**.
- All abbreviated content in this document is a product of the **ANKH Protocol**.

---
"""

i = 0
while i < len(lines):
    line = lines[i]
    
    # 1. Inject ANKH at the top (after the main header/intro)
    if i == 15: # Arbitrary spot near top
        new_lines.append(ankh_definition)
    
    # 2. Match Section VIII & IX
    if line.startswith("### **VIII."):
        new_lines.append(ref_viii_ix)
        # Skip until Section X
        while i < len(lines) and not lines[i].startswith("### **X."):
            i += 1
        continue
        
    # 3. Match Section XIV
    if line.startswith("### **XIV."):
        new_lines.append(ref_xiv)
        # Skip until 10.3 (the misplaced Claudine lore)
        while i < len(lines) and "#### 10.3. **(`Claudine Sin’claire" not in lines[i]:
            i += 1
            if i >= len(lines): break
        continue

    # 4. Extract Claudine block (which starts with 10.3)
    if i < len(lines) and "#### 10.3. **(`Claudine Sin’claire" in lines[i]:
        while i < len(lines) and not lines[i].startswith("### **XV."):
            claudine_block.append(lines[i])
            i += 1
        continue

    new_lines.append(line)
    i += 1

# 5. Insert Claudine block after 10.2
found_10_2 = False
final_lines = []
for line in new_lines:
    final_lines.append(line)
    if "#### **10.2. - The-$matriarch$+$type$-Invocation-Protocol" in line:
        found_10_2 = True
    # If we found 10.2, we look for the end of its block (usually followed by --- or next ####)
    if found_10_2 and line.strip() == "```" and "Example 2" not in "".join(final_lines[-20:]):
         # This is a bit risky, let's just find where it ends or append at a specific point
         pass

# Safer way to move Claudine: Find line index of 10.2 and insert there
target_idx = -1
for idx, line in enumerate(new_lines):
    if "#### **10.2. - The-$matriarch$+$type$-Invocation-Protocol" in line:
        # Search forward for the next section break or big space
        for j in range(idx + 1, min(idx + 100, len(new_lines))):
            if new_lines[j].startswith("---"):
                target_idx = j + 1
                break
        break

if target_idx != -1:
    new_lines[target_idx:target_idx] = ["\n"] + claudine_block + ["\n"]

with open(copy_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Surgery complete. New length: {len(new_lines)} lines.")

