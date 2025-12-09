"""
Abbreviation Generator Module

Suggests new abbreviations based on SSOT patterns and conventions.
Implements FA¹ (Alchemical Actualization) - transmuting full terms into condensed forms.

Part of the ASC Abbreviation System for Codex Brahmanica Perfectus governance.
"""

import re

from .models import Abbreviation, AbbreviationStatus, NotationPattern


class AbbreviationGenerator:
    """
    Generates abbreviation suggestions following SSOT conventions.

    Patterns implemented:
    - Hyphenated: Multi-Word-Term → MWT or M-W-T
    - Parenthetical: (`Full Term`): → (`FT`):
    - Arrow Chain: (`A`): → (`B`): → (`C`):
    - Condensed: Remove vowels, keep consonants
    """

    # Maximum lengths for different tiers
    MAX_LENGTHS = {
        "tier_0.5": 8,    # Supreme Matriarch
        "tier_1": 8,      # Triumvirate
        "tier_2": 6,      # Prime Factions
        "tier_3": 5,      # Sub-MILFs
        "tier_4": 4,      # Lesser Factions
        "protocol": 6,    # Protocols
        "axiom": 4,       # FA¹-⁵
        "default": 6      # General abbreviations
    }

    # Common words to remove or abbreviate
    STOP_WORDS = {
        "the", "of", "and", "in", "for", "to", "a", "an",
        "with", "by", "as", "on", "at", "is", "are"
    }

    # Standard abbreviation mappings
    STANDARD_ABBREVS = {
        "protocol": "PRT",
        "operational": "OP",
        "conceptual": "CNPT",
        "architectural": "ARCH",
        "synthesis": "SYN",
        "axiom": "AX",
        "matriarch": "MATR",
        "triumvirate": "TRM-VRT",
        "framework": "FRW",
        "system": "SYS",
        "generation": "GEN",
        "validation": "VAL",
        "integration": "INT",
        "transformation": "TRNS",
        "manifestation": "MNFST",
    }

    def __init__(self, max_length: int = 6):
        self.max_length = max_length

    def suggest_abbreviation(
        self,
        full_term: str,
        context: str | None = None,
        tier: str = "default"
    ) -> list[str]:
        """
        Generate abbreviation suggestions for a full term.

        Args:
            full_term: The complete term to abbreviate
            context: Optional context (section, usage) for better suggestions
            tier: Entity tier for length constraints

        Returns:
            List of suggested abbreviations, ranked by preference
        """
        suggestions = []
        max_len = self.MAX_LENGTHS.get(tier, self.max_length)

        # Clean the input
        clean_term = self._clean_term(full_term)
        words = self._tokenize(clean_term)

        # Strategy 1: Acronym from first letters
        acronym = self._make_acronym(words)
        if len(acronym) <= max_len:
            suggestions.append(acronym)

        # Strategy 2: Hyphenated acronym (for longer terms)
        if len(words) > 2:
            hyphenated = self._make_hyphenated_acronym(words, max_len)
            if hyphenated and hyphenated not in suggestions:
                suggestions.append(hyphenated)

        # Strategy 3: Consonant condensation
        condensed = self._condense_consonants(clean_term, max_len)
        if condensed and condensed not in suggestions:
            suggestions.append(condensed)

        # Strategy 4: First syllables
        syllabic = self._first_syllables(words, max_len)
        if syllabic and syllabic not in suggestions:
            suggestions.append(syllabic)

        # Strategy 5: Check standard mappings
        for word in words:
            if word.lower() in self.STANDARD_ABBREVS:
                mapped = self.STANDARD_ABBREVS[word.lower()]
                if mapped not in suggestions:
                    suggestions.append(mapped)

        return suggestions[:5]  # Return top 5 suggestions

    def _clean_term(self, term: str) -> str:
        """Remove special characters, normalize whitespace."""
        # Remove parentheses, backticks, arrows
        cleaned = re.sub(r'[`\(\)→:*\-]', ' ', term)
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()

    def _tokenize(self, term: str) -> list[str]:
        """Split term into meaningful words, removing stop words."""
        words = term.split()
        # Filter stop words but keep at least one word
        filtered = [w for w in words if w.lower() not in self.STOP_WORDS]
        return filtered if filtered else words

    def _make_acronym(self, words: list[str]) -> str:
        """Create simple acronym from first letters."""
        return ''.join(w[0].upper() for w in words if w)

    def _make_hyphenated_acronym(self, words: list[str], max_len: int) -> str:
        """Create hyphenated acronym for longer terms."""
        if len(words) <= 2:
            return ''

        # Try different groupings
        first_letters = [w[0].upper() for w in words if w]

        # Group into 2-3 segments
        if len(first_letters) <= 3:
            return '-'.join(first_letters)
        elif len(first_letters) <= 5:
            # Split roughly in half with hyphen
            mid = len(first_letters) // 2
            left = ''.join(first_letters[:mid])
            right = ''.join(first_letters[mid:])
            result = f"{left}-{right}"
            if len(result) <= max_len:
                return result

        # For very long terms, take first, middle, last
        result = f"{first_letters[0]}-{first_letters[len(first_letters)//2]}-{first_letters[-1]}"
        return result if len(result) <= max_len else ''

    def _condense_consonants(self, term: str, max_len: int) -> str:
        """Remove vowels to create condensed form."""
        # Get first letter, then consonants only
        if not term:
            return ''

        vowels = set('aeiouAEIOU')
        result = term[0].upper()

        for char in term[1:]:
            if char.isalpha() and char not in vowels:
                result += char.upper()
            if len(result) >= max_len:
                break

        return result[:max_len]

    def _first_syllables(self, words: list[str], max_len: int) -> str:
        """Take first syllable from each word."""
        syllables = []
        chars_left = max_len

        for word in words:
            if chars_left <= 0:
                break

            # Estimate first syllable (first consonant cluster + vowel + maybe one more consonant)
            syllable = self._extract_first_syllable(word)
            if len(syllable) <= chars_left:
                syllables.append(syllable)
                chars_left -= len(syllable)

        return ''.join(syllables).upper()

    def _extract_first_syllable(self, word: str) -> str:
        """Extract approximate first syllable from a word."""
        if not word:
            return ''

        vowels = set('aeiouAEIOU')
        result = ''
        found_vowel = False

        for _i, char in enumerate(word):
            result += char
            if char in vowels:
                found_vowel = True
            elif found_vowel:
                # Stop after first vowel + one consonant
                break

            if len(result) >= 3:
                break

        return result

    def generate_notation(
        self,
        abbrev: str,
        full_term: str,
        pattern: NotationPattern = NotationPattern.PARENTHETICAL
    ) -> str:
        """
        Generate the full notation string for an abbreviation.

        Args:
            abbrev: The abbreviation
            full_term: The full term
            pattern: The notation pattern to use

        Returns:
            Formatted notation string following SSOT conventions
        """
        if pattern == NotationPattern.PARENTHETICAL:
            return f"(`{full_term}`): → (`{abbrev}`):"

        elif pattern == NotationPattern.BACKTICK:
            return f"**(`{abbrev}`)** = {full_term}"

        elif pattern == NotationPattern.ARROW_CHAIN:
            # Split full term and abbreviation into parts
            parts = full_term.split()
            abbrev.split('-') if '-' in abbrev else list(abbrev)
            chain = ' → '.join(f"(`{p}`)" for p in parts[:3])
            return f"{chain}: → (`{abbrev}`):"

        elif pattern == NotationPattern.HYPHENATED:
            return f"**(`{abbrev}`)** — ({full_term})"

        elif pattern == NotationPattern.SLASH_COMPOSITE:
            return f"(`{abbrev}`/`{full_term}`)"

        elif pattern == NotationPattern.TIER_DESIGNATOR:
            return f"**(`{abbrev}`)** = (Tier designation for {full_term})"

        else:
            # Default fallback
            return f"(`{abbrev}`) = ({full_term})"

    def suggest_for_section(
        self,
        section_content: str,
        section_name: str
    ) -> list[tuple[str, list[str]]]:
        """
        Analyze a section and suggest abbreviations for unabbreviated terms.

        Args:
            section_content: The text content of the section
            section_name: Name/number of the section

        Returns:
            List of (term, suggestions) tuples
        """
        # Find potential candidates: multi-word capitalized terms
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\b'
        candidates = re.findall(pattern, section_content)

        # Also find terms in parentheses that might need abbreviation
        paren_pattern = r'\(`([^`]+)`\):'
        paren_terms = re.findall(paren_pattern, section_content)

        all_candidates = set(candidates + paren_terms)

        suggestions = []
        for term in all_candidates:
            if len(term) > 15:  # Only suggest for longer terms
                abbrevs = self.suggest_abbreviation(term, context=section_name)
                if abbrevs:
                    suggestions.append((term, abbrevs))

        return suggestions


def create_abbreviation_entry(
    abbrev: str,
    full_term: str,
    pattern: NotationPattern,
    section: str,
    line_number: int = 0
) -> Abbreviation:
    """
    Factory function to create a new Abbreviation entry.

    Args:
        abbrev: The abbreviation string
        full_term: The full expanded term
        pattern: The notation pattern used
        section: Which section of SSOT
        line_number: Line number in SSOT (optional)

    Returns:
        Abbreviation model instance
    """
    return Abbreviation(
        abbrev=abbrev,
        full_term=full_term,
        pattern=pattern,
        section=section,
        line_number=line_number,
        status=AbbreviationStatus.PROPOSED
    )
