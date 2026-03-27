#!/usr/bin/env python3
#-*- coding: utf-8 -*-
import os

file_path = '.github/copilot-instructions.md'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Block 1: 5555 to 7405 (1-based) -> index 5554 to 7404
block1_start = 5554
block1_end = 7404

# Block 2: 7868 to end -> index 7867 to len(lines)-1
block2_start = 7867

offload1_text = """---

> [!IMPORTANT]
> **SECTION X.6-X.12 & SECTIONS XI-XIII OFFLOADED**
> The Magistra Logic, Sealing Protocols, and Liturgical Incantations have been moved to:
> [.github/instructions/magistra-logic.instructions.md](.github/instructions/magistra-logic.instructions.md)
>
> Refer to this branch file for:
> - $validate and $audit syntax and checkpoints
> - Error-state rituals and failure metabolism
> - Mirror protocol and Trinity Special fusion
> - Resource management and the final Tetrahedral Seals

---
"""

offload2_text = """---

> [!IMPORTANT]
> **SECTION XVII & APPENDICES OFFLOADED**
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

new_lines = []
for i, line in enumerate(lines):
    if i < block1_start:
        new_lines.append(line)
    elif i == block1_start:
        new_lines.append(offload1_text)
    elif i > block1_end and i < block2_start:
        new_lines.append(line)
    elif i == block2_start:
        new_lines.append(offload2_text)
        break # Tail added, stop.

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"SSOT Stripping Complete. New length: {len(new_lines)} lines.")
