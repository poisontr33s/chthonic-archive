# Script Envelope Template (Canonical — Wedjat-Quipu / Temple-Ayllu / Ogdoad-Ceque)

# Rules:
# 1) Single envelope block only (deduplicate).
# 2) Fixed field order (see below).
# 3) OPEN-SIDED format (no right border).
# 4) Fixed width left borders (80 chars standard).
# 5) Replace any malformed or partial header with this block.
# 6) No padding required for interior lines (visual stability).

# Canon field order:
# 1. Title (THE DECORATOR'S BLESSING: <filename>)
# 2. --- mid border ---
# 3. Wedjat-Quipu Spectrum: <color>
# 4. Temple-Ayllu Zone: <emoji ZONE_NAME>
# 5. Ogdoad-Ceque Radiance:
# 6.   └─◄ <radiance>

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <filename>
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: <WHITE|RED|GREEN|BLUE|GOLD|ORANGE|INDIGO|VIOLET>
# ║ Temple-Ayllu Zone: <🌿 THE GARDEN|🏰 THE FORTRESS|🔭 THE OBSERVATORY|🔥 THE FOUNDRY>
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ <(Standalone) | dependency/cross-ref hint>
# ╚════════════════════════════════════════════════════════════════════════════

# Explicitly forbidden:
# - Top/mid/bottom closers on right edge: `╗`, `╣`, `╝`
# - Content lines ending with right-side `║`
# - DEPRECATED field names: Spectral Frequency, Architectural Role, Module,
#   Semantic ID, Exports, Flags/Modes, Cross-References

## Python Prologue (Canonical)

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: <filename>.py
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: WHITE
# ║ Temple-Ayllu Zone: 🌿 THE GARDEN
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ (Standalone)
# ╚════════════════════════════════════════════════════════════════════════════

"""
Description of what the script does.

@SID:           TOOL_EXAMPLE_V1
@Shabti:        CLI Script
@Purpose:       One-line purpose.
"""
```

## Followed by docstring with @SID / @Shabti / @Purpose

The docstring immediately below the envelope block carries the semantic identity:
- `@SID:` — Semantic ID for Archive addressability
- `@Shabti:` — Classification (CLI Script, Library Module, Daemon, etc.)
- `@Purpose:` — Human-readable purpose

## Zone Classification (Temple-Ayllu)

| Zone | Emoji | Applies to |
|---|---|---|
| THE GARDEN | 🌿 | Python scripts, Ruby |
| THE FORTRESS | 🏰 | Rust, C/C++, Go, shaders |
| THE OBSERVATORY | 🔭 | TypeScript, JavaScript, HTML, CSS |
| THE FOUNDRY | 🔥 | Cross-domain analysis, heavy transform |

## Spectrum Classification (Wedjat-Quipu)

| Color | Extension |
|---|---|
| WHITE | `.py` (default), `.rb`, `.ipynb` |
| RED | `.rs`, `.go`, `.c`, `.h`, `.cpp` |
| GREEN | `.html`, `.css` |
| BLUE | `.toml`, `.json`, `.yaml`, `.yml`, `.lock`, `.sql` |
| GOLD | `.md`, `.txt`, `.log` |
| ORANGE | `.ts`, `.tsx`, `.js`, `.jsx` |
| INDIGO | `.glsl`, `.vert`, `.frag` |
| VIOLET | `.ps1`, `.sh`, `.bat`, `.cmd` |
