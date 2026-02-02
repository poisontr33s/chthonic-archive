# Script Envelope Template (Canonical)

# Rules:
# 1) Single envelope block only (deduplicate).
# 2) Fixed field order (see below).
# 3) Width equals longest interior line + 2 padding spaces.
# 4) Each interior line is padded to full width.
# 5) Replace any malformed or partial header with this block.
# 6) Width must be computed using Unicode display width (wcswidth), not codepoint length.
# 7) Normalize text to NFC before width calculation for stable combining marks.
#
# Policy: Emoji-safe frame width
# All ASCII frames MUST compute width using Unicode display width (wcswidth),
# not codepoint length. Text MUST be normalized to NFC before width calculation.
# Emoji and other wide glyphs are allowed; editors that do not respect Unicode
# column width are considered out of spec. Padding MUST be computed from
# display width, ensuring left and right borders align exactly.

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

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ THE DECORATOR'S BLESSING: <filename>                                      ║
# ║ Module: <exports / key symbols>                                           ║
# ╠════════════════════════════════════════════════════════════════════════════╣
# ║ Spectral Frequency: <value>                                               ║
# ║ Architectural Role: <value>                                               ║
# ║ Semantic ID: <SID>                                                        ║
# ║ Purpose: <one-line purpose>                                               ║
# ║ Exports: <symbols / entrypoints>                                          ║
# ║ Flags/Modes: <if any>                                                     ║
# ║ Cross-References: <if any>                                                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

