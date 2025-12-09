"""
Data Models for SSOT Abbreviation System
=========================================

Core dataclasses representing abbreviations, patterns, issues, and reports.
These form the type-safe foundation for all abbreviation operations.

Notation Pattern IDs (from Audit):
- P1: Parenthetical Inline Definition — `(`FullTerm`): → (`ABBREV`):`
- P2: Backtick Inline — `` `ABBREV` ``
- P3: Triple-Arrow Chain — `→ → →`
- P4: Hyphenated Compound — `X-Y-Z`
- P5: Slash-Composite — `/`
- P6: Numeric Superscript — `FA¹⁻⁵`
- P7: Dollar-Sign Invocation — `$...$`
- P8: Greek Letter Operators — `ΦΩΨ`
- P9: CRC-XXX Entity Designators
- P10: Tier Designators — `T-X` / `Tier X`
- P11: Linguistic Mandate Abbreviations
- P12: Faction Abbreviations
- P13: SAI Designators
- P14: Protocol/Section Reference
- P15: Emoji-Semantic Layer
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class NotationPatternType(Enum):
    """The 15 notation patterns identified in the SSOT audit."""
    PARENTHETICAL_INLINE = auto()      # P1: **(`Full`): → (`ABBR`):**
    BACKTICK_INLINE = auto()           # P2: `ABBREV`
    TRIPLE_ARROW_CHAIN = auto()        # P3: → → →
    HYPHENATED_COMPOUND = auto()       # P4: X-Y-Z
    SLASH_COMPOSITE = auto()           # P5: A/B/C
    NUMERIC_SUPERSCRIPT = auto()       # P6: FA¹⁻⁵
    DOLLAR_SIGN_INVOCATION = auto()    # P7: $keyword${param}
    GREEK_LETTER_OPERATOR = auto()     # P8: ΦΩΨ
    CRC_DESIGNATOR = auto()            # P9: CRC-XXX
    TIER_DESIGNATOR = auto()           # P10: Tier X / T-X
    LINGUISTIC_MANDATE = auto()        # P11: EULP-AA, LIPAA, etc.
    FACTION_ABBREVIATION = auto()      # P12: TMO, TTG, TDPC, etc.
    SAI_DESIGNATOR = auto()            # P13: SAI + Entity
    SECTION_REFERENCE = auto()         # P14: Section X / Prt.X
    EMOJI_SEMANTIC = auto()            # P15: 👑💀⚜️


class IssueSeverity(Enum):
    """Severity levels for consistency issues."""
    CRITICAL = "critical"    # Breaks functionality or causes ambiguity
    WARNING = "warning"      # Inconsistent but functional
    INFO = "info"           # Style suggestion, not a problem


class IssueCategory(Enum):
    """Categories of consistency issues."""
    DUPLICATE = "duplicate"           # Same abbrev, different meanings
    ORPHAN = "orphan"                 # Defined but never used
    SPELLING_VARIANT = "spelling"     # TRM-VRT vs TR-VRT
    SEMANTIC_OVERLOAD = "overload"    # / used for both OR and AND
    EXCESSIVE_LENGTH = "length"       # Abbreviation too long (>6 chars)
    MISSING_DEFINITION = "undefined"  # Used but never defined
    DEPRECATED = "deprecated"         # Should not be used
    PATTERN_MISMATCH = "pattern"      # Doesn't match expected pattern


@dataclass
class NotationPattern:
    """Describes a specific notation pattern used in the SSOT."""
    pattern_type: NotationPatternType
    regex: str
    description: str
    examples: list[str] = field(default_factory=list)
    is_consistent: bool = True
    notes: str = ""


@dataclass
class AbbreviationEntry:
    """A single abbreviation with its metadata."""
    abbreviation: str
    full_term: str
    pattern_type: NotationPatternType
    section: str = ""
    line_number: int = 0
    context: str = ""  # Surrounding text for disambiguation
    status: str = "active"  # active, deprecated, proposed
    aliases: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)  # Related abbreviations

    def __hash__(self):
        return hash((self.abbreviation, self.full_term))

    def __eq__(self, other):
        if not isinstance(other, AbbreviationEntry):
            return False
        return self.abbreviation == other.abbreviation and self.full_term == other.full_term


@dataclass
class ConsistencyIssue:
    """A detected consistency problem in the abbreviation system."""
    issue_id: str
    severity: IssueSeverity
    category: IssueCategory
    description: str
    affected_entries: list[AbbreviationEntry] = field(default_factory=list)
    line_numbers: list[int] = field(default_factory=list)
    recommendation: str = ""
    auto_fixable: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.issue_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "affected": [e.abbreviation for e in self.affected_entries],
            "lines": self.line_numbers,
            "recommendation": self.recommendation,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class SectionStats:
    """Statistics for a single SSOT section."""
    section_name: str
    section_number: str
    line_start: int
    line_end: int
    abbreviation_count: int = 0
    has_notation_guide: bool = False
    patterns_used: list[NotationPatternType] = field(default_factory=list)


@dataclass
class AuditReport:
    """Complete audit report for the SSOT abbreviation system."""
    timestamp: datetime = field(default_factory=datetime.now)
    ssot_path: str = ""
    ssot_hash: str = ""
    total_lines: int = 0
    total_abbreviations: int = 0
    unique_abbreviations: int = 0
    pattern_counts: dict[str, int] = field(default_factory=dict)
    section_stats: list[SectionStats] = field(default_factory=list)
    issues: list[ConsistencyIssue] = field(default_factory=list)
    health_metrics: dict[str, float] = field(default_factory=dict)

    @property
    def critical_issues(self) -> list[ConsistencyIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

    @property
    def warning_issues(self) -> list[ConsistencyIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    @property
    def info_issues(self) -> list[ConsistencyIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.INFO]

    def summary(self) -> str:
        return (
            f"SSOT Audit Report ({self.timestamp.strftime('%Y-%m-%d %H:%M')})\n"
            f"{'=' * 50}\n"
            f"Total Lines: {self.total_lines}\n"
            f"Abbreviations: {self.total_abbreviations} total, {self.unique_abbreviations} unique\n"
            f"Issues: {len(self.critical_issues)} critical, {len(self.warning_issues)} warnings, {len(self.info_issues)} info\n"
        )
