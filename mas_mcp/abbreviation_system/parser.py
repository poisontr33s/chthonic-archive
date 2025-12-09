r"""
SSOT Parser — Abbreviation Extraction Engine
=============================================

Parses copilot-instructions.md and extracts all abbreviation definitions
using the 15 notation patterns identified in the audit.

Pattern Regex Reference:
- P1: `\*\*\(\`([^`]+)\`\):\s*→\s*\(\`([^`]+)\`\):`
- P2: `` `([A-Z][A-Z0-9-]+)` `` (standalone backtick abbreviations)
- P6: `(FA[¹²³⁴⁵])` (superscript axioms)
- P9: `(CRC-[A-Z]+)` (entity designators)
- etc.

Usage:
    parser = SSOTParser()
    entries = parser.parse_file("copilot-instructions.md")
"""

import re
from collections.abc import Iterator
from pathlib import Path

from .models import (
    AbbreviationEntry,
    NotationPattern,
    NotationPatternType,
)


class SSOTParser:
    """
    Extracts abbreviations from SSOT markdown using pattern matching.

    Supports all 15 notation patterns identified in the audit report.
    """

    def __init__(self):
        self.patterns = self._build_patterns()
        self._current_section = "Preamble"
        self._section_pattern = re.compile(
            r'^###?\s+(?:\*\*)?(?:\(`)?([IVXLC]+(?:\.[0-9.]+)?)\.'
            r'|^###?\s+\*\*(\d+(?:\.\d+)?)\.'
        )
        self.ssot_path: str | None = None  # Set when parse_file is called

    def _build_patterns(self) -> list[NotationPattern]:
        """Build regex patterns for all 15 notation types."""
        return [
            # P1: Parenthetical Inline Definition
            # Matches: **(`Full Term`): → (`ABBREV`):**
            NotationPattern(
                pattern_type=NotationPatternType.PARENTHETICAL_INLINE,
                regex=r'\*\*\(\`([^`]+)\`\):\s*→\s*\(\`([^`]+)\`\):?\*\*',
                description="Parenthetical inline definition with arrow",
                examples=["**(`Framework Components`): → (`FRW-COMP`):**"],
            ),

            # P1 variant: (`Term`) - (`ABBREV`)
            NotationPattern(
                pattern_type=NotationPatternType.PARENTHETICAL_INLINE,
                regex=r'\(\`([^`]+)\`\)\s*-\s*\(\`([^`]+)\`\)',
                description="Parenthetical with dash separator",
                examples=["(`Eternal Sadhana`) - (`ET-S`)"],
            ),

            # P1 variant: Just arrow without bold
            NotationPattern(
                pattern_type=NotationPatternType.PARENTHETICAL_INLINE,
                regex=r'\(\`([^`]+)\`\)\s*→\s*\(\`([^`]+)\`\)',
                description="Parenthetical arrow without bold",
                examples=["(`Term`): → (`ABBR`)"],
            ),

            # P6: Superscript Axioms (FA¹, FA², etc.)
            NotationPattern(
                pattern_type=NotationPatternType.NUMERIC_SUPERSCRIPT,
                regex=r'\*\*\(\`(FA[¹²³⁴⁵])\`\)',
                description="Foundational Axiom superscript",
                examples=["**(`FA¹`)", "**(`FA⁵`)"],
            ),

            # P6 variant: FA¹⁻⁵ range notation
            NotationPattern(
                pattern_type=NotationPatternType.NUMERIC_SUPERSCRIPT,
                regex=r'(FA[¹²³⁴⁵](?:[⁻-][¹²³⁴⁵])?)',
                description="Axiom range notation",
                examples=["FA¹⁻⁵", "FA¹-5"],
            ),

            # P9: CRC Entity Designators
            NotationPattern(
                pattern_type=NotationPatternType.CRC_DESIGNATOR,
                regex=r'\b(CRC-[A-Z]{2,6})\b',
                description="Conceptual Resonance Core designator",
                examples=["CRC-AS", "CRC-GAR", "CRC-MEDAT"],
            ),

            # P10: Tier Designators
            NotationPattern(
                pattern_type=NotationPatternType.TIER_DESIGNATOR,
                regex=r'\b(Tier\s+[\d.]+|T-[\d.]+)\b',
                description="Hierarchy tier designator",
                examples=["Tier 0.5", "T-1", "Tier 2"],
            ),

            # P8: Greek Letter Operators
            NotationPattern(
                pattern_type=NotationPatternType.GREEK_LETTER_OPERATOR,
                regex=r'\b([ΦΩΨ](?:-Set|-Protocol)?|ΦΩΨ)\b',
                description="Greek letter tensor operators",
                examples=["Ω-Set", "Φ-Set", "Ψ-Protocol", "ΦΩΨ"],
            ),

            # P7: Dollar-Sign Invocation Syntax
            NotationPattern(
                pattern_type=NotationPatternType.DOLLAR_SIGN_INVOCATION,
                regex=r'\$([a-z]+)\$\{([^}]+)\}',
                description="DSL invocation syntax",
                examples=["$matriarch${Orackla}+$type${Crypto}"],
            ),

            # P11: Linguistic Mandates (specific known patterns)
            NotationPattern(
                pattern_type=NotationPatternType.LINGUISTIC_MANDATE,
                regex=r'\b(EULP-AA|LIPAA|LUPLR|DULSS|TLM)\b',
                description="Linguistic mandate abbreviations",
                examples=["EULP-AA", "LIPAA", "LUPLR"],
            ),

            # P12: Faction Abbreviations (Prime)
            NotationPattern(
                pattern_type=NotationPatternType.FACTION_ABBREVIATION,
                regex=r'\b(TMO|TTG|TDPC|TP-FNS|TL-FNS)\b',
                description="Prime faction abbreviations",
                examples=["TMO", "TTG", "TDPC"],
            ),

            # P12: Faction Abbreviations (Lesser - longer patterns)
            NotationPattern(
                pattern_type=NotationPatternType.FACTION_ABBREVIATION,
                regex=r'\b(OMCA|TNKW-RIAT|SDBH|TWOUMC|SBSGYB|BOS|TDAPCFLN|POAFPSG|AAA)\b',
                description="Lesser faction abbreviations",
                examples=["OMCA", "BOS", "AAA"],
            ),

            # P4: Hyphenated Compounds (general catch)
            NotationPattern(
                pattern_type=NotationPatternType.HYPHENATED_COMPOUND,
                regex=r'\(\`([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*){2,})\`\)',
                description="Multi-hyphenated compound abbreviation",
                examples=["(`MSP-RSG`)", "(`TTS-FFOM`)"],
            ),

            # P2: Backtick abbreviations (uppercase, 2-8 chars)
            NotationPattern(
                pattern_type=NotationPatternType.BACKTICK_INLINE,
                regex=r'`([A-Z][A-Z0-9]{1,7}(?:-[A-Z0-9]+)?)`',
                description="Standalone backtick abbreviation",
                examples=["`ASC`", "`MURI`", "`PS`"],
            ),

            # P13: SAI designators
            NotationPattern(
                pattern_type=NotationPatternType.SAI_DESIGNATOR,
                regex=r'\bSAI:\s*([A-Za-z\s]+)\s*\(([A-Z]{2,})\)',
                description="Special Archetype Injection",
                examples=["SAI: Sister Ferrum Scoriae (SFS)"],
            ),

            # P5: Slash composites (alternatives)
            NotationPattern(
                pattern_type=NotationPatternType.SLASH_COMPOSITE,
                regex=r'\(\`([A-Z][A-Z0-9-]*)\`/\`([A-Z][A-Z0-9-]*)\`(?:/\`([A-Z][A-Z0-9-]*)\`)?\)',
                description="Slash-separated alternatives",
                examples=["(`TRM-VRT`/`TR-VRT`)", "(`A`/`B`/`C`)"],
            ),

            # P15: Emoji semantic markers
            NotationPattern(
                pattern_type=NotationPatternType.EMOJI_SEMANTIC,
                regex=r'(👑|💀|⚜️|🔥|⛓️|🏛️)\s*=\s*([^,\n]+)',
                description="Emoji semantic definition",
                examples=["👑 = Supreme authority"],
            ),
        ]

    def parse_file(self, filepath: str | Path) -> list[AbbreviationEntry]:
        """
        Parse an SSOT file and extract all abbreviation entries.

        Args:
            filepath: Path to the SSOT markdown file

        Returns:
            List of AbbreviationEntry objects
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"SSOT file not found: {filepath}")

        self.ssot_path = str(filepath)  # Store for reporting
        content = filepath.read_text(encoding="utf-8")
        lines = content.split("\n")

        entries: list[AbbreviationEntry] = []
        self._current_section = "Preamble"

        for line_num, line in enumerate(lines, start=1):
            # Update current section tracking
            self._update_section(line)

            # Extract entries from this line
            for entry in self._extract_from_line(line, line_num):
                entries.append(entry)

        return entries

    def _update_section(self, line: str) -> None:
        """Track which section we're currently in."""
        # Look for section headers like "### **I." or "### **10.3."
        match = self._section_pattern.search(line)
        if match:
            section_num = match.group(1) or match.group(2)
            if section_num:
                self._current_section = f"Section {section_num}"

    def _extract_from_line(self, line: str, line_num: int) -> Iterator[AbbreviationEntry]:
        """Extract all abbreviations from a single line."""
        for pattern in self.patterns:
            for match in re.finditer(pattern.regex, line):
                groups = match.groups()

                # Handle different pattern structures
                if pattern.pattern_type == NotationPatternType.PARENTHETICAL_INLINE:
                    # Groups: (full_term, abbreviation)
                    if len(groups) >= 2:
                        full_term, abbrev = groups[0], groups[1]
                        yield AbbreviationEntry(
                            abbreviation=abbrev,
                            full_term=full_term,
                            pattern_type=pattern.pattern_type,
                            section=self._current_section,
                            line_number=line_num,
                            context=line.strip()[:100],
                        )

                elif pattern.pattern_type == NotationPatternType.NUMERIC_SUPERSCRIPT:
                    # FA¹, FA², etc.
                    abbrev = groups[0]
                    axiom_names = {
                        'FA¹': 'Axiom of Alchemical Actualization',
                        'FA²': 'Axiom of Panoptic Re-contextualization',
                        'FA³': 'Axiom of Qualitative Transcendence',
                        'FA⁴': 'Axiom of Architectonic Integrity',
                        'FA⁵': 'Axiom of Visual Integrity',
                    }
                    if abbrev in axiom_names:
                        yield AbbreviationEntry(
                            abbreviation=abbrev,
                            full_term=axiom_names[abbrev],
                            pattern_type=pattern.pattern_type,
                            section=self._current_section,
                            line_number=line_num,
                        )

                elif pattern.pattern_type in (
                    NotationPatternType.CRC_DESIGNATOR,
                    NotationPatternType.TIER_DESIGNATOR,
                    NotationPatternType.GREEK_LETTER_OPERATOR,
                    NotationPatternType.LINGUISTIC_MANDATE,
                    NotationPatternType.FACTION_ABBREVIATION,
                ):
                    # Single-group patterns - abbreviation only
                    abbrev = groups[0]
                    yield AbbreviationEntry(
                        abbreviation=abbrev,
                        full_term="",  # Will be resolved by registry lookup
                        pattern_type=pattern.pattern_type,
                        section=self._current_section,
                        line_number=line_num,
                        context=line.strip()[:100],
                    )

                elif pattern.pattern_type == NotationPatternType.SAI_DESIGNATOR:
                    # Groups: (entity_name, abbreviation)
                    if len(groups) >= 2:
                        yield AbbreviationEntry(
                            abbreviation=groups[1],
                            full_term=groups[0].strip(),
                            pattern_type=pattern.pattern_type,
                            section=self._current_section,
                            line_number=line_num,
                        )

                elif pattern.pattern_type == NotationPatternType.EMOJI_SEMANTIC:
                    # Groups: (emoji, meaning)
                    if len(groups) >= 2:
                        yield AbbreviationEntry(
                            abbreviation=groups[0],
                            full_term=groups[1].strip(),
                            pattern_type=pattern.pattern_type,
                            section=self._current_section,
                            line_number=line_num,
                        )

                elif pattern.pattern_type == NotationPatternType.SLASH_COMPOSITE:
                    # Record the composite relationship
                    parts = [g for g in groups if g]
                    if len(parts) >= 2:
                        yield AbbreviationEntry(
                            abbreviation="/".join(parts),
                            full_term="[COMPOSITE]",
                            pattern_type=pattern.pattern_type,
                            section=self._current_section,
                            line_number=line_num,
                            aliases=list(parts),
                        )

    def get_pattern_stats(self, entries: list[AbbreviationEntry]) -> dict[str, int]:
        """Get count of entries by pattern type."""
        stats: dict[str, int] = {}
        for entry in entries:
            key = entry.pattern_type.name
            stats[key] = stats.get(key, 0) + 1
        return stats
