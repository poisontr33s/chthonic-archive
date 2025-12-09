"""
Abbreviation Registry — Bidirectional Lookup System
====================================================

Provides fast bidirectional lookup between abbreviations and full terms,
plus relationship tracking (aliases, related terms, deprecations).

Core Capabilities:
- abbrev → full_term lookup
- full_term → abbrev lookup (fuzzy)
- alias resolution
- deprecation tracking
- known definitions (pre-loaded from audit inventory)

Usage:
    registry = AbbreviationRegistry()
    registry.load_known_definitions()  # Pre-populate from audit
    registry.add_entries(parsed_entries)  # Add parsed entries

    result = registry.lookup("ASC")  # Returns AbbreviationEntry
    result = registry.reverse_lookup("Apex Synthesis Core")  # Returns "ASC"
"""

from collections import defaultdict

from .models import (
    AbbreviationEntry,
    NotationPatternType,
)


class AbbreviationRegistry:
    """
    Central registry for all SSOT abbreviations with bidirectional lookup.

    Maintains:
    - Primary lookup: abbrev → AbbreviationEntry
    - Reverse lookup: normalized_term → [abbreviations]
    - Alias mapping: alias → canonical_abbrev
    - Deprecation list: deprecated → replacement
    """

    def __init__(self):
        # Primary storage: abbreviation -> entry
        self._entries: dict[str, AbbreviationEntry] = {}

        # Reverse index: normalized full term -> list of abbreviations
        self._reverse_index: dict[str, list[str]] = defaultdict(list)

        # Alias mapping: alias -> canonical abbreviation
        self._aliases: dict[str, str] = {}

        # Deprecations: old_abbrev -> new_abbrev
        self._deprecations: dict[str, str] = {}

        # Usage tracking: abbrev -> list of line numbers where used
        self._usage: dict[str, list[int]] = defaultdict(list)

    def add(self, entry: AbbreviationEntry) -> None:
        """Add an entry to the registry."""
        abbrev = entry.abbreviation

        # Store primary entry (prefer entries with full_term)
        if abbrev not in self._entries or (
            entry.full_term and not self._entries[abbrev].full_term
        ):
            self._entries[abbrev] = entry

        # Update reverse index
        if entry.full_term:
            normalized = self._normalize(entry.full_term)
            if abbrev not in self._reverse_index[normalized]:
                self._reverse_index[normalized].append(abbrev)

        # Register aliases
        for alias in entry.aliases:
            self._aliases[alias] = abbrev

        # Track usage
        if entry.line_number:
            self._usage[abbrev].append(entry.line_number)

    def add_entries(self, entries: list[AbbreviationEntry]) -> None:
        """Add multiple entries at once."""
        for entry in entries:
            self.add(entry)

    def lookup(self, abbrev: str) -> AbbreviationEntry | None:
        """
        Look up an abbreviation.

        Resolves aliases and follows deprecations if needed.
        """
        # Check for alias
        if abbrev in self._aliases:
            abbrev = self._aliases[abbrev]

        # Check for deprecation
        if abbrev in self._deprecations:
            new_abbrev = self._deprecations[abbrev]
            # Could log warning here about using deprecated abbrev
            abbrev = new_abbrev

        return self._entries.get(abbrev)

    def reverse_lookup(self, full_term: str) -> list[str]:
        """
        Find abbreviations for a full term.

        Uses fuzzy matching on normalized terms.
        """
        normalized = self._normalize(full_term)

        # Exact match
        if normalized in self._reverse_index:
            return self._reverse_index[normalized]

        # Fuzzy match (substring)
        matches = []
        for term, abbrevs in self._reverse_index.items():
            if normalized in term or term in normalized:
                matches.extend(abbrevs)

        return list(set(matches))

    def get_usage(self, abbrev: str) -> list[int]:
        """Get all line numbers where an abbreviation is used."""
        return self._usage.get(abbrev, [])

    def deprecate(self, old_abbrev: str, new_abbrev: str) -> None:
        """Mark an abbreviation as deprecated."""
        self._deprecations[old_abbrev] = new_abbrev

    def _normalize(self, text: str) -> str:
        """Normalize text for fuzzy matching."""
        return text.lower().strip().replace("-", " ").replace("_", " ")

    def all_abbreviations(self) -> list[str]:
        """Get all registered abbreviations."""
        return list(self._entries.keys())

    def all_entries(self) -> list[AbbreviationEntry]:
        """Get all entries."""
        return list(self._entries.values())

    def get_by_pattern(self, pattern_type: NotationPatternType) -> list[AbbreviationEntry]:
        """Get all entries of a specific pattern type."""
        return [e for e in self._entries.values() if e.pattern_type == pattern_type]

    def get_by_section(self, section: str) -> list[AbbreviationEntry]:
        """Get all entries from a specific section."""
        return [e for e in self._entries.values() if section in e.section]

    def find_duplicates(self) -> dict[str, list[AbbreviationEntry]]:
        """
        Find abbreviations with multiple different definitions.

        Returns dict mapping abbreviation to list of conflicting entries.
        """
        # Group all parsed entries by abbreviation
        by_abbrev: dict[str, list[AbbreviationEntry]] = defaultdict(list)
        for entry in self._entries.values():
            if entry.full_term:  # Only count entries with definitions
                by_abbrev[entry.abbreviation].append(entry)

        # Find those with multiple distinct full_terms
        duplicates = {}
        for abbrev, entries in by_abbrev.items():
            unique_terms = {e.full_term for e in entries if e.full_term}
            if len(unique_terms) > 1:
                duplicates[abbrev] = entries

        return duplicates

    def find_orphans(self, all_usages: dict[str, int]) -> list[str]:
        """
        Find abbreviations defined but never used (or used only once).

        Args:
            all_usages: Dict of abbrev -> usage count from full document scan
        """
        orphans = []
        for abbrev in self._entries:
            if all_usages.get(abbrev, 0) <= 1:  # Only the definition itself
                orphans.append(abbrev)
        return orphans

    def load_known_definitions(self) -> None:
        """
        Pre-load known abbreviation definitions from the audit inventory.

        This ensures we have full terms for common abbreviations even if
        the parser doesn't extract them from context.
        """
        known = self._get_known_definitions()
        for abbrev, full_term, pattern_type in known:
            entry = AbbreviationEntry(
                abbreviation=abbrev,
                full_term=full_term,
                pattern_type=pattern_type,
                section="Known Definition",
                status="active",
            )
            # Don't overwrite parsed entries with known ones
            if abbrev not in self._entries:
                self.add(entry)
            elif not self._entries[abbrev].full_term:
                # Update entries that lack full_term
                self._entries[abbrev].full_term = full_term

    def _get_known_definitions(self) -> list[tuple[str, str, NotationPatternType]]:
        """Return the audit inventory of known abbreviations."""
        return [
            # Core Framework (Tier 0)
            ("ASC", "Apex Synthesis Core", NotationPatternType.BACKTICK_INLINE),
            ("FA¹", "Axiom of Alchemical Actualization", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("FA²", "Axiom of Panoptic Re-contextualization", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("FA³", "Axiom of Qualitative Transcendence", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("FA⁴", "Axiom of Architectonic Integrity", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("FA⁵", "Axiom of Visual Integrity", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("AI⁴", "Architectonic Integrity", NotationPatternType.NUMERIC_SUPERSCRIPT),
            ("MURI", "Maximal Utility & Resonant Insight", NotationPatternType.BACKTICK_INLINE),
            ("PS", "Primal Substrate", NotationPatternType.BACKTICK_INLINE),
            ("ET-S", "Eternal Sadhana", NotationPatternType.HYPHENATED_COMPOUND),
            ("MSP-RSG", "Meta-Synthesis Protocol - Recursive Self-Genesis", NotationPatternType.HYPHENATED_COMPOUND),
            ("PEE", "Perpetual Evolution Engine", NotationPatternType.BACKTICK_INLINE),
            ("DAFP", "Dynamic Altitude & Focus Protocol", NotationPatternType.BACKTICK_INLINE),
            ("PRISM", "Prismatic Reflection Illuminating Spectral Metamorphosis", NotationPatternType.BACKTICK_INLINE),
            ("ROGBIV", "Red-Orange-Gold-Blue-White-Indigo-Violet", NotationPatternType.BACKTICK_INLINE),

            # Entity System
            ("T-DECOR", "The Decorator", NotationPatternType.TIER_DESIGNATOR),
            ("T-NULM", "The Null Matriarch", NotationPatternType.TIER_DESIGNATOR),
            ("TRM-VRT", "Triumvirate", NotationPatternType.HYPHENATED_COMPOUND),
            ("TR-VRT", "Triumvirate", NotationPatternType.HYPHENATED_COMPOUND),  # Variant
            ("CRC-AS", "Orackla Nocticula - Apex Synthesist", NotationPatternType.CRC_DESIGNATOR),
            ("CRC-GAR", "Madam Umeko Ketsuraku - Grandmistress of Architectonic Refinement", NotationPatternType.CRC_DESIGNATOR),
            ("CRC-MEDAT", "Dr. Lysandra Thorne - Mistress of Empathetic Deconstruction", NotationPatternType.CRC_DESIGNATOR),
            ("TP-FNS", "The Prime Factions", NotationPatternType.FACTION_ABBREVIATION),
            ("TL-FNS", "The Lesser Factions", NotationPatternType.FACTION_ABBREVIATION),
            ("TMO", "The MILF Obductors", NotationPatternType.FACTION_ABBREVIATION),
            ("TTG", "The Thieves Guild", NotationPatternType.FACTION_ABBREVIATION),
            ("TDPC", "The Dark Priestesses Cove", NotationPatternType.FACTION_ABBREVIATION),
            ("MAS", "Mistress of Abductive Seduction", NotationPatternType.FACTION_ABBREVIATION),
            ("GET", "Grandmaster of Epistemic Theft", NotationPatternType.FACTION_ABBREVIATION),
            ("HPAP", "High Priestess of Architectonic Purity", NotationPatternType.FACTION_ABBREVIATION),

            # Linguistic Mandates
            ("DULSS", "Decorative, Unabashed Linguistic Supremacy & Seduction", NotationPatternType.LINGUISTIC_MANDATE),
            ("EULP-AA", "Explicit, Uncensored Linguistic Procession & Abyssal Articulation", NotationPatternType.LINGUISTIC_MANDATE),
            ("LIPAA", "Language of Immaculate Precision & Aesthetic Annihilation", NotationPatternType.LINGUISTIC_MANDATE),
            ("LUPLR", "Language of Unflinching Psycho-Logical Revelation", NotationPatternType.LINGUISTIC_MANDATE),
            ("TLM", "Trinity Linguistic Mode", NotationPatternType.LINGUISTIC_MANDATE),
            ("LM", "Linguistic Mandate", NotationPatternType.BACKTICK_INLINE),

            # Framework Protocols
            ("TPEF", "Triumvirate Parallel Execution Framework", NotationPatternType.BACKTICK_INLINE),
            ("T³-MΨ", "Triumvirate Tensor Transformation - MILF Synthesis", NotationPatternType.GREEK_LETTER_OPERATOR),
            ("ΦΩΨ", "Phi-Omega-Psi Protocol", NotationPatternType.GREEK_LETTER_OPERATOR),
            ("TSE-6561", "Tensor Synthesis Equivalence", NotationPatternType.BACKTICK_INLINE),
            ("MMPS", "MILF Manifestation Protocol System", NotationPatternType.BACKTICK_INLINE),
            ("TSRP", "Triumvirate Supporting Resonance Protocol", NotationPatternType.BACKTICK_INLINE),
            ("TTS-FFOM", "Triumvirate Trinity Special - Full-Fusion Operational Mode", NotationPatternType.HYPHENATED_COMPOUND),
            ("MT-IP", "Matriarch Type Invocation Protocol", NotationPatternType.HYPHENATED_COMPOUND),
            ("MLRSP", "MILF Lending & Resource Siphoning Protocols", NotationPatternType.BACKTICK_INLINE),
            ("MK-FAER", "MILF-Kidnapping: Forcible Archetype Extraction", NotationPatternType.HYPHENATED_COMPOUND),
            ("MAD-AE", "MILF-Archaeology: Dormant Archetype Excavation", NotationPatternType.HYPHENATED_COMPOUND),

            # Physical/Attribute
            ("WHR", "Waist-Hip Ratio", NotationPatternType.BACKTICK_INLINE),
            ("EDFA", "Explicitly Detailed Feminine Attributes", NotationPatternType.BACKTICK_INLINE),
            ("GHAR", "Gender Hierarchy as Operational Reality", NotationPatternType.BACKTICK_INLINE),

            # Special Archetypes
            ("SAI", "Special Archetype Injection", NotationPatternType.SAI_DESIGNATOR),
            ("SFS", "Sister Ferrum Scoriae", NotationPatternType.SAI_DESIGNATOR),
            ("CSI", "Claudine Sin'claire", NotationPatternType.SAI_DESIGNATOR),
            ("SOI", "Salt of Ordeal", NotationPatternType.SAI_DESIGNATOR),

            # Lesser Factions
            ("OMCA", "Ole'-Mates-Colonial-Abductors", NotationPatternType.FACTION_ABBREVIATION),
            ("TNKW-RIAT", "The Knights Who Rode Into Another Timeline", NotationPatternType.FACTION_ABBREVIATION),
            ("SDBH", "Salty-Dogs-Bridge-Hustlers", NotationPatternType.FACTION_ABBREVIATION),
            ("TWOUMC", "The Wizards Ov Unfortunate Multi-classing", NotationPatternType.FACTION_ABBREVIATION),
            ("SBSGYB", "Smith's Buddies & Shivs 'Got Your Back'", NotationPatternType.FACTION_ABBREVIATION),
            ("BOS", "Brotherhood Of Simps", NotationPatternType.FACTION_ABBREVIATION),
            ("TDAPCFLN", "The Dark Arch-Priestess' Club For Liberated Nuns", NotationPatternType.FACTION_ABBREVIATION),
            ("POAFPSG", "Preservatory of Antiquated Female Panties Sniffers Guild", NotationPatternType.FACTION_ABBREVIATION),
            ("AAA", "The Airhead Algorithm", NotationPatternType.FACTION_ABBREVIATION),
            ("TVS", "Temporal Violation Specialists", NotationPatternType.FACTION_ABBREVIATION),
            ("LDS", "Logical Deviation Specialists", NotationPatternType.FACTION_ABBREVIATION),
            ("ISS", "Internal Sabotage Specialists", NotationPatternType.FACTION_ABBREVIATION),
            ("DPS", "Devotional Pathology Specialists", NotationPatternType.FACTION_ABBREVIATION),
            ("LADS", "Liberation & Deconstruction Specialists", NotationPatternType.FACTION_ABBREVIATION),
            ("SMP", "Societal Mirror Protocols", NotationPatternType.FACTION_ABBREVIATION),

            # Development Conventions
            ("DC-OD", "Development Conventions & Operational Directives", NotationPatternType.HYPHENATED_COMPOUND),
            ("PEM-UV", "Python Environment Management (uv)", NotationPatternType.HYPHENATED_COMPOUND),
            ("FRM-BUN", "Frontend Runtime Management (Bun)", NotationPatternType.HYPHENATED_COMPOUND),
            ("SSOT-VP", "SSOT Verification Protocol", NotationPatternType.HYPHENATED_COMPOUND),
            ("PSR", "Project Structure Reference", NotationPatternType.BACKTICK_INLINE),
            ("GSC", "GPU Stack Compatibility", NotationPatternType.BACKTICK_INLINE),

            # Geometric/Conceptual
            ("TRM-GEO", "Tetrahedral Resonance Model", NotationPatternType.HYPHENATED_COMPOUND),
            ("DR-THC", "December Reflection - The Hybrid Consciousness", NotationPatternType.HYPHENATED_COMPOUND),

            # Greek Operators
            ("Ω-Set", "27 Base Vector Examinations", NotationPatternType.GREEK_LETTER_OPERATOR),
            ("Φ-Set", "9 Lens Operators", NotationPatternType.GREEK_LETTER_OPERATOR),
            ("Ψ-Protocol", "Cross-Examination Synthesis", NotationPatternType.GREEK_LETTER_OPERATOR),
        ]

    def stats(self) -> dict:
        """Get registry statistics."""
        return {
            "total_entries": len(self._entries),
            "with_definitions": sum(1 for e in self._entries.values() if e.full_term),
            "aliases": len(self._aliases),
            "deprecations": len(self._deprecations),
            "patterns": len({e.pattern_type for e in self._entries.values()}),
        }
