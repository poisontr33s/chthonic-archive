# Script Envelope Template (Canonical)

# Rules:
# 1) Single envelope block only (deduplicate).
# 2) Fixed field order (see below).
# 3) OPEN-SIDED format (no right border).
# 4) Fixed width left borders (80 chars standard).
# 5) Replace any malformed or partial header with this block.
# 6) No padding required for interior lines (visual stability).

# Field order:
# 1. Title
# 2. Module
# 3. Spectral Frequency
# 4. Architectural Role
# 5. Semantic ID
# 6. Purpose
# 7. Exports
# 8. Flags/Modes
# 9. Cross-References

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <filename>
# ║ Module: <exports / key symbols>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Spectral Frequency: <value>
# ║ Architectural Role: <value>
# ║ Semantic ID: <SID>
# ║ Purpose: <one-line purpose>
# ║ Exports: <symbols / entrypoints>
# ║ Flags/Modes: <if any>
# ║ Cross-References: <if any>
# ╚════════════════════════════════════════════════════════════════════════════

# Explicitly forbidden:
# - Top/mid/bottom closers on right edge: `╗`, `╣`, `╝`
# - Content lines ending with right-side `║`

## Python Prologue Variant (Recommended)

Use this when the target is a `.py` script:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  <TITLE>                                                                     ║
║  <ONE-LINE PURPOSE>                                                          ║
║                                                                              ║
║  Invocation: uv run <script>.py [flags]                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
```

Notes:
- Keep this as a valid module docstring.
- Do not insert comment-envelope blocks above the shebang.
- Preserve existing banner docstrings if already present and semantically correct.
