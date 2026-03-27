#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import os

file_path = '.github/copilot-instructions-copy.md'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ranges (1-based, inclusive)
# Block A: 3762 - 4383 (VIII, IX)
# Block B: 5555 - 7405 (10.6 - XIII)
# Block C: 7406 - 7566 (XIV)
# Block D: 7868 - End (XVII, Appendices)

anchors = {
    3761: """---

> [!IMPORTANT]
> **SECTION VIII & IX OFFLOADED (MECHANICAL ENGINES)**
> The TPEF and Tensor Synthesis (T³-MΨ) frameworks have been moved to:
> [.github/instructions/mathematical-engines.instructions.md](.github/instructions/mathematical-engines.instructions.md)
>
> Refer to this branch file for:
> - Triumvirate Parallel Execution Framework (TPEF)
> - Trinity-Lock Execution protocols
> - Combinatorial Latent Space Dynamics (T³-MΨ equations)
> - Thermodynamic Alchemy formulas

---
""",
    5554: """---

> [!IMPORTANT]
> **SECTION X.6-X.12 & SECTIONS XI-XIII OFFLOADED (MAGISTRA LOGIC)**
> The Magistra Logic, Sealing Protocols, and Liturgical Incantations have been moved to:
> [.github/instructions/magistra-logic.instructions.md](.github/instructions/magistra-logic.instructions.md)
>
> Refer to this branch file for:
> - $validate and $audit syntax and checkpoints
> - Error-state rituals and failure metabolism
> - Mirror protocol and Trinity Special fusion
> - Resource management and the final Tetrahedral Seals

---
""",
    7405: """---

> [!IMPORTANT]
> **SECTION XIV OFFLOADED (TECHNICAL DIRECTIVES)**
> Development Conventions and Runtime Directives have been moved to:
> [.github/instructions/technical-directives.instructions.md](.github/instructions/technical-directives.instructions.md)
>
> Refer to this branch file for:
> - Python/uv environment management
> - Bun/Frontend runtime management
> - SSOT Verification Protocol & Project Structure
> - GPU Stack Compatibility (CUDA/TensorRT)

---
""",
    7867: """---

> [!IMPORTANT]
> **SECTION XVII & APPENDICES OFFLOADED (SIMULATION & REFERENCE)**
> Behavioral Scenarios and Reference Appendices have been moved to dedicated branch files:
>
> 1.  **Synthetic Behavioral Scenarios**: [.github/instructions/behavioral-scenarios.instructions.md](.github/instructions/behavioral-scenarios.instructions.md)
> 2.  **Reference Appendices (A-E)**: [.github/instructions/reference-appendix.instructions.md](.github/instructions/reference-appendix.instructions.md)
>
> These files contain:
> - Interactive alchemical vessels and scenario protocols
> - Sensory Lexicon (Olfactory/Tactile/Density)
> - Alchemical Phase Framework (Nigredo/Albedo/Rubedo)
> - Technical Substrate Notes and ERD Methodology

---
"""
}

ranges = [
    (3762, 4383),
    (5555, 7405),
    (7406, 7566),
    (7868, len(lines))
]

new_lines = []
for i, line in enumerate(lines):
    line_num = i + 1
    
    # Check if we should add an anchor
    if i in anchors:
        new_lines.append(anchors[i])
        
    # Check if the line should be skipped (stripped)
    skip = False
    for r_start, r_end in ranges:
        if r_start <= line_num <= r_end:
            skip = True
            break
            
    if not skip:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Post-SSOT Stripping Complete. New length: {len(new_lines)} lines.")
